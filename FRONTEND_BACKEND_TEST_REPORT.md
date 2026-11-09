# Frontend and Backend Integration Test Report

**Project**: Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Frontend URL**: `http://localhost:5173` (Vite 6 + React 19)  
**Backend URL**: `http://127.0.0.1:8000` (FastAPI + Uvicorn)  
**Test Date**: 2026-11-08  

---

## 1. Environment Architecture

* **Frontend Configuration**: `frontend/.env.development` points to `VITE_API_BASE_URL=http://127.0.0.1:8000`.
* **CORS Settings**: Backend `CORSMiddleware` explicitly permits requests from `http://localhost:5173` and `http://127.0.0.1:5173`.
* **Build Verification**: `npm run build` completed cleanly (2,084 modules transformed, 0 bundle errors).

---

## 2. Comprehensive Endpoint Verification

All endpoints tested live against the running local server:

| Endpoint | Method | Purpose | Response Code | Verified Content |
| :--- | :--- | :--- | :-: | :--- |
| `/api/health` | GET | System Health Check | **200 OK** | `{"status":"healthy","faiss_vectors_loaded":577,"clip_device":"cpu",...}` |
| `/api/monuments` | GET | 100-Site Catalogue Listing | **200 OK** | 100 catalogued sites returned with complete metadata |
| `/api/monuments/{id}/knowledge`| GET | Grounded Knowledge Records | **200 OK** | Taj Mahal returned 4 verified primary citations & epigraphy |
| `/api/monuments/{id}/timeline` | GET | Historical Timeline Events | **200 OK** | Taj Mahal returned 5 chronologically ordered milestones |
| `/api/monuments/{id}/sources`  | GET | Provenance & Legal Dossier | **200 OK** | ASI, UNESCO WHC, and District Gazetteer citations |
| `/api/monuments/{id}/ask`      | POST | Grounded Cultural QA | **200 OK** | Accurately answered *"Who commissioned the Taj Mahal?"* |
| `/api/verify-monument`         | POST | Specimen Verification | **200 OK** | Multi-tier pipeline with uncertainty & calibration |
| `/api/exceptions`              | GET | Curator Exception Log | **200 OK** | Retrieved pending review items (`{"total": 81, ...}`) |
| `/api/exceptions/{id}/resolve` | POST | Curator Review Resolution | **200 OK** | Status updated to `APPROVED` with audit history |

---

## 3. UI Component Readiness

* **Image Upload & Preview**: Drag-and-drop file uploader with client-side image clamping and format validation.
* **Result Monograph**: Renders 4 distinct views based on pipeline response:
  * `VERIFIED_MATCH`: Full monograph with GPS map, historical summary, and grounded citations.
  * `UNCERTAIN_MATCH`: Side-by-side candidate comparison with cosine margins and curator review banner.
  * `UNKNOWN_HERITAGE_SPECIMEN`: Out-of-catalog alert with Gemini qualitative assessment.
  * `NON_MONUMENT_REJECTED`: Archival stamp rejection with explanation.
* **Exceptions Drawer**: Slide-out curator interface allowing resolution and note-taking on ambiguous items.
* **Responsive Layout**: Validated across mobile, tablet, and desktop breakpoints.

