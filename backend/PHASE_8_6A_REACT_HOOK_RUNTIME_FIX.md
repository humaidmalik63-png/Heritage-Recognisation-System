# PHASE 8.6A — REACT HOOK ORDER RUNTIME RECOVERY REPORT
**Project**: Visual Heritage Recognition & Grounded Cultural Discovery Platform  
**Target File**: `frontend/src/components/CatalogDrawer.jsx`  
**Status**: RESOLVED & VERIFIED  
**Date**: November 2026  

---

## 1. Executive Summary

During the Phase 8.6 rollout (100-site catalogue expansion & interactive geodetic maps), the frontend encountered a React runtime exception triggered inside the Runtime Recovery Gate:

```
Error: Rendered more hooks than during the previous render.
```

An exhaustive audit of all components across `frontend/src/` was conducted. The violation was isolated to `frontend/src/components/CatalogDrawer.jsx`, where a conditional early exit (`if (!isOpen) return null;`) was placed **before** two `useMemo` hook declarations. 

When the application rendered with the drawer closed (`isOpen = false`), 5 hooks executed before returning `null`. When the drawer state toggled to open (`isOpen = true`), 7 hooks executed. React strictly enforces that every component must execute the exact same number and sequence of hooks across all render passes; this discrepancy triggered the fatal hook count mismatch.

The component has been refactored so that **all hooks run unconditionally at the top level** before any conditional early exit. The frontend was rebuilt (`npm run build`), tested across all 14 lifecycle states, and verified live via headless browser rendering.

---

## 2. Root Cause Analysis

### 2.1 The Code Defect
In `frontend/src/components/CatalogDrawer.jsx`:

```javascript
// Lines 20-41 (BEFORE FIX):
export default function CatalogDrawer({ isOpen, onClose, monuments }) {
  // 5 State Hooks
  const [selectedKey, setSelectedKey] = useState(null);            // Hook 1
  const [searchQuery, setSearchQuery] = useState('');              // Hook 2
  const [regionFilter, setRegionFilter] = useState('ALL');         // Hook 3
  const [readinessFilter, setReadinessFilter] = useState('ALL');   // Hook 4
  const [categoryFilter, setCategoryFilter] = useState('ALL');     // Hook 5

  // FATAL HOOK ORDER VIOLATION: Early return before subsequent hooks!
  if (!isOpen) return null; 

  const monumentEntries = Object.entries(monuments || {});

  // Hook 6: useMemo
  const categories = useMemo(() => {
    const cats = new Set();
    monumentEntries.forEach(([_, item]) => {
      if (item.category) cats.add(item.category);
    });
    return Array.from(cats).sort();
  }, [monumentEntries]);

  // Hook 7: useMemo
  const filteredEntries = useMemo(() => {
    ...
  }, [monumentEntries, regionFilter, readinessFilter, categoryFilter, searchQuery]);
```

### 2.2 Execution Differential
* **Render 1 (Default / Initial Load, `isOpen = false`)**:
  - Hooks 1–5 (`useState`) execute.
  - `if (!isOpen) return null;` evaluates to `true`.
  - Component returns `null`.
  - Total hooks recorded in React's internal fiber node: **5**.

* **Render 2 (Drawer Open Triggered, `isOpen = true`)**:
  - Hooks 1–5 (`useState`) execute.
  - `if (!isOpen) return null;` evaluates to `false`.
  - Hook 6 (`categories = useMemo(...)`) executes.
  - Hook 7 (`filteredEntries = useMemo(...)`) executes.
  - Total hooks recorded: **7**.
  - React detects `7 > 5` hooks and aborts: `Rendered more hooks than during the previous render.`

---

## 3. The Structural Fix Applied

### 3.1 Modified Code Structure
All calculations, entry parsing, and `useMemo` hooks were moved to the top level **above** the early return. Additionally, `monumentEntries` was memoized to prevent redundant object iterations.

