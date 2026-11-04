"""
Heritage & Monument Recognition System - Phase 6.2 Uncertainty & Calibration Test Suite
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025)

Covers all 13 mandatory test scenarios:
  1. Strong, distinctive known monument (VERIFIED_MATCH)
  2. Two competing monuments with small margin (UNCERTAIN_MATCH)
  3. Low similarity for an unknown monument (UNKNOWN_HERITAGE_SPECIMEN)
  4. Non-monument rejection (NON_MONUMENT_REJECTED)
  5. High similarity but low gatekeeper evidence (REVIEW_REQUIRED)
  6. Missing GPS with otherwise strong evidence (VERIFIED_MATCH, no rejection)
  7. Conflicting GPS evidence (REVIEW_REQUIRED / GPS_CONFLICT)
  8. Low-quality image (LOW_IMAGE_QUALITY / REVIEW_REQUIRED)
  9. Duplicate FAISS anchors belonging to one monument (Unique Aggregation)
  10. Calibration unavailable (UNCALIBRATED / probability is None)
  11. Malformed calibration configuration (Safe fallback)
  12. Persistent human-review ticket creation & audit trail (No duplicates)
  13. Existing API response backward compatibility
"""

import io
import json
import logging
import sys
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from calibration import CalibrationEngine
from main import app, load_exceptions_log, record_exception_entry
from uncertainty import (
    AggregatedCandidate,
    DecisionState,
    ReasonCode,
    UncertaintyEngine,
    inspect_image_quality,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_uncertainty")


def make_test_image(size=(400, 400), color=(180, 150, 120), pattern=True) -> Image.Image:
    img = Image.new("RGB", size, color=color)
    if pattern:
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 350, 200], fill=(120, 80, 60))
        draw.polygon([(200, 20), (50, 50), (350, 50)], fill=(90, 50, 40))
        draw.rectangle([100, 200, 150, 350], fill=(220, 200, 180))
        draw.rectangle([250, 200, 300, 350], fill=(220, 200, 180))
    return img


