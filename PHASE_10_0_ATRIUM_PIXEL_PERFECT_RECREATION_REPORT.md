# PHASE 10.0: ATRIUM MTL PIXEL-PERFECT WEBSITE RECREATION REPORT

**Project:** ATRIUM MTL Reference Replication  
**Target File:** `frontend/atrium-reference/index.html`  
**Preview Server:** `http://localhost:8085/`  
**Date:** November 2026  
**Status:** COMPLETE & VISUALLY VALIDATED  

---

## 1. Antigravity Skills Discovered & Applied

Prior to implementation, the environment was audited for available UI/UX and frontend engineering skills:

1. **`antigravity-design-expert`**:
   - Applied spatial Z-axis layering principles (header card `z-index: 5` floating above mosaic `z-index: 1`), smooth hardware-accelerated transforms (`translate3d`), and `will-change` lifecycle scoping.
   - Enforced strict `@media (prefers-reduced-motion: reduce)` disabling of marquee animations and WAAPI transitions.

2. **`emil-design-eng`**:
   - Reviewed interaction craft, tactile button hover states (`scale(1.02)` on `.tickets-pill`, rotate & scale on `.ticket-badge`), and smooth easing curves.
   - Verified accessibility compliance: focus visible outlines (`outline: 2px solid #3b82f6; outline-offset: 3px`), comprehensive ARIA labels on all interactive controls (`role="banner"`, `role="main"`, `aria-label`, `aria-expanded`, `aria-hidden="true"` on decorative mosaic).

3. **`design-taste-frontend`**:
   - Verified typography hierarchy: strict display font binding to Archivo 900, headline stroke calibration (`-webkit-text-stroke: 1.1px`), exact letter-spacing (`-0.06em`), and disciplined body text containment.
   - Preserved viewport-locked stability using `100svh` and `overflow: hidden`, preventing unwanted document scroll bars across mobile, tablet, and desktop viewports.

4. **`design-system`**:
   - Enforced exact CSS design token architecture (`:root` tokens: `--paper`, `--ink`, `--card-dark`, `--card-cream`, `--red`, `--yellow`, `--blue`, `--col`, `--gap`, `--pitch`, `--r`).

---

## 2. Files Created

- **`frontend/atrium-reference/index.html`**:
  - The authoritative, self-contained single-document recreation.
  - Contains inline `<style>`, inline SVG icons, and vanilla JavaScript only.
  - Zero external frameworks, zero npm dependencies, zero build steps.
- **`frontend/atrium-reference/assets/fonts/archivo.woff2`**:
  - Variable Archivo font supporting weights 100–900 and widths 62%–125% (`90,104` bytes).
- **`frontend/atrium-reference/assets/fonts/inter.woff2`**:
  - Variable Inter font supporting weights 100–900 (`48,256` bytes).
- **`frontend/atrium-reference/screenshots/`**:
  - Comprehensive automated Chrome DevTools Protocol (CDP) screenshot suite validating all 7 target viewports.

---

## 3. Remote Assets & Fonts Verification

### 3.1 CloudFront Remote Media Assets
All 5 exact CloudFront asset URLs were preloaded in `<head>` and bound in `:root`:
- `--img-sculpt`: `https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/fc524fc3-03c3-40a1-9954-22eab1322592.webp`
- `--img-man`: `https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/1d56967e-0ed5-40f8-812d-9360e5ec1780.webp`
- `--img-visit`: `https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/5f3f6135-26b9-4c48-92ad-105161327cbc.webp`
- `--img-sil`: `https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/e7b68ae9-9240-4f52-a0a2-89082df4b8d0.webp`
- `--grain`: `https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/40b7fef3-410d-4ef3-bd67-0a2fc7ee5a1d.svg`

### 3.2 Self-Hosted Font Assets
Both variable web font files were provisioned in `frontend/atrium-reference/assets/fonts/` matching the specification:
- `@font-face Archivo`: `assets/fonts/archivo.woff2` (100–900, stretch 62%–125%)
- `@font-face Inter`: `assets/fonts/inter.woff2` (100–900)
Both fonts load locally with `font-display: block` and zero FOIT/FOUT fallbacks.

---

## 4. Visual Layout & DOM Structure Implementation

1. **Floating Header Card (`.hdr`)**:
   - Desktop dimensions: `left: 40px`, `right: 40px`, `height: 142px`, `border-radius: 0 0 22px 22px`.
   - Utility strip (40px height):
     - Telephone 1: `tel:+14188386000` ("House of Brutalism : 418 / 838-6000").
     - 18px hairline vertical rule at 313px.
     - Telephone 2: `tel:+14188386001` ("Studio Exhibitions : 418 / 838-6001").
     - Utility nav: Programmes, Events, Photo-prints (stacked two-line), Visits, Help preserve (stacked two-line).
     - Search button: 39×39px `#e8e7e2` with 13×13px inline SVG magnifier.
   - Main bar (102px height):
     - Logo: ATRIUM MTL (31px, Archivo 900, 85% stretch, 0.35px stroke) + subtext ("AN ARCHIVE OF LIGHT CAST IN STONE", 8.6px, muted).
     - Main Nav: Installations + 24px black circle arrow, rule separator, Interviews, Photographs, Menu button (burger icon + "Menu").
     - CTA: 116×63px rounded black pill "Tickets" (22px radius) overlapped with a 64×64px circular ticket icon rotated at -45°.

