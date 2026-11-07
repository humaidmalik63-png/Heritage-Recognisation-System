# PHASE 8.4B — SPLIT D GROUND-TRUTH, STATISTICAL AND DEPLOYMENT READINESS AUDIT
## Independent Principal Scientific Audit and Staging Verification Master Report

**Document Version:** 1.0.0 (Master Audit Report)  
**Date:** November 7, 2026  
**Auditor / Principal AI Validation Scientist:** Independent Principal AI/ML Scientific Auditor & Computer Vision Validation Team  
**System Evaluated:** Visual Heritage Recognition and Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)  
**Workspace:** `C:\Users\humai\Heritage PJ`  
**Target Dataset:** `backend/datasets/independent_final_test_v4` (**Split D**, $N=100$)  
**Calibrator Evaluated:** Frozen Platt Scaling ($A=4.2622, B=-3.5748$)  
**Audit Deliverables:**
1. `backend/phase_8_4b_ground_truth_audit.json`
2. `backend/phase_8_4b_policy_recalculation.json`
3. `backend/phase_8_4b_paired_statistics.json`
4. `backend/phase_8_4b_cross_split_integrity.json`
5. `backend/phase_8_4b_calibration_audit.json`
6. `backend/phase_8_4b_shadow_staging_plan.md`
7. `backend/phase_8_4b_final_audit_report.md` (This master document)

---

## EXECUTIVE SUMMARY

Phase 8.4B serves as the definitive independent verification audit of the Phase 8.4 prospective evaluation prior to deploying Candidate Policy D into staging. Executed under strict read-only audit controls, this phase examines ground-truth veracity, cross-dataset independence, paired statistical significance, safety confidence bounds, and confidence calibration.

### Key Audit Findings:

1. **Resolution of the Sanchi Stupa Classification Question:**
   - **Prose Narrative Discrepancy:** The Phase 8.4 report narrative (Section 3.1) contained an inadvertent editorial drafting error listing Sanchi Stupa under out-of-catalog examples.
   - **Ground-Truth Integrity Confirmed:** The underlying dataset manifest (`phase_8_4_split_d_manifest.json`), FAISS database (`monument_labels.json`), and evaluation script (`phase_8_4_evaluator.py`) **strictly and correctly categorized Sanchi Stupa as an in-catalog canonical monument** (specimens `split_d_035` through `split_d_040`). Zero relabeling was performed.
   - **Architectural Schematic Finding:** Two Sanchi Stupa specimens (`split_d_035` and `split_d_040`) were identified as historical floor plans / cross-section diagrams rather than field photographs. The system safely rejected both without false acceptance (`split_d_035` received `NON_MONUMENT_REJECTED` and `split_d_040` received `UNKNOWN_HERITAGE_SPECIMEN`).

2. **Recalculated Policy Performance:**
   - **Policy A Baseline:** Top-1 Accuracy: 65.00% (39/60), End-to-End Recall: 18.33% (11/60), Yield: 28.21% (11/39), Precision: 100.0% (11/11), Distractor FAR: 0.00% (0/40), Opportunity FAR: 0.00% (0/61), Coverage: 11.00%.
   - **Policy C (Local CLIP):** Top-1 Accuracy: 65.00% (39/60), End-to-End Recall: 20.00% (12/60), Yield: 30.77% (12/39), Precision: 100.0% (12/12), Distractor FAR: 0.00% (0/40), Opportunity FAR: 0.00% (0/61), Coverage: 12.00%.
   - **Policy D (Conservative Hybrid):** Top-1 Accuracy: 65.00% (39/60), End-to-End Recall: **21.67% (13/60)**, Yield: **33.33% (13/39)**, Precision: **100.0% (13/13)**, Distractor FAR: **0.00% (0/40)**, Opportunity FAR: **0.00% (0/61)**, Coverage: **13.00%**.

3. **Paired Statistical Significance Analysis:**
   - **Policy D vs Policy A:** Discordant pairs: $b = 2$ (Policy D recovered `split_d_021` and `split_d_077`), $c = 0$ (Policy A won 0). Point estimate difference: $\Delta \text{Recall} = +3.34\%$ (95% Newcombe CI: $[-1.21\%, +7.88\%]$). Exact McNemar two-sided p-value: **$p = 0.5000$** ($p = 0.2500$ one-sided).
   - **Scientific Conclusion:** While Policy D demonstrates a positive point-estimate recall improvement with zero regressions, the improvement is **statistically non-significant at $\alpha = 0.05$ on this sample size alone ($N=60$)**. No premature claims of definitive statistical superiority are made.

