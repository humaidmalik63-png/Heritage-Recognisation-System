"""
Phase 8.1: Threshold Optimization Engine
Project No. 30: Visual Heritage Recognition Platform (SIH 2025 - SIH25052)

Optimizes decision gatekeeper thresholds strictly on the Development Dataset.
Objective function penalizes incorrect VERIFIED_MATCH decisions heavily (10x penalty)
to guarantee curatorial safety and zero false claims on ambiguous heritage.

Saves: backend/threshold_optimization_report.json
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("threshold_optimization")

BASE_DIR = Path(__file__).resolve().parent
DEV_FEATURES_PATH = BASE_DIR / "dev_features_cache.json"
REPORT_PATH = BASE_DIR / "threshold_optimization_report.json"
CONFIG_PATH = BASE_DIR / "calibration_config.json"


def optimize_thresholds():
    if not DEV_FEATURES_PATH.exists():
        logger.error(f"Features cache not found at {DEV_FEATURES_PATH}. Run calibration first.")
        return

    with open(DEV_FEATURES_PATH, "r", encoding="utf-8") as f:
        features = json.load(f)

    logger.info(f"Loaded {len(features)} development specimen features for threshold optimization.")

    # Candidate grids
    sim_thresholds = [0.75, 0.78, 0.80, 0.82, 0.85]
    margin_thresholds = [0.03, 0.04, 0.05, 0.06, 0.08]
    gate_verified_thresholds = [0.50, 0.55, 0.60]
    gate_ambiguous_thresholds = [0.35, 0.40, 0.45]

    best_loss = float("inf")
    best_config = None
    best_metrics = None

    search_space = []
    for st in sim_thresholds:
        for mt in margin_thresholds:
            for gv in gate_verified_thresholds:
                for ga in gate_ambiguous_thresholds:
                    if ga < gv:
                        search_space.append((st, mt, gv, ga))

    logger.info(f"Evaluating {len(search_space)} threshold configurations...")

    for st, mt, gv, ga in search_space:
        true_verified = 0
        false_verified = 0
        uncertain_matches = 0
        unknown_rejections = 0
        false_rejections = 0
        curator_reviews = 0

        for r in features:
            top1_sim = r["top1_sim"]
            margin = r["margin"]
            gate = r["gatekeeper"]
            gt = r["ground_truth"]
            pred = r["pred_monument"]
            is_monument = gt not in ["non_monument", "unknown_heritage"]

            # Decision simulation matching backend/uncertainty.py
            if gate < ga and top1_sim < 0.70:
                decision = "NON_MONUMENT_REJECTED"
            elif gate >= gv and top1_sim >= st and margin >= mt:
                decision = "VERIFIED_MATCH"
            elif gate >= ga and top1_sim >= (st - 0.05) and margin < mt:
                decision = "UNCERTAIN_MATCH"
            elif gate >= ga and top1_sim < st:
                decision = "UNKNOWN_HERITAGE_SPECIMEN"
            else:
                decision = "REVIEW_REQUIRED"

            # Evaluate outcomes
            if decision == "VERIFIED_MATCH":
                if is_monument and pred == gt:
                    true_verified += 1
                else:
                    false_verified += 1
            elif decision == "UNCERTAIN_MATCH":
                uncertain_matches += 1
            elif decision == "UNKNOWN_HERITAGE_SPECIMEN":
                if gt == "unknown_heritage":
                    unknown_rejections += 1
                elif is_monument:
                    false_rejections += 1
            elif decision == "NON_MONUMENT_REJECTED":
                if gt == "non_monument":
                    unknown_rejections += 1
                elif is_monument:
                    false_rejections += 1
            elif decision == "REVIEW_REQUIRED":
                curator_reviews += 1

        # Curatorial Safety Loss Function:
        # Heavily penalizes false verified matches (10.0), false rejections (2.0), review overhead (0.2)
        # Rewards valid verified matches (-1.0) and accurate rejections (-0.5)
        loss = (
            10.0 * false_verified
            + 2.0 * false_rejections
            + 0.2 * curator_reviews
            - 1.0 * true_verified
            - 0.5 * unknown_rejections
        )

        if loss < best_loss:
            best_loss = loss
            best_config = {
                "confidence_threshold": st,
                "uncertainty_margin_threshold": mt,
                "gatekeeper_threshold_verified": gv,
                "gatekeeper_threshold_ambiguous": ga,
            }
            best_metrics = {
                "loss": round(loss, 3),
                "true_verified_matches": true_verified,
                "false_verified_matches": false_verified,
                "uncertain_matches": uncertain_matches,
                "correct_unknown_rejections": unknown_rejections,
                "false_rejections": false_rejections,
                "curator_reviews": curator_reviews,
                "false_acceptance_rate_pct": round(false_verified / max(true_verified + false_verified, 1) * 100.0, 2),
            }

    logger.info("Optimization complete!")
    logger.info(f"Optimal configuration: {best_config}")
    logger.info(f"Performance metrics: {best_metrics}")

    report = {
        "title": "Phase 8.1 Decision Gatekeeper Threshold Optimization",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": "calibration_development",
        "total_specimens_evaluated": len(features),
        "configurations_tested": len(search_space),
        "objective_function": "Loss = 10.0*FalseVerified + 2.0*FalseRejection + 0.2*Review - 1.0*TrueVerified - 0.5*Rejection",
        "optimal_thresholds": best_config,
        "optimal_metrics": best_metrics,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Update calibration_config.json with optimal thresholds
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg.update(best_config)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    logger.info(f"Saved threshold optimization report to {REPORT_PATH.name} and updated {CONFIG_PATH.name}.")


if __name__ == "__main__":
    optimize_thresholds()

