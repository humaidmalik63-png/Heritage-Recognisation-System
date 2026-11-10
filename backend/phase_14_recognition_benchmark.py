"""
Phase 14 Recognition Pipeline Evaluation & Quality Benchmark
Evaluates:
- Top-1 and Top-3 accuracy on catalog monuments
- Close-up and architectural detail resilience
- Low-resolution and occlusion resilience
- Similar monument discrimination (e.g. Qutub vs Charminar)
- False Positive Rate (FPR) on non-monuments and out-of-catalog specimens
- False Negative Rate (FNR) on catalog monuments
- Unknown detection performance
- Per-stage latency metrics
"""

import io
import json
import logging
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
sys.path.insert(0, str(BASE_DIR))

from calibration import CalibrationEngine
from catalogue_service import get_catalogue_100, check_catalogue_membership
from uncertainty import DecisionState, UncertaintyEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase14_eval")

INDEX_FILE = BASE_DIR / "monument_index.faiss"
LABELS_FILE = BASE_DIR / "monument_labels.json"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
CALIB_FILE = BASE_DIR / "calibration_config.json"

ARCH_PROMPTS = [
    "a photo of a historic monument, ancient temple, palace, or fort architecture",
    "a photo of a famous heritage building or ancient architectural landmark",
    "a photo of an ordinary everyday object, person, animal, food, document, or non-architectural scene",
    "a photo of modern interior, paperwork, receipt, household item, or common vehicle",
]

class PipelineEvaluator:
    def __init__(self):
        logger.info("Initializing Evaluation Pipeline (CPU)...")
        self.device = "cpu"
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.model.eval()

        # Precompute gatekeeper text embeddings
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
        t0 = time.perf_counter()
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
        t_gk = time.perf_counter()
        gatekeeper_score = self.evaluate_gatekeeper(img_vec)
        gk_ms = (time.perf_counter() - t_gk) * 1000.0

        # 3. FAISS Search
        t_faiss = time.perf_counter()
        query_matrix = np.expand_dims(img_vec, axis=0).astype(np.float32)
        raw_distances, raw_indices = self.faiss_index.search(query_matrix, 15)
        faiss_ms = (time.perf_counter() - t_faiss) * 1000.0

        # 4. Uncertainty Arbitration
        t_unc = time.perf_counter()
        uncertainty_res = self.uncertainty_engine.evaluate(
            image=image_rgb,
            gatekeeper_score=gatekeeper_score,
            raw_distances=raw_distances,
            raw_indices=raw_indices,
            labels=self.labels,
            metadata=self.metadata,
        )
        unc_ms = (time.perf_counter() - t_unc) * 1000.0
        total_ms = (time.perf_counter() - t0) * 1000.0

        top_candidates = uncertainty_res.top_candidates
        top1 = top_candidates[0] if len(top_candidates) > 0 else None
        top2 = top_candidates[1] if len(top_candidates) > 1 else None
        top3 = top_candidates[2] if len(top_candidates) > 2 else None

        return {
            "file": img_path.name,
            "decision": uncertainty_res.decision.value,
            "top1_key": top1.monument_key if top1 else None,
            "top1_name": top1.monument_name if top1 else None,
            "top1_sim": top1.max_similarity if top1 else 0.0,
            "top2_key": top2.monument_key if top2 else None,
            "top2_name": top2.monument_name if top2 else None,
            "top2_sim": top2.max_similarity if top2 else 0.0,
            "top3_key": top3.monument_key if top3 else None,
            "top3_name": top3.monument_name if top3 else None,
            "top3_sim": top3.max_similarity if top3 else 0.0,
            "margin": uncertainty_res.similarity_margin,
            "gatekeeper_score": round(gatekeeper_score, 4),
            "calibrated_probability": uncertainty_res.calibrated_probability,
            "latency": {
                "clip_ms": round(clip_ms, 2),
                "gatekeeper_ms": round(gk_ms, 2),
                "faiss_ms": round(faiss_ms, 2),
                "uncertainty_ms": round(unc_ms, 2),
                "total_ms": round(total_ms, 2),
            }
        }