4. **Rigorous One-Sided Safety Bounds:**
   - **Observed Point Estimate:** $\widehat{\text{FAR}} = 0.00\%$ across all 61 hazard opportunities.
   - **Exact Clopper-Pearson 95% Binomial Upper Bounds:**
     - Out-of-catalog heritage ($N=20$, $k=0$): **$13.91\%$** (Rule of three: $15.0\%$).
     - Non-monument distractors ($N=20$, $k=0$): **$13.91\%$** (Rule of three: $15.0\%$).
     - Catalog misretrievals ($N=21$, $k=0$): **$13.31\%$** (Rule of three: $14.29\%$).
     - Combined open-world distractors ($N=40$, $k=0$): **$7.22\%$** (Rule of three: $7.50\%$).
     - All system-wide hazard opportunities ($N=61$, $k=0$): **$4.79\%$** (Rule of three: $4.92\%$).

5. **Complete Cross-Split Independence Audit:**
   - Audited across 5 prior platform datasets (Reference Gallery v2, Calibration v3, Split B, Split C, Calibration Dev):
     - Exact SHA-256 Collisions: **0** ($0.0\%$).
     - Source URL Collisions: **0** ($0.0\%$).
     - Perceptual dHash Distance $< 8$ Collisions: **0** ($0.0\%$).
     - Same-Monument Author Collisions: **0** ($0.0\%$) against Reference Gallery.
     - Documented cross-monument photographer overlap (6 shared photographers contributing different monuments across datasets).

6. **Sub-Population Calibration Audit:**
   - **Catalog Specimens Only ($N=60$):** ECE = **0.2265**, Brier = 0.1887, NLL = 0.5648. Platt Scaling shows substantial **underconfidence** on high-certainty catalog images (in Bin 6 $[0.6, 0.7)$, accuracy is 100.0% while mean confidence is only 0.6181).
   - **Unknown Heritage Domes ($N=20$):** ECE = **0.4697**, Brier = 0.2288, NLL = 0.6479. Shows **overconfidence** due to architectural similarity.
   - **All 100 Specimens:** ECE = **0.1979** (95% Bootstrap CI: $[0.1582, 0.2394]$).
   - **Status Retention:** Platform certification status is strictly maintained as **`EXPERIMENTAL_CALIBRATED`**.

7. **Final Governance Decision:**
   - **`APPROVE POLICY D FOR SHADOW STAGING`**
   - Candidate Policy D is approved to execute exclusively in non-authoritative shadow staging behind an isolated feature flag. Policy A remains 100% authoritative for all user-facing recognition.

---

## 1. AUDIT OF SPLIT D GROUND-TRUTH LABELS & SPECIMENS

The specimen-level audit was conducted across all 100 Split D images in `backend/phase_8_4b_ground_truth_audit.json`.

### 1.1 The Sanchi Stupa Investigation
- **Inquiry:** The Phase 8.4 prose report listed Sanchi Stupa among out-of-catalog heritage examples, creating a potential concern regarding whether Sanchi Stupa was mislabeled as out-of-catalog.
- **Audit Findings:**
  1. The canonical catalog of 10 monuments defined in `backend/monuments_metadata.json` and `backend/monument_labels.json` consists of:
     - `brihadeeswarar_temple`
     - `charminar`
     - `gateway_of_india`
     - `hampi_stone_chariot`
     - `hawa_mahal`
     - `konark_sun_temple`
     - `qutub_minar`
     - `sanchi_stupa`
     - `taj_mahal`
     - `victoria_memorial`
  2. Inspection of `backend/phase_8_4_split_d_manifest.json` confirms that specimens `split_d_035` through `split_d_040` are strictly labeled as:
     - `category`: `"catalog"`
     - `monument_key`: `"sanchi_stupa"`
     - `monument_name`: `"Sanchi Stupa"`
  3. Inspection of `phase_8_4_policy_comparison.json` confirms that the evaluator strictly evaluated Sanchi Stupa as in-catalog.
  4. The discrepancy was purely a typographical / narrative copy-paste error in the text of Section 3.1 of `phase_8_4_final_validation_report.md`. No data relabeling occurred, and no metric corruption took place.

