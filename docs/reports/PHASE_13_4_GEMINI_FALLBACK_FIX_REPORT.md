# PHASE 13.4, 13.4B & 13.4C — GEMINI TIER-2 FALLBACK, TIMEOUT & CONCURRENCY VALIDATION REPORT

**Project:** Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH25052)<br>
**Status:** All Verification & Concurrency Lifecycle Tests Passed (Ready for Production Release)<br>
**Target Infrastructure:**
- Frontend: Vercel (`https://heritage-monuments.vercel.app`)
- Backend: Railway (`https://backend-production-b023b.up.railway.app`)
- GitHub Repository: `https://github.com/humaidmalik63-png/Heritage-Recognisation-System.git`
- Branch: `main`
- Authorized Model: `gemini-3.1-flash-lite`
- Local Host Test Environments: Backend on `http://127.0.0.1:8000`, Frontend on `http://localhost:5173`

---

## 1. Executive Summary & Problem Diagnosis

### The Observed Problem
On the live production platform (`https://heritage-monuments.vercel.app`), users uploading certain specimens or selecting test samples experienced a severe interface stall during monument recognition. The processing modal cycled through stages 1 to 5:
1. Validating Image Byte Stream & Color Space
2. Extracting EXIF GPS Metadata & Geodetic Coordinates
3. Computing 512-D Vision Features via CLIP ViT-B/32
4. Evaluating Zero-Shot Architectural Gatekeeper
5. Searching 577-Anchor FAISS Inner-Product Vector Index

It then stalled at stage 6:
`Synthesizing Curatorial Dossier & Inked Stamps...`

If the request eventually returned after 60–120+ seconds, the user was presented with:
`OFFLINE FALLBACK` badge and:
`Automated Tier-2 service temporarily unavailable; flagged for expert curatorial inspection.`

In intermittent network failure or unhandled edge conditions, the processing overlay remained on screen indefinitely with no cancel or retry option.

---

## 2. Request Lifecycle & Root Cause Trace

| # | Component | Root Cause | Impact |
|---|-----------|------------|--------|
| **1** | `backend/gemini_service.py` | `DEFAULT_TIMEOUT_SECONDS = 15.0` was defined but never passed to `types.HttpOptions` or `generate_content` call config. Sockets defaulted to system/TCP defaults (up to 60s). | Remote calls hung for tens of seconds waiting on remote response. |
| **2** | `backend/gemini_service.py` | `MAX_RETRIES = 3` with exponential backoff (`(2**attempt)*1.0 + jitter`). On 503 / 429 or network degradation, 4 full attempts were executed with sleeps, cumulating in **120+ seconds** total wait time. | Entire HTTP request blocked, causing Railway edge timeout or 2+ minute client stalls. |
| **3** | `backend/gemini_service.py` | No overall wall-clock deadline budget. Each retry had no awareness of total request elapsed time. | Requests continuously retried even when deadline had expired. |
| **4** | Google GenAI SDK | Google's Generative Language API enforces a minimum deadline constraint of 10s (`400 INVALID_ARGUMENT: Manually set deadline 8s is too short. Minimum allowed deadline is 10s.`) if sub-10s timeouts are sent in the deadline header. | Sending `timeout=8000` to Google resulted in 400 Bad Request, whereas passing `max(timeout_ms, 10000)` satisfies Google's API while local client-side `ThreadPoolExecutor` and `httpx` strictly enforce 8.0s. |
| **5** | `backend/main.py` | Synchronous invocation of `gemini_service.adjudicate_monument` lacked a bounded timeout wrapper and did not enrich fallback responses with local Tier-1 candidate knowledge. | Fallback showed empty "Automated Tier-2 service temporarily unavailable" rather than a functional local monograph. |
| **6** | `frontend/src/api.js` | `verifyMonumentImage` lacked an `AbortController` timeout signal. | If backend or edge proxy stalled, browser fetch hung forever. |
| **7** | `frontend/src/pages/Dashboard.jsx` | `handleSampleSelect` for `'non_monument'` used `canvas.toBlob` callback without wrapping `verifyMonumentImage` in `try...catch...finally`. Any error prevented `setIsLoading(false)` from running. | Processing modal remained stuck on screen permanently. |
| **8** | `frontend/src/components/ProcessingOverlay.jsx` | Stages stepped through on a 450ms timer up to stage 6 (2.7s), then froze indefinitely on `Synthesizing Curatorial Dossier & Inked Stamps...` with no timeout feedback or escape hatch. | User perceived system as frozen. |

---

## 3. Phase 13.4B Timeout Correctness Audit & Deep-Dive

