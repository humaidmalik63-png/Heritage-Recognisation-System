# Phase 8.4C.3 — Statistical Equivalence and Sustained Shadow Load Protocol

**Project**: Visual Heritage Recognition and Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)  
**Workspace**: `C:\Users\humai\Heritage PJ`  
**Date**: November 7, 2026  
**Role**: Principal Performance Statistician & ML Production Reliability Engineer  
**Phase**: 8.4C.3 (Statistical Equivalence & Sustained Shadow Load Validation)  
**Status**: PRE-REGISTERED EXPERIMENTAL PROTOCOL

---

## 1. Objective and Scope

Phase 8.4C.2 established that Candidate Policy D shadow execution introduced no obvious disruption. However, a rigorous methodological audit revealed several limitations in the 8.4C.2 validation design that must be resolved to establish genuine statistical equivalence:

1. **Pseudoreplication in Statistical Testing**: In 8.4C.2, 60 requests per condition were analyzed as independent observations ($N=60$), whereas they were 5 repeated presentations of 12 distinct image specimens. Standard $t$-distribution standard errors underestimate variance under clustered repeated measures.
2. **Partial Warm-up**: The warm-up cycle in 8.4C.2 only processed 3 specimens, leaving specimens 4–12 and non-monuments cold prior to the first measured repetition block.
3. **Memory Measurement Blind Spot**: `tracemalloc` only captures Python heap allocations and is completely blind to native C/C++ memory allocated by PyTorch (LibTorch), OpenCV, and FAISS.
4. **Transient vs. Sustained Queue Saturation**: Condition D in 8.4C.2 injected a brief burst of dummy items, which were drained almost immediately, failing to evaluate true sustained capacity saturation.

This protocol pre-registers all statistical equivalence boundaries, experimental designs, and measurement procedures prior to collecting new data.

---

## 2. Pre-Registered Equivalence Margins (TOST Framework)

Under the Two One-Sided Tests (TOST) framework, equivalence between the baseline (Policy A with shadow disabled) and the treatment (Policy A with shadow enabled) within an indifference zone $[-\Delta, +\Delta]$ is declared if and only if both one-sided null hypotheses are rejected at significance level $\alpha = 0.05$:

$$H_{01}: \mu_{\text{diff}} \le -\Delta \quad \text{vs.} \quad H_{11}: \mu_{\text{diff}} > -\Delta$$
$$H_{02}: \mu_{\text{diff}} \ge +\Delta \quad \text{vs.} \quad H_{12}: \mu_{\text{diff}} < +\Delta$$

Equivalently, the two-sided $(1 - 2\alpha) = 90\%$ confidence interval for the paired difference $\mu_{\text{diff}}$ must fall entirely within $[-\Delta, +\Delta]$.

### Pre-Registered Equivalence Boundaries

| Metric | Baseline Policy A Typical | Pre-Registered Equivalence Margin ($\pm\Delta$) | Relative Margin (%) | Operational & Engineering Justification |
| :--- | :---: | :---: | :---: | :--- |
| **p50 Latency (Median)** | ~185 ms | $\mathbf{\pm 20.0\text{ ms}}$ | $\pm 10.8\%$ | Well within HTTP/TCP network jitter; imperceptible to interactive web users ($< 50\text{ ms}$ threshold). |
| **p95 Latency** | ~1390 ms | $\mathbf{\pm 100.0\text{ ms}}$ | $\pm 7.2\%$ | Bounds latency drift for complex queries traversing uncertainty exception logging pathways on CPU. |
| **p99 Latency (Tail)** | ~1580 ms | $\mathbf{\pm 150.0\text{ ms}}$ | $\pm 9.5\%$ | Prevents worst-case outlier expansion and garbage collection / OpenMP thread starvation bottlenecks. |
| **API Error Rate** | 0.0% | $\mathbf{0.0\%}$ (Exact) | $0.0\%$ | Zero tolerance. Any HTTP error introduced by shadow staging constitutes immediate failure. |
| **Process RSS (Working Set)** | ~650–850 MB | $\mathbf{\pm 100.0\text{ MB}}$ | $\pm 12.0\%$ | Bounded worker pool (2 threads) with transient images must not exceed 100 MB resident memory footprint. |
| **CPU Utilization** | ~300% (Multi-core) | $\mathbf{\pm 40.0\%}$ | $\pm 13.3\%$ | Ensures shadow workers do not starve OpenMP threads or FastAPI async event loop. |

*Pre-registration invariant*: These margins are permanently locked prior to benchmark execution.

---

## 3. Improved Experimental Design

### 3.1 Clustered Repeated-Measures Modeling
- **Unique Specimens**: 12 fixed specimens (10 canonical catalog monuments from `dataset/*/ref_01.jpg` + 2 synthetic non-monument images).
- **Repetitions (Blocks)**: 5 experimental blocks.
- **Total Requests**: 240 requests (60 per condition).
- **Effective Sample Size**:
  - Independent Specimen Clusters: $M = 12$.
  - Experimental Blocks: $K = 5$.
  - Nominal Observations: $N = 60$ per condition.
