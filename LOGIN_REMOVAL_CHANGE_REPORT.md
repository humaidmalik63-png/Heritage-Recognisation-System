# LOGIN REMOVAL — CHANGE REPORT

**Date:** 13 November 2026
**Scope:** Frontend-only removal of the login page and all login UI.
**Base version:** 9 November project rollback (`58ff6b1 feat(phase-10.3): separate mobile-first cultural discovery frontend with breakpoint routing`)
**Branch:** `freebuff/fbb1b30e2babac6ee9890dd4` (no commit, no push, no merge, no deployment)

---

## 1. Pre-change inspection

| Item | Finding |
|---|---|
| Git status before edit | Clean working tree |
| Login page component | `frontend/src/pages/Login.jsx` |
| Registration page component | `frontend/src/pages/Signup.jsx` (linked from Login) |
| Login redirect wrapper | `frontend/src/components/ProtectedRoute.jsx` |
| Homepage | `frontend/src/pages/Dashboard.jsx`, routed at `/` |
| Routing | `frontend/src/App.jsx` (`BrowserRouter`, routes `/`, `/history`, `/login`, `/signup`, `*` → `/`) |
| Auth state | `frontend/src/context/AuthContext.jsx` — localStorage-only (`heritage_current_user`, `heritage_history_<email>`). No network/auth headers; `frontend/src/api.js` contains no login, token or `Authorization` code. |
| Frontend navigation driven by auth state | `ProtectedRoute` (redirect to `/login`), `Header` desktop Sign In / avatar + Sign Out, `Header` mobile accordion Sign In / Sign Out |
| Backend auth dependencies | None in the frontend. The login screen was a purely client-side gate. |

**Root cause of the login screen appearing:** `ProtectedRoute` redirected to `/login` whenever `user` was `null`. `AuthContext` auto-provisions a demo curator session on mount, so a fresh visitor normally bypassed the screen — but any visitor whose `heritage_current_user` was cleared (e.g. after pressing *Sign Out*, or a clean profile in some flows) was pushed to `/login`.

---

## 2. Files modified

| File | Change type |
|---|---|
| `frontend/src/App.jsx` | Modified |
| `frontend/src/components/Header.jsx` | Modified |
| `frontend/verify_hook_stability.cjs` | Modified (test list only) |
| `frontend/src/components/ProtectedRoute.jsx` | Deleted |
| `frontend/src/pages/Login.jsx` | Deleted |
| `frontend/src/pages/Signup.jsx` | Deleted |

**Diff volume:** 6 files changed, 31 insertions(+), 588 deletions(-).

No other file in the repository was touched. `git status --porcelain | grep -v '^ M frontend/'` returns no changes outside `frontend/`.

---

## 3. Exact changes made

### 3.1 `frontend/src/App.jsx`

1. Removed imports of `ProtectedRoute`, `Login` and `Signup`.
2. Removed the `isAuthPage` route-detection variable.
3. Removed the `/login` and `/signup` routes. The existing catch-all `<Route path="*" element={<Navigate to="/" replace />} />` is retained, so stale `/login` and `/signup` URLs now resolve to the homepage instead of a login form.
4. Unwrapped the homepage route so `Dashboard` renders directly:
   `element={<ProtectedRoute><Dashboard …/></ProtectedRoute>}` → `element={<Dashboard …/>}`.
5. Unwrapped the `/history` route the same way: `element={<History />}`.
6. Removed the `!isAuthPage` condition from the `Header`, `HeritageFooter` and `MobileBottomNav` render guards, so they now always render (previously hidden only on the two auth pages).
7. Simplified the `<main>` class expression to the two remaining branches (`/` vs. inner page).
8. Mobile branch condition changed from `if (isMobile && !isAuthPage)` to `if (isMobile)`; the returned JSX now uses a fragment (`<>…</>`) in place of the old `ProtectedRoute` wrapper.
9. Routing architecture, provider composition and all other layout/state logic left intact. `App.jsx` was edited in place — not rewritten or re-architected.

### 3.2 `frontend/src/components/Header.jsx`