### 1.2 Identification of Historical Architectural Schematics
During the specimen-level image audit, two catalog specimens under Sanchi Stupa were identified as non-photographic architectural illustrations:
- **`split_d_035` (`split_d_035_sanchi_stupa.jpg`):** Sourced from the Internet Archive (`File:Plan of Stupa at Sanchi India.jpg`), this specimen is a historical architectural ground floor plan.
  - *Pipeline Response:* Gatekeeper raw score fell below threshold, resulting in `decision_state = "NON_MONUMENT_REJECTED"`. Zero false acceptance.
- **`split_d_040` (`split_d_040_sanchi_stupa.jpg`):** Sourced from Wikimedia Commons (`File:Sanchi Great Stupa diagram.jpg`), this specimen is an architectural cross-section line drawing by Percy Brown.
  - *Pipeline Response:* Global CLIP similarity was $0.6160 < 0.70$, resulting in `decision_state = "UNKNOWN_HERITAGE_SPECIMEN"`. Zero false acceptance.
- *Auditor Assessment:* While these two specimens represent architectural drawings rather than authentic photographic views of the physical monument, the recognition engine safely intercepted both without false verification.

### 1.3 Audit of All 100 Specimens by Category

| Stratum / Category | Target Count | Audited Count | Ground-Truth Validated | Collision with Alternate Category | Discrepancies |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Catalog Monuments (10 sites x 6)** | 60 | 60 | 60 (100.0%) | 0 | 0 |
| **Out-of-Catalog Heritage (10 sites x 2)** | 20 | 20 | 20 (100.0%) | 0 | 0 |
| **Non-Monument Distractors (5 themes x 4)** | 20 | 20 | 20 (100.0%) | 0 | 0 |
| **Total Split D Corpus** | **100** | **100** | **100 (100.0%)** | **0** | **0** |

All 20 out-of-catalog heritage specimens (`ajanta_caves`, `chennakeshava_temple_belur`, `fatehpur_sikri`, `gol_gumbaz`, `jaisalmer_fort`, `kailasa_temple_ellora`, `meenakshi_amman_temple`, `mysore_palace`, `rani_ki_vav`, `sun_temple_modhera`) were confirmed to be genuine Indian heritage sites disjoint from the 10 cataloged monuments. All 20 non-monuments are everyday cultural objects or scenes.

---

## 2. RECALCULATION OF ALL POLICY METRICS

Metrics were independently recalculated directly from specimen-level outputs in `backend/phase_8_4b_policy_recalculation.json`.

### 2.1 Master Recalculation Table

| Metric | Policy A (Baseline) | Policy C (Local CLIP) | Policy D (Conservative Hybrid) | Exact Denominator | Formula / Definition |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Specimen Count ($N$)** | 100 | 100 | 100 | 100 | All test specimens |
| **Catalog Specimen Count ($N_{\text{cat}}$)** | 60 | 60 | 60 | 60 | In-catalog specimens |
| **Top-1 Retrieval Accuracy** | 65.00% (39) | 65.00% (39) | 65.00% (39) | 60 | Correct Top-1 / $N_{\text{cat}}$ |
| **Top-3 Retrieval Accuracy** | 86.67% (52) | 86.67% (52) | 86.67% (52) | 60 | Top-3 Correct / $N_{\text{cat}}$ |
| **Correct Top-1 Retrievals** | 39 | 39 | 39 | — | True match candidates |
| **Incorrect Top-1 Retrievals** | 21 | 21 | 21 | — | Misretrievals / confusion |
| **True Positives Verified ($TP$)** | **11** | **12** | **13** | — | Verified correct predictions |
| **False Positives Verified ($FP_{\text{total}}$)** | **0** | **0** | **0** | — | Total incorrect verifications |
| **Correct Rejections ($CR$)** | 39 | 39 | 39 | — | Rejection of non-correct inputs |
| **False Rejections ($FR$)** | 28 | 27 | 26 | — | Correct Top-1 not verified |
| **Verification Recall (End-to-End)** | 18.33% (11/60) | 20.00% (12/60) | **21.67% (13/60)** | 60 | $TP / N_{\text{cat}}$ |
| *95% Wilson Confidence Interval* | [10.56%, 29.92%] | [11.83%, 31.78%] | **[13.12%, 33.62%]** | — | Score interval |
| **Verification Yield (on Top-1 Correct)** | 28.21% (11/39) | 30.77% (12/39) | **33.33% (13/39)** | 39 | $TP / \text{Top-1 Correct}$ |
| *95% Wilson Confidence Interval* | [16.54%, 43.78%] | [18.57%, 46.42%] | **[20.63%, 49.02%]** | — | Score interval |
| **Selective Verification Precision** | **100.0% (11/11)** | **100.0% (12/12)** | **100.0% (13/13)** | $TP + FP$ | $TP / (TP + FP)$ |
| *95% Wilson Confidence Interval* | [74.12%, 100.0%] | [75.75%, 100.0%] | **[77.19%, 100.0%]** | — | Score interval |
| **False Rejection Rate (FRR)** | 46.67% (28/60) | 45.00% (27/60) | **43.33% (26/60)** | 60 | $FR / N_{\text{cat}}$ |
| **Verified Decision Coverage** | 11.00% (11/100) | 12.00% (12/100) | **13.00% (13/100)** | 100 | $(TP + FP) / N$ |
| *95% Wilson Confidence Interval* | [6.25%, 18.63%] | [7.00%, 19.81%] | **[7.76%, 20.98%]** | — | Score interval |
| **Selective Accuracy** | 100.0% | 100.0% | 100.0% | $TP + FP$ | Same as precision |

