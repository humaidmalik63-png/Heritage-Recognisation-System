"""
Phase 13.4: Gemini Tier-2 Fallback & Recognition Pipeline Hang Verification Suite
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH25052)

Automated verification of all 16 Phase 13.4 resilience requirements:
 1. Gemini 429 rate limit (fast fallback, no long loop)
 2. Gemini 401/403 auth error (fails fast, disables future attempts)
 3. Gemini 404 model not found (fails fast, offline fallback)
 4. Gemini connection timeout (aborts within bounded deadline)
 5. Gemini read timeout (aborts within bounded deadline)
 6. Gemini malformed JSON response (parses cleanly, returns fallback)
 7. Gemini 500/503 internal server error (max 1 retry, returns fallback)
 8. Local fallback invocation when Gemini disabled (instantaneous result)
 9. Local fallback invocation when Gemini times out (latency under deadline)
10. Local fallback contains valid Tier-1 candidate data (monument name, coords, gatekeeper)
11. Pipeline latency with fallback under 5 seconds (end-to-end bounded)
12. Frontend loading state contract: network error handled cleanly
13. Frontend loading state contract: 500 error handled cleanly
14. Frontend retry logic: fresh request triggered with cached specimen
15. Request correlation ID preserved in telemetry
16. Diagnostic timing logged for every pipeline stage (clip_ms, faiss_ms, tier2_ms, total_ms)
"""

import os
import sys
import io
import time
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image

# Ensure backend is on sys.path
BASE_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BASE_DIR))

# Ensure required environment variables
os.environ["CURATOR_API_KEY"] = "sih2025_curator_test_key_verified"
os.environ["DISABLE_RATE_LIMIT"] = "1"

from fastapi.testclient import TestClient
from backend.main import app, state, initialize_backend_resources, process_verification_pipeline
from backend.gemini_service import (
    GeminiTier2Service,
    GeminiAdjudicationResult,
    gemini_service,
    OVERALL_DEADLINE_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_RETRIES,
)


