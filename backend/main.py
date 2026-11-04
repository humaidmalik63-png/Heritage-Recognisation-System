"""
Heritage & Monument Recognition System - Hybrid Production FastAPI Backend
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)
Phase 6.2: Advanced Confidence Calibration & Uncertainty Engine

Features:
  - Tier 1: Local CLIP (ViT-B/32) + FAISS (IndexFlatIP, 512-D) + EXIF GPS
  - Tier 2: Gemini 2.5 Flash VLM Deep Architectural Fallback
  - Multi-candidate FAISS Unique-Monument Aggregation (prevents intra-monument anchor margin collapse)
  - Explicit 5-State Uncertainty Arbitration:
      VERIFIED_MATCH, UNCERTAIN_MATCH, UNKNOWN_HERITAGE_SPECIMEN, NON_MONUMENT_REJECTED, REVIEW_REQUIRED
  - Real Confidence Calibration Engine (ECE, Brier, Temperature Scaling; returns None when uncalibrated)
  - Image Quality Inspection (Resolution, Laplacian blur variance, Exposure analysis)
  - Geodetic Distance Verification & Spatial Conflict Detection
  - Grounded Cultural Citations & Legal Preservation Metadata
  - Persistent Curator Review Exception System with Duplicate Prevention & Audit Trail
"""

import hashlib
import io
import json
import logging
import math
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import exifread
import faiss
import numpy as np
import torch
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel, Field
from transformers import CLIPModel, CLIPProcessor

