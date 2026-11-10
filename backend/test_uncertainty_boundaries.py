"""
Phase 14.3 — Uncertainty Policy Boundary & Invariant Test Suite
Rigorously tests:
1. Exact boundary values around gk=0.35, gk=0.45, sim=0.70
2. Invalid, NaN, and Infinite score inputs
3. Competing candidates margin invariants
4. Geodetic conflict invariants
5. Image quality (blur, underexposure) invariants
6. Macro architectural details and occlusions
7. High-confidence verified matches
"""

import math
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from calibration import CalibrationEngine
from uncertainty import (
    DecisionState,
    GPSEvidence,
    ImageQualityMetrics,
    ReasonCode,
    UncertaintyEngine,
)


def run_boundary_tests():
    print("=" * 80)
    print("RUNNING PHASE 14.3 UNCERTAINTY POLICY BOUNDARY & INVARIANT AUDIT")
    print("=" * 80)

    calib = CalibrationEngine()
    engine = UncertaintyEngine(calib)

    # Dummy quality and GPS fixtures
    pass_quality = ImageQualityMetrics(
        width=500,
        height=500,
        total_pixels=250000,
        is_low_resolution=False,
        blur_score=120.0,
        is_blurry=False,
        mean_brightness=128.0,
        is_underexposed=False,
        is_overexposed=False,
        passed_quality_check=True,
    )

    blur_quality = ImageQualityMetrics(
        width=500,
        height=500,
        total_pixels=250000,
        is_low_resolution=False,
        blur_score=15.0,
        is_blurry=True,
        mean_brightness=128.0,
        is_underexposed=False,
        is_overexposed=False,
        passed_quality_check=False,
        notes=["Severe blur"],
    )

    underexposed_quality = ImageQualityMetrics(
        width=500,
        height=500,
        total_pixels=250000,
        is_low_resolution=False,
        blur_score=100.0,
        is_blurry=False,
        mean_brightness=10.0,
        is_underexposed=True,
        is_overexposed=False,
        passed_quality_check=False,
        notes=["Severe underexposure"],
    )

    no_gps = GPSEvidence(
        has_gps=False,
        coordinates=None,
        distance_km=None,
        is_consistent=True,
        geo_boost_applied=False,
        gps_conflict=False,
        note="No GPS metadata in EXIF stream.",
    )

    conflict_gps = GPSEvidence(
        has_gps=True,
        coordinates={"lat": 12.0, "lng": 77.0},
        distance_km=1250.0,
        is_consistent=False,
        geo_boost_applied=False,
        gps_conflict=True,
        note="Geodetic anomaly: 1250 km from candidate coordinates.",
    )

    test_cases = [
        # -------------------------------------------------------------
        # Group A: Exact Threshold Boundaries
        # -------------------------------------------------------------
        # Case A1: gk = 0.35, sim = 0.6999 (At or below rejection threshold -> Hard Reject)
        {
            "name": "Case A1: gk = 0.3500, sim = 0.6999 (gk <= 0.35, sim < 0.70)",
            "gk": 0.3500,
            "top1_sim": 0.6999,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.NON_MONUMENT_REJECTED,
        },
        # Case A2: gk = 0.3501, sim = 0.6999 (Just above 0.35 -> Quarantine to Review)
        {
            "name": "Case A2: gk = 0.3501, sim = 0.6999 (0.35 < gk < 0.45, sim < 0.70)",
            "gk": 0.3501,
            "top1_sim": 0.6999,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        # Case A3: gk = 0.4499, sim = 0.6999 (Just below 0.45 -> Quarantine to Review)
        {
            "name": "Case A3: gk = 0.4499, sim = 0.6999 (0.35 < gk < 0.45, sim < 0.70)",
            "gk": 0.4499,
            "top1_sim": 0.6999,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        # Case A4: gk = 0.4500, sim = 0.6999 (At ambiguous threshold -> Unknown Heritage Specimen)
        {
            "name": "Case A4: gk = 0.4500, sim = 0.6999 (gk >= 0.45, sim < 0.75)",
            "gk": 0.4500,
            "top1_sim": 0.6999,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.UNKNOWN_HERITAGE_SPECIMEN,
        },
        # Case A5: gk = 0.3500, sim = 0.7000 (At sim threshold -> Does NOT meet sim < 0.70, gk marginal -> Review)
        {
            "name": "Case A5: gk = 0.3500, sim = 0.7000 (sim >= 0.70, gk < 0.55)",
            "gk": 0.3500,
            "top1_sim": 0.7000,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        # Case A6: gk = 0.3501, sim = 0.7000 (Just above 0.35, sim = 0.70 -> Review)
        {
            "name": "Case A6: gk = 0.3501, sim = 0.7000 (sim >= 0.70, gk < 0.55)",
            "gk": 0.3501,
            "top1_sim": 0.7000,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        # Case A7: gk = 0.4500, sim = 0.7600, margin = 0.01 (sim >= 0.75, gk >= 0.45, margin < 0.08 -> Uncertain Match)
        {
            "name": "Case A7: gk = 0.4500, sim = 0.7600, margin = 0.01 (< 0.08)",
            "gk": 0.4500,
            "top1_sim": 0.7600,
            "margin": 0.01,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.UNCERTAIN_MATCH,
        },
        # Case A8: gk = 0.5500, sim = 0.8000, margin = 0.10 (Strong verified match)
        {
            "name": "Case A8: gk = 0.5500, sim = 0.8000, margin = 0.10 (Verified)",
            "gk": 0.5500,
            "top1_sim": 0.8000,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.VERIFIED_MATCH,
        },

        # -------------------------------------------------------------
        # Group B: Invalid, NaN, and Infinite Score Inputs
        # -------------------------------------------------------------
        {
            "name": "Case B1: gk = NaN, sim = 0.60 (Safeguard -> Review)",
            "gk": float("nan"),
            "top1_sim": 0.60,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        {
            "name": "Case B2: gk = 0.60, sim = NaN (Safeguard -> Review)",
            "gk": 0.60,
            "top1_sim": float("nan"),
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        {
            "name": "Case B3: gk = Inf, sim = 0.80 (Safeguard -> Review)",
            "gk": float("inf"),
            "top1_sim": 0.80,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        {
            "name": "Case B4: gk = -1.0, sim = 0.50 (Negative gk -> Hard Reject)",
            "gk": -1.0,
            "top1_sim": 0.50,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.NON_MONUMENT_REJECTED,
        },
        {
            "name": "Case B5: gk = 2.0, sim = 0.60 (High gk, low sim -> Unknown Heritage)",
            "gk": 2.0,
            "top1_sim": 0.60,
            "margin": 0.10,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.UNKNOWN_HERITAGE_SPECIMEN,
        },

        # -------------------------------------------------------------
        # Group C: Invariant Preservation
        # -------------------------------------------------------------
        # Invariant C1: Competing candidates with high similarity
        {
            "name": "Case C1: gk = 0.75, sim = 0.90, margin = 0.02 (< 0.05) -> UNCERTAIN_MATCH",
            "gk": 0.75,
            "top1_sim": 0.90,
            "margin": 0.02,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.UNCERTAIN_MATCH,
        },
        # Invariant C2: Geodetic conflict with high similarity
        {
            "name": "Case C2: gk = 0.85, sim = 0.92, GPS conflict (1250 km) -> REVIEW_REQUIRED",
            "gk": 0.85,
            "top1_sim": 0.92,
            "margin": 0.15,
            "gps": conflict_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        # Invariant C3: Severe blur on potential monument
        {
            "name": "Case C3: gk = 0.70, sim = 0.82, Image Blurry -> REVIEW_REQUIRED",
            "gk": 0.70,
            "top1_sim": 0.82,
            "margin": 0.10,
            "gps": no_gps,
            "quality": blur_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        # Invariant C4: Severe underexposure on potential monument
        {
            "name": "Case C4: gk = 0.70, sim = 0.82, Image Underexposed -> REVIEW_REQUIRED",
            "gk": 0.70,
            "top1_sim": 0.82,
            "margin": 0.10,
            "gps": no_gps,
            "quality": underexposed_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
        # Invariant C5: Macro architectural detail (e.g. Sanchi Torana detail: gk=0.38, sim=0.68)
        {
            "name": "Case C5: Architectural detail (gk = 0.38, sim = 0.68) -> REVIEW_REQUIRED (Never Rejected)",
            "gk": 0.3800,
            "top1_sim": 0.6800,
            "margin": 0.08,
            "gps": no_gps,
            "quality": pass_quality,
            "expected": DecisionState.REVIEW_REQUIRED,
        },
    ]

    passed = 0
    failed = 0

    for tc in test_cases:
        reason_codes: List[str] = []
        top2_sim = round(tc["top1_sim"] - tc["margin"], 4) if not math.isnan(tc["top1_sim"]) else 0.0
        dec = engine._arbitrate_decision(
            top1_sim=tc["top1_sim"],
            top2_sim=top2_sim,
            margin=tc["margin"],
            gatekeeper_score=tc["gk"],
            gps=tc["gps"],
            quality=tc["quality"],
            sim_threshold=calib.confidence_threshold,
            margin_threshold=calib.uncertainty_margin_threshold,
            gatekeeper_verified=calib.gatekeeper_threshold_verified,
            gatekeeper_ambiguous=calib.gatekeeper_threshold_ambiguous,
            gatekeeper_rejection=calib.gatekeeper_threshold_rejection,
            reason_codes=reason_codes,
        )

        status_str = "PASS" if dec == tc["expected"] else "FAIL"
        if dec == tc["expected"]:
            passed += 1
            print(f" [PASS] {tc['name']} -> {dec.value}")
        else:
            failed += 1
            print(f" [FAIL] {tc['name']} -> Got {dec.value}, Expected {tc['expected'].value}")

    print("-" * 80)
    print(f"SUMMARY: {passed} PASSED, {failed} FAILED out of {len(test_cases)} boundary tests.")
    print("=" * 80)
    assert failed == 0, f"{failed} boundary tests failed!"
    print("ALL BOUNDARY & INVARIANT TESTS COMPLIED WITH 100% PRECISION!")


if __name__ == "__main__":
    run_boundary_tests()
