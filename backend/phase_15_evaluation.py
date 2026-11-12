"""
Phase 15 — Recognition Accuracy Evaluation (Augmented Index + Threshold Tuning)
===============================================================================
Measures top-1 accuracy, false-negative rate, and decision distribution on the
Cohort 1 test set using both the v1 (baseline) and v2 (augmented) FAISS indexes.

Run instructions:
    # Baseline (v1 index, original thresholds)
    python backend/phase_15_evaluation.py

    # Augmented index with tuned thresholds
    PHASE15_V2_INDEX=1 python backend/phase_15_evaluation.py
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

os.environ["TESTING"] = "1"

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from calibration import CalibrationEngine
from uncertainty import UncertaintyEngine, inspect_image_quality
from main import (
    BUNDLED_ASSET_MAP,
    INDEX_FILE, LABELS_FILE, AUGMENTED_INDEX_FILE, AUGMENTED_LABELS_FILE,
    CATALOGUE_100_FILE, CALIBRATION_CONFIG_FILE,
    evaluate_architectural_gatekeeper,
    initialize_backend_resources,
)

logger = logging.getLogger("phase_15_eval")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Test set paths ────────────────────────────────────────────────────────────
TEST_SET_DIR = BASE_DIR / "datasets" / "independent_final_test_v4"
V1_RESULTS_PATH = BASE_DIR / "phase_15_baseline_results.json"
V2_RESULTS_PATH = BASE_DIR / "phase_15_augmented_results.json"


def _load_test_specimens() -> List[Dict[str, Any]]:
    """Parse independent_final_test_v4 manifest into structured specimen list."""
    manifest_path = TEST_SET_DIR.parent / "independent_final_test_v4_manifest.json"
    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}")
        return []
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    specimens = []
    for entry in data.get("specimens", data if isinstance(data, list) else []):
        if isinstance(entry, dict):
            specimens.append({
                "file": entry.get("filename", entry.get("file", "")),
                "ground_truth": entry.get("ground_truth", entry.get("key", "")),
                "category": entry.get("category", "unknown"),
            })
    return specimens


def _find_image(fname: str) -> Optional[Path]:
    """Resolve a test image file path — try test set dir first, then bundled assets."""
    candidate = TEST_SET_DIR / fname
    if candidate.exists():
        return candidate
    key_guess = fname.replace(".jpg", "").replace("-", "_")
    asset_name = BUNDLED_ASSET_MAP.get(key_guess) or BUNDLED_ASSET_MAP.get(key_guess.split("_")[0])
    if asset_name:
        candidate = BASE_DIR / "assets" / "heritage" / asset_name
        if candidate.exists():
            return candidate
    return None


def run_evaluation(index_file: Path, labels_file: Path, result_path: Path,
                   engine_label: str) -> Dict[str, Any]:
    """Run full Cohort 1 evaluation against a given FAISS index."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Evaluating: {engine_label}")
    logger.info(f"Index: {index_file.name} ({faiss.read_index(str(index_file)).ntotal} vectors)")
    logger.info(f"{'='*60}")

    with open(labels_file, "r", encoding="utf-8") as f:
        labels = json.load(f)

    with open(CATALOGUE_100_FILE, "r", encoding="utf-8") as f:
        catalogue = json.load(f)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model.eval()

    faiss_idx = faiss.read_index(str(index_file))
    calib_engine = CalibrationEngine(CALIBRATION_CONFIG_FILE)
    unc_engine = UncertaintyEngine(calib_engine)
    quality_cfg = calib_engine.image_quality_config

    specimens = _load_test_specimens()
    results: List[Dict[str, Any]] = []

    correct_top1 = 0
    correct_top3 = 0
    fp_count = 0   # non-monument incorrectly VERIFIED_MATCH
    fn_count = 0   # monument incorrectly rejected or wrong candidate
    total_catalogue = 0
    total_distractor = 0
    decision_counts = {"VERIFIED_MATCH": 0, "UNCERTAIN_MATCH": 0,
                       "REVIEW_REQUIRED": 0, "NON_MONUMENT_REJECTED": 0,
                       "UNKNOWN_HERITAGE_SPECIMEN": 0}

    for spec in specimens:
        fname = spec["file"]
        gt = spec["ground_truth"]
        category = spec["category"]

        img_path = _find_image(fname)
        if img_path is None:
            logger.warning(f"Skipping {fname}: not found")
            continue

        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as exc:
            logger.warning(f"Cannot open {img_path}: {exc}")
            continue

        # Compute embedding
        inputs = clip_processor(images=img, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = clip_model.get_image_features(**inputs)
            tensor = outputs.pooler_output if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None else outputs
            if hasattr(tensor, "last_hidden_state"):
                tensor = tensor.last_hidden_state
            vec = tensor.cpu().detach().numpy().flatten().astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec = vec / norm

        # FAISS search k=3
        D, I = faiss_idx.search(np.expand_dims(vec, axis=0), 3)
        sims = D[0].tolist()
        indices = I[0].tolist()

        candidates = []
        for sim, idx_id in zip(sims, indices):
            if idx_id < 0:
                break
            label = labels[idx_id]
            candidates.append({
                "sim": float(sim),
                "monument_key": label["monument_key"],
                "monument_name": label.get("monument_name", label["monument_key"].replace("_", " ").title()),
                "index_id": int(idx_id),
            })

        top1 = candidates[0] if candidates else None
        top2 = candidates[1] if len(candidates) > 1 else None
        top3 = candidates[2] if len(candidates) > 2 else None

        # Gatekeeper score
        gatekeeper_score = evaluate_architectural_gatekeeper(vec)

        # Quality check
        quality = inspect_image_quality(img, quality_cfg)

        # Decision via uncertainty engine
        margin = (top1["sim"] - top2["sim"]) if top2 else top1["sim"]
        top1_sim = top1["sim"] if top1 else 0.0
        top1_key = top1["monument_key"] if top1 else None

        decision = unc_engine._arbitrate_decision(
            top1_sim=top1_sim,
            top2_sim=top2["sim"] if top2 else 0.0,
            margin=margin,
            gatekeeper_score=float(gatekeeper_score),
            gps=None,
            quality=quality,
            sim_threshold=calib_engine.confidence_threshold,
            margin_threshold=calib_engine.uncertainty_margin_threshold,
            gatekeeper_verified=calib_engine.gatekeeper_threshold_verified,
            gatekeeper_ambiguous=calib_engine.gatekeeper_threshold_ambiguous,
            gatekeeper_rejection=calib_engine.gatekeeper_threshold_rejection,
            top1_key=top1_key,
        )

        is_match = (gt and gt != "unknown" and top1_key == gt) if top1_key else False
        if is_match:
            correct_top1 += 1
        if top3 and gt and any(c["monument_key"] == gt for c in candidates[:3]):
            correct_top3 += 1

        if category in ("non_monument", "distractor"):
            total_distractor += 1
            if decision.value == "VERIFIED_MATCH":
                fp_count += 1
        elif gt and gt not in ("out_of_catalog", "unknown", ""):
            total_catalogue += 1
            if not is_match:
                fn_count += 1

        decision_counts[decision.value] = decision_counts.get(decision.value, 0) + 1

        results.append({
            "file": fname,
            "ground_truth": gt,
            "category": category,
            "decision": decision.value,
            "top1_key": top1_key,
            "top1_name": top1["monument_name"] if top1 else None,
            "top1_sim": round(top1_sim, 4),
            "top2_key": top2["monument_key"] if top2 else None,
            "top2_name": top2["monument_name"] if top2 else None,
            "top2_sim": round(top2["sim"], 4) if top2 else None,
            "top3_key": top3["monument_key"] if top3 else None,
            "top3_name": top3["monument_name"] if top3 else None,
            "top3_sim": round(top3["sim"], 4) if top3 else None,
            "margin": round(margin, 4),
            "gatekeeper_score": round(float(gatekeeper_score), 4),
            "latency_ms": 0,
        })

    total = len(results)
    summary = {
        "engine_label": engine_label,
        "total_specimens": total,
        "catalog_specimens": total_catalogue,
        "distractor_specimens": total_distractor,
        "top1_accuracy_pct": round(correct_top1 / total_catalogue * 100, 2) if total_catalogue else 0,
        "top3_accuracy_pct": round(correct_top3 / total_catalogue * 100, 2) if total_catalogue else 0,
        "false_positive_rate_pct": round(fp_count / total_distractor * 100, 2) if total_distractor else 0,
        "false_negative_rate_pct": round(fn_count / total_catalogue * 100, 2) if total_catalogue else 0,
        "verified_count": decision_counts.get("VERIFIED_MATCH", 0),
        "uncertain_count": decision_counts.get("UNCERTAIN_MATCH", 0),
        "review_required_count": decision_counts.get("REVIEW_REQUIRED", 0),
        "non_monument_rejected_count": decision_counts.get("NON_MONUMENT_REJECTED", 0),
        "unknown_heritage_count": decision_counts.get("UNKNOWN_HERITAGE_SPECIMEN", 0),
    }

    output = {"summary": summary, "results": results}
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    logger.info(f"Results saved → {result_path}")
    return output


def compare_and_report(v1_out: Dict, v2_out: Dict) -> None:
    """Print side-by-side comparison of v1 vs v2 results."""
    s1 = v1_out["summary"]
    s2 = v2_out["summary"]
    print("\n" + "=" * 76)
    print("  PHASE 15 EVALUATION REPORT — V1 (baseline) vs V2 (augmented)")
    print("=" * 76)
    header = f"  {'Metric':<44} {'V1 (Baseline)':>16} {'V2 (Augmented)':>16} {'Delta':>10}"
    print(header)
    print("  " + "-" * 86)
    rows = [
        ("Top-1 Catalogue Accuracy (%)", s1["top1_accuracy_pct"], s2["top1_accuracy_pct"]),
        ("Top-3 Catalogue Accuracy (%)", s1["top3_accuracy_pct"], s2["top3_accuracy_pct"]),
        ("False Negative Rate (%)", s1["false_negative_rate_pct"], s2["false_negative_rate_pct"]),
        ("False Positive Rate (%)", s1["false_positive_rate_pct"], s2["false_positive_rate_pct"]),
        ("VERIFIED_MATCH count", s1["verified_count"], s2["verified_count"]),
        ("UNCERTAIN_MATCH count", s1["uncertain_count"], s2["uncertain_count"]),
        ("REVIEW_REQUIRED count", s1["review_required_count"], s2["review_required_count"]),
        ("NON_MONUMENT_REJECTED count", s1["non_monument_rejected_count"], s2["non_monument_rejected_count"]),
    ]
    for label, v1v, v2v in rows:
        delta = v2v - v1v
        sign = "+" if delta > 0 else ""
        bar = "█" * max(0, int(abs(delta))) if "%" in label else ""
        print(f"  {label:<44} {v1v:>15.2f}  {v2v:>15.2f}  {sign}{delta:>9.2f} {bar}")
    print("=" * 76)
    print(f"  Total specimens evaluated : {s1['total_specimens']}")
    print(f"  Catalogue specimens       : {s1['catalog_specimens']}")
    print(f"  Distractor specimens      : {s1['distractor_specimens']}")
    print()


if __name__ == "__main__":
    use_v2 = os.environ.get("PHASE15_V2_INDEX", "0").lower() in ("1", "true", "yes")

    runs: List[tuple] = [
        (INDEX_FILE, LABELS_FILE, V1_RESULTS_PATH, "v1-Baseline"),
    ]
    if use_v2:
        if not AUGMENTED_INDEX_FILE.exists():
            logger.error(f"Augmented index not found at {AUGMENTED_INDEX_FILE}.")
            logger.info("Build it first: python backend/phase_15_augment_index.py")
            sys.exit(1)
        runs.append((AUGMENTED_INDEX_FILE, AUGMENTED_LABELS_FILE, V2_RESULTS_PATH, "v2-Augmented"))
    else:
        if AUGMENTED_INDEX_FILE.exists():
            logger.info(f"AUGMENTED_INDEX=1 set but no augmented index found. Run phase_15_augment_index.py first.")

    outputs = []
    for idx_f, lab_f, res_f, label in runs:
        out = run_evaluation(idx_f, lab_f, res_f, label)
        outputs.append(out)

    if len(outputs) >= 2:
        compare_and_report(outputs[0], outputs[1])
    elif len(outputs) == 1:
        s = outputs[0]["summary"]
        print(f"\nSingle run result ({outputs[0]['summary']['engine_label']}):")
        print(f"  Top-1 accuracy : {s['top1_accuracy_pct']}%")
        print(f"  FNR            : {s['false_negative_rate_pct']}%  |  FPR: {s['false_positive_rate_pct']}%")
