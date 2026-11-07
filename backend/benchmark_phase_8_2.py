"""
Phase 8.2: Adaptive Recognition, Latency Profiling & Real-World Robustness Benchmark
Visual Heritage Recognition Platform (SIH 2025 - SIH25052)

Benchmarks 4 recognition paradigms:
- Config 1: Global CLIP + FAISS (Baseline)
- Config 2: Conditional Global + Local CLIP (Region Proposals)
- Config 3: Conditional Global + SIFT (Classical Geometric Matching)
- Config 4: Full Adaptive Pipeline (Phase 8.2 with Fast-path + Quality-gated SIFT + Non-override Rule)

Evaluated across:
1. Independent Test Dataset v2 (N=55)
2. Calibration Expansion Dataset v3 (N=265)

Slices:
- Night-time / Floodlit
- Low-light / Twilight
- Distant views
- Partial views
- Architectural carvings & friezes
- Unusual camera angles
- Occluded scenes
- Low-resolution / blur
"""

import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from calibration import CalibrationEngine
from local_feature_engine import LocalFeatureEngine
from uncertainty import DecisionState, UncertaintyEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_phase_8_2")

BASE_DIR = Path(__file__).resolve().parent
TEST_V2_MANIFEST = BASE_DIR / "datasets" / "independent_eval_v2_manifest.json"
CALIB_V3_MANIFEST = BASE_DIR / "datasets" / "calibration_dataset_v3_manifest.json"
INDEX_PATH = BASE_DIR / "monument_index.faiss"
LABELS_PATH = BASE_DIR / "monument_labels.json"
METADATA_PATH = BASE_DIR / "monuments_metadata.json"
CALIB_CONFIG_PATH = BASE_DIR / "calibration_config.json"
LOCAL_CONFIG_PATH = BASE_DIR / "local_feature_config.json"
OUTPUT_REPORT_PATH = BASE_DIR / "phase_8_2_benchmark_report.json"

MODEL_NAME = "openai/clip-vit-base-patch32"
GATEKEEPER_SCALE = 18.0

POSITIVE_PROMPTS = [
    "a photo of a historical monument, ancient temple, fort, palace, or architectural landmark",
    "famous heritage architecture exterior",
]
NEGATIVE_PROMPTS = [
    "a photo of a person, selfie, indoor room, animal, food, car, document, or random everyday object",
    "non-architectural scene",
]


