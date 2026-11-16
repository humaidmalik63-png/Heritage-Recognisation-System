# FIXES APPLIED — November 2026 fix pass

This copy of the Heritage Monument Recognition project was produced by cloning
the public GitHub repo (read-only), removing its `.git` directory so no push is
possible, and applying the security fixes (Prompts A/B/C) and recognition
fixes (Prompts 1–4) from the November 2026 inspection reports. **Nothing was
pushed to GitHub.** The live deploy is untouched; deploy this copy when ready.

Read the **"NOT done / NOT verified"** section before deploying — in
particular, **the FAISS index was NOT rebuilt** in this pass.

## 1. What changed, per file

### Security — Prompt A: demo login removed

| File | Change |
|---|---|
| `frontend/src/context/AuthContext.jsx` | **Rewritten.** No identity, no sign-in/sign-up, no hardcoded demo curator account, no plaintext passwords in localStorage, no seeded fake scans. Keeps only the device-local scan history under a single key (`heritage_scan_history`). On first load it migrates real scans out of the old per-user keys, drops the two seeded demo entries, and deletes all legacy keys (`heritage_users`, `heritage_current_user`, `heritage_history_*`). `AuthProvider`/`useAuth` export names and the `history`/`addScanToHistory`/`clearHistory` API are unchanged, so existing components keep working; `user` is always `null`. |
| `frontend/src/mobile/MobileApp.jsx` | "CURATORIAL CREDENTIALS / Authenticated User" block replaced with honest local-session text. |
| `frontend/src/mobile/MobileHeader.jsx` | Removed the curator avatar/initial badge; neutral "H" local-session badge. |
| `frontend/src/pages/History.jsx` | Removed "verified by officer {name}" wording; "ENCRYPTED LOCAL" corrected to "LOCAL BROWSER STORAGE" (localStorage is not encrypted). |
| `README.md`, `backend/FINAL_PROJECT_COMPLETION_REPORT.md`, `backend/PHASE_8_5G_FRONTEND_WHITE_SCREEN_FIX.md` | Doc references to the demo account corrected/scrubbed (the demo email address no longer appears anywhere in the project). |

Verified: `grep` for the demo password value, the demo email address, the demo
persona name, and `heritage_users`/`heritage_current_user` (except the new
cleanup code) returns zero matches in source; a production build was run and
its bundle also contains none of them.

### Security — Prompt B: backend auth, rate limits, docs gating

`backend/main.py`:

- **Admin auth (fail-closed).** New `require_admin` dependency: accepts
  `Authorization: Bearer <token>` or the legacy `X-Curator-Key` header,
  constant-time comparison (`hmac.compare_digest`), 401 with
  `WWW-Authenticate: Bearer` when the token is missing/wrong **or when no
  token is configured at all**. Token source: `ADMIN_TOKEN` env var
  (preferred) or legacy `CURATOR_API_KEY`; no default value exists.
  Applied to `GET /api/exceptions`, `POST /api/exceptions/{id}/resolve`
  (the old inline check was fail-OPEN when no key was configured — that
  hole is closed), and `GET /api/telemetry/gemini`.
- **Rate limiting** (in-memory, per client IP, sliding window, 429 with
  `Retry-After`; first `X-Forwarded-For` hop is used when present):
  `POST /api/verify-monument` 30/min, `POST /api/monuments/{id}/ask`
  20/min, `POST /explain-architecture` 20/min,
  `POST /api/recognition/local-features` 30/min.
- **Docs gating.** When `ENV=production` (or `ENVIRONMENT=production`),
  `/docs`, `/redoc`, and `/openapi.json` are disabled. The root `/`
  endpoint only advertises `/docs` outside production.