1. Removed the conditional *User Session Profile* block: the curator avatar plus the "Sign Out of Session" button, and the fallback `<Link to="/login">Sign In</Link>`.
2. Removed the mobile-accordion `Sign Out ({user.name})` button and the fallback `Sign In` link.
3. Dropped the now-unused `LogOut` icon import and removed `user`/`logout` from the `useAuth()` destructure — `history` is still consumed for the `Log` counter, so the Archival Log navigation entry is unchanged.

### 3.3 Deleted files

- `frontend/src/pages/Login.jsx` — Curator Sign In page (sign-in form, one-click demo login, link to Signup).
- `frontend/src/pages/Signup.jsx` — Create Curator Access page (registration form, link to Login).
- `frontend/src/components/ProtectedRoute.jsx` — the auth redirect wrapper that produced `<Navigate to="/login" />`.

### 3.4 `frontend/verify_hook_stability.cjs`

Removed the `'ProtectedRoute.jsx'` entry from the component list the existing hook-order regression test audits, because the component no longer exists. No test logic, threshold or assertion was changed or weakened.

### 3.5 Deliberately **not** changed

- `frontend/src/context/AuthContext.jsx` — left byte-identical. Its `user` state is consumed by unrelated functionality (`addScanToHistory`, `clearHistory`, the History page and the mobile curator badge). Removing it would have broken recognition-history logging. The automatic demo-session bootstrap keeps `user` populated so history recording continues to work with no login step.
- `frontend/src/pages/Dashboard.jsx`, `History.jsx`, all other components, all mobile components, `api.js`, `main.jsx`, `index.html`, `vite.config.js`, `vercel.json`, `.env.*`, `package.json`, `package-lock.json`, CSS/tailwind config — untouched.
- The mobile curator initial badge in `MobileHeader.jsx` is a display ornament, not a login control, and was left as-is.

---

## 4. Protected-area confirmation

| Protected area | Status |
|---|---|
| `backend/` (entire directory) | **UNTOUCHED** — no file added, modified or deleted. Verified via `git status`. |
| FastAPI routes / endpoints | **UNTOUCHED** |
| Authentication middleware / backend authorization | **UNTOUCHED** — no backend auth mechanism was removed or bypassed. |
| Gemini integration, `gemini_service.py`, Gemini API configuration | **UNTOUCHED** — no Gemini file or config was read-modified; `.env.example` and `.env.*` unchanged. |
| CLIP model implementation | **UNTOUCHED** |
| FAISS index / vector database | **UNTOUCHED** |
| Catalogue data / metadata | **UNTOUCHED** |
| Knowledge engine, uncertainty engine, gatekeeper | **UNTOUCHED** |
| Image processing / recognition / adjudication pipeline | **UNTOUCHED** |
| Environment variables | **UNTOUCHED** |
| Dependencies / `requirements.txt` / `package.json` / `package-lock.json` | **UNTOUCHED** — `npm ci` was used to restore existing locked versions only; no upgrade. |
| Railway / Vercel configuration | **UNTOUCHED** |
| Database | **UNTOUCHED** — no schema or data change. |

Because the login gate was purely client-side, removing it does not bypass or weaken any backend security requirement. Where a backend operation requires authentication, that requirement remains exactly as before.

---

## 5. Build and test results

All commands run in `frontend/` on Node v26.13.0 / npm 11.20.0.

| Check | Command | Result |
|---|---|---|
| Dependency restore | `npm ci` | **PASS** (exit 0, lockfile respected) |
| Production build | `npm run build` | **PASS** (exit 0) — Vite 6.4.5, 2100 modules transformed, built in 6.74s. `dist/index.html` 1.39 kB, `dist/assets/index-*.css` 75.44 kB, `dist/assets/index-*.js` 831.30 kB. Pre-existing chunk-size advisory only (warning, not an error). |
| Hook-order / render-stability regression | `node verify_hook_stability.cjs` | **PASS** (exit 0) — 0 hook violations, 0 scenario failures, 24 PASS lines, all 14 scenarios. |
| Residual login references in `src/` | `grep -rn` for `/login`, `/signup`, `ProtectedRoute`, `Sign In`, `Sign Out`, `LogOut`, `pages/Login`, `pages/Signup` | **0 matches** |

### 5.1 Live browser verification (desktop, 1440×900)

Dev server bound to `0.0.0.0:3000`, loaded through the preview hostname.

