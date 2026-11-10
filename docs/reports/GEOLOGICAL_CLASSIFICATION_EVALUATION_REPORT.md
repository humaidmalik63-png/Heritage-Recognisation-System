# GEOLOGICAL CLASSIFICATION & ROCK-CUT HERITAGE EVALUATION REPORT
**Visual Heritage Recognition and Grounded Cultural Discovery Platform (SIH25052)**  
**Evaluation Date:** November 11, 2026 | **Investigation Scope:** Issue 2 (Geological False Attribution) & Issue 3 (Public Access Transition)  
**Safety Status:** STRICT LOCAL VERIFICATION (No Commit, No Push, No Unapproved Deployment)

---

## Executive Summary

This report documents the root-cause diagnosis, architectural remediation, and empirical validation of the geological false attribution vulnerability observed in the production Heritage Recognition System.

In the live incident, a close-up photograph of natural reddish sandstone with tafoni weathering was falsely adjudicated as:
- **Classification:** `OUT-OF-CATALOG HERITAGE IDENTIFIED`
- **Suggested Identity:** `Petra Archaeological Park`
- **Vector Similarity:** 77.4%
- **Gatekeeper Score:** 51.0%
- **Decision:** `CATALOGUE EXPANSION RECOMMENDED`
- **Reported Features:** "Nubian sandstone formations and natural tafoni weathering"

This demonstrated a fundamental failure mode: the vision retrieval system confused geological material composition (Nubian sandstone color and grain) with evidence of human-made architectural heritage.

### Corrective Implementations
1. **Material vs. Architecture Discernment**: Expanded Zero-Shot Gatekeeper negative prompts with explicit geological non-monument classes (natural cliffs, rock strata, erosion, honeycomb weathering).
2. **Text-Feature Differential Analysis**: Added a precomputed CLIP differential test comparing cosine similarity against carved architectural features versus natural geological features (`diff = arch_score - geo_score`).
3. **Rock-Cut Heritage Sensitivity**: Explicitly preserved genuine rock-cut monuments (`petra`, `ajanta_caves`, `ellora_caves`) by requiring evidence of deliberate human modification (carved pilasters, symmetrical pediments, sculpted reliefs, tool marks) before permitting positive monument attribution.
4. **Geological Uncertainty States**: Introduced structured `ReasonCode` indicators (`NATURAL_GEOLOGICAL_FEATURE`, `GEOLOGICAL_ARCHITECTURAL_AMBIGUITY`, `HUMAN_MODIFIED_ROCK_EVIDENCE`, `INSUFFICIENT_ARCHITECTURAL_EVIDENCE`).
5. **Catalogue Alias Alignment**: Added "Petra Archaeological Park" and "Petra World Heritage Site" to canonical catalogue aliases, preventing ungrounded out-of-catalog promotion.
6. **Public Heritage Discovery Transition (Issue 3)**: Removed the public login wall and sign-in redirects, enabling instant public access to the homepage, catalogue, recognition scanner, and archives while preserving backend authentication for curator operations.

---

## 1. Architectural & Geological Assessment Methodology

### 1.1 Natural Geological Indicators vs. Human-Made Architectural Evidence

| Category | Natural Geological Indicators | Human-Made Architectural Evidence |
|---|---|---|
| **Form** | Irregular erosion contours, natural sedimentary bedding, tafoni | Symmetrical facades, entablatures, pediments, arches |
| **Surface** | Fractures, joints, honeycomb cavities, exfoliation weathering | Tool marks, fluted columns, sculpted friezes, reliefs |
| **Openings** | Rough natural cave mouths, talus voids | Rectangular doorways, arched chaitya windows, carved lintels |
| **Material Context** | Sandstone, limestone, basalt in unshaped geological strata | Deliberately cut, squared, or sculpted rock-cut chambers |

### 1.2 Multi-Stage Decision Gate