class BenchmarkRunner:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing BenchmarkRunner on {self.device}...")

        self.clip_model = CLIPModel.from_pretrained(MODEL_NAME).to(self.device)
        self.clip_processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        self.clip_model.eval()

        self.faiss_index = faiss.read_index(str(INDEX_PATH))

        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            self.labels = json.load(f)

        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.calibration_engine = CalibrationEngine(CALIB_CONFIG_PATH)
        self.uncertainty_engine = UncertaintyEngine(self.calibration_engine)

        self.local_engine = LocalFeatureEngine(
            config_path=LOCAL_CONFIG_PATH,
            clip_model=self.clip_model,
            clip_processor=self.clip_processor,
            device=self.device,
        )

        # Precompute gatekeeper text vectors
        self.gate_pos = self._get_avg_text_vector(POSITIVE_PROMPTS)
        self.gate_neg = self._get_avg_text_vector(NEGATIVE_PROMPTS)

        # Build reference items list for local feature comparison
        self.reference_items = self._load_reference_items()

    def _get_avg_text_vector(self, prompts: List[str]) -> np.ndarray:
        inputs = self.clip_processor(text=prompts, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            t = self.clip_model.get_text_features(**inputs)
            if hasattr(t, "pooler_output") and t.pooler_output is not None:
                t = t.pooler_output
            norm = t.norm(dim=-1, keepdim=True)
            norm = torch.where(norm > 0, norm, torch.ones_like(norm))
            v = (t / norm).mean(dim=0)
            v = v / v.norm()
            return v.cpu().numpy()

    def _load_reference_items(self) -> List[Dict[str, Any]]:
        ref_items = []
        for i, item in enumerate(self.labels):
            item_copy = dict(item)
            item_copy["index_id"] = i
            ref_path = BASE_DIR / item["file_path"]
            if ref_path.exists():
                item_copy["exists"] = True
            ref_items.append(item_copy)
        return ref_items

    def encode_image(self, image: Image.Image) -> np.ndarray:
        inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            out = self.clip_model.get_image_features(**inputs)
            t = out.pooler_output if hasattr(out, "pooler_output") and out.pooler_output is not None else out
            v = t.cpu().detach().numpy().flatten().astype(np.float32)
            norm = np.linalg.norm(v)
            if norm > 0:
                v = v / norm
            return v.reshape(1, -1)

    def extract_specimen_base(self, image_path: Path) -> Dict[str, Any]:
        t0 = time.time()
        with Image.open(image_path) as pil_img:
            img_rgb = pil_img.convert("RGB")
            w, h = img_rgb.size
            gray = np.array(img_rgb.convert("L"), dtype=np.float32)
            gy, gx = np.gradient(gray)
            gnorm = np.sqrt(gx**2 + gy**2)
            blur_score = float(np.var(gnorm))
            brightness = float(np.mean(gray))

        # 1. Global CLIP + FAISS
        img_vec = self.encode_image(img_rgb)

        dot_p = float(np.dot(img_vec[0], self.gate_pos))
        dot_n = float(np.dot(img_vec[0], self.gate_neg))
        z_pos = dot_p * GATEKEEPER_SCALE
        z_neg = dot_n * GATEKEEPER_SCALE
        max_z = max(z_pos, z_neg)
        ez_p = math.exp(z_pos - max_z)
        ez_n = math.exp(z_neg - max_z)
        gatekeeper_score = float(ez_p / (ez_p + ez_n))

        raw_dist, raw_idx = self.faiss_index.search(img_vec, 15)
        uncertainty_res = self.uncertainty_engine.evaluate(
            image=img_rgb,
            gatekeeper_score=gatekeeper_score,
            raw_distances=raw_dist[0],
            raw_indices=raw_idx[0],
            labels=self.labels,
            metadata=self.metadata,
            exif_gps=None,
        )

        global_cand = uncertainty_res.top_candidates[0] if uncertainty_res.top_candidates else None
        global_key = global_cand.monument_key if global_cand else None
        global_score = global_cand.max_similarity if global_cand else 0.0
        margin = uncertainty_res.similarity_margin
        calibrated_conf = uncertainty_res.calibrated_probability

        top3_keys = [c.monument_key for c in uncertainty_res.top_candidates[:3]]
        decision_state = uncertainty_res.decision.value
        t_global_ms = (time.time() - t0) * 1000.0

        is_decisive_global = (
            global_score >= 0.85
            and margin >= 0.10
            and gatekeeper_score >= 0.70
        )
        is_non_monument = (gatekeeper_score < 0.40 and global_score < 0.65) or (decision_state == "NON_MONUMENT_REJECTED")

        return {
            "img_rgb": img_rgb,
            "blur_score": blur_score,
            "brightness": brightness,
            "global_key": global_key,
            "global_score": global_score,
            "margin": margin,
            "calibrated_conf": calibrated_conf,
            "gatekeeper_score": gatekeeper_score,
            "decision_state": decision_state,
            "top3_monuments": top3_keys,
            "t_global_ms": t_global_ms,
            "is_decisive_global": is_decisive_global,
            "is_non_monument": is_non_monument,
        }

    def evaluate_config_on_specimen(self, base: Dict[str, Any], config_mode: str) -> Dict[str, Any]:
        global_key = base["global_key"]
        global_score = base["global_score"]
        gatekeeper_score = base["gatekeeper_score"]
        is_decisive_global = base["is_decisive_global"]
        is_non_monument = base["is_non_monument"]
        img_rgb = base["img_rgb"]
        blur_score = base["blur_score"]
        brightness = base["brightness"]

        local_clip_triggered = False
        sift_triggered = False
        override_applied = False
        final_key = global_key
        t_extra_ms = 0.0

        if config_mode == "global_only":
            pass

        elif config_mode == "conditional_local_clip":
            if not is_decisive_global and not is_non_monument:
                local_clip_triggered = True
                t_sub = time.time()
                local_res = self.local_engine.match_local_features(
                    image=img_rgb,
                    reference_images=self.reference_items,
                    top_k_candidates=3,
                    enable_sift=False,
                )
                hybrid_eval = self.local_engine.evaluate_hybrid_evidence(
                    global_candidate={"monument_key": global_key, "similarity": global_score} if global_key else None,
                    local_results=local_res,
                    gatekeeper_score=gatekeeper_score,
                )
                t_extra_ms = (time.time() - t_sub) * 1000.0
                final_key = hybrid_eval["final_candidate_key"]

        elif config_mode == "conditional_sift":
            if not is_decisive_global and not is_non_monument:
                sift_triggered = True
                t_sub = time.time()
                if blur_score >= 25.0 and 25.0 <= brightness <= 230.0:
                    ref_cand = next((r for r in self.reference_items if r.get("monument_key") == global_key), None)
                    if ref_cand:
                        ref_p = BASE_DIR / ref_cand["file_path"]
                        if ref_p.exists():
                            ref_gray = cv2.imread(str(ref_p), cv2.IMREAD_GRAYSCALE)
                            if ref_gray is not None:
                                cv2_gray = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2GRAY)
                                self.local_engine.verify_geometric_correspondence(cv2_gray, ref_gray, method="sift")
                t_extra_ms = (time.time() - t_sub) * 1000.0

        elif config_mode == "full_adaptive":
            if not is_decisive_global and not is_non_monument:
                local_clip_triggered = True
                t_sub = time.time()
                local_res = self.local_engine.match_local_features(
                    image=img_rgb,
                    reference_images=self.reference_items,
                    top_k_candidates=3,
                    enable_sift=True,
                    quality_gate_sift=True,
                )
                sift_triggered = local_res.get("sift_triggered", False)
                hybrid_eval = self.local_engine.evaluate_hybrid_evidence(
                    global_candidate={"monument_key": global_key, "similarity": global_score} if global_key else None,
                    local_results=local_res,
                    gatekeeper_score=gatekeeper_score,
                )
                t_extra_ms = (time.time() - t_sub) * 1000.0
                override_applied = hybrid_eval.get("override_applied", False)
                final_key = hybrid_eval.get("final_candidate_key", global_key)

        total_latency_ms = base["t_global_ms"] + t_extra_ms

        return {
            "predicted_monument": final_key,
            "global_monument": global_key,
            "global_similarity": round(global_score, 4),
            "margin": base["margin"],
            "gatekeeper_score": round(gatekeeper_score, 4),
            "calibrated_confidence": base["calibrated_conf"],
            "decision_state": base["decision_state"],
            "top3_monuments": base["top3_monuments"],
            "is_decisive_fastpath": is_decisive_global,
            "local_clip_triggered": local_clip_triggered,
            "sift_triggered": sift_triggered,
            "override_applied": override_applied,
            "latency_ms": round(total_latency_ms, 2),
        }


