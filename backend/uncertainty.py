"""
Heritage & Monument Recognition System - Advanced Uncertainty & Decision Engine
Project No. 30 (SIH 2025 – SIH25052): Phase 6.2

Integrates:
- FAISS multi-candidate unique-monument aggregation (prevents intra-monument anchor margin collapse)
- Zero-Shot Architectural Gatekeeper evidence
- EXIF GPS geodetic validation & conflict detection
- Image quality inspection (resolution, Laplacian blur variance, underexposure/overexposure)
- Explicit 5-state Decision Engine:
    1. VERIFIED_MATCH
    2. UNCERTAIN_MATCH
    3. UNKNOWN_HERITAGE_SPECIMEN
    4. NON_MONUMENT_REJECTED
    5. REVIEW_REQUIRED
- Grounded reason codes & human-in-the-loop review triggering
"""

import enum
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from calibration import CalibrationEngine

logger = logging.getLogger("uncertainty_engine")


class DecisionState(str, enum.Enum):
    VERIFIED_MATCH = "VERIFIED_MATCH"
    UNCERTAIN_MATCH = "UNCERTAIN_MATCH"
    UNKNOWN_HERITAGE_SPECIMEN = "UNKNOWN_HERITAGE_SPECIMEN"
    NON_MONUMENT_REJECTED = "NON_MONUMENT_REJECTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ReasonCode(str, enum.Enum):
    HIGH_CONFIDENCE_MATCH = "HIGH_CONFIDENCE_MATCH"
    LOW_RETRIEVAL_SIMILARITY = "LOW_RETRIEVAL_SIMILARITY"
    AMBIGUOUS_TOP_CANDIDATES = "AMBIGUOUS_TOP_CANDIDATES"
    LOW_GATEKEEPER_CONFIDENCE = "LOW_GATEKEEPER_CONFIDENCE"
    GATEKEEPER_AMBIGUOUS = "GATEKEEPER_AMBIGUOUS"
    MISSING_GPS = "MISSING_GPS"
    GPS_CONFLICT = "GPS_CONFLICT"
    GEO_VERIFIED = "GEO_VERIFIED"
    LOW_IMAGE_QUALITY = "LOW_IMAGE_QUALITY"
    UNCALIBRATED_MODEL = "UNCALIBRATED_MODEL"
    CALIBRATED_CONFIDENCE = "CALIBRATED_CONFIDENCE"


# --- Pydantic Data Models ---

class ImageQualityMetrics(BaseModel):
    width: int
    height: int
    total_pixels: int
    is_low_resolution: bool
    blur_score: float
    is_blurry: bool
    mean_brightness: float
    is_underexposed: bool
    is_overexposed: bool
    passed_quality_check: bool
    notes: List[str] = Field(default_factory=list)


class GPSEvidence(BaseModel):
    has_gps: bool
    coordinates: Optional[Dict[str, float]] = None
    distance_km: Optional[float] = None
    is_consistent: Optional[bool] = None
    geo_boost_applied: bool = False
    gps_conflict: bool = False
    note: str


class AggregatedCandidate(BaseModel):
    monument_key: str
    monument_name: str
    max_similarity: float
    matched_anchor_source: str
    is_centroid_match: bool


class UncertaintyResult(BaseModel):
    decision: DecisionState
    top1_similarity: float
    top2_similarity: float
    similarity_margin: float
    margin_threshold: float = 0.08
    calibrated_probability: Optional[float] = None
    calibration_status: str
    gatekeeper_score: float
    gps_evidence: GPSEvidence
    image_quality: ImageQualityMetrics
    reason_codes: List[str]
    requires_human_review: bool
    explanation: str
    top_candidates: List[AggregatedCandidate] = Field(default_factory=list)


# --- Helper Image & Geodetic Calculations ---

