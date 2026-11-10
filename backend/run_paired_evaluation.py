"""
Phase 14.2 — Paired Evaluation Framework & Independent Validation
Evaluates:
1. Pre-Phase 14 Baseline Policy
2. Phase 14 Initial Policy (Uncalibrated: sim < 0.70 & gk < 0.45 -> NON_MONUMENT_REJECTED)
3. Phase 14.2 Calibrated Candidate Policy (Hard-reject: sim < 0.70 & gk <= 0.35, Review: sim < 0.70 & 0.35 < gk < 0.45)

Evaluated on identical held-out test datasets under identical inference, preprocessing, model weights, and ground truth labels:
- Cohort 1: 36-Specimen Multi-Category Benchmark
- Cohort 2: 100-Specimen Independent Final Holdout (Split D)
"""

import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
logger = logging.getLogger("paired_eval")

INDEX_FILE = BASE_DIR / "monument_index.faiss"
LABELS_FILE = BASE_DIR / "monument_labels.json"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
CALIB_FILE = BASE_DIR / "calibration_config.json"
SPLIT_D_MANIFEST = BASE_DIR / "phase_8_4_split_d_manifest.json"

ARCH_PROMPTS = [
    "a photo of a historic monument, ancient temple, palace, or fort architecture",
    "a photo of a famous heritage building or ancient architectural landmark",
    "a photo of an ordinary everyday object, person, animal, food, document, or non-architectural scene",
    "a photo of modern interior, paperwork, receipt, household item, or common vehicle",
]


def compute_wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculates Wilson score interval for binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95% confidence
    p_hat = k / n
    denom = 1.0 + (z**2) / n
    center = (p_hat + (z**2) / (2.0 * n)) / denom
    margin = (z * math.sqrt((p_hat * (1.0 - p_hat)) / n + (z**2) / (4.0 * (n**2)))) / denom
    lower = max(0.0, (center - margin) * 100.0)
    upper = min(100.0, (center + margin) * 100.0)
    return (round(lower, 2), round(upper, 2))


