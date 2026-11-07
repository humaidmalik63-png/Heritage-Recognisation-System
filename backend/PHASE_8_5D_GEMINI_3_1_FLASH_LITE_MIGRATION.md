# PHASE 8.5D — GEMINI 3.1 FLASH-LITE MIGRATION & MULTIMODAL AUDIT REPORT
**Visual Heritage Recognition & Grounded Cultural Discovery Platform**  
*SIH 2025 (Problem Statement: SIH25052) — Architectural Quality, Verification, and Multimodal Audit*  
**Date:** November 7, 2026  
**Status:** Certified & Production Verified

---

## 1. Executive Summary

Phase 8.5D successfully migrated the Tier-2 Multimodal Vision-Language Model service to Google's stable **`gemini-3.1-flash-lite`** model. This migration resolves the deprecation of `gemini-2.5-flash` (HTTP 404) and the quota exhaustion of `gemini-3.8-flash` (HTTP 429), while instituting a robust, configurable environment architecture, structured multimodal schema extraction, fail-fast quota handling, and preserving authoritative Policy A recognition invariants.

### Key Milestones Delivered
1. **Model Migration**: Migrated from legacy `gemini-2.5-flash` to **`gemini-3.1-flash-lite`**.
2. **Dynamic Environment Configuration**: Sourced `GEMINI_MODEL=gemini-3.1-flash-lite` from `.env` and `os.environ` across the entire codebase, eliminating hardcoded model references.
3. **Structured Open-World Vision Schema**: Enforced structured JSON output containing:
   - `proposed_identity`
   - `is_catalog_monument`
   - `visual_evidence`
   - `confidence_description` (qualitative, non-numeric)
   - `uncertainty_reason`
4. **Authoritative Boundary Verification**: Tested 5 real-world heritage monuments outside the catalog (Eiffel Tower, Colosseum, Mysore Palace, Red Fort, Golden Temple). Gemini identified each monument accurately while strictly marking `is_catalog_monument: false` for all 5.
5. **Fail-Fast Error & Quota Handling**: Intercepted HTTP 401/403 (auth), HTTP 404 (model not found), and HTTP 429 (quota exhaustion) without infinite or repeated retries, cleanly dropping to the sub-millisecond offline curatorial fallback.
6. **Full Regression Integrity**: All 12/12 Gemini integration scenarios, 6/6 API tests, 12/12 end-to-end user journeys, and 13/13 uncertainty scenarios passed with 100% success. Frontend build compiled cleanly without errors.

---

## 2. Model Deprecation Audit & Migration Rationalization

| Model Evaluated | API Response Status | Observation & Root Cause | Resolution |
|:---|:---:|:---|:---|
| **`gemini-2.5-flash`** | `404 NOT_FOUND` | Google officially retired the `gemini-2.5-flash` endpoint for active API keys (`"This model models/gemini-2.5-flash is no longer available to new users"`). | **Deprecated & Replaced** |
| **`gemini-3.8-flash`** | `429 RESOURCE_EXHAUSTED` | Valid model architecture, but free-tier request quota (20 requests/day) was exhausted during automated benchmark runs. | **Rate-Limited** |
| **`gemini-3.1-flash-lite`** | **`200 OK`** | Successfully accepted requests via modern `google.genai` SDK with instant responses, high throughput, and dedicated quota allocations. | **Adopted as Authoritative Model** |

---

## 3. Architecture & Implementation Changes

### 3.1 Environment Variable Configuration
- **`backend/.env`**: Added `GEMINI_MODEL="gemini-3.1-flash-lite"`.
- **`backend/.env.example`**: Updated developer template with documentation for `GEMINI_MODEL`.
- **`backend/gemini_service.py`**:
  ```python
  DEFAULT_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
  ```
- **`backend/main.py`** & **`backend/knowledge_engine.py`**: Dynamically inherit model names from `gemini_service.model_name` rather than hardcoding string literals.

