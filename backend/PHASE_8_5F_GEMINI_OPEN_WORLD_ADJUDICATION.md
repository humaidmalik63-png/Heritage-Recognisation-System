# PHASE 8.5F — GEMINI-ASSISTED OPEN-WORLD MONUMENT ADJUDICATION REPORT

**Platform**: Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Competition Reference**: Smart India Hackathon 2025 (Problem SIH25052)  
**Execution Timestamp**: 2026-11-07T18:15:00+05:30  
**Status**: Certified & Operational (14/14 Tests Passed, 100% Evaluation Success)

---

## 1. Executive Summary & Problem Diagnosis

### 1.1 The Golden Temple Misclassification Anomaly
In previous iterations, when photographs of prominent out-of-catalog Indian heritage monuments (such as the **Golden Temple / Harmandir Sahib** in Amritsar) were submitted, the system exhibited candidate ambiguity:
- **Actual Subject**: Golden Temple, Amritsar (Unindexed in 10-monument catalog).
- **CLIP Tier 1 Alignments**:
  - Top-1: Charminar (Cosine Similarity: `0.8377` / `0.8324`)
  - Top-2: Taj Mahal (Cosine Similarity: `0.8155`)
- **Similarity Margin**: `0.0222` (narrower than the pre-registered calibrated threshold of `0.0800`).
- **Original Routing**: `UNCERTAIN_MATCH` ("CLOSE CANDIDATE COMPETITION").

### 1.2 Root Cause Analysis
1. **Catalog Ambiguity Fallback Trap**: Because the Golden Temple exhibits high architectural salience (domes, arches, marble surfaces, reflective water bodies), CLIP assigns high similarity scores (> 0.80) to multiple catalogue monuments.
2. **Adjudication Exclusion**: `backend/main.py` historically restricted Tier-2 Gemini invocation to `UNKNOWN_HERITAGE_SPECIMEN` and `REVIEW_REQUIRED`. `UNCERTAIN_MATCH` was completely excluded from Tier-2 invocation, trapping ambiguous out-of-catalog specimens in in-catalog candidate competition.
3. **Low-Threshold Fix Inadequacy**: The earlier Eiffel Tower threshold rule (similarity < 0.75) only caught out-of-catalog items with weak CLIP scores; it was fundamentally blind to high-similarity out-of-catalog monuments.

---

## 2. Architecture: Tier-2 Gemini 3.1 Flash-Lite Adjudication Engine

### 2.1 Adjudication Trigger Criteria
Adjudication is triggered if and only if:
1. `gemini_service.is_available()` is True.
2. The specimen triggers an ambiguous or unindexed state:
   $$\text{DecisionState} \in \{\text{UNCERTAIN\_MATCH}, \text{UNKNOWN\_HERITAGE\_SPECIMEN}, \text{REVIEW\_REQUIRED}\}$$
3. The specimen passes the Zero-Shot Gatekeeper threshold:
   $$\text{Architectural Gatekeeper Score} \ge 0.40$$

If Gatekeeper score $< 0.40$ (e.g., invoices, mathematics papers, receipts), the engine immediately rejects the specimen as `NON_MONUMENT_REJECTED` without calling Gemini, saving latency and preventing non-monument hallucination.

### 2.2 Structured Adjudication Schema
Implemented in `backend/gemini_service.py` (`GeminiAdjudicationResult`):
- `proposed_identity`: Optional[str] (Official monument name or None)
- `proposed_location`: Optional[str] (City, State, Country or None)
- `is_heritage_structure`: bool
- `is_catalog_monument`: bool
- `visible_architectural_evidence`: str (>= 25 characters of concrete architectural features)
- `distinguishing_features`: List[str]
- `qualitative_confidence`: Literal["HIGH", "MEDIUM", "LOW", "UNCERTAIN"]
- `uncertainty_reason`: str
- `is_offline_fallback`: bool
- `model_name`: str (`gemini-3.1-flash-lite`)

