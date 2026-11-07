# PHASE 8.3B — INDEPENDENT VALIDATION DATASET SPECIFICATION & PROTOCOL
## Plan for Clean Hold-Out Evaluation Corpus: Split D (`independent_final_test_v4`)

**Document Version:** 1.0.0  
**Date:** November 7, 2026  
**Status:** PROPOSED & PRE-REGISTERED PROTOCOL  
**Workspace:** `C:\Users\humai\Heritage PJ`  
**Purpose:** Provide an uncontaminated, statistically defensible independent evaluation corpus for final certification of Policy D and confidence calibration.

---

## 1. Scientific Justification for a New Independent Dataset (Split D)

### 1.1 Contamination Audit of Existing Evaluation Splits
To maintain strict scientific reproducibility and avoid circular validation, previous splits must be formally reclassified:
- **Split B (`independent_eval_v2`, $N=55$):** Extensively utilized during Phase 8.2B and 8.2C to compare Platt Scaling vs Temperature Scaling and benchmark adaptive recognition pipelines. It is formally classified as an **Exploratory & Model-Selection Corpus**.
- **Split C (`independent_final_test_v3`, $N=28$):** Extensively inspected during Phase 8.2D, 8.2E, and 8.3. The 8 correctly retrieved unverified specimens and 7 retrieval failures were directly analyzed to formulate margin relaxation floors ($0.05$) and inlier thresholds ($10$). It is formally classified as a **Diagnostic & Model-Selection Corpus**.

> [!IMPORTANT]
> **No Circular Certification:** Re-evaluating candidate Policy D on Split B or Split C cannot provide unbiased confirmation of generalization performance. Final certification requires a completely untouched, prospectively collected dataset: **Split D**.

---

## 2. Target Dataset Composition & Stratification (Target $N=100$)

Split D is designed to provide sufficient statistical power for confidence intervals while rigorously testing the decision engine against edge cases:

```
+------------------------------------------------+---------------+-----------------------------------------------+
| Stratum Category                               | Target Count  | Key Architectural Sub-Conditions Covered      |
+------------------------------------------------+---------------+-----------------------------------------------+
| 1. Canonical Catalog Monuments (10 classes)    | 60 specimens  | 6 distinct specimens per monument:            |
|    - Brihadeeswarar Temple                     | (6 per class) |   * 1 Macro architectural carving / frieze    |
|    - Charminar                                 |               |   * 1 Extreme angle (worm-eye or side profile)|
|    - Gateway of India                          |               |   * 1 Nighttime / artificial illumination     |
|    - Hampi Stone Chariot                       |               |   * 1 Distant / atmospheric haze              |
|    - Hawa Mahal                                |               |   * 1 Non-iconic elevation (rear/courtyard)   |
|    - Konark Sun Temple                         |               |   * 1 Standard daytime frontal view           |
|    - Qutub Minar                               |               |                                               |
|    - Sanchi Stupa                              |               |                                               |
|    - Taj Mahal                                 |               |                                               |
|    - Victoria Memorial                         |               |                                               |
+------------------------------------------------+---------------+-----------------------------------------------+
| 2. Out-of-Catalog Indian Heritage Monuments    | 20 specimens  | Architectural relatives and stylistic twins:  |
|                                                |               |   * Dravidian: Meenakshi Amman, Madurai (2)   |
|                                                |               |   * Deccan: Gol Gumbaz, Bijapur (2)           |
|                                                |               |   * Rock-Cut: Kailasa Temple, Ellora (2)      |
|                                                |               |   * Indo-Islamic: Fatehpur Sikri (2)          |
|                                                |               |   * Sun Temples: Modhera Sun Temple (2)       |
|                                                |               |   * Buddhist: Ajanta Caves, Karla Caves (2)   |
|                                                |               |   * Saracenic: Mysore Palace (2)              |
|                                                |               |   * Stepwells: Rani ki Vav, Patan (2)         |
|                                                |               |   * Forts: Jaisalmer Fort, Mehrangarh (2)     |
|                                                |               |   * Hoysala: Belur Chennakeshava Temple (2)   |
+------------------------------------------------+---------------+-----------------------------------------------+
| 3. Non-Monument Distractors                    | 20 specimens  | Everyday visual distractors & open-world items|
|                                                |               |   * Modern office / glass architecture (4)    |
|                                                |               |   * Indian street food & culinary items (4)   |
|                                                |               |   * Dense pedestrian crowds & bazaars (4)     |
|                                                |               |   * Natural landscapes & trees (4)            |
|                                                |               |   * Vehicles, boats & domestic animals (4)    |
+------------------------------------------------+---------------+-----------------------------------------------+
| Total Proposed Sample Size                     | 100 specimens | Complete 3-way balance (60% Cat, 20% Unk, 20% NM)|
+------------------------------------------------+---------------+-----------------------------------------------+
```

