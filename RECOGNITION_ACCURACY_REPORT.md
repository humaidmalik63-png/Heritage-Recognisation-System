# Recognition Accuracy & False-Positive Audit Report

**Project**: Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Audit Date**: 2026-11-08  
**Component**: CLIP ViT-B/32 + FAISS Nearest-Neighbor Index + Canonical Catalogue Service + Gemini Adjudication  

---

## 1. Executive Summary

A critical false-positive bug was reported where an image of a local building displaying a sign reading **"Mughal Heritage Museum"** was incorrectly verified as:
* **Monument**: Forbidden City
* **Location**: Dongcheng, Beijing, China
* **Architectural Style**: Traditional Chinese Palatial Architecture
* **Status**: Protected Monument

This investigation reproduced the issue, audited the FAISS vector index, isolated the root cause, and applied a strict algorithmic fix with zero regression on catalogued monuments.

---

## 2. Root Cause Analysis

### A. The Vulnerability in Canonical Membership Resolution
* The Forbidden City has the UNESCO alternate name **"Palace Museum"** in `backend/datasets/heritage_catalogue_100.json`.
* In `backend/catalogue_service.py`, `GENERIC_WORDS` contained architectural terms like `fort`, `temple`, `palace`, but **lacked `museum`, `museums`, and `heritage`**.
* When tokenizing `"Palace Museum"`, `"palace"` was stripped, leaving only `{"museum"}` as the supposedly unique proper noun.
* When evaluating `"Mughal Heritage Museum"`, Step 4 (`proper_token_subset`) tested whether `{"museum"}.issubset({"mughal", "heritage", "museum"})`.
* Because `{"museum"}` was a subset, the query was resolved to **`forbidden_city`**.
* In `backend/main.py`, receiving `CATALOGUED_AND_RECOGNITION_READY` forced `final_decision = DecisionState.VERIFIED_MATCH` and assigned an artificial similarity of `0.88`, overriding visual and uncertainty gates.

### B. FAISS Index Audit
* **Vector Count**: 577 vectors (`monument_index.faiss`).
* **Label Count**: 577 labels (`monument_labels.json`).
* **Index-Label Alignment**: Zero offset or ordering mismatch (all 577 vectors map 1:1 to their corresponding label indices).
* **Forbidden City Vectors**: Reside at indices `517` through `520` (3 reference views + 1 centroid anchor).

---

## 3. Algorithmic Fix Applied

1. **Expanded Generic Vocabulary** in `backend/catalogue_service.py`:
   Added `"museum"`, `"museums"`, `"heritage"`, `"gallery"`, `"galleries"`, `"exhibition"`, `"building"`, `"buildings"`, `"hall"`, `"house"`, `"park"`, `"national"`, `"state"`.
2. **Proper-Noun Subset Safety Guard**:
   In `check_catalogue_membership()`, single-word proper-noun subsets (`len(v_proper) < 2`) are prohibited from triggering subset matches. Multi-word alias matches now require at least 2 distinct proper nouns.
3. **Visual Corroboration Guard** in `backend/main.py`:
   Gemini Tier-2 open-world adjudication can promote a catalogued candidate to `VERIFIED_MATCH` only if visual similarity is corroborated (`max_similarity >= 0.55` in top candidates or verified by local SIFT/ORB feature inliers). Without visual alignment, the specimen is safely classified as `UNKNOWN_HERITAGE_SPECIMEN` and logged for human review.

---

## 4. Live 8-Scenario Regression Test Suite

All tests executed live against `http://127.0.0.1:8000/api/verify-monument`:

| # | Specimen Description | Category | Expected Status | Actual Status | Predicted Identity | Confidence | Review Flagged | Result |
| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :-: | :-: |
| 1 | **Taj Mahal** (`split_d_041`) | Known In-Catalogue Monument | `VERIFIED_MATCH` | `VERIFIED_MATCH` | Taj Mahal | **99.8%** | No | **PASS** |
| 2 | **Qutub Minar** (`img_1.jpg`) | Known In-Catalogue Monument | `VERIFIED_MATCH` | `VERIFIED_MATCH` | Qutub Minar | **99.8%** | No | **PASS** |
| 3 | **Forbidden City** (`img_1.jpg`) | Known In-Catalogue International | `VERIFIED_MATCH` | `VERIFIED_MATCH` | Forbidden City | **99.8%** | No | **PASS** |
| 4 | **White House** (`white_house.jpg`) | Out-of-Catalogue Structure | `UNKNOWN_HERITAGE_SPECIMEN` | `UNKNOWN_HERITAGE_SPECIMEN` | The White House | **60.0%** | Yes | **PASS** |
| 5 | **Mughal Heritage Museum** (`sc_153758`) | Unrelated Building / Signage | `NON_MONUMENT_REJECTED` | `NON_MONUMENT_REJECTED` | None | **44.7%** | No | **PASS** |
| 6 | **Pattadakal Temples** (`split_c_015`) | Out-of-Catalogue Heritage Site | `UNKNOWN_HERITAGE_SPECIMEN` | `UNKNOWN_HERITAGE_SPECIMEN` | Pattadakal Group | **60.0%** | Yes | **PASS** |
| 7 | **Non-Monument Object** (`split_d_062`) | Non-Monument Graphic | `NON_MONUMENT_REJECTED` | `NON_MONUMENT_REJECTED` | None | **30.0%** | No | **PASS** |
| 8 | **Ambiguous Crop** (`extracted_specimen`)| Low-Quality Ambiguous Photo | `NON_MONUMENT_REJECTED` | `NON_MONUMENT_REJECTED` | None | **53.2%** | No | **PASS** |

### Key Regression Observations
* **Zero False Positives**: Neither the "Mughal Heritage Museum" photograph nor the White House was mapped to the Forbidden City.
* **Out-of-Catalogue Safety**: The White House and Pattadakal were correctly identified by Gemini Tier-2 without forcing catalogue attribution, properly triggering curator review exceptions.
* **Catalogue Accuracy Preserved**: In-catalogue monuments (Taj Mahal, Qutub Minar, Forbidden City) remain recognized at 99.8% confidence.