- **Security headers middleware** on every response:
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: strict-origin-when-cross-origin`,
  `Permissions-Policy: camera=(), microphone=(), geolocation=()`, and a
  restrictive CSP (`default-src 'self'; frame-ancestors 'none';
  base-uri 'self'`) except on the docs pages, which need their own assets.
- **15 MB upload limit enforced server-side** with HTTP 413 + a clear
  message on `POST /api/verify-monument` (already present, now via the
  shared `MAX_UPLOAD_BYTES` constant), `POST /explain-architecture`, and
  `POST /api/recognition/local-features` (new).

`frontend/src/api.js`: admin token store held **in module memory only**
(`setAdminToken`/`clearAdminToken`/`hasAdminToken`) — never written to
localStorage/sessionStorage/cookies, cleared on page reload. Sent as
`Authorization: Bearer` on the three admin endpoints; 401s surface as
errors with `.status === 401`.

`frontend/src/components/ExceptionsDrawer.jsx`: unlock UI — when the backend
returns 401, the drawer shows an admin-token prompt (password field, clear
explanation that the token is memory-only) plus a Lock button to forget the
token. A rejected token is dropped, never retried.

### Security — Prompt C: headers + text + upload limit

- `vercel.json` (root) and `frontend/vercel.json`: added a `headers` array
  for all routes — CSP, `X-Frame-Options: DENY`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy:
  strict-origin-when-cross-origin`, `Permissions-Policy: camera=(self),
  microphone=(), geolocation=()`. The CSP was built from the app's actual
  external usage: Google Fonts, OpenStreetMap tiles, the Railway backend
  origin + localhost dev backends, `blob:` object-URL previews, `data:`
  favicon, same-origin media. See the files for the exact policy.
- "VGG16 • FAISS" and the "VERAFIED MATCHES" typo: **already absent** in
  this snapshot (the hero already says "OpenAI CLIP ViT-B/32 (512-D)" and
  "577 FAISS Anchors") — no change needed.
- Stale "pending photographic field survey" disclaimer: removed from the
  metadata-only footnote in `MonographResult.jsx` and from the backend
  metadata-only response message in `main.py` (the message now reports the
  live loaded vector count). The footnote now states plainly that the
  match was NOT verified against the vector index.
- Client-side 15 MB checks added in `frontend/src/components/UploadSection.jsx`
  and `frontend/src/mobile/MobileRecognition.jsx` (consistent alert text
  with the backend 413), matching the existing "UP TO 15MB" labels.

### Recognition — Prompt 1: verdict logic

`backend/catalogue_service.py`:

- **Group-alias map** (`GROUP_ALIAS_MAP`, matched before exact-name
  lookup, after normalisation that strips parentheticals and is
  case/punctuation-insensitive): Vamana / Kandariya Mahadeva / Lakshmana /
  Chitragupta / Vishwanath temples (with and without "Khajuraho") →
  `khajuraho_temples`; "Lal Qila" → `red_fort`; "Masjid-i Jahan-Numa" /
  "Jama Masjid Delhi" → `jama_masjid`. "Red Fort (Lal Qila)" already
  resolved via paren-stripping and still does.
- **Deliberate non-mapping:** "Virupaksha Temple" is NOT aliased to
  `hampi_stone_chariot` — it is a different temple in the Hampi complex,
  and aliasing it would invent a grouping the metadata does not support.
  The Hampi override case is handled by the abstention rule instead (below).
- `get_faiss_recognition_ready_keys()` now respects
  `recognition_readiness`: only `RECOGNITION_READY` entries count (all 100
  existing entries are unaffected; the new Jama Masjid entry is excluded
  until the index is rebuilt — see §4).

`backend/gemini_service.py`:

- `adjudicate_monument(image, tier1_candidates=None)`: when the Tier-1
  top-3 are supplied, the prompt gains CANDIDATE-CHOICE RULES — name a
  listed candidate verbatim, do not substitute a nearby/subsidiary
  structure's name, name a different monument only if it is clearly a
  different structure, abstain (null identity) if unsure. The existing
  429 retry/backoff (1s/2s/4s, quota fail-fast) was already present and
  left untouched.
- Key resolution: `GEMINI_API_KEY`, with `GOOGLE_API_KEY` as fallback
  (new — the code previously read only `GEMINI_API_KEY`; the fallback is
  additive and changes nothing when `GEMINI_API_KEY` is set). Added an
  `initialize(api_key=None)` method so the client can be (re)configured
  without ever logging the key. A stale "10-monument catalogue" field
  description was corrected.

