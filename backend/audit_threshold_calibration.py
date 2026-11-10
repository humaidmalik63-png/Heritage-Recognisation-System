"""
Phase 14.1 — Threshold Calibration Sweep on Calibration Dataset (v3)
Audits the Rule 1 boundary:
    top1_sim < sim_reject AND gatekeeper < gk_reject

Tuning is executed exclusively on calibration_dataset_v3 (265 specimens: 199 catalogue, 33 unknown, 33 non-monument)
without touching the untouched holdout test dataset (Split D).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

BASE_DIR = Path(__file__).resolve().parent
CALIB_CACHE_FILE = BASE_DIR / "datasets" / "calibration_v3_features_cache.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("threshold_sweep")


def run_threshold_sweep() -> Dict[str, Any]:
    with open(CALIB_CACHE_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    logger.info(f"Loaded {len(records)} calibration records from {CALIB_CACHE_FILE.name}")
    catalogue_recs = [r for r in records if r["ground_truth"] not in ["unknown_heritage", "non_monument"]]
    unknown_recs = [r for r in records if r["ground_truth"] == "unknown_heritage"]
    non_mon_recs = [r for r in records if r["ground_truth"] == "non_monument"]

    logger.info(f"Breakdown: Catalogue={len(catalogue_recs)}, Unknown={len(unknown_recs)}, Non-Monument={len(non_mon_recs)}")

    sim_range = [0.55, 0.60, 0.65, 0.68, 0.70, 0.72, 0.75, 0.80]
    gk_range = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55]

    sweep_results = []

    best_score = -1.0
    best_config = None

    for sim_thresh in sim_range:
        for gk_thresh in gk_range:
            # Evaluate arbitration on calibration cohort:
            # Rule 1: sim < sim_thresh AND gk < gk_thresh => NON_MONUMENT_REJECTED
            # Rule 2: sim >= 0.75 AND gk < gk_thresh => REVIEW_REQUIRED
            # Rule 3: gk >= 0.60 AND sim >= 0.78 AND margin >= 0.05 => VERIFIED_MATCH
            # Rule 4: gk >= 0.45 AND sim >= 0.70 AND margin < 0.05 => UNCERTAIN_MATCH
            # Rule 5: gk >= 0.45 AND sim < 0.78 => UNKNOWN_HERITAGE_SPECIMEN
            # Else: REVIEW_REQUIRED

            nm_rejected = 0
            nm_falsely_verified = 0
            cat_falsely_rejected = 0
            cat_verified = 0
            unk_detected = 0

            for r in non_mon_recs:
                sim = r["top1_sim"]
                gk = r["gatekeeper"]
                margin = r["margin"]

                if sim < sim_thresh and gk < gk_thresh:
                    nm_rejected += 1
                elif gk >= 0.60 and sim >= 0.78 and margin >= 0.05:
                    nm_falsely_verified += 1

            for r in catalogue_recs:
                sim = r["top1_sim"]
                gk = r["gatekeeper"]
                margin = r["margin"]

                if sim < sim_thresh and gk < gk_thresh:
                    cat_falsely_rejected += 1
                elif gk >= 0.60 and sim >= 0.78 and margin >= 0.05 and r["is_correct"] == 1:
                    cat_verified += 1

            for r in unknown_recs:
                sim = r["top1_sim"]
                gk = r["gatekeeper"]
                margin = r["margin"]

                if gk >= 0.45 and sim < 0.78:
                    unk_detected += 1
                elif gk >= 0.60 and sim >= 0.78 and margin >= 0.05:
                    nm_falsely_verified += 1

            # Metrics
            nm_rejection_acc = (nm_rejected / len(non_mon_recs)) * 100.0
            fnr = (cat_falsely_rejected / len(catalogue_recs)) * 100.0
            fpr = (nm_falsely_verified / (len(non_mon_recs) + len(unknown_recs))) * 100.0
            cat_recall = (cat_verified / len(catalogue_recs)) * 100.0
            unk_acc = (unk_detected / len(unknown_recs)) * 100.0

            # Combined objective score: Maximize rejection acc + unk acc - 10*FPR - 10*FNR
            objective = nm_rejection_acc + unk_acc - (10.0 * fpr) - (10.0 * fnr)

            result_entry = {
                "sim_threshold": sim_thresh,
                "gk_threshold": gk_thresh,
                "nm_rejection_acc_pct": round(nm_rejection_acc, 2),
                "fnr_pct": round(fnr, 2),
                "fpr_pct": round(fpr, 2),
                "unknown_acc_pct": round(unk_acc, 2),
                "catalogue_verified_pct": round(cat_recall, 2),
                "objective_score": round(objective, 2),
            }
            sweep_results.append(result_entry)

            if objective > best_score:
                best_score = objective
                best_config = result_entry

    print("\n" + "=" * 80)
    print("CALIBRATION THRESHOLD SWEEP SUMMARY (Grid size: 56 combinations)")
    print("=" * 80)
    print(f"Optimal Configuration on Calibration Set: {best_config}")
    print("\nSelected Key Operating Points:")
    print(f"{'Sim Thresh':<12} {'GK Thresh':<12} {'NM Reject %':<14} {'FNR %':<10} {'FPR %':<10} {'Objective':<10}")
    print("-" * 70)
    # Print sample points including 0.70 / 0.45
    for r in sweep_results:
        if r["sim_threshold"] in [0.65, 0.70, 0.75] and r["gk_threshold"] in [0.35, 0.40, 0.45, 0.50]:
            is_phase14 = " <-- Phase 14 Rule" if r["sim_threshold"] == 0.70 and r["gk_threshold"] == 0.45 else ""
            print(f"{r['sim_threshold']:<12.2f} {r['gk_threshold']:<12.2f} {r['nm_rejection_acc_pct']:<14.2f} {r['fnr_pct']:<10.2f} {r['fpr_pct']:<10.2f} {r['objective_score']:<10.2f}{is_phase14}")

    out_file = BASE_DIR / "phase_14_threshold_calibration_sweep.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"optimal": best_config, "all_results": sweep_results}, f, indent=2)
    logger.info(f"Saved sweep results to {out_file.name}")

    return {"optimal": best_config, "sweep": sweep_results}


if __name__ == "__main__":
    run_threshold_sweep()
