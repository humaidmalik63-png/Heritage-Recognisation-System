# PHASE 8.6 — 100-SITE HERITAGE CATALOGUE EXPANSION & GEMINI INTERACTIVE MAP REPORT

**Project**: Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Competition / Identification**: Smart India Hackathon (SIH 2025) — SIH25052  
**Implementation Phase**: Phase 8.6  
**Execution Timestamp**: 2026-11-07  
**Status**: COMPLETE (100% PASS across all verification suites)

---

## 1. Executive Summary

Phase 8.6 accomplishes two primary architectural evolutions for the platform:
1. **Interactive Geodetic Map Panel for Gemini Open-World Adjudication**: Connected the Tier-2 Gemini 3.1 Flash-Lite adjudication engine to an authoritative geodetic resolution service. When Gemini identifies an out-of-catalog heritage site, the system cross-references the proposed monument name against authentic registry data, maps exact verified latitude/longitude coordinates (never hallucinating coordinates), and renders an interactive OpenStreetMap Leaflet panel with an archival rust-red marker, zoom controls, and cartographic metadata directly inside the Curatorial Monograph interface (View 2). A graceful fallback notice is rendered if geodetic coordinates are pending field survey.
2. **Expansion to Exactly 100 Heritage Sites (50 Indian + 50 International)**: Expanded the catalog from 10 monuments to exactly 100 world-renowned cultural monuments and archaeological wonders while preserving 100% backward compatibility. The catalogue features 50 Indian sites (including the 10 core flagship monuments) and 50 International sites across Europe, the Americas, Asia, and Africa. Every site contains complete curatorial metadata: stable ID, primary title, vernacular alternate names, country, state/province, city/region, verified latitude/longitude, architectural style, historical epoch/dynasty, curated monograph overview, UNESCO/ASI preservation framework, and recognition readiness classification (`RECOGNITION_READY` vs. `METADATA_ONLY`).

---

## 2. Pre-Change Safeguards & Operational Health Check

Before modifying codebase configurations, local safety backups were created and verified:
- `backend/datasets/monument_index_v2.faiss.bak_phase8_5` (430,125 bytes)
- `backend/datasets/monument_labels_v2.json.bak_phase8_5` (85,508 bytes)
- `backend/knowledge_sources.json.bak_phase8_5` (87,836 bytes)
- `backend/monument_index.faiss.bak_phase8_5` (430,125 bytes)
- `backend/monument_labels.json.bak_phase8_5` (85,508 bytes)
- `backend/monuments_metadata.json.bak_phase8_5` (20,115 bytes)

Pre-change test suites verified complete operational health:
- `test_index.py`: **10/10 (100% Top-1 Accuracy, Cosine Similarity > 0.91)**
- `test_uncertainty.py`: **13/13 Scenarios Passed**
- `test_knowledge_engine.py`: **10/10 Scenarios Passed**
- `test_gemini_integration.py`: **12/12 Scenarios Passed**
- `test_api.py`: **6/6 Tests Passed**
- `npm run build`: Production build cleanly completed in 10.18s

---

## 3. The 100-Site Heritage Catalogue Architecture

The catalogue is stored in `backend/datasets/heritage_catalogue_100.json` and loaded into the application state at startup.

### 3.1 Geographic and Category Distribution

| Region | Count | Primary Categories Represented |
| :--- | :---: | :--- |
| **India** | 50 | Mausoleums, Temple Complexes, Rock-Cut Cave Temples, Hill Forts, Palaces, Stepwells, Astronomical Observatories, Colonial Public Monuments |
| **International** | 50 | Ancient Amphitheatres, Megalithic Rings, Classical Temples, Gothic Cathedrals, Mesoamerican Step Pyramids, Incan Citadels, Buddhist Stupas, Moorish Palaces, Modernist Engineering Wonders |
| **Total** | **100** | **Balanced Global Heritage Coverage** |

### 3.2 Catalogue Composition Summary

#### Indian Heritage Sites (50 Sites)
1. **Core Flagship 10 (FAISS Vector-Anchored, 21 Anchors Each)**:
   - `taj_mahal` (Agra, Uttar Pradesh) — Mughal Architecture
   - `qutub_minar` (New Delhi) — Indo-Islamic Architecture
   - `charminar` (Hyderabad, Telangana) — Indo-Islamic / Qutb Shahi Architecture
   - `hawa_mahal` (Jaipur, Rajasthan) — Rajput-Mughal Architecture
   - `konark_sun_temple` (Konark, Odisha) — Kalinga Architecture
   - `gateway_of_india` (Mumbai, Maharashtra) — Indo-Saracenic Architecture
   - `hampi_stone_chariot` (Hampi, Karnataka) — Vijayanagara Dravidian Architecture
   - `sanchi_stupa` (Sanchi, Madhya Pradesh) — Ancient Buddhist Stupa
   - `victoria_memorial` (Kolkata, West Bengal) — Indo-Saracenic Revival / Neoclassical
   - `brihadeeswarar_temple` (Thanjavur, Tamil Nadu) — Dravidian Chola Architecture
