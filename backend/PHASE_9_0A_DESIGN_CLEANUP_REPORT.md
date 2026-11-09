# PHASE 9.0A: AI DESIGN SLOP REMOVAL & CURATORIAL ARCHIVE REFINEMENT REPORT

**Project:** Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Directory:** `C:\Users\humai\Heritage PJ`  
**Date:** November 2026  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

In accordance with Phase 9.0A instructions, the entire frontend was audited and systematically refactored to eliminate generic "AI slop" design tropes (neon reticle glows, iOS-style translucent liquid-glassmorphism, artificial pulsing animations, uncurated sparkles icons, nested cards-in-cards, and repetitive tech marketing jargon). 

The platform's authentic museum identity—**THE CURATORIAL ARCHIVE**—has been elevated to institutional standards, mirroring the visual language of prestigious national conservation authorities such as the Archaeological Survey of India (ASI) and UNESCO World Heritage Centre.

---

## 2. AI Slop Audit & Elimination Inventory

| Category | Previously Observed Pattern | Curatorial Refactoring Applied |
| :--- | :--- | :--- |
| **Glow & Neons** | `.scanner-line` had `box-shadow: 0 0 14px 3px rgba(158, 59, 36, 0.65)` neon glow. | Replaced with a crisp, razor-thin 1px solid terracotta (#9E3B24) scanline with zero blur. |
| **Glassmorphism** | `.liquid-glass` used translucent white (`rgba(253, 251, 247, 0.88)`), heavy `backdrop-filter: blur(16px)`, and specular border reflections. | Replaced with authentic solid ivory `#FDFBF7` archival plates with crisp 1px hairline borders (`#E2DDD5`) and tactile, subtle elevation shadows. |
| **Spurious Motion** | Continuous `animate-ping` and `animate-pulse` on status indicators, exceptions badges, and online beacons. | Replaced with steady, authoritative status dots (solid emerald `#059669` and amber `#D97706`) and calm typography. |
| **Generic AI Icons** | `Sparkles` icon used on sample buttons, facts sections, and demo login buttons. | Replaced with scholarly symbols: `BookOpen`, `Scroll`, `Landmark`, `KeyRound`, and `Layers`. Unused `Sparkles` imports completely excised. |
| **Card Bubbly Radii** | Overly rounded cards (`rounded-2xl`, bubbly pill containers) resembling casual mobile SaaS apps. | Refactored into architectural plates with disciplined 2px to 4px radius (`rounded-sm`/`rounded`), subtle corner registration ticks, and double borders (`3px double #E2DDD5`). |
| **Jargon & Slop Copy** | "ENTRY PORTAL // SPECIMEN INGESTION", "SERIES 2026-IND-HYBRID // SIH25052", "Turnkey Evaluation Samples". | Refactored to formal curatorial language: "DIRECTORATE OF ARCHAEOLOGY & COMPUTATIONAL EPIGRAPHY", "ACCESSION INGESTION // SPECIMEN PLATE", "Curated Reference Specimens". |
| **Stamp Clutter** | Up to five competing inked stamps crammed together in result ribbons. | Consolidated into an organized, unified curatorial accession band with distinct status hierarchy. |

---

## 3. Component-by-Component Refactoring Details

### 3.1 Styling Engine (`frontend/src/index.css`)
- **Base Typography & Smoothing:** Enabled font-feature settings (`'cv02', 'cv03', 'cv04', 'cv11'`) and optimized subpixel rendering.
- **Scrollbar Craft:** Added a tailored archival scrollbar in muted parchment (`#F1ECE1`) with hairline thumb (`#C5BDB2`).
- **Surface Elevation:** Defined `.archival-plate` with solid alabaster/ivory substrate (`#FDFBF7`) and 1px hairline border (`#E2DDD5`).
- **Archival Inked Stamps:** Calibrated `.archival-stamp`, `.archival-stamp-tier2`, and `.archival-stamp-rejected` with muted, museum-grade tinted backgrounds (`#F8ECE9`, `#FBF6ED`, `#F4F4F5`) and restrained letter-spacing.
- **Scanning Line:** Cleaned `.scanner-line` down to 1px thickness with linear cubic-bezier ease, eliminating specular blur.

### 3.2 Header & Navigation (`frontend/src/components/Header.jsx`)
- Removed `liquid-glass` backdrop blur.
- Excised `animate-ping` on the engine online beacon.
- Excised `animate-pulse` on the pending exceptions count pill.
- Refined masthead copy to: *"Two-tier visual recognition engine integrating on-device neural embeddings and vector retrieval with multimodal verification for authoritative cultural discovery."*
- Balanced navigation buttons with restrained hover effects.

### 3.3 Specimen Ingestion Plate (`frontend/src/components/UploadSection.jsx`)
- Replaced bubbly dropzone with an architectural mounting plate equipped with subtle corner ticks (`border-t border-l border-archive-hairline`).
- Replaced `Sparkles` with `BookOpen`.
- Renamed turnkey samples to **"Curated Reference Specimens"** with clear historical era attributions (Mughal, Qutb Shahi, Vijayanagara, Chola).

### 3.4 Processing Overlay (`frontend/src/components/ProcessingOverlay.jsx`)
- Replaced glassy modal with an archival photographic darkroom inspection plate.
- Eliminated neon laser glow in favor of a 1px terracotta scan marker.
- Styled stages as an orderly curatorial telemetry log.

### 3.5 Monograph Results Dossier (`frontend/src/components/MonographResult.jsx`)
Refined all five distinct decision views:
1. **`VERIFIED_MATCH`:** Reorganized top header into a clear accession band: catalog badge, catalog ID (`ASI-ARCH-REG`), tier stamp, and cosine similarity metric. Structural signatures and epigraphical citations formatted as archival field cards.
2. **`UNCERTAIN_MATCH`:** Replaced neon yellow borders with restrained amber (`#D97706`), presenting side-by-side candidate comparison with discriminative margin bar.
3. **`UNKNOWN_HERITAGE_SPECIMEN`:** Replaced bright electric-blue badges with dignified slate/blue archival tags, displaying open-world attribution from Gemini 3.1 Flash-Lite without speculative over-confidence.
4. **`REVIEW_REQUIRED`:** Restrained terracotta warning plate indicating evidence conflict or degraded input quality.
5. **`NON_MONUMENT_REJECTED`:** Subdued rejection monograph with gatekeeper score and candidate vectors, removing harsh alert styling.

### 3.6 Uncertainty & Calibration Inspector (`frontend/src/components/PipelineInspector.jsx`)
- Removed `animate-pulse` from human review badge.
- Harmonized badge color tokens across decision states.
- Replaced technical buzzwords with multi-evidence synthesis explanations.

### 3.7 Grounded Knowledge Viewer (`frontend/src/components/GroundedKnowledgeViewer.jsx`)
- Removed `Sparkles` icon from verified curatorial facts and living traditions.
- Maintained strict tab structure: Overview, Architectural Analysis, Timeline, Cultural Significance, Preservation Record, Source Archive, and Curatorial Inquiry.
- Inquiry response styled as an authoritative field research report with explicit grounding disclaimers.

### 3.8 Authentication Portals (`Login.jsx` & `Signup.jsx`)
- Removed `liquid-glass` class.
- Replaced `Sparkles` icon on demo login with `KeyRound`.
- Preserved secure session authentication and local credential validation.

---

## 4. Verification & Build Integrity

### 4.1 Production Build (`npm run build`)
- **Modules Transformed:** 2,084
- **Build Duration:** 10.17 seconds
- **Errors / Syntax Warnings:** 0
- **Bundle Output:**
  - `dist/index.html`: 1.28 kB (gzip: 0.72 kB)
  - `dist/assets/index-Co3lK9Sc.css`: 51.35 kB (gzip: 13.28 kB)
  - `dist/assets/index-CED72eoO.js`: 735.37 kB (gzip: 213.88 kB)

### 4.2 Local Service Health
- **FastAPI Backend:** Running on `http://127.0.0.1:8000`
- **Health Endpoint (`/api/health`):**
  - Status: `healthy`
  - FAISS Vectors: `577`
  - Catalogue Count: `100` sites
  - Knowledge Records: `10` sites
  - Model Device: `cpu`
  - Tier 2 VLM: `gemini-3.1-flash-lite`
- **Vite Frontend:** Running on `http://localhost:5173` (`HTTP/1.1 200 OK`)

---

## 5. Architectural Non-Regression Commitments Verified
- **No Git Push:** Repository unpushed to GitHub per user constraint.
- **No Public Cloud Tunnels:** Zero Localtunnel or Cloudflare processes running.
- **Backend Recognition Thresholds:** SIFT/ORB, FAISS inner-product search, and Confidence Calibration Engine preserved with 100% fidelity.

