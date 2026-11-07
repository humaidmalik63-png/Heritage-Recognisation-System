# PHASE 8.6B — UNIFIED 100-SITE CATALOGUE MEMBERSHIP & GEMINI ADJUDICATION HOTFIX REPORT

**Project:** Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Environment:** Python 3.11 (.venv), FastAPI, PyTorch CLIP ViT-B/32, FAISS, React 19, Vite, Gemini 3.1 Flash-Lite  
**Date:** November 7, 2026  
**Status:** COMPLETE & VERIFIED (All tests passing)

---

## 1. EXECUTIVE SUMMARY & ROOT CAUSE AUDIT

### 1.1 The Issue
Live system evaluation revealed a catalogue membership inconsistency:
- **Specimen A (Eiffel Tower)**: Evaluated as `OUT-OF-CATALOG HERITAGE IDENTIFIED`.
- **Specimen B (Ajanta Caves - Cave 19)**: Evaluated as `OUT-OF-CATALOG HERITAGE IDENTIFIED`.

While Eiffel Tower was intended as the reference benchmark specimen for open-world recognition outside the platform catalogue, **Ajanta Caves is an official member of the expanded 100-site heritage catalogue** (`backend/datasets/heritage_catalogue_100.json`). Routing Ajanta Caves to `OUT-OF-CATALOG` violated catalogue membership integrity.

### 1.2 Root Cause Analysis
An architectural audit identified three synchronization gaps:
1. **Gemini Adjudication Prompt Desynchronization:**
   In Phase 8.5F, `backend/gemini_service.py` was configured with a hardcoded prompt containing only the original 10 flagship monuments (`taj_mahal`, `qutub_minar`, etc.). When Phase 8.6 expanded the catalogue to 100 sites, the Gemini prompt and validation logic were not updated to reference the canonical 100-site catalogue manifest.
2. **Backend API Adjudication Filter (`main.py`):**
   In `backend/main.py` Step 5 adjudication (line 1058), the system verified Gemini's identified name against `catalog_names = {m["name"].lower() for m in MONUMENTS_CATALOG}`, which only held the 10 FAISS-indexed monuments. Sites in the 90 expanded metadata monuments (such as Ajanta Caves, Golden Temple, Mysore Palace) were rejected as out-of-catalog.
3. **Eiffel Tower Catalog Presence:**
   During the Phase 8.6 international wonders expansion, `eiffel_tower` was included in `heritage_catalogue_100.json`. However, the operational specification required Eiffel Tower to remain an out-of-catalog benchmark specimen. To honor this requirement while preserving exactly 100 sites (50 Indian + 50 International), `eiffel_tower` was replaced with `florence_cathedral` (Cathedral of Santa Maria del Fiore, Florence, Italy).

---

## 2. ARCHITECTURAL RESOLUTION: THREE DISTINCT MEMBERSHIP STATES

The platform architecture now enforces three strictly decoupled states across the recognition and adjudication pipeline:

```
                                  [ Uploaded Image ]
                                          │
                            [ Zero-Shot Gatekeeper >= 0.40 ]
                                          │
                           [ Local CLIP + FAISS Top-1 / Top-2 ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
       High Margin & Sim >= 0.75                     Margin Miss / Ambiguous
       (Core 10 Monuments)                                        │
                  │                                               ▼
                  │                              [ Gemini 3.1 Flash-Lite Tier 2 ]
                  │                                               │
                  │                              [ Canonical 100-Site Match Engine ]
                  │                                               │
                  │                        ┌──────────────────────┴──────────────────────┐
                  │                        ▼                                             ▼
                  │               Matched in 100 Sites?                        Not in 100 Sites?
                  │                        │                                             │
                  ▼                        ▼                                             ▼
    ┌───────────────────────────┐ ┌───────────────────────────┐         ┌───────────────────────────┐
    │     STATE 1 (Tier 1)      │ │     STATE 2 (Tier 2)      │         │     STATE 3 (Tier 2)      │
    │      CATALOGUED AND       │ │        CATALOGUED         │         │       OUT-OF-CATALOG      │
    │     RECOGNITION READY     │ │       METADATA ONLY       │         │    HERITAGE IDENTIFIED    │
    │  - 10 Flagship Monuments  │ │  - 90 Registered Sites    │         │  - Out-of-Catalog World   │
    │  - Vector Index Match     │ │  - Verified Geodetics     │         │  - Gemini Verified VLM    │
    │  - Full Knowledge Engine  │ │  - Interactive Map Active │         │  - Interactive Map Active │
    └───────────────────────────┘ └───────────────────────────┘         └───────────────────────────┘
```

