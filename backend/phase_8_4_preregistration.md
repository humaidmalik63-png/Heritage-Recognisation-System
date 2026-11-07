# PHASE 8.4 — PRE-REGISTRATION PROTOCOL
## Prospective Independent Validation of Frozen Recognition Policies on Split D

**Protocol Document Version:** 1.0.0 (Pre-Registration Protocol)  
**Date of Pre-Registration:** November 7, 2026 (Before Split D Collection and Evaluation)  
**Lead Validation Auditor:** AI/ML Principal Validation Engineer & Reproducibility Auditor  
**System Evaluated:** Visual Heritage Recognition and Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)  
**Workspace:** `C:\Users\humai\Heritage PJ`  
**Governance Status:** `EXPERIMENTAL_CALIBRATED` (Candidate testing only; no production modification)

---

## 1. Scientific Justification & Motivation

### 1.1 Prevention of Post-Hoc Bias (HARKing)
Previous validation iterations (Phases 8.2–8.3) demonstrated that evaluating recognition candidates on historical evaluation splits (Split B and Split C) introduces subtle model-selection bias:
- **Split B (`independent_eval_v2`, $N=55$):** Informed calibrator selection (Platt vs Temperature scaling).
- **Split C (`independent_final_test_v3`, $N=28$):** Diagnostic inspection of its 8 unverified catalog specimens directly shaped the relaxed margin floor ($0.05$) and geometric inlier threshold ($10$).

To eliminate circularity and confirm real-world generalization, **Split D** is collected prospectively. All endpoints, thresholds, statistical methodologies, and decision criteria are hereby **pre-registered and cryptographically locked** before any Split D image is evaluated.

---

## 2. Frozen Candidate Policy Definitions

Three specific candidate policies are locked for comparative prospective validation:

### 2.1 Policy A — Baseline Production Policy
$$\text{VERIFIED} \iff \text{sim} \ge 0.75 \land \text{gatekeeper} \ge 0.50 \land [(\text{margin} \ge 0.08) \lor \text{gps\_match}]$$
- Verifies solely on global CLIP ViT-B/32 embedding similarity when the uncorroborated margin $\ge 0.08$.

### 2.2 Policy C — Local Semantic CLIP Corroboration
$$\text{VERIFIED} \iff \text{sim} \ge 0.75 \land \text{gatekeeper} \ge 0.50 \land [(\text{margin} \ge 0.08) \lor \text{gps\_match} \lor (\text{margin} \ge 0.05 \land \text{local\_clip\_mean} \ge 0.80)]$$
- Relaxes margin down to $0.05$ if a 3x3 multi-crop grid of 224x224 px patches achieves mean cosine similarity $\ge 0.80$ with the Top-1 candidate.

### 2.3 Policy D — Conservative Multi-Evidence Hybrid Corroboration
$$\text{VERIFIED} \iff \text{sim} \ge 0.75 \land \text{gatekeeper} \ge 0.50 \land [(\text{margin} \ge 0.08) \lor \text{gps\_match} \lor (\text{margin} \ge 0.05 \land (\text{sift\_inliers} \ge 10 \lor (\text{local\_clip\_mean} \ge 0.80 \land \text{gatekeeper} \ge 0.65)))]$$
- Relaxes margin to $0.05$ only if corroborated by physical SIFT/RANSAC geometric consensus ($\ge 10$ inliers) OR jointly corroborated by Local CLIP ($\ge 0.80$) and elevated Gatekeeper confidence ($\ge 0.65$).

---

## 3. Cryptographic Checksum & Parameter Registry

```
+------------------------------------+------------------------------------------------------------------+---------------------------------------+
| Component / Configuration          | SHA-256 Checksum                                                 | Locked State                          |
+------------------------------------+------------------------------------------------------------------+---------------------------------------+
| Production FAISS Index (210 vect)  | 519620C2B6C9EDAF3A91D5C67D05F8FBDD5DE344E629065CA8BBC46E5E55C603 | Dimension 512, IndexFlatIP            |
| Reference Gallery Manifest (200 img| EC9192385D77EF8DB77BE3A3EEC83013A8E1F01ED63BFEE61F8421D08DC8ED67 | 10 Canonical Monuments x 20 views     |
| Production Calibration Config      | 214FBB0366AB076F5150DCEB45BEA9234C869DD5BC0E61E3410587DD7CB4957F | Platt Scaling: A=4.2622, B=-3.5748    |
| Local Feature Engine Source        | E16CABCAEE98FC50F2FDEE170748613F999CA4E3966C2B242AFA2BD10201D134 | SIFT nfeatures=600, Lowe ratio=0.75   |
| Metric Computation Engine          | 031167D75D3FEC7412FE487F205654C3A90B51E4745F124572C484EBC0FBC293 | Standardized automated reporting      |
+------------------------------------+------------------------------------------------------------------+---------------------------------------+
```