`backend/uncertainty.py`:

- `GPSEvidence` records which monument the EXIF coordinates were compared
  against (`compared_against_monument_key/name`).
- New `reevaluate_gps_for_monument(exif_gps, monument_key, metadata)`:
  re-runs the GPS check against any monument (used for the FINAL
  attribution). Returns a no-conflict record when there is no GPS data, no
  monument, or no recorded coordinates — it never invents a conflict.
- No threshold or decision-rule changes.

`backend/main.py` (§5 verdict logic):

- Tier-1 top-3 are now passed into Tier-2 adjudication.
- **Abstention post-process:** if Tier 2 proposes an identity that is not
  in the top-3 and not alias-resolvable, while Tier 1 is strong
  (`best_score` ≥ the configured confidence threshold, 0.75), the Tier-1
  decision is retained and the result is marked
  `post_processed_abstention`. This is the Hampi fix: Tier 2's
  "Virupaksha Temple, Hampi" (out-of-catalogue) no longer overrides a
  correct Tier-1 Hampi top-1. Genuine out-of-catalogue photos are
  unaffected when Tier 1 is weak. Trade-off (documented honestly): when
  Tier 1 is strong but wrong, the Tier-2 naming is lost — the guardrail
  "never guess confidently wrong" favours keeping Tier 1 here.
- **B0 decisive-agreement branch (new):** when the similarity margin is ≥
  the configured 0.08 threshold, Tier 2 confirms the same monument as the
  Tier-1 top-1 with HIGH/MEDIUM confidence and real evidence, the entry
  is recognition-ready, and there is no GPS conflict, the verdict is
  VERIFIED_MATCH. **No "geological-architectural ambiguity" / rock flag
  exists anywhere in this code snapshot** (verified by search) — the live
  REVIEW_REQUIREDs on decisive matches (Machu Picchu, Statue of Liberty,
  Sydney Opera House) must have come from other rules or from deployed
  code that differs from this snapshot. B0 is the guard that decisive
  agreement verifies normally; see the live-test checklist in §5.
- **B3 no-visual-support branch changed:** Tier 2 names a catalogue
  monument with confidence but no Tier-1 candidate supports it — verdict
  is now **UNCERTAIN_MATCH** attributed to the Tier-2 monument (flag
  `tier2_attributed_uncertain`), with the catalogue status left
  recognition-ready. Previously this overwrote the status to
  OUT_OF_CATALOG and returned UNKNOWN — the verdict-logic bug (Red Fort
  photo 1, Ajanta fresco, Khajuraho photo 2). Judgment call: UNCERTAIN,
  not VERIFIED, because the anti-hallucination gate (no visual support)
  must stay; the prompts-file checklist accepts "VERIFIED or UNCERTAIN,
  NOT out-of-catalog".
- **GPS recompute (§5B):** after adjudication, if the final attributed
  monument differs from the Tier-1 top-1, GPS evidence is re-evaluated
  against the FINAL monument; reason codes and telemetry are updated, and
  a VERIFIED verdict is downgraded to REVIEW_REQUIRED only if GPS
  conflicts with the FINAL monument. A Red Fort photo with Delhi GPS is
  no longer marked GPS_CONFLICT for being far from Fatehpur Sikri.
- Thresholds were **not** changed. Note the discrepancy found during
  inspection: the prompts file says the similarity threshold is 0.72, but
  the live `backend/calibration_config.json` sets `confidence_threshold`
  0.75 with `uncertainty_margin_threshold` 0.08. Both configured values
  were left exactly as they are; the verdict code reads them from config.

### Recognition — Prompt 2: index gaps (photos + wiring, NO rebuild)