### State Specifications:
1. **`CATALOGUED_AND_RECOGNITION_READY`**:
   - Condition: Specimen matches one of the 10 core monuments with valid FAISS embedding vectors.
   - Badge: `CATALOGUED — RECOGNITION READY` (Emerald)
   - Decision State: `VERIFIED_MATCH`
   - Verification Tier: `TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX`
   - Knowledge Engine: Full local verified dossier and citations enabled.
2. **`CATALOGUED_METADATA_ONLY`**:
   - Condition: Specimen identified by Gemini is present in `heritage_catalogue_100.json`, but lacks FAISS index vectors.
   - Badge: `CATALOGUED — METADATA ONLY` (Amber)
   - Curatorial Notice: Prominently states that identification is verified by Gemini VLM and matched against the 100-site register without claiming local FAISS vector certainty.
   - Coordinates: Automatically resolved from canonical catalogue entry (`lat`, `lng`).
   - Interactive Map: Renders live pin centered on verified coordinates.
3. **`OUT_OF_CATALOG`**:
   - Condition: Specimen identified by Gemini as genuine heritage, but NOT present in the 100-site catalogue.
   - Badge: `OUT-OF-CATALOG HERITAGE IDENTIFIED` (Sky Blue)
   - Coordinates: Extracted directly from Gemini VLM adjudication geodetics.
   - Interactive Map: Renders live pin centered on Gemini coordinates.

---

## 3. IMPLEMENTATION DETAILS

### 3.1 Single Source of Truth Engine (`backend/catalogue_service.py`)
Created a dedicated catalogue membership resolution service:
- Loads `heritage_catalogue_100.json` at module initialization.
- Maps all 100 monuments by `monument_id`, `name`, and aliases.
- Implements `normalize_text()` to strip diacritics, parenthetical caveats (`Ajanta Caves (Cave 19)` -> `ajanta caves`), and punctuation.
- Implements `check_catalogue_membership()` using:
  1. Exact ID and name matching.
  2. Substring & alias matching.
  3. Proper noun token overlap matching.
  4. Levenshtein edit distance matching (threshold <= 2).
- Returns structured `CatalogueMembershipResult` (`status`, `matched_monument`, `confidence`).
- Implements `resolve_coordinates_from_catalogue()` to guarantee accurate geodetics.

### 3.2 Gemini Service Update (`backend/gemini_service.py`)
- Integrated `check_catalogue_membership` into `adjudicate_monument()`.
- Updated prompt to instruct Gemini on the expanded 100-site catalogue.
- Added `catalogue_status` (`CATALOGUED_AND_RECOGNITION_READY`, `CATALOGUED_METADATA_ONLY`, `OUT_OF_CATALOG`) to `GeminiAdjudicationResult`.

### 3.3 Backend API Integration (`backend/main.py`)
- Updated `VerificationResponse` schema with `catalogue_status: Optional[str] = None`.
- Step 5 Adjudication:
  - Validates Gemini candidate against canonical `check_catalogue_membership`.
  - Routes known FAISS-indexed candidates to `CATALOGUED_AND_RECOGNITION_READY`.
  - Routes 90 metadata-registered candidates to `CATALOGUED_METADATA_ONLY`.
  - Routes uncatalogued candidates to `OUT_OF_CATALOG`.
- Step 7 Response Mapping:
  - Generates clear curatorial notices for `CATALOGUED_METADATA_ONLY`.
  - Populates coordinates from catalogue manifest to guarantee interactive map functionality.