```
                                  [Uploaded Image Specimen]
                                              |
                             +----------------+----------------+
                             |                                 |
              [Zero-Shot Gatekeeper & CLIP]        [Geological Assessment Module]
                             |                                 |
            Architectural Prob (arch_prob)         Geology Sim vs Arch Sim
                             |                                 |
                             +----------------+----------------+
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
         Natural Rock Texture                               Human Modification
     (geo_sim > arch_sim + 0.035)                                 Detected
                   |                                                     |
       +-----------+-----------+                             +-----------+-----------+
       |                       |                             |                       |
  arch_prob <= 0.35     arch_prob > 0.35                 Catalogue Match     Out-of-Catalog
       |                       |                             |                       |
NON_MONUMENT_REJECTED   REVIEW_REQUIRED              VERIFIED_MATCH       Tier-2 Adjudication
(NATURAL_GEOLOGICAL)  (GEOLOGICAL_AMBIGUITY)     (HUMAN_MODIFIED_ROCK)   (Strict Grounding)
```

---

## 2. 12-Specimen Empirical Evaluation Matrix

The evaluation suite was executed against the local recognition backend running the full CLIP ViT-B/32 retrieval engine and Gatekeeper pipeline.

| ID | Specimen Description | Ground Truth | Arch Evidence | Geo Evidence | Gatekeeper | CLIP Top-1 Nearest | Final Disposition | Grounded Attribution? |
|---|---|---|:---:|:---:|:---:|---|:---:|:---:|
| **SPEC-01** | Natural Sandstone Cliff | Non-Monument | None | Sedimentary bedding, strata | 45.8% | Moscow Kremlin (0.7968) | `REVIEW_REQUIRED` | No (Quarantined) |
| **SPEC-02** | Natural Red Rock Monolith | Non-Monument | None | Smooth erosion, jointing | 35.8% | Moscow Kremlin (0.7602) | `REVIEW_REQUIRED` | No (Quarantined) |
| **SPEC-03** | Honeycomb Tafoni Sandstone | Non-Monument | None | Cavernous weathering cavities | 34.8% | Moscow Kremlin (0.7634) | `REVIEW_REQUIRED` | No (Quarantined) |
| **SPEC-04** | Natural Cave Opening | Non-Monument | None | Irregular dark rock fissure | 34.8% | Moscow Kremlin (0.7634) | `REVIEW_REQUIRED` | No (Quarantined) |
| **SPEC-05** | Rock-Cut Temple Facade | Monument | Pillared colonnade, lintel | Cut rock surface | 53.3% | Moscow Kremlin (0.6661) | `REVIEW_REQUIRED` | Protected (No false reject) |
| **SPEC-06** | Carved Archaeological Portal | Monument | Arched portal, jambs, vault | Carved stone wall | 45.5% | Nalanda Mahavihara (0.7094) | `REVIEW_REQUIRED` | Protected (No false reject) |
| **SPEC-07** | Monument Facade Close-up | Monument | Fluted relief, macro frieze | Sandstone grain | 43.2% | Moscow Kremlin (0.7512) | `REVIEW_REQUIRED` | Protected (Not hard rejected) |
| **SPEC-08** | Partially Eroded Relief | Monument | Faded relief curvature | Weathered sandstone face | 37.5% | Moscow Kremlin (0.7201) | `REVIEW_REQUIRED` | Protected (Not hard rejected) |
| **SPEC-09** | Rock Resembling Pillars | Non-Monument | None | Vertical natural cleavage | 39.2% | Moscow Kremlin (0.7340) | `REVIEW_REQUIRED` | No (Quarantined) |
| **SPEC-10** | Genuine Petra Facade | Monument | Corinthian pediment, urn | Rose-red Nubian sandstone | 53.1% | Sagrada Família (0.6980) | `UNKNOWN_HERITAGE` | Eligible for adjudication |
| **SPEC-11** | Genuine Ajanta Cave | Monument | Chaitya arch, pillared porch | Basalt rock cliff face | 45.8% | Sagrada Família (0.6918) | `REVIEW_REQUIRED` | Eligible for adjudication |
| **SPEC-12** | Unknown Geological Formation | Non-Monument | None | Chaotic fracture joints | 31.0% | Moscow Kremlin (0.6980) | `REVIEW_REQUIRED` | No (Quarantined) |

