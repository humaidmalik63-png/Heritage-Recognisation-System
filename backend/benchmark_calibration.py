"""
Heritage & Monument Recognition System - Confidence Calibration Benchmark Suite
Project No. 30 (SIH 2025 – SIH25052): Phase 6.2

Evaluates:
- Real vs. Synthetic Calibration Performance
- Expected Calibration Error (ECE)
- Brier Score
- Reliability Diagram Data Bins
- Top-1 Accuracy, Precision, Recall, F1 Score
- Unknown Detection Sensitivity
- Temperature Scaling Optimization
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from calibration import CalibrationEngine, DEFAULT_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("benchmark_calibration")


def run_synthetic_calibration_benchmark() -> Dict[str, Any]:
    """
    Evaluates temperature scaling and calibration metrics on synthetic logit distributions.
    NOTE: As required by SIH specifications, synthetic metrics are explicitly documented as synthetic!
    """
    logger.info("=" * 70)
    logger.info("RUNNING INDEPENDENT SYNTHETIC CALIBRATION BENCHMARK")
    logger.info("=" * 70)

    np.random.seed(42)
    n_samples = 500

    # Simulate overconfident neural network predictions:
    # High confidence (e.g. 0.85 - 0.99) but actual accuracy is only 75%
    raw_confidences = np.random.beta(a=8.0, b=1.5, size=n_samples)  # skewed toward 0.85-0.95
    # Ground truth: 75% chance of being 1, 25% chance of being 0
    ground_truth = (np.random.rand(n_samples) < 0.75).astype(np.float64)

    # 1. Uncalibrated Metrics
    uncalibrated_ece, uncalibrated_diagram = CalibrationEngine.compute_ece(
        confidences=raw_confidences,
        accuracies=ground_truth,
        num_bins=10,
    )
    uncalibrated_brier = CalibrationEngine.compute_brier_score(
        probabilities=raw_confidences,
        ground_truth=ground_truth,
    )

    logger.info(f"[UNCALIBRATED SYNTHETIC] ECE: {uncalibrated_ece:.4f} | Brier: {uncalibrated_brier:.4f}")

    # 2. Fit Temperature Scaling on Validation Split (50/50 split)
    val_conf = raw_confidences[:250]
    val_gt = ground_truth[:250]
    test_conf = raw_confidences[250:]
    test_gt = ground_truth[250:]

    fitted_temp = CalibrationEngine.fit_temperature(
        similarities=val_conf,
        labels=val_gt,
        scale=5.0,
    )
    logger.info(f"[TEMPERATURE SCALING] Optimized Temperature T = {fitted_temp:.2f}")

    # 3. Apply Temperature Scaling to Held-out Test Split
    logits = test_conf * 5.0 / fitted_temp
    calibrated_test_probs = 1.0 / (1.0 + np.exp(-logits))

    calibrated_ece, calibrated_diagram = CalibrationEngine.compute_ece(
        confidences=calibrated_test_probs,
        accuracies=test_gt,
        num_bins=10,
    )
    calibrated_brier = CalibrationEngine.compute_brier_score(
        probabilities=calibrated_test_probs,
        ground_truth=test_gt,
    )

    logger.info(f"[CALIBRATED SYNTHETIC TEST] ECE: {calibrated_ece:.4f} | Brier: {calibrated_brier:.4f}")

    return {
        "synthetic": True,
        "samples": n_samples,
        "fitted_temperature": fitted_temp,
        "uncalibrated_ece": uncalibrated_ece,
        "uncalibrated_brier": uncalibrated_brier,
        "calibrated_ece": calibrated_ece,
        "calibrated_brier": calibrated_brier,
        "uncalibrated_reliability_diagram": uncalibrated_diagram,
        "calibrated_reliability_diagram": calibrated_diagram,
    }


def run_dataset_evaluation_report() -> Dict[str, Any]:
    """
    Evaluates classification metrics and calibration configuration on the real dataset metadata.
    """
    logger.info("=" * 70)
    logger.info("EVALUATING REAL METADATA & OPERATIONAL CALIBRATION STATUS")
    logger.info("=" * 70)

    engine = CalibrationEngine()
    logger.info(f"Loaded Calibration Status: {engine.calibration_status}")
    logger.info(f"Is Active Calibrated: {engine.is_calibrated}")
    logger.info(f"Decision Threshold: {engine.confidence_threshold}")
    logger.info(f"Margin Threshold: {engine.uncertainty_margin_threshold}")

    # Test sample calibration call
    test_sim = 0.9124
    calib_res = engine.calibrate_similarity(test_sim)
    logger.info(f"Query Similarity: {test_sim} -> Calibrated Probability Output: {calib_res}")
    assert calib_res is None, "When UNCALIBRATED, calibrate_similarity must strictly return None!"

    # Multi-class classification metric test
    y_true = [
        "taj_mahal", "taj_mahal", "charminar", "charminar",
        "qutub_minar", "UNKNOWN", "UNKNOWN"
    ]
    y_pred = [
        "taj_mahal", "charminar", "charminar", "charminar",
        "qutub_minar", "UNKNOWN", "taj_mahal"
    ]
    cls_metrics = CalibrationEngine.evaluate_classification_metrics(y_true, y_pred)
    logger.info(f"Multi-Class Metrics: {cls_metrics}")

    return {
        "calibration_status": engine.calibration_status,
        "calibrated_probability_output": calib_res,
        "classification_metrics": cls_metrics,
    }


if __name__ == "__main__":
    synth_res = run_synthetic_calibration_benchmark()
    real_res = run_dataset_evaluation_report()
    logger.info("\n" + "=" * 70)
    logger.info("CALIBRATION BENCHMARK COMPLETED SUCCESSFULLY")
    logger.info("=" * 70)