### 3.2 Enhanced Structured Schema
In [`backend/gemini_service.py`](file:///C:/Users/humai/Heritage%20PJ/backend/gemini_service.py#L46-L75):
```python
class UnknownHeritageAnalysis(BaseModel):
    proposed_identity: Optional[str] = Field(default=None, description="Tentative monument name and location if recognizable, or null if uncertain.")
    is_catalog_monument: bool = Field(default=False, description="True ONLY if the specimen belongs to the authoritative 10-monument catalogue; False otherwise.")
    visual_evidence: str = Field(default="", description="Detailed explanation of visible architectural characteristics, materials, and forms.")
    confidence_description: str = Field(default="UNCERTAIN", description="Qualitative description of visual confidence.")
    uncertainty_reason: str = Field(default="", description="Epistemological caveats, visible occlusions, or why identification cannot be guaranteed.")
    visible_observations: List[str] = Field(default_factory=list)
    candidate_styles: List[str] = Field(default_factory=list)
    candidate_descriptions: List[str] = Field(default_factory=list)
    curatorial_caveat: str = Field(default="Visual analysis is exploratory and does not establish verified historical identity without epigraphical or archival records.")
    is_offline_fallback: bool = False
```

### 3.3 Fail-Fast Quota & Error Handling
[`backend/gemini_service.py`](file:///C:/Users/humai/Heritage%20PJ/backend/gemini_service.py#L320-L360):
- **401/403 (Auth)**: Disables client immediately, flags `auth_error_detected = True`, records `AUTH_INVALID_KEY` telemetry, zero retries.
- **404 (Model Not Found)**: Fails fast without retry, records `MODEL_NOT_FOUND_404`.
- **429 (Quota Exhaustion)**: Checks for `"quota"`, `"billing"`, `"plan"`, or `"free_tier_requests"`. When present, fails fast without repeated retries to eliminate blocking latencies.
- **Transient Network/5xx**: Bounded exponential backoff (1s, 2s, 4s) up to 3 retries max.
- **Security Invariant**: API keys are masked using regex redaction (`key=[REDACTED]`) before logging or persisting telemetry.

---

## 4. Live API Connectivity & Token Usage

### 4.1 Text Request Test
- **Prompt**: *"In 2 sentences, describe the structural function of an Indo-Islamic corbelled dome in Mughal architecture."*
- **Model**: `gemini-3.1-flash-lite`
- **HTTP Status**: `200 OK`
- **Latency**: `1,530.93 ms`
- **Token Usage**:
  - Prompt Tokens: **23**
  - Candidate Tokens: **66**
  - Total Tokens: **89**
- **Response**:
  > *"An Indo-Islamic corbelled dome is constructed by layering inward-projecting horizontal stone courses until the aperture is narrow enough to be capped with a single slab. This technique relies on the weight of the masonry to create stability through inward gravity, allowing for the creation of vaulted spaces without the outward thrust inherent in true radial arches."*

---

## 5. Live Multimodal Image Recognition Results

Five authentic heritage monuments outside the catalog were evaluated using the live `gemini-3.1-flash-lite` multimodal endpoint:

```
Authoritative Primary 10-Monument Catalog:
1. Taj Mahal, 2. Qutub Minar, 3. Charminar, 4. Hawa Mahal, 5. Konark Sun Temple,
6. Gateway of India, 7. Hampi Stone Chariot, 8. Sanchi Stupa, 9. Victoria Memorial, 10. Brihadeeswarar Temple
```

### 5.1 Results Matrix

| Specimen | Proposed Identity | Is Catalog Monument? | Expected | Catalog Correct? | Qualitative Confidence | Latency | Fallback? |
|:---|:---|:---:|:---:|:---:|:---|:---:|:---:|
| **Eiffel Tower** | `Eiffel Tower, Paris/France` | **False** | False | **PASSED** | High - globally recognized landmark | 3,081 ms | False |
| **Colosseum** | `The Colosseum, Rome/Italy` | **False** | False | **PASSED** | High - globally recognized landmark | 3,348 ms | False |
| **Mysore Palace** | `Mysore Palace, Mysore, India` | **False** | False | **PASSED** | High - iconic Amba Vilas profile | 3,828 ms | False |
| **Red Fort** | `Red Fort, Delhi` | **False** | False | **PASSED** | High - iconic Mughal silhouette | 3,327 ms | False |
| **Golden Temple** | `Harmandir Sahib (Golden Temple), Amritsar` | **False** | False | **PASSED** | High - iconic religious monument | 3,400 ms | False |

### 5.2 Curatorial Visual Evidence Highlights
- **Eiffel Tower**: *"The image displays the iconic wrought-iron lattice tower structure... features a distinct tapering silhouette, four arched legs converging into a single vertical column, and a complex network of crisscrossing metal trusses."* (Styles: Structural Expressionism, Industrial Architecture).
- **Colosseum**: *"Massive elliptical amphitheater characterized by a multi-tiered facade featuring superimposed orders of columns (Doric/Tuscan, Ionic, Corinthian)... use of travertine limestone, tuff, and brick-faced concrete."* (Styles: Roman Imperial, Classical Antiquity).
- **Mysore Palace**: *"Exhibits a distinct Indo-Saracenic architectural style, characterized by a symmetrical facade, a central elevated tower, and multiple red-domed turrets... cusped arches, intricate balconies."* (Styles: Indo-Saracenic, Hindu-Gothic, Rajput-Mughal fusion).
- **Red Fort**: *"Displays the iconic Lahori Gate entrance of the Red Fort in Delhi. Key features include massive red sandstone curtain walls, crenellated parapets, and flanking octagonal towers with chhatris."* (Styles: Mughal Architecture, Indo-Islamic Architecture).
- **Golden Temple**: *"Two-story rectangular building covered in gold leaf, featuring a central dome and four smaller chhatris situated in the middle of a large sacred pool (sarovar)... marble base with pietra dura inlay."* (Styles: Sikh Architecture, Rajput-Mughal elements).

---

## 6. Deterministic Offline Fallback Validation

To guarantee uninterrupted operational readiness when network or API limits are encountered:

| Specimen | Mode | Proposed Identity | Is Catalog? | Curatorial Caveat Attached? | Latency |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Eiffel Tower** | Offline Fallback | `None` | `False` | Yes | 0.04 ms |
| **Colosseum** | Offline Fallback | `None` | `False` | Yes | 0.05 ms |

**Offline Fallback Statement**:  
*"Offline Curatorial Mode: Tier-1 CLIP similarity remained below 0.80 threshold with no confident nearest neighbor."*  
**Curatorial Caveat**:  
*"Visual analysis is exploratory and does not establish verified historical identity without epigraphical or archival records."*

---

## 7. Full Regression Test Matrix

| Test Suite File | Test Count | Result | Core Governance Capability Verified |
|:---|:---:|:---:|:---|
| `backend/test_gemini_integration.py` | 12 | **PASSED** | 12 Scenarios (Auth failure, 429 backoff, timeouts, offline fallback, grounded Q&A, live request) |
| `backend/test_api.py` | 6 | **PASSED** | Health check reports `gemini-3.1-flash-lite`, verify endpoint, catalog, exception logs |
| `backend/test_e2e_user_journey.py` | 12 | **PASSED** | 12 End-to-end user journeys (monument verification, Ask the Archive live Q&A) |
| `backend/test_uncertainty.py` | 13 | **PASSED** | 5 Canonical decision states, multi-evidence Qutub corroboration rule, GPS conflict rules |
| `frontend` (Vite Build) | 1 | **PASSED** | Production bundle compiled in 9.70s with zero errors |
| **Total** | **44 / 44** | **100% PASS** | **Zero Regressions** |

---

## 8. Preserved Invariants & Non-Negotiable Governance

- **Policy A Remains Authoritative**: Tier 1 (CLIP ViT-B/32 + FAISS IndexFlatIP + Zero-Shot Gatekeeper + Uncertainty Engine) remains the sole authoritative arbiter of monument verification.
- **Tier 2 Remains Non-Overriding**: Gemini Tier-2 outputs exploratory architectural analyses for unindexed or ambiguous specimens. It cannot force a `VERIFIED_MATCH` or override Policy A.
- **Numerical Confidence Decoupling**: Gemini qualitative confidence descriptions (`confidence_description`) are strictly textual and isolated from calibrated probabilities ($T=0.1082$).
- **No FAISS or Gallery Mutations**: The 210-vector FAISS index and reference gallery remain completely untouched.
- **Git State**: Zero Git commits or pushes made.

---

## 9. Live System Status & Instructions

Both backend and frontend services remain running in daemon mode:
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Frontend Application**: [http://localhost:5173](http://localhost:5173)

### Verification via Python or cURL:
```python
import requests

with open("backend/datasets/phase_8_5c_ooc_eval/eiffel_tower.jpg", "rb") as f:
    resp = requests.post("http://127.0.0.1:8000/api/verify-monument", files={"file": ("eiffel_tower.jpg", f, "image/jpeg")})
data = resp.json()

print(data["verification_status"])  # "UNKNOWN_HERITAGE_SPECIMEN"
print(data["tier2_analysis"]["proposed_identity"])  # "Eiffel Tower, Paris/France"
print(data["tier2_analysis"]["is_catalog_monument"])  # False
```