### A. ThreadPoolExecutor & Context Manager Audit
- **Context Manager Check**: Inspected all uses of `ThreadPoolExecutor`. The Tier-2 executor `_tier2_executor` is a module-level global singleton pool (`max_workers=4, thread_name_prefix="tier2_vlm"`). It is **not** managed within a `with` statement, ensuring that `executor.__exit__` -> `executor.shutdown(wait=True)` is **never** invoked upon request completion or timeout.
- **Future Timeout & Cancellation**: In `_execute_with_retry`, when `fut.result(timeout=call_timeout)` raises `concurrent.futures.TimeoutError`, `fut.cancel()` is immediately called. If the task was still queued, it is removed from the queue and never executed.
- **Immediate Return**: The calling FastAPI thread catches `TimeoutError` and returns immediately to the HTTP client with the deterministic local fallback without waiting for the worker thread.
- **Transport-Level Protection**: Underneath Google's GenAI SDK, requests are executed via `httpx.send(..., timeout=http_request.timeout)`. The request timeout is set to 10.0s (conforming to Google's minimum header constraint). Even if a remote socket hangs, `httpx` terminates the socket connection after 10.0s, ensuring worker threads are never stranded.

### B. Actual Measured Overall Deadline Verification
- We tested with a mocked Gemini request that deliberately blocked for 15.0s (with a configured `timeout=4.0s`).
- **Actual Measured Caller Duration**: `4.008s` (from calling function invocation until return). The caller returned in **4.008s**, strictly bounded by the execution timeout budget.
- Multi-attempt budget enforcement: On transient 503 errors, the overall deadline (`OVERALL_DEADLINE_SECONDS = 9.5s`) dynamically reduces the remaining call budget (`call_timeout = min(self.timeout, remaining_budget)`). The actual pipeline elapsed time on 503 retry was measured at `9.51s`, exactly matching the 9.5s wall-clock ceiling.

---

## 4. Phase 13.4C Atomic Admission Control & Worker Lifecycle Validation

### A. Atomic Admission Control vs. Check-Then-Act Race Condition
In high-concurrency environments, checking `_work_queue.qsize() >= 4` is vulnerable to a classic check-then-act race condition: multiple requests arriving within microseconds can all observe `qsize() < 4`, submit concurrently, and flood the executor with queued tasks.

**Remediation:**
Implemented atomic admission control using `threading.BoundedSemaphore(value=TIER2_MAX_WORKERS)`:
```python
TIER2_MAX_WORKERS = 4
_tier2_admission_semaphore = threading.BoundedSemaphore(value=TIER2_MAX_WORKERS)
```
In `_execute_with_retry()`:
1. `admitted = _tier2_admission_semaphore.acquire(blocking=False)` provides an atomic test-and-decrement in $\mathcal{O}(1)$.
2. If `not admitted`, the request immediately fast-fails to local fallback with error category `"POOL_SATURATED"`.
3. No task is submitted to the executor queue. The queue size remains **strictly 0**.
4. The permit is released **strictly** upon worker task completion via `fut.add_done_callback(lambda f: _tier2_admission_semaphore.release())`.

### B. Worker Lifecycle & Slot Holding Audit
- **In-Flight Protection**: When callers time out (e.g. at 1.5s) while background worker threads are still running (e.g. taking 3.0s), the admission slot **remains acquired**.
- **No Premature Release**: The slot is released **only** when the background thread actually terminates.
- **Verification**: In `test_2_worker_lifecycle_and_slot_holding`, 4 workers blocked for 3.0s while callers timed out at 1.0s. At $t = 1.01\text{s}$, callers had safely returned, but a probe request was rejected immediately (`reason='Tier-2 worker pool saturated...'`, latency `1.14ms`). Once workers finished at $t = 3.30\text{s}$, subsequent requests acquired permits normally.

### C. Ten-Request Synchronized Concurrency Breakdown

Ten requests were synchronized via `threading.Barrier(10)` to submit at the exact same microsecond with an injected 10-second Gemini hang:

| Req # | Submit Time ($t$) | Return Time ($t$) | Duration | Disposition | Reason / Monograph State |
|:---:|:---:|:---:|:---:|:---:|:---|
| **0** | +0.000s | +1.508s | 1.508s | `ADMITTED_INVOKED` | Admitted; timed out at 1.5s; offline fallback returned |
| **1** | +0.000s | +1.508s | 1.508s | `ADMITTED_INVOKED` | Admitted; timed out at 1.5s; offline fallback returned |
| **2** | +0.000s | +1.508s | 1.508s | `ADMITTED_INVOKED` | Admitted; timed out at 1.5s; offline fallback returned |
| **3** | +0.000s | +1.508s | 1.508s | `ADMITTED_INVOKED` | Admitted; timed out at 1.5s; offline fallback returned |
| **4** | +0.000s | +0.003s | 0.003s | `REJECTED_SATURATION` | Saturation fast-fail; offline fallback returned in 3ms |
| **5** | +0.000s | +0.003s | 0.003s | `REJECTED_SATURATION` | Saturation fast-fail; offline fallback returned in 3ms |
| **6** | +0.000s | +0.003s | 0.003s | `REJECTED_SATURATION` | Saturation fast-fail; offline fallback returned in 3ms |
| **7** | +0.000s | +0.004s | 0.004s | `REJECTED_SATURATION` | Saturation fast-fail; offline fallback returned in 4ms |
| **8** | +0.000s | +0.004s | 0.004s | `REJECTED_SATURATION` | Saturation fast-fail; offline fallback returned in 4ms |
| **9** | +0.000s | +0.004s | 0.004s | `REJECTED_SATURATION` | Saturation fast-fail; offline fallback returned in 4ms |

