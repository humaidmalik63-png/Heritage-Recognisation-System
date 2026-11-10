"""
Phase 14.1 — Benchmark Population Integrity & Paired Evaluation Engine
Audits:
1. Population discrepancy analysis (why sample counts differed between baseline and Phase 14)
2. Exact-hash and perceptual-hash (dHash) leakage between test specimens and FAISS reference gallery
3. Strict paired evaluation under identical conditions, identical labels, and identical datasets
"""

import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from calibration import CalibrationEngine
from catalogue_service import get_catalogue_100
from uncertainty import DecisionState, UncertaintyEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_audit")

INDEX_FILE = BASE_DIR / "monument_index.faiss"
LABELS_FILE = BASE_DIR / "monument_labels.json"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
CALIB_FILE = BASE_DIR / "calibration_config.json"
REF_GALLERY_DIR = BASE_DIR / "datasets" / "reference_gallery_100"
SPLIT_D_DIR = BASE_DIR / "datasets" / "independent_final_test_v4"
SPLIT_D_MANIFEST = BASE_DIR / "phase_8_4_split_d_manifest.json"

ARCH_PROMPTS = [
    "a photo of a historic monument, ancient temple, palace, or fort architecture",
    "a photo of a famous heritage building or ancient architectural landmark",
    "a photo of an ordinary everyday object, person, animal, food, document, or non-architectural scene",
    "a photo of modern interior, paperwork, receipt, household item, or common vehicle",
]