### 2.2 Disaggregated Hazard Breakdown of False Acceptances

To prevent aggregation masking, false acceptance metrics are reported across their distinct negative hazard pools:

```mermaid
pie title Hazard Opportunities Breakdown (N=61 Opportunities)
    "Non-Monument Distractors (N=20)" : 20
    "Out-of-Catalog Heritage (N=20)" : 20
    "Catalog Misretrievals (N=21)" : 21
```

| Negative Hazard Category | Specimen Count ($N$) | Policy A False Acceptances | Policy C False Acceptances | Policy D False Acceptances | Observed FAR | Exact 95% Clopper-Pearson Upper Bound |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A. Out-of-Catalog Heritage** | 20 | 0 | 0 | 0 | **0.00% (0/20)** | **13.91%** |
| **B. Non-Monument Distractors** | 20 | 0 | 0 | 0 | **0.00% (0/20)** | **13.91%** |
| **C. In-Catalog Misretrievals** | 21 | 0 | 0 | 0 | **0.00% (0/21)** | **13.31%** |
| **Combined Distractors (A + B)** | 40 | 0 | 0 | 0 | **0.00% (0/40)** | **7.22%** |
| **All System-Wide Opportunities** | 61 | 0 | 0 | 0 | **0.00% (0/61)** | **4.79%** |

---

## 3. STATISTICAL COMPARISON OF POLICIES

Paired per-specimen outcomes were computed in `backend/phase_8_4b_paired_statistics.json`.

### 3.1 2x2 Paired Contingency Tables (Catalog Specimens, $N=60$)

#### Comparison 1: Policy C versus Policy A
- Both Verified (A=1, C=1): **11** specimens
- Only Policy C Verified (A=0, C=1): **1** specimen (`split_d_021`)
- Only Policy A Verified (A=1, C=0): **0** specimens
- Neither Verified (A=0, C=0): **48** specimens
- Discordant Pairs: $b = 1, c = 0$ ($n_{\text{discordant}} = 1$)
- **McNemar Exact Test:**
  - One-sided p-value: **$p = 0.5000$**
  - Two-sided p-value: **$p = 1.0000$**
  - Continuity-corrected statistic: $\chi^2 = 0.0000$
- **Recall Difference:** $\Delta = +1/60 = +1.67\%$ (95% Newcombe CI: $[-1.56\%, +4.89\%]$)

#### Comparison 2: Policy D versus Policy A
- Both Verified (A=1, D=1): **11** specimens
- Only Policy D Verified (A=0, D=1): **2** specimens (`split_d_021`, `split_d_077`)
- Only Policy A Verified (A=1, D=0): **0** specimens
- Neither Verified (A=0, D=0): **47** specimens
- Discordant Pairs: $b = 2, c = 0$ ($n_{\text{discordant}} = 2$)
- **McNemar Exact Test:**
  - One-sided p-value: **$p = 0.2500$**
  - Two-sided p-value: **$p = 0.5000$**
  - Continuity-corrected statistic: $\chi^2 = 0.5000$
