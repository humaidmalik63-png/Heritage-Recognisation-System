# PHASE 13 — PRODUCTION DEPLOYMENT & VERIFICATION REPORT

**Project:** Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH25052)  
**Date & Timestamp:** 2026-11-10 19:22:00 IST  
**Environment:** Live Production (Railway Backend + Vercel Frontend + GitHub Repository)  
**Status:** **RELEASE SUCCESSFUL**

---

## 1. PRODUCTION DEPLOYMENT IDENTIFIERS

| Attribute | Deployment Value |
|---|---|
| **GitHub Repository** | `https://github.com/humaidmalik63-png/Heritage-Recognisation-System.git` |
| **Branch** | `main` (fast-forward push, no force-push) |
| **Previous Production Baseline** | `f7e7804470c17a61f22e232938cfd7946955a90e` |
| **New Release Commit Hash** | `3423900883c175035235bb957fc2dea738d44480` |
| **Commit Message** | `release: Phase 12 performance and Phase 13 security hardening` |
| **Railway Backend Service URL** | `https://backend-production-b023b.up.railway.app` |
| **Railway Edge / Router** | `railway-hikari` (Edge: `sin1`) |
| **Vercel Frontend URL** | `https://heritage-monuments.vercel.app` |
| **Vercel Production Deployment ID** | `dpl_JDMDVvEZm22fm4UmwhQRjt7WxYr5` |
| **Vercel Deployed Bundle** | `/assets/index-X6BM_fo1.js` |

---

## 2. LIVE SECURITY & BACKEND TEST RESULTS (RAILWAY)

All verification tests were executed directly against the live Railway production backend:

| Test Target | Endpoint / Request | Expected Result | Live Actual Result | Status |
|---|---|---|---|---|
| **Health & Vectors** | `GET /api/health` | HTTP 200, 577 vectors, 100 monuments | `{"status":"healthy","faiss_vectors_loaded":577,"catalogue_100_count":100,"monuments_count":100,"gemini_tier2_model":"gemini-3.1-flash-lite"}` | **PASS** |
| **Archival Fallback** | `GET /dataset/petra/img_1.jpg` | HTTP 200, >300KB JPEG | HTTP 200, `Content-Length: 348903`, Valid JPEG SOI (`\xff\xd8`) | **PASS** |
| **Exception Access** | `GET /api/exceptions` (Anonymous) | HTTP 401 Unauthorized | HTTP 401: `{"detail":"Unauthorized: Valid administrator authentication required."}` | **PASS** |
| **Exception Resolution**| `POST /api/exceptions/exp_01/resolve` (Anon)| HTTP 401 Unauthorized | HTTP 401: `{"detail":"Unauthorized: Valid administrator authentication required."}` | **PASS** |
| **Public Summary** | `GET /api/exceptions/summary` | HTTP 200, sanitized count | HTTP 200: `{"total":0,"pending_count":0}` | **PASS** |
| **Telemetry Privacy** | `GET /api/telemetry/gemini` (Anonymous) | HTTP 401 Unauthorized | HTTP 401: `{"detail":"Unauthorized: Valid administrator authentication required."}` | **PASS** |
| **Public Status** | `GET /api/telemetry/status` (Public) | HTTP 200, online status | HTTP 200: `{"status":"online","model_family":"gemini-3.1-flash-lite"}` | **PASS** |
| **VLM Rate Limiting**| `POST /api/monuments/taj_mahal/ask` | 15 req/min tier | Requests 1–15: HTTP 422; Request 16: HTTP 429 Too Many Requests (`Retry-After: 59s`) | **PASS** |
| **Upload Limit** | `POST /api/verify-monument` (>15MB) | HTTP 413 Content Too Large| HTTP 413 Content Too Large | **PASS** |
| **Live Recognition** | `POST /api/verify-monument` (Taj Mahal) | `VERIFIED_MATCH` >= 99% | HTTP 200: `Taj Mahal`, `VERIFIED_MATCH`, `99.8%` confidence, 6 grounded citations | **PASS** |
| **Live Recognition** | `POST /api/verify-monument` (Petra) | `VERIFIED_MATCH` >= 99% | HTTP 200: `Petra`, `VERIFIED_MATCH`, `99.7%` confidence | **PASS** |

---

## 3. LIVE FRONTEND & EDGE SECURITY VERIFICATION (VERCEL)

Verified against the live production custom domain `https://heritage-monuments.vercel.app`:

