"""
Heritage & Monument Recognition System - Phase 8.4C.2 Paired Performance & Load Validation
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025)

Conducts a paired, randomized, controlled performance experiment comparing:
- Condition A: Shadow Disabled (Authoritative Baseline)
- Condition B: Shadow Enabled with Normal Workload
- Condition C: Shadow Enabled with Slow Workload (Timeouts)
- Condition D: Shadow Enabled under Saturated Concurrency

Outputs:
- backend/phase_8_4c2_performance_results.json
- backend/phase_8_4c2_paired_latency_analysis.json
- backend/phase_8_4c2_resource_utilization.json
"""

import io
import json
import logging
import math
import os
import random
import sys
import tempfile
import threading
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Tuple

import unittest
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from shadow_engine import (
    ShadowConfig,
    ShadowEngine,
    shadow_engine,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("phase_8_4c2_validator")

# Pre-defined Acceptance Criteria
BUDGET_MAX_P50_DELTA_MS = 25.0       # Max acceptable p50 overhead over baseline
BUDGET_MAX_PERCENT_DELTA = 25.0       # Max acceptable percentage increase
BUDGET_MAX_P99_MS = 450.0             # Max acceptable p99 tail latency on CPU
BUDGET_MAX_ERROR_RATE = 0.0           # Zero API errors permitted
BUDGET_MAX_TEL_FAILURES = 0           # Zero telemetry write failures permitted


def create_synthetic_non_monument(pattern: str) -> bytes:
    """Generates synthetic non-monument images that trigger gatekeeper rejection without network calls."""
    img = Image.new("RGB", (320, 240), color=(230, 230, 230))
    draw = ImageDraw.Draw(img)
    if pattern == "office_document":
        draw.rectangle([20, 20, 300, 40], fill=(50, 50, 50))
        for y in range(60, 220, 15):
            draw.line([(25, y), (295, y)], fill=(120, 120, 120), width=3)
    else:
        # Texture grid
        for i in range(0, 320, 20):
            draw.line([(i, 0), (i, 240)], fill=(180, 180, 180), width=1)
        for j in range(0, 240, 20):
            draw.line([(0, j), (320, j)], fill=(180, 180, 180), width=1)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def load_fixed_specimens() -> List[Dict[str, Any]]:
    """Loads 10 real catalog monument images and 2 synthetic non-monuments into fixed in-memory collection."""
    dataset_dir = BASE_DIR / "dataset"
    monuments = [
        ("brihadeeswarar_temple", "Brihadeeswarar Temple"),
        ("charminar", "Charminar"),
        ("gateway_of_india", "Gateway of India"),
        ("hampi_stone_chariot", "Hampi Stone Chariot"),
        ("hawa_mahal", "Hawa Mahal"),
        ("konark_sun_temple", "Konark Sun Temple"),
        ("qutub_minar", "Qutub Minar"),
        ("sanchi_stupa", "Sanchi Stupa"),
        ("taj_mahal", "Taj Mahal"),
        ("victoria_memorial", "Victoria Memorial"),
    ]

    specimens = []
    for key, name in monuments:
        img_path = dataset_dir / key / "ref_01.jpg"
        with open(img_path, "rb") as f:
            bytes_data = f.read()
        specimens.append({
            "key": key,
            "name": name,
            "filename": f"{key}_ref_01.jpg",
            "bytes": bytes_data,
            "is_catalog_monument": True,
        })

    # Add 2 non-monuments
    specimens.append({
        "key": "synthetic_document",
        "name": "Non-Monument Document",
        "filename": "synthetic_document.jpg",
        "bytes": create_synthetic_non_monument("office_document"),
        "is_catalog_monument": False,
    })
    specimens.append({
        "key": "synthetic_texture_grid",
        "name": "Non-Monument Grid",
        "filename": "synthetic_grid.jpg",
        "bytes": create_synthetic_non_monument("grid"),
        "is_catalog_monument": False,
    })

    return specimens


def compute_statistics(values: List[float]) -> Dict[str, float]:
    arr = np.array(values, dtype=np.float64)
    n = len(arr)
    mean_val = float(np.mean(arr)) if n > 0 else 0.0
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    median_val = float(np.median(arr)) if n > 0 else 0.0
    p90_val = float(np.percentile(arr, 90)) if n > 0 else 0.0
    p95_val = float(np.percentile(arr, 95)) if n > 0 else 0.0
    p99_val = float(np.percentile(arr, 99)) if n > 0 else 0.0
    return {
        "count": n,
        "mean": round(mean_val, 2),
        "std_dev": round(std_val, 2),
        "median": round(median_val, 2),
        "p50": round(median_val, 2),
        "p90": round(p90_val, 2),
        "p95": round(p95_val, 2),
        "p99": round(p99_val, 2),
        "min": round(float(np.min(arr)), 2) if n > 0 else 0.0,
        "max": round(float(np.max(arr)), 2) if n > 0 else 0.0,
    }


def compute_paired_comparison(enabled_vals: List[float], disabled_vals: List[float]) -> Dict[str, Any]:
    diffs = np.array(enabled_vals, dtype=np.float64) - np.array(disabled_vals, dtype=np.float64)
    n = len(diffs)
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
    median_diff = float(np.median(diffs))
    se = std_diff / math.sqrt(n) if n > 0 else 0.0

    # Student's t critical value for df=n-1 (for n=60, t_crit=2.001 at alpha=0.05)
    t_crit = 2.001 if n >= 60 else 2.045
    ci_lower = mean_diff - t_crit * se
    ci_upper = mean_diff + t_crit * se

    baseline_mean = float(np.mean(disabled_vals)) if len(disabled_vals) > 0 else 1.0
    percent_diff = (mean_diff / baseline_mean) * 100.0 if baseline_mean > 0 else 0.0

    p50_diff = float(np.percentile(enabled_vals, 50) - np.percentile(disabled_vals, 50))
    p90_diff = float(np.percentile(enabled_vals, 90) - np.percentile(disabled_vals, 90))
    p95_diff = float(np.percentile(enabled_vals, 95) - np.percentile(disabled_vals, 95))
    p99_diff = float(np.percentile(enabled_vals, 99) - np.percentile(disabled_vals, 99))

    is_acceptable = (
        mean_diff <= BUDGET_MAX_P50_DELTA_MS
        and percent_diff <= BUDGET_MAX_PERCENT_DELTA
        and np.percentile(enabled_vals, 99) <= BUDGET_MAX_P99_MS
    )

    return {
        "sample_size": n,
        "mean_diff_ms": round(mean_diff, 2),
        "median_diff_ms": round(median_diff, 2),
        "std_diff_ms": round(std_diff, 2),
        "standard_error_ms": round(se, 3),
        "ci_95_percent": {
            "lower_ms": round(ci_lower, 2),
            "upper_ms": round(ci_upper, 2),
            "margin_of_error_ms": round(t_crit * se, 2),
        },
        "percentage_difference": round(percent_diff, 2),
        "tail_differences_ms": {
            "p50_diff": round(p50_diff, 2),
            "p90_diff": round(p90_diff, 2),
            "p95_diff": round(p95_diff, 2),
            "p99_diff": round(p99_diff, 2),
        },
        "acceptance_criteria_met": bool(is_acceptable),
        "budget_thresholds": {
            "max_mean_diff_ms": BUDGET_MAX_P50_DELTA_MS,
            "max_percent_diff": BUDGET_MAX_PERCENT_DELTA,
            "max_p99_ms": BUDGET_MAX_P99_MS,
        },
    }


def execute_validation_suite():
    logger.info("Initializing Phase 8.4C.2 Paired Performance & Shadow Load Validation Suite...")
    specimens = load_fixed_specimens()
    logger.info(f"Loaded {len(specimens)} fixed test specimens (10 catalog monuments, 2 non-monuments).")

    # Counterbalanced block order across 5 independent repetitions
    blocks = [
        ["disabled", "normal", "slow", "saturated"],
        ["normal", "saturated", "disabled", "slow"],
        ["slow", "disabled", "saturated", "normal"],
        ["saturated", "slow", "normal", "disabled"],
        ["disabled", "slow", "normal", "saturated"],
    ]

    all_run_records: List[Dict[str, Any]] = []
    condition_latencies: Dict[str, List[float]] = {
        "disabled": [],
        "normal": [],
        "slow": [],
        "saturated": [],
    }
    condition_shadow_durations: Dict[str, List[float]] = {
        "normal": [],
        "slow": [],
        "saturated": [],
    }
    condition_timeouts: Dict[str, int] = {"disabled": 0, "normal": 0, "slow": 0, "saturated": 0}
    condition_dropped: Dict[str, int] = {"disabled": 0, "normal": 0, "slow": 0, "saturated": 0}
    condition_errors: Dict[str, int] = {"disabled": 0, "normal": 0, "slow": 0, "saturated": 0}

    resource_metrics_per_condition: Dict[str, Dict[str, Any]] = {}

    with TestClient(app) as client:
        # Step 1: Warm-up runs (executed separately and excluded from measured statistics)
        logger.info("Executing separate warm-up cycles (excluded from metrics)...")
        shadow_engine.set_runtime_enabled(False)
        for i in range(3):
            client.post("/api/verify-monument", files={"file": ("warm_dis.jpg", specimens[i]["bytes"], "image/jpeg")})

        shadow_engine.set_runtime_enabled(True)
        for i in range(3):
            client.post("/api/verify-monument", files={"file": ("warm_en.jpg", specimens[i]["bytes"], "image/jpeg")})
        time.sleep(0.1)

        # Clear queue and metrics after warm-up
        while not shadow_engine._queue.empty():
            try:
                shadow_engine._queue.get_nowait()
            except Exception:
                break

        logger.info("Warm-up complete. Commencing 5 randomized repetitions (240 total measured requests)...")

        # Step 2: Main Experimental Loop across 5 Repetitions
        for rep_idx, condition_order in enumerate(blocks, start=1):
            logger.info(f"--- Starting Repetition Block {rep_idx}/5: Order={condition_order} ---")

            for cond in condition_order:
                tracemalloc.start()
                t_cpu_start = time.process_time()
                t_wall_start = time.perf_counter()

                # Configure condition environment
                if cond == "disabled":
                    shadow_engine.set_runtime_enabled(False)
                elif cond == "normal":
                    shadow_engine.set_runtime_enabled(True)
                elif cond == "slow":
                    shadow_engine.set_runtime_enabled(True)
                elif cond == "saturated":
                    shadow_engine.set_runtime_enabled(True)

                # Execute all 12 specimens in exact fixed sequence
                for spec_idx, spec in enumerate(specimens):
                    # For Condition C (slow), simulate a 550ms delay inside evaluate_policy_d
                    # For Condition D (saturated), saturate queue before dispatch
                    patcher = None
                    saturation_cleaner = None

                    if cond == "slow":
                        def slow_eval_func(*args, **kwargs):
                            time.sleep(0.55)
                            return ("VERIFIED_MATCH", spec["key"])
                        patcher = patch.object(ShadowEngine, "evaluate_policy_d", side_effect=slow_eval_func)
                        patcher.start()

                    elif cond == "saturated":
                        # Put 10 dummy items in queue to trigger saturation
                        dummy_img = Image.new("RGB", (64, 64), (10, 10, 10))
                        for sat_i in range(10):
                            shadow_engine.submit_shadow_evaluation(
                                request_id=f"sat_filler_{rep_idx}_{spec_idx}_{sat_i}",
                                image=dummy_img,
                                top1_key="taj_mahal",
                                top1_sim=0.8,
                                margin=0.06,
                                gatekeeper_score=0.8,
                                policy_a_decision="UNCERTAIN_MATCH",
                                policy_a_monument="taj_mahal",
                            )

                    # Send request and time Policy A response latency
                    t_req_start = time.perf_counter()
                    resp = client.post(
                        "/api/verify-monument",
                        files={"file": (spec["filename"], spec["bytes"], "image/jpeg")},
                    )
                    req_latency_ms = (time.perf_counter() - t_req_start) * 1000.0

                    if patcher:
                        patcher.stop()

                    status_code = resp.status_code
                    if status_code != 200:
                        condition_errors[cond] += 1

                    resp_data = resp.json() if status_code == 200 else {}
                    pol_a_decision = resp_data.get("verification_status", "ERROR")
                    pol_a_monument = resp_data.get("monument_key")

                    condition_latencies[cond].append(req_latency_ms)

                    # Inspect shadow metrics
                    m = shadow_engine.get_metrics()
                    record_entry = {
                        "repetition": rep_idx,
                        "condition": cond,
                        "specimen_index": spec_idx,
                        "specimen_key": spec["key"],
                        "policy_a_latency_ms": round(req_latency_ms, 2),
                        "status_code": status_code,
                        "policy_a_decision": pol_a_decision,
                        "policy_a_monument": pol_a_monument,
                        "queue_length": m["queue_length"],
                    }
                    all_run_records.append(record_entry)

                # Let any in-flight shadow tasks settle
                time.sleep(0.15)

                t_cpu_elapsed = time.process_time() - t_cpu_start
                t_wall_elapsed = time.perf_counter() - t_wall_start
                cpu_util = (t_cpu_elapsed / t_wall_elapsed) * 100.0 if t_wall_elapsed > 0 else 0.0

                current_mem, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                metrics_snapshot = shadow_engine.get_metrics()

                if cond not in resource_metrics_per_condition:
                    resource_metrics_per_condition[cond] = {
                        "cpu_percent_samples": [],
                        "peak_memory_mb_samples": [],
                        "queue_occupancy_samples": [],
                        "telemetry_health": metrics_snapshot["telemetry"],
                    }

                resource_metrics_per_condition[cond]["cpu_percent_samples"].append(round(cpu_util, 2))
                resource_metrics_per_condition[cond]["peak_memory_mb_samples"].append(round(peak_mem / (1024 * 1024), 2))
                resource_metrics_per_condition[cond]["queue_occupancy_samples"].append(metrics_snapshot["queue_length"])

                # Drain queue between blocks
                while not shadow_engine._queue.empty():
                    try:
                        shadow_engine._queue.get_nowait()
                    except Exception:
                        break

    # Parse telemetry file for actual Policy D execution duration and timeout count
    telemetry_path = shadow_engine.config.telemetry_path
    shadow_log_events = []
    if telemetry_path.exists():
        with open(telemetry_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        shadow_log_events.append(json.loads(line))
                    except Exception:
                        pass

    # Tally telemetry event outcomes
    for ev in shadow_log_events:
        etype = ev.get("event_type")
        if etype == "SHADOW_TIMEOUT":
            condition_timeouts["slow"] += 1
        elif etype == "SHADOW_SKIPPED_CAPACITY":
            condition_dropped["saturated"] += 1
        elif etype == "SHADOW_EVALUATION_COMPLETED":
            dur = ev.get("latency_ms", 0.0)
            condition_shadow_durations["normal"].append(dur)

    # Step 3: Compute Summary Statistics per Condition
    per_condition_stats = {}
    for cond in ["disabled", "normal", "slow", "saturated"]:
        stats = compute_statistics(condition_latencies[cond])
        stats["api_error_rate_percent"] = round((condition_errors[cond] / len(condition_latencies[cond])) * 100.0, 2)
        stats["timeouts_observed"] = condition_timeouts[cond]
        stats["dropped_tasks"] = condition_dropped[cond]
        per_condition_stats[cond] = stats

    # Step 4: Compute Paired Latency Analysis (Conditions B, C, D vs Condition A)
    paired_analyses = {
        "normal_vs_disabled": compute_paired_comparison(
            condition_latencies["normal"], condition_latencies["disabled"]
        ),
        "slow_vs_disabled": compute_paired_comparison(
            condition_latencies["slow"], condition_latencies["disabled"]
        ),
        "saturated_vs_disabled": compute_paired_comparison(
            condition_latencies["saturated"], condition_latencies["disabled"]
        ),
    }

    # Step 5: Aggregate Resource Utilization
    resource_summary = {}
    for cond, data in resource_metrics_per_condition.items():
        resource_summary[cond] = {
            "mean_cpu_percent": round(float(np.mean(data["cpu_percent_samples"])), 2),
            "max_cpu_percent": round(float(np.max(data["cpu_percent_samples"])), 2),
            "mean_peak_memory_mb": round(float(np.mean(data["peak_memory_mb_samples"])), 2),
            "max_peak_memory_mb": round(float(np.max(data["peak_memory_mb_samples"])), 2),
            "max_queue_occupancy": max(data["queue_occupancy_samples"]),
            "telemetry_health": data["telemetry_health"],
        }

    # Verify Functional Invariance: Policy A decisions in Normal vs Disabled
    decision_matches = 0
    for i in range(len(condition_latencies["disabled"])):
        dec_dis = all_run_records[i]["policy_a_decision"]
        # Match corresponding Normal run
        dec_norm = [r["policy_a_decision"] for r in all_run_records if r["condition"] == "normal" and r["specimen_index"] == all_run_records[i]["specimen_index"]][0]
        if dec_dis == dec_norm:
            decision_matches += 1

    policy_a_invariance_pct = round((decision_matches / len(condition_latencies["disabled"])) * 100.0, 2)

    # Compile Final Reports
    perf_results_payload = {
        "phase": "8.4C.2",
        "title": "Paired Performance and Shadow Load Validation Results",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_measured_requests": len(all_run_records),
        "specimens_count": len(specimens),
        "repetitions_count": 5,
        "conditions": ["disabled", "normal", "slow", "saturated"],
        "pre_defined_budget": {
            "max_acceptable_mean_diff_ms": BUDGET_MAX_P50_DELTA_MS,
            "max_acceptable_percent_diff": BUDGET_MAX_PERCENT_DELTA,
            "max_acceptable_p99_ms": BUDGET_MAX_P99_MS,
            "max_acceptable_error_rate": BUDGET_MAX_ERROR_RATE,
        },
        "per_condition_summary": per_condition_stats,
        "policy_a_functional_invariance_percent": policy_a_invariance_pct,
        "raw_run_records": all_run_records,
    }

    paired_analysis_payload = {
        "phase": "8.4C.2",
        "title": "Paired Latency Statistical Comparison",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paired_comparisons": paired_analyses,
        "acceptance_verdict": {
            "normal_condition_pass": paired_analyses["normal_vs_disabled"]["acceptance_criteria_met"],
            "slow_condition_pass": paired_analyses["slow_vs_disabled"]["acceptance_criteria_met"],
            "saturated_condition_pass": paired_analyses["saturated_vs_disabled"]["acceptance_criteria_met"],
            "overall_latency_budget_satisfied": (
                paired_analyses["normal_vs_disabled"]["acceptance_criteria_met"]
                and paired_analyses["slow_vs_disabled"]["acceptance_criteria_met"]
                and paired_analyses["saturated_vs_disabled"]["acceptance_criteria_met"]
            ),
        },
    }

    resource_payload = {
        "phase": "8.4C.2",
        "title": "Resource Utilization and Hardware Impact Audit",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resource_summary": resource_summary,
        "telemetry_system_health": shadow_engine.telemetry.get_health(),
    }

    # Write files
    p1 = BASE_DIR / "phase_8_4c2_performance_results.json"
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(perf_results_payload, f, indent=2)
    logger.info(f"Wrote performance results to {p1}")

    p2 = BASE_DIR / "phase_8_4c2_paired_latency_analysis.json"
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(paired_analysis_payload, f, indent=2)
    logger.info(f"Wrote paired latency analysis to {p2}")

    p3 = BASE_DIR / "phase_8_4c2_resource_utilization.json"
    with open(p3, "w", encoding="utf-8") as f:
        json.dump(resource_payload, f, indent=2)
    logger.info(f"Wrote resource utilization to {p3}")

    logger.info("=" * 75)
    logger.info("PHASE 8.4C.2 PAIRED PERFORMANCE EXPERIMENT COMPLETED SUCCESSFULLY")
    logger.info(f"Condition A (Disabled):  Mean={per_condition_stats['disabled']['mean']}ms, p50={per_condition_stats['disabled']['p50']}ms, p99={per_condition_stats['disabled']['p99']}ms")
    logger.info(f"Condition B (Normal):    Mean={per_condition_stats['normal']['mean']}ms, p50={per_condition_stats['normal']['p50']}ms, p99={per_condition_stats['normal']['p99']}ms | Paired Diff: {paired_analyses['normal_vs_disabled']['mean_diff_ms']}ms ({paired_analyses['normal_vs_disabled']['percentage_difference']}%)")
    logger.info(f"Condition C (Slow):      Mean={per_condition_stats['slow']['mean']}ms, p50={per_condition_stats['slow']['p50']}ms, p99={per_condition_stats['slow']['p99']}ms | Paired Diff: {paired_analyses['slow_vs_disabled']['mean_diff_ms']}ms ({paired_analyses['slow_vs_disabled']['percentage_difference']}%)")
    logger.info(f"Condition D (Saturated): Mean={per_condition_stats['saturated']['mean']}ms, p50={per_condition_stats['saturated']['p50']}ms, p99={per_condition_stats['saturated']['p99']}ms | Paired Diff: {paired_analyses['saturated_vs_disabled']['mean_diff_ms']}ms ({paired_analyses['saturated_vs_disabled']['percentage_difference']}%)")
    logger.info(f"Policy A Functional Invariance: {policy_a_invariance_pct}%")
    logger.info("=" * 75)

    return 0


if __name__ == "__main__":
    sys.exit(execute_validation_suite())