class PairedEvaluator:
    def __init__(self):
        logger.info("Initializing CLIP ViT-B/32 on CPU...")
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

    def run_image(self, img_path: Path) -> Dict[str, Any]:
        with Image.open(img_path) as raw_img:
            image_rgb = raw_img.convert("RGB")

        # 1. CLIP Embedding
        t_clip = time.perf_counter()
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
        clip_ms = (time.perf_counter() - t_clip) * 1000.0

        # 2. Gatekeeper
        gatekeeper_score = self.evaluate_gatekeeper(img_vec)

        # 3. FAISS Search
        query_matrix = np.expand_dims(img_vec, axis=0).astype(np.float32)
        raw_distances, raw_indices = self.faiss_index.search(query_matrix, 15)

        # 4. Phase 14.2 Calibrated Candidate Arbitration
        t_p14_calib = time.perf_counter()
        p14_calib_res = self.uncertainty_engine.evaluate(
            image=image_rgb,
            gatekeeper_score=gatekeeper_score,
            raw_distances=raw_distances,
            raw_indices=raw_indices,
            labels=self.labels,
            metadata=self.metadata,
        )
        p14_calib_ms = (time.perf_counter() - t_p14_calib) * 1000.0

        # Extract unique candidate ranking
        monument_best: Dict[str, Dict[str, Any]] = {}
        dists = raw_distances[0]
        indices = raw_indices[0]
        for dist, idx in zip(dists, indices):
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
        b_top1_sim = top1["sim"] if top1 else 0.0
        b_top2_sim = top2["sim"] if top2 else 0.0
        b_margin = b_top1_sim - b_top2_sim

        # 5. Pre-Phase 14 Baseline Arbitration
        t_base = time.perf_counter()
        if gatekeeper_score < 0.35 and b_top1_sim < 0.65:
            b_decision = "NON_MONUMENT_REJECTED"
        elif gatekeeper_score < 0.40 and b_top1_sim >= 0.75:
            b_decision = "REVIEW_REQUIRED"
        elif gatekeeper_score >= 0.55 and b_top1_sim >= 0.75 and b_margin >= 0.05:
            b_decision = "VERIFIED_MATCH"
        elif gatekeeper_score >= 0.45 and b_top1_sim >= 0.70 and b_margin < 0.05:
            b_decision = "UNCERTAIN_MATCH"
        elif gatekeeper_score >= 0.45 and b_top1_sim < 0.75:
            b_decision = "UNKNOWN_HERITAGE_SPECIMEN"
        else:
            b_decision = "REVIEW_REQUIRED"
        base_ms = (time.perf_counter() - t_base) * 1000.0

        # 6. Phase 14 Initial (Uncalibrated) Arbitration
        t_uncal = time.perf_counter()
        if b_top1_sim < 0.70 and gatekeeper_score < 0.45:
            p14_uncal_decision = "NON_MONUMENT_REJECTED"
        elif gatekeeper_score < 0.45 and b_top1_sim >= 0.80:
            p14_uncal_decision = "REVIEW_REQUIRED"
        elif gatekeeper_score >= 0.55 and b_top1_sim >= 0.80 and b_margin >= 0.05:
            p14_uncal_decision = "VERIFIED_MATCH"
        elif gatekeeper_score >= 0.45 and b_top1_sim >= 0.80 and b_margin < 0.05:
            p14_uncal_decision = "UNCERTAIN_MATCH"
        elif gatekeeper_score >= 0.45 and b_top1_sim < 0.80:
            p14_uncal_decision = "UNKNOWN_HERITAGE_SPECIMEN"
        else:
            p14_uncal_decision = "REVIEW_REQUIRED"
        uncal_ms = (time.perf_counter() - t_uncal) * 1000.0

        p14_top1 = p14_calib_res.top_candidates[0] if p14_calib_res.top_candidates else None
        p14_top2 = p14_calib_res.top_candidates[1] if len(p14_calib_res.top_candidates) > 1 else None
        p14_top3 = p14_calib_res.top_candidates[2] if len(p14_calib_res.top_candidates) > 2 else None

        return {
            "file": img_path.name,
            "gatekeeper_score": round(gatekeeper_score, 4),
            "clip_ms": round(clip_ms, 2),
            "top1_sim": round(b_top1_sim, 4),
            "top2_sim": round(b_top2_sim, 4),
            "margin": round(b_margin, 4),
            "baseline": {
                "decision": b_decision,
                "top1_key": top1["key"] if top1 else None,
                "top1_sim": round(b_top1_sim, 4),
                "top2_key": top2["key"] if top2 else None,
                "top2_sim": round(b_top2_sim, 4),
                "top3_key": top3["key"] if top3 else None,
                "margin": round(b_margin, 4),
                "latency_ms": round(clip_ms + base_ms, 2),
            },
            "phase14_uncalibrated": {
                "decision": p14_uncal_decision,
                "top1_key": top1["key"] if top1 else None,
                "top1_sim": round(b_top1_sim, 4),
                "top2_key": top2["key"] if top2 else None,
                "top2_sim": round(b_top2_sim, 4),
                "top3_key": top3["key"] if top3 else None,
                "margin": round(b_margin, 4),
                "latency_ms": round(clip_ms + uncal_ms, 2),
            },
            "phase14_calibrated": {
                "decision": p14_calib_res.decision.value,
                "top1_key": p14_top1.monument_key if p14_top1 else None,
                "top1_sim": round(p14_top1.max_similarity if p14_top1 else 0.0, 4),
                "top2_key": p14_top2.monument_key if p14_top2 else None,
                "top2_sim": round(p14_top2.max_similarity if p14_top2 else 0.0, 4),
                "top3_key": p14_top3.monument_key if p14_top3 else None,
                "margin": round(p14_calib_res.similarity_margin, 4),
                "calibrated_prob": p14_calib_res.calibrated_probability,
                "latency_ms": round(clip_ms + p14_calib_ms, 2),
            }
        }