def run_evaluation():
    evaluator = PipelineEvaluator()

    # Define test suite:
    # Category 1: Known Catalogue Monuments (Ground Truth = monument_key)
    # Category 2: Close-up / Architectural Details (Ground Truth = monument_key)
    # Category 3: Similar Monument Pairs
    # Category 4: Out of Catalog / Unindexed (Ground Truth = out_of_catalog)
    # Category 5: Non-Monuments (Ground Truth = non_monument)

    test_items = []

    # 1. Standard known monuments from assets & split_d
    standard_catalog = [
        ("backend/assets/heritage/taj-mahal.jpg", "taj_mahal", "standard_catalog"),
        ("backend/assets/heritage/petra.jpg", "petra", "standard_catalog"),
        ("backend/assets/heritage/colosseum.jpg", "colosseum", "standard_catalog"),
        ("backend/assets/heritage/charminar.jpg", "charminar", "standard_catalog"),
        ("backend/assets/heritage/brihadeeswarar.jpg", "brihadeeswarar_temple", "standard_catalog"),
        ("backend/assets/heritage/hawa-mahal.jpg", "hawa_mahal", "standard_catalog"),
        ("backend/assets/heritage/konark-sun-temple.jpg", "konark_sun_temple", "standard_catalog"),
        ("backend/assets/heritage/qutub-minar.jpg", "qutub_minar", "standard_catalog"),
        ("backend/assets/heritage/hampi.jpg", "hampi_stone_chariot", "standard_catalog"),
        ("backend/assets/heritage/mysore-palace.jpg", "mysore_palace", "standard_catalog"),
        ("backend/assets/heritage/golden-temple.jpg", "golden_temple", "standard_catalog"),
        ("backend/assets/heritage/ajanta-caves.jpg", "ajanta_caves", "standard_catalog"),
        ("backend/datasets/phase_8_5c_ooc_eval/big_ben.jpg", "big_ben", "standard_catalog"),
        ("backend/datasets/phase_8_5c_ooc_eval/statue_of_liberty.jpg", "statue_of_liberty", "standard_catalog"),
    ]
    for p, gt, cat in standard_catalog:
        if Path(p).exists():
            test_items.append({"path": Path(p), "ground_truth": gt, "category": cat})

    # 2. Architectural Close-Ups & Details
    detail_specimens = [
        ("backend/datasets/local_feature_eval/feat_taj_jali_02.jpg", "taj_mahal", "architectural_detail"),
        ("backend/datasets/local_feature_eval/feat_taj_pietradura_01.jpg", "taj_mahal", "architectural_detail"),
        ("backend/datasets/local_feature_eval/feat_hawa_jharokha_01.jpg", "hawa_mahal", "architectural_detail"),
        ("backend/datasets/local_feature_eval/feat_konark_wheel_01.jpg", "konark_sun_temple", "architectural_detail"),
        ("backend/datasets/local_feature_eval/feat_qutub_balcony_02.jpg", "qutub_minar", "architectural_detail"),
        ("backend/datasets/local_feature_eval/feat_brih_vimana_tier_01.jpg", "brihadeeswarar_temple", "architectural_detail"),
        ("backend/datasets/local_feature_eval/feat_sanchi_torana_01.jpg", "sanchi_stupa", "architectural_detail"),
        ("backend/datasets/local_feature_eval/feat_charminar_stucco_01.jpg", "charminar", "architectural_detail"),
    ]
    for p, gt, cat in detail_specimens:
        if Path(p).exists():
            test_items.append({"path": Path(p), "ground_truth": gt, "category": cat})

    # 3. Challenging Conditions: Low-res & Partial Occlusion
    challenging_specimens = [
        ("backend/datasets/local_feature_eval/feat_qutub_lowres_03.jpg", "qutub_minar", "low_resolution"),
        ("backend/datasets/local_feature_eval/feat_charminar_occluded_02.jpg", "charminar", "partially_occluded"),
        ("backend/datasets/local_feature_eval/feat_sanchi_partial_03.jpg", "sanchi_stupa", "partially_occluded"),
        ("backend/datasets/independent_final_test_v4/split_d_012_charminar.jpg", "charminar", "angled_view"),
        ("backend/datasets/independent_final_test_v4/split_d_034_qutub_minar.jpg", "qutub_minar", "angled_view"),
        ("backend/datasets/independent_final_test_v4/split_d_046_taj_mahal.jpg", "taj_mahal", "perspective_angle"),
    ]
    for p, gt, cat in challenging_specimens:
        if Path(p).exists():
            test_items.append({"path": Path(p), "ground_truth": gt, "category": cat})

    # 4. Out-of-Catalog / Unindexed Monuments
    ooc_specimens = [
        ("backend/datasets/phase_8_5f_specimens/ordinary_building.jpg", "out_of_catalog", "unindexed_ordinary"),
    ]
    for p, gt, cat in ooc_specimens:
        if Path(p).exists():
            test_items.append({"path": Path(p), "ground_truth": gt, "category": cat})

    # 5. Non-Monument Distractors
    non_monument_specimens = [
        ("backend/datasets/local_feature_eval/feat_nonmon_glass_01.jpg", "non_monument", "non_monument"),
        ("backend/datasets/local_feature_eval/feat_nonmon_rock_02.jpg", "non_monument", "non_monument"),
        ("backend/datasets/phase_8_5f_specimens/mathematics_paper.jpg", "non_monument", "non_monument"),
        ("backend/datasets/receipt_distractor.jpg", "non_monument", "non_monument"),
        ("backend/datasets/independent_final_test_v4/split_d_062_non_monument.jpg", "non_monument", "non_monument"),
        ("backend/datasets/independent_final_test_v4/split_d_063_non_monument.jpg", "non_monument", "non_monument"),
        ("backend/datasets/independent_final_test_v4/split_d_090_non_monument.jpg", "non_monument", "non_monument"),
    ]
    for p, gt, cat in non_monument_specimens:
        if Path(p).exists():
            test_items.append({"path": Path(p), "ground_truth": gt, "category": cat})

    logger.info(f"Loaded {len(test_items)} evaluation specimens across 5 categories.")

    # Execution
    results = []
    latencies = []
    for item in test_items:
        res = evaluator.run_image(item["path"])
        res["ground_truth"] = item["ground_truth"]
        res["category"] = item["category"]
        results.append(res)
        latencies.append(res["latency"]["total_ms"])

    # Metric Calculations
    # 1. Catalogue items
    catalog_items = [r for r in results if r["ground_truth"] not in ["out_of_catalog", "non_monument"]]
    top1_correct = sum(1 for r in catalog_items if r["top1_key"] == r["ground_truth"])
    top3_correct = sum(1 for r in catalog_items if r["ground_truth"] in [r["top1_key"], r["top2_key"], r["top3_key"]])
    top1_acc = (top1_correct / len(catalog_items)) * 100.0 if catalog_items else 0.0
    top3_acc = (top3_correct / len(catalog_items)) * 100.0 if catalog_items else 0.0

    # 2. False Positives: non_monument or out_of_catalog declared VERIFIED_MATCH
    distractors = [r for r in results if r["ground_truth"] in ["out_of_catalog", "non_monument"]]
    false_positives = sum(1 for r in distractors if r["decision"] == "VERIFIED_MATCH")
    fpr = (false_positives / len(distractors)) * 100.0 if distractors else 0.0

    # 3. False Negatives: catalogue items declared NON_MONUMENT_REJECTED or UNKNOWN when they are standard
    standard_items = [r for r in results if r["category"] == "standard_catalog"]
    false_negatives = sum(1 for r in standard_items if r["decision"] in ["NON_MONUMENT_REJECTED", "UNKNOWN_HERITAGE_SPECIMEN"])
    fnr = (false_negatives / len(standard_items)) * 100.0 if standard_items else 0.0

    # 4. Non-monument rejection accuracy
    non_mon_items = [r for r in results if r["ground_truth"] == "non_monument"]
    non_mon_rejected = sum(1 for r in non_mon_items if r["decision"] == "NON_MONUMENT_REJECTED")
    non_mon_acc = (non_mon_rejected / len(non_mon_items)) * 100.0 if non_mon_items else 0.0

    # 5. Out of catalog unknown detection
    ooc_items = [r for r in results if r["ground_truth"] == "out_of_catalog"]
    ooc_unknown = sum(1 for r in ooc_items if r["decision"] in ["UNKNOWN_HERITAGE_SPECIMEN", "REVIEW_REQUIRED"])
    ooc_acc = (ooc_unknown / len(ooc_items)) * 100.0 if ooc_items else 0.0

    metrics = {
        "total_specimens": len(results),
        "catalog_specimens": len(catalog_items),
        "distractor_specimens": len(distractors),
        "top1_accuracy_pct": round(top1_acc, 2),
        "top3_accuracy_pct": round(top3_acc, 2),
        "false_positive_rate_pct": round(fpr, 2),
        "false_negative_rate_pct": round(fnr, 2),
        "non_monument_rejection_accuracy_pct": round(non_mon_acc, 2),
        "out_of_catalog_unknown_accuracy_pct": round(ooc_acc, 2),
        "average_latency_ms": round(float(np.mean(latencies)), 2),
        "median_latency_ms": round(float(np.median(latencies)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
    }

    print("\n" + "="*70)
    print("PHASE 14 RECOGNITION QUALITY BENCHMARK RESULTS")
    print("="*70)
    print(f"Total Evaluated Specimens:   {metrics['total_specimens']}")
    print(f"Top-1 Catalogue Accuracy:    {metrics['top1_accuracy_pct']}% ({top1_correct}/{len(catalog_items)})")
    print(f"Top-3 Catalogue Accuracy:    {metrics['top3_accuracy_pct']}% ({top3_correct}/{len(catalog_items)})")
    print(f"False Positive Rate (FPR):   {metrics['false_positive_rate_pct']}% ({false_positives}/{len(distractors)})")
    print(f"False Negative Rate (FNR):   {metrics['false_negative_rate_pct']}% ({false_negatives}/{len(standard_items)})")
    print(f"Non-Monument Rejection Acc:  {metrics['non_monument_rejection_accuracy_pct']}% ({non_mon_rejected}/{len(non_mon_items)})")
    print(f"Out-of-Catalog Unknown Acc:  {metrics['out_of_catalog_unknown_accuracy_pct']}% ({ooc_unknown}/{len(ooc_items)})")
    print(f"Average Total Latency:       {metrics['average_latency_ms']} ms")
    print(f"Median Latency:              {metrics['median_latency_ms']} ms")
    print(f"95th Percentile Latency:     {metrics['p95_latency_ms']} ms")
    print("="*70)

    # Save detailed evaluation JSON
    eval_output_file = BASE_DIR / "phase_14_evaluation_results.json"
    with open(eval_output_file, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "detailed_results": results}, f, indent=2)
    print(f"Saved complete evaluation dataset results to {eval_output_file}")

    return metrics

if __name__ == "__main__":
    run_evaluation()