- **Clustered Bootstrap**: All confidence intervals for paired differences are estimated via **specimen-clustered bootstrap** ($B = 2,000$ resamples at the specimen cluster level). This preserves intra-specimen correlation structures and provides valid empirical coverage.

### 3.2 Counterbalanced Block Ordering
To control for temporal drift, OS scheduling jitter, and thermal throttling, the execution order across the 4 conditions is counterbalanced across the 5 blocks:
- Block 1: `[disabled, normal, slow, saturated]`
- Block 2: `[normal, saturated, disabled, slow]`
- Block 3: `[slow, disabled, saturated, normal]`
- Block 4: `[saturated, slow, normal, disabled]`
- Block 5: `[disabled, slow, normal, saturated]`

### 3.3 Full-Spectrum Warm-Up Protocol
Prior to initiating measured blocks, a complete warm-up cycle is executed:
- All 12 specimens are processed through Policy A with shadow disabled.
- All 12 specimens are processed through Policy A with shadow enabled.
- All warm-up observations are logged separately and strictly excluded from statistical reporting.

---

## 4. Sustained Queue Saturation Protocol

To evaluate Condition D under genuine sustained saturation:
1. **Background Pressure Generator**: A dedicated background thread continuously submits shadow tasks to maintain the shadow queue at exactly its configured capacity ($\text{capacity} = 10$).
2. **Worker Behavior**: The 2 worker threads actively process incoming tasks.
3. **Capacity Rejection Verification**: When Policy A requests are fired concurrently against this saturated state:
   - Each submission attempts admission.
   - Tasks arriving when queue $= 10$ are immediately rejected with `SHADOW_SKIPPED_CAPACITY` in $\mathcal{O}(1)$ time.
   - Queue depth is logged continuously over time.
   - Telemetry accurately records dropped submissions.
   - Zero unbounded queues or thread leaks occur.
4. **Cooperative Deadline Expiry**: In Condition C, tasks simulate 600 ms duration against the 500 ms deadline; workers must safely terminate expired tasks without being permanently occupied.

---

## 5. Dual Memory & Hardware Measurement

1. **Process Working Set (RSS)**:
   - Captured via Windows 64-bit API `GetProcessMemoryInfo` (`PROCESS_MEMORY_COUNTERS_EX.WorkingSetSize`).
   - Reflects true physical resident memory, including PyTorch C++ tensors, OpenCV Mats, FAISS C++ structures, and Python runtime.
2. **Python Heap Memory**:
   - Captured via `tracemalloc.get_traced_memory()`.
3. **CPU Utilization**:
   - Measured via `time.process_time() / time.perf_counter()` over the exact condition execution window.

---

## 6. Decision Rules & Staging Thresholds

The post-experiment governance decision will be made according to the following strict criteria:

1. **APPROVE NEXT CONTROLLED STAGING LEVEL**:
   - All TOST equivalence tests pass at $\alpha = 0.05$ (90% CI inside $[-\Delta, +\Delta]$ for p50, p95, and p99).
   - API error rate is 0.0%.
   - Policy A decision invariance is 100.0%.
   - Queue saturation safely drops excess tasks without blocking Policy A.
   - All 5 functional regression test suites pass.
2. **MAINTAIN CURRENT CONTROLLED STAGING**:
   - TOST p-value is inconclusive (e.g. 90% CI slightly overlaps equivalence boundary due to sampling variance or tail outliers, but mean overhead $< 15\text{ ms}$ and 0 errors).
   - No evidence of systematic degradation, but conservative observation is warranted.
3. **BLOCK FURTHER STAGING EXPANSION**:
   - Statistically significant positive degradation outside equivalence boundary ($\mu > +\Delta$).
   - Any non-zero API error rate ($> 0.0\%$).
   - Any violation of Policy A functional invariance.

---

## 7. Protocol Amendment 8.4C.4 — Timeout Semantics Clarification

**Date of Amendment**: November 7, 2026  
**Auditor**: Principal Performance Statistician & ML Reliability Auditor  
**Scope**: Clarification of Timeout Enforcement and Cancellation Semantics.

### Historical Context:
Section 4 and earlier texts used the shorthand phrase "hard 500 ms deadline". In Phase 8.4C.4 audit, this terminology was formally refined to prevent misleading operational assumptions regarding OS-level thread preemption.

### Technical Distinction:
1. **Deadline Expiry**: A time threshold comparison ($t_{\text{elapsed}} > 500\text{ ms}$) evaluated at execution checkpoints.
2. **Cooperative Cancellation**: Checkpoints evaluated between SIFT reference comparisons and before local CLIP feature extraction. If the deadline has expired, a `TimeoutError` is raised, preventing further sub-tasks from executing.
3. **Actual Task Termination**: The thread unwinds via standard Python exception handling or normal function return. **There is no guaranteed asynchronous thread killing in standard Python / CPython runtimes.** Native C++ operations (e.g., active OpenCV RANSAC or PyTorch matrix multiplications) cannot be interrupted mid-call and run to completion before the thread yields.
4. **Binding Standard**: All operational documentation and monitoring systems shall refer to this mechanism as **cooperative deadline expiry**, reserving "hard termination" exclusively for process-level isolation boundaries.