def compute_cohort_metrics(records: List[Dict[str, Any]], system_key: str) -> Dict[str, Any]:
    catalog_recs = [r for r in records if r["ground_truth"] not in ["out_of_catalog", "unknown_heritage", "non_monument"]]
    distractor_recs = [r for r in records if r["ground_truth"] in ["out_of_catalog", "unknown_heritage", "non_monument"]]
    non_mon_recs = [r for r in records if r["ground_truth"] == "non_monument"]
    unk_recs = [r for r in records if r["ground_truth"] in ["out_of_catalog", "unknown_heritage"]]

    # Top-1 & Top-3 on catalog items
    top1_corr = sum(1 for r in catalog_recs if r[system_key]["top1_key"] == r["ground_truth"])
    top3_corr = sum(1 for r in catalog_recs if r["ground_truth"] in [r[system_key]["top1_key"], r[system_key]["top2_key"], r[system_key]["top3_key"]])
    top1_acc = (top1_corr / len(catalog_recs)) * 100.0 if catalog_recs else 0.0
    top3_acc = (top3_corr / len(catalog_recs)) * 100.0 if catalog_recs else 0.0

    # False Positives: Distractor declared VERIFIED_MATCH
    fp = sum(1 for r in distractor_recs if r[system_key]["decision"] == "VERIFIED_MATCH")
    fpr = (fp / len(distractor_recs)) * 100.0 if distractor_recs else 0.0
    fpr_ci = compute_wilson_ci(fp, len(distractor_recs))

    # False Negatives: Catalog item declared NON_MONUMENT_REJECTED
    fn = sum(1 for r in catalog_recs if r[system_key]["decision"] == "NON_MONUMENT_REJECTED")
    fnr = (fn / len(catalog_recs)) * 100.0 if catalog_recs else 0.0
    fnr_ci = compute_wilson_ci(fn, len(catalog_recs))

    # Non-monument clean rejection accuracy
    nm_rej = sum(1 for r in non_mon_recs if r[system_key]["decision"] == "NON_MONUMENT_REJECTED")
    nm_acc = (nm_rej / len(non_mon_recs)) * 100.0 if non_mon_recs else 0.0

    # Review Required count & rate across all records
    review_count = sum(1 for r in records if r[system_key]["decision"] == "REVIEW_REQUIRED")
    review_rate = (review_count / len(records)) * 100.0 if records else 0.0

    # Verified Match count & rate across catalog records
    vm_count = sum(1 for r in catalog_recs if r[system_key]["decision"] == "VERIFIED_MATCH")
    vm_rate = (vm_count / len(catalog_recs)) * 100.0 if catalog_recs else 0.0

    # Unknown detection accuracy
    unk_det = sum(1 for r in unk_recs if r[system_key]["decision"] in ["UNKNOWN_HERITAGE_SPECIMEN", "REVIEW_REQUIRED"])
    unk_acc = (unk_det / len(unk_recs)) * 100.0 if unk_recs else 0.0

    # Latencies
    lats = [r[system_key]["latency_ms"] for r in records]
    mean_lat = float(np.mean(lats)) if lats else 0.0
    med_lat = float(np.median(lats)) if lats else 0.0

    return {
        "total_specimens": len(records),
        "catalog_specimens": len(catalog_recs),
        "distractor_specimens": len(distractor_recs),
        "top1_acc_pct": round(top1_acc, 2),
        "top1_correct_count": top1_corr,
        "top3_acc_pct": round(top3_acc, 2),
        "top3_correct_count": top3_corr,
        "fpr_pct": round(fpr, 2),
        "false_positive_count": fp,
        "fpr_ci_95": fpr_ci,
        "fnr_pct": round(fnr, 2),
        "false_negative_count": fn,
        "fnr_ci_95": fnr_ci,
        "non_monument_rejection_acc_pct": round(nm_acc, 2),
        "non_monument_rejected_count": nm_rej,
        "non_monument_total": len(non_mon_recs),
        "review_required_rate_pct": round(review_rate, 2),
        "review_required_count": review_count,
        "verified_match_rate_pct": round(vm_rate, 2),
        "verified_match_count": vm_count,
        "unknown_detection_acc_pct": round(unk_acc, 2),
        "unknown_detected_count": unk_det,
        "mean_latency_ms": round(mean_lat, 2),
        "median_latency_ms": round(med_lat, 2),
    }


