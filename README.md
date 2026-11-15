# Visual Heritage Recognition & Grounded Cultural Discovery Platform

[![Live App on Vercel](https://img.shields.io/badge/Vercel-Live%20Frontend-black?logo=vercel)](https://heritage-monuments.vercel.app)
[![API on Railway](https://img.shields.io/badge/Railway-Live%20Backend-0B0D0E?logo=railway)](https://backend-production-b023b.up.railway.app)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C?logo=pytorch)](https://pytorch.org)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-blue)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/Gemini-3.1%20Flash--Lite-4285F4?logo=google)](https://deepmind.google/technologies/gemini/)

> **An enterprise-grade multimodal visual recognition and cultural education platform** that identifies global monuments from photographs in under 15ms using vector search, verifies uncertain cases with multimodal AI (Gemini 3.1 Flash-Lite), and serves authoritative, grounded architectural dossiers backed by ASI and UNESCO archives.

---

## 🏛️ System Architecture

```text
[User Photograph Upload / Camera Input]
                   │
                   ▼
       [FastAPI Verification Gateway]
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
[EXIF & Quality Check]    [OpenAI CLIP ViT-B/32]
                                  │ (512-D Dense Vector)
                                  ▼
                     [FAISS Inner-Product Index]
                     (577 Vectors / 100 Sites)
                                  │
                                  ▼
                    [Uncertainty & Gatekeeper Engine]
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
[Top Match Confidence >= 0.68]               [Ambiguous / Out-of-Catalog]
         │                                                 │
         ▼                                                 ▼
[Tier-1 Instant Match (<15ms)]             [Tier-2 Gemini 3.1 Flash-Lite]
         │                                 (Multimodal Visual Adjudication)
         └────────────────────────┬────────────────────────┘
                                  │
                                  ▼
              [Grounded Knowledge Engine (ASI & UNESCO)]
                                  │
                                  ▼
      [Interactive Curatorial Monograph & Dossier Response]
```

---

## 🌟 Key Features

1. **Dual-Tier Hybrid Recognition**:
   - **Tier-1 (Deterministic)**: Sub-15ms vector retrieval using OpenAI CLIP (`ViT-B/32`) and a pre-indexed FAISS search engine covering 100 canonical cultural monuments.
   - **Tier-2 (Multimodal AI)**: Automatic escalation to Google Gemini 3.1 Flash-Lite whenever lighting, viewpoints, or out-of-catalog structures introduce uncertainty.
2. **Grounded Cultural Knowledge**:
   - Every identified monument is linked directly to authoritative, factual historical and architectural facts with primary citations from the **Archaeological Survey of India (ASI)** and **UNESCO World Heritage Convention**.
3. **Responsive Mobile-First Interface**:
   - ATRIUM-inspired curatorial layout with touch-optimized camera scanning, swipeable archival categories, interactive maps, and persistent personal survey logging.
4. **Calibrated Uncertainty & Anti-Hallucination**:
   - Strict gatekeeper logic isolates natural rock formations, modern buildings, and unindexed structures, preventing misattribution.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── datasets/                # Authoritative 100-site catalogue & schemas
│   ├── main.py                  # FastAPI core application & endpoints
│   ├── gemini_service.py        # Gemini 3.1 Flash-Lite tier-2 integration
│   ├── uncertainty.py           # Multi-criteria confidence & gatekeeper
│   ├── calibration.py           # Confidence calibration engine
│   ├── local_feature_engine.py  # Classical SIFT / homography validation
│   ├── monument_index.faiss     # 577 pre-compiled 512-D FAISS vectors
│   ├── monument_labels.json     # Label mappings
│   ├── monuments_metadata.json  # Comprehensive architectural facts
│   └── requirements.txt         # Backend Python dependencies
├── frontend/
│   ├── src/                     # React 19 source code (Desktop & Mobile)
│   ├── public/                  # Static assets & cultural photography
│   ├── package.json             # Frontend Node.js dependencies
│   └── vite.config.js           # Vite build configuration
├── docs/
│   └── reports/                 # Complete phase audits, security & testing reports
├── PROJECT_LINKS.txt            # Live deployment & repository URLs
├── requirements.txt             # Production container dependencies
├── Dockerfile                   # Docker production container manifest
├── vercel.json                  # Vercel deployment configuration
└── README.md                    # Project documentation & execution guide
```

---

## 🚀 Quickstart & Local Installation

### Prerequisites
- **Python**: 3.11 or 3.12 (64-bit)
- **Node.js**: 18.x or 20.x
- **Google Gemini API Key** (optional for Tier-2, Tier-1 runs 100% offline)

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/humaidmalik63-png/Heritage-Recognisation-System.git
cd Heritage-Recognisation-System

# Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables (optional for Gemini)
cp backend/.env.example backend/.env
# Edit backend/.env and insert your GEMINI_API_KEY

# Run FastAPI backend server
uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```
The backend API is now live at: `http://127.0.0.1:8001` (Docs at `/docs`).

### 2. Frontend Setup
In a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```
The frontend is now running at: `http://localhost:5173` (or `5175`).

---

## 🧪 Testing & Verification

Run the comprehensive test suites:
```bash
# Test API endpoints
python -m pytest backend/test_api.py

# Test uncertainty & gatekeeper logic
python -m pytest backend/test_uncertainty.py

# Test viewport responsiveness
python test_phase_10_3_viewports.py
```

---

## 🌐 Live Production Deployments

- **Frontend Client**: [https://heritage-monuments.vercel.app](https://heritage-monuments.vercel.app)
- **Backend API**: [https://backend-production-b023b.up.railway.app](https://backend-production-b023b.up.railway.app)
- **API Health Check**: [https://backend-production-b023b.up.railway.app/api/health](https://backend-production-b023b.up.railway.app/api/health)
- **Project Links File**: [`PROJECT_LINKS.txt`](PROJECT_LINKS.txt)

---

## 📄 License & Attribution
Developed for SIH 2025 / Academic Capstone Submission. Cultural heritage data and photography referenced from the Archaeological Survey of India (ASI) and UNESCO World Heritage Center under fair-use educational guidelines.