- **Recall Difference:** $\Delta = +2/60 = +3.34\%$ (95% Newcombe CI: $[-1.21\%, +7.88\%]$)

#### Comparison 3: Policy D versus Policy C
- Both Verified (C=1, D=1): **12** specimens
- Only Policy D Verified (C=0, D=1): **1** specimen (`split_d_077`)
- Only Policy C Verified (C=1, D=0): **0** specimens
- Neither Verified (C=0, D=0): **47** specimens
- Discordant Pairs: $b = 1, c = 0$ ($n_{\text{discordant}} = 1$)
- **McNemar Exact Test:**
  - One-sided p-value: **$p = 0.5000$**
  - Two-sided p-value: **$p = 1.0000$**
- **Recall Difference:** $\Delta = +1/60 = +1.67\%$ (95% Newcombe CI: $[-1.56\%, +4.89\%]$)

### 3.2 Analysis of Discordant Specimens
1. **`split_d_021` (Hawa Mahal):**
   - *Parameters:* Top-1 Sim = 0.8842, Margin = 0.0704 ($0.05 \le \text{margin} < 0.08$), Local CLIP mean = 0.8494, SIFT Inliers = 5.
   - *Outcome:* Policy A rejected it ($0.0704 < 0.08$). Policy C and Policy D verified it via Local CLIP patch consensus ($\ge 0.80$).
   - *Photographer:* `Firo0002` (disjoint from reference gallery).
2. **`split_d_077` (Hampi Stone Chariot):**
   - *Parameters:* Top-1 Sim = 0.8912, Margin = 0.0637 ($0.05 \le \text{margin} < 0.08$), Local CLIP mean = 0.7174 ($< 0.80$), SIFT Inliers = 18 ($\ge 10$).
   - *Outcome:* Policy A rejected it ($0.0637 < 0.08$). Policy C rejected it (Local CLIP $< 0.80$). Policy D verified it via SIFT geometric affine consensus ($18 \ge 10$).
   - *Photographer:* `A.Savin` (disjoint from reference gallery for Hampi).

### 3.3 Statistical Auditor Conclusion on Superiority
> [!IMPORTANT]
> **Audit Finding on Statistical Power:**
> While Policy D demonstrated a monotonic recall gain of $+3.34\%$ with zero regressions ($c = 0$), the paired McNemar two-sided p-value is **$p = 0.5000$**, which does not cross the conventional significance threshold ($\alpha = 0.05$). The Newcombe 95% confidence interval for the difference $[-1.21\%, +7.88\%]$ crosses zero.
> Therefore, from a strict frequentist perspective, **statistical superiority cannot be certified on $N=60$ catalog specimens alone**. The evidence demonstrates safety preservation and positive empirical yield, justifying shadow staging rather than immediate authoritative replacement.

---

## 4. RECALCULATION OF EXACT SAFETY BOUNDS

A critical validation principle is that **an observed 0% False Acceptance Rate does NOT prove an underlying error rate of zero**.

### 4.1 Exact Upper Confidence Bounds

When zero false acceptances are observed ($k = 0$) in a sample of size $N$, the exact one-sided $100(1 - \alpha)\%$ upper bound on the true binomial hazard probability $p$ is given by:
$$p_{\text{upper}} = 1 - \alpha^{1/N}$$
For a 95% confidence level ($\alpha = 0.05$):
$$p_{\text{upper}} = 1 - 0.05^{1/N}$$

| Hazard Category | Denominator ($N$) | Observed $k$ | Point Estimate $\widehat{p}$ | Rule of Three ($\approx 3/N$) | Exact 95% Clopper-Pearson Upper Bound |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Out-of-Catalog Heritage** | 20 | 0 | 0.00% | 15.00% | **13.91%** |
| **Non-Monument Distractors** | 20 | 0 | 0.00% | 15.00% | **13.91%** |
| **Catalog Misretrievals** | 21 | 0 | 0.00% | 14.29% | **13.31%** |
| **Combined Distractors** | 40 | 0 | 0.00% | 7.50% | **7.22%** |
| **All Hazard Opportunities** | 61 | 0 | 0.00% | 4.92% | **4.79%** |

