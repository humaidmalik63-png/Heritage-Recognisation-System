# Phase 8.4C — Controlled Shadow Staging Rollout Guide
**Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)**  
*Role: Senior ML Systems Engineer & Production Reliability Engineer*  
*Target Environment: Hybrid Production Backend (FastAPI)*

---

## 1. Overview & Operational Principles

This document provides step-by-step procedures, runbooks, and promotion gates for operating **Candidate Policy D in Shadow Mode**. 

### Core Safeguards:
- **Zero Impact on User Experience**: Policy A remains the sole authoritative engine.
- **Fail-Safe Defaults**: Shadow mode is disabled out-of-the-box (`ENABLE_SHADOW_CANDIDATE_POLICY_D=false`).
- **Instant Kill Switch**: Deactivates instantly via environment variable or in-memory API without service restart.
- **Resource Quarantine**: Maximum 2 workers, maximum queue depth of 10, 500 ms hard timeout budget.

---

## 2. Multi-Stage Rollout Plan

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Stage 0     │       │     Stage 1     │       │     Stage 2     │       │     Stage 3     │
│ Pre-Flight Dry  │ ────► │  Canary Shadow  │ ────► │  Staging Soak   │ ────► │ Evaluation Gate │
│ (Disabled State)│       │ (Single Worker) │       │ (Full Concurr.) │       │  (Readiness)    │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### Stage 0: Pre-Flight Verification (Baseline)
- **Objective**: Confirm that the platform functions identically with the shadow engine compiled in disabled mode.
- **Actions**:
  1. Verify `ENABLE_SHADOW_CANDIDATE_POLICY_D` is unset or `false`.
  2. Run the test suite:
     ```bash
     .\.venv\Scripts\python.exe backend/test_shadow_staging.py
     ```
  3. Confirm `backend/phase_8_4c_shadow_test_report.json` indicates all 12 tests passed.
  4. Ensure `backend/test_api.py` and `backend/test_uncertainty.py` pass cleanly.

### Stage 1: Canary Shadow Activation
- **Objective**: Verify that shadow tasks are successfully scheduled and recorded to disk without latency regression.
- **Actions**:
  1. Set the environment variable:
     ```powershell
     $env:ENABLE_SHADOW_CANDIDATE_POLICY_D="true"
     ```
  2. Launch the backend service in staging:
     ```powershell
     .\.venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8000
     ```
  3. Send 5 test verification requests (e.g. Taj Mahal, Charminar, Non-monument).
  4. Verify that `backend/telemetry/shadow_staging_audit.jsonl` receives structured comparison entries.
  5. Check that API latency remains $< 350$ ms on CPU.

### Stage 2: Staging Soak & Concurrency Stress Test
- **Objective**: Verify that admission control, queue bounding, and timeouts operate safely under load.
- **Actions**:
  1. Execute automated concurrent requests (e.g. 5 concurrent clients sending 20 images).
  2. Monitor `backend/telemetry/shadow_staging_audit.jsonl` for:
     - `SHADOW_TIMEOUT` count ($< 2\%$ of requests).
     - `SHADOW_SKIPPED_CAPACITY` count (under extreme bursts, confirms graceful task dropping).
     - `SHADOW_ERROR` count ($0$ unhandled exceptions).
  3. Confirm zero memory leak or worker thread hang.

### Stage 3: Prospective Observation & Divergence Logging
- **Objective**: Collect observational telemetry across prospective specimen queries to evaluate real-world Policy D performance.
- **Actions**:
  1. Let shadow mode run for a designated observation period ($\ge 250$ real queries).
  2. Periodically parse `backend/telemetry/shadow_staging_audit.jsonl` using the telemetry inspection runbook.
  3. Tally candidate upgrades, candidate downgrades, and any false acceptance alerts.

---

## 3. Operational Runbooks

### 3.1 Enabling & Disabling the Kill Switch

#### Method A: Environment Variable (Recommended for Deployment)
To enable shadow evaluation:
```powershell
# Windows PowerShell
$env:ENABLE_SHADOW_CANDIDATE_POLICY_D="true"
```
```bash
# Linux / macOS Bash
export ENABLE_SHADOW_CANDIDATE_POLICY_D=true
```