- 14 new anchor photos added (see `backend/SOURCES.md` for URL, author,
  and licence per photo — all freely licensed Wikimedia Commons
  photographs, verified as real photos by file inspection and visual
  check on 15 Nov 2026):
  - Elephanta Caves ×3 (Cave 2 exterior, Cave 3 entrance, Cave 1 panel)
  - Khajuraho Temples ×3 (temple shikhara, Vishwanath Temple, Chitragupta Temple)
  - Red Fort ×4 (Lahori Gate passage, Lahori Gate at night, gate close-up, Diwan-i-Khas)
  - Agra Fort ×4 (Amar Singh Gate tilework, Jahangir Mahal front, eastern flank ramparts, Diwan-i-Khas)
- Each photo exists in BOTH `backend/datasets/reference_gallery_100/<id>/`
  (the live index source, continuing the existing `ref_04.jpg` numbering)
  and `backend/dataset/<id>/` (the `index_builder.py` source and
  `/dataset` preview mount). One near-duplicate Jahangir Mahal frontal
  was downloaded, inspected, and deliberately NOT included.
- `backend/datasets/reference_gallery_100/` now contains the REAL photos
  (477 files, fetched from Git LFS into this copy) instead of LFS pointer
  text files, so the rebuild command in §4 works without `git lfs pull`.
  The `backend/dataset/` copies of the other monuments are still LFS
  pointers in this copy — use the gallery_100 rebuild path, not
  `index_builder.py` (see §4).
- Build-script hardening in `backend/index_builder.py` and
  `backend/rebuild_faiss_v2.py`: files that fail a JPEG/PNG/WebP
  magic-byte check (e.g. LFS pointers) are skipped with an explicit
  warning and counted; the scripts refuse to write an empty index; the
  summary reports skipped monuments/files; the "Added 4 image vectors"
  log line now reports the actual count. `rebuild_faiss_v2.py` accepts a
  `HERITAGE_GALLERY_DIR` env override (default unchanged) and labels
  `file_path` entries with the actual gallery directory name, so the
  gallery_100 rebuild labels paths correctly.
- The `reference_gallery_v2/` directory and `reference_gallery_manifest.json`
  (a 10-monument historical artifact) were deliberately NOT edited.

### Recognition — Prompt 3: labels

- Backend (`main.py` CASE D): the `"Potential {best_name} (Audit Required)"`
  headline pattern is removed. Unindexed specimens now return
  `monument_name = "Unknown heritage specimen — needs curator review"`.
- Desktop (`frontend/src/components/MonographResult.jsx`, VIEW 2 only):
  metadata-only headline is now "Proposed catalogued match: {name}";
  out-of-catalog headline is "Proposed identity (unverified): {name}";
  unindexed headline is the exact "Unknown heritage specimen — needs
  curator review". VIEW 1 (uncertain), VIEW 3 (review), and VIEW 5
  (verified) behaviour is unchanged, including the `verification_status`
  default the History modal relies on.
- Mobile (`frontend/src/mobile/MobileResults.jsx`): headlines are now
  status-driven — verified shows the name; uncertain shows "Possible
  match (uncertain)" with the name as a subline; metadata-only /
  out-of-catalog use the same qualified wording as desktop; review and
  plain-unknown show the unknown-specimen headline, with the Tier-1
  closest match shown only as a small "hint only" line on review;
  non-monument shows "Not a heritage monument". `rejection_message` is
  now displayed for non-verified results. Style/era/monograph/
  coordinates/citations are shown only for verified, uncertain, or
  metadata-only results (plus Tier-2 evidence text for out-of-catalog);
  the misleading "85.0%" default confidence is replaced with "—" when the
  backend sends no score, and the `verified_match` key fallback no longer
  appears on unverified results.

### Recognition — Prompt 4: Jama Masjid