---

## 3. Strict Inclusion, Exclusion & Attribution Standards

### 3.1 Provenance and Licensing
1. **Source:** Wikimedia Commons, OpenStreetMap, or institutional open archives with verified open licenses (CC BY, CC BY-SA, or CC0 / Public Domain).
2. **Metadata Tracking:** Manifest must record:
   - `specimen_id` (e.g. `split_d_001_brihadeeswarar.jpg`)
   - `canonical_monument_key`
   - `condition_type`
   - `photographer_author`
   - `license_type`
   - `source_url`
   - `original_title`
   - `sha256_checksum`
   - `dhash_perceptual_hash`

### 3.2 Photographer-Group Separation & Zero-Overlap Guarantee
- **Exclusion Rule 1 (Author Disjointness):** No image may be sourced from any photographer, flickr account, or uploader present in:
  - Reference Gallery v2 ($200$ images)
  - Calibration Dataset v3 ($265$ images, 180 authors)
  - Split B ($55$ images)
  - Split C ($28$ images)
- **Exclusion Rule 2 (Perceptual Hash Deduplication):** Perceptual difference hash (dHash, 64-bit) must have a Hamming distance $d_H \ge 12$ against all existing gallery and test images, preventing re-compressed, cropped, or filtered duplicates.
- **Exclusion Rule 3 (Cryptographic Exactness):** SHA-256 hash must be unique across all workspace directories.

---

## 4. Pre-Registration & Integrity Audit Protocol

Before running any recognition model or policy on Split D:
1. **Manifest Freezing:** Create `backend/datasets/independent_final_test_v4_manifest.json` and compute its global SHA-256 hash.
2. **Read-Only Lock:** Place images into `backend/datasets/independent_final_test_v4/` with read-only file system permissions.
3. **Execution Script Isolation:** Use a dedicated validation script that outputs directly to `phase_8_4_split_d_results.json` without modifying calibrator weights, thresholds, or reference vectors.
4. **Third-Party Integrity Audit:** Verify that all 100 images conform to the exclusion and provenance rules before publishing metrics.

---

## 5. Certification Pass Criteria for Split D

For the platform to advance from `EXPERIMENTAL_CALIBRATED` to fully `CALIBRATED`:
1. **Statistical Power:** $N \ge 80$ evaluated specimens with complete author isolation.
2. **Verification Recall (Catalog):** $\ge 25.0\%$ on catalog specimens under Policy D.
3. **Selective Verification Precision:** $\ge 95.0\%$ on verified predictions.
4. **False Acceptance Rate (FAR):** $\le 2.0\%$ on non-monument and out-of-catalog distractors (exact 95% Wilson confidence upper bound $< 6.0\%$).
5. **Expected Calibration Error (ECE):** $\le 0.15$ on 10 uniform bins.
6. **Zero Non-Monument False Overrides:** The Gatekeeper must intercept 100% of non-monument distractors ($< 0.45$).