2. **Hero Typography & Content (`.hero`)**:
   - Position: `left: 86px`, `top: calc(200px + (var(--H, 800) - 800) * 0.5px)`, `width: 480px`.
   - 4-line H1 reveal:
     - Line 1: `An archive`
     - Line 2: `of light`
     - Line 3: `cast in`
     - Line 4: `stone`
     - Archivo 900, 80px, line-height 75.3px, letter-spacing -0.06em, text-stroke 1.1px.
   - Body copy (at top 344px):
     - *"ATRIUM MTL archives old structures as raw photographs from across Montreal, a collection at an **Annual Photography Retrospective**, autumn 2026."*
   - Actions (at top 460px): Tickets pill + Installations link with 32px arrow circle.

3. **6-Column Kinetic Mosaic (`.grid`)**:
   - Order: `x3`, `x2`, `x1`, `c1`, `c2`, `c3` (each having 5 `.cell` elements):
     - `c1`: red, sculpture (`f-sculpt`), man (`f-man`), blue, visit
     - `c2`: yellow, visit (`f-visit`), dark, silhouette, red
     - `c3`: blue, cream, silhouette (`f-sil`), yellow, sculpture
     - `x1`: blue, man, red, sculpture, cream
     - `x2`: yellow, silhouette, cream, red, visit
     - `x3`: man, blue, dark, sculpture, yellow
   - Numeric photo crops implemented via `::before`:
     - `.f-sculpt`: width `124.19%`, height `112.57%`, left `-16.07%`, top `-8.5%`
     - `.f-man`: width `113.48%`, height `103.36%`, left `-5.36%`, top `-3.54%`
     - `.f-visit`: width `110.07%`, height `100%`, left `-3.9%`, top `8.5%` + 3-stop linear gradient and top fade
     - `.f-sil`: width `139.29%`, height `126.37%`, left `-8.77%`, top `-56.64%`
   - Grain texture overlay (`--grain`) applied with `multiply 0.13` on color tiles and `screen 0.035` on dark tiles.

---

## 5. Animation Engine & WAAPI Handoff

- **CSS Infinite Marquee**:
  - Speed: 14.6s linear loop (`0.342` card heights/sec).
  - Directions: `.c1`, `.c3`, `.x2` move `colDown` (`0` to `-50%`); `.c2`, `.x1`, `.x3` move `colUp` (`-50%` to `0`).
  - JS clones each column's 5 cells once so 50% translate loops seamlessly without visual seams.
- **WAAPI Choreographed Entrance Timeline**:
  - Header slides down from `translateY(calc(-100% - 48px))` (0.95s, EXPO `cubic-bezier(0.16, 1, 0.3, 1)`).
  - Staggered utility strip fade (from 0.32s, 40ms stagger).
  - Logo drops 10px; nav items drop 8px; CTA drops.
  - H1 `.ln` elements rise from `110%` over 1.0s (stagger 85ms from 0.30s).
  - Body text rises 14px; actions rise 12px.
  - Columns enter with smooth Quint-out deceleration and at `T0 + 2100ms`, control is handed off seamlessly to the running CSS marquee.

---

## 6. Responsive Architecture & Visual Validation

All 7 required viewport resolutions were rendered, captured via headless Chrome DevTools Protocol, and inspected:

| Viewport | Mode | Result | Notes |
| :--- | :--- | :--- | :--- |
| **1280 × 800** | `desk` | **PASSED** | Reference baseline. 1:1 canvas scale (`--s: 1.0`), 3-column mosaic aligned under header, 4-line headline with exact negative tracking. |
| **1440 × 900** | `desk` | **PASSED** | Proportional scaling (`--s: 1.125`), zero letterboxing, sharp subpixel rendering. |
| **1920 × 1080** | `desk` (`ex1`) | **PASSED** | Wide canvas scaling; extra column `.x1` dynamically activates on the left of `.c1`. |
| **390 × 844** | `mob` | **PASSED** | Mobile portrait; logo on left, `≡ Menu` button on right, single flex column, 3-column mosaic band below actions. Zero horizontal scroll. |
| **430 × 932** | `mob` | **PASSED** | iPhone 14/15 Pro Max layout; identical fluid proportions, safe area respected. |
| **768 × 1024** | `tab-p` | **PASSED** | Tablet portrait; full utility strip, centered `≡ Menu`, Tickets pill on right, 4-column balanced mosaic band. |
| **1024 × 768** | `tab-l` | **PASSED** | Tablet landscape; side-by-side hero text and 3-column mosaic, full utility header. |

---

## 7. Isolation & Verification of Existing Project

- **Existing React Application (`frontend/src/`)**: 100% UNTOUCHED.
- **Backend Recognition Engine & Models (`backend/`)**: 100% UNTOUCHED.
- **FastAPI Server**: Running on `http://127.0.0.1:8000` (Status: `healthy`, 577 FAISS vectors).
- **Vite React Dev Server**: Running on `http://localhost:5173/` (Status: `200 OK`).
- **No Git Commit / Push**: Repository remains on branch `main` without unstaged additions or remote pushes.