- Added `jama_masjid` to `backend/monuments_metadata.json` and
  `backend/datasets/heritage_catalogue_100.json` (101 entries each; the
  only change to those files is the addition — verified by diff).
  Every field comes from the expansion pack's verbatim entry: name
  "Jama Masjid", alternate "Masjid-i Jahan-Numa", Delhi/Delhi/India,
  the verbatim description, "Mughal Empire (17th century)", the verbatim
  preservation status, category "mosque", `recognition_readiness:
  "METADATA_ONLY"`. Two honest mappings, documented here:
  `architectural_style: "Mughal Architecture"` is derived from the
  pack's "Mughal Empire (17th century)" + Shah Jahan description, and
  `coordinates: null` because no verified coordinates exist in any
  source (all GPS/catalogue/map code paths are null-safe for this —
  verified by test). `sources: []` and `grounded_citations: {}` are
  empty rather than invented.
- The 3 verified photos (2012 front exterior, 2016 exterior, 2022 night
  view) are in both photo directories as `ref_01..03.jpg` (see
  `backend/SOURCES.md`).
- Alias map entries (above) resolve "Masjid-i Jahan-Numa" and
  "Jama Masjid Delhi" to `jama_masjid`.
- `generate_heritage_catalogue_100.py` was NOT edited: it asserts
  coordinates + sources and generates the 100-site file; Jama Masjid is
  the 101st post-generation entry. Do not re-run the generator over the
  edited catalogue file or the entry will be lost. There is no
  knowledge-engine record for Jama Masjid (that would require inventing
  content); the knowledge/timeline/sources endpoints will 404 for it
  until one is written from real sources.
- Behaviour change to expect: until the rebuild + readiness flip (§4),
  Jama Masjid photos produce a metadata-only proposal, NOT an
  out-of-catalog verdict and NOT a verification. The old Prompt-2
  regression expectation ("Jama still correctly out-of-catalog") is
  superseded by this state.

### Config templates

- `.env.example` (root) and `backend/.env.example` rewritten: empty
  `GEMINI_API_KEY=`, empty `ADMIN_TOKEN=` with generation instructions
  (no value), `ENV=` placeholder, `GEMINI_MODEL=gemini-3.1-flash-lite`,
  `CORS_ORIGINS` guidance (localhost + the live Vercel origin),
  `PORT=8001` for local dev (the Dockerfile uses 8000 for containers;
  Railway injects its own `PORT`). `.gitignore` already covered `.env`
  and was left as-is. No real `.env` file is shipped.

## 2. How to run it

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env          # then fill in GEMINI_API_KEY + ADMIN_TOKEN
uvicorn main:app --host 0.0.0.0 --port 8001
```

First run downloads the CLIP model (`openai/clip-vit-base-patch32`,
~350 MB) — allow time and disk space. Health check:
`GET http://localhost:8001/api/health` (reports the loaded vector count).

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (expects backend on :8001)
npm run build      # production build; Vercel uses the root vercel.json
```

Production frontend env (`frontend/.env.production`) already points at the
Railway backend. For local dev, `frontend/.env.development` points at
`127.0.0.1:8001`.

### Adding the Gemini key + admin token

1. Get a key at https://aistudio.google.com/app/apikey and set
   `GEMINI_API_KEY=<key>` in `backend/.env` (or the Railway dashboard
   variables). `GOOGLE_API_KEY` is accepted as a fallback. Never put the
   key in frontend code or commit it.
2. Generate an admin token and set `ADMIN_TOKEN=<token>` in the same
   place:
   `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
3. Set `ENV=production` on the deployed backend so `/docs` is disabled.
4. To use the Exceptions drawer: open it, enter the admin token when
   prompted. It lives in page memory only — reload or Lock to forget it.
   Without `ADMIN_TOKEN` configured, the admin endpoints reject everyone.

## 3. NOT done / NOT verified — read before deploying

- **The FAISS index was NOT rebuilt.** The shipped
  `backend/monument_index.faiss` / `backend/monument_labels.json` are the
  previous 577-vector index (477 photos + 100 centroids). The 17 new
  photos and the Jama Masjid entry have NO effect on recognition until
  the rebuild in §4 runs. No vector count is claimed beyond the 577 that
  shipped in the repo.
- **No live-site verification.** Nothing in this pass was tested against
  the deployed site or a deployed backend. The verdict/fuzzy/GPS logic
  was unit-tested with synthetic inputs (see §6); the frontend production
  build was verified; the full recognition checklists in §5 must still be
  run with real photos after deploy.