| Validation | Result |
|---|---|
| Homepage opens without login | **PASS** — `/` renders the full application, no auth step |
| Login page visible | **PASS (absent)** — no "Curator Sign In", "Create Curator Access", "One-Click Curator Demo Login", "Sign In" or "Sign Out" text anywhere in the rendered DOM |
| Login buttons / navigation options | **PASS (absent)** — rendered anchors are `/`, `/history`, `#recognition`, `#discover`, `#archive`, `#how-it-works`, `#about` only. No `/login` or `/signup` link exists. |
| Header intact | **PASS** — desktop nav (Discover / Archive / Recognition / How It Works / About) and the "Recognise a Monument" button render |
| Direct `/login` URL | **PASS** — resolves to pathname `/`, renders the homepage, no login form (catch-all redirect) |
| Direct `/signup` URL | **PASS** — same SPA fallback, HTTP 200 |
| Refresh | **PASS** — reload keeps `/` and re-renders the application |
| Browser back/forward | **PASS (by construction)** — client-side routing via `BrowserRouter` and the `*` catch-all are unchanged; no hard redirect remains |
| New frontend console errors | **PASS** — no React/JS runtime errors. The only console entries are `ERR_CONNECTION_REFUSED` for `http://127.0.0.1:8001/api/health`, `/api/monuments`, `/api/exceptions`, caused solely by the local FastAPI backend not running in this environment (expected, pre-existing, and already handled by the `try/catch` + `console.warn` branches in `App.jsx`). |
| Monument images / details | **PASS (assets)** — all 18 local `/assets/heritage/*.jpg` images return HTTP 200 and render in the hero and discovery sections. Full dossier details require the backend. |

### 5.2 Backend verification (follow-up run — live FastAPI + CLIP + FAISS)

The real backend was started locally (`uvicorn backend.main:app` on port 8001, CPU, torch 2.15.0+cpu / transformers 5.23.0 / faiss-cpu) with the project's own artefacts. Startup log:

```
Loaded Phase 8.6 Heritage Catalogue: 100 sites (50 Indian + 50 International).
Loaded FAISS index with 577 vectors, 577 labels, and 100 monument metadata records.
Loaded 577 reference views into Local Feature Engine cache.
Running Tier-2 in pure offline fallback mode.      <- no GEMINI_API_KEY present
Engine startup complete. Service ready.
```

`GET /api/health` → `{"status":"healthy","faiss_vectors_loaded":577,"clip_device":"cpu","gemini_tier2_configured":false,"monuments_count":100,"catalogue_100_count":100,"knowledge_records_count":10,"exceptions_count":0,"calibration_status":"EXPERIMENTAL_CALIBRATED"}`

| Validation | Result | Evidence |
|---|---|---|
| Catalogue loads | **PASS** | `GET /api/monuments` → `total: 100`, `catalogue_size: 100`, keys `taj_mahal, qutub_minar, charminar, hawa_mahal, konark_sun_temple, …` |
| In-catalogue recognition (Taj Mahal) | **PASS** | `POST /api/verify-monument` → `VERIFIED_MATCH`, `Taj Mahal`, `ASI-ARCH-TAJ-01`, confidence `99.8`, top-1 cosine `0.9997`, tier `TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX`, 239 ms |
| In-catalogue recognition (Ajanta Caves) | **PASS** | `VERIFIED_MATCH`, `Ajanta Caves`, `0.9999`, 145 ms |
| Out-of-catalogue specimen (Eiffel Tower) | **PASS (routed correctly)** | `UNCERTAIN_MATCH` — top-3 `louvre_pyramid 0.8142 / arc_de_triomphe 0.7981 / leaning_tower_of_pisa 0.7646`, gatekeeper `0.6334`, `human_review_flagged: true`, exception `EXC-18CCE311` created, local features `TRIGGERED_AMBIGUOUS_SPECIMEN` |
| Uncertainty classification | **PASS** | Non-monument (`mathematics_paper.jpg`) → `NON_MONUMENT_REJECTED`, gatekeeper `0.4096`, no exception |
| Curatorial review | **PASS** | Flagged exception persisted to the review log and returned by `GET /api/exceptions` |
| Gemini offline fallback | **PASS** | `gemini_service.is_available() == False`; `adjudicate_monument()` returns `is_offline_fallback=True` with curatorial caveat |
| Gemini Tier-2 adjudication branch | **PASS (stubbed transport, no network)** | With a stubbed client returning a valid adjudication JSON, `proposed_identity='Eiffel Tower'`, `qualitative_confidence=HIGH`, membership lookup `OUT_OF_CATALOG`, and main.py policy **B2** evaluates `True` → final `UNKNOWN_HERITAGE_SPECIMEN`, `out_of_catalog_identified=True` |
| Tier-2 activation gate for the real Eiffel scan | **PASS (conditions met)** | `decision=UNCERTAIN_MATCH` ✓ and `arch_prob=0.6334 >= 0.40` ✓, so `should_adjudicate` is `True` as soon as `gemini_service.is_available()` is `True` |
| Frontend renders live catalogue | **PASS** | Homepage (no login) opened through the preview against the live backend; the Catalogue drawer rendered **Louvre Pyramid**, **Hagia Sophia** and **Arc de Triomphe** — names that exist only in the `/api/monuments` payload, not in any hardcoded component |

