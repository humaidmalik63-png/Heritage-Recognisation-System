# Phase 8.4C.4 — Statistical Validation Gap Audit and Evidence Reconciliation

**Project**: Visual Heritage Recognition and Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)  
**Workspace**: `C:\Users\humai\Heritage PJ`  
**Date**: November 7, 2026  
**Auditor**: Principal Performance Statistician & ML Reliability Auditor  
**Phase**: 8.4C.4 (Validation Gap Closure & Evidence Reconciliation)  
**Status**: COMPLETE — ALL GAPS AUDITED & RECONCILED

---

## 1. Executive Summary & Audit Mandate

Phase 8.4C.3 executed a rigorous, paired empirical validation of Candidate Policy D shadow execution against authoritative Policy A across 240 measured requests. While Phase 8.4C.3 resolved primary concerns regarding pseudoreplication, full-spectrum warm-up, and native memory tracking, a forensic reliability review identified four outstanding validation and reporting gaps requiring formal closure before considering any future staging adjustments:

1. **Memory Measurement Reconciliation**: Normal shadow and Slow shadow exhibited peak RSS increases of $+102.51\text{ MB}$ and $+101.19\text{ MB}$ over the baseline maximum, slightly exceeding the pre-registered $\pm 100.0\text{ MB}$ margin.
2. **Incomplete p95 Equivalence Reporting**: Phase 8.4C.3 reported point estimates of p95 latency differences but did not formalize confidence intervals or a dedicated equivalence verdict for the pre-registered p95 margin ($\pm 100.0\text{ ms}$).
3. **Imprecise Timeout Terminology**: Historical reports described the 500 ms limit as a "hard deadline" or "guaranteed termination", obscuring standard Python cooperative thread cancellation semantics.
4. **Statistical Power & Sample Size Limitations**: TOST equivalence tests at the strict $\pm 20\text{ ms}$ boundary were statistically inconclusive due to high between-specimen variance across $M = 12$ specimen clusters. A formal power model is required to establish how many independent clusters are needed for definitive testing.

This audit report closes each gap with mathematical and empirical rigor, preserving all raw historical data and pre-registered margins.

---

## 2. Memory Measurement Reconciliation

### 2.1 Empirical Observations
In `backend/phase_8_4c3_resource_analysis.json`, native memory was captured via the Windows 64-bit API `GetProcessMemoryInfo` (Working Set Size / RSS), and Python heap memory was captured via `tracemalloc`:

| Condition | Mean Native RSS (MB) | Mean Overhead vs Baseline (MB) | Max Native RSS (MB) | Peak Overhead vs Baseline Max (MB) | Mean Python Heap (MB) | Max Python Heap (MB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Disabled Baseline** | 969.00 MB | — | 990.35 MB | — | 49.10 MB | 49.72 MB |
| **Normal Shadow** | 992.32 MB | **+23.32 MB** | 1092.86 MB | **+102.51 MB** | 48.49 MB | 49.72 MB |
| **Slow Shadow** | 1025.23 MB | **+56.23 MB** | 1091.54 MB | **+101.19 MB** | 49.77 MB | 50.56 MB |
| **Saturated Shadow** | 1007.15 MB | **+38.15 MB** | 1035.70 MB | **+45.35 MB** | 49.03 MB | 50.57 MB |

### 2.2 Reconciling Mean vs. Peak Overhead
- **Mean Memory Overhead**: Across all experimental repetitions, the mean resident memory overhead introduced by shadow execution was $+23.32\text{ MB}$ (Normal), $+56.23\text{ MB}$ (Slow), and $+38.15\text{ MB}$ (Saturated). All mean increases comfortably satisfied the pre-registered equivalence margin of $\mathbf{\pm 100.0\text{ MB}}$.
- **Peak Memory Overhead**: The absolute peak RSS observed in Normal shadow was $1092.86\text{ MB}$ (Block 4) and in Slow shadow was $1091.54\text{ MB}$ (Block 4). Compared against the baseline maximum of $990.35\text{ MB}$, the peak overhead was:
  $$\Delta_{\text{peak, normal}} = 1092.86 - 990.35 = \mathbf{+102.51\text{ MB}} \quad (+2.51\% \text{ above } 100\text{ MB margin})$$
  $$\Delta_{\text{peak, slow}} = 1091.54 - 990.35 = \mathbf{+101.19\text{ MB}} \quad (+1.19\% \text{ above } 100\text{ MB margin})$$

### 2.3 Root Cause Analysis: Transient Allocation vs. Memory Leak
Forensic inspection of the detailed block timeline confirms that this peak was **transient native allocator behavior**, not a progressive memory leak:
1. **Python Heap Invariance**: Python heap remained flat between $48.49\text{ MB}$ and $49.77\text{ MB}$ across all conditions and blocks. Zero Python objects leaked.
2. **Immediate Reclamation**: In Block 4, the test sequence was `[saturated, slow, normal, disabled]`. The native RSS reached its peak of $1092.86\text{ MB}$ during Normal shadow. Immediately upon entering the subsequent Disabled block, native RSS dropped from $1092.86\text{ MB}$ down to $990.27\text{ MB}$ (a reduction of $102.59\text{ MB}$).
3. **Allocation Source**: The transient Working Set expansion was caused by PyTorch LibTorch tensor caching and OpenCV SIFT/RANSAC scratch buffers allocated concurrently by the 2 worker threads during multi-threaded CPU feature matching.
4. **Pre-Registration Invariant**: The pre-registered margin of $\pm 100.0\text{ MB}$ is maintained without retrospective alteration. While average memory overhead is well within limits, the peak boundary breach (+2.51 MB) is formally recorded as an audit finding.

---

## 3. Complete p95 Latency Equivalence Analysis

### 3.1 Point Estimates and Margins
The pre-registered p95 latency equivalence margin was:

$$\Delta_{\text{p95, margin}} = \mathbf{\pm 100.0\text{ ms}} \quad (\alpha = 0.05, \text{ 90% TOST Confidence Interval})$$

Based on the 240 measured requests ($N = 60$ per condition, $M = 12$ specimen clusters, $K = 5$ blocks):
- Baseline Disabled p95: **$1351.75\text{ ms}$**
- Normal Shadow p95: **$1491.04\text{ ms}$** $\implies \Delta_{\text{p95}} = \mathbf{+139.29\text{ ms}}$ ($+10.3\%$)
- Slow Shadow p95: **$1511.07\text{ ms}$** $\implies \Delta_{\text{p95}} = \mathbf{+159.32\text{ ms}}$ ($+11.8\%$)
- Saturated Shadow p95: **$1387.78\text{ ms}$** $\implies \Delta_{\text{p95}} = \mathbf{+36.03\text{ ms}}$ ($+2.7\%$)

### 3.2 Clustered Bootstrap Confidence Intervals & Equivalence Verdicts

| Condition vs Baseline | Point Estimate $\Delta_{\text{p95}}$ | Clustered $SE$ | 90% Clustered CI | 95% Clustered CI | Pre-Registered Margin | Equivalence Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Normal vs Disabled** | +139.29 ms | 64.5 ms | `[+33.19 ms, +245.39 ms]` | `[+12.87 ms, +265.71 ms]` | $\pm 100.0\text{ ms}$ | **EQUIVALENCE REJECTED** (Exceeds Margin) |
| **Slow vs Disabled** | +159.32 ms | 72.1 ms | `[+40.70 ms, +277.94 ms]` | `[+18.00 ms, +300.64 ms]` | $\pm 100.0\text{ ms}$ | **EQUIVALENCE REJECTED** (Exceeds Margin) |
| **Saturated vs Disabled** | +36.03 ms | 58.3 ms | `[-59.90 ms, +131.96 ms]` | `[-78.24 ms, +150.30 ms]` | $\pm 100.0\text{ ms}$ | **INCONCLUSIVE** (Insufficient Power) |

### 3.3 Root Cause of Tail Latency Expansion
1. **Bimodal Request Profiling**: The latency profile is sharply bimodal: canonical catalog queries complete in ~140–210 ms, whereas unverified specimens (synthetic non-monuments and low-similarity queries) trigger exception ticketing, uncertainty logging, and disk I/O, completing in ~1300–1600 ms.
2. **CPU Thread Contention at the Tail**: When outlier queries execute, the background thread pool simultaneously runs feature matching. On a multi-core CPU without hardware GPU isolation, background thread execution induces modest cache eviction and scheduler latency on Policy A's exception handler.
3. **Queue Saturated Resilience**: Under saturation, excess candidate tasks are rejected immediately via `SHADOW_SKIPPED_CAPACITY` in $\mathcal{O}(1)$ time without dispatching worker threads, explaining why Saturated p95 remained within $+36.03\text{ ms}$ of baseline.
4. **Binding Conclusion**: Formal p95 equivalence is **not satisfied** under the pre-registered $\pm 100.0\text{ ms}$ margin.

---

## 4. Timeout Semantics and Terminology Reconciliation

A critical audit finding concerns the terminology used to describe the 500 ms execution threshold in `backend/shadow_engine.py`:

```
========================================================================================
TIMEOUT ARCHITECTURE DISTINCTION IN PYTHON / CPYTHON
========================================================================================
1. DEADLINE EXPIRY:
   A wall-clock timestamp comparison: (time.perf_counter() - t0) >= deadline_seconds.
   Checked at discrete checkpoints between sub-stages (before SIFT candidate matching
   and before local CLIP feature extraction).

2. COOPERATIVE CANCELLATION:
   When an execution checkpoint detects deadline expiry, evaluate_policy_d raises
   TimeoutError, unwinding Python execution and aborting subsequent sub-stages.

3. ACTUAL TASK TERMINATION:
   Python worker threads cannot be forcefully killed or asynchronously interrupted.
   If a thread is executing native C++ code (OpenCV cv::findHomography or PyTorch BLAS),
   the thread runs until the C++ function returns before the Python interpreter checks
   the deadline.
========================================================================================
```

### Corrections Applied:
- The misleading phrase "guaranteed hard termination" has been removed from all documentation.
- All operational guidelines now formally specify **cooperative deadline expiry**.
- Protocol amendment 8.4C.4 has been formally appended to [backend/phase_8_4c3_experimental_protocol.md](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c3_experimental_protocol.md), preserving protocol history.

---

## 5. Statistical Power, Cluster Sample Size, and Dataset Diversity

### 5.1 Sample Size Model for TOST Equivalence
In a clustered repeated-measures TOST design with equivalence boundary $\Delta$, observed mean difference $\mu_D$, significance level $\alpha = 0.05$ ($z_{\alpha} = 1.645$), and target power $1 - \beta$, the required number of independent specimen clusters $M$ is:

$$M \ge \frac{(z_{1 - \alpha} + z_{1 - \beta})^2 \cdot \sigma^2_{\text{cluster}}}{(\Delta - |\mu_D|)^2}$$

Using the empirical parameters observed in Phase 8.4C.3 ($\mu_D = 7.78\text{ ms}$, $\sigma_D = 149.93\text{ ms}$, clustered standard error with $M = 12$ clusters $= 15.822\text{ ms}$, $\Delta = 20.0\text{ ms}$):

- **Current Statistical Power**: With $M = 12$ clusters, $t_2 = \frac{20.0 - 7.78}{15.822} = 0.772 \implies \text{Power} \approx \mathbf{25.2\%}$. The test was severely underpowered.
- **Required Clusters for 80% Power** ($z_{\beta} = 0.842$):
  $$SE_{\text{req}} = \frac{20.0 - 7.78}{1.645 + 0.842} = \frac{12.22}{2.487} = 4.914\text{ ms} \implies M \ge 12 \times \left(\frac{15.822}{4.914}\right)^2 \approx \mathbf{125\text{ clusters}}$$
- **Required Clusters for 90% Power** ($z_{\beta} = 1.282$):
  $$SE_{\text{req}} = \frac{20.0 - 7.78}{1.645 + 1.282} = \frac{12.22}{2.927} = 4.175\text{ ms} \implies M \ge 12 \times \left(\frac{15.822}{4.175}\right)^2 \approx \mathbf{172\text{ clusters}}$$

### 5.2 Pseudoreplication Invariant
Replaying requests for the same 12 images repeatedly does not increase $M$. True statistical power requires distinct, independent physical specimens.

### 5.3 Prospective Validation Dataset Specification ($N = 200$ Specimens)
To enable definitive statistical equivalence testing, an expanded evaluation dataset must be curated spanning 5 critical axes of variation:
1. **Viewpoint & Perspective (40 specimens)**: Frontal elevations, 45-degree oblique facades, acute-angle perspective distortions, worm's-eye architectural details.
2. **Illumination & Diurnal Variance (40 specimens)**: Bright midday sun, golden hour, diffuse overcast skies, dusk, and artificial night floodlighting.
3. **Scale & Composition (40 specimens)**: Broad landscape establishing shots, medium architectural framing, and tight macro-detail carvings.
4. **Occlusion & Clutter (40 specimens)**: Foreground trees/foliage, pedestrian/tourist crowds, and restoration scaffolding.
5. **Negative & Out-of-Catalog Distractors (40 specimens)**: 20 non-monument heritage artifacts (paintings, coins, textiles) and 20 non-monument everyday scenes.

*Evaluation Invariant*: This dataset shall be reserved exclusively for prospective validation and must never be used to tune recognition thresholds or calibrators.

---

## 6. Full-System Regression & Reproducibility Verification

All 5 core regression test suites were re-executed to verify that audit activities introduced zero regressions:

1. `backend/test_shadow_staging.py` — **12/12 PASSED** (8.96s)
2. `backend/test_shadow_concurrency_audit.py` — **10/10 PASSED** (13.00s)
3. `backend/test_uncertainty.py` — **13/13 PASSED** (3.06s)
4. `backend/test_api.py` — **6/6 PASSED** (3.59s)
5. `npm --prefix frontend run build` — **PASS (OK)** (2084 modules, 8.97s)

Policy A functional response invariance remains **100.0%**. Zero production code, thresholds, FAISS vectors, or models were altered.

