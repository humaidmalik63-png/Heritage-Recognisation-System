# PHASE 14 — CONTROLLED PRODUCTION DEPLOYMENT & VERIFICATION REPORT
**Visual Heritage Recognition and Grounded Cultural Discovery Platform (SIH25052)**  
**Deployment Date:** November 10, 2026 | **Environment:** Production (Railway + Vercel) | **Release Status:** PRODUCTION OPERATIONAL

---

## Executive Summary

Phase 14 has been committed, pushed to GitHub `main`, and deployed to production across both **Railway** (backend API) and **Vercel** (frontend application). 

All 10 pre-deployment regression suites, boundary audits, live production health checks, and 10 production smoke tests passed with **100% success**. The user-facing platform is fully operational on its canonical production domains with zero downtime or regressions.

---

## 1. Release Identification & Version Metadata

| Parameter | Value | Notes |
|---|---|---|
| **Repository** | `https://github.com/humaidmalik63-png/Heritage-Recognisation-System.git` | Target branch: `main` |
| **Previous Production Baseline** | `6aa1ef0389eb781048a30932c3d78ce3f256ab60` | Phase 13.4 Rollback Target |
| **New Production Commit SHA** | `d305deb7821bde5e054d56a5656b53e590e7d9fe` | Phase 14 Production Release |
| **Commit Message** | `feat: implement Phase 14 calibrated heritage recognition and UX improvements` | 25 files changed |
| **Railway Backend URL** | `https://backend-production-b023b.up.railway.app` | Docker container on Railway |
| **Vercel Frontend URL** | `https://heritage-monuments.vercel.app` | Canonical domain |
| **Vercel Deployment ID** | `dpl_EzP8ihYd1uJr5MiiDLA5oD6DCNtt` | Project: `heritage-monuments` (`prj_iMCKffts1tkod84uNZRNthLtjB5E`) |
| **Vercel Deployment URL** | `https://heritage-monuments-62pueh9ic-humaidmalik63-png.vercel.app` | Aliased to canonical |

---

## 2. Release Contents (Files Included in Commit `d305deb`)

### 2.1 Backend Pipeline & Calibration Core
1. `backend/calibration.py`: Added configurable `gatekeeper_threshold_rejection = 0.35` and accessor property.
2. `backend/uncertainty.py`: Implemented calibrated Rule 1 (`top1_sim < 0.70 AND gk <= 0.35` $\to$ `NON_MONUMENT_REJECTED`; `0.35 < gk < 0.45` $\to$ `REVIEW_REQUIRED`), score `NaN`/`Inf` sanitization to review quarantine.
3. `backend/knowledge_engine.py`: Grounded knowledge coverage bridged across all 100 heritage catalogue sites.
4. `backend/main.py`: Explainability payload decomposition, engine attribution telemetry, and dynamic knowledge bridging on `/timeline`, `/sources`, and `/ask`.
5. `backend/gemini_usage_telemetry.json`: Telemetry counters updated from audit runs.

### 2.2 Test & Audit Suites
6. `backend/test_knowledge_engine.py`: Test 9 non-monument fixture updated to authentic non-monument specimen; separate assertion for ambiguous flat-white canvas.
7. `backend/test_phase_14_enhancements.py`: Feature verification suite covering 100-site coverage, explainability decomposition, and candidate competition.
8. `backend/test_uncertainty_boundaries.py`: 18 boundary and invariant test cases.
9. `backend/run_paired_evaluation.py`: Three-way paired evaluation harness with Wilson 95% CIs.
10. `backend/phase_14_recognition_benchmark.py`: Benchmark runner.
11. `backend/audit_100_knowledge_coverage.py`: 100-monument integrity audit script.
12. `backend/audit_benchmark_integrity.py`: Benchmark dataset separation audit script.
13. `backend/audit_threshold_calibration.py`: Parameter sweep script.