---

## 4. Pre-Registered Study Endpoints & Metrics

### 4.1 Primary Efficacy Endpoint
- **End-to-End Verification Recall ($\text{Recall}_{\text{verif}}$):**
  $$\text{Recall}_{\text{verif}} = \frac{TP_{\text{verified}}}{N_{\text{catalog}}}$$
  Fraction of ALL ground-truth catalog monuments correctly recognized and automatically verified.

### 4.2 Primary Safety Endpoint
- **False Acceptance Rate on Distractors ($\text{FAR}_{\text{distractors}}$):**
  $$\text{FAR}_{\text{distractors}} = \frac{FP_{\text{distractor}}}{N_{\text{distractors}}}$$
  Fraction of open-world negative queries (out-of-catalog heritage and non-monuments) falsely verified as catalog monuments.

### 4.3 Secondary Endpoints & Reconciled Denominators
- **Conditional Verification Yield ($\text{Yield}_{\text{verif}}$):**
  $$\text{Yield}_{\text{verif}} = \frac{TP_{\text{verified}}}{N_{\text{correct\_retrievals}}}$$
- **Selective Verification Precision ($\text{Precision}_{\text{verif}}$):**
  $$\text{Precision}_{\text{verif}} = \frac{TP_{\text{verified}}}{TP_{\text{verified}} + FP_{\text{verified}}}$$
- **System-Wide False Acceptance Rate ($\text{FAR}_{\text{system\_wide}}$):**
  $$\text{FAR}_{\text{system\_wide}} = \frac{FP_{\text{distractor}} + FP_{\text{misretrievals}}}{N_{\text{distractors}} + N_{\text{misretrievals}}}$$
  Reconciles the denominator distinction between pure open-world distractors ($N_{\text{distractors}}$) and all opportunities for false acceptance ($N_{\text{distractors}} + N_{\text{misretrievals}}$).
- **Verified Decision Coverage:** $\text{Coverage} = \frac{TP + FP}{N_{\text{total}}}$.
- **Expected Calibration Error (ECE):** 10 uniform bins on $[0, 1]$.
- **Warm Inference Latency:** Mean and P95 on CPU execution.

---

## 5. Statistical Methodology

1. **Binomial Proportions:** All proportions (Recall, Precision, FAR, Coverage) shall be reported with exact 95% Wilson score confidence intervals.
2. **Paired Statistical Comparisons:** Comparison between policies shall use paired differences across specimens, accounting for potential correlation within monument classes and photographer groups.
3. **Continuous Metrics:** Brier score and NLL shall be accompanied by 1,000-iteration bootstrap confidence intervals.

---

## 6. Pre-Registered Decision Rule for Advancement

A candidate policy may be recommended for **`ADVANCE TO PRODUCTION READINESS REVIEW`** if and only if it satisfies all of the following criteria on Split D:
1. **Safety Boundary:** $\text{FAR}_{\text{distractors}} \le 2.0\%$ (Wilson 95% CI upper bound $< 6.0\%$).
2. **Non-Monument Gatekeeper Integrity:** $100\%$ interception of non-monument distractors ($< 0.45$).
3. **Meaningful Verification Recovery:** $\text{Recall}_{\text{verif}} \ge 20.0\%$ (statistically superior to baseline Policy A, which operates at ~12–17%).
4. **Selective Precision:** $\text{Precision}_{\text{verif}} \ge 95.0\%$.
5. **Interactive Latency:** Mean execution latency $\le 500$ ms.

If no candidate satisfies all five conditions, the pre-registered decision shall be **`REJECT ALL CANDIDATES AND CONTINUE RESEARCH`**.

