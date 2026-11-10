# 📚 Heritage Recognition System — Documentation & Reports Index

This directory archives historical architectural decisions, deployment reports, validation audits, benchmark evaluations, and security reviews conducted throughout the platform's lifecycle.

---

## 📑 Phase Reports & Audits

### 🔬 Phase 14 — Calibrated Uncertainty & Quality Architecture
*Comprehensive calibration, paired evaluation, and zero-hallucination uncertainty policies.*

- **[PHASE_14_PRODUCTION_DEPLOYMENT_REPORT.md](reports/PHASE_14_PRODUCTION_DEPLOYMENT_REPORT.md)**  
  Final production release gate for Phase 14 on Railway & Vercel, smoke verification, and live telemetry audit.
- **[PHASE_14_IMPLEMENTATION_REPORT.md](reports/PHASE_14_IMPLEMENTATION_REPORT.md)**  
  Implementation details of the calibrated uncertainty policy, `GATEKEEPER_AMBIGUOUS` state, and gatekeeper margin adjustments.
- **[PHASE_14_RECOGNITION_EVALUATION.md](reports/PHASE_14_RECOGNITION_EVALUATION.md)**  
  Three-way paired evaluation (136 specimens) across Cohort 1 and Holdout Split D with confidence intervals and raw metrics.

---

### 🛡️ Phase 13 — Security Hardening, Bounded Concurrency & Fallbacks
*Production stability, threadpool safety, atomic admission control, and deterministic failover.*

- **[PHASE_13_4_PRODUCTION_DEPLOYMENT_REPORT.md](reports/PHASE_13_4_PRODUCTION_DEPLOYMENT_REPORT.md)**  
  Verification and deployment audit of the Gemini Tier-2 fallback mechanism on Railway and Vercel.
- **[PHASE_13_4_GEMINI_FALLBACK_FIX_REPORT.md](reports/PHASE_13_4_GEMINI_FALLBACK_FIX_REPORT.md)**  
  Root cause analysis and implementation of the non-blocking Gemini 3.1 Flash-Lite timeout and fallback pipeline.
- **[PHASE_13_PRODUCTION_DEPLOYMENT_REPORT.md](reports/PHASE_13_PRODUCTION_DEPLOYMENT_REPORT.md)**  
  Phase 13 release audit covering rate limiting, curated exception logs, and geodetic sanity gates.
- **[PHASE_13_2_FINAL_RELEASE_GATE.md](reports/PHASE_13_2_FINAL_RELEASE_GATE.md)**  
  Release gate verification for security patches and curator authentication endpoints.

---

### 🎨 Phase 10 — UI/UX Overhaul & Mobile Adaptation
*Atrium-inspired museum aesthetic, responsive viewports, and mobile-first experience.*

- **[PHASE_10_0_ATRIUM_PIXEL_PERFECT_RECREATION_REPORT.md](reports/PHASE_10_0_ATRIUM_PIXEL_PERFECT_RECREATION_REPORT.md)**  
  Pixel-perfect implementation of the museum-grade atrium UI layout and typography.
- **[PHASE_10_1_HERITAGE_WEBSITE_TRANSFORMATION_REPORT.md](reports/PHASE_10_1_HERITAGE_WEBSITE_TRANSFORMATION_REPORT.md)**  
  Transformation of legacy interfaces into an institutional digital museum platform.
- **[PHASE_10_2_LOCAL_VALIDATION_REPORT.md](reports/PHASE_10_2_LOCAL_VALIDATION_REPORT.md)**  
  Local integration and headless browser validation for all components.
- **[PHASE_10_2_RAILWAY_DEPLOYMENT_REPORT.md](reports/PHASE_10_2_RAILWAY_DEPLOYMENT_REPORT.md)**  
  Containerization and Railway deployment audit for the modernized platform.
- **[PHASE_10_3_SEPARATE_MOBILE_FRONTEND_REPORT.md](reports/PHASE_10_3_SEPARATE_MOBILE_FRONTEND_REPORT.md)**  
  Responsive layout audit across mobile viewports (360x800, 390x844, 430x932).

---

### 🏛️ Foundational Audits & Benchmark Studies
*Core recognition benchmarks, memory profiling, and cloud architecture reviews.*

- **[RECOGNITION_ACCURACY_REPORT.md](reports/RECOGNITION_ACCURACY_REPORT.md)**  
  Initial benchmark accuracy metrics and evaluation across 100 heritage sites.
- **[SECURITY_REVIEW.md](reports/SECURITY_REVIEW.md)**  
  Threat modeling, input sanitization, and API security boundary assessment.
- **[MEMORY_OPTIMIZATION_REPORT.md](reports/MEMORY_OPTIMIZATION_REPORT.md)**  
  PyTorch CPU memory optimization, FAISS index quantization, and heap footprint profiling.
- **[HOSTING_COMPARISON.md](reports/HOSTING_COMPARISON.md)**  
  Evaluation of cloud hosting providers (Railway vs. Render vs. Fly.io) for PyTorch CPU inference.
- **[DEPLOYMENT_AUDIT.md](reports/DEPLOYMENT_AUDIT.md)**  
  Initial deployment verification and environment configuration audit.
- **[DEPLOYMENT_TEST_REPORT.md](reports/DEPLOYMENT_TEST_REPORT.md)**  
  Automated integration and end-to-end smoke test logs.
- **[FRONTEND_BACKEND_TEST_REPORT.md](reports/FRONTEND_BACKEND_TEST_REPORT.md)**  
  Contract testing between React frontend and FastAPI backend endpoints.
- **[GEMINI_INTEGRATION_REPORT.md](reports/GEMINI_INTEGRATION_REPORT.md)**  
  Initial integration testing with Google Gemini multimodal APIs.
- **[LOCAL_DEVELOPMENT_STATUS.md](reports/LOCAL_DEVELOPMENT_STATUS.md)**  
  Development environment setup, local vector index verification, and tooling status.
- **[KNOWN_ISSUES.md](reports/KNOWN_ISSUES.md)**  
  Known constraints, edge-case behaviors, and upstream dependency tracking.

---

## 🖼️ Media & Visual Assets
Visual assets used in project documentation and demonstrations are located in `docs/assets/`:
- `desktop_preview.png`: Full-resolution desktop interface showcase.
- `mobile_preview.png`: Mobile interface showcase across responsive viewports.
- `citations_preview.png`: Authoritative citation & historical monograph dossier modal.