- **Backend was not run end-to-end** in this environment (no torch/CLIP
  model here). `python -m py_compile` passes on all backend files, and
  the importable modules were exercised, but `uvicorn` startup and the
  `/api/verify-monument` pipeline were not executed. Run the backend
  locally once before deploying.
- **Rate limits are per-process, in-memory.** They reset on restart and
  do not coordinate across multiple backend instances. Fine for a single
  Railway instance; use a shared store (e.g. Redis) if the backend ever
  scales horizontally.
- **CSP is untested in a browser.** The policy was built from a static
  audit of external hosts (Google Fonts, OSM tiles, Railway/localhost
  backends). After deploying, open the browser console and confirm no
  CSP violations block fonts, tiles, images, or API calls.
- **Hardcoded "577" display strings** (`HeritageHero.jsx`,
  `HeritageFooter.jsx`, `HowItWorks.jsx`, `MobileApp.jsx`,
  `MobileDiscover.jsx`) are still correct for the shipped 577-vector
  index. After the rebuild, update them to the new count (expected 595 —
  see §4). The header pills already read the live count from `/api/health`.
- **Exception ledger untouched.** The 51 pending exceptions (including
  test entries) were not resolved, edited, or deleted.
- **No knowledge-engine record for Jama Masjid** (see §1, Prompt 4).

## 4. Rebuilding the FAISS index (required for Prompts 2 + 4 to take effect)

Prerequisites: backend venv with `requirements.txt` installed (torch,
transformers, faiss-cpu, pillow), ~350 MB for the CLIP model download,
and the real photos in `backend/datasets/reference_gallery_100/` (already
in this copy — no `git lfs pull` needed for this path).

```bash
cd backend
# Back up the current index first (it is overwritten):
cp monument_index.faiss monument_index.faiss.bak
cp monument_labels.json monument_labels.json.bak
HERITAGE_GALLERY_DIR=datasets/reference_gallery_100 python rebuild_faiss_v2.py
```

This overwrites the ACTIVE index (`backend/monument_index.faiss` +
`backend/monument_labels.json`, which `main.py` loads) and writes
versioned copies under `backend/datasets/`. **Expected result: 595
vectors** (494 photos + 101 centroids) — 477 + 17 new photos, 100 + 1
Jama Masjid centroid. If the script reports skipped pointer files or a
different count, stop and investigate before deploying; do not ship a
partial index. Then:

1. Flip Jama Masjid to recognition-ready: in BOTH
   `backend/monuments_metadata.json` and
   `backend/datasets/heritage_catalogue_100.json`, change Jama Masjid's
   `"recognition_readiness": "METADATA_ONLY"` to `"RECOGNITION_READY"`.
2. Restart the backend and confirm `/api/health` reports the new count.
3. Update the hardcoded "577" display strings (see §3).
4. Run the Prompt-2 and Prompt-4 checklists in §5.

Do NOT use `backend/index_builder.py` for the live index: it reads
`backend/dataset/`, where most photos are still Git LFS pointers in this
copy, and would build a partial index (it now warns loudly about this).
If you ever need that path, run `git lfs pull` in a full clone first.

## 5. Live test checklists (run after deploy, with real photos)

From the November 2026 prompts files, reproduced verbatim in intent.
Do NOT resolve real exception-ledger cases just to test.

### Prompt 1 — verdict logic (no rebuild needed)

1. Red Fort photo 1 → Red Fort VERIFIED or UNCERTAIN, NOT out-of-catalog.
2. Ajanta fresco close-up → Ajanta, NOT out-of-catalog.
3. Machu Picchu, Statue of Liberty, Sydney Opera House, Leaning Tower of
   Pisa → VERIFIED_MATCH.
4. Hampi Stone Chariot → Hampi, NOT Virupaksha/out-of-catalog.
5. Taj Mahal photo still VERIFIED_MATCH Tier 1.
6. Blank image still "insufficient evidence".
7. A Georgian church photo still UNKNOWN, never a catalogue verify.