### 4.2 Statistical Independence Assessment
- **Independent Observations:** The 20 non-monument distractors span 5 disparate categories (food, modern skyscrapers, landscapes, markets) and are statistically independent. The 20 out-of-catalog heritage specimens represent 10 distinct architectural traditions across India.
- **Correlated Hazards:** Misretrievals within the same monument class (e.g. night photos of Sanchi Stupa retrieving Konark) share architectural features (carved sandstone, decorative relief), introducing mild positive correlation. This reinforces the necessity of relying on the conservative $4.79\%$ upper bound rather than the naive $0.00\%$ point estimate.

---

## 5. COMPLETE CROSS-SPLIT DATASET INDEPENDENCE MATRIX

Audited across all prior platform corpora in `backend/phase_8_4b_cross_split_integrity.json`.

```mermaid
graph LR
    SplitD[Split D N=100] --- RefGal[Reference Gallery v2 N=200]
    SplitD --- CalibV3[Calibration Dataset v3 N=265]
    SplitD --- SplitB[Split B Eval v2 N=55]
    SplitD --- SplitC[Split C Final v3 N=28]
    SplitD --- CalDev[Calibration Dev N=47]
    
    style SplitD fill:#2ecc71,stroke:#27ae60,stroke-width:2px;
```

| Prior Dataset | Sample Size | SHA-256 Collisions | Source URL Collisions | Perceptual Near-Duplicates ($d < 8$) | Same-Monument Photographer Overlap | Cross-Monument Photographer Overlap | Independence Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reference Gallery v2** | 200 | **0** | **0** | **0** | **0** | 6 authors | **CONFIRMED INDEPENDENT** |
| **Calibration Dataset v3** | 265 | **0** | **0** | **0** | **0** | 8 authors | **CONFIRMED INDEPENDENT** |
| **Split B (`independent_eval_v2`)** | 55 | **0** | **0** | **0** | **0** | 4 authors | **CONFIRMED INDEPENDENT** |
| **Split C (`independent_final_test_v3`)** | 28 | **0** | **0** | **0** | **0** | 3 authors | **CONFIRMED INDEPENDENT** |
| **Calibration Development** | 47 | **0** | **0** | **0** | **0** | 2 authors | **CONFIRMED INDEPENDENT** |
| **Total Prior Corpus Audited** | **595** | **0** | **0** | **0** | **0** | — | **ALL INDEPENDENT** |

### 5.1 Photographer Overlap Clarification
- **Same-Monument Disjointness (100% Verified):** There are **zero** instances where an author who photographed a monument in the reference gallery photographed that same monument in Split D.
- **Cross-Monument Overlap:** Six prolific Wikimedia contributors (e.g., `Bernard Gagnon`, `Vyacheslav Argenberg`, `A.Savin`) appear across different monuments in multiple datasets (e.g., `A.Savin` contributed Taj Mahal in Split B and Hampi in Split D). Because their contributions involve entirely different physical monuments, lighting conditions, and camera hardware, image content independence is preserved.

---

## 6. CONFIDENCE CALIBRATOR AUDIT

The frozen Platt Scaling model ($A = 4.2622, B = -3.5748$) was evaluated in `backend/phase_8_4b_calibration_audit.json`.

### 6.1 Calibration by Sub-Population

| Sub-Population Evaluated | Specimen Count ($N$) | Mean Predicted Confidence | Empirical Positive Accuracy | Expected Calibration Error (ECE) | Brier Score | Negative Log-Likelihood (NLL) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Catalog Specimens Only** | 60 | 0.4859 | 0.6500 | **0.2265** | 0.1887 | 0.5648 |
| **Out-of-Catalog Heritage** | 20 | 0.4697 | 0.0000 | **0.4697** | 0.2288 | 0.6479 |
| **Non-Monument Distractors** | 20 | 0.3030 | 0.0000 | **0.3030** | 0.0938 | 0.3630 |
| **All Combined Specimens** | **100** | **0.4461** | **0.3900** | **0.1979** | **0.1777** | **0.5411** |

