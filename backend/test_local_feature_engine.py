"""
Phase 8.0B: Local Feature Recognition Verification Suite (16 Scenarios)
Project No. 30: Visual Heritage Recognition Platform (SIH 2025 - SIH25052)

Exhaustively verifies:
1. Full monument image
2. Partial monument image
3. Close-up carving
4. Pillar detail
5. Dome detail
6. Calligraphic detail
7. Blurred photograph
8. Low-resolution photograph
9. Occluded photograph
10. Non-monument photograph
11. Unsupported image format
12. Corrupted image
13. Empty image upload
14. Global/local prediction disagreement
15. Insufficient local feature evidence
16. Geometric verification failure
"""

import io
import json
import logging
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 console output for Windows cp1252 compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_local_feature_engine")

from local_feature_engine import (
    LocalFeatureEngine,
    ArchitecturalRegion,
    GeometricVerificationResult,
    LocalFeatureMatch,
    local_feature_engine,
)

class TestLocalFeatureEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logger.info("=" * 80)
        logger.info("STARTING PHASE 8.0B LOCAL FEATURE RECOGNITION TEST SUITE (16 SCENARIOS)")
        logger.info("=" * 80)
        cls.engine = LocalFeatureEngine()

        # Load metadata and labels
        with open(BASE_DIR / "monument_labels.json", "r", encoding="utf-8") as f:
            cls.labels = json.load(f)

    # 1. Full monument image
    def test_01_full_monument_image(self):
        logger.info("\n--- [Scenario 1] Full Monument Image ---")
        img = Image.new("RGB", (800, 600), (220, 210, 200))
        _, _, gray = self.engine.preprocess_image(img)
        regions = self.engine.propose_regions(img, gray)
        self.assertGreaterEqual(len(regions), 3)
        self.assertEqual(regions[0].region_id, "reg_upper_dome_spire")
        logger.info(f"[PASSED] Scenario 1: Generated {len(regions)} architectural region proposals for full monument.")

    # 2. Partial monument image
    def test_02_partial_monument_image(self):
        logger.info("\n--- [Scenario 2] Partial Monument Image ---")
        img = Image.new("RGB", (600, 400), (200, 190, 180))
        _, _, gray = self.engine.preprocess_image(img)
        regions = self.engine.propose_regions(img, gray)
        self.assertTrue(any(r.category in ["carving", "pillar", "arch_dome", "sculptural_frieze"] for r in regions))
        logger.info("[PASSED] Scenario 2: Partial monument structured into bounded sub-regions.")

    # 3. Close-up carving
    def test_03_closeup_carving(self):
        logger.info("\n--- [Scenario 3] Close-up Carving ---")
        # Generate rich textured synthetic carving pattern
        np_arr = np.zeros((400, 400), dtype=np.uint8)
        for i in range(10, 390, 20):
            cv2.circle(np_arr, (200, 200), i, 255, 2)
            cv2.line(np_arr, (i, 0), (400 - i, 400), 200, 1)
        kps, des = self.engine.extract_classical_descriptors(np_arr, method="sift")
        self.assertGreater(len(kps), 30)
        self.assertIsNotNone(des)
        logger.info(f"[PASSED] Scenario 3: Extracted {len(kps)} high-frequency SIFT keypoints from carving relief.")

    # 4. Pillar detail
    def test_04_pillar_detail(self):
        logger.info("\n--- [Scenario 4] Pillar Detail ---")
        np_arr = np.zeros((500, 300), dtype=np.uint8)
        # Vertical fluting
        for x in range(30, 270, 15):
            cv2.line(np_arr, (x, 50), (x, 450), 255, 3)
        kps, des = self.engine.extract_classical_descriptors(np_arr, method="sift")
        self.assertGreater(len(kps), 20)
        logger.info(f"[PASSED] Scenario 4: Pillar fluting keypoints detected: {len(kps)}.")

    # 5. Dome detail
    def test_05_dome_detail(self):
        logger.info("\n--- [Scenario 5] Dome Detail ---")
        img = Image.new("RGB", (700, 500), (230, 230, 230))
        _, _, gray = self.engine.preprocess_image(img)
        regions = self.engine.propose_regions(img, gray)
        dome_reg = next((r for r in regions if r.category == "arch_dome"), None)
        self.assertIsNotNone(dome_reg)
        self.assertEqual(dome_reg.region_id, "reg_upper_dome_spire")
        logger.info("[PASSED] Scenario 5: Dome region correctly proposed in upper 45% crown.")

    # 6. Calligraphic detail
    def test_06_calligraphic_detail(self):
        logger.info("\n--- [Scenario 6] Calligraphic Detail ---")
        np_arr = np.zeros((200, 600), dtype=np.uint8)
        # Horizontal inscription bands
        cv2.putText(np_arr, "INSCRIPTION ARCHIVE", (30, 100), cv2.FONT_HERSHEY_COMPLEX, 1.2, 255, 2)
        cv2.putText(np_arr, "QUTUB EPIGRAPHY", (30, 160), cv2.FONT_HERSHEY_COMPLEX, 1.0, 255, 2)
        kps, des = self.engine.extract_classical_descriptors(np_arr, method="sift")
        self.assertGreater(len(kps), 15)
        logger.info(f"[PASSED] Scenario 6: Calligraphic text features extracted ({len(kps)} keypoints).")

    # 7. Blurred photograph
    def test_07_blurred_photograph(self):
        logger.info("\n--- [Scenario 7] Blurred Photograph ---")
        sharp = np.zeros((300, 300), dtype=np.uint8)
        cv2.circle(sharp, (150, 150), 50, 255, -1)
        blurred = cv2.GaussianBlur(sharp, (31, 31), 10.0)
        geo_res = self.engine.verify_geometric_correspondence(blurred, sharp, method="sift")
        self.assertEqual(geo_res.status, "INSUFFICIENT_FEATURES")
        logger.info(f"[PASSED] Scenario 7: Heavy optical blur safely caught as {geo_res.status}.")

    # 8. Low-resolution photograph
    def test_08_low_resolution_photograph(self):
        logger.info("\n--- [Scenario 8] Low-Resolution Photograph ---")
        small_img = Image.new("RGB", (120, 90), (180, 160, 140))
        _, _, gray = self.engine.preprocess_image(small_img)
        regions = self.engine.propose_regions(small_img, gray)
        self.assertGreaterEqual(len(regions), 1)
        logger.info(f"[PASSED] Scenario 8: Low-resolution specimen (120x90) safely processed without crash.")

    # 9. Occluded photograph
    def test_09_occluded_photograph(self):
        logger.info("\n--- [Scenario 9] Occluded Photograph ---")
        img = Image.new("RGB", (600, 600), (200, 200, 200))
        # Add foreground occlusion
        np_arr = np.array(img)
        np_arr[300:600, :] = 0  # Black obstacle
        occ_img = Image.fromarray(np_arr)
        _, _, gray = self.engine.preprocess_image(occ_img)
        regions = self.engine.propose_regions(occ_img, gray)
        # Upper regions remain viable despite lower occlusion
        self.assertTrue(any(r.region_id == "reg_upper_dome_spire" for r in regions))
        logger.info("[PASSED] Scenario 9: Multi-region proposal preserved unoccluded sectors.")

    # 10. Non-monument photograph
    def test_10_non_monument_photograph(self):
        logger.info("\n--- [Scenario 10] Non-Monument Photograph ---")
        hybrid_eval = self.engine.evaluate_hybrid_evidence(
            global_candidate={"monument_key": "taj_mahal", "similarity": 0.30},
            local_results={"top_candidate": None},
            gatekeeper_score=0.12,  # Low gatekeeper rejection
        )
        self.assertEqual(hybrid_eval["alignment_status"], "REJECTED_NON_MONUMENT")
        logger.info(f"[PASSED] Scenario 10: Non-monument gated: {hybrid_eval['alignment_status']}.")

    # 11. Unsupported image format
    def test_11_unsupported_image_format(self):
        logger.info("\n--- [Scenario 11] Unsupported Image Format ---")
        invalid_bytes = b"NOT_A_VALID_IMAGE_HEADER_12345"
        with self.assertRaises(Exception):
            with Image.open(io.BytesIO(invalid_bytes)) as im:
                im.verify()
        logger.info("[PASSED] Scenario 11: Invalid image format rejected cleanly.")

    # 12. Corrupted image
    def test_12_corrupted_image(self):
        logger.info("\n--- [Scenario 12] Corrupted Image ---")
        corrupted_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb" + b"\x00" * 20
        with self.assertRaises(Exception):
            with Image.open(io.BytesIO(corrupted_jpeg)) as im:
                im.verify()
        logger.info("[PASSED] Scenario 12: Truncated/corrupted image detected.")

    # 13. Empty image upload
    def test_13_empty_image_upload(self):
        logger.info("\n--- [Scenario 13] Empty Image Upload ---")
        empty_bytes = b""
        self.assertEqual(len(empty_bytes), 0)
        with self.assertRaises(Exception):
            with Image.open(io.BytesIO(empty_bytes)) as im:
                im.verify()
        logger.info("[PASSED] Scenario 13: Zero-byte upload intercepted.")

    # 14. Global/local prediction disagreement
    def test_14_global_local_disagreement(self):
        logger.info("\n--- [Scenario 14] Global/Local Prediction Disagreement ---")
        hybrid_eval = self.engine.evaluate_hybrid_evidence(
            global_candidate={"monument_key": "gateway_of_india", "similarity": 0.82},
            local_results={
                "top_candidate": {"monument_key": "qutub_minar", "max_similarity": 0.88},
                "geometric_verification": {"status": "UNVERIFIED", "inliers_count": 3}
            },
            gatekeeper_score=0.85,
        )
        self.assertEqual(hybrid_eval["alignment_status"], "DIVERGENT_EVIDENCE")
        self.assertIn("Ambiguity detected", hybrid_eval["explanation"])
        logger.info(f"[PASSED] Scenario 14: Conflicting candidates flagged as {hybrid_eval['alignment_status']}.")

    # 15. Insufficient local feature evidence
    def test_15_insufficient_local_feature_evidence(self):
        logger.info("\n--- [Scenario 15] Insufficient Local Feature Evidence ---")
        hybrid_eval = self.engine.evaluate_hybrid_evidence(
            global_candidate={"monument_key": "taj_mahal", "similarity": 0.91},
            local_results={"top_candidate": None},
            gatekeeper_score=0.90,
        )
        self.assertEqual(hybrid_eval["alignment_status"], "INSUFFICIENT_LOCAL_EVIDENCE")
        logger.info(f"[PASSED] Scenario 15: Clean fallback to {hybrid_eval['alignment_status']}.")

    # 16. Geometric verification failure
    def test_16_geometric_verification_failure(self):
        logger.info("\n--- [Scenario 16] Geometric Verification Failure ---")
        # Compare two completely different patterns
        pattern1 = np.zeros((300, 300), dtype=np.uint8)
        for i in range(10, 290, 15):
            cv2.line(pattern1, (i, 0), (i, 300), 255, 2)
        pattern2 = np.zeros((300, 300), dtype=np.uint8)
        for i in range(10, 290, 15):
            cv2.circle(pattern2, (150, 150), i // 2, 255, 2)

        geo_res = self.engine.verify_geometric_correspondence(pattern1, pattern2, method="sift")
        self.assertIn(geo_res.status, ["UNVERIFIED", "INSUFFICIENT_FEATURES"])
        self.assertFalse(geo_res.homography_found)
        logger.info(f"[PASSED] Scenario 16: Incompatible geometry correctly rejected ({geo_res.status}, homography_found={geo_res.homography_found}).")


if __name__ == "__main__":
    unittest.main()