### Prompt 2 — index gaps (after the §4 rebuild)

1. Elephanta ×3 → Elephanta Caves verified, NEVER Ajanta.
2. Khajuraho ×3 → Khajuraho verified.
3. Red Fort ×2 → verified.
4. Agra Fort → Agra Fort verified.
5. Regression: Ajanta ×3 still Ajanta; Taj Mahal still Tier 1
   VERIFIED_MATCH. (The original "Jama still out-of-catalog" regression
   is superseded — see §1, Prompt 4.)

### Prompt 3 — labels

1. Casbah of Algiers photo → no "Victoria Memorial" headline.
2. Georgian church photo → no "Qutub Minar" headline.
3. Caucasus fortress photo → no "Mesa Verde" headline.
4. Verified matches (Taj Mahal) display exactly as before.
   Check BOTH desktop and mobile results screens.

### Prompt 4 — Jama Masjid (after the §4 rebuild + readiness flip)

1. Jama Masjid ×3 (incl. night view) → VERIFIED_MATCH Jama Masjid.
2. Regression: Taj Mahal still Tier 1, Red Fort still correct.

### Security smoke tests

1. `POST /api/exceptions/{id}/resolve` with no token → 401, ledger unchanged.
2. `GET /api/exceptions` and `GET /api/telemetry/gemini` with no token → 401;
   with the admin token → 200. Wrong token → 401.
3. With `ENV=production`: `/docs` and `/openapi.json` → 404.
4. Upload a >15 MB image → 413 with a clear message (backend); the
   upload UI also refuses it before sending.
5. Response headers on the frontend include CSP / X-Frame-Options /
   X-Content-Type-Options; backend responses include the security headers.
6. Rapid-fire >30 verify requests in a minute from one IP → 429s with
   `Retry-After` (do not hammer the live backend to test this — test
   locally).

## 6. Verification performed in this pass (15 Nov 2026)

- `python -m py_compile` on every backend `.py` file: all pass (one
  pre-existing `SyntaxWarning` in the untouched
  `audit_calibration_analysis.py`).
- 42 standalone unit/structural tests against the real
  `catalogue_service` and `uncertainty` modules with synthetic inputs
  (no CLIP/FAISS/Gemini): **42 passed, 0 failed** — covering all group
  aliases, qualified names ("Red Fort (Lal Qila)"), case-insensitivity,
  the Virupaksha non-mapping, out-of-catalogue safety, the 100-key
  FAISS-ready set with Jama excluded, GPS re-evaluation against the
  final monument (Red Fort vs Fatehpur Sikri contrast, Taj boost, no-GPS
  and null-coords safety), and structural checks on the `main.py` /
  `gemini_service.py` changes (B0/B3/abstention branches, admin + rate
  limit + docs gating + headers + 413s, candidate-choice prompt, key
  fallback, empty token defaults).
- Frontend: `npm ci` + `npm run build` (Vite 6.4.5, 2100 modules)
  succeeds; the built bundle contains no demo credentials, no demo
  persona, and no legacy auth keys (the only `heritage_users` reference
  is the new cleanup code). `node_modules` and `dist/` were removed
  afterwards; the ZIP ships source only.
- Secret sweep: no `.env` files, no `.git`, no Google/GitHub key
  patterns, no private keys, no password assignments anywhere in the
  copy. `.env.example` files contain empty placeholders only.
- All 17 new photos verified as real JPEG photographs (magic bytes,
  dimensions, visual inspection) with author + licence recorded in
  `backend/SOURCES.md`. All 477 gallery_100 photos + 18 frontend
  heritage images verified as real images (not LFS pointers).
- JSON validity: both metadata files load as 101 entries; diffs confirm
  the Jama Masjid addition is the only change. Both `vercel.json` files
  are valid JSON with the headers array present.

## 7. Judgments & trade-offs (for the record)

- B3 → UNCERTAIN (not VERIFIED): keeps the anti-hallucination gate while
  fixing the verdict bug. See §1.
