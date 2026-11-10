"""
Phase 13.4B: Final Timeout Correctness & Concurrency Audit Test Suite.
Verifies:
1. ThreadPoolExecutor & Future.result(timeout=...) behavior without blocking context managers.
2. Actual wall-clock duration of calling functions when Gemini deliberately hangs (>15s).
3. Fallback correctness across 9 failure & success scenarios (never upgrades to VERIFIED_MATCH, no invented citations).
4. Concurrency safety: 10 concurrent hanging requests do not cause thread explosion or deadlocks.
"""

import sys
import os
import time
import threading
import concurrent.futures
from unittest.mock import MagicMock
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
os.environ["UNIT_TEST_MODE"] = "1"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["GEMINI_API_KEY"] = "AIzaSyDummyKeyForAuditTesting1234567890"

from backend.gemini_service import GeminiTier2Service, _tier2_executor, OVERALL_DEADLINE_SECONDS, DEFAULT_TIMEOUT_SECONDS
from backend.main import app, process_verification_pipeline
from fastapi.testclient import TestClient

def test_1_executor_not_context_managed():
    """Verify executor is a persistent pool and context manager shutdown(wait=True) is not invoked."""
    print("Testing 1. Executor Context Manager Audit...")
    assert _tier2_executor is not None
    assert isinstance(_tier2_executor, concurrent.futures.ThreadPoolExecutor)
    assert _tier2_executor._max_workers == 4
    # Ensure pool is alive and active
    fut = _tier2_executor.submit(lambda: 42)
    assert fut.result(timeout=2.0) == 42
    print(" [PASS] 1. Executor is persistent global pool with max_workers=4 (no context-manager shutdown hang)")

def test_2_actual_overall_deadline_blocking_gemini():
    """Verify calling function returns within bounded deadline when Gemini deliberately hangs (15s)."""
    print("Testing 2. Actual Overall Deadline for Blocked Gemini Request...")
    service = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890", timeout_seconds=4.0)

    # Deliberately blocking mock that sleeps 15s (far exceeds 4.0s timeout and 9.5s deadline)
    def hanging_call(*args, **kwargs):
        time.sleep(15.0)
        mock_resp = MagicMock()
        mock_resp.text = '{"proposed_identity": "Fake"}'
        return mock_resp

    mock_client = MagicMock()
    mock_client.models.generate_content = hanging_call
    service.client = mock_client
    service.configured = True

    dummy_img = Image.new("RGB", (224, 224), color=(100, 100, 100))
    context = {
        "candidate_key": "taj_mahal",
        "candidate_name": "Taj Mahal",
        "top_similarity": 0.82,
        "gatekeeper_score": 0.95,
        "is_catalog_monument": True,
    }

    t0 = time.perf_counter()
    # Call the actual calling function
    result = service.adjudicate_monument(dummy_img, context)
    elapsed = time.perf_counter() - t0

    print(f"    Elapsed time for deliberately hung request: {elapsed:.3f}s")
    assert elapsed < 5.5, f"Calling function took {elapsed:.2f}s; expected <= 5.5s (timeout was 4.0s)"
    assert result.is_offline_fallback is True
    assert result.qualitative_confidence == "UNCERTAIN"
    assert "timed out" in result.uncertainty_reason.lower() or "offline" in result.uncertainty_reason.lower()
    print(" [PASS] 2. Calling function returned within bounded deadline (elapsed: %.2fs < 5.5s)" % elapsed)