### 5.3 Known limitations of this verification run

- **No `GEMINI_API_KEY` is configured in this environment**, so no live Gemini API call was made. The pipeline was proved to reach the Tier-2 stage, satisfy its activation gate, and handle both the offline-fallback and adjudicated-response paths. The real network call to `gemini-3.1-flash-lite` requires the key to be set as a project secret and is reported as **not tested**.
- The **cloud browser cannot reach the VM's loopback** (`127.0.0.1:8001` → `ERR_CONNECTION_REFUSED`), and the preview edge proxy does not complete browser `multipart/form-data` POSTs (GETs succeed). Therefore the **upload button could not be driven through the browser UI**. The identical multipart POST the frontend sends (`POST /api/verify-monument` with a `file` field) was verified directly against the live backend and through a local same-origin bridge (178 ms, `VERIFIED_MATCH` / `Taj Mahal` / `99.8`).
- Test artefacts created at runtime (`backend/exceptions_log.json`, Gemini telemetry counters) were removed/reverted; `git diff --quiet -- backend/` confirms `backend/` is **identical to HEAD**.
- No shortcuts, stubs, or fakes exist in the application code. The only stubbed element was the throwaway verification script in `/tmp`, never in the repository.

---

## 6. Remaining login-related references

| Location | What remains | Assessment |
|---|---|---|
| `frontend/src/context/AuthContext.jsx` | `login`, `signup`, `logout` functions and the `heritage_users` / `heritage_current_user` localStorage keys still exist. Nothing in the UI calls `login`, `signup` or `logout` any more. | **Intentional and necessary.** `user` and `history` from this context power recognition-history logging (`addScanToHistory`), history clearing, the History page and the mobile curator badge. Deleting the context would have broken unrelated functionality. The session helpers are inert dead code with no UI entry point. |
| `frontend/src/mobile/MobileHeader.jsx` | Curator initial badge (`title={user?.name}`) in the mobile header. | Not a login control or link — a decorative identity badge. Left unchanged to avoid an unrelated visual change. |
| `frontend/src/pages/History.jsx` | Text: "verified by officer {user?.name} ({user?.badgeNumber})". | Descriptive copy, not a login prompt. Left unchanged. |
| Repository Markdown documentation (`backend/*.md`, `PHASE_*.md`, `README.md`, `run_all.bat` demo credentials note) | Historical reports describing the former login/signup portals and demo credentials. | Historical records only; no runtime effect. Not modified, per the no-unrelated-change rule. |

No user-facing login page, login button, login link, login route or login redirect remains in the application.

---

## 7. Change control compliance

- No backend modifications — **confirmed**.
- No database modifications — **confirmed**.
- No catalogue modifications — **confirmed**.
- No Gemini modifications — **confirmed**.
- No unrelated UI redesign — **confirmed** (only the login controls and auth-page scaffolding were removed).
- No dependency upgrades — **confirmed** (`npm ci` restored locked versions).
- No Git commit — **confirmed** (changes left staged in the working tree only).
- No Git push — **confirmed**.
- No merge into main — **confirmed**.
- No Railway deployment — **confirmed**.
- No Vercel deployment — **confirmed**.

**Stopping here for local validation review and your approval.**
