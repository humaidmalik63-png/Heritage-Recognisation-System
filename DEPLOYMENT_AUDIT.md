# Complete Repository & Deployment Audit
**Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025 - SIH25052)**
*Date: November 8, 2026 | Auditor: Senior DevOps & AI Infrastructure Specialist*

---

## 1. Executive Summary

This audit performs an end-to-end architectural, dependency, and infrastructure review of the Heritage Recognition FastAPI platform prior to production deployment.

### System Specifications
* **Runtime**: Python `3.12.10` (64-bit)
* **Application Framework**: FastAPI `0.162.0` on Uvicorn `0.54.0`
* **Deep Learning Runtime**: PyTorch `2.15.0` (CPU Inference Engine)
* **Vision-Language Foundation**: OpenAI CLIP `ViT-B/32` via Hugging Face Transformers `5.22.1`
* **Vector Index**: FAISS `1.15.1` (Flat Inner Product index with 577 unit-normalized 512-D vectors)
* **Classical Geometric Engine**: OpenCV `5.0.0.93` (SIFT, ORB, RANSAC homography estimation)
* **Tier-2 Grounded Multimodal VLM**: Google Gemini 3.1 Flash-Lite via `google-genai 2.34.0`
* **Primary Entry Point**: `backend/main.py:app`

---

## 2. Dependency Audit & Discrepancies

### Missing Dependencies Identified
* **`opencv-python-headless`**:
  * *Finding*: `backend/local_feature_engine.py` and `backend/shadow_engine.py` import `cv2`. Root `requirements.txt` included OpenCV, but `backend/requirements.txt` lacked it. If a container or deployment environment only installed `backend/requirements.txt`, application startup would crash with `ModuleNotFoundError: No module named 'cv2'`.
  * *Remediation*: Synchronized `backend/requirements.txt` and root `requirements.txt` with `opencv-python-headless>=4.8.0`.

* **`psutil`**:
  * *Finding*: Necessary for real-time memory monitoring, container health checks, and OOM watchdog integration.
  * *Remediation*: Added to production requirements.

### Exact Production Dependency Manifest (`requirements.txt`)
```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
python-multipart>=0.0.9
pillow>=10.0.0
exifread>=3.0.0
torch>=2.2.0
transformers>=4.40.0
faiss-cpu>=1.8.0
google-genai>=0.1.0
pydantic>=2.6.0
duckduckgo-search>=5.0.0
requests>=2.31.0
python-dotenv>=1.0.0
opencv-python-headless>=4.8.0
psutil>=5.9.0
```

---

## 3. Storage & Asset Manifest Audit

### Required Core Startup Files (Under 2.5 MB Total)
These files are strictly required at container startup and must be bundled directly inside the production deployment image:

| File Path | Size | Purpose | Startup Criticality |
| :--- | :--- | :--- | :--- |
| `backend/monument_index.faiss` | 1,181,741 B (1.13 MB) | 577 FAISS vectors for 100 heritage sites | **P0 (Hard Failure if missing)** |
| `backend/monument_labels.json` | 240,765 B (235 KB) | Label mapping connecting FAISS IDs to sites | **P0 (Hard Failure if missing)** |
| `backend/monuments_metadata.json` | 116,250 B (113 KB) | Canonical architectural facts, eras, citations | **P0 (Hard Failure if missing)** |
| `backend/datasets/heritage_catalogue_100.json` | 117,866 B (115 KB) | 100-site authoritative register (50 IN + 50 INT) | **P0 (Hard Failure if missing)** |
| `backend/calibration_config.json` | 2,132 B (2.1 KB) | Temperature scaling & margin thresholds | **P0 (Hard Failure if missing)** |
| `backend/knowledge_sources.json` | 87,836 B (86 KB) | ASI & UNESCO primary source citations | **P0 (Hard Failure if missing)** |
| `backend/exceptions_log.json` | 147,610 B (144 KB) | Curator exception records & audit history | **P1 (Auto-created if missing)** |

### Optional Image Asset Directories (~973 MB)
* `backend/dataset/`: 788 image files (289.33 MB)
* `backend/datasets/`: 1,283 files (683.71 MB)
* *Audit Insight*:
  The core visual recognition pipeline uses the **pre-compiled FAISS vector index (`monument_index.faiss`)** and embedded CLIP embeddings. It does NOT read raw dataset images from disk during standard `/api/verify-monument` inference!
  The only component that attempts to read raw reference images from disk is `local_feature_engine.py` line 544 for classical SIFT keypoint homography when verifying local crops. `local_feature_engine.py` already includes an explicit safety check:
  ```python
  if ref_path.exists():
      ref_gray = cv2.imread(str(ref_path), cv2.IMREAD_GRAYSCALE)
  ```
  If reference images are omitted, it smoothly falls back to 512-D local region embedding cosine similarity without crashing.

---

## 4. Path Resolution & Cross-Platform Compatibility Audit

* **Windows vs. Linux Separators**:
  * *Audit Result*: All critical paths in `backend/main.py`, `backend/gemini_service.py`, `backend/catalogue_service.py`, and `backend/local_feature_engine.py` use `pathlib.Path` with `BASE_DIR = Path(__file__).resolve().parent`.
  * *Verification*: Paths resolve identically on Windows (`\` notation) and Linux/Docker (`/` notation).
* **Relative Imports vs. Top-Level Imports**:
  * In `backend/main.py`: `sys.path.insert(0, str(BASE_DIR))` guarantees that sibling modules (`calibration`, `uncertainty`, `gemini_service`, `catalogue_service`) are importable whether invoked as `uvicorn backend.main:app` from the project root or `python main.py` from within `backend/`.

---

## 5. Security & Administrative Audit

* **CORS Wildcard Configuration**:
  * Currently configured as `allow_origins=["*"]` with `allow_credentials=True`. This must be updated to support an environment-variable allowlist (`CORS_ORIGINS`) to prevent unauthorized cross-origin credential leaks in production.
* **Curator Endpoint Authentication**:
  * `POST /api/exceptions/{exception_id}/resolve` allows modifying curator logs without an authentication token.
  * *Remediation*: Implement header-based API key authentication (`X-Curator-Key`) with configurable `CURATOR_API_KEY`.
* **Request Body Size Limits**:
  * The file upload handler in `verify_monument` must enforce an explicit payload size cap (15 MB) to prevent denial-of-service memory exhaustion.

---

## 6. Deployment Readiness Scorecard

| Category | Status | Notes |
| :--- | :---: | :--- |
| **Code Modularity** | ✅ PASS | Decoupled engines (Calibration, Uncertainty, Catalogue, VLM) |
| **Configuration Management** | ✅ PASS | Centralized `.env` support with fallback defaults |
| **Model Caching** | ✅ PASS | Singleton in-memory loading via `initialize_backend_resources()` |
| **Path Robustness** | ✅ PASS | `pathlib.Path` utilized consistently |
| **Error Isolation** | ✅ PASS | Gemini failures fall back to deterministic offline state |
| **Memory Headroom** | ⚠️ REQUIRES >1GB | Peak inference requires ~900 MB RAM; 512 MB free tiers will OOM |
| **Administrative Security** | ⚠️ REQUIRES AUTH | Curator resolution route must be protected |