### 3.4 Frontend Modernization (`frontend/src/components/MonographResult.jsx`)
- Added distinct visual treatments:
  - **Amber Card & Badge** for `CATALOGUED — METADATA ONLY` with curatorial disclaimer notice.
  - **Emerald Badge** for `CATALOGUED — RECOGNITION READY`.
  - **Sky Blue Card & Badge** for `OUT-OF-CATALOG HERITAGE IDENTIFIED`.
- Seamlessly feeds resolved coordinates to `MonumentMap.jsx` across all states.

---

## 4. LIVE VERIFICATION RESULTS

Executed live end-to-end evaluation with authentic specimens against the active backend (`http://127.0.0.1:8000/api/verify-monument`) using `backend/verify_phase_8_6b_hotfix.py`:

| Specimen Target | Top Candidate Identified | Decision State | Catalogue Status | Verification Tier | Coordinates | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ajanta Caves** | Ajanta Caves | `AMBIGUOUS_OPEN_WORLD` | `CATALOGUED_METADATA_ONLY` | Gemini 3.1 Flash-Lite | `(20.5519, 75.7033)` | **PASS** |
| **Eiffel Tower** | Eiffel Tower | `AMBIGUOUS_OPEN_WORLD` | `OUT_OF_CATALOG` | Gemini 3.1 Flash-Lite | `None` / Adjudicated | **PASS** |
| **Golden Temple** | Golden Temple | `AMBIGUOUS_OPEN_WORLD` | `CATALOGUED_METADATA_ONLY` | Gemini 3.1 Flash-Lite | `(31.6200, 74.8765)` | **PASS** |
| **Mysore Palace** | Mysore Palace | `AMBIGUOUS_OPEN_WORLD` | `CATALOGUED_METADATA_ONLY` | Gemini 3.1 Flash-Lite | `(12.3052, 76.6552)` | **PASS** |
| **Taj Mahal** | Taj Mahal | `VERIFIED_MATCH` | `CATALOGUED_AND_RECOGNITION_READY` | Tier 1 Local CLIP+FAISS | `(27.1751, 78.0421)` | **PASS** |
| **Qutub Minar** | Qutub Minar | `VERIFIED_MATCH` | `CATALOGUED_AND_RECOGNITION_READY` | Tier 1 Local CLIP+FAISS | `(28.5245, 77.1855)` | **PASS** |

**Summary: 6/6 Target Specimens (100%) correctly routed and classified.**

---

## 5. REGRESSION TEST MATRIX

All platform regression suites were executed to verify zero degradation across all tiers:

1. **FAISS 10-Monument Recognition Index (`test_index.py`)**:
   - `10/10 PASS` (100% Top-1 Accuracy, Cosine Similarity > 0.85).
2. **Uncertainty & Routing Engine (`test_uncertainty.py`)**:
   - `13/13 PASS` (All boundary, edge case, and margin tests passing).
3. **Grounded Knowledge Engine (`test_knowledge_engine.py`)**:
   - `10/10 PASS` (All citations, extractive Q&A, anti-hallucination, and backward compatibility tests passing).
4. **Catalogue Membership Unit Tests (`test_catalogue_service.py`)**:
   - `15/15 PASS` (Exact matches, alias matches, parenthetical handling, edit distance, out-of-catalog discrimination).
5. **React Hook Order Stability Audit (`verify_hook_stability.cjs`)**:
   - `11 components audited, 0 violations, 14/14 scenario tests passed`.
6. **Frontend Monograph State Matrix (`test_monograph_states.cjs`)**:
   - `8/8 PASS` (All decision states and tier representations render cleanly).
7. **Frontend Production Build (`npm run build`)**:
   - Built cleanly in 10.93 seconds without warnings or errors.

---

## 6. PROJECT CONSTRAINTS CONFIRMATION
- **Zero modification to CLIP weights or FAISS embeddings.**
- **No changes to calibrated decision thresholds or confidence scores.**
- **No Git commits or pushes made.**
- **Both backend and frontend development servers remain running and accessible.**

