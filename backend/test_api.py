"""
Heritage & Monument Recognition System - Integration Test Suite
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025)
Tests:
  1. GET /api/health
  2. GET /api/monuments (Catalog & Grounded Citations check)
  3. GET /api/exceptions (Curator Human-Review Exception Log)
  4. POST /api/verify-monument (Taj Mahal: Grounded Citations & Tier 1 Match)
  5. POST /api/verify-monument (Charminar: Verified Match)
  6. POST /api/verify-monument (Synthetic Non-Monument: Non-Monument Rejection)
"""

import io
import logging
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_api")


def create_synthetic_non_monument_image() -> bytes:
    img = Image.new("RGB", (300, 300), color=(240, 240, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 280, 60], fill=(70, 80, 95))
    draw.rectangle([30, 90, 270, 110], fill=(180, 190, 200))
    draw.rectangle([30, 130, 200, 150], fill=(200, 210, 220))
    draw.rectangle([30, 170, 240, 190], fill=(180, 190, 200))
    draw.rectangle([30, 220, 150, 260], fill=(100, 110, 125))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def run_tests():
    logger.info("=" * 75)
    logger.info("STARTING SIH 2025 COMPLIANT BACKEND INTEGRATION TESTS")
    logger.info("=" * 75)

    with TestClient(app) as client:
        # Test 1: GET /api/health
        logger.info("\n--- [Test 1] Testing GET /api/health ---")
        health_resp = client.get("/api/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["status"] == "healthy"
        assert health_data["faiss_vectors_loaded"] == 210
        assert health_data["monuments_count"] == 10
        logger.info(f"[PASSED] Health: {health_data}")

        # Test 2: GET /api/monuments
        logger.info("\n--- [Test 2] Testing GET /api/monuments ---")
        cat_resp = client.get("/api/monuments")
        assert cat_resp.status_code == 200
        cat_data = cat_resp.json()
        assert cat_data["total"] in [10, 100]
        assert "taj_mahal" in cat_data["monuments"]
        assert "grounded_citations" in cat_data["monuments"]["taj_mahal"]
        logger.info("[PASSED] Monuments catalog with grounded citations verified.")

        # Test 3: GET /api/exceptions
        logger.info("\n--- [Test 3] Testing GET /api/exceptions ---")
        exc_resp = client.get("/api/exceptions")
        assert exc_resp.status_code == 200
        exc_data = exc_resp.json()
        assert "exceptions" in exc_data
        logger.info(f"[PASSED] Human-review exception log verified (Count: {exc_data['total']}).")

        # Test 4: POST /api/verify-monument (Taj Mahal Real Image)
        logger.info("\n--- [Test 4] Testing POST /api/verify-monument (Taj Mahal Grounded Match) ---")
        taj_path = BASE_DIR / "dataset" / "taj_mahal" / "img_1.jpg"
        with open(taj_path, "rb") as f:
            taj_bytes = f.read()

        taj_resp = client.post(
            "/api/verify-monument",
            files={"file": ("taj_test.jpg", taj_bytes, "image/jpeg")},
        )
        assert taj_resp.status_code == 200
        taj_data = taj_resp.json()
        assert taj_data["is_monument"] is True
        assert taj_data["verification_status"] == "VERIFIED_MATCH"
        assert taj_data["monument_key"] == "taj_mahal"
        assert taj_data["grounded_citations"] is not None
        assert "Archaeological Survey of India" in taj_data["grounded_citations"]["primary_source"]
        logger.info(f"[PASSED] Taj Mahal verified with grounded source citations.")

        # Test 5: POST /api/verify-monument (Charminar Real Image)
        logger.info("\n--- [Test 5] Testing POST /api/verify-monument (Charminar) ---")
        charminar_path = BASE_DIR / "dataset" / "charminar" / "img_2.jpg"
        with open(charminar_path, "rb") as f:
            charminar_bytes = f.read()

        charminar_resp = client.post(
            "/api/verify-monument",
            files={"file": ("charminar_test.jpg", charminar_bytes, "image/jpeg")},
        )
        assert charminar_resp.status_code == 200
        charminar_data = charminar_resp.json()
        assert charminar_data["is_monument"] is True
        assert charminar_data["monument_key"] == "charminar"
        logger.info(f"[PASSED] Charminar verified.")

        # Test 6: POST /api/verify-monument (Synthetic Non-Monument Rejection)
        logger.info("\n--- [Test 6] Testing POST /api/verify-monument (Synthetic Non-Monument) ---")
        non_monument_bytes = create_synthetic_non_monument_image()
        non_resp = client.post(
            "/api/verify-monument",
            files={"file": ("receipt_test.jpg", non_monument_bytes, "image/jpeg")},
        )
        assert non_resp.status_code == 200
        non_data = non_resp.json()
        assert non_data["is_monument"] is False
        assert non_data["verification_status"] == "NON_MONUMENT_REJECTED"
        logger.info("[PASSED] Non-monument rejection verified.")

    logger.info("\n" + "=" * 75)
    logger.info("ALL SIH 2025 BACKEND INTEGRATION TESTS PASSED (6/6)")
    logger.info("=" * 75)


if __name__ == "__main__":
    run_tests()