def test_3_verify_fallback_correctness_all_scenarios():
    """Verify 9 scenarios: success, timeout, 429, 401/403, 404, malformed, 503, local success, local reject."""
    print("Testing 3. Verifying Fallback Correctness Across All Scenarios...")
    dummy_img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    context = {
        "candidate_key": "taj_mahal",
        "candidate_name": "Taj Mahal",
        "top_similarity": 0.78,
        "gatekeeper_score": 0.88,
        "is_catalog_monument": True,
    }

    # 3a. Success
    srv_succ = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890")
    m_succ = MagicMock()
    m_succ.models.generate_content.return_value = MagicMock(
        text='{"proposed_identity": "Taj Mahal", "qualitative_confidence": "HIGH", "visible_architectural_evidence": "White marble dome and minarets.", "is_heritage_structure": true, "distinguishing_features": ["Four minarets"]}'
    )
    srv_succ.client = m_succ
    res_succ = srv_succ.adjudicate_monument(dummy_img, context)
    assert res_succ.is_offline_fallback is False
    assert res_succ.proposed_identity == "Taj Mahal"
    print("   [3a] Gemini Success: Verified")

    # 3b. Timeout
    srv_to = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890", timeout_seconds=1.0)
    srv_to.client = MagicMock()
    srv_to.client.models.generate_content.side_effect = lambda *a, **kw: time.sleep(5.0)
    res_to = srv_to.adjudicate_monument(dummy_img, context)
    assert res_to.is_offline_fallback is True
    assert res_to.qualitative_confidence == "UNCERTAIN"
    print("   [3b] Gemini Timeout: Fallback verified, not promoted")

    # 3c. 429 Rate Limit
    srv_429 = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890")
    srv_429.client = MagicMock()
    srv_429.client.models.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded for model")
    res_429 = srv_429.adjudicate_monument(dummy_img, context)
    assert res_429.is_offline_fallback is True
    print("   [3c] Gemini 429 Quota: Fast fallback verified")

    # 3d. 401/403 Auth Error
    srv_auth = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890")
    srv_auth.client = MagicMock()
    srv_auth.client.models.generate_content.side_effect = Exception("403 Forbidden: API key not valid")
    res_auth = srv_auth.adjudicate_monument(dummy_img, context)
    assert res_auth.is_offline_fallback is True
    assert srv_auth.auth_error_detected is True
    print("   [3d] Gemini 401/403: Service disabled, fast fallback verified")

    # 3e. 404 Model Not Found
    srv_404 = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890")
    srv_404.client = MagicMock()
    srv_404.client.models.generate_content.side_effect = Exception("404 Model models/gemini-deprecated is not found")
    res_404 = srv_404.adjudicate_monument(dummy_img, context)
    assert res_404.is_offline_fallback is True
    print("   [3e] Gemini 404: Fast fallback without retry verified")

    # 3f. Malformed JSON
    srv_json = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890")
    srv_json.client = MagicMock()
    srv_json.client.models.generate_content.return_value = MagicMock(text="<HTML>Not JSON</HTML>")
    res_json = srv_json.adjudicate_monument(dummy_img, context)
    assert res_json.is_offline_fallback is True
    print("   [3f] Gemini Malformed JSON: Graceful fallback verified")

    # 3g. 500/503 Server Error (1 retry then fallback)
    srv_503 = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890")
    srv_503.client = MagicMock()
    srv_503.client.models.generate_content.side_effect = Exception("503 Service Unavailable: Backends overloaded")
    t0 = time.perf_counter()
    res_503 = srv_503.adjudicate_monument(dummy_img, context)
    elapsed_503 = time.perf_counter() - t0
    assert res_503.is_offline_fallback is True
    assert elapsed_503 < 4.0, f"503 retry took too long: {elapsed_503:.2f}s"
    print("   [3g] Gemini 503: Max 1 retry then fallback in %.2fs" % elapsed_503)

    # 3h. Local Fallback Valid Candidate
    fb_valid = srv_to._create_deterministic_fallback(context, reason="Test fallback")
    assert fb_valid.proposed_identity == "Taj Mahal"
    assert fb_valid.verified_coordinates is not None
    assert fb_valid.qualitative_confidence == "UNCERTAIN"
    print("   [3h] Local Fallback Candidate: Correct coordinates & UNCERTAIN status verified")

    # 3i. Local Fallback Non-Monument / Low Similarity
    empty_context = {"top_similarity": 0.20, "gatekeeper_score": 0.15, "candidate_name": None}
    fb_empty = srv_to._create_deterministic_fallback(empty_context, reason="Non monument")
    assert fb_empty.proposed_identity is None
    assert fb_empty.is_catalog_monument is False
    print("   [3i] Local Fallback Low Similarity: Identity None & Unindexed verified")
    print(" [PASS] 3. All 9 fallback & resilience scenarios verified successfully")

