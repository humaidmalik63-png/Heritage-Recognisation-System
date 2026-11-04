"""
Heritage & Monument Recognition System - Confidence Calibration Engine
Project No. 30 (SIH 2025 – SIH25052): Phase 6.2

Addresses the fundamental machine learning invariant:
FAISS cosine similarity is NOT a calibrated probability.

Provides:
- Temperature scaling architecture
- Expected Calibration Error (ECE) computation
- Brier score calculation
- Reliability diagram bin aggregation
- Multi-class classification metrics (Accuracy, Precision, Recall, F1, Unknown detection)
- Safe handling of UNCALIBRATED states (returns None for calibrated probability)
"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("calibration_engine")

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "method": "temperature_scaling",
    "calibration_status": "UNCALIBRATED",
    "temperature": 1.0,
    "confidence_threshold": 0.80,
    "uncertainty_margin_threshold": 0.05,
    "gatekeeper_threshold_verified": 0.55,
    "gatekeeper_threshold_ambiguous": 0.45,
    "gatekeeper_scale": 18.0,
    "geo_boost_distance_km": 5.0,
    "geo_conflict_distance_km": 150.0,
    "image_quality": {
        "min_dimension": 200,
        "min_total_pixels": 60000,
        "blur_laplacian_threshold": 35.0,
        "exposure_low_threshold": 25.0,
        "exposure_high_threshold": 230.0,
    },
    "metrics": {
        "dataset_size": 40,
        "calibration_samples": 0,
        "test_samples": 0,
        "ece": None,
        "brier_score": None,
        "notes": "Default uncalibrated configuration.",
    },
}


class CalibrationEngine:
    """
    Manages probability calibration, threshold configuration, and calibration metrics.
    Guarantees that raw cosine similarity is never masqueraded as empirical probability.
    """

    def __init__(self, config_source: Optional[Union[str, Path, Dict[str, Any]]] = None):
        self.config: Dict[str, Any] = self._load_and_validate_config(config_source)

    def _load_and_validate_config(
        self, config_source: Optional[Union[str, Path, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Loads and validates calibration configuration. Falls back gracefully if malformed."""
        if config_source is None:
            config_path = Path(__file__).resolve().parent / "calibration_config.json"
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        return self._sanitize_config(loaded)
                except Exception as exc:
                    logger.warning(f"Error loading calibration_config.json ({exc}). Using defaults.")
                    return dict(DEFAULT_CONFIG)
            return dict(DEFAULT_CONFIG)

        if isinstance(config_source, dict):
            return self._sanitize_config(config_source)

        if isinstance(config_source, (str, Path)):
            path = Path(config_source)
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        return self._sanitize_config(loaded)
                except Exception as exc:
                    logger.warning(f"Malformed config at {path} ({exc}). Using defaults.")
                    return dict(DEFAULT_CONFIG)
            logger.warning(f"Config path {path} does not exist. Using defaults.")
            return dict(DEFAULT_CONFIG)

        return dict(DEFAULT_CONFIG)

    def _sanitize_config(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures all required fields and valid types exist in the config."""
        clean = dict(DEFAULT_CONFIG)
        if not isinstance(raw, dict):
            return clean

        for key in ["version", "method", "calibration_status"]:
            if key in raw and isinstance(raw[key], str):
                clean[key] = raw[key]

        for float_key in [
            "temperature",
            "confidence_threshold",
            "uncertainty_margin_threshold",
            "gatekeeper_threshold_verified",
            "gatekeeper_threshold_ambiguous",
            "gatekeeper_scale",
            "geo_boost_distance_km",
            "geo_conflict_distance_km",
        ]:
            if float_key in raw and isinstance(raw[float_key], (int, float)):
                clean[float_key] = float(raw[float_key])

        if "image_quality" in raw and isinstance(raw["image_quality"], dict):
            iq = clean["image_quality"]
            for q_key, val in raw["image_quality"].items():
                if isinstance(val, (int, float)):
                    iq[q_key] = val
            clean["image_quality"] = iq

        if "metrics" in raw and isinstance(raw["metrics"], dict):
            clean["metrics"] = raw["metrics"]

        return clean

    @property
    def is_calibrated(self) -> bool:
        """True if the model has a validated, active calibration mapping."""
        return self.config.get("calibration_status") == "CALIBRATED"

    @property
    def calibration_status(self) -> str:
        return self.config.get("calibration_status", "UNCALIBRATED")

    @property
    def temperature(self) -> float:
        return float(self.config.get("temperature", 1.0))

    @property
    def confidence_threshold(self) -> float:
        return float(self.config.get("confidence_threshold", 0.80))

    @property
    def uncertainty_margin_threshold(self) -> float:
        return float(self.config.get("uncertainty_margin_threshold", 0.05))

    @property
    def gatekeeper_threshold_verified(self) -> float:
        return float(self.config.get("gatekeeper_threshold_verified", 0.55))

    @property
    def gatekeeper_threshold_ambiguous(self) -> float:
        return float(self.config.get("gatekeeper_threshold_ambiguous", 0.45))

    @property
    def geo_boost_distance_km(self) -> float:
        return float(self.config.get("geo_boost_distance_km", 5.0))

    @property
    def geo_conflict_distance_km(self) -> float:
        return float(self.config.get("geo_conflict_distance_km", 150.0))

    @property
    def image_quality_config(self) -> Dict[str, Any]:
        return self.config.get("image_quality", DEFAULT_CONFIG["image_quality"])

    def calibrate_similarity(
        self, similarity: float, logits: Optional[np.ndarray] = None
    ) -> Optional[float]:
        """
        Calibrates similarity to a posterior probability.
        If calibration_status is UNCALIBRATED, strictly returns None to prevent
        masquerading cosine similarity as an empirical probability.
        """
        if not self.is_calibrated:
            return None

        # Temperature scaling on scaled cosine logit
        T = max(self.temperature, 1e-4)
        if logits is not None and len(logits) > 0:
            # Softmax over temperature-scaled logits
            scaled = logits / T
            exp_scaled = np.exp(scaled - np.max(scaled))
            probs = exp_scaled / np.sum(exp_scaled)
            return float(round(probs[0], 4))

        # Sigmoid scaling on similarity margin if single score passed
        try:
            logit = (similarity - self.confidence_threshold) * 10.0 / T
            prob = 1.0 / (1.0 + math.exp(-logit))
            return float(round(prob, 4))
        except OverflowError:
            return 1.0 if similarity > self.confidence_threshold else 0.0

    @staticmethod
    def compute_ece(
        confidences: np.ndarray,
        accuracies: np.ndarray,
        num_bins: int = 10,
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Computes Expected Calibration Error (ECE) and reliability diagram bin records.

        ECE = sum_m (|B_m| / N) * |acc(B_m) - conf(B_m)|
        """
        confidences = np.asarray(confidences, dtype=np.float64)
        accuracies = np.asarray(accuracies, dtype=np.float64)

        if len(confidences) == 0:
            return 0.0, []

        bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
        ece = 0.0
        n_total = len(confidences)
        diagram_data: List[Dict[str, Any]] = []

        for b in range(num_bins):
            bin_lower = bin_boundaries[b]
            bin_upper = bin_boundaries[b + 1]

            if b == num_bins - 1:
                in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
            else:
                in_bin = (confidences >= bin_lower) & (confidences < bin_upper)

            bin_size = int(np.sum(in_bin))

            if bin_size > 0:
                bin_acc = float(np.mean(accuracies[in_bin]))
                bin_conf = float(np.mean(confidences[in_bin]))
                bin_weight = bin_size / n_total
                ece += bin_weight * abs(bin_acc - bin_conf)

                diagram_data.append({
                    "bin_index": b,
                    "bin_lower": round(bin_lower, 3),
                    "bin_upper": round(bin_upper, 3),
                    "count": bin_size,
                    "empirical_accuracy": round(bin_acc, 4),
                    "mean_confidence": round(bin_conf, 4),
                    "calibration_error": round(abs(bin_acc - bin_conf), 4),
                })
            else:
                diagram_data.append({
                    "bin_index": b,
                    "bin_lower": round(bin_lower, 3),
                    "bin_upper": round(bin_upper, 3),
                    "count": 0,
                    "empirical_accuracy": 0.0,
                    "mean_confidence": round((bin_lower + bin_upper) / 2.0, 4),
                    "calibration_error": 0.0,
                })

        return float(round(ece, 4)), diagram_data

    @staticmethod
    def compute_brier_score(
        probabilities: np.ndarray,
        ground_truth: np.ndarray,
    ) -> float:
        """
        Computes the Brier score: mean squared difference between predicted probabilities
        and true one-hot / binary outcomes. Lower is better (0.0 is perfect).
        """
        probabilities = np.asarray(probabilities, dtype=np.float64)
        ground_truth = np.asarray(ground_truth, dtype=np.float64)

        if len(probabilities) == 0:
            return 0.0

        brier = float(np.mean((probabilities - ground_truth) ** 2))
        return round(brier, 4)

    @staticmethod
    def fit_temperature(
        similarities: np.ndarray,
        labels: np.ndarray,
        scale: float = 10.0,
    ) -> float:
        """
        Fits temperature T > 0 on a validation set using grid search over NLL.
        Labels are 1 for correct match, 0 for incorrect/unknown.
        """
        similarities = np.asarray(similarities, dtype=np.float64)
        labels = np.asarray(labels, dtype=np.float64)

        if len(similarities) == 0 or len(labels) == 0:
            return 1.0

        best_t = 1.0
        best_loss = float("inf")

        for t_candidate in np.linspace(0.1, 5.0, 50):
            # Sigmoid logits
            logits = similarities * scale / t_candidate
            # Numerically stable BCE loss
            bce = np.mean(
                np.maximum(logits, 0) - logits * labels + np.log(1.0 + np.exp(-np.abs(logits)))
            )
            if bce < best_loss:
                best_loss = bce
                best_t = float(round(t_candidate, 2))

        return best_t

    @staticmethod
    def evaluate_classification_metrics(
        y_true: List[str],
        y_pred: List[str],
        unknown_label: str = "UNKNOWN",
    ) -> Dict[str, float]:
        """
        Calculates Top-1 accuracy, Precision, Recall, Macro-F1, and Unknown detection rate.
        """
        if not y_true or len(y_true) != len(y_pred):
            return {
                "top1_accuracy": 0.0,
                "precision_macro": 0.0,
                "recall_macro": 0.0,
                "f1_macro": 0.0,
                "unknown_detection_rate": 0.0,
            }

        n = len(y_true)
        correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        accuracy = correct / n

        # Extract unique classes
        classes = sorted(list(set(y_true + y_pred)))
        precisions = []
        recalls = []
        f1s = []

        for cls in classes:
            tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
            fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
            fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)

        # Unknown detection rate (recall on unknown class)
        unknown_tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == unknown_label and yp == unknown_label)
        unknown_total = sum(1 for yt in y_true if yt == unknown_label)
        unknown_rate = (unknown_tp / unknown_total) if unknown_total > 0 else 1.0

        return {
            "top1_accuracy": round(accuracy, 4),
            "precision_macro": round(float(np.mean(precisions)), 4),
            "recall_macro": round(float(np.mean(recalls)), 4),
            "f1_macro": round(float(np.mean(f1s)), 4),
            "unknown_detection_rate": round(unknown_rate, 4),
        }

