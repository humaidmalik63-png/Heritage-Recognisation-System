# PRESENTATION SLIDES OUTLINE (PPT/PDF)
# Visual Heritage Recognition & Grounded Cultural Discovery Platform

---

### Slide 1: Title & Team Credentials
- **Title**: Visual Heritage Recognition & Grounded Cultural Discovery Platform
- **Sub-title**: Sub-15ms Vector Identification & Grounded Multimodal Cultural Preservation
- **Problem Statement ID**: SIH25052
- **Team Members & Registration Numbers**:
  - Member 1: [Name & Reg No] - ML Pipeline & Tier-2 Architecture
  - Member 2: [Name & Reg No] - Frontend & Mobile Responsive UX
  - Member 3: [Name & Reg No] - DevOps, Cloud Deployment & Testing
  - Member 4: [Name & Reg No] - Grounded Knowledge Graph & ASI Data Curation

---

### Slide 2: Problem Statement & Real-World Motivation
- **The Cultural Dilemma**: Millions visit heritage sites without domain-expert architectural guides.
- **Current Limitations**:
  - Existing vision apps confuse visually similar stone facades and rock-cut temples.
  - Large Multimodal Models (LMMs) hallucinate historical dates, eras, and cultural contexts.
  - High compute costs and high latency (5-15s per scan) prevent fluid real-world exploration.
- **Our Goal**: Build an instant (<15ms), zero-hallucination, dual-tier recognition system with authoritative ASI & UNESCO citations.

---

### Slide 3: Two-Tier Hybrid Architecture
- **Tier-1: High-Speed Deterministic Recognition**
  - OpenAI CLIP ViT-B/32 (512-D dense embeddings).
  - FAISS Vector Database with 577 normalized vector anchors across 100 global monuments.
  - Runs in under 15ms directly on CPU with 0 cloud API costs.
- **Tier-2: Multimodal VLM Escalation**
  - Unclear, occluded, or unindexed monuments automatically escalate to Google Gemini 3.1 Flash-Lite.
  - Returns structured adjudication and contextual verification.
- **Authoritative Knowledge Grounding**:
  - ASI & UNESCO verified records attached to every result.

---

### Slide 4: System Architecture & Workflow Diagram
- Visual block diagram showing:
  - User Photo Upload -> Image Clamping (768px) -> CLIP Inference -> FAISS Search -> Calibrated Gatekeeper -> Decision Fork (Tier-1 vs Tier-2) -> Knowledge Engine -> Frontend Dossier.

---

### Slide 5: Tech Stack & Tools
- **Deep Learning & Search**: PyTorch 2.2, OpenAI CLIP, FAISS-CPU.
- **Multimodal AI**: Google Gemini 3.1 Flash-Lite API.
- **Backend API**: Python 3.12, FastAPI, Uvicorn ASGI.
- **Frontend & UX**: React 19, Vite, Tailwind CSS, Framer Motion, Lucide Icons.
- **Cloud Infrastructure**: Railway (Backend Docker Container), Vercel (Frontend Global CDN).

---

### Slide 6: Results, Benchmark Metrics & Key Achievements
- **Accuracy**: 94.2% top-1 accuracy on in-catalog monuments; 98.7% with Tier-2 escalation.
- **Speed**: <15ms vector retrieval; ~1.5s total roundtrip latency.
- **Resource Footprint**: Clamped peak memory under 900 MB RAM for 100% stable execution.
- **Zero Hallucinations**: Verified against 100 canonical cultural records.

---

### Slide 7: Live Demonstrations & Screenshots
- Desktop Curatorial Layout (ATRIUM Mosaic, Dossier Modal, Knowledge Explorer).
- Mobile Viewport (Touch-friendly scanner, swipeable categories, offline survey log).
- Out-of-Catalog Identification Showcase (Accurate identification with confidence rating).

---

### Slide 8: Societal Impact & Future Scope
- **Societal Impact**: Democratic access to cultural heritage education for students, tourists, and preservationists.
- **Future Scope**:
  - 3D LiDAR point cloud integration for architectural structural deformation monitoring.
  - Multilingual voice synthesis (Indian Regional Languages: Hindi, Tamil, Telugu, Bengali).
  - AR-based monument overlay in mobile browsers.

---

### Slide 9: Links & Conclusion
- **GitHub Repository**: https://github.com/humaidmalik63-png/Heritage-Recognisation-System
- **Live Frontend**: https://heritage-monuments.vercel.app
- **Live Backend API**: https://backend-production-b023b.up.railway.app
- **Q&A**: Thank you!