#### Why Wall-Clock Duration is 1.51s / 2.14s:
- The 4 admitted requests run concurrently and each wait up to the caller timeout ceiling ($1.50\text{s}$). They all finish at $t \approx 1.508\text{s}$.
- The 6 rejected requests fail the non-blocking semaphore check immediately and return within $2\text{--}4\text{ms}$.
- Because the calls are concurrent, the total wall-clock duration of the test is determined by $\max(\text{caller\_return\_times}) \approx 1.508\text{s}$. With thread spawn/join overhead in test harnesses, total execution completes in $1.51\text{s} - 2.14\text{s}$, completely eliminating the previous 120s cascade.

### D. Fallback Safety & Immutability
- **Late Worker Isolation**: Worker threads executing in the background have zero reference to the returned HTTP response object. When a late worker finishes, its result is discarded; it cannot mutate, corrupt, or alter the monograph already delivered to the client.
- **Uncertainty Preservation**: The pipeline maintains `REVIEW_REQUIRED` (or `UNCERTAIN`). It never fabricates citations and never promotes an unverified match to `VERIFIED_MATCH`.

---

## 5. Comprehensive Regression & Test Verification

| Test Suite | Command | Cases | Result | Duration |
|---|---|---|---|---|
| **Phase 13.4C Concurrency & Lifecycle** | `python test_phase_13_4c_concurrency_lifecycle.py` | 4 Scenarios | **4 / 4 PASSED** | 5.04s |
| **Phase 13.4B Timeout & Concurrency Audit** | `python test_phase_13_4b_audit.py` | 5 Scenarios | **5 / 5 PASSED** | 25.10s |
| **Phase 13.4 Gemini Fallback & Resilience** | `python test_phase_13_4_gemini_fallback.py` | 16 Scenarios | **16 / 16 PASSED** | 8.57s |
| **Phase 11 Security Hardening Suite** | `python test_phase_11_security.py` | 17 Hardening Cases | **17 / 17 PASSED** | 10.37s |
| **Phase 6.3 Grounded Knowledge Engine** | `python backend/test_knowledge_engine.py` | 10 Engine Cases | **10 / 10 PASSED** | 33.20s |
| **Phase 12 Catalogue Service Tests** | `pytest backend/test_catalogue_service.py` | 15 Cases | **15 / 15 PASSED** | 0.80s |
| **Phase 12 Uncertainty Engine Tests** | `pytest backend/test_uncertainty.py` | 13 Cases | **13 / 13 PASSED** | 4.85s |
| **Phase 12 Frontend Hook Stability** | `node frontend/verify_hook_stability.cjs` | 14 Invariants | **14 / 14 PASSED** | 1.12s |
| **Phase 12 Frontend Monograph States** | `node frontend/test_monograph_states.cjs` | 7 Invariants | **7 / 7 PASSED** | 0.64s |
| **Phase 10.3 Viewport Capture** | `python test_phase_10_3_viewports.py` | 11 Viewports | **11 / 11 CAPTURED** | 14.80s |
| **Frontend Production Build** | `npm --prefix frontend run build` | 2,104 Modules | **PASSED** (0 errors) | 10.45s |

---

## 6. Localhost Deployment & Interactive Verification

Both services have been spun up locally for interactive end-to-end verification:
- **FastAPI Backend**: `http://127.0.0.1:8000`
  - Health check: `curl http://127.0.0.1:8000/api/health` -> `{"status":"healthy","faiss_vectors_loaded":577,"clip_device":"cpu","gemini_tier2_configured":true,"gemini_tier2_model":"gemini-3.1-flash-lite","monuments_count":100,"catalogue_100_count":100,"knowledge_records_count":10,"exceptions_count":84,"calibration_status":"EXPERIMENTAL_CALIBRATED"}`
- **React Frontend**: `http://localhost:5173` (Vite dev server)
  - HTTP 200 OK verified.

---

## 7. Controlled Release Gate

> [!IMPORTANT]
> In accordance with the non-negotiable instructions:
> - **All changes have been tested and verified locally only.**
> - **No commits have been created.**
> - **No code has been pushed to GitHub.**
> - **No deployments have been triggered on Railway or Vercel.**
>
> We stand ready to commit, push to `main`, and execute production release as soon as you provide authorization.