def run_benchmark_on_dataset(runner: BenchmarkRunner, manifest_path: Path, dataset_name: str) -> Dict[str, Any]:
    with open(manifest_path, "r", encoding="utf-8") as f:
        m_data = json.load(f)
    records = m_data.get("records", [])
    logger.info(f"Extracting base evaluations for {dataset_name} ({len(records)} specimens)...")

    # Extract base evaluation for each specimen
    base_evals = []
    for idx, r in enumerate(records, 1):
        img_p = BASE_DIR / r["relative_path"]
        if not img_p.exists():
            continue
        base = runner.extract_specimen_base(img_p)
        base["record"] = r
        base_evals.append(base)
        if idx % 30 == 0 or idx == len(records):
            logger.info(f"Base extracted {idx}/{len(records)} specimens...")

    configs = ["global_only", "conditional_local_clip", "conditional_sift", "full_adaptive"]
    results_by_config: Dict[str, Any] = {}

    for cfg in configs:
        logger.info(f"Evaluating config: {cfg} across {len(base_evals)} specimens...")
        latencies: List[float] = []
        catalog_correct = 0
        catalog_top3_correct = 0
        catalog_mrr_sum = 0.0
        catalog_count = 0

        far_false_accepts = 0
        distractor_count = 0
        rejected_count = 0
        review_count = 0

        fastpath_count = 0
        local_clip_count = 0
        sift_count = 0
        override_count = 0

        per_monument: Dict[str, Dict[str, int]] = {}
        condition_performance: Dict[str, Dict[str, Any]] = {}

        for item in base_evals:
            r = item["record"]
            gt_key = r.get("monument_key") or r.get("ground_truth_label")
            is_distractor = gt_key in ["non_monument", "unknown_heritage"]
            cond = r.get("condition") or r.get("view_type") or "general"

            eval_res = runner.evaluate_config_on_specimen(item, cfg)
            pred = eval_res["predicted_monument"]
            top3 = eval_res["top3_monuments"]
            state = eval_res["decision_state"]
            lat = eval_res["latency_ms"]

            latencies.append(lat)
            if eval_res["is_decisive_fastpath"]:
                fastpath_count += 1
            if eval_res["local_clip_triggered"]:
                local_clip_count += 1
            if eval_res["sift_triggered"]:
                sift_count += 1
            if eval_res["override_applied"]:
                override_count += 1

            if state == "REVIEW_REQUIRED":
                review_count += 1

            # Condition tracking
            if cond not in condition_performance:
                condition_performance[cond] = {"total": 0, "correct": 0, "rejected": 0, "mean_lat": []}
            condition_performance[cond]["total"] += 1
            condition_performance[cond]["mean_lat"].append(lat)

            if is_distractor:
                distractor_count += 1
                if state in ["NON_MONUMENT_REJECTED", "UNKNOWN_HERITAGE_SPECIMEN"]:
                    rejected_count += 1
                    condition_performance[cond]["rejected"] += 1
                elif state == "VERIFIED_MATCH":
                    far_false_accepts += 1
            else:
                catalog_count += 1
                is_correct = (pred == gt_key)
                if is_correct:
                    catalog_correct += 1
                    condition_performance[cond]["correct"] += 1

                # Top-3 & MRR
                if gt_key in top3:
                    catalog_top3_correct += 1
                    rank = top3.index(gt_key) + 1
                    catalog_mrr_sum += 1.0 / rank

                # Per-monument tracking
                if gt_key not in per_monument:
                    per_monument[gt_key] = {"total": 0, "correct": 0, "top3": 0}
                per_monument[gt_key]["total"] += 1
                if is_correct:
                    per_monument[gt_key]["correct"] += 1
                if gt_key in top3:
                    per_monument[gt_key]["top3"] += 1

        total_specimens = len(latencies)
        top1_acc = round(catalog_correct / catalog_count, 4) if catalog_count > 0 else 0.0
        top3_acc = round(catalog_top3_correct / catalog_count, 4) if catalog_count > 0 else 0.0
        mrr = round(catalog_mrr_sum / catalog_count, 4) if catalog_count > 0 else 0.0
        far = round(far_false_accepts / distractor_count, 4) if distractor_count > 0 else 0.0
        rejection_rate = round(rejected_count / distractor_count, 4) if distractor_count > 0 else 0.0
        review_rate = round(review_count / total_specimens, 4) if total_specimens > 0 else 0.0

        lat_mean = round(float(np.mean(latencies)), 2)
        lat_median = round(float(np.median(latencies)), 2)
        lat_p95 = round(float(np.percentile(latencies, 95)), 2)

        cond_summary = {}
        for c_name, c_data in condition_performance.items():
            tot = c_data["total"]
            corr = c_data["correct"]
            rej = c_data["rejected"]
            cond_summary[c_name] = {
                "total": tot,
                "accuracy_or_rejection": round((corr + rej) / tot, 4),
                "mean_latency_ms": round(float(np.mean(c_data["mean_lat"])), 2),
            }

        monument_summary = {}
        for m_name, m_data in per_monument.items():
            tot = m_data["total"]
            corr = m_data["correct"]
            t3 = m_data["top3"]
            monument_summary[m_name] = {
                "total": tot,
                "top1_accuracy": round(corr / tot, 4) if tot > 0 else 0.0,
                "top3_accuracy": round(t3 / tot, 4) if tot > 0 else 0.0,
            }

        results_by_config[cfg] = {
            "top1_accuracy": top1_acc,
            "top3_accuracy": top3_acc,
            "mrr": mrr,
            "false_acceptance_rate": far,
            "rejection_rate": rejection_rate,
            "human_review_rate": review_rate,
            "catalog_specimens": catalog_count,
            "distractor_specimens": distractor_count,
            "total_specimens": total_specimens,
            "latency": {
                "mean_ms": lat_mean,
                "median_ms": lat_median,
                "p95_ms": lat_p95,
            },
            "execution_profile": {
                "decisive_fastpath_rate": round(fastpath_count / total_specimens, 4),
                "local_clip_triggered_rate": round(local_clip_count / total_specimens, 4),
                "sift_triggered_rate": round(sift_count / total_specimens, 4),
                "override_rate": round(override_count / total_specimens, 4),
            },
            "per_monument": monument_summary,
            "condition_breakdown": cond_summary,
        }

    return results_by_config