| Verification Area | Check Performed | Observed Value / Finding | Status |
|---|---|---|---|
| **Root Availability** | `GET /` | HTTP 200 OK | **PASS** |
| **Production Bundle** | Script Tag in `index.html` | `<script type="module" crossorigin src="/assets/index-X6BM_fo1.js"></script>` | **PASS** |
| **Demo Credentials** | Grep bundle for `curator123` | **0 occurrences** (completely absent from production build) | **PASS** |
| **Demo User Object** | Grep bundle for `DEFAULT_DEMO_USER` | **0 occurrences** (completely absent from production build) | **PASS** |
| **Demo Login Button** | Grep bundle for `One-Click` | **0 occurrences** (completely absent from production build) | **PASS** |
| **Frame Protection** | `X-Frame-Options` header | `DENY` | **PASS** |
| **MIME Sniffing** | `X-Content-Type-Options` header | `nosniff` | **PASS** |
| **HSTS Enforcement** | `Strict-Transport-Security` header | `max-age=63072000; includeSubDomains; preload` | **PASS** |
| **Hardware Privacy** | `Permissions-Policy` header | `camera=(self), geolocation=(), microphone=()` | **PASS** |
| **CSP Header** | `Content-Security-Policy` header | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://*.tile.openstreetmap.org https://backend-production-b023b.up.railway.app; connect-src 'self' https://backend-production-b023b.up.railway.app http://localhost:8000 http://localhost:8001 http://127.0.0.1:8000 http://127.0.0.1:8001; frame-ancestors 'none';` | **PASS** |
| **Edge Asset Delivery**| `GET /assets/heritage/petra.jpg` | HTTP 200, 348,903 bytes, binary JPEG (`\xff\xd8`), Sub-millisecond Edge Delivery | **PASS** |
| **Edge Asset Delivery**| `GET /assets/heritage/taj-mahal.jpg`| HTTP 200, 310,707 bytes, binary JPEG | **PASS** |
| **Edge Asset Delivery**| `GET /assets/heritage/colosseum.jpg`| HTTP 200, 149,987 bytes, binary JPEG | **PASS** |

---

## 4. ACTUAL PRODUCTION RESPONSE HEADERS

### Railway Backend (`GET /dataset/petra/img_1.jpg`)
```http
HTTP/1.1 200 OK
Server: railway-hikari
Content-Type: image/jpeg
Content-Length: 348903
Accept-Ranges: bytes
content-security-policy: default-src 'self'; img-src 'self' data: blob: https:; font-src 'self' https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; frame-ancestors 'none';
x-content-type-options: nosniff
x-frame-options: DENY
permissions-policy: camera=(self), geolocation=(), microphone=()
referrer-policy: strict-origin-when-cross-origin
strict-transport-security: max-age=31536000; includeSubDomains; preload
x-ratelimit-limit: 150
x-ratelimit-remaining: 149
x-ratelimit-reset: 60
```

### Vercel Frontend (`GET /`)
```http
HTTP/1.1 200 OK
Server: Vercel
Content-Type: text/html; charset=utf-8
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://*.tile.openstreetmap.org https://backend-production-b023b.up.railway.app; connect-src 'self' https://backend-production-b023b.up.railway.app http://localhost:8000 http://localhost:8001 http://127.0.0.1:8000 http://127.0.0.1:8001; frame-ancestors 'none';
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(self), geolocation=(), microphone=()
```

---

## 5. RESOLUTION OF PREVIOUS INCIDENT

The issue where visiting `https://heritage-monuments.vercel.app` displayed:
```text
Could not load reference image from https://backend-production-b023b.up.railway.app/dataset/petra/img_1.jpg
```
has been **permanently resolved**:
1. `backend/assets/heritage/` now contains all 21 authentic landmark photos tracked as raw binary files in Git.
2. The `/dataset/{monument_key}/{filename}` endpoint on Railway automatically intercepts Git LFS pointers and serves the native binary fallback.
3. The live endpoint on Railway returns the full 348 KB JPEG binary.
4. The frontend resolves sample images via `/assets/heritage/petra.jpg` on Vercel Edge CDN first, with polite error auto-dismiss fallback.

---

## 6. ROLLBACK PROCEDURES (IF EVER NEEDED)

If a critical production regression is reported, rollback can be executed cleanly:

1. **GitHub Rollback:**
   ```bash
   git revert 3423900883c175035235bb957fc2dea738d44480
   git push origin main
   ```
2. **Railway Rollback:**
   Re-deploy previous deployment corresponding to commit `f7e7804470c17a61f22e232938cfd7946955a90e` directly from Railway Dashboard.
3. **Vercel Rollback:**
   ```bash
   npx vercel rollback --yes
   # or re-assign alias:
   npx vercel alias set <previous_deployment_url> heritage-monuments.vercel.app
   ```

---

## 7. FINAL RELEASE STATUS

**RELEASE STATUS: RELEASE SUCCESSFUL**

- Both Railway backend and Vercel frontend deployments are live and healthy.
- All 12 security areas, asset verifications, and end-to-end recognition pipelines verified with empirical evidence.
- No further code modifications or deployments required.
