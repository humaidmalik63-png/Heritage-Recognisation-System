"""
Phase 8.0B: Advanced Local Architectural Feature Recognition Engine
Project No. 30: Visual Heritage Recognition Platform (SIH 2025 - SIH25052)

Provides local architectural feature extraction, region proposals, local CLIP embeddings,
classical keypoint descriptors (SIFT/ORB), and RANSAC-based geometric verification.
Seamlessly complements Tier-1 Global CLIP + FAISS recognition without bypassing safety controls.
"""

import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
import torch

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "local_feature_config.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("local_feature_engine")


class ArchitecturalRegion:
    """Represents an extracted or proposed architectural region in an image."""
    def __init__(
        self,
        region_id: str,
        box: Tuple[int, int, int, int],  # (ymin, xmin, ymax, xmax) in pixels
        norm_box: Tuple[float, float, float, float],  # (ymin, xmin, ymax, xmax) in [0, 1]
        category: str,
        confidence: float = 1.0,
    ):
        self.region_id = region_id
        self.box = box
        self.norm_box = norm_box
        self.category = category  # "carving", "pillar", "arch_dome", "sculptural_frieze", "unclassified_structural_region"
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "bounding_box": {
                "ymin": round(self.norm_box[0], 4),
                "xmin": round(self.norm_box[1], 4),
                "ymax": round(self.norm_box[2], 4),
                "xmax": round(self.norm_box[3], 4),
            },
            "category": self.category,
            "confidence": round(self.confidence, 4),
        }


class GeometricVerificationResult:
    """Statistics for RANSAC geometric correspondence."""
    def __init__(
        self,
        keypoints_query: int = 0,
        keypoints_reference: int = 0,
        good_matches_count: int = 0,
        inliers_count: int = 0,
        inlier_ratio: float = 0.0,
        status: str = "INSUFFICIENT_FEATURES",  # "VERIFIED", "UNVERIFIED", "INSUFFICIENT_FEATURES"
        homography_found: bool = False,
    ):
        self.keypoints_query = keypoints_query
        self.keypoints_reference = keypoints_reference
        self.good_matches_count = good_matches_count
        self.inliers_count = inliers_count
        self.inlier_ratio = inlier_ratio
        self.status = status
        self.homography_found = homography_found

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keypoints_query": self.keypoints_query,
            "keypoints_reference": self.keypoints_reference,
            "good_matches_count": self.good_matches_count,
            "inliers_count": self.inliers_count,
            "inlier_ratio": round(self.inlier_ratio, 4),
            "status": self.status,
            "homography_found": self.homography_found,
        }


class LocalFeatureMatch:
    """Result of matching local features against reference assets."""
    def __init__(
        self,
        monument_key: str,
        monument_name: str,
        region: ArchitecturalRegion,
        similarity_score: float,
        geometric_verification: GeometricVerificationResult,
        matched_reference_id: Optional[str] = None,
        descriptor_type: str = "HYBRID_CLIP_SIFT",
    ):
        self.monument_key = monument_key
        self.monument_name = monument_name
        self.region = region
        self.similarity_score = similarity_score
        self.geometric_verification = geometric_verification
        self.matched_reference_id = matched_reference_id
        self.descriptor_type = descriptor_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "monument_key": self.monument_key,
            "monument_name": self.monument_name,
            "region": self.region.to_dict(),
            "similarity_score": round(self.similarity_score, 4),
            "geometric_verification": self.geometric_verification.to_dict(),
            "matched_reference_id": self.matched_reference_id,
            "descriptor_type": self.descriptor_type,
        }


