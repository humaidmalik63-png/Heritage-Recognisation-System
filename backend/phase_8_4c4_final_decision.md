# Phase 8.4C.4 — Final Governance Decision and Staging Policy

**Project**: Visual Heritage Recognition and Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)  
**Workspace**: `C:\Users\humai\Heritage PJ`  
**Date**: November 7, 2026  
**Author**: Principal Performance Statistician & ML Reliability Auditor  
**Phase**: 8.4C.4 (Statistical Validation Gap Closure and Evidence Reconciliation)  
**Document Status**: FINAL — BINDING GOVERNANCE DETERMINATION

---

## 1. Executive Governance Determination

Under the regulatory mandate of Phase 8.4C.4, following the comprehensive audit and statistical reconciliation of the paired load experiments, the formal governance decision is:

```
========================================================================================
FINAL GOVERNANCE DETERMINATION:
>>> MAINTAIN CURRENT CONTROLLED STAGING <<<
========================================================================================
```

The system shall remain in its current controlled shadow staging configuration. No expansion of shadow traffic, worker concurrency, or queue limits is permitted at this time. Authoritative Policy A remains the sole user-facing recognition policy.

---

## 2. Comparative Evaluation of Governance Alternatives

Every available governance option was evaluated against the empirical results, pre-registered statistical criteria, and reliability constraints established across Phases 8.4C.1 through 8.4C.4.

```
+------------------------------------+------------------+-------------------------------------------------------------+
| Governance Alternative             | Decision Status  | Primary Technical & Statistical Justification               |
+------------------------------------+------------------+-------------------------------------------------------------+
| APPROVE NEXT CONTROLLED STAGING    | REJECTED         | 1. Tail latency equivalence rejected (p95 overhead > 100ms) |
| LEVEL                              |                  | 2. Peak native RSS overhead breached margin (+102.51 MB)   |
|                                    |                  | 3. Clustered TOST equivalence underpowered (Power = 25.2%)  |
+------------------------------------+------------------+-------------------------------------------------------------+
| BLOCK SHADOW STAGING               | REJECTED         | 1. Zero API errors (0.00% failure rate across 240 queries)  |
|                                    |                  | 2. 100.0% functional response invariance on Policy A        |
|                                    |                  | 3. Mean latency overhead is negligible (+7.78 ms)           |
|                                    |                  | 4. Queue shed load cleanly under saturation with zero leaks |
+------------------------------------+------------------+-------------------------------------------------------------+
| MAINTAIN CURRENT CONTROLLED        | APPROVED         | 1. Authoritative Policy A is fully protected and unaltered  |
| STAGING                            |                  | 2. Shadow mode remains strictly disabled by default         |
|                                    |                  | 3. Preserves isolated observational telemetry channel       |
|                                    |                  | 4. Enforces clear empirical prerequisites before expansion  |
+------------------------------------+------------------+-------------------------------------------------------------+
```

### 2.1 Why "APPROVE NEXT CONTROLLED STAGING LEVEL" Was Rejected
Expanding staging traffic (e.g., increasing worker count, increasing queue depth, or routing live production traffic to shadow evaluation) was **formally rejected** on three distinct scientific and operational grounds:

1. **Failure of p95 Tail Latency Equivalence**:
   - The pre-registered p95 equivalence margin was $\Delta_{\text{p95, margin}} = \mathbf{\pm 100.0\text{ ms}}$.
   - Normal shadow vs. Baseline Disabled exhibited a p95 increase of $\mathbf{+139.29\text{ ms}}$ ($+10.3\%$), with a 90% clustered bootstrap confidence interval of `[+33.19 ms, +245.39 ms]`.
   - Slow shadow vs. Baseline Disabled exhibited a p95 increase of $\mathbf{+159.32\text{ ms}}$ ($+11.8\%$), with a 90% clustered bootstrap confidence interval of `[+40.70 ms, +277.94 ms]`.
   - Because the upper bounds of both confidence intervals ($+245.39\text{ ms}$ and $+277.94\text{ ms}$) substantially exceed the $+100.0\text{ ms}$ threshold, formal p95 equivalence is **statistically rejected**. Advancing staging levels under an unverified tail latency profile risks degrading user response times during edge-case query processing.