2. **Recognition-Ready Extended Indian Sites (With authentic photographic assets)**:
   - `red_fort` (Delhi) — Mughal Architecture (28.6562° N, 77.2410° E)
   - `golden_temple` (Amritsar, Punjab) — Sikh Architecture (31.6200° N, 74.8765° E)
   - `mysore_palace` (Mysuru, Karnataka) — Indo-Saracenic Revival (12.3052° N, 76.6552° E)
   - `india_gate` (New Delhi) — Triumphal Arch / Neoclassical (28.6129° N, 77.2295° E)
   - `meenakshi_temple` (Madurai, Tamil Nadu) — Dravidian Nayaka Style (9.9195° N, 78.1193° E)
   - `shore_temple` (Mahabalipuram, Tamil Nadu) — Pallava Dravidian Style (12.6163° N, 80.1983° E)
   - `humayuns_tomb` (New Delhi) — Mughal Charbagh Style (28.5933° N, 77.2507° E)
   - `sun_temple_modhera` (Modhera, Gujarat) — Māru-Gurjara Style (23.5835° N, 72.1330° E)
   - `ellora_caves` / Kailasa Temple (Maharashtra) — Dravidian Rock-cut Style (20.0240° N, 75.1793° E)
   - `fatehpur_sikri` (Uttar Pradesh) — Mughal Imperial Architecture (27.0945° N, 77.6679° E)
   - `gol_gumbaz` (Vijayapura, Karnataka) — Deccani Indo-Islamic Style (16.8306° N, 75.7362° E)
3. **Curated Metadata-Only Indian Heritage (29 Sites)**:
   - `ajanta_caves`, `khajuraho_temples`, `elephanta_caves`, `nalanda_mahavihara`, `chhatrapati_shivaji_terminus`, `amer_fort`, `golconda_fort`, `somnath_temple`, `jantar_mantar_jaipur`, `mahabodhi_temple`, `rani_ki_vav`, `chittorgarh_fort`, `gwalior_fort`, `badami_cave_temples`, `belur_chennakeshava_temple`, `halebidu_hoysaleswara_temple`, `mehrangarh_fort`, `agra_fort`, `padmanabhaswamy_temple`, `ranganathaswamy_temple`, `ramappa_temple`, `dholavira`, `basilica_of_bom_jesus`, `rashtrapati_bhavan`, `lotus_temple`, `akshardham_delhi`, `jaisalmer_fort`, `kumbhalgarh_fort`, `cellular_jail`.

#### International Heritage Sites (50 Sites)
1. **Recognition-Ready Extended International Sites (With authentic photographic assets)**:
   - `eiffel_tower` (Paris, France) — Puddle-Iron Structural Expressionism (48.8584° N, 2.2945° E)
   - `colosseum` (Rome, Italy) — Classical Roman Architecture (41.8902° N, 12.4922° E)
   - `statue_of_liberty` (New York, USA) — Neoclassical Copper Repoussé (40.6892° N, -74.0445° E)
   - `big_ben` (London, United Kingdom) — Gothic Revival Architecture (51.5007° N, -0.1246° E)
2. **Curated Metadata-Only International Heritage (46 Sites)**:
   - `great_wall_of_china`, `machu_picchu`, `petra`, `christ_the_redeemer`, `chichen_itza`, `great_pyramid_of_giza`, `acropolis_of_athens`, `stonehenge`, `angkor_wat`, `alhambra`, `sagrada_familia`, `sydney_opera_house`, `leaning_tower_of_pisa`, `notre_dame_cathedral`, `louvre_pyramid`, `st_basils_cathedral`, `parthenon`, `moai_easter_island`, `borobudur`, `prambanan`, `hagia_sophia`, `blue_mosque`, `pantheon_rome`, `brandenburg_gate`, `neuschwanstein_castle`, `tower_bridge`, `westminster_abbey`, `arc_de_triomphe`, `palace_of_versailles`, `mont_saint_michel`, `kremlin`, `forbidden_city`, `terracotta_army`, `fushimi_inari_taisha`, `kinkaku_ji`, `himeji_castle`, `senso_ji`, `petronas_towers`, `burj_khalifa`, `sheikh_zayed_grand_mosque`, `carnac_stones`, `pompeii`, `teotihuacan`, `tikal`, `mesa_verde`, `golden_gate_bridge`.

---

## 4. Gemini Open-World Geodetic Map Integration

### 4.1 Anti-Hallucination Coordinate Resolution Policy
Gemini 3.1 Flash-Lite's text generation output is never treated as authoritative for floating-point coordinates. Instead, when Gemini adjudicates a monument and proposes an identity:
1. `resolve_coordinates_from_catalogue(proposed_identity)` matches the proposed identity against:
   - Normalized `monument_id`
   - Primary `monument_name` (case-insensitive)
   - Vernacular `alternate_names`
   - Bi-directional substring matching (minimum 4-character token)
2. If matched, verified geodetic coordinates are attached from `datasets/heritage_catalogue_100.json`:
   ```python
   {
       "lat": 31.6200,
       "lng": 74.8765,
       "catalog_id": "golden_temple",
       "geodetic_source": "Authoritative Heritage Registry (India / UNESCO / National Archive)"
   }
   ```