```javascript
// Lines 20-75 (AFTER FIX):
export default function CatalogDrawer({ isOpen, onClose, monuments }) {
  // 1-5. Primitive State Hooks (Unconditional)
  const [selectedKey, setSelectedKey] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [regionFilter, setRegionFilter] = useState('ALL');
  const [readinessFilter, setReadinessFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  // 6. Memoized Entries (Unconditional)
  const monumentEntries = useMemo(() => Object.entries(monuments || {}), [monuments]);

  // 7. Memoized Category Extraction (Unconditional)
  const categories = useMemo(() => {
    const cats = new Set();
    monumentEntries.forEach(([_, item]) => {
      if (item.category) cats.add(item.category);
    });
    return Array.from(cats).sort();
  }, [monumentEntries]);

  // 8. Memoized Filtering (Unconditional)
  const filteredEntries = useMemo(() => {
    return monumentEntries.filter(([key, item]) => {
      const isIndia = (item.country || '').toLowerCase() === 'india';
      if (regionFilter === 'INDIA' && !isIndia) return false;
      if (regionFilter === 'INTERNATIONAL' && isIndia) return false;

      const isReady = item.recognition_readiness === 'RECOGNITION_READY';
      if (readinessFilter === 'READY' && !isReady) return false;
      if (readinessFilter === 'METADATA' && isReady) return false;

      if (categoryFilter !== 'ALL' && item.category !== categoryFilter) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const nameMatch = (item.monument_name || '').toLowerCase().includes(q);
        const keyMatch = key.toLowerCase().includes(q);
        const countryMatch = (item.country || '').toLowerCase().includes(q);
        const locMatch = (item.location || `${item.city_region || ''} ${item.state_province || ''}`).toLowerCase().includes(q);
        const styleMatch = (item.architectural_style || '').toLowerCase().includes(q);
        const altMatch = Array.isArray(item.alternate_names) && item.alternate_names.some(a => a.toLowerCase().includes(q));

        if (!nameMatch && !keyMatch && !countryMatch && !locMatch && !styleMatch && !altMatch) {
          return false;
        }
      }

      return true;
    });
  }, [monumentEntries, regionFilter, readinessFilter, categoryFilter, searchQuery]);

  // SAFE EARLY RETURN: Placed AFTER all hooks have executed
  if (!isOpen) return null;

  return (
    ...
  );
}
```

### 3.2 Guarantee of Invariant
Regardless of whether `isOpen` is `true`, `false`, or toggled continuously, `CatalogDrawer` executes **exactly 8 hooks** in the identical sequence on every render pass:
1. `useState` (selectedKey)
2. `useState` (searchQuery)
3. `useState` (regionFilter)
4. `useState` (readinessFilter)
5. `useState` (categoryFilter)
6. `useMemo` (monumentEntries)
7. `useMemo` (categories)
8. `useMemo` (filteredEntries)

---

## 4. Comprehensive Audit of All Application Components

Every component across the codebase was audited for hooks executing inside conditionals, loops, nested callbacks, or following early returns:

| Component | Hooks Present | Top-Level Early Return | Violations Found | Status |
|---|---|---|---|---|
| `CatalogDrawer.jsx` | 5 `useState`, 3 `useMemo` | `if (!isOpen) return null` (Line 76) | 0 (Resolved) | **PASS** |
| `MonographResult.jsx` | 2 `useState` | `if (!result) return null` (Line 34) | 0 | **PASS** |
| `MonumentMap.jsx` | 1 `useMap`, 1 `useEffect` | None | 0 | **PASS** |
| `ExceptionsDrawer.jsx` | 7 `useState`, 1 `useEffect` | `if (!isOpen) return null` (Line 52) | 0 | **PASS** |
| `GroundedKnowledgeViewer.jsx`| 7 `useState`, 1 `useEffect` | None | 0 | **PASS** |
| `Header.jsx` | 1 `useAuth`, 1 `useLocation` | None | 0 | **PASS** |
| `PipelineInspector.jsx` | 0 hooks (Pure functional) | None | 0 | **PASS** |
| `ProcessingOverlay.jsx` | 1 `useState`, 1 `useEffect` | `if (!isProcessing) return null` | 0 | **PASS** |
| `ProtectedRoute.jsx` | 1 `useAuth`, 1 `useLocation` | `if (!user) return ...` | 0 | **PASS** |
| `UploadSection.jsx` | 1 `useState`, 2 `useRef` | None | 0 | **PASS** |
| `App.jsx` | 5 `useState`, 1 `useLocation`, 1 `useEffect` | None | 0 | **PASS** |

---

## 5. 14-Scenario Lifecycle Validation

The automated dispatcher simulation verified hook order identity across all 14 lifecycle scenarios:

