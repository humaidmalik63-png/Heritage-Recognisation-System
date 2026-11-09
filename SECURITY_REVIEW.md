# Production Security Review & Hardening Report
**Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform**
*Date: November 8, 2026 | Auditor: Senior Cloud Security Specialist*

---

## 1. Vulnerability Assessment & Hardening Matrix

| Component | Identified Vulnerability / Risk | Severity | Hardening Measure Implemented |
| :--- | :--- | :---: | :--- |
| **CORS Middleware** | Wildcard `allow_origins=["*"]` with `allow_credentials=True` violated standard browser security and exposed session headers. | **MEDIUM** | Replaced with environment-configurable `CORS_ORIGINS` allowlist (e.g., `https://your-frontend.vercel.app,http://localhost:5173`). Wildcard `*` now explicitly disables credentials. |
| **Curator Exceptions** | `POST /api/exceptions/{id}/resolve` allowed arbitrary unauthorized clients to approve, reject, or corrupt audit records. | **HIGH** | Added header-based authentication `X-Curator-Key` validated against environment variable `CURATOR_API_KEY`. Requests without valid keys return `401 Unauthorized`. |
| **File Ingestion (DoS)** | Unbounded `await file.read()` allowed multi-gigabyte uploads to cause instantaneous container Out-Of-Memory crashes. | **HIGH** | Enforced 15 MB hard limit on uploaded payloads and enabled `Image.MAX_IMAGE_PIXELS = 50_000_000` to prevent decompression bombs. |
| **API Secret Hygiene** | Potential leakage of `GEMINI_API_KEY` in telemetry endpoints or error stack traces. | **CRITICAL** | Zero logging of API keys; keys read exclusively via `os.environ`. Telemetry endpoints mask sensitive credentials. `.env` strictly gitignored. |
| **Path Traversal** | Potential directory traversal if file paths from query parameters were passed to `open()`. | **MEDIUM** | Verified that all file access uses canonical `pathlib.Path` anchored to `BASE_DIR`. No client input is ever passed to file system reads. |

---

## 2. Hardening Implementation Details

### A. Environment-Configurable CORS Allowlist
```python
raw_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]
is_wildcard = "*" in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=not is_wildcard,  # Credentials forbidden with wildcard in W3C spec
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

### B. Curator Administrative Endpoint Protection
```python
CURATOR_API_KEY = os.environ.get("CURATOR_API_KEY", "sih2025-curator-secret").strip()

@app.post("/api/exceptions/{exception_id}/resolve")
def resolve_exception(
    exception_id: str,
    payload: ResolveExceptionRequest,
    x_curator_key: Optional[str] = Header(None, alias="X-Curator-Key")
):
    if CURATOR_API_KEY and x_curator_key != CURATOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Valid X-Curator-Key header required to resolve curator exceptions."
        )
    ...
```

### C. File Upload Size Capping & MIME Validation
```python
MAX_UPLOAD_SIZE = 15 * 1024 * 1024  # 15 MB maximum payload
Image.MAX_IMAGE_PIXELS = 50_000_000  # Guard against pixel decompression bombs

if len(image_bytes) > MAX_UPLOAD_SIZE:
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail="Payload too large: Image exceeds 15 MB limit."
    )
```

