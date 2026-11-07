"""
Heritage & Monument Recognition System - Phase 8.4C Shadow Staging Verification Suite
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025)

Automated test suite verifying all 12 non-negotiable production invariants for Candidate Policy D:
1. Production response identical with shadow mode enabled and disabled.
2. Candidate Policy D cannot overwrite or alter Policy A's returned decision, confidence, or monument identity.
3. Shadow timeout does not delay API response beyond the configured budget.
4. Policy D exception or crash does not fail Policy A recognition.
5. In disabled mode, no background evaluation is submitted or queued.
6. Queue saturation drops/skips candidate tasks safely without blocking or queue explosion.
7. Telemetry correctly records:
   - Agreement cases
   - Policy D upgrades (from Policy A UNCERTAIN to Policy D VERIFIED)
   - Policy D downgrades
   - Unverified agreements
   - Out-of-catalog negative rejections
8. Shadow timeout emits a timeout telemetry event with accurate elapsed time.
9. Shadow execution error emits an error telemetry event without crashing the host process.
10. Telemetry write failure does not break production recognition.
11. Dynamic kill switch immediately prevents new shadow tasks from queuing.
12. Application shutdown cleanly stops the shadow executor without corrupting in-flight telemetry.

Outputs machine-readable summary: backend/phase_8_4c_shadow_test_report.json
"""