- Abstention gate at the configured 0.75 threshold: Tier-2 namings are
  dropped only when Tier 1 is strong. If a future test shows Tier 2
  correctly overriding a strong-but-wrong Tier 1, revisit this gate.
- No rock flag was found in this snapshot, so B0 guards decisive
  agreement directly. If the live deploy's flag lives in code outside
  this repo snapshot, the flag itself still needs the margin < 0.08
  restriction from the prompts file.
- The 0.75 (config) vs 0.72 (prompts file) similarity-threshold
  discrepancy was reported, not "fixed" — changing a calibration value
  without evidence would violate the guardrail.
- Frontend admin token in memory only: less convenient than a saved
  login, but a persisted token in browser storage would recreate the
  exact vulnerability Prompt A removed.
- The 17 photos are 1920px-wide Commons derivatives (one 1600px
  original), not full-resolution originals — the pipeline downscales to
  768px and CLIP resizes to 224px, so full originals add nothing but size.

## Patch — 16 Nov 2026 (screenshot issues: corrupt-image banner, wrong rejection view, silent Tier 2)

Diagnosed from three localhost screenshots (museum photo + White House photo):

1. **"Invalid or corrupted image: cannot identify image file <_io.BytesIO object at 0x...>"** — the backend put Pillow's raw exception (with a memory address) into the API error, and the frontend showed it verbatim. The upload itself had failed Pillow decoding (unreadable/corrupt bytes, or a phone HEIC the Pillow build could not decode). Fixed in `backend/main.py`: the raw error is now logged server-side only; the API returns a clean message naming JPG/PNG/WebP + the 15 MB limit. The empty-file case no longer gets double-wrapped. Optional HEIF/HEIC decoding added via `pillow-heif` (guarded import; new dep in both `requirements.txt` files — run `pip install -r requirements.txt`).
2. **Stale verdict under the error banner + broken preview** — `frontend/src/pages/Dashboard.jsx` never cleared the previous result on a failed verify, so the old panel stayed visible with the new file's broken preview. Fixed: all three verify paths now clear the result on error (and the sample-canvas path now handles failures instead of hanging the loader).
3. **Museum photo shown as "SPECIMEN REJECTED // NON-HERITAGE" with an "Unknown Heritage Specimen" message** — Tier 2 (Gemini) had said "not a heritage structure", which overrode the Tier-1 UNKNOWN verdict with no confidence requirement, while the message still carried the Tier-1 UNKNOWN explanation. Fixed in `backend/main.py`: the non-monument override now requires HIGH/MEDIUM Tier-2 confidence + real evidence (mirroring branches B0–B3); a low-confidence call keeps the Tier-1 verdict. When the override does fire, the message now states the Tier-2 determination in Tier 2's own words. Note: the photographed museum is NOT in the 101-site catalogue, so UNKNOWN (not a verified match) remains the correct outcome family for it.
4. **"Gemini to answer hi nhi de ra" (White House photo)** — Tier 2 described the White House in its evidence text but returned `proposed_identity: null`, so the UI fell back to the unindexed branch with no proposed identity. Fixed in `backend/gemini_service.py`: the prompt now requires the identity field to match any site named in the evidence, and requires naming a clearly identifiable out-of-catalogue site instead of abstaining. Also fixed the prompt's catalogue count (100 → 101) and removed a dead duplicated `except` block in the parse fallback. The VIEW 2 adjudication badge in `MonographResult.jsx` no longer claims an adjudication when Tier 2 never ran (shows "TIER 1 ONLY // NO TIER-2 ADJUDICATION").
5. Stale "100 indexed" copy in the desktop + mobile recognition headers now carries no number (the live header pill already shows the real counts).

Thresholds untouched (0.75 / 0.08). FAISS index still the old 577-vector build — the §4 rebuild is a separate step and is NOT in this patch. Verified: `py_compile` on both backend files; live validation-path test (corrupt/empty/oversize) against the real `process_verification_pipeline`; `npm run build` (2100 modules). Live photo retest (White House + museum) is still the user's step.
