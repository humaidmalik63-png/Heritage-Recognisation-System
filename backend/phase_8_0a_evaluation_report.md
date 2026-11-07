# Phase 8.0A: Multi-View Reference Gallery Expansion — Evaluation Report
**Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform**  
**SIH 2025 (SIH25052)**  
*Date: 2026-11-05*

---

## 1. Executive Summary

Phase 8.0A successfully addressed the visual reference bottleneck identified in Phase 7.3 causal error analysis. By expanding the reference gallery from **40 photographs (4 per monument)** to **200 verified multi-view photographs (20 per monument)**, independent benchmark retrieval performance improved dramatically:

| Metric | Baseline ($N=40$) | Phase 8.0A ($N=200$) | Improvement ($\Delta$) |
|---|---|---|---|
| **Top-1 Accuracy** | **65.00%** (13/20) | **90.00%** (18/20) | **+25.00%** |
| **Top-3 Accuracy** | **100.00%** (20/20) | **100.00%** (20/20) | **Maintained (100%)** |
| **Mean Reciprocal Rank (MRR)** | **0.7917** | **0.9417** | **+0.1500** |
| **Mean Similarity Margin** | **+0.0591** | **+0.2223** | **+0.1632 (3.7x wider)** |
| **False Acceptance Rate** | **0.00%** (0 false) | **0.00%** (0 false) | **0 False Acceptances** |
| **Uncertainty Safety Catch** | **100.00%** | **100.00%** | **100% Intercepted** |

---

## 2. Zero Data Leakage Guarantee

All 200 reference photographs were audited against the 20 independent evaluation holdout images in `backend/datasets/independent_eval/`:
- **Exact SHA-256 Collisions:** 0
- **dHash Near-Duplicates (Hamming $\le$ 6):** 0
- **Holdout Contamination:** 0.00%
- Every reference photograph is independently licensed (CC BY 2.0, CC BY-SA 3.0/4.0, Public Domain) with provenance recorded in `backend/source_attributions.json`.

---

## 3. Monument-by-Monument Resolution Analysis

In Phase 7.3, 7 out of 20 holdouts experienced Top-1 ranking failures due to viewpoint sparseness. Multi-view expansion resolved 5 of these 7 failures immediately:

1. **Konark Sun Temple (`konark_sun_temple`):**
   - *Baseline:* Both holdouts ranked behind Brihadeeswarar Temple (chariot wheel close-ups confused Dravidian stone carving).
   - *Phase 8.0A:* **2/2 Correct at Top-1** (Sim: 0.9971 and 0.9181, margins: +0.1384 and +0.0689).
2. **Charminar (`charminar`):**
   - *Baseline:* Distant street view confused with Gateway of India archways.
   - *Phase 8.0A:* **2/2 Correct at Top-1** (Sim: 0.9156 and 0.9997, margin: +0.0810).
3. **Gateway of India (`gateway_of_india`):**
   - *Baseline:* Distant sea approach failed margin threshold.
   - *Phase 8.0A:* **2/2 Correct at Top-1** (Sim: 0.9008 and 0.9987).
4. **Hampi Stone Chariot (`hampi_stone_chariot`):**
   - *Baseline:* Rear angle confused with Konark stone chariot elements.
   - *Phase 8.0A:* **2/2 Correct at Top-1** (Sim: 0.9975 and 0.9753).
5. **Qutub Minar (`qutub_minar`):**
   - Both holdouts (specimens 13 & 14) represent extreme angle base perspectives.
   - Both were safely flagged by Phase 6.2 Uncertainty Engine (`REVIEW_REQUIRED` and `UNCERTAIN_MATCH`), yielding **zero false acceptances**.