### 2.3 Evaluation Results & Manifests
14. `backend/phase_14_1_knowledge_coverage_audit.json`: 100% coverage audit results.
15. `backend/phase_14_1_paired_evaluation_results.json`: Cohort 1 & Cohort 2 initial results.
16. `backend/phase_14_2_paired_evaluation_results.json`: Three-way paired benchmark results.
17. `backend/phase_14_evaluation_results.json`: Evaluation telemetry.
18. `backend/phase_14_threshold_calibration_sweep.json`: 56-configuration parameter sweep.

### 2.4 Frontend Enhancements & Mobile Touch
19. `frontend/src/components/MonographResult.jsx`: Explainability and robust offline derivation passed to views.
20. `frontend/src/components/PipelineInspector.jsx`: Visual engine attribution bar, stage latencies breakdown.
21. `frontend/src/mobile/MobileBottomNav.jsx`: WCAG 2.5.5 accessible 44px min touch target enforcement.
22. `frontend/src/mobile/mobile.css`: Smooth scrolling and touch manipulation utility classes.

### 2.5 Documentation & Release Reports
23. `PHASE_13_PRODUCTION_DEPLOYMENT_REPORT.md`: Baseline release audit.
24. `PHASE_14_IMPLEMENTATION_REPORT.md`: Exhaustive diff and implementation report.
25. `PHASE_14_RECOGNITION_EVALUATION.md`: Benchmark evaluation and statistical validation report.

---

## 3. Pre-Deployment Validation Gate Results

All 10 regression suites were executed locally prior to pushing:

| Suite # | Target Domain | Command | Result |
|---|---|---|:---:|
| 1 | Uncertainty Boundaries & Invariants | `python backend/test_uncertainty_boundaries.py` | **18 / 18 PASSED** |
| 2 | React Hook Lifecycle Invariants | `node frontend/verify_hook_stability.cjs` | **14 / 14 PASSED** |
| 3 | Monograph Render States | `node frontend/test_monograph_states.cjs` | **7 / 7 PASSED** |
| 4 | Production Frontend Bundle | `npm --prefix frontend run build` | **CLEAN (12.45s)** |
| 5 | Concurrency & Worker Lifecycle | `python test_phase_13_4c_concurrency_lifecycle.py` | **4 / 4 PASSED** |
| 6 | Uncertainty & Gating Invariants | `python backend/test_uncertainty.py` | **13 / 13 PASSED** |
| 7 | Security & Production Hardening | `python test_phase_11_security.py` | **17 / 17 PASSED** |
| 8 | Fallback & Deadline Timers | `python test_phase_13_4b_audit.py` | **5 / 5 PASSED** |
| 9 | Grounded Knowledge & Gating | `python backend/test_knowledge_engine.py` | **10 / 10 PASSED** |
| 10 | Phase 14 Feature Enhancements | `python backend/test_phase_14_enhancements.py` | **7 / 7 PASSED** |

---

## 4. Railway Backend Deployment Verification

Railway automatically built and deployed commit `d305deb7821bde5e054d56a5656b53e590e7d9fe`.

### Health Check Response (`GET /api/health`):
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
  "exceptions_count": 0,
  "calibration_status": "EXPERIMENTAL_CALIBRATED"
}
```

### Verification Criteria:
- **Deployment Status**: HTTP 200 OK.
- **FAISS Index**: 577 vectors loaded cleanly into index.
- **Catalogue Records**: All 100 heritage catalogue monuments loaded.
- **CLIP ViT-B/32**: Active and computing embeddings on CPU.
- **Gemini 3.1 Flash-Lite**: Operational with non-blocking timeout fallback.
- **Security Protections**: Rate limiting, security headers, and curator authorization active.

---

## 5. Vercel Frontend Deployment Verification

Deployed via Option 3 directly from `frontend/` targeting project `heritage-monuments` (`prj_iMCKffts1tkod84uNZRNthLtjB5E`).

- **Canonical URL**: `https://heritage-monuments.vercel.app` (HTTP 200 OK)
- **Deployment ID**: `dpl_EzP8ihYd1uJr5MiiDLA5oD6DCNtt`
- **Asset Status**: All JavaScript (`index-Bkyo2yKz.js`, `vendor-react`, `vendor-motion`, `vendor-icons`) and CSS (`index-Zc0Uacma.css`) bundles return HTTP 200.
- **Security Headers Active**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: ... connect-src 'self' https://backend-production-b023b.up.railway.app ...`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