def main():
    runner = BenchmarkRunner()

    test_v2_results = run_benchmark_on_dataset(runner, TEST_V2_MANIFEST, "Independent Test Dataset v2 (N=55)")
    calib_v3_results = run_benchmark_on_dataset(runner, CALIB_V3_MANIFEST, "Calibration Expansion Dataset v3 (N=265)")

    final_report = {
        "title": "Phase 8.2 Comprehensive Adaptive Recognition & Robustness Benchmark",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "architectural_configuration": {
            "global_encoder": "openai/clip-vit-base-patch32",
            "vector_index": "FAISS IndexFlatIP (210 vectors)",
            "calibrator": "Platt Scaling (A=4.2622, B=-3.5748)",
            "local_features": "Multi-region Local CLIP + Quality-gated SIFT/RANSAC",
            "fastpath_enabled": True,
            "conservative_non_override_rule": True,
        },
        "independent_test_dataset_v2": {
            "dataset_size": 55,
            "results_by_configuration": test_v2_results,
        },
        "calibration_expansion_dataset_v3": {
            "dataset_size": 265,
            "results_by_configuration": calib_v3_results,
        },
    }

    with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Phase 8.2 Benchmark complete! Saved to {OUTPUT_REPORT_PATH.name}")


if __name__ == "__main__":
    main()