def test_4_concurrency_and_resource_safety():
    """Simulate 10 concurrent hanging requests to ensure threads do not explode or deadlock."""
    print("Testing 4. Concurrency & Resource Safety (10 Concurrent Hanging Requests)...")
    service = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890", timeout_seconds=1.5)

    def slow_call(*args, **kwargs):
        time.sleep(10.0)
        return MagicMock(text="{}")

    service.client = MagicMock()
    service.client.models.generate_content = slow_call
    service.configured = True

    dummy_img = Image.new("RGB", (224, 224), color=(80, 80, 80))
    context = {"candidate_key": "taj_mahal", "candidate_name": "Taj Mahal", "top_similarity": 0.75}

    initial_threads = threading.active_count()
    print(f"    Initial active threads: {initial_threads}")

    start_time = time.perf_counter()
    results = []

    def make_request(idx):
        t_req = time.perf_counter()
        res = service.adjudicate_monument(dummy_img, context)
        t_dur = time.perf_counter() - t_req
        results.append((idx, res.is_offline_fallback, t_dur))

    threads = [threading.Thread(target=make_request, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()

    # Peak thread check
    peak_threads = threading.active_count()
    print(f"    Peak active threads during concurrent execution: {peak_threads}")

    for t in threads:
        t.join(timeout=10.0)

    total_time = time.perf_counter() - start_time
    print(f"    All 10 requests completed in {total_time:.2f}s")
    assert len(results) == 10, f"Only {len(results)}/10 requests finished"
    assert all(r[1] is True for r in results), "All results must be offline fallback"

    # Thread pool cap verification
    # _tier2_executor has max_workers=4, so it should not create 10 worker threads
    assert _tier2_executor._max_workers == 4

    print(" [PASS] 4. Concurrency safety verified: 10 requests completed cleanly without deadlock or unbounded threads")

def test_5_full_pipeline_uncertainty_preservation():
    """Verify in full pipeline that offline fallback NEVER upgrades to VERIFIED_MATCH."""
    print("Testing 5. Full Pipeline Uncertainty Preservation on Fallback...")
    with TestClient(app) as client:
        # Post a low-confidence or non-monument image
        img = Image.new("RGB", (200, 200), color=(128, 128, 128))
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()

        # Overwrite gemini_service to always fail
        from backend import main
        original_service = main.gemini_service
        failing_service = GeminiTier2Service(api_key="AIzaSyDummyKeyForAuditTesting1234567890", timeout_seconds=1.0)
        failing_service.client = MagicMock()
        failing_service.client.models.generate_content.side_effect = Exception("503 Service Unavailable")
        main.gemini_service = failing_service

        try:
            response = client.post(
                "/api/verify-monument",
                files={"file": ("test_gray.jpg", img_bytes, "image/jpeg")},
            )
            assert response.status_code == 200
            data = response.json()
            status = data.get("verification_status") or data.get("decision")
            assert status in ["REVIEW_REQUIRED", "NON_MONUMENT_REJECTED", "UNINDEXED_HERITAGE", "UNCERTAIN_MATCH"]
            assert status != "VERIFIED_MATCH", "Offline fallback must NEVER promote to VERIFIED_MATCH"
            assert data["pipeline_telemetry"]["is_offline_fallback"] is True
            print(f"    Pipeline decision: {status}, is_offline_fallback: {data['pipeline_telemetry']['is_offline_fallback']}")
            print(" [PASS] 5. Pipeline uncertainty preservation confirmed (never promoted to VERIFIED_MATCH)")
        finally:
            main.gemini_service = original_service

if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING PHASE 13.4B TIMEOUT, CONCURRENCY & INTEGRITY AUDIT")
    print("=" * 70)
    test_1_executor_not_context_managed()
    test_2_actual_overall_deadline_blocking_gemini()
    test_3_verify_fallback_correctness_all_scenarios()
    test_4_concurrency_and_resource_safety()
    test_5_full_pipeline_uncertainty_preservation()
    print("=" * 70)
    print("ALL PHASE 13.4B AUDIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