class LocalFeatureEngine:
    """
    Modular engine providing region proposal, local visual embedding extraction,
    classical SIFT/ORB matching, and geometric verification.
    """
    def __init__(self, config_path: Optional[Path] = None, clip_model=None, clip_processor=None, device: str = "cpu"):
        self.config_path = config_path or CONFIG_PATH
        self.config = self._load_config()
        self.device = device
        self.clip_model = clip_model
        self.clip_processor = clip_processor

        # Classical feature detectors
        sift_n = self.config["classical_matching"].get("sift_n_features", 600)
        orb_n = self.config["classical_matching"].get("orb_n_features", 600)
        self.sift = cv2.SIFT_create(nfeatures=sift_n)
        self.orb = cv2.ORB_create(nfeatures=orb_n)

        # Reference cache: { image_path: (keypoints, descriptors, pil_img) }
        self._reference_descriptor_cache: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load config ({e}), using default fallback.")
        return {
            "classical_matching": {
                "sift_n_features": 600,
                "orb_n_features": 600,
                "lowe_ratio_threshold": 0.75,
                "ransac_reproj_threshold": 5.0,
                "min_good_matches": 8,
                "min_inliers_for_verification": 12,
                "min_inlier_ratio": 0.25,
            },
            "region_proposal": {
                "max_proposed_regions": 4,
                "min_region_area_pct": 0.05,
                "max_region_area_pct": 0.95,
            },
            "local_clip": {
                "similarity_threshold": 0.75,
            },
            "hybrid_aggregation": {
                "global_weight": 0.65,
                "local_weight": 0.35,
            }
        }

    def set_clip_resources(self, model, processor, device: str = "cpu"):
        self.clip_model = model
        self.clip_processor = processor
        self.device = device

    # -------------------------------------------------------------------------
    # 1. IMAGE PREPROCESSING
    # -------------------------------------------------------------------------
    def preprocess_image(self, image: Image.Image, max_dim: int = 1600) -> Tuple[Image.Image, np.ndarray, np.ndarray]:
        """
        Validates, corrects orientation, resizes if exceeding max_dim,
        and returns (pil_rgb, cv2_bgr, cv2_gray).
        """
        img_rgb = image.convert("RGB")
        w, h = img_rgb.size

        # Downscale proportionally if gigantic to conserve memory
        if max(w, h) > max_dim:
            scale = max_dim / float(max(w, h))
            new_w, new_h = int(w * scale), int(h * scale)
            img_rgb = img_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)

        np_rgb = np.array(img_rgb)
        cv2_bgr = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2BGR)
        cv2_gray = cv2.cvtColor(cv2_bgr, cv2.COLOR_BGR2GRAY)
        return img_rgb, cv2_bgr, cv2_gray

    # -------------------------------------------------------------------------
    # 2. ARCHITECTURAL REGION PROPOSAL
    # -------------------------------------------------------------------------
    def propose_regions(self, image: Image.Image, cv2_gray: np.ndarray) -> List[ArchitecturalRegion]:
        """
        Generates structured multi-scale architectural regions:
        1. Top sector (Domes, Spire, Finials, Chhatri)
        2. Middle sector (Arches, Entrances, Colonnades, Windows)
        3. Bottom sector (Plinths, Friezes, Bas-relief carvings, Wheels)
        4. Saliency/high-gradient carving region (highest detail density)
        """
        w, h = image.size
        regions: List[ArchitecturalRegion] = []
        max_regions = self.config["region_proposal"].get("max_proposed_regions", 4)

        # 1. Top sector (Upper architectural crown)
        ymin_1, ymax_1 = 0, int(h * 0.45)
        xmin_1, xmax_1 = int(w * 0.15), int(w * 0.85)
        regions.append(ArchitecturalRegion(
            region_id="reg_upper_dome_spire",
            box=(ymin_1, xmin_1, ymax_1, xmax_1),
            norm_box=(ymin_1 / h, xmin_1 / w, ymax_1 / h, xmax_1 / w),
            category="arch_dome",
            confidence=0.88,
        ))

        # 2. Middle sector (Main portal, arcade, columns)
        ymin_2, ymax_2 = int(h * 0.25), int(h * 0.75)
        xmin_2, xmax_2 = int(w * 0.10), int(w * 0.90)
        regions.append(ArchitecturalRegion(
            region_id="reg_middle_arcade_pillars",
            box=(ymin_2, xmin_2, ymax_2, xmax_2),
            norm_box=(ymin_2 / h, xmin_2 / w, ymax_2 / h, xmax_2 / w),
            category="pillar",
            confidence=0.85,
        ))

        # 3. Bottom sector (Plinth, frieze, carving base)
        ymin_3, ymax_3 = int(h * 0.55), h
        xmin_3, xmax_3 = int(w * 0.10), int(w * 0.90)
        regions.append(ArchitecturalRegion(
            region_id="reg_lower_frieze_plinth",
            box=(ymin_3, xmin_3, ymax_3, xmax_3),
            norm_box=(ymin_3 / h, xmin_3 / w, ymax_3 / h, xmax_3 / w),
            category="carving",
            confidence=0.82,
        ))

        # 4. Saliency / Gradient Energy Focus
        # Detect high-frequency texture using Laplacian gradient energy
        try:
            lap = cv2.Laplacian(cv2_gray, cv2.CV_64F)
            energy = np.abs(lap)
            # Blur energy map to find cluster
            kernel_size = max(15, (min(w, h) // 20) | 1)
            blurred_energy = cv2.GaussianBlur(energy, (kernel_size, kernel_size), 0)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred_energy)

            # Center high-detail crop around maximum energy location
            cx, cy = max_loc
            box_w = int(w * 0.40)
            box_h = int(h * 0.40)
            xmin_4 = max(0, cx - box_w // 2)
            xmax_4 = min(w, xmin_4 + box_w)
            ymin_4 = max(0, cy - box_h // 2)
            ymax_4 = min(h, ymin_4 + box_h)

            regions.append(ArchitecturalRegion(
                region_id="reg_salient_carving_focus",
                box=(ymin_4, xmin_4, ymax_4, xmax_4),
                norm_box=(ymin_4 / h, xmin_4 / w, ymax_4 / h, xmax_4 / w),
                category="sculptural_frieze",
                confidence=0.92,
            ))
        except Exception as e:
            logger.debug(f"Gradient saliency calculation skipped: {e}")

        return regions[:max_regions]

    # -------------------------------------------------------------------------
    # 3. LOCAL CLIP REGION EMBEDDINGS
    # -------------------------------------------------------------------------
    def extract_region_clip_embedding(self, region_crop: Image.Image) -> np.ndarray:
        """Extracts and normalizes 512-D CLIP visual embedding from region crop."""
        if not self.clip_model or not self.clip_processor:
            raise RuntimeError("CLIP model and processor must be initialized before embedding.")

        inputs = self.clip_processor(images=region_crop, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.clip_model.get_image_features(**inputs)
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                tensor = outputs.pooler_output
            elif hasattr(outputs, "last_hidden_state"):
                tensor = outputs.last_hidden_state
            else:
                tensor = outputs
            vec = tensor.cpu().detach().numpy().flatten().astype(np.float32)

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    # -------------------------------------------------------------------------
    # 4. SIFT / ORB KEYPOINTS & RANSAC GEOMETRIC VERIFICATION
    # -------------------------------------------------------------------------
    def extract_classical_descriptors(self, cv2_gray: np.ndarray, method: str = "sift") -> Tuple[List[Any], Optional[np.ndarray]]:
        """Extracts keypoints and descriptors using SIFT (preferred) or ORB."""
        if method.lower() == "sift":
            kps, des = self.sift.detectAndCompute(cv2_gray, None)
        else:
            kps, des = self.orb.detectAndCompute(cv2_gray, None)
        return kps, des

    def verify_geometric_correspondence(
        self,
        query_gray: np.ndarray,
        reference_gray: np.ndarray,
        method: str = "sift",
    ) -> GeometricVerificationResult:
        """
        Runs feature extraction, Lowe's ratio test matching, and RANSAC
        geometric homography estimation between query and reference image.
        """
        kps1, des1 = self.extract_classical_descriptors(query_gray, method=method)
        kps2, des2 = self.extract_classical_descriptors(reference_gray, method=method)

        num_kp1 = len(kps1)
        num_kp2 = len(kps2)

        cfg = self.config["classical_matching"]
        min_good = cfg.get("min_good_matches", 8)
        min_inliers = cfg.get("min_inliers_for_verification", 12)
        min_ratio = cfg.get("min_inlier_ratio", 0.25)
        lowe_ratio = cfg.get("lowe_ratio_threshold", 0.75)
        ransac_thresh = cfg.get("ransac_reproj_threshold", 5.0)

        # Insufficient keypoints detected
        if des1 is None or des2 is None or len(kps1) < 4 or len(kps2) < 4:
            return GeometricVerificationResult(
                keypoints_query=num_kp1,
                keypoints_reference=num_kp2,
                good_matches_count=0,
                inliers_count=0,
                inlier_ratio=0.0,
                status="INSUFFICIENT_FEATURES",
                homography_found=False,
            )

        # Match descriptors with FLANN or BFMatcher
        if method.lower() == "sift":
            # FLANN parameters for SIFT (KDTree)
            index_params = dict(algorithm=1, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            try:
                raw_matches = flann.knnMatch(des1, des2, k=2)
            except Exception:
                bf = cv2.BFMatcher()
                raw_matches = bf.knnMatch(des1, des2, k=2)
        else:
            # BFMatcher with Hamming distance for ORB
            bf = cv2.BFMatcher(cv2.NORM_HAMMING)
            raw_matches = bf.knnMatch(des1, des2, k=2)

        # Apply Lowe's ratio test
        good_matches = []
        for match_pair in raw_matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < lowe_ratio * n.distance:
                    good_matches.append(m)

        num_good = len(good_matches)
        if num_good < min_good:
            return GeometricVerificationResult(
                keypoints_query=num_kp1,
                keypoints_reference=num_kp2,
                good_matches_count=num_good,
                inliers_count=0,
                inlier_ratio=0.0,
                status="INSUFFICIENT_FEATURES",
                homography_found=False,
            )

        # Geometric RANSAC verification
        src_pts = np.float32([kps1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kps2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        try:
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_thresh)
            if mask is not None:
                inliers_count = int(np.sum(mask))
                inlier_ratio = float(inliers_count / max(1, num_good))
                homography_found = (H is not None and inliers_count >= 4)

                is_verified = (inliers_count >= min_inliers and inlier_ratio >= min_ratio)
                status = "VERIFIED" if is_verified else "UNVERIFIED"

                return GeometricVerificationResult(
                    keypoints_query=num_kp1,
                    keypoints_reference=num_kp2,
                    good_matches_count=num_good,
                    inliers_count=inliers_count,
                    inlier_ratio=inlier_ratio,
                    status=status,
                    homography_found=homography_found,
                )
        except Exception as e:
            logger.debug(f"Homography estimation failed: {e}")

        return GeometricVerificationResult(
            keypoints_query=num_kp1,
            keypoints_reference=num_kp2,
            good_matches_count=num_good,
            inliers_count=0,
            inlier_ratio=0.0,
            status="UNVERIFIED",
            homography_found=False,
        )

    # -------------------------------------------------------------------------
    # 5. MULTI-VIEW REFERENCE LOCAL MATCHING
    # -------------------------------------------------------------------------
    def match_local_features(
        self,
        image: Image.Image,
        reference_images: List[Dict[str, Any]],
        top_k_candidates: int = 3,
        enable_sift: bool = True,
        quality_gate_sift: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes complete Tier 1B local feature analysis:
        1. Preprocesses image.
        2. Generates architectural region proposals.
        3. Extracts local CLIP embeddings for each region.
        4. Matches regions against reference image set.
        5. Computes SIFT/RANSAC geometric verification against top candidate (if enabled and quality passed).
        6. Aggregates multi-region local evidence.
        """
        t0 = time.time()
        img_rgb, cv2_bgr, cv2_gray = self.preprocess_image(image)
        regions = self.propose_regions(img_rgb, cv2_gray)

        region_matches: List[LocalFeatureMatch] = []
        candidate_scores: Dict[str, List[float]] = {}
        candidate_names: Dict[str, str] = {}

        # 1. Process each proposed region
        for r in regions:
            ymin, xmin, ymax, xmax = r.box
            # Ensure valid non-empty slice
            if ymax - ymin < 10 or xmax - xmin < 10:
                continue

            crop = img_rgb.crop((xmin, ymin, xmax, ymax))
            crop_gray = cv2_gray[ymin:ymax, xmin:xmax]

            # Extract local CLIP feature if CLIP model available
            region_vec = None
            if self.clip_model and self.clip_processor:
                try:
                    region_vec = self.extract_region_clip_embedding(crop)
                except Exception as e:
                    logger.debug(f"Could not extract CLIP for region {r.region_id}: {e}")

            # Find best reference image match for this region
            best_ref = None
            best_sim = 0.0

            if region_vec is not None and reference_images:
                for ref_item in reference_images:
                    ref_vec = ref_item.get("embedding")
                    if ref_vec is not None:
                        sim = float(np.dot(region_vec, ref_vec))
                        if sim > best_sim:
                            best_sim = sim
                            best_ref = ref_item

            if best_ref:
                m_key = best_ref.get("monument_key", "")
                m_name = best_ref.get("monument_name", m_key)
                candidate_names[m_key] = m_name
                candidate_scores.setdefault(m_key, []).append(best_sim)

                # Placeholder geometric verification (detailed evaluation against top overall below)
                geo_res = GeometricVerificationResult(status="PENDING")
                region_matches.append(LocalFeatureMatch(
                    monument_key=m_key,
                    monument_name=m_name,
                    region=r,
                    similarity_score=best_sim,
                    geometric_verification=geo_res,
                    matched_reference_id=best_ref.get("image_id"),
                ))

        # 2. Determine top local candidate by max / mean similarity
        ranked_candidates = []
        for k, scores in candidate_scores.items():
            max_s = float(np.max(scores))
            mean_s = float(np.mean(scores))
            ranked_candidates.append({
                "monument_key": k,
                "monument_name": candidate_names.get(k, k),
                "max_similarity": max_s,
                "mean_similarity": mean_s,
                "region_matches_count": len(scores),
            })
        ranked_candidates.sort(key=lambda x: x["max_similarity"], reverse=True)

        top_local_candidate = ranked_candidates[0] if ranked_candidates else None

        # 3. Perform RANSAC Geometric Verification against top candidate reference image (if enabled & quality passed)
        top_geo_res = GeometricVerificationResult(status="BYPASSED")
        sift_triggered = False

        if enable_sift and top_local_candidate and reference_images:
            # Contrast/blur quality check: skip SIFT if image has severe blur or extreme brightness
            gy, gx = np.gradient(cv2_gray.astype(np.float32))
            gnorm = np.sqrt(gx**2 + gy**2)
            blur_score = float(np.var(gnorm))
            mean_brightness = float(np.mean(cv2_gray))

            sift_eligible = True
            if quality_gate_sift:
                if blur_score < 25.0 or mean_brightness < 25.0 or mean_brightness > 230.0:
                    sift_eligible = False
                    top_geo_res = GeometricVerificationResult(status="BYPASSED_LOW_QUALITY")

            if sift_eligible:
                sift_triggered = True
                top_key = top_local_candidate["monument_key"]
                # Locate an eligible reference image of this monument
                ref_match_cand = next(
                    (r for r in reference_images if r.get("monument_key") == top_key and "file_path" in r),
                    None
                )
                if ref_match_cand:
                    ref_path = BASE_DIR / ref_match_cand["file_path"]
                    if ref_path.exists():
                        ref_gray = cv2.imread(str(ref_path), cv2.IMREAD_GRAYSCALE)
                        if ref_gray is not None:
                            top_geo_res = self.verify_geometric_correspondence(cv2_gray, ref_gray, method="sift")
                            # Update corresponding region geometric verification
                            for rm in region_matches:
                                if rm.monument_key == top_key:
                                    rm.geometric_verification = top_geo_res

        elapsed_ms = (time.time() - t0) * 1000.0

        return {
            "top_candidate": top_local_candidate,
            "ranked_candidates": ranked_candidates[:top_k_candidates],
            "regions_evaluated": len(regions),
            "region_matches": [rm.to_dict() for rm in region_matches],
            "geometric_verification": top_geo_res.to_dict(),
            "sift_triggered": sift_triggered,
            "latency_ms": round(elapsed_ms, 2),
        }

    # -------------------------------------------------------------------------
    # 6. EVIDENCE AGGREGATION & DECISION ENGINE COMPATIBILITY (Tier 1C)
    # -------------------------------------------------------------------------
    def evaluate_hybrid_evidence(
        self,
        global_candidate: Optional[Dict[str, Any]],
        local_results: Dict[str, Any],
        gatekeeper_score: float,
    ) -> Dict[str, Any]:
        """
        Evaluates agreement/disagreement between Global Tier 1 and Local Tier 1B evidence.
        Preserves existing decision states strictly.
        """
        global_key = global_candidate.get("monument_key") if global_candidate else None
        global_score = float(global_candidate.get("similarity", 0.0)) if global_candidate else 0.0

        local_cand = local_results.get("top_candidate")
        local_key = local_cand.get("monument_key") if local_cand else None
        local_score = float(local_cand.get("max_similarity", 0.0)) if local_cand else 0.0

        geo_status = local_results.get("geometric_verification", {}).get("status", "INSUFFICIENT_FEATURES")
        inlier_count = local_results.get("geometric_verification", {}).get("inliers_count", 0)

        # Default alignment state
        override_applied = False
        final_candidate_key = global_key

        if gatekeeper_score < 0.35:
            alignment = "REJECTED_NON_MONUMENT"
            explanation = "Specimen rejected by visual gatekeeper before local evidence evaluation."
        elif not local_key:
            alignment = "INSUFFICIENT_LOCAL_EVIDENCE"
            explanation = "Insufficient localized architectural features detected."
        elif global_key == local_key:
            if geo_status == "VERIFIED":
                alignment = "AGREEMENT_CONFIRMED_GEOMETRIC"
                explanation = f"Strong agreement: Global and local evidence both identify '{global_key}' with {inlier_count} verified geometric inliers."
            else:
                alignment = "AGREEMENT_CONFIRMED_VISUAL"
                explanation = f"Consistent agreement: Global and local feature vectors both identify '{global_key}'."
        elif global_key != local_key:
            # Conservative non-override invariant:
            # Local evidence can NEVER override a reliable global result unless SIFT RANSAC is VERIFIED with >= 10 inliers.
            alignment = "DIVERGENT_EVIDENCE"
            if geo_status == "VERIFIED" and inlier_count >= 10:
                override_applied = True
                final_candidate_key = local_key
                explanation = (
                    f"Ambiguity detected: Local architectural analysis conclusively confirmed '{local_key}' with {inlier_count} "
                    f"verified geometric inliers, safely overriding ambiguous global candidate '{global_key}'."
                )
            else:
                override_applied = False
                final_candidate_key = global_key
                explanation = (
                    f"Ambiguity detected: Global retrieval suggests '{global_key}' ({global_score:.3f}), "
                    f"while local feature analysis matches '{local_key}' ({local_score:.3f}). "
                    f"Conservative safety rule: Retaining global candidate '{global_key}' because local "
                    f"feature evidence lacks >= 10 verified RANSAC inliers (actual inliers: {inlier_count})."
                )
        else:
            alignment = "INSUFFICIENT_LOCAL_EVIDENCE"
            explanation = "Localized evidence could not conclusively differentiate monument candidates."

        return {
            "alignment_status": alignment,
            "explanation": explanation,
            "global_candidate": global_key,
            "global_similarity": round(global_score, 4),
            "local_candidate": local_key,
            "local_similarity": round(local_score, 4),
            "geometric_verification_status": geo_status,
            "inlier_count": inlier_count,
            "override_applied": override_applied,
            "final_candidate_key": final_candidate_key,
            "evidence_quality": "HIGH" if geo_status == "VERIFIED" else ("MEDIUM" if local_score >= 0.80 else "LOW"),
        }


# Global singleton engine instance
local_feature_engine = LocalFeatureEngine()

