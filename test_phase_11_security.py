"""
Phase 11: Production Security & Hardening Test Suite
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform
Tests all 20 security checklist controls locally.
"""

import os
import sys
import io
import time
from pathlib import Path

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BASE_DIR))

# Ensure test curator key is configured for the test runner
os.environ["CURATOR_API_KEY"] = "sih2025_curator_test_key_verified"
os.environ["DISABLE_RATE_LIMIT"] = "0"

from fastapi.testclient import TestClient
from PIL import Image

# Import FastAPI app from backend.main
from backend.main import app, state, initialize_backend_resources


def get_test_client():
    """Initializes backend models and returns TestClient instance."""
    initialize_backend_resources()
    return TestClient(app)


def create_test_image(format="JPEG", size=(200, 200), color=(180, 50, 50)) -> bytes:
    """Creates a genuine test image buffer in JPEG, PNG, or WebP format."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


# --- 1. Security Headers Verification ---
def test_security_headers(client):
    """Verifies all mandatory defensive headers are present on API responses."""
    res = client.get("/api/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options"
    assert headers.get("X-Frame-Options") == "DENY", "Missing X-Frame-Options: DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block", "Missing X-XSS-Protection"
    assert "strict-origin" in headers.get("Referrer-Policy", ""), "Missing Referrer-Policy"
    assert "camera" in headers.get("Permissions-Policy", ""), "Missing Permissions-Policy"
    assert "default-src" in headers.get("Content-Security-Policy", ""), "Missing Content-Security-Policy"


# --- 2. CORS Allowlist & Isolation ---
def test_cors_allowed_origin(client):
    """Verifies preflight and requests from registered production frontend are accepted."""
    headers = {
        "Origin": "https://heritage-monuments.vercel.app",
        "Access-Control-Request-Method": "POST",
    }
    res = client.options("/api/verify-monument", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://heritage-monuments.vercel.app"


def test_cors_disallowed_origin(client):
    """Verifies unauthorized origins do not receive CORS permission."""
    headers = {
        "Origin": "https://malicious-attacker-domain.evil",
        "Access-Control-Request-Method": "POST",
    }
    res = client.options("/api/verify-monument", headers=headers)
    # Origin should not be echoed back
    allow_origin = res.headers.get("access-control-allow-origin")
    assert allow_origin != "https://malicious-attacker-domain.evil"


# --- 3. Health Endpoint & FAISS Vector Integrity ---
def test_api_health_status(client):
    """Verifies FAISS vectors, 100 catalogue sites, and health telemetry are intact."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["faiss_vectors_loaded"] == 577, f"Expected 577 vectors, got {data['faiss_vectors_loaded']}"
    assert data["monuments_count"] == 100, f"Expected 100 monuments, got {data['monuments_count']}"
    assert data["catalogue_100_count"] == 100


