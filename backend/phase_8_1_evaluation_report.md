# PHASE 8.1 INDEPENDENT VALIDATION AND CONFIDENCE CALIBRATION REPORT
## Visual Heritage Recognition Platform (SIH 2025 SIH25052)
**Audit Timestamp**: 2026-11-05T06:37:04Z  
**Independent Test Dataset**: independent_eval_v2 (55 authentic specimens)  
**Strict Leakage Invariant**: 0 SHA-256 collisions against Reference Gallery & Development splits.  

---

## 1. EXECUTIVE SUMMARY & BENCHMARK COMPARISON

| Paradigm / Configuration | Top-1 Accuracy (%) | Top-3 Accuracy (%) | MRR | Mean Latency (ms) | Role / Status |
|---|---|---|---|---|---|
| **A Global CLIP** | **77.78%** | 88.89% | - | 141.12 ms | Evaluated |
| **B Global GPS** | **77.78%** | 88.89% | - | 141.12 ms | Evaluated |
| **C Local CLIP** | **77.78%** | -% | - | 873.48 ms | Evaluated |
| **D SIFT Corroboration** | **77.78%** | -% | - | 1014.6 ms | Evaluated |
| **E Hybrid Local** | **77.78%** | -% | - | 1014.6 ms | Evaluated |
| **F Full Production** | **77.78%** | 88.89% | 0.8333 | 1014.6 ms | Evaluated |
| **G Conditional Production** | **77.78%** | 88.89% | 0.8333 | 797.44 ms | Evaluated |

---

## 2. EMPIRICAL CONFIDENCE CALIBRATION ON INDEPENDENT HOLDOUT

- **Calibrated Model Expected Calibration Error (ECE)**: **0.2806**
- **Uncalibrated Raw Cosine ECE**: **0.3070**
- **Relative Calibration Error Reduction**: **8.6%**
- **Calibrated Brier Score**: **0.1938** (vs. uncalibrated 0.2714)

### Reliability Diagram Bins on Independent Test Dataset v2
| Bin Range | Specimen Count | Mean Predicted Probability | Empirical Accuracy | Calibration Gap |
|---|---|---|---|---|
| [0.00, 0.10) | 0 | 0.0500 | 0.0000 | 0.0000 |
| [0.10, 0.20) | 0 | 0.1500 | 0.0000 | 0.0000 |
| [0.20, 0.30) | 1 | 0.2995 | 0.0000 | 0.2995 |
| [0.30, 0.40) | 10 | 0.3569 | 0.0000 | 0.3569 |
| [0.40, 0.50) | 16 | 0.4510 | 0.2500 | 0.2010 |
| [0.50, 0.60) | 24 | 0.5491 | 0.8333 | 0.2843 |
| [0.60, 0.70) | 4 | 0.6179 | 1.0000 | 0.3821 |
| [0.70, 0.80) | 0 | 0.7500 | 0.0000 | 0.0000 |
| [0.80, 0.90) | 0 | 0.8500 | 0.0000 | 0.0000 |
| [0.90, 1.00) | 0 | 0.9500 | 0.0000 | 0.0000 |

---

## 3. CURATORIAL SAFETY & UNCERTAINTY METRICS

- **False Acceptance Rate (Incorrect VERIFIED_MATCH)**: **0.0%** (0 false claims)
- **Unknown Heritage Rejection Rate**: **11.11%** (Out-of-catalog Indian heritage sites safely intercepted)
- **Non-Monument Distractor Rejection Rate**: **50.0%** (Objects and scenes rejected by Zero-Shot Gatekeeper)
- **Uncertain Match Rate**: **56.36%** (Close candidate margins routed to curation)
- **Review Required Rate**: **3.64%**

---

## 4. PER-MONUMENT RECOGNITION BREAKDOWN (CONFIG F PRODUCTION)

| Monument Key | Total Queries | Top-1 Accuracy (%) | Verified Matches | Uncertain Matches | Review Required |
|---|---|---|---|---|---|
| `brihadeeswarar_temple` | 2 | **100.0%** | 0 | 2 | 0 |
| `charminar` | 2 | **50.0%** | 0 | 1 | 0 |
| `gateway_of_india` | 2 | **0.0%** | 0 | 2 | 0 |
| `hampi_stone_chariot` | 3 | **100.0%** | 0 | 3 | 0 |
| `hawa_mahal` | 4 | **100.0%** | 4 | 0 | 0 |
| `konark_sun_temple` | 4 | **75.0%** | 0 | 4 | 0 |
| `qutub_minar` | 4 | **100.0%** | 2 | 2 | 0 |
| `sanchi_stupa` | 4 | **100.0%** | 2 | 2 | 0 |
| `taj_mahal` | 10 | **60.0%** | 3 | 6 | 0 |
| `victoria_memorial` | 1 | **100.0%** | 0 | 1 | 0 |

---

## 5. LOCAL FEATURE CORROBORATION METRICS

- **Global / Local Agreement Rate**: **60.0%**
- **Global / Local Divergence Rate**: **40.0%** (ambiguity flagged for review)
- **SIFT/RANSAC Geometric Verification Rate**: **1.82%**
- **Mean SIFT Keypoint Inliers**: **2.95** (Max inliers: **19**)

---

## 6. INFERENCE LATENCY & HARDWARE PROFILING

- **Mean End-to-End Latency**: **1014.6 ms**
- **Median Latency**: **998.81 ms**
- **P95 Latency**: **1188.07 ms**