# Import Calibration and Uncertainty modules
from calibration import CalibrationEngine
from uncertainty import (
    AggregatedCandidate,
    DecisionState,
    GPSEvidence,
    ImageQualityMetrics,
    ReasonCode,
    UncertaintyEngine,
    UncertaintyResult,
    compute_haversine_distance_km,
    inspect_image_quality,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("heritage_backend")

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
INDEX_FILE = BASE_DIR / "monument_index.faiss"
LABELS_FILE = BASE_DIR / "monument_labels.json"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
EXCEPTIONS_FILE = BASE_DIR / "exceptions_log.json"
CALIBRATION_CONFIG_FILE = BASE_DIR / "calibration_config.json"

MODEL_NAME = "openai/clip-vit-base-patch32"
GATEKEEPER_SCALE = 18.0

CATALOG_ID_MAP = {
    "taj_mahal": "ASI-ARCH-TAJ-01",
    "qutub_minar": "ASI-ARCH-QUT-02",
    "hawa_mahal": "ASI-ARCH-HAW-03",
    "konark_sun_temple": "ASI-ARCH-KON-04",
    "gateway_of_india": "ASI-ARCH-GOI-05",
    "charminar": "ASI-ARCH-CHA-06",
    "hampi_stone_chariot": "ASI-ARCH-HAM-07",
    "sanchi_stupa": "ASI-ARCH-SAN-08",
    "victoria_memorial": "ASI-ARCH-VIC-09",
    "brihadeeswarar_temple": "ASI-ARCH-BRI-10",
}

POSITIVE_PROMPTS = [
    "a photo of a historical monument, ancient temple, fort, palace, or architectural landmark",
    "famous heritage architecture exterior",
]

NEGATIVE_PROMPTS = [
    "a photo of a person, selfie, indoor room, animal, food, car, document, or random everyday object",
    "non-architectural scene",
]

# Global application state holder
state: Dict[str, Any] = {
    "device": "cpu",
    "clip_model": None,
    "clip_processor": None,
    "faiss_index": None,
    "labels": [],
    "metadata": {},
    "gatekeeper_pos_vec": None,
    "gatekeeper_neg_vec": None,
    "gemini_client": None,
    "gemini_configured": False,
    "calibration_engine": None,
    "uncertainty_engine": None,
}


# --- Pydantic Models ---

class CandidateMatch(BaseModel):
    monument_key: str
    monument_name: str
    cosine_similarity: float


class PipelineTelemetry(BaseModel):
    exif_gps: Optional[Dict[str, Any]] = None
    architectural_gatekeeper_score: float
    top_3_candidates: List[CandidateMatch]
    decision_reason: str
    geo_boost_applied: bool = False


class GroundedCitations(BaseModel):
    primary_source: Optional[str] = None
    gazetteer_reference: Optional[str] = None
    unesco_whc_ref: Optional[str] = None
    epigraphical_records: Optional[str] = None
    legal_framework: Optional[str] = None
    curatorial_notes: Optional[str] = None


class VerificationResponse(BaseModel):
    is_monument: bool
    verification_status: str  # "VERIFIED_MATCH", "UNCERTAIN_MATCH", "UNKNOWN_HERITAGE_SPECIMEN", "NON_MONUMENT_REJECTED", "REVIEW_REQUIRED"
    is_uncertain: bool = False
    verification_tier: str
    confidence_score: float
    catalog_id: Optional[str] = None
    monument_key: Optional[str] = None
    monument_name: Optional[str] = None
    location: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    architectural_style: Optional[str] = None
    built_by_or_era: Optional[str] = None
    historical_summary: Optional[str] = None
    structural_features_detected: List[str] = Field(default_factory=list)
    preservation_status: Optional[str] = None
    grounded_citations: Optional[GroundedCitations] = None
    rejection_message: Optional[str] = None
    pipeline_telemetry: PipelineTelemetry
    human_review_flagged: bool = False
    exception_id: Optional[str] = None
    uncertainty: Optional[UncertaintyResult] = None


class ExceptionItem(BaseModel):
    id: str
    timestamp: str
    specimen_filename: str
    specimen_hash: Optional[str] = None
    monument_key_candidate: Optional[str] = None
    monument_name_candidate: Optional[str] = None
    top_candidates: Optional[List[Dict[str, Any]]] = None
    gatekeeper_score: float
    top_similarity_score: float
    similarity_margin: Optional[float] = None
    reason: str
    reason_codes: Optional[List[str]] = None
    calibration_status: Optional[str] = None
    status: str = "PENDING_REVIEW"  # PENDING_REVIEW, APPROVED, REJECTED, CATALOGED
    curator_notes: Optional[str] = None
    user_email: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class ResolveExceptionRequest(BaseModel):
    status: str  # APPROVED, REJECTED, CATALOGED
    curator_notes: str


class GeminiMonumentSchema(BaseModel):
    is_monument: bool = Field(description="True if image depicts a recognized heritage monument/temple/fort/palace; False otherwise.")
    monument_name: Optional[str] = Field(default=None, description="Official name of the heritage monument.")
    location: Optional[str] = Field(default=None, description="City, State, and Country.")
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate if known.")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate if known.")
    architectural_style: Optional[str] = Field(default=None, description="Architectural movement or style.")
    built_by_or_era: Optional[str] = Field(default=None, description="Dynasty, builder, or historic era.")
    historical_summary: Optional[str] = Field(default=None, description="3-4 informative historical sentences.")
    structural_features_detected: List[str] = Field(default_factory=list, description="4-5 distinct architectural features visible.")
    confidence_score: float = Field(default=88.0, description="Estimated confidence percentage 0-100.")


# --- Helper Functions ---