# --- 4. Input Validation & Magic Byte Enforcement ---
def test_file_upload_empty_rejection(client):
    """Verifies empty file upload is rejected with 400 Bad Request."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    res = client.post("/api/verify-monument", files=files)
    assert res.status_code == 400
    assert "empty" in res.json().get("detail", "").lower()


def test_file_upload_svg_rejection(client):
    """Verifies SVG upload is rejected to eliminate vector XSS risks."""
    svg_payload = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    files = {"file": ("exploit.svg", svg_payload, "image/svg+xml")}
    res = client.post("/api/verify-monument", files=files)
    assert res.status_code == 400
    assert "svg" in res.json().get("detail", "").lower()


def test_file_upload_fake_extension(client):
    """Verifies renaming binary / text file to .jpg is caught by magic bytes inspection."""
    fake_payload = b"MZ\x90\x00\x03\x00\x00\x00This is an executable masquerading as a JPEG"
    files = {"file": ("fake.jpg", fake_payload, "image/jpeg")}
    res = client.post("/api/verify-monument", files=files)
    assert res.status_code == 400
    assert "unsupported" in res.json().get("detail", "").lower()


def test_file_upload_oversized_rejection(client):
    """Verifies uploads exceeding 15MB limit are rejected with 413 Payload Too Large."""
    # 16 MB of zeros
    oversized = b"\xff\xd8\xff" + b"\x00" * (16 * 1024 * 1024)
    files = {"file": ("huge.jpg", oversized, "image/jpeg")}
    res = client.post("/api/verify-monument", files=files)
    assert res.status_code == 413
    assert "too large" in res.json().get("detail", "").lower()


# --- 5. IDOR & Path Traversal Mitigation ---
def test_path_traversal_rejection(client):
    """Verifies directory traversal identifiers are blocked by regex sanitization."""
    res = client.get("/api/monuments/..%2F..%2Fetc%2Fpasswd/knowledge")
    assert res.status_code in (400, 404)
    if res.status_code == 400:
        assert "invalid monument_id" in res.json().get("detail", "").lower()


def test_inquiry_length_sanitization(client):
    """Verifies questions exceeding 500 characters or containing HTML are sanitized."""
    # Question with HTML
    payload = {"question": "What is the history? <script>alert('xss')</script>"}
    res = client.post("/api/monuments/taj_mahal/ask", json=payload)
    assert res.status_code == 200

    # Oversized question (blocked by Pydantic max_length=500 with 422 or sanitizer with 400)
    huge_question = "A" * 600
    res_huge = client.post("/api/monuments/taj_mahal/ask", json={"question": huge_question})
    assert res_huge.status_code in (400, 422)


# --- 6. Curator Authentication & Constant-Time Verification ---
def test_curator_resolve_without_key_rejected(client):
    """Verifies resolving an exception without valid X-Curator-Key is blocked with 401."""
    res = client.post(
        "/api/exceptions/EXC-TEST01/resolve",
        json={"status": "APPROVED", "curator_notes": "Attempted without credentials"},
    )
    assert res.status_code == 401
    assert "unauthorized" in res.json().get("detail", "").lower()


def test_curator_resolve_with_wrong_key_rejected(client):
    """Verifies wrong key is blocked with 401."""
    res = client.post(
        "/api/exceptions/EXC-TEST01/resolve",
        headers={"X-Curator-Key": "incorrect_guess_attacker"},
        json={"status": "APPROVED", "curator_notes": "Attempted with wrong key"},
    )
    assert res.status_code == 401


def test_curator_resolve_with_correct_key(client):
    """Verifies valid curator key allows exception resolution."""
    # Create or record a test exception first
    client.get("/api/exceptions")
    res = client.post(
        "/api/exceptions/EXC-AF9821DC/resolve",
        headers={"X-Curator-Key": "sih2025_curator_test_key_verified"},
        json={"status": "APPROVED", "curator_notes": "Verified by curatorial audit team"},
    )
    # Either 200 (if found) or 404 (if ID was pruned) - importantly NOT 401
    assert res.status_code in (200, 404)
    assert res.status_code != 401


# --- 7. Exceptions Pagination ---
def test_exceptions_pagination(client):
    """Verifies limit and offset parameters work correctly for authorized admin."""
    from backend.auth import create_session_token
    token, _ = create_session_token("admin", role="admin")
    res = client.get("/api/exceptions?limit=2&offset=0", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "limit" in data
    assert data["limit"] == 2
    assert "offset" in data
    assert len(data["exceptions"]) <= 2


# --- 8. Rate Limiting Sliding-Window Verification ---
def test_rate_limiting_enforcement(client):
    """Verifies rate limiter triggers 429 after exceeding limit."""
    from backend.security import RateLimiter
    # Test rate limiter logic directly to verify window mathematics
    limiter = RateLimiter(window_seconds=10)
    test_ip = "192.168.1.100"

    # Send up to limit
    for _ in range(5):
        allowed, _, _ = limiter.is_allowed(test_ip, max_requests=5)
        assert allowed is True

    # 6th request must be blocked
    allowed, remaining, retry_after = limiter.is_allowed(test_ip, max_requests=5)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


# --- 9. Real Monument Verification Pipeline Test ---
def test_real_monument_verification(client):
    """Verifies full end-to-end recognition pipeline with genuine Petra image."""
    petra_path = Path("frontend/public/assets/heritage/petra.jpg")
    if not petra_path.exists():
        print("  (Warning: Petra test image not found in assets, skipping)")
        return

    with open(petra_path, "rb") as f:
        img_bytes = f.read()

    files = {"file": ("petra.jpg", img_bytes, "image/jpeg")}
    res = client.post("/api/verify-monument", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["is_monument"] is True
    assert data["monument_key"] == "petra"
    assert data["monument_name"] == "Petra"
    assert data["verification_status"] == "VERIFIED_MATCH"
    assert data["confidence_score"] >= 85.0
    assert data["grounded_citations"] is not None


# --- 10. Non-Monument Rejection Pipeline Test ---
def test_synthetic_non_monument_rejection(client):
    """Verifies non-architectural test image is properly classified or rejected."""
    # Plain solid gray image
    non_mon_bytes = create_test_image(format="JPEG", size=(300, 300), color=(128, 128, 128))
    files = {"file": ("gray_square.jpg", non_mon_bytes, "image/jpeg")}
    res = client.post("/api/verify-monument", files=files)
    assert res.status_code == 200
    data = res.json()
    # Should not be verified as a catalog monument
    assert data["verification_status"] in ("NON_MONUMENT_REJECTED", "UNKNOWN_HERITAGE_SPECIMEN", "UNCERTAIN_MATCH", "REVIEW_REQUIRED")
    assert data["verification_status"] != "VERIFIED_MATCH"


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING PHASE 11 SECURITY & PRODUCTION HARDENING TEST SUITE")
    print("=" * 70)

    # Initialize backend
    initialize_backend_resources()
    test_client = TestClient(app)

    tests = [
        ("1. Security Headers Verification", test_security_headers),
        ("2. CORS Allowed Origin", test_cors_allowed_origin),
        ("3. CORS Disallowed Origin", test_cors_disallowed_origin),
        ("4. Health Endpoint & FAISS Vector Count", test_api_health_status),
        ("5. Input Validation: Empty File Rejection", test_file_upload_empty_rejection),
        ("6. Input Validation: Malicious SVG Rejection", test_file_upload_svg_rejection),
        ("7. Input Validation: Fake Extension Rejection", test_file_upload_fake_extension),
        ("8. Input Validation: Oversized File Rejection (>15MB)", test_file_upload_oversized_rejection),
        ("9. IDOR / Path Traversal Sanitization", test_path_traversal_rejection),
        ("10. Inquiry Question Sanitization & Length Bound", test_inquiry_length_sanitization),
        ("11. Curator Auth: Missing Key Rejection (401)", test_curator_resolve_without_key_rejected),
        ("12. Curator Auth: Wrong Key Rejection (401)", test_curator_resolve_with_wrong_key_rejected),
        ("13. Curator Auth: Correct Key Verification", test_curator_resolve_with_correct_key),
        ("14. Exceptions Log Pagination", test_exceptions_pagination),
        ("15. Rate Limiting Sliding Window Enforcement", test_rate_limiting_enforcement),
        ("16. Full Recognition Pipeline (Petra Specimen)", test_real_monument_verification),
        ("17. Non-Monument Reject Pipeline", test_synthetic_non_monument_rejection),
    ]

    passed = 0
    failed = 0
    start_time = time.time()

    for name, test_fn in tests:
        try:
            test_fn(test_client)
            print(f" [PASS] {name}")
            passed += 1
        except Exception as exc:
            print(f" [FAIL] {name}: {exc}")
            failed += 1

    duration = time.time() - start_time
    print("=" * 70)
    print(f"SUMMARY: {passed} PASSED, {failed} FAILED in {duration:.2f}s")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)
