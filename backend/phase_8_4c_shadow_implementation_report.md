# Phase 8.4C — Controlled Shadow Staging Implementation Report
**Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)**  
*Role: Senior ML Systems Engineer & Production Reliability Engineer*  
*Timestamp: November 7, 2026*  
*Status: IMPLEMENTED & RIGOROUSLY VALIDATED (12/12 Invariant Tests Passing)*

---

## 1. Executive Summary

In accordance with the Phase 8.4B prospective validation findings and staging recommendations, **Candidate Policy D (Conservative Hybrid Recognition)** has been implemented in **shadow staging mode** alongside the authoritative **Policy A (Production Baseline)**.

The implementation strictly satisfies all production invariants:
1. **Policy A remains 100% authoritative**: The live user response, confidence score, monument name, and decision state are generated exclusively by Policy A and returned without alteration.
2. **True Shadow Observation**: Candidate Policy D runs asynchronously in detached background threads. Policy D has zero write access to the HTTP response payload.
3. **Strict Resource and Latency Isolation**: A hard timeout budget of 500 ms is enforced. A bounded worker pool (max 2 threads) and bounded queue (max 10 items) prevent CPU starvation and queue explosion under load.
4. **Resilient Failure Decoupling**: Any timeout, CUDA/SIFT exception, or telemetry I/O error within Policy D is trapped and logged without affecting the production recognition endpoint.
5. **Fail-Safe Kill Switch**: Defaults to **DISABLED** (`ENABLE_SHADOW_CANDIDATE_POLICY_D=false`). Can be toggled dynamically at runtime without service restart.
6. **No Structural Rewrites**: Preserves all 5 canonical decision states, the 210-vector FAISS index, Platt calibration parameters, and zero Gemini decision override.

---

## 2. Production Architecture & Asynchronous Request Lifecycle

### 2.1 Sequence and Control Flow

```
User Upload (/api/verify-monument)
       │
       ▼
[Image Validation & EXIF Parsing]
       │
       ▼
[CLIP Feature Extraction & Architectural Gatekeeper]
       │
       ▼
[Multi-Candidate FAISS Query (210 Vectors, 10 Monuments)]
       │
       ▼
[Uncertainty Engine Evaluation (Policy A)]
       │
       ▼
[Optional Local Features & Gemini Tier-2 Fallback]
       │
       ▼
[Construct Authoritative VerificationResponse] (Policy A)
       │
       ├────────────────────────────────────────┐
       │ (Synchronous / Immediate Return)       │ (Asynchronous Dispatch if enabled)
       ▼                                        ▼
[HTTP 200 OK Returned to User]           [ShadowEngine.submit_shadow_evaluation()]
                                                │
                                         [Admission Control]
                                         (Queue full? -> Drop with SHADOW_SKIPPED_CAPACITY)
                                                │
                                         [ThreadPoolExecutor (Max 2 Workers)]
                                                │
                                         [Policy D Evaluation (SIFT + Local CLIP)]
                                         (Timeout > 500ms? -> SHADOW_TIMEOUT)
                                         (Exception? -> SHADOW_ERROR)
                                                │
                                                ▼
                                  [ShadowTelemetryLogger (Mutex-Protected JSONL)]
                                  (backend/telemetry/shadow_staging_audit.jsonl)
```

### 2.2 Core Component Specifications

| Component | Implementation File | Key Guarantees |
| :--- | :--- | :--- |
| **Shadow Config** | `backend/shadow_engine.py` | Priority resolution: runtime override $\to$ env var $\to$ JSON config $\to$ default `False`. Malformed values fail safely to disabled. |
| **Admission Queue** | `queue.Queue(maxsize=10)` | Non-blocking `put_nowait()`. Rejects excess tasks with `SHADOW_SKIPPED_CAPACITY` to prevent thread/memory exhaustion. |
| **Worker Pool** | `ThreadPoolExecutor(max_workers=2)` | Dedicated thread prefix `policy_d_shadow_worker`. Detached daemon execution. |
| **Deadline Guard** | 500 ms Hard Budget | SIFT matching and local CLIP check early-exit timestamps against deadline budget. Exceeded tasks log `SHADOW_TIMEOUT`. |
| **Telemetry Logger** | `ShadowTelemetryLogger` | Mutex-locked JSONL appending. Strict sensitive data redaction (zero raw images, zero raw bytes, zero API keys). Disk errors never bubble up. |
| **Platform Shutdown** | `atexit` + FastAPI Lifespan | Non-blocking cancellation and graceful termination during server shutdown. |

---

## 3. Candidate Policy D Logic in Shadow Mode