### 2.3 Conservative Adjudication Policy
1. **In-Catalog Protection**: Tier-1 CLIP + FAISS remains authoritative for in-catalog monuments. Gemini cannot force `VERIFIED_MATCH` or override verified matches.
2. **Identifiable Out-of-Catalog Attribution**:
   If `is_heritage_structure == True` and `is_catalog_monument == False` and qualitative confidence is `HIGH` or `MEDIUM` with concrete architectural evidence, the specimen is routed to `UNKNOWN_HERITAGE_SPECIMEN` with `out_of_catalog_identified = True`.
3. **Negative Controls**: If Gemini indicates `is_heritage_structure == False`, specimen is routed to `NON_MONUMENT_REJECTED`.
4. **Offline / Uncertain Fallback**: If Gemini is offline or returns `UNCERTAIN` / `LOW`, Tier-1 uncertainty is strictly preserved; no hallucinated identities are presented.

---

## 3. Empirical Validation Results (14-Specimen Test Suite)

All 14 test specimens evaluated live against the running system (`backend/phase_8_5f_adjudication_results.json`):

| ID | Specimen Name | Category | Top-1 Catalog Cand (Sim) | Adjudicated Decision | Out of Catalog? | Latency | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OOC_IND_01** | **Golden Temple** | Indian Out-of-Catalog | Charminar (0.8324) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("Golden Temple (Harmandir Sahib)") | 17.6s | **PASSED** |
| **OOC_IND_02** | **Mysore Palace** | Indian Out-of-Catalog | Gateway of India (0.7869) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("Mysore Palace") | 22.5s | **PASSED** |
| **OOC_IND_03** | **Red Fort** | Indian Out-of-Catalog | Taj Mahal (0.8402) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("Red Fort") | 10.3s | **PASSED** |
| **OOC_IND_04** | **India Gate** | Indian Out-of-Catalog | Gateway of India (0.8542) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("India Gate") | 8.1s | **PASSED** |
| **OOC_INT_01** | **Eiffel Tower** | International Out-of-Catalog | Taj Mahal (0.7223) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("Eiffel Tower") | 4.9s | **PASSED** |
| **OOC_INT_02** | **Colosseum** | International Out-of-Catalog | Hawa Mahal (0.7249) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("Colosseum") | 10.9s | **PASSED** |
| **OOC_INT_03** | **Statue of Liberty**| International Out-of-Catalog | Taj Mahal (0.6791) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("Statue of Liberty") | 9.6s | **PASSED** |
| **OOC_INT_04** | **Big Ben** | International Out-of-Catalog | Victoria Memorial (0.7373) | `UNKNOWN_HERITAGE_SPECIMEN` | **True** ("Elizabeth Tower (Big Ben)") | 5.4s | **PASSED** |
| **CAT_POS_01** | **Taj Mahal** | In-Catalog Positive | Taj Mahal (0.9430) | `VERIFIED_MATCH` | **False** (Tier-1 Local Match) | 158ms | **PASSED** |
| **CAT_POS_02** | **Qutub Minar** | In-Catalog Positive | Qutub Minar (0.9435) | `VERIFIED_MATCH` | **False** (Tier-1 Local Match) | 199ms | **PASSED** |
| **CAT_POS_03** | **Charminar** | In-Catalog Positive | Charminar (0.9746) | `VERIFIED_MATCH` | **False** (Tier-1 Local Match) | 196ms | **PASSED** |
| **NON_MON_01** | **Math Paper** | Negative Control | Distractor Gated | `NON_MONUMENT_REJECTED` | **False** (Gatekeeper: 0.3889) | 136ms | **PASSED** |
| **NON_MON_02** | **Receipt** | Negative Control | Distractor Gated | `NON_MONUMENT_REJECTED` | **False** (Gatekeeper: 0.3740) | 105ms | **PASSED** |
| **NON_MON_03** | **Modern Office** | Negative Control | Distractor Gated | `NON_MONUMENT_REJECTED` | **False** (Gatekeeper: 0.3920) | 133ms | **PASSED** |

