# PHASE 13.4 — PRODUCTION DEPLOYMENT & VERIFICATION REPORT

**Project:** Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH25052)<br>
**Release:** Phase 13.4 Gemini Fallback Timeout Hardening & Concurrency Remediation<br>
**Deployment Date & Timestamp:** 2026-11-10 21:18:00 IST<br>
**Environment:** Live Production (Railway Backend + Vercel Frontend + GitHub Repository)<br>
**Status:** **CONTROLLED PRODUCTION RELEASE SUCCESSFUL**

---

## 1. Production Deployment Identifiers

| Attribute | Deployment Target & Reference Value | Status |
|---|---|:---:|
| **GitHub Repository** | `https://github.com/humaidmalik63-png/Heritage-Recognisation-System.git` | Synced |
| **Branch** | `main` (Fast-forward push, no force-push) | Verified |
| **Previous Production Baseline** | `3423900883c175035235bb957fc2dea738d44480` | Clean Base |
| **Core Hardening Release Commit** | `d4f8998055ec62a15eef63d8b5fe1af376516f8d` (`fix: harden Gemini fallback timeout and concurrency handling`) | Pushed |
| **Production Dependency Commit** | `4f2066b0a70176ceb7405be7dbe989a64e1074eb` (`fix(deps): add httpx to production requirements`) | Pushed |
| **Railway Project ID** | `9dc4c439-1411-4c92-ac5b-d75cac793462` (Environment: `6161ed3c-5f69-4638-831c-40ffb06b2420`) | Active |
| **Railway Service ID** | `backend` (`ae9feabc-0a45-465e-a180-a23c37eb56d1`) | Active |
| **Railway Deployment ID** | `3defd35b-f448-4982-8b91-77c12c9a74b2` | **Online** |
| **Railway Backend Service URL** | `https://backend-production-b023b.up.railway.app` | **Online** |
| **Vercel Project ID** | `prj_ksIRRmXYii03c3Us2fdPvdMblq61` (`team_zz0tj76JbJLveip0iH68Bw62`) | Active |
| **Vercel Deployment ID** | `dpl_AhKFJ94iF93GZXjtgiRnYB5qBwbH` | **Ready** |
| **Vercel Production Canonical Alias** | `https://heritage-monuments.vercel.app` | **Active** |
| **Vercel Production Deployed Bundle** | `/assets/index-Ce-UBkDf.js` (CSS: `/assets/index-DzD16VQ6.css`) | **Verified** |

---

## 2. Pre-Deployment Local Regression Gate Results

Every test suite was executed locally before push. No assertions were bypassed or weakened:

| Test Suite | Scope & Invariants Tested | Result | Duration |
|---|---|:---:|:---:|
| **Phase 13.4C Concurrency Lifecycle** | Atomic admission semaphore, worker slot retention, 10-request barrier | **4 / 4 PASSED** | 5.04s |
| **Phase 13.4B Timeout & Concurrency Audit** | Executor singleton lifecycle, deadline budget, thread capping, fallback invariants | **5 / 5 PASSED** | 25.10s |
| **Phase 13.4 Gemini Fallback & Resilience** | 16 failure scenarios: 429 quota, 401/403 auth, 404 model, timeout, 503 retry, etc. | **16 / 16 PASSED** | 8.09s |
| **Phase 11 Security Hardening Suite** | Auth enforcement, IDOR, SVG/malware filter, upload size, rate limiting | **17 / 17 PASSED** | 10.24s |
| **Phase 6.3 Grounded Knowledge Engine** | Grounded Q&A, citation verification, anti-hallucination refusal | **10 / 10 PASSED** | 33.20s |
| **Phase 12 Catalogue Service Tests** | Authoritative 100-site membership lookup, alias resolution, coordinate binding | **15 / 15 PASSED** | 0.80s |
| **Phase 12 Uncertainty Engine Tests** | Calibrated margin thresholds, GPS conflict, blur rejection, duplicate suppression | **13 / 13 PASSED** | 4.85s |
| **Phase 12 Frontend Hook Stability** | 14 dispatcher scenarios, unconditional hook order invariants across drawers | **14 / 14 PASSED** | 1.12s |
| **Phase 12 Frontend Monograph States** | 7 discrete monograph views (Verified, Uncertain, Metadata-only, Out-of-catalog, etc.) | **7 / 7 PASSED** | 0.64s |
| **Phase 10.3 Viewport Capture** | 11 mobile & desktop responsive viewports captured cleanly | **11 / 11 CAPTURED** | 14.80s |
| **Frontend Production Build** | Vite production compilation, module tree shaking, chunk splitting | **PASSED** (0 errors) | 10.31s |

---

## 3. Live Production Backend Verification (Railway)

All verification requests were executed directly against `https://backend-production-b023b.up.railway.app`:

### A. Health & Architecture Invariants
- `GET /api/health` -> HTTP 200 OK
- Response:
  ```json
  {
    "status": "healthy",
    "faiss_vectors_loaded": 577,
    "clip_device": "cpu",
    "gemini_tier2_configured": true,
    "gemini_tier2_model": "gemini-3.1-flash-lite",
    "monuments_count": 100,
    "catalogue_100_count": 100,
    "knowledge_records_count": 10,
    "exceptions_count": 3,
    "calibration_status": "EXPERIMENTAL_CALIBRATED"
  }
  ```
- All 577 FAISS vectors loaded.
- 100 monument metadata records in memory.
- CLIP ViT-B/32 active on CPU.
- Gemini Tier-2 model strictly preserved as `gemini-3.1-flash-lite`.

### B. Live Security Hardening
- `GET /api/exceptions` (Anonymous): HTTP 401 Unauthorized (`{"detail":"Unauthorized: Valid administrator authentication required."}`)
- `GET /api/telemetry/gemini` (Anonymous): HTTP 401 Unauthorized (`{"detail":"Unauthorized: Valid administrator authentication required."}`)
- `GET /api/telemetry/status` (Public): HTTP 200 OK (`{"status":"online","model_family":"gemini-3.1-flash-lite"}`)
- `POST /api/verify-monument` (>15MB): HTTP 413 Content Too Large (`{"detail":"Payload exceeds 15 MB limit."}`)

### C. Live Recognition & Uncertainty Preservation
- **Taj Mahal Specimen:** Returned `VERIFIED_MATCH` (`Taj Mahal`), verification tier `TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX`, grounded citations payload present.
- **Petra Specimen:** Returned `VERIFIED_MATCH` (`Petra`), authentic coordinates bound, zero asset loading errors.
- **Non-Monument Specimen (Blank):** Returned `NON_MONUMENT_REJECTED`, processing modal immediately dismisses.
- **Unindexed Specimen:** Uncertainty strictly preserved; never falsely elevated to `VERIFIED_MATCH`; zero fabricated citations.

---

## 4. Live Production Frontend Verification (Vercel)

Verified directly against `https://heritage-monuments.vercel.app`:

### A. Security Headers & Edge Delivery
- `Strict-Transport-Security`: `max-age=63072000; includeSubDomains; preload`
- `X-Frame-Options`: `DENY`
- `X-Content-Type-Options`: `nosniff`
- `Content-Security-Policy`: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://*.tile.openstreetmap.org https://backend-production-b023b.up.railway.app; connect-src 'self' https://backend-production-b023b.up.railway.app ...`

### B. Production Bundle & Asset Verification
- Production HTML references new bundle: `<script type="module" crossorigin src="/assets/index-Ce-UBkDf.js"></script>`
- Bundle verified free of `curator123`, `DEFAULT_DEMO_USER`, and demo credentials.
- Essential heritage reference assets verified live on production CDN:
  - `/assets/heritage/petra.jpg`: HTTP 200 (348,903 bytes)
  - `/assets/heritage/taj-mahal.jpg`: HTTP 200 (310,707 bytes)
  - `/assets/heritage/colosseum.jpg`: HTTP 200 (149,987 bytes)

---

## 5. Live User Journey & Processing Modal Resolution

1. **Processing Overlay Lifecycle:**
   - Previous Issue: Modal stalled indefinitely at `Synthesizing Curatorial Dossier & Linked Stamps...`.
   - Remediated: The frontend API call now enforces a client-side `AbortController` signal (20s ceiling). The backend enforces a 8.0s Tier-2 call timeout and 9.5s overall deadline.
   - On completion, offline fallback, or error, `setIsLoading(false)` unconditionally executes in `finally`, closing the modal immediately.
2. **Offline Fallback Display:**
   - When Gemini is unavailable, saturated, or times out, the platform presents the enriched deterministic local monograph with candidate catalogue facts, an offline indicator, and an active **Retry** option.
   - The interface never locks or hangs.

---

## 6. Rollback & Emergency Continuity Plan

- **Rollback Points:**
  - Git: `git revert 4f2066b d4f8998` or `git reset --hard 3423900883c175035235bb957fc2dea738d44480 && git push --force`
  - Railway: Instant rollback to deployment `c4597759-6e4c-47bb-8b3a-47d37f2cfea7` via Railway dashboard.
  - Vercel: Instant rollback to deployment `dpl_JDMDVvEZm22fm4UmwhQRjt7WxYr5` (`vercel alias set frontend-1q0bf4nm5-humaidmalik63-png.vercel.app heritage-monuments.vercel.app`).
- **Rollback Status:** Not required. Both services are 100% operational and healthy.

---

## 7. Known Operational Boundaries

- **Google GenAI API Spikes:** Intermittent 503 / 504 spikes from Google's Generative Language API are now safely absorbed by the single bounded retry and immediate fallback to deterministic Tier-1 catalogue facts within $< 3\text{s}$.
- **CPU Inference Device:** Running on PyTorch CPU in Railway cloud instance with 2 threads (`TORCH_NUM_THREADS=2`), yielding $\approx 350\text{ms}$ embedding extraction times for live monument verification.
