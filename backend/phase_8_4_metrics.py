"""
Phase 8.4 Reproducible Metric Computation Engine
Provides authoritative, standardized metric calculations, confidence intervals,
and table formatters to guarantee mathematical consistency across all Phase 8.4 deliverables.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculates Wilson score confidence interval for binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996 if confidence == 0.95 else 2.57583
    p = k / n
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    half_width = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denominator
    lower = max(0.0, centre - half_width)
    upper = min(1.0, centre + half_width)
    return (round(lower, 4), round(upper, 4))

def bootstrap_ci(values: List[float], n_bootstraps: int = 1000, ci: float = 0.95) -> Tuple[float, float]:
    """Computes bootstrap confidence interval for arbitrary sample distributions."""
    if not values or len(values) < 2:
        return (0.0, 0.0)
    arr = np.array(values)
    boot_means = []
    rng = np.random.RandomState(42)
    n = len(arr)
    for _ in range(n_bootstraps):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means.append(float(np.mean(sample)))
    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(boot_means, alpha * 100))
    upper = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    return (round(lower, 4), round(upper, 4))

def calculate_ece(confidences: List[float], ground_truths: List[int], n_bins: int = 10) -> float:
    """Calculates 10-bin Expected Calibration Error."""
    if not confidences or len(confidences) != len(ground_truths):
        return 0.0
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    total_samples = len(confidences)
    ece = 0.0
    for i in range(n_bins):
        b_low, b_high = bins[i], bins[i+1]
        bin_indices = [
            idx for idx, c in enumerate(confidences)
            if b_low <= c < b_high or (i == n_bins - 1 and c == 1.0)
        ]
        if bin_indices:
            b_conf = float(np.mean([confidences[idx] for idx in bin_indices]))
            b_acc = float(np.mean([ground_truths[idx] for idx in bin_indices]))
            ece += (len(bin_indices) / total_samples) * abs(b_acc - b_conf)
    return round(ece, 4)

def calculate_policy_metrics(
    records: List[Dict[str, Any]],
    policy_name: str
) -> Dict[str, Any]:
    """
    Authoritative evaluation function for any policy on a dataset.
    Explicitly reconciles:
      - FAR_distractors (denominator = out-of-catalog + non-monuments)
      - FAR_opportunities (denominator = distractors + misretrievals)
      - Verification Recall (denominator = total catalog specimens)
      - Verification Yield (denominator = correct Top-1 retrievals)
      - Selective Accuracy / Precision (denominator = total verified predictions)
    """
    n_total = len(records)
    n_catalog = sum(1 for r in records if r["category"] == "catalog")
    n_unknown = sum(1 for r in records if r["category"] == "unknown_heritage")
    n_non_monument = sum(1 for r in records if r["category"] == "non_monument")
    n_distractors = n_unknown + n_non_monument

    top1_correct = 0
    top3_correct = 0

    tp_verified = 0
    fp_verified = 0
    fp_verified_distractor = 0
    fp_verified_catalog_misretrieval = 0

    correct_rejections = 0
    false_rejections = 0
    uncertain_count = 0
    review_count = 0

    confidences = []
    binary_ground_truths = []
    brier_scores = []
    log_losses = []

    for r in records:
        cat = r["category"]
        is_retrieval_correct = r.get("retrieval_correct", False)
        is_top3_correct = r.get("top3_correct", False)
        state = r[f"decision_state_{policy_name}"]
        prob = float(r.get("calibrated_probability", 0.50))

        y_true = 1 if (cat == "catalog" and is_retrieval_correct) else 0
        confidences.append(prob)
        binary_ground_truths.append(y_true)

        brier_scores.append((prob - y_true)**2)
        p_clip = np.clip(prob, 1e-7, 1.0 - 1e-7)
        log_losses.append(-(y_true * math.log(p_clip) + (1 - y_true) * math.log(1.0 - p_clip)))

        if cat == "catalog":
            if is_retrieval_correct:
                top1_correct += 1
                top3_correct += 1
            elif is_top3_correct:
                top3_correct += 1

        if state == "VERIFIED_MONUMENT":
            if cat == "catalog" and is_retrieval_correct:
                tp_verified += 1
            else:
                fp_verified += 1
                if cat in ["unknown_heritage", "non_monument"]:
                    fp_verified_distractor += 1
                else:
                    fp_verified_catalog_misretrieval += 1
        elif state in ["NON_MONUMENT_REJECTED", "UNKNOWN_HERITAGE_SPECIMEN"]:
            if cat in ["unknown_heritage", "non_monument"] or not is_retrieval_correct:
                correct_rejections += 1
            else:
                false_rejections += 1
        elif state == "UNCERTAIN_MATCH":
            uncertain_count += 1
            if cat == "catalog" and is_retrieval_correct:
                false_rejections += 1
        elif state == "REVIEW_REQUIRED":
            review_count += 1
            if cat == "catalog" and is_retrieval_correct:
                false_rejections += 1

    catalog_misretrievals = n_catalog - top1_correct
    n_false_acceptance_opportunities = n_distractors + catalog_misretrievals

    # Primary metrics
    top1_acc = round(top1_correct / n_catalog, 4) if n_catalog > 0 else 0.0
    top3_acc = round(top3_correct / n_catalog, 4) if n_catalog > 0 else 0.0

    verif_recall = round(tp_verified / n_catalog, 4) if n_catalog > 0 else 0.0
    verif_yield = round(tp_verified / top1_correct, 4) if top1_correct > 0 else 0.0

    total_verified = tp_verified + fp_verified
    verif_precision = round(tp_verified / total_verified, 4) if total_verified > 0 else None
    selective_acc = verif_precision

    # Reconciled FAR definitions
    far_distractors = round(fp_verified_distractor / n_distractors, 4) if n_distractors > 0 else 0.0
    far_opportunities = round(fp_verified / n_false_acceptance_opportunities, 4) if n_false_acceptance_opportunities > 0 else 0.0

    frr = round(false_rejections / n_catalog, 4) if n_catalog > 0 else 0.0
    coverage = round(total_verified / n_total, 4) if n_total > 0 else 0.0

    ece = calculate_ece(confidences, binary_ground_truths, 10)
    brier = round(float(np.mean(brier_scores)), 4) if brier_scores else None
    nll = round(float(np.mean(log_losses)), 4) if log_losses else None

    # Confidence intervals
    recall_ci = wilson_score_interval(tp_verified, n_catalog)
    yield_ci = wilson_score_interval(tp_verified, top1_correct) if top1_correct > 0 else (0.0, 0.0)
    precision_ci = wilson_score_interval(tp_verified, total_verified) if total_verified > 0 else (None, None)
    far_dist_ci = wilson_score_interval(fp_verified_distractor, n_distractors) if n_distractors > 0 else (0.0, 0.0)
    far_opp_ci = wilson_score_interval(fp_verified, n_false_acceptance_opportunities) if n_false_acceptance_opportunities > 0 else (0.0, 0.0)
    coverage_ci = wilson_score_interval(total_verified, n_total) if n_total > 0 else (0.0, 0.0)

    return {
        "policy_name": policy_name,
        "sample_counts": {
            "total_specimens": n_total,
            "catalog_specimens": n_catalog,
            "unknown_heritage_specimens": n_unknown,
            "non_monument_specimens": n_non_monument,
            "total_open_world_distractors": n_distractors,
            "catalog_retrieval_errors": catalog_misretrievals,
            "total_false_acceptance_opportunities": n_false_acceptance_opportunities
        },
        "decisions": {
            "correct_top1_retrievals": top1_correct,
            "incorrect_top1_retrievals": catalog_misretrievals,
            "correct_top3_retrievals": top3_correct,
            "true_positives_verified": tp_verified,
            "false_positives_verified_total": fp_verified,
            "false_positives_verified_distractor": fp_verified_distractor,
            "false_positives_verified_misretrieval": fp_verified_catalog_misretrieval,
            "correct_rejections": correct_rejections,
            "false_rejections": false_rejections,
            "uncertain_matches": uncertain_count,
            "review_required": review_count
        },
        "performance_metrics": {
            "top1_retrieval_accuracy": top1_acc,
            "top3_retrieval_accuracy": top3_acc,
            "verification_recall_end_to_end": verif_recall,
            "verification_recall_95_ci": recall_ci,
            "verification_yield_on_correct_retrievals": verif_yield,
            "verification_yield_95_ci": yield_ci,
            "verification_precision": verif_precision,
            "verification_precision_95_ci": precision_ci,
            "false_acceptance_rate_distractors": far_distractors,
            "false_acceptance_rate_distractors_95_ci": far_dist_ci,
            "false_acceptance_rate_opportunities": far_opportunities,
            "false_acceptance_rate_opportunities_95_ci": far_opp_ci,
            "false_rejection_rate": frr,
            "verified_decision_coverage": coverage,
            "verified_decision_coverage_95_ci": coverage_ci,
            "selective_accuracy": selective_acc
        },
        "calibration_metrics": {
            "ece_10_bins": ece,
            "brier_score": brier,
            "nll": nll
        }
    }

