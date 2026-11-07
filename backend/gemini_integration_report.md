# Phase 7.2: Gemini 2.5 Flash Tier-2 Integration & Reliability Report
## Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform
### SIH Reference: SIH25052

---

## 1. Executive Summary

Phase 7.2 establishes a resilient, production-grade integration with **Gemini 2.5 Flash** as a specialized **Tier-2 Exploratory and Interpretive Engine**. 

### Core Architectural Principle: Two-Tier Decoupling
1. **Tier 1 (Deterministic Edge Engine)**:
   - Evaluates images locally using `openai/clip-vit-base-patch32` and an exact L2/Inner-Product `FAISS` vector index (50 anchors across 10 monuments).
   - Enforces Phase 6.2 Uncertainty Engine invariants (`VERIFIED_MATCH`, `UNCERTAIN_MATCH`, `UNKNOWN_HERITAGE_SPECIMEN`, `NON_MONUMENT_REJECTED`, `REVIEW_REQUIRED`).
   - Retains absolute supremacy over recognition decisions.
2. **Tier 2 (Cloud Generative Engine - Gemini 2.5 Flash)**:
   - Operates strictly downstream of Tier 1.
   - **Never overrides Tier 1 vector decisions** (e.g., cannot convert an unknown specimen into a `VERIFIED_MATCH`).
   - Activates conditionally to provide exploratory hypothesis generation, deep architectural feature interpretation, and conversational historical Q&A with strict ASI/UNESCO citation anchoring.

---

## 2. Gemini 2.5 Flash Configuration & Security Invariants

### 2.1 Configuration
- **Target Model**: `gemini-2.5-flash`
- **Environment Variable**: `GEMINI_API_KEY` loaded via `python-dotenv` from `.env`.
- **Masking & Safety**:
  - The API key is masked in all logging, diagnostic outputs, and health endpoints (e.g., `AIzaSy...4xQ9`).
  - `.env.example` provides documentation and secure placeholders only. No raw keys are committed or exposed.
  - If no key is configured, Tier 2 automatically engages deterministic offline fallback routines without raising unhandled exceptions.

---

## 3. Resilience, Fault Tolerance & Telemetry

### 3.1 Retry & Rate-Limit Strategy
- **Bounded Exponential Backoff**: Base delay $1.0\text{ s}$, doubling per retry ($1\text{s} \to 2\text{s} \to 4\text{s}$), with a strict cap of 3 retry attempts.
- **Fail-Fast on Authentication**: HTTP 401/403 or invalid credentials fail immediately on the first attempt without redundant retries.
- **Timeout Protection**: Strict 15-second per-request timeout prevents hanging connections during network degradation.
- **Circuit Protection**: When upstream quotas are exhausted or network access is unavailable, the system safely falls back to local knowledge and cached hypotheses.

### 3.2 Persistent Telemetry (`gemini_usage_telemetry.json`)
A thread-safe telemetry manager logs and aggregates all Tier-2 invocations:
- `total_requests`, `successful_requests`, `failed_requests`
- `total_retries`
- Cumulative and rolling `average_latency_ms`
- Token consumption tracking (`total_input_tokens`, `total_output_tokens`)
- Granular error categorisation: `RATE_LIMIT_429`, `AUTH_INVALID_KEY`, `TIMEOUT`, `SERVER_ERROR_5XX`, `EMPTY_RESPONSE`, `CLIENT_ERROR`
- Per-feature invocation breakdown: `unknown_heritage_analysis`, `grounded_historical_qa`, `architectural_explanation`

Diagnostic telemetry is exposed to curators via `GET /api/telemetry/gemini`.

---

## 4. Implemented Capabilities

### Capability A: Unknown Specimen Exploratory Hypotheses
- **Trigger**: When Tier 1 classifies an image as `UNKNOWN_HERITAGE_SPECIMEN` (or `UNCERTAIN_MATCH`).
- **Function**: Multimodal analysis of visual characteristics (e.g., stone masonry, dome structures, pillar carvings).
- **Invariants**:
  - Emits candidate architectural traditions, probable historical eras, and visual observations.
  - Generates clear cautionary caveats stating the specimen is unindexed and requires field verification.
  - **Does NOT alter** `verification_status = UNKNOWN_HERITAGE_SPECIMEN`.

### Capability B: Grounded Historical Inquiry Assistant
- **Trigger**: User queries via `POST /api/monuments/{monument_id}/ask`.
- **Function**: Synthesizes verified answers strictly bounded by the Archaeological Survey of India (ASI) and UNESCO World Heritage documentation registered in `backend/knowledge_sources.json`.
- **Anti-Hallucination Guardrails**:
  - Refuses speculative, mythical, or unverified claims.
  - Appends mandatory archival citation badges (`[CIT-TAJ-01]`, `[CIT-KNR-01]`).
  - Reverts to deterministic offline extractive QA if Gemini is unavailable.

### Capability C: Visual Architectural Interpreter
- **Trigger**: Curator requests via `POST /api/monuments/{monument_id}/explain-architecture`.
- **Function**: Detailed breakdown of salient architectural motifs (e.g., shikhara curvature, jali lattice work, squinch arches) anchored to the verified monument monograph.

---

## 5. Verification Test Suite Results

The automated test suite in `backend/test_gemini_integration.py` verifies 12 comprehensive scenarios:

| # | Scenario | Expected Behavior | Result |
|---|---|---|:---:|
| 1 | Configuration & Safe Initialization | Key masking, correct model target (`gemini-2.5-flash`) | **PASSED** |
| 2 | Capability A (Multimodal Unknown Analysis) | JSON schema parsed, candidate styles extracted, caveat attached | **PASSED** |
| 3 | Decision Engine Invariant Preservation | Decision remains `UNKNOWN_HERITAGE_SPECIMEN` | **PASSED** |
| 4 | Capability B (Grounded Historical Q&A) | Grounded answers strictly cite ASI/UNESCO source IDs | **PASSED** |
| 5 | Anti-Hallucination Refusal | Speculative inquiries trigger verified refusal response | **PASSED** |
| 6 | Capability C (Architectural Feature Interpretation) | Architectural breakdown returns structured visual analysis | **PASSED** |
| 7 | Bounded Exponential Backoff & Retry | Retries up to 3 times on transient 503 / 500 errors | **PASSED** |
| 8 | Rate-Limit (429) Handling | Exponential backoff delay observed and logged in telemetry | **PASSED** |
| 9 | Request Timeout Enforcement | 15s timeout halts hanging requests, invokes fallback | **PASSED** |
| 10 | Authentication Fail-Fast | 401/403 fails immediately without redundant retries | **PASSED** |
| 11 | Complete Offline Fallback Mode | Deterministic responses when API key is missing | **PASSED** |
| 12 | Telemetry Persistence & Diagnostics | `gemini_usage_telemetry.json` records metrics accurately | **PASSED** |

**Summary**: 12/12 Scenarios Passed (100% test pass rate).

---

## 6. Frontend Integration

1. **`MonographResult.jsx`**:
   - Renders Tier-2 Exploratory AI Hypotheses card for unindexed/ambiguous specimens.
   - Distinctive amber/gold archival styling (`archival-stamp-tier2`) clearly separating vector verification from exploratory AI interpretations.
   - Offline fallback badge and clear curatorial disclaimer.
2. **`api.js`**:
   - `fetchGeminiTelemetry()` for live pipeline diagnostics.
   - `explainMonumentArchitecture(monumentId, file)` for deep-dive architectural exploration.