def compute_dhash(img_path: Path, hash_size: int = 8) -> str:
    """Computes difference hash (dHash) for perceptual image duplicate detection."""
    try:
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return ""
        resized = cv2.resize(img, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
        diff = resized[:, 1:] > resized[:, :-1]
        return "".join(format(x, "02x") for x in np.packbits(diff))
    except Exception:
        return ""


def dhash_distance(h1: str, h2: str) -> int:
    """Computes Hamming distance between two hex dHash strings."""
    if not h1 or not h2 or len(h1) != len(h2):
        return 999
    b1 = bin(int(h1, 16))[2:].zfill(len(h1) * 4)
    b2 = bin(int(h2, 16))[2:].zfill(len(h2) * 4)
    return sum(c1 != c2 for c1, c2 in zip(b1, b2))


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class DualPolicyEvaluator:
    """
    Evaluates both:
    1. Pre-Phase 14 Baseline Policy (Uncalibrated / strict legacy thresholds without Phase 14 tuning)
    2. Phase 14 Enhanced Policy
    under 100% identical inference and preprocessing conditions.
    """

    def __init__(self):
        logger.info("Initializing CLIP ViT-B/32 and FAISS Index for Dual Evaluation...")
        self.device = "cpu"
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.model.eval()

        text_inputs = self.processor(text=ARCH_PROMPTS, return_tensors="pt", padding=True)
        with torch.no_grad():
            text_outputs = self.model.get_text_features(**text_inputs)
            if hasattr(text_outputs, "pooler_output") and text_outputs.pooler_output is not None:
                text_feats = text_outputs.pooler_output
            elif hasattr(text_outputs, "text_embeds"):
                text_feats = text_outputs.text_embeds
            else:
                text_feats = text_outputs
            norm = text_feats.norm(p=2, dim=-1, keepdim=True)
            self.gatekeeper_text_embeds = (text_feats / norm).numpy()

        self.faiss_index = faiss.read_index(str(INDEX_FILE))
        with open(LABELS_FILE, "r", encoding="utf-8") as f:
            self.labels = json.load(f)
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.calibration_engine = CalibrationEngine(CALIB_FILE)
        self.uncertainty_engine = UncertaintyEngine(self.calibration_engine)
        self.catalogue_100 = get_catalogue_100()

    def evaluate_gatekeeper(self, img_vec: np.ndarray) -> float:
        sims = np.dot(self.gatekeeper_text_embeds, img_vec)
        arch_score = float(max(sims[0], sims[1]))
        non_arch_score = float(max(sims[2], sims[3]))
        scale = 18.0
        exp_arch = np.exp(scale * arch_score)
        exp_non = np.exp(scale * non_arch_score)
        return float(exp_arch / (exp_arch + exp_non + 1e-12))

    def run_image_features(self, img_path: Path) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray, Image.Image]:
        with Image.open(img_path) as raw_img:
            image_rgb = raw_img.convert("RGB")

        inputs = self.processor(images=image_rgb, return_tensors="pt")
        with torch.no_grad():
            img_outputs = self.model.get_image_features(**inputs)
            if hasattr(img_outputs, "pooler_output") and img_outputs.pooler_output is not None:
                features = img_outputs.pooler_output
            elif hasattr(img_outputs, "image_embeds"):
                features = img_outputs.image_embeds
            else:
                features = img_outputs
            norm = features.norm(p=2, dim=-1, keepdim=True)
            img_vec = (features / norm).squeeze(0).numpy()

        gk_score = self.evaluate_gatekeeper(img_vec)
        query_matrix = np.expand_dims(img_vec, axis=0).astype(np.float32)
        raw_distances, raw_indices = self.faiss_index.search(query_matrix, 15)

        return img_vec, gk_score, raw_distances, raw_indices, image_rgb

    def evaluate_phase_14(self, image_rgb: Image.Image, gk_score: float, dists: np.ndarray, indices: np.ndarray) -> Dict[str, Any]:
        """Runs Phase 14 calibrated uncertainty engine."""
        unc_res = self.uncertainty_engine.evaluate(
            image=image_rgb,
            gatekeeper_score=gk_score,
            raw_distances=dists,
            raw_indices=indices,
            labels=self.labels,
            metadata=self.metadata,
        )
        cands = unc_res.top_candidates
        top1 = cands[0] if len(cands) > 0 else None
        top2 = cands[1] if len(cands) > 1 else None
        top3 = cands[2] if len(cands) > 2 else None

        return {
            "decision": unc_res.decision.value,
            "top1_key": top1.monument_key if top1 else None,
            "top1_sim": top1.max_similarity if top1 else 0.0,
            "top2_key": top2.monument_key if top2 else None,
            "top2_sim": top2.max_similarity if top2 else 0.0,
            "top3_key": top3.monument_key if top3 else None,
            "top3_sim": top3.max_similarity if top3 else 0.0,
            "margin": unc_res.similarity_margin,
            "gatekeeper_score": gk_score,
        }

    def evaluate_baseline(self, image_rgb: Image.Image, gk_score: float, dists: np.ndarray, indices: np.ndarray) -> Dict[str, Any]:
        """
        Runs Pre-Phase 14 baseline arbitration logic:
        - Legacy Rule 1: sim < (sim_threshold - 0.10) => 0.70, but without calibrated margin/gatekeeper tuning.
        - Legacy acceptance: allowed centroid matches without candidate-competition margin check.
        """
        # Aggregate candidates as baseline did
        monument_best: Dict[str, Dict[str, Any]] = {}
        d = dists[0]
        idx_list = indices[0]
        for dist, idx in zip(d, idx_list):
            if int(idx) == -1 or int(idx) >= len(self.labels):
                continue
            rec = self.labels[int(idx)]
            m_key = rec["monument_key"]
            sim = float(dist)
            if m_key not in monument_best or sim > monument_best[m_key]["sim"]:
                monument_best[m_key] = {
                    "key": m_key,
                    "sim": sim,
                }

        sorted_cands = sorted(monument_best.values(), key=lambda x: x["sim"], reverse=True)
        top1 = sorted_cands[0] if len(sorted_cands) > 0 else None
        top2 = sorted_cands[1] if len(sorted_cands) > 1 else None
        top3 = sorted_cands[2] if len(sorted_cands) > 2 else None

        top1_sim = top1["sim"] if top1 else 0.0
        top2_sim = top2["sim"] if top2 else 0.0
        margin = top1_sim - top2_sim

        # Baseline decision rules:
        # Pre-Phase 14 Baseline Rule:
        if gk_score < 0.35 and top1_sim < 0.65:
            decision = "NON_MONUMENT_REJECTED"
        elif gk_score < 0.40 and top1_sim >= 0.75:
            decision = "REVIEW_REQUIRED"
        elif gk_score >= 0.55 and top1_sim >= 0.75 and margin >= 0.05:
            decision = "VERIFIED_MATCH"
        elif gk_score >= 0.45 and top1_sim >= 0.70 and margin < 0.05:
            decision = "UNCERTAIN_MATCH"
        elif gk_score >= 0.45 and top1_sim < 0.75:
            decision = "UNKNOWN_HERITAGE_SPECIMEN"
        else:
            decision = "REVIEW_REQUIRED"

        return {
            "decision": decision,
            "top1_key": top1["key"] if top1 else None,
            "top1_sim": top1_sim,
            "top2_key": top2["key"] if top2 else None,
            "top2_sim": top2_sim,
            "top3_key": top3["key"] if top3 else None,
            "top3_sim": top3["sim"] if top3 else 0.0,
            "margin": margin,
            "gatekeeper_score": gk_score,
        }