Candidate Policy D evaluates evidence according to the frozen Phase 8.4 specification:
1. **Severe Non-Monument Gate**: If architectural gatekeeper score $< 0.45 \implies$ `NON_MONUMENT_REJECTED`.
2. **Review Corridor**: If gatekeeper $\in [0.45, 0.50)$ or top-1 cosine similarity $\in [0.70, 0.75) \implies$ `REVIEW_REQUIRED`.
3. **Unknown Heritage Gate**: If top-1 similarity $< 0.70 \implies$ `UNKNOWN_HERITAGE_SPECIMEN`.
4. **Decisive Match Gate**: If similarity margin $\ge 0.08 \implies$ `VERIFIED_MATCH`.
5. **Corroborated Recovery Corridor**: If margin $\in [0.05, 0.08)$:
   - Evaluates SIFT/RANSAC geometric inliers against cached reference images of the top candidate ($\ge 10$ inliers).
   - If SIFT is ambiguous, falls back to 3x3 multi-crop local CLIP consistency ($\ge 0.80$ mean similarity and gatekeeper $\ge 0.65$).
   - If either corroboration holds $\implies$ **promoted to `VERIFIED_MATCH`**.
   - Otherwise $\implies$ remains `UNCERTAIN_MATCH`.

---

## 4. Automated Verification Results (12/12 Requirements Passed)

Automated testing was conducted via `python backend/test_shadow_staging.py`. Full structured results are persisted in `backend/phase_8_4c_shadow_test_report.json`.

| No. | Test Invariant | Status | Duration | Measured Behavior |
| :---: | :--- | :---: | :---: | :--- |
| **1** | Production response identical with shadow enabled vs disabled | **PASSED** | 3461.9 ms | 11/11 response fields identical; 0 divergence observed |
| **2** | Candidate Policy D cannot overwrite or alter Policy A response | **PASSED** | 134.7 ms | Mock Policy D override completely isolated; 0 leakage |
| **3** | Shadow timeout does not delay API response beyond budget | **PASSED** | 241.8 ms | API returned in 189.9 ms despite worker running a slow task |
| **4** | Policy D exception does not fail Policy A recognition | **PASSED** | 108.6 ms | HTTP 200 returned; SIFT exception safely trapped |
| **5** | Disabled mode submits zero background tasks or queue items | **PASSED** | 106.1 ms | Queue length unchanged; submission rejected with `SHADOW_DISABLED` |
| **6** | Queue saturation drops candidate tasks safely | **PASSED** | 7.6 ms | Excess tasks dropped immediately with `SHADOW_SKIPPED_CAPACITY` |
| **7** | Telemetry correctly records all divergence taxonomy categories | **PASSED** | 7.0 ms | `AGREEMENT`, `UPGRADE`, `DOWNGRADE`, `UNVERIFIED_AGREEMENT`, `OUT_OF_CATALOG_NEGATIVE_REJECTION` verified |
| **8** | Shadow timeout emits accurate timeout telemetry event | **PASSED** | 315.4 ms | `event_type="SHADOW_TIMEOUT"`, elapsed time recorded accurately |
| **9** | Shadow execution error emits accurate error telemetry | **PASSED** | 113.0 ms | `event_type="SHADOW_ERROR"` with error details logged |
| **10** | Telemetry write failure does not break recognition | **PASSED** | 89.8 ms | Disk write error swallowed gracefully; API returned HTTP 200 |
| **11** | Dynamic kill switch immediately prevents new tasks | **PASSED** | 0.1 ms | Instant deactivation; immediate `SHADOW_DISABLED` response |
| **12** | Clean shutdown terminates executor without telemetry corruption | **PASSED** | 15.6 ms | Executor safely terminated; zero corrupted JSON lines |

**Overall Test Suite Result**: **12 / 12 PASSED (100%)**

---

## 5. Pre-Existing Regression & Platform Verification

To ensure zero regressions across the codebase:
- **`backend/test_uncertainty.py`**: **13 / 13 PASSED (100%)**
- **`backend/test_api.py`**: **6 / 6 PASSED (100%)**
- **Frontend Build (`npm --prefix frontend run build`)**: **PASSED in 9.66s** with zero TypeScript or bundling errors.

---

## 6. Frozen Configuration & System State

All frozen platform artifacts remain unperturbed:
- **FAISS Reference Index (210 vectors)**: SHA-256 `519620C2B6C9EDAF3A91D5C67D05F8FBDD5DE344E629065CA8BBC46E5E55C603`
- **Platt Calibration Parameters**: Status `EXPERIMENTAL_CALIBRATED` ($A=4.2622, B=-3.5748$)
- **Kill-Switch Configuration**: Default `ENABLE_SHADOW_CANDIDATE_POLICY_D=false`
- **Git Commit / Push Status**: **Zero commits, zero pushes** (clean development sandbox preserved).