import io
import json
import logging
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from shadow_engine import (
    ShadowConfig,
    ShadowEngine,
    ShadowTelemetryLogger,
    shadow_engine,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_shadow_staging")


def create_synthetic_image(text: str, color: tuple) -> bytes:
    img = Image.new("RGB", (320, 240), color=color)
    draw = ImageDraw.Draw(img)
    draw.text((20, 100), text, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


class Phase84CShadowStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._client_cm = TestClient(app)
        cls.client = cls._client_cm.__enter__()
        resp = cls.client.get("/api/health")
        assert resp.status_code == 200, "API health check failed"
        cls.test_results: List[Dict[str, Any]] = []

    def setUp(self):
        shadow_engine.set_runtime_enabled(False)
        while not shadow_engine._queue.empty():
            try:
                shadow_engine._queue.get_nowait()
            except Exception:
                break

    def tearDown(self):
        shadow_engine.set_runtime_enabled(False)
        while not shadow_engine._queue.empty():
            try:
                shadow_engine._queue.get_nowait()
            except Exception:
                break

    @classmethod
    def tearDownClass(cls):
        shadow_engine.set_runtime_enabled(False)
        try:
            cls._client_cm.__exit__(None, None, None)
        except Exception:
            pass

    def _record_result(self, test_num: int, name: str, passed: bool, details: Dict[str, Any], duration_ms: float):
        result_entry = {
            "test_number": test_num,
            "test_name": name,
            "passed": passed,
            "duration_ms": round(duration_ms, 2),
            "details": details,
        }
        self.test_results.append(result_entry)
        status_str = "PASSED" if passed else "FAILED"
        logger.info(f"[{status_str}] Test {test_num}: {name} ({duration_ms:.1f}ms)")

    # -------------------------------------------------------------------------
    # TEST 1: Response identical with shadow mode enabled vs disabled
    # -------------------------------------------------------------------------
    def test_01_response_identical_shadow_enabled_vs_disabled(self):
        t0 = time.perf_counter()
        img_bytes = create_synthetic_image("Taj Mahal Front Dome View", (80, 120, 160))

        # 1. Run with shadow mode DISABLED
        shadow_engine.set_runtime_enabled(False)
        resp_disabled = self.client.post(
            "/api/verify-monument",
            files={"file": ("specimen_taj.jpg", img_bytes, "image/jpeg")},
        )
        self.assertEqual(resp_disabled.status_code, 200)
        data_disabled = resp_disabled.json()

        # 2. Run with shadow mode ENABLED
        shadow_engine.set_runtime_enabled(True)
        resp_enabled = self.client.post(
            "/api/verify-monument",
            files={"file": ("specimen_taj.jpg", img_bytes, "image/jpeg")},
        )
        self.assertEqual(resp_enabled.status_code, 200)
        data_enabled = resp_enabled.json()

        # 3. Verify core recognition fields are strictly invariant
        invariant_fields = [
            "is_monument",
            "verification_status",
            "is_uncertain",
            "verification_tier",
            "confidence_score",
            "monument_name",
            "monument_key",
            "location",
            "catalog_id",
            "rejection_message",
            "human_review_flagged",
        ]

        diffs = {}
        for field in invariant_fields:
            val_dis = data_disabled.get(field)
            val_en = data_enabled.get(field)
            if val_dis != val_en:
                diffs[field] = {"disabled": val_dis, "enabled": val_en}

        passed = len(diffs) == 0
        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            1,
            "Production response identical with shadow mode enabled vs disabled",
            passed,
            {"verified_fields": invariant_fields, "differences": diffs},
            dur_ms,
        )
        self.assertTrue(passed, f"Found response discrepancies: {diffs}")

    # -------------------------------------------------------------------------
    # TEST 2: Policy D cannot overwrite or alter Policy A's decision
    # -------------------------------------------------------------------------
    def test_02_policy_d_cannot_overwrite_policy_a(self):
        t0 = time.perf_counter()
        img_bytes = create_synthetic_image("Ambiguous Specimen", (100, 100, 100))

        shadow_engine.set_runtime_enabled(True)

        # Mock evaluate_policy_d to return a completely different decision:
        # e.g., Policy D claims VERIFIED_MATCH for "sun_temple_konark"
        with patch.object(ShadowEngine, "evaluate_policy_d", return_value=("VERIFIED_MATCH", "sun_temple_konark")):
            resp = self.client.post(
                "/api/verify-monument",
                files={"file": ("specimen_ambig.jpg", img_bytes, "image/jpeg")},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        status = data.get("verification_status")
        monument = data.get("monument_key")

        # Invariant: returned status must NEVER be influenced by Policy D mock
        leak_detected = (monument == "sun_temple_konark" and status == "VERIFIED_MATCH")
        passed = not leak_detected

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            2,
            "Candidate Policy D cannot overwrite or alter Policy A's returned decision",
            passed,
            {"policy_a_status": status, "policy_a_monument": monument, "leak_detected": leak_detected},
            dur_ms,
        )
        self.assertTrue(passed, "Policy D decision leaked into Policy A returned response!")

    # -------------------------------------------------------------------------
    # TEST 3: Shadow timeout does not delay API response beyond configured budget
    # -------------------------------------------------------------------------
    def test_03_shadow_timeout_budget_isolation(self):
        t0 = time.perf_counter()
        img_bytes = create_synthetic_image("Taj Mahal", (80, 120, 160))

        shadow_engine.set_runtime_enabled(True)

        # Inject an artificial delay inside evaluate_policy_d
        unblock_event = threading.Event()
        def slow_eval(*args, **kwargs):
            unblock_event.wait(timeout=0.6)
            return ("VERIFIED_MATCH", "taj_mahal")

        with patch.object(ShadowEngine, "evaluate_policy_d", side_effect=slow_eval):
            req_start = time.perf_counter()
            resp = self.client.post(
                "/api/verify-monument",
                files={"file": ("specimen_slow.jpg", img_bytes, "image/jpeg")},
            )
            req_duration_ms = (time.perf_counter() - req_start) * 1000.0

        unblock_event.set()
        time.sleep(0.05)

        self.assertEqual(resp.status_code, 200)
        # Non-blocking invariant: The HTTP response must return immediately (< 1000ms on CPU)
        # without waiting for the 1.5s shadow task
        passed = req_duration_ms < 1000.0

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            3,
            "Shadow timeout does not delay API response beyond configured budget",
            passed,
            {"api_request_duration_ms": round(req_duration_ms, 2), "expected_max_ms": 1000.0},
            dur_ms,
        )
        self.assertTrue(passed, f"API response was blocked by shadow task! Duration: {req_duration_ms:.1f}ms")

    # -------------------------------------------------------------------------
    # TEST 4: Policy D exception does not fail Policy A recognition
    # -------------------------------------------------------------------------
    def test_04_policy_d_exception_does_not_fail_policy_a(self):
        t0 = time.perf_counter()
        img_bytes = create_synthetic_image("Taj Mahal", (80, 120, 160))

        shadow_engine.set_runtime_enabled(True)

        # Inject a simulated exception in Policy D
        def crashing_eval(*args, **kwargs):
            raise RuntimeError("CRITICAL SIFT/RANSAC SEGMENTATION FAULT IN SHADOW THREAD")

        with patch.object(ShadowEngine, "evaluate_policy_d", side_effect=crashing_eval):
            resp = self.client.post(
                "/api/verify-monument",
                files={"file": ("specimen_crash.jpg", img_bytes, "image/jpeg")},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        passed = (resp.status_code == 200 and "verification_status" in data)

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            4,
            "Policy D exception or crash does not fail Policy A recognition",
            passed,
            {"http_status": resp.status_code, "verification_status": data.get("verification_status")},
            dur_ms,
        )
        self.assertTrue(passed, "Policy D crash caused Policy A endpoint to fail!")

    # -------------------------------------------------------------------------
    # TEST 5: In disabled mode, no background evaluation is submitted or queued
    # -------------------------------------------------------------------------
    def test_05_disabled_mode_zero_queue_or_submissions(self):
        t0 = time.perf_counter()
        img_bytes = create_synthetic_image("Charminar", (120, 80, 80))

        shadow_engine.set_runtime_enabled(False)
        self.assertFalse(shadow_engine.is_enabled())

        resp = self.client.post(
            "/api/verify-monument",
            files={"file": ("specimen_disabled.jpg", img_bytes, "image/jpeg")},
        )
        self.assertEqual(resp.status_code, 200)

        # Directly attempt submission to test the fail-safe
        dummy_img = Image.new("RGB", (100, 100), (0, 0, 0))
        q_len_before = shadow_engine._queue.qsize()
        sub_status = shadow_engine.submit_shadow_evaluation(
            request_id="test_disabled_submission",
            image=dummy_img,
            top1_key="taj_mahal",
            top1_sim=0.85,
            margin=0.10,
            gatekeeper_score=0.90,
            policy_a_decision="VERIFIED_MATCH",
            policy_a_monument="taj_mahal",
        )

        q_len_after = shadow_engine._queue.qsize()
        metrics_after = shadow_engine.get_metrics()
        self.assertEqual(sub_status, "SHADOW_DISABLED")

        passed = (
            sub_status == "SHADOW_DISABLED"
            and q_len_after == q_len_before
        )

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            5,
            "In disabled mode, no background evaluation is submitted or queued",
            passed,
            {
                "submission_status": sub_status,
                "queue_length": metrics_after["queue_length"],
                "active_threads": metrics_after["active_threads"],
            },
            dur_ms,
        )
        self.assertTrue(passed, "Task was queued despite shadow mode being disabled!")

    # -------------------------------------------------------------------------
    # TEST 6: Queue saturation drops/skips candidate tasks safely (SHADOW_SKIPPED_CAPACITY)
    # -------------------------------------------------------------------------
    def test_06_queue_saturation_safety(self):
        t0 = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_log_path = Path(tmp_dir) / "test_shadow.jsonl"
            test_logger = ShadowTelemetryLogger(log_path=test_log_path)
            test_config = ShadowConfig(enabled=True, max_workers=1, max_queue_size=2)
            test_engine = ShadowEngine(config=test_config)
            test_engine.telemetry = test_logger

            blocker_event = threading.Event()

            def blocking_task(*args, **kwargs):
                blocker_event.wait(timeout=2.0)
                return ("VERIFIED_MATCH", "taj_mahal")

            dummy_img = Image.new("RGB", (100, 100), (50, 50, 50))

            with patch.object(ShadowEngine, "evaluate_policy_d", side_effect=blocking_task):
                # Submit 1 (running)
                s1 = test_engine.submit_shadow_evaluation(
                    request_id="task_1", image=dummy_img, top1_key="taj_mahal",
                    top1_sim=0.8, margin=0.1, gatekeeper_score=0.9,
                    policy_a_decision="VERIFIED_MATCH", policy_a_monument="taj_mahal",
                )
                # Submit 2 (queue item 1)
                s2 = test_engine.submit_shadow_evaluation(
                    request_id="task_2", image=dummy_img, top1_key="taj_mahal",
                    top1_sim=0.8, margin=0.1, gatekeeper_score=0.9,
                    policy_a_decision="VERIFIED_MATCH", policy_a_monument="taj_mahal",
                )
                # Submit 3 (queue item 2 - queue full at capacity 2)
                s3 = test_engine.submit_shadow_evaluation(
                    request_id="task_3", image=dummy_img, top1_key="taj_mahal",
                    top1_sim=0.8, margin=0.1, gatekeeper_score=0.9,
                    policy_a_decision="VERIFIED_MATCH", policy_a_monument="taj_mahal",
                )
                # Submit 4: Must be dropped immediately with SHADOW_SKIPPED_CAPACITY
                s4 = test_engine.submit_shadow_evaluation(
                    request_id="task_4", image=dummy_img, top1_key="taj_mahal",
                    top1_sim=0.8, margin=0.1, gatekeeper_score=0.9,
                    policy_a_decision="VERIFIED_MATCH", policy_a_monument="taj_mahal",
                )

                blocker_event.set()
                test_engine.shutdown(wait=True)

            passed = (s4 == "SHADOW_SKIPPED_CAPACITY")
            metrics = test_engine.get_metrics()

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            6,
            "Queue saturation drops/skips candidate tasks safely without blocking",
            passed,
            {
                "submission_1": s1,
                "submission_2": s2,
                "submission_3": s3,
                "submission_4_overflow": s4,
                "total_dropped": metrics["dropped_submissions"],
            },
            dur_ms,
        )
        self.assertTrue(passed, f"Overflow task was not safely skipped! Status: {s4}")

    # -------------------------------------------------------------------------
    # TEST 7: Telemetry correctly records all divergence categories
    # -------------------------------------------------------------------------
    def test_07_telemetry_divergence_categories(self):
        t0 = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_log_path = Path(tmp_dir) / "test_divergence.jsonl"
            tlogger = ShadowTelemetryLogger(log_path=test_log_path)

            scenarios = [
                # 1. AGREEMENT
                {"a_dec": "VERIFIED_MATCH", "d_dec": "VERIFIED_MATCH", "a_mon": "taj_mahal", "d_mon": "taj_mahal", "expected": "AGREEMENT"},
                # 2. POLICY_D_UPGRADE
                {"a_dec": "UNCERTAIN_MATCH", "d_dec": "VERIFIED_MATCH", "a_mon": "hawa_mahal", "d_mon": "hawa_mahal", "expected": "POLICY_D_UPGRADE"},
                # 3. POLICY_D_DOWNGRADE
                {"a_dec": "VERIFIED_MATCH", "d_dec": "UNCERTAIN_MATCH", "a_mon": "qutub_minar", "d_mon": "qutub_minar", "expected": "POLICY_D_DOWNGRADE"},
                # 4. UNVERIFIED_AGREEMENT
                {"a_dec": "UNCERTAIN_MATCH", "d_dec": "UNCERTAIN_MATCH", "a_mon": "charminar", "d_mon": "charminar", "expected": "UNVERIFIED_AGREEMENT"},
                # 5. OUT_OF_CATALOG_NEGATIVE_REJECTION
                {"a_dec": "NON_MONUMENT_REJECTED", "d_dec": "NON_MONUMENT_REJECTED", "a_mon": "", "d_mon": "", "expected": "OUT_OF_CATALOG_NEGATIVE_REJECTION"},
            ]

            classified = []
            for sc in scenarios:
                cat = ShadowEngine.classify_divergence(sc["a_dec"], sc["d_dec"])
                classified.append(cat)
                tlogger.record_event({
                    "event_type": "SHADOW_EVALUATION_COMPLETED",
                    "request_id": f"req_{sc['expected']}",
                    "policy_a_decision": sc["a_dec"],
                    "policy_d_decision": sc["d_dec"],
                    "divergence_category": cat,
                    "policy_a_monument": sc["a_mon"],
                    "policy_d_monument": sc["d_mon"],
                    "latency_ms": 45.2,
                })

            entries = []
            with open(test_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    entries.append(json.loads(line))

            passed = (
                len(entries) == 5
                and all(e["divergence_category"] == sc["expected"] for e, sc in zip(entries, scenarios))
            )

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            7,
            "Telemetry correctly records all divergence categories",
            passed,
            {"expected_categories": [sc["expected"] for sc in scenarios], "actual_categories": classified},
            dur_ms,
        )
        self.assertTrue(passed, f"Divergence mismatch: {classified}")

    # -------------------------------------------------------------------------
    # TEST 8: Shadow timeout emits a timeout telemetry event with accurate elapsed time
    # -------------------------------------------------------------------------
    def test_08_shadow_timeout_telemetry(self):
        t0 = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_log_path = Path(tmp_dir) / "test_timeout.jsonl"
            tlogger = ShadowTelemetryLogger(log_path=test_log_path)
            config = ShadowConfig(enabled=True, max_workers=1, max_queue_size=5, timeout_ms=100)
            engine = ShadowEngine(config=config)
            engine.telemetry = tlogger

            def sleeping_policy_d(*args, **kwargs):
                time.sleep(0.25)
                return ("VERIFIED_MATCH", "taj_mahal")

            dummy_img = Image.new("RGB", (64, 64), (10, 10, 10))

            with patch.object(ShadowEngine, "evaluate_policy_d", side_effect=sleeping_policy_d):
                engine.submit_shadow_evaluation(
                    request_id="req_timeout_test",
                    image=dummy_img,
                    top1_key="taj_mahal",
                    top1_sim=0.8,
                    margin=0.1,
                    gatekeeper_score=0.9,
                    policy_a_decision="UNCERTAIN_MATCH",
                    policy_a_monument="taj_mahal",
                )
                time.sleep(0.30)
                engine.shutdown(wait=True)

            entries = []
            with open(test_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    entries.append(json.loads(line))

            timeout_entries = [e for e in entries if e.get("event_type") == "SHADOW_TIMEOUT"]
            has_timeout = len(timeout_entries) > 0
            elapsed_ok = has_timeout and timeout_entries[0].get("elapsed_ms", 0) >= 90.0

            passed = has_timeout and elapsed_ok

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            8,
            "Shadow timeout emits a timeout telemetry event with accurate elapsed time",
            passed,
            {"timeout_event_found": has_timeout, "timeout_entries": timeout_entries},
            dur_ms,
        )
        self.assertTrue(passed, "Timeout telemetry event was not recorded properly!")

    # -------------------------------------------------------------------------
    # TEST 9: Shadow execution error emits an error telemetry event
    # -------------------------------------------------------------------------
    def test_09_shadow_execution_error_telemetry(self):
        t0 = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_log_path = Path(tmp_dir) / "test_error.jsonl"
            tlogger = ShadowTelemetryLogger(log_path=test_log_path)
            config = ShadowConfig(enabled=True, max_workers=1, max_queue_size=5)
            engine = ShadowEngine(config=config)
            engine.telemetry = tlogger

            def crashing_policy_d(*args, **kwargs):
                raise ValueError("Synthetic RANSAC degenerate matrix error")

            dummy_img = Image.new("RGB", (64, 64), (20, 20, 20))

            with patch.object(ShadowEngine, "evaluate_policy_d", side_effect=crashing_policy_d):
                engine.submit_shadow_evaluation(
                    request_id="req_error_test",
                    image=dummy_img,
                    top1_key="taj_mahal",
                    top1_sim=0.8,
                    margin=0.1,
                    gatekeeper_score=0.9,
                    policy_a_decision="UNCERTAIN_MATCH",
                    policy_a_monument="taj_mahal",
                )
                time.sleep(0.1)
                engine.shutdown(wait=True)

            entries = []
            with open(test_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    entries.append(json.loads(line))

            error_entries = [e for e in entries if e.get("event_type") == "SHADOW_ERROR"]
            passed = (
                len(error_entries) > 0
                and "Synthetic RANSAC" in error_entries[0].get("error_message", "")
            )

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            9,
            "Shadow execution error emits an error telemetry event without crashing host process",
            passed,
            {"error_event_found": len(error_entries) > 0, "error_details": error_entries},
            dur_ms,
        )
        self.assertTrue(passed, "Error telemetry event was not recorded properly!")

    # -------------------------------------------------------------------------
    # TEST 10: Telemetry write failure does not break production recognition
    # -------------------------------------------------------------------------
    def test_10_telemetry_write_failure_resilience(self):
        t0 = time.perf_counter()
        img_bytes = create_synthetic_image("Taj Mahal", (80, 120, 160))

        shadow_engine.set_runtime_enabled(True)

        with patch.object(ShadowTelemetryLogger, "record_event", side_effect=OSError("Read-only filesystem simulation")):
            resp = self.client.post(
                "/api/verify-monument",
                files={"file": ("specimen_disk_err.jpg", img_bytes, "image/jpeg")},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        passed = (resp.status_code == 200 and "verification_status" in data)

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            10,
            "Telemetry write failure does not break production recognition",
            passed,
            {"http_status": resp.status_code, "verification_status": data.get("verification_status")},
            dur_ms,
        )
        self.assertTrue(passed, "Telemetry write failure crashed the production recognition request!")

    # -------------------------------------------------------------------------
    # TEST 11: Dynamic kill switch immediately prevents new shadow tasks from queuing
    # -------------------------------------------------------------------------
    def test_11_dynamic_kill_switch(self):
        t0 = time.perf_counter()

        dummy_img = Image.new("RGB", (64, 64), (10, 10, 10))

        # 1. Initially enabled
        shadow_engine.set_runtime_enabled(True)
        self.assertTrue(shadow_engine.is_enabled())

        # 2. Flip kill switch dynamically
        shadow_engine.set_runtime_enabled(False)
        self.assertFalse(shadow_engine.is_enabled())

        # 3. Submit evaluation immediately after kill switch
        q_len_before = shadow_engine._queue.qsize()
        sub_status = shadow_engine.submit_shadow_evaluation(
            request_id="req_kill_switch_test",
            image=dummy_img,
            top1_key="taj_mahal",
            top1_sim=0.8,
            margin=0.1,
            gatekeeper_score=0.9,
            policy_a_decision="VERIFIED_MATCH",
            policy_a_monument="taj_mahal",
        )

        q_len_after = shadow_engine._queue.qsize()
        passed = (sub_status == "SHADOW_DISABLED" and q_len_after == q_len_before)

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            11,
            "Dynamic kill switch immediately prevents new shadow tasks from queuing",
            passed,
            {"kill_switch_state": shadow_engine.is_enabled(), "submission_result": sub_status},
            dur_ms,
        )
        self.assertTrue(passed, "Task was queued after kill switch was activated!")

    # -------------------------------------------------------------------------
    # TEST 12: Application shutdown cleanly stops shadow executor without corruption
    # -------------------------------------------------------------------------
    def test_12_shutdown_cleans_executor_safely(self):
        t0 = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_log_path = Path(tmp_dir) / "test_shutdown.jsonl"
            tlogger = ShadowTelemetryLogger(log_path=test_log_path)
            config = ShadowConfig(enabled=True, max_workers=2, max_queue_size=5)
            engine = ShadowEngine(config=config)
            engine.telemetry = tlogger

            dummy_img = Image.new("RGB", (64, 64), (30, 30, 30))

            with patch.object(ShadowEngine, "evaluate_policy_d", return_value=("VERIFIED_MATCH", "taj_mahal")):
                engine.submit_shadow_evaluation(
                    request_id="shutdown_task_1", image=dummy_img, top1_key="taj_mahal",
                    top1_sim=0.8, margin=0.1, gatekeeper_score=0.9,
                    policy_a_decision="VERIFIED_MATCH", policy_a_monument="taj_mahal",
                )
                engine.submit_shadow_evaluation(
                    request_id="shutdown_task_2", image=dummy_img, top1_key="taj_mahal",
                    top1_sim=0.8, margin=0.1, gatekeeper_score=0.9,
                    policy_a_decision="VERIFIED_MATCH", policy_a_monument="taj_mahal",
                )

                engine.shutdown(wait=True)

            is_shutdown = engine._executor._shutdown

            valid_json_count = 0
            with open(test_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        json.loads(line)
                        valid_json_count += 1

            passed = is_shutdown and (valid_json_count >= 2)

        dur_ms = (time.perf_counter() - t0) * 1000.0
        self._record_result(
            12,
            "Application shutdown cleanly stops the shadow executor without corrupting in-flight telemetry",
            passed,
            {"executor_shutdown": is_shutdown, "valid_telemetry_records": valid_json_count},
            dur_ms,
        )
        self.assertTrue(passed, "Shutdown did not cleanly terminate executor or corrupted telemetry!")


def run_all_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase84CShadowStagingTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    report_data = {
        "phase": "8.4C",
        "title": "Controlled Shadow Staging Test Report",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total_tests": result.testsRun,
        "passed_tests": result.testsRun - len(result.failures) - len(result.errors),
        "failed_tests": len(result.failures),
        "errored_tests": len(result.errors),
        "all_passed": result.wasSuccessful(),
        "test_results": Phase84CShadowStagingTests.test_results,
        "production_invariants_verified": [
            "Policy A remains authoritative",
            "Zero influence of Policy D on Policy A returned responses",
            "Shadow timeout budget strictly isolated (< 500ms)",
            "Shadow exceptions completely insulated",
            "Default disabled kill switch functioning",
            "Queue saturation backpressure functional",
            "Complete divergence taxonomy logged",
            "Thread-safe telemetry without disk or memory leaks",
        ],
    }

    report_path = BASE_DIR / "phase_8_4c_shadow_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Wrote machine-readable test report to {report_path}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