def run_all_uncertainty_tests():
    logger.info("=" * 75)
    logger.info("STARTING PHASE 6.2 UNCERTAINTY & CALIBRATION TEST SUITE (13 SCENARIOS)")
    logger.info("=" * 75)

    engine = UncertaintyEngine()
    test_img = make_test_image()

    labels = [
        {"index_id": 0, "monument_key": "taj_mahal", "monument_name": "Taj Mahal", "source": "taj_1.jpg", "is_centroid": False},
        {"index_id": 1, "monument_key": "taj_mahal", "monument_name": "Taj Mahal", "source": "taj_2.jpg", "is_centroid": False},
        {"index_id": 2, "monument_key": "taj_mahal", "monument_name": "Taj Mahal", "source": "taj_centroid", "is_centroid": True},
        {"index_id": 3, "monument_key": "charminar", "monument_name": "Charminar", "source": "cha_1.jpg", "is_centroid": False},
        {"index_id": 4, "monument_key": "charminar", "monument_name": "Charminar", "source": "cha_centroid", "is_centroid": True},
        {"index_id": 5, "monument_key": "qutub_minar", "monument_name": "Qutub Minar", "source": "qut_1.jpg", "is_centroid": False},
    ]

    metadata = {
        "taj_mahal": {"monument_name": "Taj Mahal", "coordinates": {"lat": 27.1751, "lng": 78.0421}},
        "charminar": {"monument_name": "Charminar", "coordinates": {"lat": 17.3616, "lng": 78.4747}},
        "qutub_minar": {"monument_name": "Qutub Minar", "coordinates": {"lat": 28.5245, "lng": 77.1855}},
    }

    # -------------------------------------------------------------
    # Scenario 1: Strong, distinctive known monument (VERIFIED_MATCH)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 1] Strong Distinctive Known Monument ---")
    dists_1 = np.array([0.92, 0.90, 0.88, 0.65, 0.63, 0.60], dtype=np.float32)
    idxs_1 = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)
    res_1 = engine.evaluate(
        image=test_img,
        gatekeeper_score=0.98,
        raw_distances=dists_1,
        raw_indices=idxs_1,
        labels=labels,
        metadata=metadata,
        exif_gps=None,
    )
    assert res_1.decision == DecisionState.VERIFIED_MATCH, f"Expected VERIFIED_MATCH, got {res_1.decision}"
    assert res_1.top1_similarity == 0.92
    assert res_1.top2_similarity == 0.65
    assert res_1.similarity_margin >= 0.05
    assert res_1.calibrated_probability is None, "Expected None when uncalibrated"
    assert res_1.requires_human_review is False
    logger.info(f"[PASSED] Scenario 1: {res_1.decision} (Top-1: {res_1.top1_similarity}, Margin: {res_1.similarity_margin})")

    # -------------------------------------------------------------
    # Scenario 2: Two competing monuments with small margin (UNCERTAIN_MATCH)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 2] Competing Monuments with Small Margin ---")
    dists_2 = np.array([0.84, 0.82, 0.83, 0.825, 0.81, 0.50], dtype=np.float32)
    # idx 0 is taj_mahal (0.84), idx 3 is charminar (0.825) -> margin = 0.015 < 0.05
    idxs_2 = np.array([0, 1, 3, 4, 2, 5], dtype=np.int64)
    res_2 = engine.evaluate(
        image=test_img,
        gatekeeper_score=0.90,
        raw_distances=dists_2,
        raw_indices=idxs_2,
        labels=labels,
        metadata=metadata,
    )
    assert res_2.decision == DecisionState.UNCERTAIN_MATCH, f"Expected UNCERTAIN_MATCH, got {res_2.decision}"
    assert res_2.similarity_margin < 0.05
    assert ReasonCode.AMBIGUOUS_TOP_CANDIDATES.value in res_2.reason_codes
    assert res_2.requires_human_review is True
    logger.info(f"[PASSED] Scenario 2: {res_2.decision} (Margin: {res_2.similarity_margin} < 0.05, Review: {res_2.requires_human_review})")

    # -------------------------------------------------------------
    # Scenario 3: Low similarity for an unknown monument (UNKNOWN_HERITAGE_SPECIMEN)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 3] Low Similarity for Unknown Monument ---")
    dists_3 = np.array([0.62, 0.59, 0.58, 0.55, 0.52, 0.45], dtype=np.float32)
    idxs_3 = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)
    res_3 = engine.evaluate(
        image=test_img,
        gatekeeper_score=0.88,  # Clear architecture detected
        raw_distances=dists_3,
        raw_indices=idxs_3,
        labels=labels,
        metadata=metadata,
    )
    assert res_3.decision == DecisionState.UNKNOWN_HERITAGE_SPECIMEN, f"Expected UNKNOWN_HERITAGE_SPECIMEN, got {res_3.decision}"
    assert ReasonCode.LOW_RETRIEVAL_SIMILARITY.value in res_3.reason_codes
    assert res_3.requires_human_review is True
    logger.info(f"[PASSED] Scenario 3: {res_3.decision} (Nearest: {res_3.top1_similarity} < 0.80)")

    # -------------------------------------------------------------
    # Scenario 4: Non-monument rejection (NON_MONUMENT_REJECTED)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 4] Non-Monument Specimen Rejection ---")
    dists_4 = np.array([0.45, 0.44, 0.42, 0.40, 0.39, 0.35], dtype=np.float32)
    idxs_4 = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)
    res_4 = engine.evaluate(
        image=test_img,
        gatekeeper_score=0.08,  # Fails gatekeeper
        raw_distances=dists_4,
        raw_indices=idxs_4,
        labels=labels,
        metadata=metadata,
    )
    assert res_4.decision == DecisionState.NON_MONUMENT_REJECTED, f"Expected NON_MONUMENT_REJECTED, got {res_4.decision}"
    assert ReasonCode.LOW_GATEKEEPER_CONFIDENCE.value in res_4.reason_codes
    assert res_4.requires_human_review is False
    logger.info(f"[PASSED] Scenario 4: {res_4.decision} (Gatekeeper: {res_4.gatekeeper_score})")

    # -------------------------------------------------------------
    # Scenario 5: High similarity but low gatekeeper evidence (REVIEW_REQUIRED)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 5] High Similarity with Conflicting Low Gatekeeper ---")
    dists_5 = np.array([0.88, 0.85, 0.82, 0.60, 0.55, 0.50], dtype=np.float32)
    idxs_5 = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)
    res_5 = engine.evaluate(
        image=test_img,
        gatekeeper_score=0.25,  # Contradicting gatekeeper
        raw_distances=dists_5,
        raw_indices=idxs_5,
        labels=labels,
        metadata=metadata,
    )
    assert res_5.decision == DecisionState.REVIEW_REQUIRED, f"Expected REVIEW_REQUIRED, got {res_5.decision}"
    assert res_5.requires_human_review is True
    logger.info(f"[PASSED] Scenario 5: {res_5.decision} (Sim: {res_5.top1_similarity}, Gatekeeper: {res_5.gatekeeper_score})")

    # -------------------------------------------------------------
    # Scenario 6: Missing GPS with otherwise strong evidence (VERIFIED_MATCH, no rejection)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 6] Missing GPS with Strong Visual Evidence ---")
    res_6 = engine.evaluate(
        image=test_img,
        gatekeeper_score=0.95,
        raw_distances=dists_1,
        raw_indices=idxs_1,
        labels=labels,
        metadata=metadata,
        exif_gps=None,  # Missing GPS
    )
    assert res_6.decision == DecisionState.VERIFIED_MATCH, "Missing GPS must not cause rejection!"
    assert res_6.gps_evidence.has_gps is False
    assert ReasonCode.MISSING_GPS.value in res_6.reason_codes
    logger.info(f"[PASSED] Scenario 6: {res_6.decision} (has_gps: False, verified purely on visual vector)")

    # -------------------------------------------------------------
    # Scenario 7: Conflicting GPS evidence (REVIEW_REQUIRED / GPS_CONFLICT)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 7] Conflicting GPS Evidence ---")
    # Taj Mahal is in Agra (~27.17° N, ~78.04° E). We simulate a photo geotagged in Mumbai (18.92° N, 72.83° E, >1000 km away)
    mumbai_gps = {"lat": 18.9220, "lng": 72.8347}
    res_7 = engine.evaluate(
        image=test_img,
        gatekeeper_score=0.92,
        raw_distances=dists_1,
        raw_indices=idxs_1,
        labels=labels,
        metadata=metadata,
        exif_gps=mumbai_gps,
    )
    assert res_7.decision == DecisionState.REVIEW_REQUIRED, f"Expected REVIEW_REQUIRED, got {res_7.decision}"
    assert res_7.gps_evidence.gps_conflict is True
    assert ReasonCode.GPS_CONFLICT.value in res_7.reason_codes
    assert res_7.requires_human_review is True
    logger.info(f"[PASSED] Scenario 7: {res_7.decision} (Distance: {res_7.gps_evidence.distance_km:.1f} km, Conflict: True)")

    # -------------------------------------------------------------
    # Scenario 8: Low-quality image (LOW_IMAGE_QUALITY / REVIEW_REQUIRED)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 8] Low-Quality Image (Blur / Underexposure) ---")
    blurry_img = test_img.filter(ImageFilter.GaussianBlur(radius=15))
    quality = inspect_image_quality(blurry_img, engine.calibration.image_quality_config)
    assert quality.is_blurry is True
    assert quality.passed_quality_check is False

    res_8 = engine.evaluate(
        image=blurry_img,
        gatekeeper_score=0.75,
        raw_distances=dists_1,
        raw_indices=idxs_1,
        labels=labels,
        metadata=metadata,
    )
    assert res_8.decision == DecisionState.REVIEW_REQUIRED
    assert ReasonCode.LOW_IMAGE_QUALITY.value in res_8.reason_codes
    assert res_8.image_quality.is_blurry is True
    logger.info(f"[PASSED] Scenario 8: {res_8.decision} (Blur Score: {res_8.image_quality.blur_score})")

    # -------------------------------------------------------------
    # Scenario 9: Duplicate FAISS anchors belonging to one monument (Unique Aggregation)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 9] Duplicate FAISS Anchors of Same Monument ---")
    # Top 3 raw FAISS results are ALL taj_mahal: idx 0 (0.95), idx 1 (0.92), idx 2 (0.90)
    # 4th result is charminar: idx 3 (0.70)
    raw_dists_dup = np.array([0.95, 0.92, 0.90, 0.70, 0.68, 0.50], dtype=np.float32)
    raw_idxs_dup = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)

    agg_candidates = engine.aggregate_faiss_candidates(
        raw_distances=raw_dists_dup,
        raw_indices=raw_idxs_dup,
        labels=labels,
        metadata=metadata,
        top_k=3,
    )
    assert len(agg_candidates) >= 2
    assert agg_candidates[0].monument_key == "taj_mahal"
    assert agg_candidates[0].max_similarity == 0.95
    assert agg_candidates[1].monument_key == "charminar"
    assert agg_candidates[1].max_similarity == 0.70

    # Margin must be 0.95 - 0.70 = 0.25 (NOT comparing Taj Mahal anchor 1 to Taj Mahal anchor 2!)
    margin = agg_candidates[0].max_similarity - agg_candidates[1].max_similarity
    assert round(margin, 2) == 0.25
    logger.info(f"[PASSED] Scenario 9: Unique aggregation successfully separated {agg_candidates[0].monument_key} from {agg_candidates[1].monument_key} (Margin: {margin:.4f})")

    # -------------------------------------------------------------
    # Scenario 10: Calibration unavailable (UNCALIBRATED / probability is None)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 10] Calibration Engine Uncalibrated Invariant ---")
    calib = CalibrationEngine()
    assert calib.calibration_status == "UNCALIBRATED"
    assert calib.is_calibrated is False
    calib_prob = calib.calibrate_similarity(0.9542)
    assert calib_prob is None, "When uncalibrated, calibrate_similarity must strictly return None!"
    logger.info(f"[PASSED] Scenario 10: calibrate_similarity(0.9542) strictly returned None under UNCALIBRATED status.")

    # -------------------------------------------------------------
    # Scenario 11: Malformed calibration configuration (Safe fallback)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 11] Malformed Calibration Config Fallback ---")
    malformed_json_dict = {"version": "invalid_structure", "temperature": "NOT_A_NUMBER"}
    fallback_engine = CalibrationEngine(malformed_json_dict)
    assert fallback_engine.calibration_status == "UNCALIBRATED"
    assert fallback_engine.confidence_threshold == 0.80
    assert fallback_engine.temperature == 1.0
    logger.info(f"[PASSED] Scenario 11: Engine gracefully absorbed malformed config without crashing.")

    # -------------------------------------------------------------
    # Scenario 12: Persistent human-review ticket creation & audit trail (No duplicates)
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 12] Persistent Ticket Creation & Duplicate Suppression ---")
    fake_cand = AggregatedCandidate(
        monument_key="taj_mahal",
        monument_name="Taj Mahal",
        max_similarity=0.74,
        matched_anchor_source="test.jpg",
        is_centroid_match=False,
    )
    specimen_hash = "abc123testspecimen"

    # Create ticket 1
    t1 = record_exception_entry(
        filename="test_specimen.jpg",
        gatekeeper_score=0.82,
        top_candidate=fake_cand,
        reason="Uncertain match simulation",
        specimen_hash=specimen_hash,
    )
    # Call again with identical specimen hash
    t2 = record_exception_entry(
        filename="test_specimen.jpg",
        gatekeeper_score=0.82,
        top_candidate=fake_cand,
        reason="Uncertain match duplicate scan",
        specimen_hash=specimen_hash,
    )
    assert t1 == t2, f"Duplicate scan must return existing ticket ID! Got {t1} vs {t2}"

    # Verify audit history
    log = load_exceptions_log()
    target_entry = next((item for item in log if item["id"] == t1), None)
    assert target_entry is not None
    assert "history" in target_entry
    assert target_entry["history"][0]["action"] == "CREATED"
    logger.info(f"[PASSED] Scenario 12: Duplicate scan suppressed (Reused ticket {t1}); Audit trail initialized.")

    # -------------------------------------------------------------
    # Scenario 13: Existing API response backward compatibility
    # -------------------------------------------------------------
    logger.info("\n--- [Scenario 13] API Response Backward Compatibility ---")
    with TestClient(app) as client:
        # Test real Taj Mahal image
        taj_path = BASE_DIR / "dataset" / "taj_mahal" / "img_1.jpg"
        with open(taj_path, "rb") as f:
            taj_bytes = f.read()

        resp = client.post(
            "/api/verify-monument",
            files={"file": ("compat_test.jpg", taj_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200, f"API error: {resp.text}"
        data = resp.json()

        # Check existing fields are preserved
        assert "is_monument" in data
        assert "verification_status" in data
        assert "verification_tier" in data
        assert "confidence_score" in data
        assert "catalog_id" in data
        assert "monument_key" in data
        assert "monument_name" in data
        assert "location" in data
        assert "coordinates" in data
        assert "pipeline_telemetry" in data
        assert "top_3_candidates" in data["pipeline_telemetry"]
        assert "grounded_citations" in data

        # Check NEW uncertainty object is present
        assert "uncertainty" in data
        unc = data["uncertainty"]
        assert "decision" in unc
        assert "top1_similarity" in unc
        assert "top2_similarity" in unc
        assert "similarity_margin" in unc
        assert "calibrated_probability" in unc
        assert "calibration_status" in unc
        assert "gatekeeper_score" in unc
        assert "gps_evidence" in unc
        assert "image_quality" in unc
        assert "reason_codes" in unc
        assert "requires_human_review" in unc
        assert "explanation" in unc

        logger.info(f"[PASSED] Scenario 13: Backward compatibility verified. Uncertainty object integrated cleanly.")

    logger.info("\n" + "=" * 75)
    logger.info("ALL 13 PHASE 6.2 UNCERTAINTY & CALIBRATION TESTS PASSED PERFECTLY!")
    logger.info("=" * 75)


if __name__ == "__main__":
    run_all_uncertainty_tests()