def run_population_integrity_audit():
    logger.info("=" * 70)
    logger.info("STEP 1: BENCHMARK POPULATION INTEGRITY & AUDIT")
    logger.info("=" * 70)

    # Inspect the 36 specimens
    specimens_36 = [
        # Standard Catalog (14)
        ("backend/assets/heritage/taj-mahal.jpg", "taj_mahal", "known_catalogue"),
        ("backend/assets/heritage/petra.jpg", "petra", "known_catalogue"),
        ("backend/assets/heritage/colosseum.jpg", "colosseum", "known_catalogue"),
        ("backend/assets/heritage/charminar.jpg", "charminar", "similar_pairs"),
        ("backend/assets/heritage/brihadeeswarar.jpg", "brihadeeswarar_temple", "known_catalogue"),
        ("backend/assets/heritage/hawa-mahal.jpg", "hawa_mahal", "known_catalogue"),
        ("backend/assets/heritage/konark-sun-temple.jpg", "konark_sun_temple", "known_catalogue"),
        ("backend/assets/heritage/qutub-minar.jpg", "qutub_minar", "similar_pairs"),
        ("backend/assets/heritage/hampi.jpg", "hampi_stone_chariot", "known_catalogue"),
        ("backend/assets/heritage/mysore-palace.jpg", "mysore_palace", "known_catalogue"),
        ("backend/assets/heritage/golden-temple.jpg", "golden_temple", "known_catalogue"),
        ("backend/assets/heritage/ajanta-caves.jpg", "ajanta_caves", "known_catalogue"),
        ("backend/datasets/phase_8_5c_ooc_eval/big_ben.jpg", "big_ben", "known_catalogue"),
        ("backend/datasets/phase_8_5c_ooc_eval/statue_of_liberty.jpg", "statue_of_liberty", "known_catalogue"),

        # Architectural Details (8)
        ("backend/datasets/local_feature_eval/feat_taj_jali_02.jpg", "taj_mahal", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_taj_pietradura_01.jpg", "taj_mahal", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_hawa_jharokha_01.jpg", "hawa_mahal", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_konark_wheel_01.jpg", "konark_sun_temple", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_qutub_balcony_02.jpg", "qutub_minar", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_brih_vimana_tier_01.jpg", "brihadeeswarar_temple", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_sanchi_torana_01.jpg", "sanchi_stupa", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_charminar_stucco_01.jpg", "charminar", "architectural_closeups"),

        # Occluded & Low Quality & Perspective (6)
        ("backend/datasets/local_feature_eval/feat_qutub_lowres_03.jpg", "qutub_minar", "low_quality_images"),
        ("backend/datasets/local_feature_eval/feat_charminar_occluded_02.jpg", "charminar", "occluded_monuments"),
        ("backend/datasets/local_feature_eval/feat_sanchi_partial_03.jpg", "sanchi_stupa", "occluded_monuments"),
        ("backend/datasets/independent_final_test_v4/split_d_012_charminar.jpg", "charminar", "similar_pairs"),
        ("backend/datasets/independent_final_test_v4/split_d_034_qutub_minar.jpg", "qutub_minar", "similar_pairs"),
        ("backend/datasets/independent_final_test_v4/split_d_046_taj_mahal.jpg", "taj_mahal", "known_catalogue"),

        # Out-of-Catalog (1)
        ("backend/datasets/phase_8_5f_specimens/ordinary_building.jpg", "out_of_catalog", "unknown_monuments"),

        # Non-Monument Distractors (7)
        ("backend/datasets/local_feature_eval/feat_nonmon_glass_01.jpg", "non_monument", "non_monument_distractors"),
        ("backend/datasets/local_feature_eval/feat_nonmon_rock_02.jpg", "non_monument", "non_monument_distractors"),
        ("backend/datasets/phase_8_5f_specimens/mathematics_paper.jpg", "non_monument", "non_monument_distractors"),
        ("backend/datasets/receipt_distractor.jpg", "non_monument", "non_monument_distractors"),
        ("backend/datasets/independent_final_test_v4/split_d_062_non_monument.jpg", "non_monument", "non_monument_distractors"),
        ("backend/datasets/independent_final_test_v4/split_d_063_non_monument.jpg", "non_monument", "non_monument_distractors"),
        ("backend/datasets/independent_final_test_v4/split_d_090_non_monument.jpg", "non_monument", "non_monument_distractors"),
    ]

    # Leakage check with reference gallery
    logger.info("Checking SHA-256 and dHash collisions against reference gallery (577 anchors)...")
    gallery_hashes = {}
    gallery_dhashes = {}
    for p in REF_GALLERY_DIR.glob("*/*.jpg"):
        sha = compute_sha256(p)
        dh = compute_dhash(p)
        gallery_hashes[sha] = str(p.relative_to(WORKSPACE_ROOT))
        gallery_dhashes[dh] = str(p.relative_to(WORKSPACE_ROOT))

    exact_matches = []
    near_matches = []

    for rel_path, gt, cat in specimens_36:
        p = WORKSPACE_ROOT / rel_path
        if not p.exists():
            logger.warning(f"File missing: {rel_path}")
            continue
        sha = compute_sha256(p)
        dh = compute_dhash(p)

        if sha in gallery_hashes:
            exact_matches.append((rel_path, gallery_hashes[sha]))
        else:
            # Check near matches (dHash <= 4)
            for g_dh, g_path in gallery_dhashes.items():
                dist = dhash_distance(dh, g_dh)
                if dist <= 4:
                    near_matches.append((rel_path, g_path, dist))
                    break

    logger.info(f"Leakage Audit Results: Exact SHA-256 collisions: {len(exact_matches)}; Near dHash collisions: {len(near_matches)}")
    for test_f, gal_f in exact_matches:
        logger.info(f"  [EXACT COLLISION] {test_f} == {gal_f}")
    for test_f, gal_f, dist in near_matches:
        logger.info(f"  [NEAR COLLISION d={dist}] {test_f} ~ {gal_f}")

    return specimens_36, exact_matches, near_matches


if __name__ == "__main__":
    run_population_integrity_audit()