---

## 6. Live Production Smoke Tests

All 10 production smoke tests were executed directly against the live production endpoints (`https://backend-production-b023b.up.railway.app` and `https://heritage-monuments.vercel.app`):

| Test # | Test Description | Input Specimen | Production Result | Status |
|---|---|---|---|:---:|
| 1 | Production Health Check | `/api/health` | HTTP 200, 577 vectors, 100 monuments | **PASS** |
| 2 | Known Catalogue Monument | `taj_mahal/ref_01.jpg` | `status: VERIFIED_MATCH`, similarity: 99.8%, match: Taj Mahal | **PASS** |
| 3 | Known Monument Differing View | `split_d_046_taj_mahal.jpg` | `status: UNCERTAIN_MATCH`, score: 88.0%, preserved candidate | **PASS** |
| 4 | Architectural Close-Up / Partial | `feat_charminar_occluded_02.jpg` | `status: REVIEW_REQUIRED`, $gk = 0.3523 \in (0.35, 0.45)$, quarantined | **PASS** |
| 5 | Clear Non-Monument Distractor | `split_d_090_non_monument.jpg` | `status: NON_MONUMENT_REJECTED`, $gk = 0.2987 \le 0.35$, hard-rejected | **PASS** |
| 6 | Blank Canvas Input | Pure white 200x200 JPEG | `status: REVIEW_REQUIRED`, zero knowledge leaked | **PASS** |
| 7 | Grounded Citations (Extended Site) | `/api/monuments/petra/knowledge` | HTTP 200, 2 verified citations, National Heritage Directorate | **PASS** |
| 8 | Grounded Timeline & 404 Guard | `/api/monuments/petra/timeline` vs fake | 2 timeline events returned, fake ID returns clean HTTP 404 | **PASS** |
| 9 | API Security Headers | Live HTTP response | Strict transport security, nosniff, CORS enforced | **PASS** |
| 10 | Phase 14 Explainability Payload | Live verification response | `engine_attribution = Tier-1 CLIP ViT-B/32 + FAISS Index`, candidates returned | **PASS** |

---

## 7. Incidents & Recovery Actions

1. **Subshell Curl Hang**:
   - *Issue*: Background health probe hung on Windows PowerShell `curl` without an explicit socket timeout.
   - *Recovery*: Task was cancelled cleanly with zero side-effects. Future probes executed via python `urllib.request` / `requests` with explicit 10s timeouts.
2. **Vercel Project Isolation**:
   - *Issue*: Project `frontend` failed on GitHub check due to root directory inference attempting to build Python.
   - *Resolution*: Release targeted project `heritage-monuments` (`prj_iMCKffts1tkod84uNZRNthLtjB5E`) scoped to `frontend/`, achieving clean, instantaneous production deployment.

---

## 8. Rollback Baseline Retention

The rollback target remains securely documented and accessible:
- **Baseline Git Commit**: `6aa1ef0389eb781048a30932c3d78ce3f256ab60` (Phase 13.4)
- **Railway Recovery**: Rollback can be executed immediately via Railway deployment history to the container associated with `6aa1ef0`.
- **Vercel Recovery**: Deployment `heritage-monuments-7xy3ys622-humaidmalik63-png.vercel.app` remains intact and promotable with a single click.

---

## 9. Final Release Status

### **PHASE 14 PRODUCTION RELEASE: COMPLETE & FULLY OPERATIONAL**

- **GitHub Repository**: Updated at commit `d305deb7821bde5e054d56a5656b53e590e7d9fe`.
- **Railway Backend**: Healthy, serving 100-site catalogue with calibrated uncertainty rejection.
- **Vercel Frontend**: Operational on canonical domain `https://heritage-monuments.vercel.app`.
- **Zero Regressions**: 10/10 pre-deployment suites and 10/10 production smoke tests passed with 100% compliance.