### Evaluation Summary:
- **Total Specimens Tested**: 14
- **Total Passed**: 14 (100.0%)
- **In-Catalog Positive Accuracy**: 3/3 (100.0%) — Pure Tier-1 Vector Match (< 200ms)
- **Non-Monument Negative Controls**: 3/3 (100.0%) — Zero Tier-2 Gemini API Calls Saved (< 140ms)
- **Out-of-Catalog Indian Monuments**: 4/4 (100.0%) — Accurately Identified Without False Catalog Attribution
- **Out-of-Catalog International Monuments**: 4/4 (100.0%) — Accurately Identified Without False Catalog Attribution

---

## 4. Frontend Monograph UI Enhancements

1. **Header & Badges**:
   - Dynamic model attribution: `health.gemini_tier2_model` (`gemini-3.1-flash-lite`).
   - Removed all stale hardcoded strings (`Gemini 2.5 Flash`).
2. **Out-of-Catalog Heritage Monograph Card**:
   - Rendered in `frontend/src/components/MonographResult.jsx` under `UNKNOWN_HERITAGE_SPECIMEN` when `out_of_catalog_identified = True`.
   - Distinctive Sky-blue Archival border (`border-sky-400`).
   - Badge: `OUT-OF-CATALOG HERITAGE IDENTIFIED // TIER-2 OPEN WORLD`.
   - Displays Proposed Identity, Location, and Confidence chip.
   - Identified Architectural Indicators (Distinguishing features rendered as pill tags).
   - In-Catalog Competition Diagnostics showing nearest and runner-up catalogue candidates with cosine similarities.
   - Clear Curatorial Disclaimer: *"Note: This structure lies outside the active 10-monument verified catalogue. Attribution has been adjudicated by Gemini 3.1 Flash-Lite based on authentic architectural features."*

---

## 5. Comprehensive Regression Test Suite

All subsystem regression suites executed and verified:
1. `backend/test_index.py`: 10/10 In-Catalog FAISS Top-1 Vector Retrievals **PASSED** (100%).
2. `backend/test_api.py`: 6/6 API Integration Tests **PASSED** (100%).
3. `backend/test_uncertainty.py`: 13/13 Uncertainty Scenarios **PASSED** (100%).
4. `backend/test_knowledge_engine.py`: 10/10 Grounded Knowledge Scenarios **PASSED** (100%).
5. `backend/test_local_feature_engine.py`: 16/16 SIFT/RANSAC Geometric Scenarios **PASSED** (100%).
6. `backend/test_shadow_staging.py`: 10/10 Shadow Isolation Scenarios **PASSED** (100%).
7. `backend/test_shadow_concurrency_audit.py`: 3/3 High-Concurrency Starvation Tests **PASSED** (100%).
8. `backend/test_gemini_integration.py`: 12/12 Gemini Reliability & Fail-Fast Scenarios **PASSED** (100%).
9. `frontend`: Production build (`vite build`) compiled cleanly without errors (`dist/index.html` 1.28 kB).

---

## 6. System Health & Operational State

- **Backend Daemon**: Running on `http://127.0.0.1:8000` (Status: Healthy, Model: `gemini-3.1-flash-lite`, FAISS: 210 vectors).
- **Frontend Daemon**: Running on `http://127.0.0.1:5173` (Vite dev server active and responsive).
- **Governance Invariants Maintained**:
  - Authoritative Policy A intact and untouched.
  - Shadow Mode remains disabled by default (`ENABLE_SHADOW_CANDIDATE_POLICY_D=false`).
  - No threshold changes to $T=0.1082$ or margin threshold ($0.0800$).
  - No Git commits or pushes made.