2. **Peak Resident Memory Boundary Breach**:
   - The pre-registered resident memory margin was $\mathbf{\pm 100.0\text{ MB}}$.
   - While the mean RSS increase was well within tolerance ($+23.32\text{ MB}$ normal, $+56.23\text{ MB}$ slow), peak native RSS reached $1092.86\text{ MB}$ during Normal shadow and $1091.54\text{ MB}$ during Slow shadow, relative to a baseline maximum of $990.35\text{ MB}$.
   - This represents an overhead of $\mathbf{+102.51\text{ MB}}$ ($+2.51\text{ MB}$ over margin) and $\mathbf{+101.19\text{ MB}}$ ($+1.19\text{ MB}$ over margin) respectively.
   - Although root-cause analysis verified this allocation to be transient LibTorch/OpenCV scratch buffers rather than a progressive leak, pre-registered margins cannot be retroactively relaxed to justify staging expansion.

3. **Insufficient Statistical Power of Current Sample**:
   - As demonstrated in `phase_8_4c4_power_and_sample_size.json`, testing equivalence at $\Delta = \pm 20.0\text{ ms}$ with $M = 12$ specimen clusters achieves only $\mathbf{25.2\%}$ statistical power ($SE = 15.822\text{ ms}$).
   - Approving higher traffic tiers based on an underpowered study violates statistical validation standards.

### 2.2 Why "BLOCK SHADOW STAGING" Was Rejected
Completely terminating or blocking shadow staging was **formally rejected** because the implementation demonstrated complete architectural safety and zero user impact:

1. **Absolute Functional Invariance (100.0%)**:
   - Across all 240 measured requests in Phase 8.4C.3 and all regression suites in Phases 8.4C.1, 8.4C.2, and 8.4C.4, Policy A produced identical decision states, top-1 monument predictions, calibrated confidence scores, and bounding boxes.
   - Candidate Policy D code has zero write access to Policy A response structures.

2. **Zero Production Failures**:
   - The authoritative API error rate was exactly $\mathbf{0.00\%}$ across all test blocks, including under forced saturation.

3. **Controlled Mean Latency Overhead**:
   - The overall paired mean latency difference was $+7.78\text{ ms}$ ($+1.8\%$), well within the practical operational budget of the system.

4. **Graceful Saturation Shedding**:
   - When the queue capacity (10 tasks) was reached, excess tasks were shed in $\mathcal{O}(1)$ time with zero worker thread starvation, zero lock contention, and zero unbounded memory growth.

5. **No Memory Leaks**:
   - Python heap remained perfectly stable at $\approx 49\text{ MB}$, and native Working Set dropped back to baseline ($990.27\text{ MB}$) immediately upon ceasing shadow load.

### 2.3 Why "MAINTAIN CURRENT CONTROLLED STAGING" Was Selected
Maintaining the existing controlled staging environment provides the optimal balance of production safety and experimental visibility:
- Authoritative recognition operates with complete isolation.
- Shadow execution remains disabled by default in production configurations (`ENABLE_SHADOW_CANDIDATE_POLICY_D=false`).
- Shadow telemetry collection is available when explicitly activated for controlled observational validation.
- Clear, quantifiable criteria are established for future progression.

---

## 3. Strict Production Invariants in Force

The following invariants are binding and remain enforced across the platform:

```
========================================================================================
BINDING PRODUCTION INVARIANTS (PHASE 8.4C.4)
========================================================================================
1. AUTHORITATIVE POLICY:
   Policy A remains the sole authoritative, user-facing recognition policy.
   Policy D is strictly observational and can never modify Policy A outputs.

2. DEFAULT DISABLED:
   ENABLE_SHADOW_CANDIDATE_POLICY_D = false
   Shadow processing must remain disabled by default in all deployments.

3. CONCURRENCY LIMITS:
   Worker pool concurrency = 2 threads.
   Admission queue capacity = 10 tasks.
   Worker pool thread count and queue depth shall NOT be increased.

4. TIMEOUT SEMANTICS:
   500 ms cooperative deadline check. Python threads cannot be forcefully killed;
   tasks expire at cooperative checkpoints between processing stages.

5. ZERO ALGORITHMIC OR DATA CHANGES:
   - Zero changes to Policy A recognition thresholds.
   - Zero changes to calibration parameters or temperature scalers.
   - Zero changes to FAISS index (frozen at 210 vectors, 10 catalog monuments).
   - Zero Gemini overrides of recognition decisions.
   - Zero Git commits or pushes to GitHub.
========================================================================================
```

---

## 4. Mandatory Prerequisites for Future Staging Expansion

Before any request to approve the next controlled staging level (such as increasing worker count, deepening the queue, or enabling shadow execution on live traffic) may be submitted, the following three prerequisites must be fully satisfied:

