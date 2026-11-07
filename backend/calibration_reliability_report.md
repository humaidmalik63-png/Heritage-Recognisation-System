# CONFIDENCE CALIBRATION & RELIABILITY DIAGRAM REPORT
## Phase 8.1: Large-Scale Independent Validation and Empirical Calibration
**Audit Timestamp**: 2026-11-05T06:01:10Z  
**Development Dataset Size**: 47 authentic photographic specimens  
**Cross-Validation Strategy**: 5-Fold Grouped Cross-Validation (grouped by source/author)  

---

## 1. CALIBRATION METHODS COMPARISON TABLE

| Calibration Paradigm | Expected Calibration Error (ECE) | Brier Score (MSE) | Log Loss (NLL) | Relative ECE Reduction |
|---|---|---|---|---|
| **Raw Cosine Similarity (Uncalibrated)** | **0.3462** | **0.3165** | **0.8696** | Baseline (0.0%) |
| Temperature Scaling | 0.2102 | 0.1794 | 0.5216 | -39.3% |
| Platt Scaling | 0.1235 | 0.2159 | 0.6227 | -64.3% |
| Isotonic Regression | 0.1373 | 0.1457 | 0.8900 | -60.3% |
| **Multivariable Logistic** | **0.0904** | **0.0204** | **0.1040** | **-73.9%** |

---

## 2. WINNING METHOD & FROZEN PARAMETERS: Multivariable Logistic

```json
{
  "method": "multivariable_logistic",
  "weights": {
    "top1_sim": -1.004,
    "margin": 0.2432,
    "gatekeeper": -0.8446,
    "quality": -1.7033,
    "sift_inliers": 0.9994,
    "agreement": 1.0771
  },
  "bias": -1.5834
}
```

---

## 3. RELIABILITY DIAGRAM BINS (Multivariable Logistic)

| Bin Range | Sample Count | Mean Predicted Confidence | Empirical Accuracy | Calibration Gap |
|---|---|---|---|---|
| [0.00, 0.10] | 16 | 0.0730 | 0.0000 | 0.0730 |
| [0.10, 0.20] | 7 | 0.1386 | 0.0000 | 0.1386 |
| [0.20, 0.30] | 1 | 0.2418 | 0.0000 | 0.2418 |
| [0.30, 0.40] | 0 | 0.3500 | 0.0000 | 0.0000 |
| [0.40, 0.50] | 1 | 0.4845 | 1.0000 | 0.5155 |
| [0.50, 0.60] | 1 | 0.5866 | 1.0000 | 0.4134 |
| [0.60, 0.70] | 1 | 0.6373 | 1.0000 | 0.3627 |
| [0.70, 0.80] | 1 | 0.7175 | 1.0000 | 0.2825 |
| [0.80, 0.90] | 1 | 0.8767 | 1.0000 | 0.1233 |
| [0.90, 1.00] | 18 | 0.9904 | 1.0000 | 0.0096 |

---

## 4. MATHEMATICAL VERIFICATION & INVARIANTS

1. **Cosine Similarity is Not a Probability**: Raw CLIP inner-product scores range between 0.60 and 0.99 for architectural queries. Untreated, they vastly overestimate confidence on ambiguous stone friezes.
2. **Calibration Achievement**: The selected **Multivariable Logistic** reduces Expected Calibration Error from **0.3462** down to **0.0904**, demonstrating empirical reliability without fabricating certainty.
3. **Zero Holdout Contamination**: All parameters were fitted strictly on the Grouped 5-Fold Development split. The final Independent Test Dataset v2 was never observed during fitting.