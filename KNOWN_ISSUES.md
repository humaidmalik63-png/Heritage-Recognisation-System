# Known Issues and Technical Tracking

**Project**: Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Last Updated**: 2026-11-08  

---

## 1. Resolved Issues

* **[RESOLVED] False-Positive "Mughal Heritage Museum" -> Forbidden City**:
  * *Root Cause*: Missing `"museum"` in `GENERIC_WORDS` allowed single-token subset matching against `"Palace Museum"` (Forbidden City alternate name).
  * *Resolution*: Added `"museum"`, `"heritage"`, `"gallery"`, etc. to `GENERIC_WORDS`, required `len(v_proper) >= 2` for subset matching, and added a visual corroboration threshold (`>= 0.55`) in `main.py`.
* **[RESOLVED] NameError in Exception Logging**:
  * *Root Cause*: `process_verification_pipeline` referenced `file.filename` instead of `filename`.
  * *Resolution*: Updated to `filename or "uploaded_specimen.jpg"`.
* **[RESOLVED] Missing Root Endpoint 404**:
  * *Root Cause*: Accessing `/` returned standard FastAPI `404 Not Found`.
  * *Resolution*: Added `@app.get("/")` returning platform status and links to `/docs` and `/api/health`.

---

## 2. Active Technical Considerations (Local Mode)

* **Large JavaScript Bundle Chunk Warning**:
  * *Observation*: `dist/assets/index-CYSUwa5e.js` is 735 kB after minification (exceeds default 500 kB chunk threshold).
  * *Impact*: None on local execution. For future optimization, Leaflet and Framer Motion can be dynamically imported using `manualChunks` in `vite.config.js`.
* **Unauthenticated HF Hub Warning during Local Boot**:
  * *Observation*: Log outputs `Warning: You are sending unauthenticated requests to the HF Hub` when loading `openai/clip-vit-base-patch32`.
  * *Impact*: Benign notice. Model weights are cached locally and boot cleanly without requiring an API token.
* **Curator API Authentication**:
  * *Current State*: In local development (`backend/.env`), `CURATOR_API_KEY` is not set, allowing local testing without authorization headers. In production, setting `CURATOR_API_KEY` will strictly require the `X-Curator-Key` header.