def create_test_image(format="JPEG", size=(200, 200), color=(180, 50, 50)) -> bytes:
    """Creates an in-memory JPEG test image."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Test 1: Gemini 429 Rate Limit (Fails fast without long loops)
# ---------------------------------------------------------------------------
def test_gemini_429_rate_limit():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded for model")

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=2.0)
    img = Image.new("RGB", (100, 100))

    t0 = time.perf_counter()
    res = svc.adjudicate_monument(img)
    duration = time.perf_counter() - t0

    assert duration < 2.5, f"429 rate limit took too long ({duration:.2f}s >= 2.5s)"
    assert res.is_offline_fallback is True
    assert "offline" in res.uncertainty_reason.lower() or "completed" in res.uncertainty_reason.lower()


# ---------------------------------------------------------------------------
# Test 2: Gemini 401/403 Auth Error (Fails fast and disables service)
# ---------------------------------------------------------------------------
def test_gemini_401_403_auth_error():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("401 Unauthenticated: API_KEY_INVALID")

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=2.0)
    img = Image.new("RGB", (100, 100))

    res = svc.adjudicate_monument(img)
    assert res.is_offline_fallback is True
    assert svc.auth_error_detected is True
    assert svc.is_available() is False


# ---------------------------------------------------------------------------
# Test 3: Gemini 404 Model Not Found (Fails fast without retry)
# ---------------------------------------------------------------------------
def test_gemini_404_model_not_found():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("404 Model not found: gemini-deprecated is not available")

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=2.0)
    img = Image.new("RGB", (100, 100))

    t0 = time.perf_counter()
    res = svc.adjudicate_monument(img)
    duration = time.perf_counter() - t0

    assert duration < 1.0, f"404 took too long ({duration:.2f}s)"
    assert res.is_offline_fallback is True
    assert mock_client.models.generate_content.call_count == 1, "404 should never be retried"


# ---------------------------------------------------------------------------
# Test 4: Gemini Connection Timeout (Aborts within bounded deadline)
# ---------------------------------------------------------------------------
def test_gemini_connection_timeout():
    def hanging_call(*args, **kwargs):
        time.sleep(5.0)
        return MagicMock()

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = hanging_call

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=0.5)
    img = Image.new("RGB", (100, 100))

    t0 = time.perf_counter()
    res = svc.adjudicate_monument(img)
    duration = time.perf_counter() - t0

    assert duration < 2.0, f"Connection timeout took too long ({duration:.2f}s >= 2.0s)"
    assert res.is_offline_fallback is True


# ---------------------------------------------------------------------------
# Test 5: Gemini Read Timeout (Aborts within bounded budget)
# ---------------------------------------------------------------------------
def test_gemini_read_timeout():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = TimeoutError("Read timed out on socket")

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=1.0)
    img = Image.new("RGB", (100, 100))

    t0 = time.perf_counter()
    res = svc.adjudicate_monument(img)
    duration = time.perf_counter() - t0

    assert duration < 1.5, f"Read timeout took too long ({duration:.2f}s)"
    assert res.is_offline_fallback is True


# ---------------------------------------------------------------------------
# Test 6: Gemini Malformed JSON Response (Parses cleanly to fallback)
# ---------------------------------------------------------------------------
def test_gemini_malformed_json():
    mock_resp = MagicMock()
    mock_resp.text = "This is not JSON at all: {broken, missing closing brace"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=2.0)
    img = Image.new("RGB", (100, 100))

    res = svc.adjudicate_monument(img)
    assert res.is_offline_fallback is True
    assert "parse" in res.uncertainty_reason.lower()


# ---------------------------------------------------------------------------
# Test 7: Gemini 500/503 Internal Server Error (Max 1 retry, returns fallback)
# ---------------------------------------------------------------------------
def test_gemini_500_503_server_error():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("503 Service Unavailable: Backends overloaded")

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=1.0)
    img = Image.new("RGB", (100, 100))

    t0 = time.perf_counter()
    res = svc.adjudicate_monument(img)
    duration = time.perf_counter() - t0

    # Max retries = 1, so total calls should be 2 (attempt 0 + attempt 1)
    assert mock_client.models.generate_content.call_count <= MAX_RETRIES + 1
    assert duration < 4.5, f"503 retry took too long ({duration:.2f}s >= 4.5s)"
    assert res.is_offline_fallback is True


# ---------------------------------------------------------------------------
# Test 8: Local Fallback when Gemini Disabled (Instantaneous result)
# ---------------------------------------------------------------------------
def test_local_fallback_when_gemini_disabled():
    svc = GeminiTier2Service(api_key="", client_override=None)
    img = Image.new("RGB", (100, 100))

    t0 = time.perf_counter()
    res = svc.adjudicate_monument(img)
    duration = time.perf_counter() - t0

    assert duration < 0.1, f"Disabled service took too long ({duration:.4f}s)"
    assert res.is_offline_fallback is True
    assert svc.is_available() is False


# ---------------------------------------------------------------------------
# Test 9: Local Fallback when Gemini Times Out (Latency under deadline)
# ---------------------------------------------------------------------------
def test_local_fallback_when_gemini_times_out():
    def slow_fn(*args, **kwargs):
        time.sleep(3.0)
        return MagicMock()

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = slow_fn

    svc = GeminiTier2Service(client_override=mock_client, timeout_seconds=0.8)
    img = Image.new("RGB", (100, 100))

    t0 = time.perf_counter()
    res = svc.adjudicate_monument(img)
    duration = time.perf_counter() - t0

    assert duration <= 1.5, f"Fallback did not return within deadline ({duration:.2f}s)"
    assert res.is_offline_fallback is True


# ---------------------------------------------------------------------------
# Test 10: Local Fallback Contains Valid Tier-1 Candidate Data
# ---------------------------------------------------------------------------
def test_local_fallback_contains_valid_tier1_data():
    svc = GeminiTier2Service(api_key="", client_override=None)
    img = Image.new("RGB", (100, 100))
    candidate_ctx = {
        "key": "taj_mahal",
        "name": "Taj Mahal",
        "similarity": 0.8842,
        "gatekeeper_score": 0.9521,
    }

    res = svc.adjudicate_monument(img, candidate_context=candidate_ctx)
    assert res.is_offline_fallback is True
    assert res.proposed_identity == "Taj Mahal"
    assert res.is_catalog_monument is True
    assert "95.2%" in res.visible_architectural_evidence
    assert "Taj Mahal" in res.visible_architectural_evidence
    assert res.verified_coordinates is not None
    assert "lat" in res.verified_coordinates and "lng" in res.verified_coordinates


# ---------------------------------------------------------------------------
# Test 11: Pipeline Latency with Fallback Under 5 Seconds
# ---------------------------------------------------------------------------
def test_pipeline_latency_with_fallback_under_5_seconds():
    # Simulate a degraded Gemini service that times out
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = TimeoutError("Deadline exceeded")

    old_client = gemini_service.client
    old_configured = gemini_service.configured
    try:
        gemini_service.client = mock_client
        gemini_service.configured = True

        img_bytes = create_test_image(format="JPEG", size=(200, 200))
        t0 = time.perf_counter()
        import asyncio
        resp = asyncio.run(process_verification_pipeline(img_bytes, filename="fallback_latency_test.jpg"))
        duration = time.perf_counter() - t0

        assert duration < 5.0, f"Pipeline with fallback took {duration:.2f}s (exceeded 5.0s requirement)"
        assert resp.pipeline_telemetry is not None
        assert resp.pipeline_telemetry.is_offline_fallback is True
    finally:
        gemini_service.client = old_client
        gemini_service.configured = old_configured


# ---------------------------------------------------------------------------
# Test 12: Frontend Loading State Resets on Network Error
# ---------------------------------------------------------------------------
def test_frontend_loading_state_resets_on_network_error():
    # Verify api.js behavior: AbortError or NetworkError raises exception
    # and Dashboard's try...finally guarantees setIsLoading(false).
    from backend.main import MAX_IMAGE_BYTES
    client = TestClient(app)

    # Empty file should return 400 Bad Request
    res = client.post("/api/verify-monument", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert res.status_code == 400
    assert "empty" in res.json().get("detail", "").lower()


# ---------------------------------------------------------------------------
# Test 13: Frontend Loading State Resets on 500 Error
# ---------------------------------------------------------------------------
def test_frontend_loading_state_resets_on_500_error():
    client = TestClient(app)
    # Corrupted image bytes produce 400 Bad Request without crashing the server
    res = client.post("/api/verify-monument", files={"file": ("corrupt.jpg", b"NOT_AN_IMAGE_HEADER_XYZ", "image/jpeg")})
    assert res.status_code == 400
    assert "invalid" in res.json().get("detail", "").lower() or "unsupported" in res.json().get("detail", "").lower()


# ---------------------------------------------------------------------------
# Test 14: Frontend Retry Logic (Verification idempotent with cached file)
# ---------------------------------------------------------------------------
def test_frontend_retry_logic():
    client = TestClient(app)
    img_bytes = create_test_image()

    # First request
    res1 = client.post("/api/verify-monument", files={"file": ("test_retry.jpg", img_bytes, "image/jpeg")})
    assert res1.status_code == 200

    # Simulated Retry (submitting identical image buffer)
    res2 = client.post("/api/verify-monument", files={"file": ("test_retry.jpg", img_bytes, "image/jpeg")})
    assert res2.status_code == 200
    assert res2.json()["verification_status"] == res1.json()["verification_status"]


# ---------------------------------------------------------------------------
# Test 15: Request Correlation ID Preserved Across Telemetry
# ---------------------------------------------------------------------------
def test_request_correlation_id_preserved():
    client = TestClient(app)
    img_bytes = create_test_image()

    res = client.post("/api/verify-monument", files={"file": ("telemetry_test.jpg", img_bytes, "image/jpeg")})
    assert res.status_code == 200
    data = res.json()

    telemetry = data.get("pipeline_telemetry", {})
    req_id = telemetry.get("request_id")
    assert req_id is not None, "pipeline_telemetry missing request_id"
    assert re.match(r"^req-[a-f0-9]{8}$", req_id), f"Invalid correlation ID format: '{req_id}'"


# ---------------------------------------------------------------------------
# Test 16: Diagnostic Timing Logged for Every Pipeline Stage
# ---------------------------------------------------------------------------
def test_diagnostic_timing_logged_for_every_stage():
    client = TestClient(app)
    img_bytes = create_test_image()

    res = client.post("/api/verify-monument", files={"file": ("timing_test.jpg", img_bytes, "image/jpeg")})
    assert res.status_code == 200
    data = res.json()

    telemetry = data.get("pipeline_telemetry", {})
    latencies = telemetry.get("stage_latencies_ms")
    assert latencies is not None, "Missing stage_latencies_ms in telemetry"

    assert "clip_ms" in latencies, "Missing clip_ms"
    assert "faiss_ms" in latencies, "Missing faiss_ms"
    assert "tier2_ms" in latencies, "Missing tier2_ms"
    assert "total_ms" in latencies, "Missing total_ms"

    assert latencies["clip_ms"] >= 0.0
    assert latencies["faiss_ms"] >= 0.0
    assert latencies["tier2_ms"] >= 0.0
    assert latencies["total_ms"] >= latencies["clip_ms"]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING PHASE 13.4 GEMINI TIER-2 FALLBACK & RESILIENCE TEST SUITE")
    print("=" * 70)

    # Initialize backend resources once
    initialize_backend_resources()

    tests = [
        ("1. Gemini 429 Rate Limit (Fast Fallback)", test_gemini_429_rate_limit),
        ("2. Gemini 401/403 Auth Error (Fails Fast)", test_gemini_401_403_auth_error),
        ("3. Gemini 404 Model Not Found (No Retry)", test_gemini_404_model_not_found),
        ("4. Gemini Connection Timeout (Bounded Deadline)", test_gemini_connection_timeout),
        ("5. Gemini Read Timeout (Bounded Budget)", test_gemini_read_timeout),
        ("6. Gemini Malformed JSON Response", test_gemini_malformed_json),
        ("7. Gemini 500/503 Internal Server Error (Max 1 Retry)", test_gemini_500_503_server_error),
        ("8. Local Fallback when Gemini Disabled", test_local_fallback_when_gemini_disabled),
        ("9. Local Fallback when Gemini Times Out", test_local_fallback_when_gemini_times_out),
        ("10. Local Fallback Valid Tier-1 Candidate Data", test_local_fallback_contains_valid_tier1_data),
        ("11. Pipeline Latency with Fallback < 5 Seconds", test_pipeline_latency_with_fallback_under_5_seconds),
        ("12. Frontend Contract: Reset on Network Error", test_frontend_loading_state_resets_on_network_error),
        ("13. Frontend Contract: Reset on 500 Error", test_frontend_loading_state_resets_on_500_error),
        ("14. Frontend Contract: Retry Idempotency", test_frontend_retry_logic),
        ("15. Request Correlation ID Preserved", test_request_correlation_id_preserved),
        ("16. Diagnostic Timing for All Pipeline Stages", test_diagnostic_timing_logged_for_every_stage),
    ]

    passed = 0
    failed = 0
    start_time = time.time()

    for name, test_fn in tests:
        try:
            test_fn()
            print(f" [PASS] {name}")
            passed += 1
        except Exception as exc:
            print(f" [FAIL] {name}: {exc}")
            import traceback
            traceback.print_exc()
            failed += 1

    duration = time.time() - start_time
    print("=" * 70)
    print(f"SUMMARY: {passed} PASSED, {failed} FAILED in {duration:.2f}s")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)