### 6.2 Deep Calibration Diagnosis
1. **Severe Underconfidence on In-Catalog Specimen Predictions:**
   - In Bin 5 ($[0.5, 0.6)$), the calibrator assigned an average confidence of **0.5525**, yet the empirical accuracy was **82.35%** (a negative gap of $-0.2710$).
   - In Bin 6 ($[0.6, 0.7)$), the calibrator assigned an average confidence of **0.6181**, yet the empirical accuracy was **100.00%** (a negative gap of $-0.3819$).
   - This occurs because Platt Scaling operates as a 1D sigmoid on cosine similarity. To protect against open-world negatives, its learned slope is heavily compressed, resulting in conservative probabilities for genuine catalog monuments.
2. **Overconfidence on Out-of-Catalog Heritage:**
   - Out-of-catalog heritage domes and carvings share visual motifs with catalog monuments, yielding moderate cosine similarity ($s \approx 0.72$). The scalar calibrator maps this to $\sim 0.47$ confidence, despite ground truth $Y=0$.
3. **Certification Status Rationale:**
   - Platform certification status must strictly remain **`EXPERIMENTAL_CALIBRATED`**.
   - Advancing to fully `CALIBRATED` requires multi-feature calibration (e.g. conditioned on Gatekeeper score and similarity margin) to resolve the dual challenges of underconfidence on catalog images and overconfidence on out-of-catalog domes.

---

## 7. SHADOW STAGING EVALUATION & SAFETY VERIFICATION

The shadow staging deployment plan is detailed in [phase_8_4b_shadow_staging_plan.md](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4b_shadow_staging_plan.md).

### 7.1 Key Staging Safeguards
- **Authoritative Isolation:** Policy A strictly serves 100% of production traffic.
- **Asynchronous Execution:** Policy D executes in a background thread pool with a **500 ms hard timeout**.
- **Independent Telemetry:** Disagreements and latencies are recorded to `backend/telemetry/shadow_staging_audit.jsonl`.
- **Zero Gemini Override:** Gemini cultural synthesis operates read-only on Policy A outputs.
- **Instant Kill Switch:** Environment variable `ENABLE_SHADOW_CANDIDATE_POLICY_D=false` completely halts shadow computation without application restart.

---

## 8. PRODUCTION PROTECTION VERIFICATION

The following production components were verified as **strictly read-only and unmodified**:
- `backend/calibration_config.json` (SHA-256: `214FBB0366AB076F5150DCEB45BEA9234C869DD5BC0E61E3410587DD7CB4957F`)
- `backend/monument_index.faiss` (SHA-256: `519620C2B6C9EDAF3A91D5C67D05F8FBDD5DE344E629065CA8BBC46E5E55C603`)
- `backend/monument_labels.json` (210 reference vectors across 10 canonical monuments)
- CLIP ViT-B/32 model weights and Zero-Shot Gatekeeper prompt embeddings
- Five canonical uncertainty states (`VERIFIED_MONUMENT`, `UNCERTAIN_MATCH`, `REVIEW_REQUIRED`, `UNKNOWN_HERITAGE_SPECIMEN`, `NON_MONUMENT_REJECTED`)
- Git repository clean: zero automated commits, zero pushes to GitHub.

---

## 9. FINAL AUDIT DECISION

Based on the evidence audited across Split D:

### Formal Decision:
# **APPROVE POLICY D FOR SHADOW STAGING**

### Auditor Summary Justification:
1. **Safety Preserved:** Zero false acceptances observed across all 40 open-world negative distractors and 21 catalog misretrievals ($FAR_{\text{distractors}} = 0.0\%$, $FAR_{\text{opportunities}} = 0.0\%$, exact one-sided 95% upper bound $< 4.79\%$).
2. **Positive Utility Yield:** Policy D safely unlocked automated verification for two additional challenging specimens (`split_d_021` and `split_d_077`), achieving 100% selective precision.
3. **Statistically Responsible:** Acknowledges that $p = 0.5000$ in paired McNemar testing represents insufficient evidence for direct production cutover, making non-authoritative shadow staging the scientifically optimal pathway.
4. **Dataset Integrity:** Confirmed 100% image valid, zero SHA-256 collisions, zero URL collisions, and zero same-monument author overlap across all prior datasets.
5. **Certification Status:** Platform confidence calibration status remains strictly certified as **`EXPERIMENTAL_CALIBRATED`**.

---
*Report certified by Independent Principal AI/ML Scientific Auditor & Computer Vision Validation Team on November 7, 2026.*