To immediately disable shadow evaluation:
```powershell
# Windows PowerShell
$env:ENABLE_SHADOW_CANDIDATE_POLICY_D="false"
```
```bash
# Linux / macOS Bash
export ENABLE_SHADOW_CANDIDATE_POLICY_D=false
```

#### Method B: In-Memory Dynamic Runtime Override
For instant zero-downtime control inside scripts or admin consoles:
```python
from backend.shadow_engine import shadow_engine

# Instant shutdown of shadow evaluations (drops all subsequent incoming tasks)
shadow_engine.set_runtime_enabled(False)

# Re-enable shadow evaluations
shadow_engine.set_runtime_enabled(True)
```

---

### 3.2 Telemetry Audit Inspection Runbook

Telemetry records are appended as valid JSON objects (one per line) to:
`backend/telemetry/shadow_staging_audit.jsonl`

#### Inspecting Divergence Distribution via CLI:
```powershell
.\.venv\Scripts\python.exe -c "
import json
from collections import Counter
from pathlib import Path

log_file = Path('backend/telemetry/shadow_staging_audit.jsonl')
if not log_file.exists():
    print('No telemetry records found yet.')
    exit(0)

events = []
with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            events.append(json.loads(line))

print(f'Total shadow records: {len(events)}')
types = Counter(e.get('event_type') for e in events)
print('Event types:', dict(types))

completed = [e for e in events if e.get('event_type') == 'SHADOW_EVALUATION_COMPLETED']
cats = Counter(e.get('divergence_category') for e in completed)
print('Divergence categories:', dict(cats))
"
```

#### Divergence Taxonomy Definitions:
- `AGREEMENT`: Both Policy A and Policy D output `VERIFIED_MATCH`.
- `POLICY_D_UPGRADE`: Policy A was `UNCERTAIN_MATCH` or `REVIEW_REQUIRED`, but Policy D corroboration safely promoted the specimen to `VERIFIED_MATCH`.
- `POLICY_D_DOWNGRADE`: Policy A was `VERIFIED_MATCH`, but Policy D did not verify.
- `UNVERIFIED_AGREEMENT`: Both policies classified the specimen as uncertain or review required.
- `OUT_OF_CATALOG_NEGATIVE_REJECTION`: Both policies agreed the specimen is a non-monument or unindexed heritage site.

---

### 3.3 Incident Response & Alarm Thresholds

| Alert Condition | Threshold | Root Cause Diagnosis | Action |
| :--- | :--- | :--- | :--- |
| **API Latency Spike** | Endpoint latency $> 600$ ms | CPU contention on worker threads | **Trigger Kill Switch immediately**: `set_runtime_enabled(False)` |
| **High Timeout Rate** | `SHADOW_TIMEOUT` $> 5\%$ of tasks | Reference image loading or FLANN match stall | Check CPU core load; decrease image resolution limit to 640px |
| **Queue Saturation** | `SHADOW_SKIPPED_CAPACITY` $> 10\%$ | Influx rate exceeds worker throughput (2 threads) | Normal backpressure; if sustained, evaluate dedicated worker process |
| **Shadow Exceptions** | `SHADOW_ERROR` $> 0.5\%$ of tasks | Corrupted image array, OpenCV Homography degeneracy | Inspect `error_message` in audit log; errors are fully isolated |

---

## 4. Promotion Criteria (Shadow to Live Cutover)

Before Candidate Policy D can be considered for promotion to authoritative production in Phase 9.0, **all** of the following quantitative criteria must be satisfied during shadow staging:

1. **Zero False Acceptances ($\text{FAR} = 0.0\%$)**:
   - Zero non-monument or out-of-catalog heritage specimens verified by Policy D across $\ge 250$ prospective specimens.
2. **Strict Superiority or Parity in Verification Recall**:
   - $\ge 85\%$ of Policy D upgrades confirmed to be ground-truth catalog monuments.
3. **P99 Execution Budget Compliance**:
   - Shadow Policy D execution duration $\le 450$ ms at 99th percentile.
4. **Reliability & Stability**:
   - Zero host process crashes, memory leaks, or unhandled exceptions across $\ge 72$ hours of staging operation.
5. **Stakeholder & Curatorial Alignment**:
   - Audit sign-off by cultural heritage curators confirming upgraded matches exhibit verified architectural features.