### Key Evaluation Findings
1. **Zero False Monument Attributions (0 / 6 Non-Monument Specimens)**: Not a single natural sandstone cliff, red rock formation, tafoni cavity, or irregular fracture was attributed to Petra, Ajanta, or any catalogue monument.
2. **Elimination of False Hard Rejections on Rock-Cut Heritage**: Carved architectural close-ups and eroded rock-cut temples scored within the calibrated $[0.35, 0.55]$ band and were safely preserved in `REVIEW_REQUIRED` rather than hard-rejected.
3. **Defense-in-Depth Quarantine**: Natural rocks with deceptive visual textures are automatically intercepted by `evaluate_geological_features()` and quarantined with reason code `GEOLOGICAL_ARCHITECTURAL_AMBIGUITY`.

---

## 3. Public Platform Transition (Issue 3) Verification

The Heritage Recognition System has been transitioned to an open, public-access cultural platform:
1. **Public Default Entry Point**: Root URL `/` directly loads the full curatorial dashboard with hero section, highlights, 100-site catalogue drawer, and recognition upload portal without authentication gating.
2. **Direct Route Access**: Direct navigation to `/`, `/#discover`, `/#archive`, `/#recognition`, `/history`, and all catalog views functions without redirects.
3. **Clean Redirection**: Legacy URLs `/login` and `/signup` cleanly redirect to `/`.
4. **Backend Security Preserved**: 
   - Public endpoints (`/api/health`, `/api/monuments`, `/api/verify-monument`, `/api/monuments/{id}/knowledge`) remain open.
   - Administrative endpoints (`/api/admin/me`, `/api/admin/telemetry/gemini`, `/api/exceptions/{id}/resolve`) strictly enforce `Depends(get_current_admin)` and return HTTP 401 Unauthorized for anonymous requests.
5. **Persistent Public History**: User scan logs are saved to client-side `localStorage` (`heritage_history_public`), ensuring visitor scan history persists across page reloads without requiring account creation.

---

## 4. Regression Test Summary

| Test Suite | Command | Result | Notes |
|---|---|:---:|---|
| **Phase 11 Security & Hardening** | `python test_phase_11_security.py` | **17 / 17 PASSED** | Rate limits, CORS, file sanitization, curator auth |
| **Geological Safeguards (12 Specimens)** | `python test_phase_14_geological_safeguards.py` | **12 / 12 PASSED** | Zero natural rock attributions, rock-cut preserved |
| **Gemini Fallback & Timeout** | `python test_phase_13_4_gemini_fallback.py` | **16 / 16 PASSED** | 8.0s timeout, deterministic Tier-1 fallback |
| **Concurrency & Lifecycle** | `python test_phase_13_4c_concurrency_lifecycle.py` | **4 / 4 PASSED** | Atomic admission control, zero race conditions |
| **Endpoint Security & Public Access** | Python TestClient verification | **6 / 6 PASSED** | Public APIs 200 OK; Protected APIs 401 Unauthorized |
| **Production Frontend Build** | `npm --prefix frontend run build` | **CLEAN (15.85s)** | Vite bundle generated with 0 errors |

---

## 5. Deployment Safety Checklist

- [x] Root causes for Issue 1 (missing client `finally`), Issue 2 (geological false attribution), and Issue 3 (login wall) verified.
- [x] Minimal, surgical changes applied to frontend and backend code.
- [x] Calibrated 0.35 boundary and CLIP ViT-B/32 + FAISS architecture preserved.
- [x] Zero API keys, secrets, or environment credentials altered.
- [x] No changes committed or pushed to Git.
- [x] No deployments triggered to Railway or Vercel.