def compute_haversine_distance_km(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """Calculates the great-circle distance between two geodetic coordinates in km."""
    r_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_km * c


def inspect_image_quality(
    image: Image.Image, config: Dict[str, Any]
) -> ImageQualityMetrics:
    """
    Evaluates image resolution, Laplacian focus/blur variance, and luminance exposure.
    """
    w, h = image.size
    total_pixels = w * h

    min_dim = int(config.get("min_dimension", 200))
    min_pixels = int(config.get("min_total_pixels", 60000))
    blur_thresh = float(config.get("blur_laplacian_threshold", 35.0))
    exp_low = float(config.get("exposure_low_threshold", 25.0))
    exp_high = float(config.get("exposure_high_threshold", 230.0))

    is_low_res = (w < min_dim) or (h < min_dim) or (total_pixels < min_pixels)

    # Convert to grayscale array for blur and luminance checks
    gray = np.array(image.convert("L"), dtype=np.float32)

    # Laplacian kernel variance via discrete 2D convolution
    # Kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    if gray.shape[0] >= 3 and gray.shape[1] >= 3:
        # Fast discrete Laplacian convolution
        laplacian = (
            gray[:-2, 1:-1]
            + gray[2:, 1:-1]
            + gray[1:-1, :-2]
            + gray[1:-1, 2:]
            - 4.0 * gray[1:-1, 1:-1]
        )
        blur_score = float(np.var(laplacian))
    else:
        blur_score = 0.0

    is_blurry = blur_score < blur_thresh

    # Exposure luminance distribution
    mean_brightness = float(np.mean(gray))
    is_underexposed = mean_brightness < exp_low
    is_overexposed = mean_brightness > exp_high

    notes = []
    if is_low_res:
        notes.append(f"Low resolution ({w}x{h} px). Minimum required: {min_dim}x{min_dim}.")
    if is_blurry:
        notes.append(f"Image exhibits high blur or lack of edge detail (Laplacian var {blur_score:.1f} < {blur_thresh}).")
    if is_underexposed:
        notes.append(f"Severe underexposure detected (Mean luminance {mean_brightness:.1f} < {exp_low}).")
    if is_overexposed:
        notes.append(f"Severe overexposure detected (Mean luminance {mean_brightness:.1f} > {exp_high}).")

    passed = not (is_low_res or is_blurry or is_underexposed or is_overexposed)

    return ImageQualityMetrics(
        width=w,
        height=h,
        total_pixels=total_pixels,
        is_low_resolution=is_low_res,
        blur_score=round(blur_score, 2),
        is_blurry=is_blurry,
        mean_brightness=round(mean_brightness, 2),
        is_underexposed=is_underexposed,
        is_overexposed=is_overexposed,
        passed_quality_check=passed,
        notes=notes,
    )


# --- Uncertainty Engine Class ---

class UncertaintyEngine:
    """
    Evaluates multimodal evidence for heritage recognition, enforcing
    calibrated thresholds and anti-hallucination guardrails.
    """

    def __init__(self, calibration_engine: Optional[CalibrationEngine] = None):
        self.calibration = calibration_engine or CalibrationEngine()

    def aggregate_faiss_candidates(
        self,
        raw_distances: np.ndarray,
        raw_indices: np.ndarray,
        labels: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        top_k: int = 5,
    ) -> List[AggregatedCandidate]:
        """
        CRITICAL REQUIREMENT:
        Aggregates FAISS search hits by UNIQUE MONUMENT ID before calculating margins.
        Prevents comparing two different anchors belonging to the same monument.
        """
        monument_best: Dict[str, Dict[str, Any]] = {}

        dists = raw_distances[0] if getattr(raw_distances, "ndim", 1) == 2 else raw_distances
        indices = raw_indices[0] if getattr(raw_indices, "ndim", 1) == 2 else raw_indices

        for dist, idx in zip(dists, indices):
            if int(idx) == -1 or int(idx) >= len(labels):
                continue
            record = labels[int(idx)]
            m_key = record["monument_key"]
            sim = float(dist)

            if m_key not in monument_best or sim > monument_best[m_key]["similarity"]:
                monument_best[m_key] = {
                    "similarity": sim,
                    "monument_name": record.get("monument_name")
                    or metadata.get(m_key, {}).get("monument_name", m_key),
                    "source": record.get("source", "unknown"),
                    "is_centroid": record.get("is_centroid", False),
                }

        # Sort descending by similarity
        sorted_items = sorted(
            monument_best.items(), key=lambda kv: kv[1]["similarity"], reverse=True
        )[:top_k]

        aggregated: List[AggregatedCandidate] = []
        for m_key, data in sorted_items:
            aggregated.append(
                AggregatedCandidate(
                    monument_key=m_key,
                    monument_name=data["monument_name"],
                    max_similarity=round(data["similarity"], 4),
                    matched_anchor_source=data["source"],
                    is_centroid_match=data["is_centroid"],
                )
            )

        return aggregated

    def evaluate(
        self,
        image: Image.Image,
        gatekeeper_score: float,
        raw_distances: np.ndarray,
        raw_indices: np.ndarray,
        labels: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        exif_gps: Optional[Dict[str, Any]] = None,
        local_feature_corroboration: Optional[Dict[str, Any]] = None,
    ) -> UncertaintyResult:
        """
        Executes comprehensive evidence synthesis across:
        1. Unique-monument aggregated FAISS retrieval (top-1, top-2, margin).
        2. Zero-shot gatekeeper architectural score.
        3. EXIF GPS proximity or conflict.
        4. Image quality inspection.
        5. Calibration status & calibrated probability.
        """
        # 1. Image Quality Assessment
        quality_cfg = self.calibration.image_quality_config
        quality = inspect_image_quality(image, quality_cfg)

        # 2. FAISS Unique-Monument Aggregation
        candidates = self.aggregate_faiss_candidates(
            raw_distances=raw_distances,
            raw_indices=raw_indices,
            labels=labels,
            metadata=metadata,
            top_k=5,
        )

        top1 = candidates[0] if len(candidates) > 0 else None
        top2 = candidates[1] if len(candidates) > 1 else None

        top1_sim = top1.max_similarity if top1 else 0.0
        top2_sim = top2.max_similarity if top2 else 0.0
        similarity_margin = round(top1_sim - top2_sim, 4)

        # 3. GPS Evidence Assessment
        gps_evidence = self._evaluate_gps(exif_gps, top1, metadata)

        # 4. Calibration Assessment
        calibrated_prob = self.calibration.calibrate_similarity(
            similarity=top1_sim,
            margin=similarity_margin,
            gatekeeper=gatekeeper_score,
            quality=1.0 if quality.passed_quality_check else 0.0,
            sift_inliers=10 if quality.passed_quality_check else 0,
            agreement=1.0 if (gatekeeper_score >= 0.5 and similarity_margin >= 0.05) else 0.0,
        )
        calib_status = self.calibration.calibration_status

        # 5. Threshold Definitions from Config
        sim_threshold = self.calibration.confidence_threshold
        margin_threshold = self.calibration.uncertainty_margin_threshold
        gatekeeper_verified = self.calibration.gatekeeper_threshold_verified
        gatekeeper_ambiguous = self.calibration.gatekeeper_threshold_ambiguous

        # 6. Synthesize Reason Codes & Decision State
        reason_codes: List[str] = []

        if calib_status == "UNCALIBRATED":
            reason_codes.append(ReasonCode.UNCALIBRATED_MODEL.value)
        else:
            reason_codes.append(ReasonCode.CALIBRATED_CONFIDENCE.value)

        if not quality.passed_quality_check:
            reason_codes.append(ReasonCode.LOW_IMAGE_QUALITY.value)

        if not gps_evidence.has_gps:
            reason_codes.append(ReasonCode.MISSING_GPS.value)
        elif gps_evidence.geo_boost_applied:
            reason_codes.append(ReasonCode.GEO_VERIFIED.value)
        elif gps_evidence.gps_conflict:
            reason_codes.append(ReasonCode.GPS_CONFLICT.value)

        # Decision State Arbitration
        decision = self._arbitrate_decision(
            top1_sim=top1_sim,
            top2_sim=top2_sim,
            margin=similarity_margin,
            gatekeeper_score=gatekeeper_score,
            gps=gps_evidence,
            quality=quality,
            sim_threshold=sim_threshold,
            margin_threshold=margin_threshold,
            gatekeeper_verified=gatekeeper_verified,
            gatekeeper_ambiguous=gatekeeper_ambiguous,
            reason_codes=reason_codes,
            top1_key=top1.monument_key if top1 else None,
            local_corroboration=local_feature_corroboration,
        )

        requires_review = decision in [
            DecisionState.UNCERTAIN_MATCH,
            DecisionState.UNKNOWN_HERITAGE_SPECIMEN,
            DecisionState.REVIEW_REQUIRED,
        ]

        explanation = self._generate_explanation(
            decision=decision,
            top1=top1,
            top2=top2,
            top1_sim=top1_sim,
            top2_sim=top2_sim,
            margin=similarity_margin,
            gatekeeper_score=gatekeeper_score,
            gps=gps_evidence,
            quality=quality,
            calibrated_prob=calibrated_prob,
            calib_status=calib_status,
        )

        return UncertaintyResult(
            decision=decision,
            top1_similarity=top1_sim,
            top2_similarity=top2_sim,
            similarity_margin=similarity_margin,
            margin_threshold=round(margin_threshold, 4),
            calibrated_probability=calibrated_prob,
            calibration_status=calib_status,
            gatekeeper_score=round(gatekeeper_score, 4),
            gps_evidence=gps_evidence,
            image_quality=quality,
            reason_codes=reason_codes,
            requires_human_review=requires_review,
            explanation=explanation,
            top_candidates=candidates,
        )

    def _evaluate_gps(
        self,
        exif_gps: Optional[Dict[str, Any]],
        top1: Optional[AggregatedCandidate],
        metadata: Dict[str, Any],
    ) -> GPSEvidence:
        """Evaluates EXIF GPS evidence with proximity boost or distance conflict detection."""
        if not exif_gps or "lat" not in exif_gps or "lng" not in exif_gps:
            return GPSEvidence(
                has_gps=False,
                coordinates=None,
                distance_km=None,
                is_consistent=None,
                geo_boost_applied=False,
                gps_conflict=False,
                note="EXIF GPS metadata not found in specimen image. Processing proceeds via visual embeddings.",
            )

        coords = {"lat": float(exif_gps["lat"]), "lng": float(exif_gps["lng"])}

        if not top1 or top1.monument_key not in metadata:
            return GPSEvidence(
                has_gps=True,
                coordinates=coords,
                distance_km=None,
                is_consistent=None,
                geo_boost_applied=False,
                gps_conflict=False,
                note=f"EXIF GPS located at ({coords['lat']:.4f}, {coords['lng']:.4f}), but candidate coordinates are unindexed.",
            )

        cand_coords = metadata[top1.monument_key].get("coordinates")
        if not cand_coords or "lat" not in cand_coords or "lng" not in cand_coords:
            return GPSEvidence(
                has_gps=True,
                coordinates=coords,
                distance_km=None,
                is_consistent=None,
                geo_boost_applied=False,
                gps_conflict=False,
                note="Candidate monument coordinates not recorded in metadata registry.",
            )

        dist_km = compute_haversine_distance_km(
            coords["lat"], coords["lng"], cand_coords["lat"], cand_coords["lng"]
        )

        boost_thresh = self.calibration.geo_boost_distance_km
        conflict_thresh = self.calibration.geo_conflict_distance_km

        geo_boost = dist_km <= boost_thresh
        gps_conflict = dist_km > conflict_thresh

        if geo_boost:
            note = f"Geodetic Proximity Verified: Photograph coordinates are within {dist_km:.2f} km of {top1.monument_name}."
        elif gps_conflict:
            note = (
                f"Geodetic Anomaly: Photograph EXIF GPS coordinates are {dist_km:.1f} km from {top1.monument_name} "
                f"(exceeds consistency threshold of {conflict_thresh:.0f} km)."
            )
        else:
            note = f"EXIF GPS detected: {dist_km:.1f} km from {top1.monument_name} coordinates."

        return GPSEvidence(
            has_gps=True,
            coordinates=coords,
            distance_km=round(dist_km, 2),
            is_consistent=not gps_conflict,
            geo_boost_applied=geo_boost,
            gps_conflict=gps_conflict,
            note=note,
        )

    def _arbitrate_decision(
        self,
        top1_sim: float,
        top2_sim: float,
        margin: float,
        gatekeeper_score: float,
        gps: GPSEvidence,
        quality: ImageQualityMetrics,
        sim_threshold: float,
        margin_threshold: float,
        gatekeeper_verified: float,
        gatekeeper_ambiguous: float,
        reason_codes: List[str],
        top1_key: Optional[str] = None,
        local_corroboration: Optional[Dict[str, Any]] = None,
    ) -> DecisionState:
        """
        Deterministic, transparent arbitration across the 5 decision states.
        """
        # RULE 1: Severe Non-Monument Rejection
        # Low architectural gatekeeper and low vector similarity
        if gatekeeper_score < gatekeeper_ambiguous and top1_sim < 0.70:
            reason_codes.append(ReasonCode.LOW_GATEKEEPER_CONFIDENCE.value)
            return DecisionState.NON_MONUMENT_REJECTED

        # RULE 2: Review Required on Geodetic Conflict or Severe Image Quality Degradation
        # High visual similarity but location contradicts by > 150 km
        if gps.gps_conflict and top1_sim >= 0.75:
            return DecisionState.REVIEW_REQUIRED

        # Severe quality failure (extreme blur / pitch black) on potential monument
        if not quality.passed_quality_check and gatekeeper_score >= gatekeeper_ambiguous:
            if quality.is_blurry or quality.is_underexposed:
                return DecisionState.REVIEW_REQUIRED

        # Conflicting gatekeeper vs similarity (high similarity but very low gatekeeper)
        if top1_sim >= sim_threshold and gatekeeper_score < gatekeeper_ambiguous:
            reason_codes.append(ReasonCode.LOW_GATEKEEPER_CONFIDENCE.value)
            return DecisionState.REVIEW_REQUIRED

        # RULE 3: Verified Match
        # High gatekeeper, high similarity (or geo-boosted), and decisive margin
        effective_sim_threshold = sim_threshold - 0.08 if gps.geo_boost_applied else sim_threshold

        # High-confidence corroboration for narrowly missed margin (e.g. Qutub Minar vs Charminar):
        # When Top-1 candidate has exceptionally high visual similarity (>= 0.90),
        # strong gatekeeper evidence (>= 0.70), no GPS conflict,
        # the margin narrowly misses the threshold (margin >= 0.065),
        # AND local architectural feature agreement confirms the candidate:
        is_narrowly_missed_margin = (
            margin >= (margin_threshold - 0.015)
            and top1_sim >= 0.90
            and gatekeeper_score >= 0.70
            and not gps.gps_conflict
        )
        has_local_agreement = False
        if local_corroboration:
            align_status = local_corroboration.get("alignment_status")
            local_cand = local_corroboration.get("top_local_candidate")
            local_key = local_cand.get("monument_key") if isinstance(local_cand, dict) else None
            if (
                align_status in ["AGREEMENT_CONFIRMED_VISUAL", "AGREEMENT_CONFIRMED_GEOMETRIC"]
                and (local_key is None or local_key == top1_key)
            ):
                has_local_agreement = True

        if (
            gatekeeper_score >= gatekeeper_verified
            and top1_sim >= effective_sim_threshold
            and not gps.gps_conflict
            and (margin >= margin_threshold or (is_narrowly_missed_margin and has_local_agreement))
        ):
            reason_codes.append(ReasonCode.HIGH_CONFIDENCE_MATCH.value)
            return DecisionState.VERIFIED_MATCH

        # RULE 4: Uncertain Match (Candidate Competition)
        # Top-1 candidate meets catalog similarity threshold, but margin to Top-2 is too narrow
        if (
            gatekeeper_score >= gatekeeper_ambiguous
            and top1_sim >= effective_sim_threshold
            and margin < margin_threshold
        ):
            reason_codes.append(ReasonCode.AMBIGUOUS_TOP_CANDIDATES.value)
            return DecisionState.UNCERTAIN_MATCH

        # RULE 5: Unknown Heritage Specimen
        # Architecture detected, but similarity to all indexed monuments is low
        if gatekeeper_score >= gatekeeper_ambiguous and top1_sim < effective_sim_threshold:
            reason_codes.append(ReasonCode.LOW_RETRIEVAL_SIMILARITY.value)
            return DecisionState.UNKNOWN_HERITAGE_SPECIMEN

        # Gatekeeper marginal
        if gatekeeper_score < gatekeeper_verified:
            reason_codes.append(ReasonCode.GATEKEEPER_AMBIGUOUS.value)
            return DecisionState.REVIEW_REQUIRED

        return DecisionState.REVIEW_REQUIRED

    def _generate_explanation(
        self,
        decision: DecisionState,
        top1: Optional[AggregatedCandidate],
        top2: Optional[AggregatedCandidate],
        top1_sim: float,
        top2_sim: float,
        margin: float,
        gatekeeper_score: float,
        gps: GPSEvidence,
        quality: ImageQualityMetrics,
        calibrated_prob: Optional[float],
        calib_status: str,
    ) -> str:
        """Constructs an editorial curatorial explanation."""
        top1_name = top1.monument_name if top1 else "None"
        top2_name = top2.monument_name if top2 else "None"

        if decision == DecisionState.VERIFIED_MATCH:
            geo_note = " with geodetic GPS verification" if gps.geo_boost_applied else ""
            if margin < self.calibration.uncertainty_margin_threshold:
                return (
                    f"Specimen verified as {top1_name}{geo_note}. "
                    f"Vector cosine alignment is exceptionally strong ({top1_sim:.4f}) and corroborated by "
                    f"local architectural feature agreement (margin: {margin:.4f} over {top2_name}). "
                    f"Architectural Gatekeeper score is {gatekeeper_score * 100:.1f}%."
                )
            return (
                f"Specimen verified as {top1_name}{geo_note}. "
                f"Vector cosine alignment is strong ({top1_sim:.4f}) with a decisive margin of {margin:.4f} "
                f"over {top2_name} ({top2_sim:.4f}). Architectural Gatekeeper score is {gatekeeper_score * 100:.1f}%."
            )

        if decision == DecisionState.UNCERTAIN_MATCH:
            return (
                f"Ambiguous attribution: Close competition between {top1_name} (sim: {top1_sim:.4f}) "
                f"and {top2_name} (sim: {top2_sim:.4f}) with a narrow margin of {margin:.4f} "
                f"(below threshold of {self.calibration.uncertainty_margin_threshold:.2f}). "
                "Classified as Uncertain Match to avoid forced attribution; flagged for human curator review."
            )

        if decision == DecisionState.UNKNOWN_HERITAGE_SPECIMEN:
            return (
                f"Heritage architecture verified by Gatekeeper ({gatekeeper_score * 100:.1f}%), "
                f"but similarity to all cataloged monuments fell below threshold "
                f"(Nearest: {top1_name} at {top1_sim:.4f} < {self.calibration.confidence_threshold:.2f}). "
                "Classified as Unknown Heritage Specimen to adhere to SIH anti-hallucination protocols."
            )

        if decision == DecisionState.NON_MONUMENT_REJECTED:
            return (
                f"Specimen rejected as non-heritage: Architectural Gatekeeper probability ({gatekeeper_score * 100:.1f}%) "
                f"and vector similarity ({top1_sim:.4f}) indicate an everyday object, document, person, or non-monument scene."
            )

        # REVIEW_REQUIRED
        reasons = []
        if gps.gps_conflict:
            reasons.append(f"GPS location conflict ({gps.distance_km:.1f} km from site)")
        if not quality.passed_quality_check:
            reasons.extend(quality.notes)
        if gatekeeper_score < self.calibration.gatekeeper_threshold_verified:
            reasons.append(f"Marginal gatekeeper score ({gatekeeper_score * 100:.1f}%)")

        detail = "; ".join(reasons) if reasons else "Borderline feature alignment"
        return (
            f"Curatorial review required before catalog attribution. Flagged conditions: {detail}."
        )