3. If unmatched or unrecognized, coordinates are strictly set to `None`.
4. In the frontend, if coordinates exist, the `<MonumentMap>` Leaflet container renders:
   - OpenStreetMap cartographic tiles
   - Archival rust-red pin icon (`#9E3B24`) with drop-shadow
   - Auto-centering `useMap().flyTo([lat, lng], 15)`
   - Pop-up badge with official monument title and administrative region
5. If unverified, the interface renders a graceful fallback notification:
   > *"Verified geographical coordinates unavailable for this site; curatorial geodetic audit pending."*

---

## 5. API & Frontend Integration

### 5.1 Updated API Endpoints
- `GET /api/health`: Returns service health, vector count, device, and both `monuments_count: 10` and `catalogue_100_count: 100`.
- `GET /api/monuments`:
  - Default: Returns all 100 heritage sites.
  - Query parameters:
    - `country`: Filter by `india`, `international`, or specific country name.
    - `category`: Filter by architectural category (e.g., `Mausoleum`, `Temple Complex`, `Hill Fort`).
    - `readiness`: Filter by `recognition_ready` vs. `metadata_only`.
    - `search`: Case-insensitive substring search matching title, alternate names, city, or style.
    - `scope=flagship`: Returns the original 10 core monuments for backward compatibility.
- `POST /api/verify-monument`:
  - Populates top-level `coordinates` and `catalog_id` when out-of-catalog heritage is adjudicated.
  - Passes `tier2_analysis.verified_coordinates` and `tier2_analysis.geodetic_source`.

### 5.2 Frontend Components Updated
- `frontend/src/components/CatalogDrawer.jsx`:
  - Full-featured drawer interface with instant search bar, Region tabs (`All (100)`, `India (50)`, `Global (50)`), Readiness filters (`Vector Ready`, `Metadata Only`), and Category dropdown.
  - Accordion expansion reveals complete monographs, historical epochs, structural signatures, source citations, and an **embedded interactive `MonumentMap`** with live OpenStreetMap tiles for any selected monument.
- `frontend/src/components/MonographResult.jsx`:
  - Integrated `MonumentMap` in View 2 (`UNKNOWN_HERITAGE_SPECIMEN` / `out_of_catalog_identified`) with geodetic source badge and graceful fallback notice.
  - Preserves all 7 curatorial monograph views.
- `frontend/src/components/Header.jsx`:
  - Header pill dynamically renders `Catalog (100)`.

---

## 6. Live Regression Verification Matrix

The test script `backend/run_phase_8_6_verification.py` was executed against the live application runtime:

| Test Part | Test Case | Target / Specimen | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **Part 1** | Catalogue Integrity | `heritage_catalogue_100.json` | 100 sites (50 IN, 50 INT) | Exactly 100 sites | **PASSED** |
| **Part 2** | Live Health Telemetry | `GET /api/health` | `catalogue_100_count: 100` | 100 loaded, healthy | **PASSED** |
| **Part 3** | API Filtering & Search | `GET /api/monuments` | All=100, IN=50, INT=50 | All=100, IN=50, INT=50 | **PASSED** |
| **Part 4** | Core Recognition (1) | `taj_mahal_view_01.jpg` | `VERIFIED_MATCH` | `VERIFIED_MATCH` (0.94+) | **PASSED** |
| **Part 5** | Core Recognition (2) | `charminar_view_01.jpg` | `VERIFIED_MATCH` | `VERIFIED_MATCH` (0.97+) | **PASSED** |
| **Part 6** | Out-of-Catalog (India) | `golden_temple.jpg` | `UNKNOWN_HERITAGE_SPECIMEN` + Map | `lat: 31.62, lng: 74.8765` | **PASSED** |
| **Part 7** | Out-of-Catalog (Global) | `eiffel_tower.jpg` | `UNKNOWN_HERITAGE_SPECIMEN` + Map | `lat: 48.8584, lng: 2.2945` | **PASSED** |
| **Part 8** | Negative Control | `mathematics_paper.jpg` | `NON_MONUMENT_REJECTED` | Rejected, coords=None | **PASSED** |

### Additional Suite Passes
- `node frontend/test_monograph_states.cjs`: **7/7 Monograph Render States Passed (0 errors)**
- `npm --prefix frontend run build`: **Built in 15.54s (0 errors)**
- Edge Headless Browser Route Audit:
  - `/`: **PASSED** (found `"Drop specimen photograph"`, `"Catalog (100)"`)
  - `/history`: **PASSED** (found `"Taj Mahal"`)
  - `/login`: **PASSED** (found `"Curator Sign In"`)
  - `/signup`: **PASSED** (found `"Create Archival Account"`)

---

## 7. Operational Instructions

To launch the platform locally:

```bash
# 1. Start the FastAPI backend
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 2. Start the Vite React frontend
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Access the interface at `http://localhost:5173`. Click the **Catalog (100)** button in the top navigation bar to explore all 100 heritage monuments with interactive cartography and curatorial monographs.

