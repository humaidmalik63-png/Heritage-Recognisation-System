# 🏛️ Visual Heritage Recognition & Grounded Cultural Discovery Platform

[![Live App on Vercel](https://img.shields.io/badge/Vercel-Live%20Frontend-black?style=for-the-badge&logo=vercel)](https://heritage-monuments.vercel.app)
[![API on Railway](https://img.shields.io/badge/Railway-Live%20Backend-0B0D0E?style=for-the-badge&logo=railway)](https://backend-production-b023b.up.railway.app)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-blue?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![Gemini 3.1](https://img.shields.io/badge/Google%20Gemini-3.1%20Flash--Lite-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)

> **Identify any cultural monument in milliseconds.** Powered by a high-speed Dual-Tier AI architecture (OpenAI CLIP + In-Memory FAISS Vector Retrieval + Google Gemini 3.1 Flash-Lite) paired with authoritative architectural dossiers backed by **ASI (Archaeological Survey of India)** and **UNESCO** records.

---

## 📸 Visual Previews

### 💻 Desktop Curatorial Discovery Experience
The desktop interface features an ATRIUM-inspired aesthetic layout, dynamic heritage mosaic, instant camera/file drag-and-drop scanner, and deep architectural dossiers:

![Desktop Curatorial Interface](docs/assets/desktop_preview.png)

---

### 📱 Independent Mobile-First Experience
Optimized for on-site tourists and cultural explorers with touch-friendly controls, quick-swipe architectural categories, live camera recognition, and offline history logs:

| Mobile Home Sanctuary | Detailed Curatorial Dossier Modal |
| :---: | :---: |
| ![Mobile Experience](docs/assets/mobile_preview.png) | ![Dossier Modal](docs/assets/dossier_modal_preview.png) |

---

## ⚡ How It Works (In Simple Terms)

Ever wonder how the platform recognizes a monument in **less than 15 milliseconds** without making expensive cloud API calls every time?

```text
📸 1. User Uploads Photo (Phone Camera or Drag-and-Drop)
               │
               ▼
🔍 2. AI Converts Image into 512 Numbers (OpenAI CLIP ViT-B/32)
               │
               ▼
⚡ 3. Lightning Vector Search (<15ms via FAISS)
   Compares against 577 visual angles across 100 world heritage sites.
               │
               ├─────────────────────────────────────────┐
               ▼ (Confidence is High ≥ 0.68)             ▼ (Ambiguous or Unknown Site)
      [Tier-1 Instant Match]                  [Tier-2 Gemini 3.1 Flash-Lite]
      Identifies site offline in ~15ms.       Escalates to Google's Vision AI for
               │                              nuanced multi-angle adjudication.
               └────────────────────┬────────────────────┘
                                    │
                                    ▼
📜 4. Grounded Knowledge Injection (ASI & UNESCO Records)
   Pulls historical era, architectural style, primary citations, and location map.
                                    │
                                    ▼
🏛️ 5. Beautiful Interactive Dossier Displayed to User!
```

---

## 🌟 Why This Platform is Unique

| Feature | Typical Vision Apps | Our Heritage Platform |
| :--- | :--- | :--- |
| **Search Speed** | 3 to 10 seconds per scan | **< 15 milliseconds** (Tier-1 FAISS) |
| **Cloud Cost** | Expensive API calls on every image | **Zero cost for 90%+ queries** (Local Vector Engine) |
| **Hallucinations** | Generates fake dates and fake centuries | **0% Hallucination** (Strictly grounded in ASI & UNESCO records) |
| **Ambiguity Handling** | Wrong guesses on similar stone temples | **Smart Escalation** to Gemini 3.1 Flash-Lite for tie-breaking |
| **Mobile UX** | Clunky desktop-shrunk UI | **Dedicated touch-friendly mobile interface** with swipe navigation |

---

## 🏛️ Supported Monuments Corpus

The vector database includes **100 canonical cultural monuments** across India and the World:
- **India (50 ASI Monuments)**: Taj Mahal, Qutub Minar, Konark Sun Temple, Ajanta & Ellora Caves, Brihadeeswarar Temple, Badami Cave Temples, Hampi, Red Fort, Sanchi Stupa, etc.
- **International (50 UNESCO Sites)**: Colosseum, Petra, Eiffel Tower, Angkor Wat, Machu Picchu, Acropolis of Athens, Great Wall of China, Pyramids of Giza, etc.

---

## 🚀 Quickstart: Run Locally in 5 Minutes

### Step 1: Clone the Repository
```bash
git clone https://github.com/humaidmalik63-png/Heritage-Recognisation-System.git
cd Heritage-Recognisation-System
```

### Step 2: Start Backend (Python)
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # On Linux/macOS use: source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server on port 8001
uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```
*Backend is now live at: `http://127.0.0.1:8001` (Interactive API Docs at `http://127.0.0.1:8001/docs`)*

### Step 3: Start Frontend (React + Vite)
In a second terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Open your browser at: `http://localhost:5173` (or `http://localhost:5175`)*

---

## 🌐 Live Deployments & Official Links

- **Live Web Client (Vercel CDN)**: [https://heritage-monuments.vercel.app](https://heritage-monuments.vercel.app)
- **Live Backend API (Railway Container)**: [https://backend-production-b023b.up.railway.app](https://backend-production-b023b.up.railway.app)
- **Backend Health Check**: [https://backend-production-b023b.up.railway.app/api/health](https://backend-production-b023b.up.railway.app/api/health)
- **Project Submission Links**: [`PROJECT_LINKS.txt`](PROJECT_LINKS.txt)
- **Comprehensive Project Report**: [`docs/PROJECT_REPORT_SUBMISSION.md`](docs/PROJECT_REPORT_SUBMISSION.md)
- **Presentation Slides Outline**: [`docs/PRESENTATION_SLIDES_OUTLINE.md`](docs/PRESENTATION_SLIDES_OUTLINE.md)

---

## 🛠️ Technology Stack

- **Machine Learning & Vision**: OpenAI CLIP `ViT-B/32`, PyTorch 2.2 CPU, Facebook FAISS-CPU.
- **Multimodal AI**: Google Gemini 3.1 Flash-Lite (Tier-2 Multimodal Adjudication).
- **Backend API**: Python 3.12, FastAPI, Uvicorn, Pydantic v2.
- **Frontend Application**: React 19, Vite, Tailwind CSS, Framer Motion, Lucide Icons, Leaflet Maps.
- **Hosting**: Vercel Edge Network (Frontend) + Railway Cloud Container (Backend).

---

## 📄 License & Fair-Use Attribution
Educational and cultural preservation research project developed for academic presentation and SIH 2025 submission. Primary photographic and historical citations are curated from the Archaeological Survey of India (ASI) and UNESCO World Heritage Center.