def load_exceptions_log() -> List[Dict[str, Any]]:
    if not EXCEPTIONS_FILE.exists():
        return []
    try:
        with open(EXCEPTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error(f"Error reading exceptions log: {exc}")
        return []


def save_exceptions_log(exceptions: List[Dict[str, Any]]):
    try:
        with open(EXCEPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(exceptions, f, indent=2)
    except Exception as exc:
        logger.error(f"Error saving exceptions log: {exc}")


def record_exception_entry(
    filename: str,
    gatekeeper_score: float,
    top_candidate: Optional[Any],
    reason: str,
    specimen_hash: Optional[str] = None,
    top_candidates_list: Optional[List[Any]] = None,
    similarity_margin: Optional[float] = None,
    reason_codes: Optional[List[str]] = None,
    calibration_status: Optional[str] = "UNCALIBRATED",
    user_email: Optional[str] = "system@curator.local",
) -> str:
    """
    Records an exception ticket with duplicate scan prevention and an audit trail.
    """
    current_log = load_exceptions_log()

    # Prevent duplicate tickets for identical uploaded scans
    if specimen_hash:
        for existing in current_log:
            if existing.get("specimen_hash") == specimen_hash and existing.get("status") == "PENDING_REVIEW":
                logger.info(f"Duplicate scan detected. Reusing existing exception ticket: {existing['id']}")
                return existing["id"]

    exception_id = f"EXC-{uuid.uuid4().hex[:8].upper()}"

    top_cand_serialized = []
    if top_candidates_list:
        for c in top_candidates_list[:3]:
            if hasattr(c, "dict"):
                top_cand_serialized.append(c.dict())
            elif isinstance(c, dict):
                top_cand_serialized.append(c)

    m_key = getattr(top_candidate, "monument_key", None)
    m_name = getattr(top_candidate, "monument_name", None)
    top_sim = float(getattr(top_candidate, "max_similarity", getattr(top_candidate, "cosine_similarity", 0.0)))

    now_iso = datetime.utcnow().isoformat() + "Z"

    new_entry = {
        "id": exception_id,
        "timestamp": now_iso,
        "specimen_filename": filename,
        "specimen_hash": specimen_hash,
        "monument_key_candidate": m_key,
        "monument_name_candidate": m_name,
        "top_candidates": top_cand_serialized,
        "gatekeeper_score": round(float(gatekeeper_score), 4),
        "top_similarity_score": round(top_sim, 4),
        "similarity_margin": round(float(similarity_margin), 4) if similarity_margin is not None else None,
        "reason": reason,
        "reason_codes": reason_codes or [],
        "calibration_status": calibration_status,
        "status": "PENDING_REVIEW",
        "curator_notes": None,
        "user_email": user_email,
        "history": [
            {
                "action": "CREATED",
                "timestamp": now_iso,
                "reason": reason,
                "status": "PENDING_REVIEW",
            }
        ],
    }

    current_log.insert(0, new_entry)
    save_exceptions_log(current_log[:100])
    logger.info(f"Recorded human-review exception: {exception_id} ({reason})")
    return exception_id


def extract_exif_gps(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    try:
        tags = exifread.process_file(io.BytesIO(image_bytes), details=False)
        if "GPS GPSLatitude" not in tags or "GPS GPSLongitude" not in tags:
            return None

        def _dms_to_deg(dms_values, ref: str) -> float:
            d = float(dms_values[0].num) / float(dms_values[0].den)
            m = float(dms_values[1].num) / float(dms_values[1].den)
            s = float(dms_values[2].num) / float(dms_values[2].den)
            deg = d + (m / 60.0) + (s / 3600.0)
            if ref in ["S", "W"]:
                deg = -deg
            return round(deg, 6)

        lat_ref = str(tags.get("GPS GPSLatitudeRef", "N")).strip().upper()
        lng_ref = str(tags.get("GPS GPSLongitudeRef", "E")).strip().upper()
        lat = _dms_to_deg(tags["GPS GPSLatitude"].values, lat_ref)
        lng = _dms_to_deg(tags["GPS GPSLongitude"].values, lng_ref)

        return {
            "lat": lat,
            "lng": lng,
            "raw_status": "EXIF GPS Found",
        }
    except Exception as exc:
        logger.debug(f"EXIF GPS extraction error: {exc}")
        return None


def compute_clip_image_embedding(image: Image.Image) -> np.ndarray:
    model = state["clip_model"]
    processor = state["clip_processor"]
    device = state["device"]

    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
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


def evaluate_architectural_gatekeeper(img_vec: np.ndarray) -> float:
    pos_vec = state["gatekeeper_pos_vec"]
    neg_vec = state["gatekeeper_neg_vec"]

    sim_pos = float(np.dot(img_vec, pos_vec))
    sim_neg = float(np.dot(img_vec, neg_vec))

    exp_pos = math.exp(sim_pos * GATEKEEPER_SCALE)
    exp_neg = math.exp(sim_neg * GATEKEEPER_SCALE)
    prob = exp_pos / (exp_pos + exp_neg)
    return float(round(prob, 4))


def execute_gemini_fallback(image: Image.Image) -> Optional[Dict[str, Any]]:
    client = state.get("gemini_client")
    if not client:
        return None

    try:
        from google.genai import types

        prompt = (
            "You are a Senior Architectural Historian and Heritage Specialist. "
            "Analyze this uploaded photograph and identify the heritage monument, ancient temple, "
            "fort, palace, or archaeological site. If it is NOT a heritage landmark (e.g., modern building, "
            "person, selfie, everyday object, indoor scene), set is_monument=False."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiMonumentSchema,
                temperature=0.1,
            ),
        )

        parsed_data = json.loads(response.text)
        return parsed_data
    except Exception as exc:
        logger.error(f"Gemini Tier 2 fallback call error: {exc}")
        return None


# --- Lifespan Initialization ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Heritage Monument Recognition Engine (SIH 2025)...")

    # 1. Device configuration
    device = "cuda" if torch.cuda.is_available() else "cpu"
    state["device"] = device
    logger.info(f"Target compute device: {device.upper()}")

    # 2. Load CLIP Model & Processor (Loaded once at startup)
    logger.info(f"Loading CLIP model: {MODEL_NAME}...")
    clip_model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
    clip_processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    clip_model.eval()
    state["clip_model"] = clip_model
    state["clip_processor"] = clip_processor

    # 3. Precompute Zero-Shot Gatekeeper Text Embeddings
    logger.info("Pre-computing Zero-Shot Gatekeeper text embeddings...")

    def _get_avg_text_vector(prompts: List[str]) -> np.ndarray:
        inp = clip_processor(text=prompts, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            out = clip_model.get_text_features(**inp)
            t = out.pooler_output if hasattr(out, "pooler_output") and out.pooler_output is not None else out
            v = t.cpu().numpy()
            v = v / np.linalg.norm(v, axis=1, keepdims=True)
            mean_v = np.mean(v, axis=0)
            return mean_v / np.linalg.norm(mean_v)

    state["gatekeeper_pos_vec"] = _get_avg_text_vector(POSITIVE_PROMPTS)
    state["gatekeeper_neg_vec"] = _get_avg_text_vector(NEGATIVE_PROMPTS)

    # 4. Load FAISS Index, Labels & Monuments Metadata
    if not INDEX_FILE.exists():
        raise FileNotFoundError(f"FAISS index missing at {INDEX_FILE}. Run index_builder.py first.")
    if not LABELS_FILE.exists():
        raise FileNotFoundError(f"Labels mapping missing at {LABELS_FILE}.")
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Metadata file missing at {METADATA_FILE}.")

    state["faiss_index"] = faiss.read_index(str(INDEX_FILE))
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        state["labels"] = json.load(f)
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        state["metadata"] = json.load(f)

    # 5. Initialize Confidence Calibration & Uncertainty Engines
    calibration_engine = CalibrationEngine(CALIBRATION_CONFIG_FILE)
    uncertainty_engine = UncertaintyEngine(calibration_engine)
    state["calibration_engine"] = calibration_engine
    state["uncertainty_engine"] = uncertainty_engine

    logger.info(f"Loaded Confidence Calibration Engine: Status = {calibration_engine.calibration_status}")

    # Ensure exceptions file exists
    if not EXCEPTIONS_FILE.exists():
        save_exceptions_log([])

    logger.info(
        f"Loaded FAISS index with {state['faiss_index'].ntotal} vectors, "
        f"{len(state['labels'])} labels, and {len(state['metadata'])} monument metadata records."
    )

    # 6. Initialize Gemini Tier 2 Client if configured
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key and gemini_key != "your_google_ai_studio_api_key_here":
        try:
            from google import genai
            state["gemini_client"] = genai.Client(api_key=gemini_key)
            state["gemini_configured"] = True
            logger.info("Gemini 2.5 Flash Tier 2 VLM client successfully configured.")
        except Exception as exc:
            logger.warning(f"Could not initialize Gemini Client: {exc}")
            state["gemini_configured"] = False
    else:
        logger.info("No active GEMINI_API_KEY detected. Running in pure offline Tier 1 mode.")
        state["gemini_configured"] = False

    logger.info("Engine startup complete. Service ready.")
    yield
    logger.info("Service shutting down...")


# --- FastAPI Application ---

app = FastAPI(
    title="Visual Heritage Recognition & Grounded Cultural Discovery Platform",
    description="Project No. 30 (SIH 2025): Two-Tier Hybrid Architecture with Calibrated Uncertainty Engine",
    version="2.1.0",
    lifespan=lifespan,
)

# Standard robust CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static dataset images for client preview & verification
if DATASET_DIR.exists():
    app.mount("/dataset", StaticFiles(directory=str(DATASET_DIR)), name="dataset")


# --- API Routes ---

@app.get("/api/health")
def get_health():
    """Returns live engine health and diagnostic status."""
    calib = state.get("calibration_engine")
    return {
        "status": "healthy",
        "faiss_vectors_loaded": state["faiss_index"].ntotal if state["faiss_index"] else 0,
        "clip_device": state["device"],
        "gemini_tier2_configured": state["gemini_configured"],
        "monuments_count": len(state["metadata"]),
        "exceptions_count": len(load_exceptions_log()),
        "calibration_status": calib.calibration_status if calib else "UNCALIBRATED",
    }


@app.get("/api/monuments")
def get_monuments_catalog():
    """Returns the comprehensive catalog of 10 indexed heritage monuments."""
    return {
        "total": len(state["metadata"]),
        "monuments": state["metadata"],
    }


@app.get("/api/exceptions")
def get_exceptions_list():
    """Curator Exception Log: Returns flagged or ambiguous scans awaiting human oversight."""
    exceptions = load_exceptions_log()
    return {
        "total": len(exceptions),
        "exceptions": exceptions,
    }


@app.post("/api/exceptions/{exception_id}/resolve")
def resolve_exception(exception_id: str, payload: ResolveExceptionRequest):
    """Allows a curator to inspect and resolve a flagged exception item while preserving audit history."""
    current_log = load_exceptions_log()
    target = next((item for item in current_log if item["id"] == exception_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Exception record not found.")

    prev_status = target.get("status", "PENDING_REVIEW")
    now_iso = datetime.utcnow().isoformat() + "Z"

    target["status"] = payload.status.upper()
    target["curator_notes"] = payload.curator_notes
    target["resolved_at"] = now_iso

    if "history" not in target or not isinstance(target["history"], list):
        target["history"] = []

    target["history"].append({
        "action": "RESOLVED",
        "previous_status": prev_status,
        "new_status": payload.status.upper(),
        "timestamp": now_iso,
        "curator_notes": payload.curator_notes,
    })

    save_exceptions_log(current_log)

    return {
        "success": True,
        "message": f"Exception {exception_id} updated to {payload.status.upper()}",
        "exception": target,
    }


@app.post("/api/verify-monument", response_model=VerificationResponse)
async def verify_monument(file: UploadFile = File(...)):
    """
    Phase 6.2 Advanced Recognition & Calibrated Uncertainty Pipeline:
    - Step 1: Read, validate, and compute image hash.
    - Step 2: Quality Inspection (Resolution, Laplacian blur, Exposure).
    - Step 3: Zero-Shot Architectural Gatekeeper & CLIP Feature Extraction.
    - Step 4: Multi-Candidate Unique-Monument FAISS Aggregation.
    - Step 5: Geodetic EXIF GPS Verification & Spatial Conflict Detection.
    - Step 6: Uncertainty Engine Evaluation across 5 Explicit States.
    - Step 7: Tier 2 Gemini VLM Fallback (if configured & justified).
    - Step 8: Curator Review Exception Logging (with duplicate suppression).
    """
    # 1. Read & validate image bytes
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        with Image.open(io.BytesIO(image_bytes)) as raw_img:
            raw_img.verify()

        with Image.open(io.BytesIO(image_bytes)) as valid_img:
            image_rgb = valid_img.convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid or corrupted image: {exc}")

    # Compute fast specimen hash for duplicate detection
    specimen_hash = hashlib.sha256(image_bytes).hexdigest()[:16]

    # 2. Extract EXIF GPS, CLIP Embedding & Gatekeeper Score
    exif_gps = extract_exif_gps(image_bytes)
    img_vec = compute_clip_image_embedding(image_rgb)
    arch_prob = evaluate_architectural_gatekeeper(img_vec)

    # 3. Query FAISS index for top 15 nearest anchors
    query_matrix = np.expand_dims(img_vec, axis=0).astype(np.float32)
    raw_distances, raw_indices = state["faiss_index"].search(query_matrix, 15)

    # 4. Evaluate Multimodal Evidence via Dedicated Uncertainty Engine
    uncertainty_engine: UncertaintyEngine = state["uncertainty_engine"]
    uncertainty_res: UncertaintyResult = uncertainty_engine.evaluate(
        image=image_rgb,
        gatekeeper_score=arch_prob,
        raw_distances=raw_distances[0],
        raw_indices=raw_indices[0],
        labels=state["labels"],
        metadata=state["metadata"],
        exif_gps=exif_gps,
    )

    top_candidates_agg = uncertainty_res.top_candidates
    best_cand = top_candidates_agg[0] if len(top_candidates_agg) > 0 else None
    best_key = best_cand.monument_key if best_cand else ""
    best_name = best_cand.monument_name if best_cand else ""
    best_score = best_cand.max_similarity if best_cand else 0.0

    # Build legacy telemetry top 3 candidates for backwards compatibility
    top_3_telemetry = [
        CandidateMatch(
            monument_key=c.monument_key,
            monument_name=c.monument_name,
            cosine_similarity=c.max_similarity,
        )
        for c in top_candidates_agg[:3]
    ]

    geo_boost = uncertainty_res.gps_evidence.geo_boost_applied

    # 5. Handle Tier 2 Gemini VLM Fallback if configured and indicated
    if (
        state["gemini_configured"]
        and uncertainty_res.decision in [DecisionState.UNKNOWN_HERITAGE_SPECIMEN, DecisionState.REVIEW_REQUIRED]
        and arch_prob >= 0.40
    ):
        logger.info(f"Dispatching to Tier 2 Gemini VLM Fallback (arch_prob={arch_prob}, best_score={best_score})...")
        vlm_result = execute_gemini_fallback(image_rgb)
        if vlm_result:
            if vlm_result.get("is_monument", False):
                coords = None
                if vlm_result.get("latitude") and vlm_result.get("longitude"):
                    coords = {"lat": float(vlm_result["latitude"]), "lng": float(vlm_result["longitude"])}

                m_name = vlm_result.get("monument_name", "Identified Heritage Landmark")
                slug_key = m_name.lower().replace(" ", "_")[:20]
                catalog_id = f"ASI-VLM-{slug_key[:4].upper()}-99"

                return VerificationResponse(
                    is_monument=True,
                    verification_status=DecisionState.VERIFIED_MATCH.value,
                    is_uncertain=False,
                    verification_tier="TIER 2 // VLM DEEP ARCHITECTURAL VERIFICATION",
                    confidence_score=round(float(vlm_result.get("confidence_score", 88.0)), 1),
                    catalog_id=catalog_id,
                    monument_key=slug_key,
                    monument_name=m_name,
                    location=vlm_result.get("location", "Location Verified"),
                    coordinates=coords,
                    architectural_style=vlm_result.get("architectural_style", "Historical Heritage"),
                    built_by_or_era=vlm_result.get("built_by_or_era", "Heritage Era"),
                    historical_summary=vlm_result.get("historical_summary", "Historical site verified by VLM."),
                    structural_features_detected=vlm_result.get("structural_features_detected", []),
                    preservation_status="VLM Verified Monument of Cultural Interest",
                    grounded_citations=GroundedCitations(
                        primary_source="Gemini 2.5 Flash Multimodal Archaeological Engine",
                        curatorial_notes="Identified outside primary local vector database via deep vision-language synthesis."
                    ),
                    pipeline_telemetry=PipelineTelemetry(
                        exif_gps=exif_gps,
                        architectural_gatekeeper_score=arch_prob,
                        top_3_candidates=top_3_telemetry,
                        decision_reason="Identified via Gemini 2.5 Flash VLM Multimodal Architectural Analysis",
                        geo_boost_applied=geo_boost,
                    ),
                    uncertainty=uncertainty_res,
                )
            else:
                return VerificationResponse(
                    is_monument=False,
                    verification_status=DecisionState.NON_MONUMENT_REJECTED.value,
                    is_uncertain=False,
                    verification_tier="REJECTED // NON-MONUMENT SPECIMEN",
                    confidence_score=round(float(vlm_result.get("confidence_score", 95.0)), 1),
                    rejection_message="Gemini VLM analysis confirmed that the submitted photograph does not depict a heritage monument or historical landmark.",
                    pipeline_telemetry=PipelineTelemetry(
                        exif_gps=exif_gps,
                        architectural_gatekeeper_score=arch_prob,
                        top_3_candidates=top_3_telemetry,
                        decision_reason="Specimen rejected by Gemini VLM Tier 2 Inspection.",
                        geo_boost_applied=geo_boost,
                    ),
                    uncertainty=uncertainty_res,
                )

    # 6. Handle Human Review Exception Logging
    exception_id = None
    if uncertainty_res.requires_human_review:
        exception_id = record_exception_entry(
            filename=file.filename or "uploaded_specimen.jpg",
            gatekeeper_score=arch_prob,
            top_candidate=best_cand,
            reason=uncertainty_res.explanation,
            specimen_hash=specimen_hash,
            top_candidates_list=top_candidates_agg,
            similarity_margin=uncertainty_res.similarity_margin,
            reason_codes=uncertainty_res.reason_codes,
            calibration_status=uncertainty_res.calibration_status,
        )

    # 7. Map Uncertainty State to Backward-Compatible VerificationResponse
    decision = uncertainty_res.decision

    # --- CASE A: VERIFIED MATCH ---
    if decision == DecisionState.VERIFIED_MATCH and best_key in state["metadata"]:
        m_data = state["metadata"][best_key]
        catalog_id = CATALOG_ID_MAP.get(best_key, f"ASI-ARCH-{best_key[:3].upper()}-00")
        heuristic_conf_pct = round(min(best_score * 100.0, 99.8), 1)

        citations = None
        if "grounded_citations" in m_data:
            citations = GroundedCitations(**m_data["grounded_citations"])

        return VerificationResponse(
            is_monument=True,
            verification_status=DecisionState.VERIFIED_MATCH.value,
            is_uncertain=False,
            verification_tier="TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX",
            confidence_score=heuristic_conf_pct,
            catalog_id=catalog_id,
            monument_key=best_key,
            monument_name=m_data["monument_name"],
            location=m_data["location"],
            coordinates=m_data["coordinates"],
            architectural_style=m_data["architectural_style"],
            built_by_or_era=m_data["built_by_or_era"],
            historical_summary=m_data["historical_summary"],
            structural_features_detected=m_data["structural_features_detected"],
            preservation_status=m_data.get("preservation_status"),
            grounded_citations=citations,
            pipeline_telemetry=PipelineTelemetry(
                exif_gps=exif_gps,
                architectural_gatekeeper_score=arch_prob,
                top_3_candidates=top_3_telemetry,
                decision_reason=uncertainty_res.explanation,
                geo_boost_applied=geo_boost,
            ),
            human_review_flagged=False,
            exception_id=None,
            uncertainty=uncertainty_res,
        )

    # --- CASE B: UNCERTAIN MATCH (CANDIDATE COMPETITION) ---
    if decision == DecisionState.UNCERTAIN_MATCH:
        m_data = state["metadata"].get(best_key, {})
        catalog_id = CATALOG_ID_MAP.get(best_key, f"ASI-ARCH-{best_key[:3].upper()}-00")

        return VerificationResponse(
            is_monument=True,
            verification_status=DecisionState.UNCERTAIN_MATCH.value,
            is_uncertain=True,
            verification_tier="UNCERTAIN // CLOSE CANDIDATE COMPETITION",
            confidence_score=round(best_score * 100.0, 1),
            catalog_id=catalog_id,
            monument_key=best_key,
            monument_name=m_data.get("monument_name", best_name),
            location=m_data.get("location"),
            coordinates=m_data.get("coordinates"),
            architectural_style=m_data.get("architectural_style"),
            built_by_or_era=m_data.get("built_by_or_era"),
            historical_summary=m_data.get("historical_summary"),
            structural_features_detected=m_data.get("structural_features_detected", []),
            preservation_status=m_data.get("preservation_status"),
            grounded_citations=GroundedCitations(**m_data.get("grounded_citations", {})) if m_data.get("grounded_citations") else None,
            rejection_message=uncertainty_res.explanation,
            pipeline_telemetry=PipelineTelemetry(
                exif_gps=exif_gps,
                architectural_gatekeeper_score=arch_prob,
                top_3_candidates=top_3_telemetry,
                decision_reason="Ambiguous visual distinction between top unique candidates. Human review requested.",
                geo_boost_applied=geo_boost,
            ),
            human_review_flagged=True,
            exception_id=exception_id,
            uncertainty=uncertainty_res,
        )

    # --- CASE C: UNKNOWN HERITAGE SPECIMEN ---
    if decision == DecisionState.UNKNOWN_HERITAGE_SPECIMEN:
        return VerificationResponse(
            is_monument=False,
            verification_status=DecisionState.UNKNOWN_HERITAGE_SPECIMEN.value,
            is_uncertain=True,
            verification_tier="UNKNOWN SPECIMEN // UNINDEXED OR AMBIGUOUS HERITAGE SITE",
            confidence_score=round(best_score * 100.0, 1),
            monument_name="Unindexed / Ambiguous Heritage Site",
            rejection_message=uncertainty_res.explanation,
            pipeline_telemetry=PipelineTelemetry(
                exif_gps=exif_gps,
                architectural_gatekeeper_score=arch_prob,
                top_3_candidates=top_3_telemetry,
                decision_reason="Explicit Uncertainty State Triggered (SIH 2025 Compliance). Flagged for human review.",
                geo_boost_applied=geo_boost,
            ),
            human_review_flagged=True,
            exception_id=exception_id,
            uncertainty=uncertainty_res,
        )

    # --- CASE D: REVIEW REQUIRED (GEODETIC CONFLICT OR DEGRADED QUALITY) ---
    if decision == DecisionState.REVIEW_REQUIRED:
        return VerificationResponse(
            is_monument=False,
            verification_status=DecisionState.REVIEW_REQUIRED.value,
            is_uncertain=True,
            verification_tier="REVIEW REQUIRED // CURATORIAL AUDIT FLAGGED",
            confidence_score=round(best_score * 100.0, 1),
            monument_name=f"Potential {best_name} (Audit Required)",
            rejection_message=uncertainty_res.explanation,
            pipeline_telemetry=PipelineTelemetry(
                exif_gps=exif_gps,
                architectural_gatekeeper_score=arch_prob,
                top_3_candidates=top_3_telemetry,
                decision_reason=uncertainty_res.explanation,
                geo_boost_applied=geo_boost,
            ),
            human_review_flagged=True,
            exception_id=exception_id,
            uncertainty=uncertainty_res,
        )

    # --- CASE E: NON-MONUMENT REJECTED ---
    return VerificationResponse(
        is_monument=False,
        verification_status=DecisionState.NON_MONUMENT_REJECTED.value,
        is_uncertain=False,
        verification_tier="REJECTED // NON-MONUMENT SPECIMEN",
        confidence_score=round(max(best_score * 100.0, (1.0 - arch_prob) * 100.0), 1),
        rejection_message=uncertainty_res.explanation,
        pipeline_telemetry=PipelineTelemetry(
            exif_gps=exif_gps,
            architectural_gatekeeper_score=arch_prob,
            top_3_candidates=top_3_telemetry,
            decision_reason="Specimen failed architectural gatekeeper and retrieval similarity thresholds.",
            geo_boost_applied=geo_boost,
        ),
        human_review_flagged=False,
        exception_id=None,
        uncertainty=uncertainty_res,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
