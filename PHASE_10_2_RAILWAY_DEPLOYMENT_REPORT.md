# Phase 10.2: Heritage Platform Production Deployment Report

**Project:** Visual Heritage Recognition & Grounded Cultural Discovery Platform  
**Target Deployments:**  
- **Backend (API & Models):** Railway (`https://backend-production-b023b.up.railway.app`)  
- **Frontend (Web Application):** Vercel (`https://heritage-monuments.vercel.app`)  
**Date:** November 9, 2026  
**Status:** Approved by User • Committed • Pushed to Origin Main • Live Deployment Operational  

---

## 1. Executive Summary

Following explicit user authorization, the Phase 10.2 redesign has been committed to `origin/main` to trigger automated production deployment:
- **Desktop Visual Redesign:** ATRIUM-inspired curatorial layout, 3-column continuous scrolling mosaic with authentic heritage photography, institutional metadata ribbons, dual call-to-actions, and live telemetry ribbons.
- **Mobile Independent Experience:** Decoupled mobile-first layout with dominant 4:3 architectural sanctuary photo, sticky minimal header, touch-friendly dual CTAs, swipeable horizontal category filter carousels, 2-column compact archive cards, and a fixed bottom navigation bar (`Discover`, `Archive`, floating central `Recognise`, `Log` badge counter, `About`).
- **Header Layout Fix:** Promoted `"A Living Archive of Culture and Place"` to the top institutional metadata ribbon, restoring elegant breathing room and preventing crowded navigation links.
- **Backend Recognition Integration:** Preserved 100% of the two-tier hybrid architecture (FastAPI, 512-D CLIP ViT-B/32, 577 FAISS vectors across 100 monuments, Gemini 3.1 Flash-Lite adjudication, calibrated uncertainty engine, and grounded citations).

---

## 2. Production Services & Endpoint URLs

| Service | Environment | Production URL | Status |
|---|---|---|---|
| **Frontend Web Client** | Vercel (Edge CDN) | `https://heritage-monuments.vercel.app` | **ONLINE** |
| **Backend API Engine** | Railway (Container) | `https://backend-production-b023b.up.railway.app` | **ONLINE** |
| **Health Check Endpoint** | Railway | `https://backend-production-b023b.up.railway.app/api/health` | **ONLINE** (577 vectors, 100 sites) |
| **Recognition API** | Railway | `POST /api/verify-monument` | **ONLINE** |

---

## 3. Git Commit & Security Audit

- **Branch:** `main`
- **Secrets Audit:**
  - `backend/.env` is ignored by `.gitignore` (0 API keys committed).
  - Production secrets are injected securely via Railway environment variables (`GEMINI_API_KEY`).
  - `frontend/.env.production` contains only the public Railway backend URL (`https://backend-production-b023b.up.railway.app`).
  - FAISS index (`monument_index.faiss`) remains embedded and tracked cleanly without Git LFS pointer degradation.

---

## 4. Verification Checklists for Mobile Phone Review

When reviewing on your mobile phone:
1. **Header:** Sticky minimal header with `HERITAGE.` logo, active engine status indicator, and tap-friendly menu toggle.
2. **Hero:** Large headline *"Every place holds a story."*, supporting text, prominent Taj Mahal 4:3 photo, and dual CTAs (*Recognise a Monument* / *Explore the Archive*).
3. **Bottom Navigation Bar:** Fixed at the bottom with safe-area padding. Features Discover, Archive, highlighted terracotta Recognise button, Log (with scan count badge), and About.
4. **Archive Corpus:** Horizontal category swipe filter chips and a clean, compact 2-column card grid.
5. **Recognition Camera & Upload:** Direct field camera and gallery photo upload with real-time recognition.