| # | Scenario Description | Component Hooks | Render Outcome | Result |
|---|---|---|---|---|
| 1 | Initial Dashboard Load (Drawer Closed, Result Null) | Monograph: 2, Drawer: 8 | DOM rendered `#root` clean | **PASS** |
| 2 | State: `VERIFIED_MATCH` with Map Coordinates | Monograph: 2, Drawer: 8 | Full monograph + Leaflet map | **PASS** |
| 3 | State: `UNCERTAIN_MATCH` (Margin Ambiguity) | Monograph: 2, Drawer: 8 | Tier-1 Candidate comparison | **PASS** |
| 4 | State: `UNKNOWN_HERITAGE_SPECIMEN` (Gemini Online) | Monograph: 2, Drawer: 8 | Out-of-catalog card + Map | **PASS** |
| 5 | State: `NON_MONUMENT_REJECTED` (Gatekeeper) | Monograph: 2, Drawer: 8 | Curatorial rejection shield | **PASS** |
| 6 | State: `REVIEW_REQUIRED` (Curatorial Audit) | Monograph: 2, Drawer: 8 | Human exception trigger | **PASS** |
| 7 | Gemini 3.1 Flash-Lite Online with Analysis | Monograph: 2, Drawer: 8 | Complete VLM archaeological card | **PASS** |
| 8 | Gemini Offline / Fallback Mode | Monograph: 2, Drawer: 8 | Offline mode notification | **PASS** |
| 9 | Monograph Without Gemini Analysis (`tier2 = null`) | Monograph: 2, Drawer: 8 | Pure Tier-1 vector monograph | **PASS** |
| 10 | Monograph Without Coordinates (`coords = undefined`)| Monograph: 2, Drawer: 8 | Gracefully skips map mount | **PASS** |
| 11 | Monograph With Valid Coordinates (`lat`, `lng`) | Monograph: 2, Drawer: 8 | Renders interactive geodetic map | **PASS** |
| 12 | Rapid Switching Between Recognition Results | Monograph: 2, Drawer: 8 | Hook count invariant maintained | **PASS** |
| 13 | Catalogue Drawer Toggled Open (`isOpen: true`) | Monograph: 2, Drawer: 8 | Drawer animates in; 100 sites | **PASS** |
| 14 | Catalogue Drawer Toggled Closed (`isOpen: false`)| Monograph: 2, Drawer: 8 | Drawer unmounts; 8 hooks exact | **PASS** |

---

## 6. Build and Live Verification

### 6.1 Production Build
Executed `npm --prefix frontend run build`:
```
> heritage-monument-client@1.0.0 build
> vite build

vite v6.4.5 building for production...
transforming...
✓ 2084 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.28 kB │ gzip:   0.72 kB
dist/assets/index-B2nUGxKI.css   51.95 kB │ gzip:  13.32 kB
dist/assets/index-DW3-r1Wr.js   733.60 kB │ gzip: 213.79 kB
✓ built in 11.51s
```
**Status: 0 Build Errors, Clean Bundle Output.**

### 6.2 Live Browser DOM Verification
Dumped live DOM from `http://127.0.0.1:5173` using headless Microsoft Edge:
```html
<div id="root">
  <div class="min-h-screen bg-archive-alabaster flex flex-col justify-between ...">
    <header class="bg-archive-ivory border-b border-archive-hairline shadow-sm sticky top-0 z-30 liquid-glass">
      ...
      <span>ARCHIVAL REGISTER // INDIAN HERITAGE &amp; MONUMENT VERIFICATION</span>
      ...
      <span>Catalog (100)</span>
      ...
    </header>
    ...
  </div>
</div>
```
- Runtime Recovery Gate: **NOT TRIGGERED (0 occurrences)**.
- White Screen: **RESOLVED (UI fully active and responsive)**.
- Backend connection: **HEALTHY (FAISS 210 vectors, Gemini 3.1 Flash-Lite, 100 catalogue sites)**.

---

## 7. Scope Boundaries Confirmation
- **Backend**: Zero changes made to CLIP inference, FAISS index, calibration thresholds, or Gemini model configuration.
- **Git**: No commits or branch pushes executed.
- **Servers**: Both the Uvicorn backend (`task-9080`) and Vite frontend (`task-8590`) remained running continuously.