### Prerequisite 1: Prospective Clustered Validation Dataset ($M \ge 150$ Clusters)
- **Deficiency Addressed**: Resolves the low statistical power ($25.2\%$) of the 12-specimen dataset.
- **Specification**: Curate an independent prospective dataset comprising at least $150$ distinct physical specimen clusters ($N \ge 200$ images total):
  - $\ge 120$ catalog specimens across 10 canonical monuments.
  - $\ge 40$ out-of-catalog heritage distractors (unrelated archaeological and museum artifacts).
  - $\ge 40$ non-monument everyday images (urban, nature, vehicular).
- **Diversity Coverage**: Must span all 5 pre-registered axes of variation (viewpoint, illumination, scale, occlusion, clutter).
- **Statistical Target**: Achieve $\ge 85\%$ statistical power for TOST equivalence at $\Delta = \pm 20.0\text{ ms}$ ($\alpha = 0.05$).

### Prerequisite 2: Tail Latency Mitigation & Thread Priority Containment
- **Deficiency Addressed**: Resolves the tail latency inflation at p95 ($+139.29\text{ ms}$ normal, $+159.32\text{ ms}$ slow).
- **Engineering Action**:
  - Implement CPU thread affinity or set shadow worker thread execution priority to `THREAD_PRIORITY_BELOW_NORMAL` / OS nice level, preventing shadow feature matching from starving Policy A's exception handler.
  - Re-run paired equivalence validation to prove $\Delta_{\text{p95}} \le \pm 100.0\text{ ms}$ with 90% clustered bootstrap CI contained inside the margin.

### Prerequisite 3: Peak Working Set Buffer Containment
- **Deficiency Addressed**: Resolves the $+102.51\text{ MB}$ peak Working Set overhead.
- **Engineering Action**:
  - Configure PyTorch LibTorch allocator settings (`PYTORCH_CUDA_ALLOC_CONF` or CPU thread cache recycling) and OpenCV multi-threading buffer reuse to cap concurrent working buffer spikes below $\pm 80.0\text{ ms}$ / $\text{MB}$.
  - Verify that peak native RSS during shadow execution does not exceed baseline maximum by more than $\mathbf{\pm 100.0\text{ MB}}$.

---

## 5. Artifact & Deliverable Traceability Index

All Phase 8.4C.4 deliverables, analytical computations, and protocol updates are preserved in the platform workspace:

1. **Validation Gap Audit Report**:
   - File: [backend/phase_8_4c4_validation_gap_audit.md](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c4_validation_gap_audit.md)
   - Scope: Complete analysis of memory observations, p95 bootstrap intervals, timeout terminology audit, power modeling, and full-system regression results.

2. **p95 Latency Equivalence Dataset**:
   - File: [backend/phase_8_4c4_p95_equivalence.json](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c4_p95_equivalence.json)
   - Scope: Condition-level p95 percentiles, paired differences, clustered standard errors, 90% and 95% bootstrap confidence intervals, and formal equivalence rejection verdicts.

3. **Memory Measurement Reconciliation Dataset**:
   - File: [backend/phase_8_4c4_memory_reconciliation.json](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c4_memory_reconciliation.json)
   - Scope: Mean and peak native RSS (Working Set) vs. Python heap (`tracemalloc`), overhead calculations, block timeline tracking, and transient allocation attribution.

4. **Power and Sample Size Projections**:
   - File: [backend/phase_8_4c4_power_and_sample_size.json](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c4_power_and_sample_size.json)
   - Scope: Mathematical power curves for clustered TOST, required sample size derivations for 80% and 90% power, and prospective 200-specimen dataset specification.

5. **Final Governance Decision Document**:
   - File: [backend/phase_8_4c4_final_decision.md](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c4_final_decision.md)
   - Scope: This binding governance decision document.

6. **Historical Protocol & Report Reconciliation**:
   - [backend/phase_8_4c3_experimental_protocol.md](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c3_experimental_protocol.md): Appended Protocol Amendment 8.4C.4 clarifying timeout semantics.
   - [backend/phase_8_4c3_final_report.md](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c3_final_report.md): Corrected timeout terminology from "hard deadline" to "cooperative deadline".
   - [backend/phase_8_4c3_sustained_load_results.json](file:///C:/Users/humai/Heritage%20PJ/backend/phase_8_4c3_sustained_load_results.json): Embedded structured `timeout_semantics` metadata.

---

## 6. Verification & Sign-Off

The entire audit, reconciliation, and governance review was conducted in strict adherence to scientific reproducibility standards. All raw observation data from Phase 8.4C.3 remain untouched. Full regression test suites were executed with 100% pass rates, and Policy A response invariance is confirmed at 100.0%.

**Governance Determination**: **`MAINTAIN CURRENT CONTROLLED STAGING`**  
**Authorized By**: Principal Performance Statistician & ML Reliability Auditor  
**Date**: November 7, 2026