def run_paired_evaluation():
    evaluator = PairedEvaluator()

    # -------------------------------------------------------------------------
    # COHORT 1: 36-Specimen Multi-Category Benchmark
    # -------------------------------------------------------------------------
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATING COHORT 1: 36-SPECIMEN MULTI-CATEGORY BENCHMARK (PAIRED)")
    logger.info("=" * 80)

    specimens_36 = [
        # Known Catalogue Monuments (12)
        ("backend/assets/heritage/taj-mahal.jpg", "taj_mahal", "known_catalogue"),
        ("backend/assets/heritage/petra.jpg", "petra", "known_catalogue"),
        ("backend/assets/heritage/colosseum.jpg", "colosseum", "known_catalogue"),
        ("backend/assets/heritage/brihadeeswarar.jpg", "brihadeeswarar_temple", "known_catalogue"),
        ("backend/assets/heritage/hawa-mahal.jpg", "hawa_mahal", "known_catalogue"),
        ("backend/assets/heritage/konark-sun-temple.jpg", "konark_sun_temple", "known_catalogue"),
        ("backend/assets/heritage/hampi.jpg", "hampi_stone_chariot", "known_catalogue"),
        ("backend/assets/heritage/mysore-palace.jpg", "mysore_palace", "known_catalogue"),
        ("backend/assets/heritage/golden-temple.jpg", "golden_temple", "known_catalogue"),
        ("backend/assets/heritage/ajanta-caves.jpg", "ajanta_caves", "known_catalogue"),
        ("backend/datasets/phase_8_5c_ooc_eval/big_ben.jpg", "big_ben", "known_catalogue"),
        ("backend/datasets/phase_8_5c_ooc_eval/statue_of_liberty.jpg", "statue_of_liberty", "known_catalogue"),

        # Similar-Looking Monuments (4)
        ("backend/assets/heritage/charminar.jpg", "charminar", "similar_pairs"),
        ("backend/assets/heritage/qutub-minar.jpg", "qutub_minar", "similar_pairs"),
        ("backend/datasets/independent_final_test_v4/split_d_012_charminar.jpg", "charminar", "similar_pairs"),
        ("backend/datasets/independent_final_test_v4/split_d_034_qutub_minar.jpg", "qutub_minar", "similar_pairs"),

        # Architectural Close-Ups (8)
        ("backend/datasets/local_feature_eval/feat_taj_jali_02.jpg", "taj_mahal", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_taj_pietradura_01.jpg", "taj_mahal", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_hawa_jharokha_01.jpg", "hawa_mahal", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_konark_wheel_01.jpg", "konark_sun_temple", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_qutub_balcony_02.jpg", "qutub_minar", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_brih_vimana_tier_01.jpg", "brihadeeswarar_temple", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_sanchi_torana_01.jpg", "sanchi_stupa", "architectural_closeups"),
        ("backend/datasets/local_feature_eval/feat_charminar_stucco_01.jpg", "charminar", "architectural_closeups"),

        # Occluded Monuments (2)
        ("backend/datasets/local_feature_eval/feat_charminar_occluded_02.jpg", "charminar", "occluded_monuments"),
        ("backend/datasets/local_feature_eval/feat_sanchi_partial_03.jpg", "sanchi_stupa", "occluded_monuments"),

        # Low-Quality Images (2)
        ("backend/datasets/local_feature_eval/feat_qutub_lowres_03.jpg", "qutub_minar", "low_quality_images"),
        ("backend/datasets/independent_final_test_v4/split_d_046_taj_mahal.jpg", "taj_mahal", "low_quality_images"),

        # Unknown Monuments (1)
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

    c1_records = []
    for rel_path, gt, cat in specimens_36:
        p = WORKSPACE_ROOT / rel_path
        if not p.exists():
            continue
        eval_res = evaluator.run_image(p)
        eval_res["ground_truth"] = gt
        eval_res["category"] = cat
        eval_res["rel_path"] = rel_path
        c1_records.append(eval_res)

    c1_base = compute_cohort_metrics(c1_records, "baseline")
    c1_uncal = compute_cohort_metrics(c1_records, "phase14_uncalibrated")
    c1_calib = compute_cohort_metrics(c1_records, "phase14_calibrated")

    # Category breakdown for Cohort 1
    categories = [
        "known_catalogue",
        "similar_pairs",
        "architectural_closeups",
        "occluded_monuments",
        "low_quality_images",
        "unknown_monuments",
        "non_monument_distractors",
    ]
    c1_cat_breakdown = {}
    for cat in categories:
        cat_recs = [r for r in c1_records if r["category"] == cat]
        c1_cat_breakdown[cat] = {
            "count": len(cat_recs),
            "baseline": compute_cohort_metrics(cat_recs, "baseline"),
            "phase14_uncalibrated": compute_cohort_metrics(cat_recs, "phase14_uncalibrated"),
            "phase14_calibrated": compute_cohort_metrics(cat_recs, "phase14_calibrated"),
            "specimens": [
                {
                    "file": r["file"],
                    "ground_truth": r["ground_truth"],
                    "top1_sim": r["top1_sim"],
                    "gatekeeper": r["gatekeeper_score"],
                    "baseline_decision": r["baseline"]["decision"],
                    "uncalibrated_decision": r["phase14_uncalibrated"]["decision"],
                    "calibrated_decision": r["phase14_calibrated"]["decision"],
                }
                for r in cat_recs
            ]
        }

    # -------------------------------------------------------------------------
    # COHORT 2: 100-Specimen Independent Holdout (Split D)
    # -------------------------------------------------------------------------
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATING COHORT 2: 100-SPECIMEN INDEPENDENT HOLDOUT (SPLIT D)")
    logger.info("=" * 80)

    with open(SPLIT_D_MANIFEST, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    split_d_items = manifest_data["records"]

    c2_records = []
    for item in split_d_items:
        p = WORKSPACE_ROOT / "backend" / item["relative_path"]
        if not p.exists():
            continue
        eval_res = evaluator.run_image(p)
        gt = item["monument_key"]
        cat = item["category"]
        cond = item.get("condition", "standard")
        eval_res["ground_truth"] = gt
        eval_res["category"] = cat
        eval_res["condition"] = cond
        eval_res["rel_path"] = item["relative_path"]
        c2_records.append(eval_res)

    c2_base = compute_cohort_metrics(c2_records, "baseline")
    c2_uncal = compute_cohort_metrics(c2_records, "phase14_uncalibrated")
    c2_calib = compute_cohort_metrics(c2_records, "phase14_calibrated")

    # Category breakdown for Cohort 2
    c2_cat_breakdown = {}
    for cat_name in ["catalog", "unknown_heritage", "non_monument"]:
        sub_recs = [r for r in c2_records if r["category"] == cat_name]
        c2_cat_breakdown[cat_name] = {
            "count": len(sub_recs),
            "baseline": compute_cohort_metrics(sub_recs, "baseline"),
            "phase14_uncalibrated": compute_cohort_metrics(sub_recs, "phase14_uncalibrated"),
            "phase14_calibrated": compute_cohort_metrics(sub_recs, "phase14_calibrated"),
        }

    # Print Report
    print("\n" + "=" * 105)
    print("PHASE 14.2 THREE-WAY PAIRED EVALUATION: BASELINE vs UNCALIBRATED vs CALIBRATED CANDIDATE")
    print("=" * 105)
    print("\n--- COHORT 1: 36-SPECIMEN MULTI-CATEGORY BENCHMARK ---")
    print(f"{'Metric':<32} {'Baseline':<24} {'Phase 14 Initial':<24} {'Phase 14.2 Calibrated':<24}")
    print("-" * 105)
    metrics_display_c1 = [
        ("Top-1 Catalogue Accuracy", f"{c1_base['top1_acc_pct']}% ({c1_base['top1_correct_count']}/{c1_base['catalog_specimens']})", f"{c1_uncal['top1_acc_pct']}% ({c1_uncal['top1_correct_count']}/{c1_uncal['catalog_specimens']})", f"{c1_calib['top1_acc_pct']}% ({c1_calib['top1_correct_count']}/{c1_calib['catalog_specimens']})"),
        ("Top-3 Catalogue Accuracy", f"{c1_base['top3_acc_pct']}% ({c1_base['top3_correct_count']}/{c1_base['catalog_specimens']})", f"{c1_uncal['top3_acc_pct']}% ({c1_uncal['top3_correct_count']}/{c1_uncal['catalog_specimens']})", f"{c1_calib['top3_acc_pct']}% ({c1_calib['top3_correct_count']}/{c1_calib['catalog_specimens']})"),
        ("False Positive Rate (FPR)", f"{c1_base['fpr_pct']}% ({c1_base['false_positive_count']}/{c1_base['distractor_specimens']}) CI{c1_base['fpr_ci_95']}", f"{c1_uncal['fpr_pct']}% ({c1_uncal['false_positive_count']}/{c1_uncal['distractor_specimens']}) CI{c1_uncal['fpr_ci_95']}", f"{c1_calib['fpr_pct']}% ({c1_calib['false_positive_count']}/{c1_calib['distractor_specimens']}) CI{c1_calib['fpr_ci_95']}"),
        ("False Negative Rate (FNR)", f"{c1_base['fnr_pct']}% ({c1_base['false_negative_count']}/{c1_base['catalog_specimens']}) CI{c1_base['fnr_ci_95']}", f"{c1_uncal['fnr_pct']}% ({c1_uncal['false_negative_count']}/{c1_uncal['catalog_specimens']}) CI{c1_uncal['fnr_ci_95']}", f"{c1_calib['fnr_pct']}% ({c1_calib['false_negative_count']}/{c1_calib['catalog_specimens']}) CI{c1_calib['fnr_ci_95']}"),
        ("Non-Monument Clean Rejection", f"{c1_base['non_monument_rejection_acc_pct']}% ({c1_base['non_monument_rejected_count']}/{c1_base['non_monument_total']})", f"{c1_uncal['non_monument_rejection_acc_pct']}% ({c1_uncal['non_monument_rejected_count']}/{c1_uncal['non_monument_total']})", f"{c1_calib['non_monument_rejection_acc_pct']}% ({c1_calib['non_monument_rejected_count']}/{c1_calib['non_monument_total']})"),
        ("REVIEW_REQUIRED Rate", f"{c1_base['review_required_rate_pct']}% ({c1_base['review_required_count']}/{c1_base['total_specimens']})", f"{c1_uncal['review_required_rate_pct']}% ({c1_uncal['review_required_count']}/{c1_uncal['total_specimens']})", f"{c1_calib['review_required_rate_pct']}% ({c1_calib['review_required_count']}/{c1_calib['total_specimens']})"),
        ("Verified-Match Rate", f"{c1_base['verified_match_rate_pct']}% ({c1_base['verified_match_count']}/{c1_base['catalog_specimens']})", f"{c1_uncal['verified_match_rate_pct']}% ({c1_uncal['verified_match_count']}/{c1_uncal['catalog_specimens']})", f"{c1_calib['verified_match_rate_pct']}% ({c1_calib['verified_match_count']}/{c1_calib['catalog_specimens']})"),
        ("Mean Latency (ms)", f"{c1_base['mean_latency_ms']} ms", f"{c1_uncal['mean_latency_ms']} ms", f"{c1_calib['mean_latency_ms']} ms"),
        ("Median Latency (ms)", f"{c1_base['median_latency_ms']} ms", f"{c1_uncal['median_latency_ms']} ms", f"{c1_calib['median_latency_ms']} ms"),
    ]
    for name, b_val, u_val, c_val in metrics_display_c1:
        print(f"{name:<32} {b_val:<24} {u_val:<24} {c_val:<24}")

    print("\n--- COHORT 2: 100-SPECIMEN INDEPENDENT HOLDOUT (Split D - Zero Leakage) ---")
    print(f"{'Metric':<32} {'Baseline':<24} {'Phase 14 Initial':<24} {'Phase 14.2 Calibrated':<24}")
    print("-" * 105)
    metrics_display_c2 = [
        ("Top-1 Catalogue Accuracy", f"{c2_base['top1_acc_pct']}% ({c2_base['top1_correct_count']}/{c2_base['catalog_specimens']})", f"{c2_uncal['top1_acc_pct']}% ({c2_uncal['top1_correct_count']}/{c2_uncal['catalog_specimens']})", f"{c2_calib['top1_acc_pct']}% ({c2_calib['top1_correct_count']}/{c2_calib['catalog_specimens']})"),
        ("Top-3 Catalogue Accuracy", f"{c2_base['top3_acc_pct']}% ({c2_base['top3_correct_count']}/{c2_base['catalog_specimens']})", f"{c2_uncal['top3_acc_pct']}% ({c2_uncal['top3_correct_count']}/{c2_uncal['catalog_specimens']})", f"{c2_calib['top3_acc_pct']}% ({c2_calib['top3_correct_count']}/{c2_calib['catalog_specimens']})"),
        ("False Positive Rate (FPR)", f"{c2_base['fpr_pct']}% ({c2_base['false_positive_count']}/{c2_base['distractor_specimens']}) CI{c2_base['fpr_ci_95']}", f"{c2_uncal['fpr_pct']}% ({c2_uncal['false_positive_count']}/{c2_uncal['distractor_specimens']}) CI{c2_uncal['fpr_ci_95']}", f"{c2_calib['fpr_pct']}% ({c2_calib['false_positive_count']}/{c2_calib['distractor_specimens']}) CI{c2_calib['fpr_ci_95']}"),
        ("False Negative Rate (FNR)", f"{c2_base['fnr_pct']}% ({c2_base['false_negative_count']}/{c2_base['catalog_specimens']}) CI{c2_base['fnr_ci_95']}", f"{c2_uncal['fnr_pct']}% ({c2_uncal['false_negative_count']}/{c2_uncal['catalog_specimens']}) CI{c2_uncal['fnr_ci_95']}", f"{c2_calib['fnr_pct']}% ({c2_calib['false_negative_count']}/{c2_calib['catalog_specimens']}) CI{c2_calib['fnr_ci_95']}"),
        ("Non-Monument Clean Rejection", f"{c2_base['non_monument_rejection_acc_pct']}% ({c2_base['non_monument_rejected_count']}/{c2_base['non_monument_total']})", f"{c2_uncal['non_monument_rejection_acc_pct']}% ({c2_uncal['non_monument_rejected_count']}/{c2_uncal['non_monument_total']})", f"{c2_calib['non_monument_rejection_acc_pct']}% ({c2_calib['non_monument_rejected_count']}/{c2_calib['non_monument_total']})"),
        ("REVIEW_REQUIRED Rate", f"{c2_base['review_required_rate_pct']}% ({c2_base['review_required_count']}/{c2_base['total_specimens']})", f"{c2_uncal['review_required_rate_pct']}% ({c2_uncal['review_required_count']}/{c2_uncal['total_specimens']})", f"{c2_calib['review_required_rate_pct']}% ({c2_calib['review_required_count']}/{c2_calib['total_specimens']})"),
        ("Verified-Match Rate", f"{c2_base['verified_match_rate_pct']}% ({c2_base['verified_match_count']}/{c2_base['catalog_specimens']})", f"{c2_uncal['verified_match_rate_pct']}% ({c2_uncal['verified_match_count']}/{c2_uncal['catalog_specimens']})", f"{c2_calib['verified_match_rate_pct']}% ({c2_calib['verified_match_count']}/{c2_calib['catalog_specimens']})"),
        ("Mean Latency (ms)", f"{c2_base['mean_latency_ms']} ms", f"{c2_uncal['mean_latency_ms']} ms", f"{c2_calib['mean_latency_ms']} ms"),
        ("Median Latency (ms)", f"{c2_base['median_latency_ms']} ms", f"{c2_uncal['median_latency_ms']} ms", f"{c2_calib['median_latency_ms']} ms"),
    ]
    for name, b_val, u_val, c_val in metrics_display_c2:
        print(f"{name:<32} {b_val:<24} {u_val:<24} {c_val:<24}")

    # Inspect close-ups, occlusions, and low-quality images
    print("\n--- CLOSE-UPS, OCCLUSIONS, AMBIGUOUS ANGLES & LOW-QUALITY SPECIMENS AUDIT ---")
    sensitive_cats = ["architectural_closeups", "occluded_monuments", "low_quality_images"]
    for cat in sensitive_cats:
        print(f"\n[Category: {cat.upper()}]")
        for item in c1_cat_breakdown[cat]["specimens"]:
            status_flag = "RECOVERED_TO_REVIEW" if item['uncalibrated_decision'] == 'NON_MONUMENT_REJECTED' and item['calibrated_decision'] == 'REVIEW_REQUIRED' else item['calibrated_decision']
            print(f"  {item['file']:<35} | GT: {item['ground_truth']:<22} | Sim: {item['top1_sim']:.4f} | GK: {item['gatekeeper']:.4f} | Initial: {item['uncalibrated_decision']} -> Calibrated: {item['calibrated_decision']} ({status_flag})")

    # Save complete JSON
    out_dict = {
        "cohort_1_benchmark_36": {
            "baseline": c1_base,
            "phase14_uncalibrated": c1_uncal,
            "phase14_calibrated": c1_calib,
            "category_breakdown": c1_cat_breakdown,
            "records": c1_records,
        },
        "cohort_2_holdout_100_split_d": {
            "baseline": c2_base,
            "phase14_uncalibrated": c2_uncal,
            "phase14_calibrated": c2_calib,
            "category_breakdown": c2_cat_breakdown,
            "records": c2_records,
        }
    }
    out_file = BASE_DIR / "phase_14_2_paired_evaluation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, indent=2)
    logger.info(f"Saved complete paired evaluation report to {out_file.name}")

    return out_dict


if __name__ == "__main__":
    run_paired_evaluation()
