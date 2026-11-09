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
torch.set_num_threads(2)
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel, Field
from transformers import CLIPModel, CLIPProcessor

# Ensure backend dir is on sys.path for direct imports
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import Calibration, Uncertainty, and Knowledge Engine modules
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
from knowledge_schema import (
    AskKnowledgeRequest,
    AskKnowledgeResponse,
    GroundedKnowledgeRecord,
    HistoricalEvent,
    SourceCitation,
)
from knowledge_engine import GroundedKnowledgeEngine
from gemini_service import (
    gemini_service,
    telemetry_manager,
    UnknownHeritageAnalysis,
    GeminiAdjudicationResult,
    ArchitecturalExplanation,
)
from catalogue_service import (
    check_catalogue_membership,
    CatalogueStatus,
    CatalogueMembershipResult,
    get_catalogue_100,
)
from local_feature_engine import local_feature_engine
from shadow_engine import shadow_engine

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
KNOWLEDGE_SOURCES_FILE = BASE_DIR / "knowledge_sources.json"
CATALOGUE_100_FILE = BASE_DIR / "datasets" / "heritage_catalogue_100.json"

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
    "catalogue_100": {},
    "gatekeeper_pos_vec": None,
    "gatekeeper_neg_vec": None,
    "gemini_client": None,
    "gemini_configured": False,
    "calibration_engine": None,
    "uncertainty_engine": None,
    "knowledge_engine": None,
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
    margin_threshold: float = 0.08


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
    tier2_analysis: Optional[Dict[str, Any]] = None
    local_features: Optional[Dict[str, Any]] = None
    out_of_catalog_identified: bool = False
    catalogue_status: Optional[str] = "OUT_OF_CATALOG"


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
            model=gemini_service.model_name,
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


# --- Backend Initialization Helper ---

def initialize_backend_resources(gemini_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Initializes CLIP, FAISS, Gatekeeper embeddings, and Tier-2 services.
    Idempotent: Reuses existing in-memory models if already loaded.
    """
    if state.get("clip_model") is not None and state.get("faiss_index") is not None:
        if gemini_api_key and not state.get("gemini_configured"):
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            if hasattr(gemini_service, "initialize"):
                gemini_service.initialize()
            state["gemini_service"] = gemini_service
            state["gemini_client"] = getattr(gemini_service, "client", None)
            state["gemini_configured"] = gemini_service.is_available()
        return state

    logger.info("Initializing Heritage Monument Recognition Engine (SIH 2025)...")
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key

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

    # 4B. Load 100-Site Extended Heritage Catalogue (Phase 8.6)
    if CATALOGUE_100_FILE.exists():
        with open(CATALOGUE_100_FILE, "r", encoding="utf-8") as f:
            state["catalogue_100"] = json.load(f)
        logger.info(f"Loaded Phase 8.6 Heritage Catalogue: {len(state['catalogue_100'])} sites (50 Indian + 50 International).")
    else:
        logger.warning(f"100-Site Heritage Catalogue not found at {CATALOGUE_100_FILE}.")

    # 5. Initialize Confidence Calibration, Uncertainty & Knowledge Engines
    calibration_engine = CalibrationEngine(CALIBRATION_CONFIG_FILE)
    uncertainty_engine = UncertaintyEngine(calibration_engine)
    state["calibration_engine"] = calibration_engine
    state["uncertainty_engine"] = uncertainty_engine

    knowledge_engine = GroundedKnowledgeEngine(KNOWLEDGE_SOURCES_FILE)
    state["knowledge_engine"] = knowledge_engine

    logger.info(f"Loaded Confidence Calibration Engine: Status = {calibration_engine.calibration_status}")
    logger.info(f"Loaded Grounded Knowledge Engine: {len(knowledge_engine.records)} verified records from {KNOWLEDGE_SOURCES_FILE.name}")

    # Ensure exceptions file exists
    if not EXCEPTIONS_FILE.exists():
        save_exceptions_log([])

    logger.info(
        f"Loaded FAISS index with {state['faiss_index'].ntotal} vectors, "
        f"{len(state['labels'])} labels, and {len(state['metadata'])} monument metadata records."
    )

    # 5B. Initialize Local Feature Engine with CLIP resources and pre-indexed reference vectors
    local_feature_engine.set_clip_resources(
        state["clip_model"],
        state["clip_processor"],
        state["device"]
    )
    ref_items = []
    for item in state["labels"]:
        idx_id = item["index_id"]
        vec = state["faiss_index"].reconstruct(idx_id)
        ref_items.append({
            "image_id": item.get("image_id", str(idx_id)),
            "monument_key": item["monument_key"],
            "monument_name": item["monument_name"],
            "embedding": vec,
            "file_path": item.get("file_path"),
            "view_type": item.get("view_type"),
        })
    state["reference_items"] = ref_items
    logger.info(f"Loaded {len(ref_items)} reference views into Local Feature Engine cache.")

    # 6. Initialize Gemini Tier 2 Service
    state["gemini_service"] = gemini_service
    state["gemini_client"] = gemini_service.client
    state["gemini_configured"] = gemini_service.is_available()
    if state["gemini_configured"]:
        logger.info(f"Gemini Tier 2 VLM service operational ({gemini_service.model_name}).")
    else:
        logger.info("Running Tier-2 in pure offline fallback mode.")

    # 7. Initialize Policy D Shadow Staging Engine (Phase 8.4C)
    state["shadow_engine"] = shadow_engine
    logger.info(
        f"Policy D Shadow Staging Engine: ENABLED={shadow_engine.is_enabled()} "
        f"[workers={shadow_engine.config.max_workers}, max_queue={shadow_engine.config.max_queue_size}, "
        f"timeout={shadow_engine.config.timeout_seconds*1000:.0f}ms]"
    )

    logger.info("Engine startup complete. Service ready.")
    return state


# --- Lifespan Initialization ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_backend_resources()
    yield
    logger.info("Service shutting down...")
    shadow_engine.shutdown()


# --- FastAPI Application ---

app = FastAPI(
    title="Visual Heritage Recognition & Grounded Cultural Discovery Platform",
    description="Project No. 30 (SIH 2025): Two-Tier Hybrid Architecture with Calibrated Uncertainty Engine",
    version="2.1.0",
    lifespan=lifespan,
)

# Production-grade CORS configuration with environment-variable allowlist
raw_origins = os.environ.get("CORS_ORIGINS", "*").strip()
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]
is_wildcard = "*" in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else allowed_origins,
    allow_credentials=not is_wildcard,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Serve static dataset images for client preview & verification
if DATASET_DIR.exists():
    app.mount("/dataset", StaticFiles(directory=str(DATASET_DIR)), name="dataset")


# --- API Routes ---

@app.get("/")
def get_root():
    """Root entry point providing discovery links for documentation and health checks."""
    return {
        "platform": "Visual Heritage Recognition & Grounded Cultural Discovery Platform",
        "status": "online",
        "documentation": "/docs",
        "health_check": "/api/health",
        "catalogue": "/api/catalogue",
        "verify_endpoint": "POST /api/verify-monument",
    }


@app.get("/api/health")
def get_health():
    """Returns live engine health and diagnostic status."""
    calib = state.get("calibration_engine")
    ke = state.get("knowledge_engine")
    return {
        "status": "healthy",
        "faiss_vectors_loaded": state["faiss_index"].ntotal if state["faiss_index"] else 0,
        "clip_device": state["device"],
        "gemini_tier2_configured": gemini_service.is_available(),
        "gemini_tier2_model": gemini_service.model_name,
        "monuments_count": len(state["metadata"]),
        "catalogue_100_count": len(state.get("catalogue_100", {})),
        "knowledge_records_count": len(ke.records) if ke else 0,
        "exceptions_count": len(load_exceptions_log()),
        "calibration_status": calib.calibration_status if calib else "UNCALIBRATED",
    }


@app.get("/api/monuments")
def get_monuments_catalog(
    country: Optional[str] = None,
    category: Optional[str] = None,
    readiness: Optional[str] = None,
    search: Optional[str] = None,
    scope: Optional[str] = None,
):
    """
    Returns the comprehensive catalog of heritage monuments.
    By default returns the full 100-site heritage catalogue (50 Indian + 50 International).
    Supports filtering by country, category, recognition readiness, and search query.
    If scope == 'flagship', returns the original 10 core monuments for backward compatibility.
    """
    cat_source = state.get("catalogue_100") or state["metadata"]
    if scope == "flagship":
        return {
            "total": len(state["metadata"]),
            "catalogue_size": len(state["metadata"]),
            "monuments": state["metadata"],
        }

    filtered = {}
    for mid, item in cat_source.items():
        if country and country.lower() != "all":
            c_low = country.lower()
            item_c = item.get("country", "").lower()
            if c_low == "india" and item_c != "india":
                continue
            elif c_low == "international" and item_c == "india":
                continue
            elif c_low not in ["india", "international"] and item_c != c_low:
                continue

        if category and category.lower() != "all":
            if item.get("category", "").lower() != category.lower():
                continue

        if readiness and readiness.lower() != "all":
            if item.get("recognition_readiness", "").lower() != readiness.lower():
                continue

        if search:
            s = search.lower().strip()
            name_match = s in item.get("monument_name", "").lower()
            key_match = s in mid.lower()
            city_match = s in item.get("city_region", "").lower()
            state_match = s in item.get("state_province", "").lower()
            country_match = s in item.get("country", "").lower()
            loc_match = s in item.get("location", "").lower()
            alt_match = any(s in alt.lower() for alt in item.get("alternate_names", []))
            if not (name_match or key_match or city_match or state_match or country_match or loc_match or alt_match):
                continue

        filtered[mid] = item

    return {
        "total": len(filtered),
        "catalogue_size": len(cat_source),
        "monuments": filtered,
    }


# --- Phase 6.3 Grounded Knowledge Engine Endpoints ---

@app.get("/api/monuments/{monument_id}/knowledge", response_model=GroundedKnowledgeRecord)
def get_monument_knowledge(monument_id: str):
    """
    Phase 6.3: Retrieves authoritative, source-backed historical, architectural,
    and preservation knowledge for a recognized monument.
    """
    engine: GroundedKnowledgeEngine = state.get("knowledge_engine")
    if not engine:
        raise HTTPException(status_code=500, detail="Knowledge Engine is not initialized.")

    record = engine.get_knowledge(monument_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grounded knowledge record for monument '{monument_id}' was not found in the curatorial register."
        )
    return record


@app.get("/api/monuments/{monument_id}/timeline", response_model=List[HistoricalEvent])
def get_monument_timeline(monument_id: str):
    """
    Phase 6.3: Retrieves verified chronological historical timeline events for a monument.
    """
    engine: GroundedKnowledgeEngine = state.get("knowledge_engine")
    if not engine:
        raise HTTPException(status_code=500, detail="Knowledge Engine is not initialized.")

    if monument_id not in engine.records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monument '{monument_id}' was not found in the historical register."
        )
    return engine.get_timeline(monument_id)


@app.get("/api/monuments/{monument_id}/sources", response_model=List[SourceCitation])
def get_monument_sources(monument_id: str):
    """
    Phase 6.3: Retrieves primary source citations (ASI, UNESCO, Ministry of Culture, Gazetteers)
    validating the historical monograph for a monument.
    """
    engine: GroundedKnowledgeEngine = state.get("knowledge_engine")
    if not engine:
        raise HTTPException(status_code=500, detail="Knowledge Engine is not initialized.")

    if monument_id not in engine.records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monument '{monument_id}' was not found in the source register."
        )
    return engine.get_sources(monument_id)


@app.post("/api/monuments/{monument_id}/ask", response_model=AskKnowledgeResponse)
def ask_monument_archive(monument_id: str, payload: AskKnowledgeRequest):
    """
    Phase 6.3: Retrieval-First 'Ask the Archive' Q&A.
    Answers inquiries strictly anchored to verified ASI & UNESCO historical excerpts.
    Explicitly refuses to guess or hallucinate when evidence is insufficient.
    Operates offline or with Gemini 2.5 Flash when configured.
    """
    engine: GroundedKnowledgeEngine = state.get("knowledge_engine")
    if not engine:
        raise HTTPException(status_code=500, detail="Knowledge Engine is not initialized.")

    if monument_id not in engine.records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monument '{monument_id}' was not found in the knowledge register."
        )

    clean_question = payload.question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inquiry question cannot be empty or solely whitespace."
        )

    gemini_handler = state.get("gemini_service") if gemini_service.is_available() else state.get("gemini_client")
    return engine.ask_archive(
        monument_id=monument_id,
        question=clean_question,
        gemini_client=gemini_handler,
    )


# --- Phase 7.2 Gemini Tier-2 Diagnostics & Architectural Explanation ---

@app.get("/api/telemetry/gemini")
def get_gemini_telemetry():
    """Phase 7.2: Returns safe aggregated telemetry for Gemini Tier-2 usage without sensitive keys."""
    return telemetry_manager.get_public_stats()


@app.post("/api/monuments/{monument_id}/explain-architecture")
async def explain_monument_architecture(
    monument_id: str,
    file: UploadFile = File(...),
):
    """
    Phase 7.2 Capability C:
    Generates a structured architectural explanation rigorously separating
    directly visible observations from stylistic interpretations and verified facts.
    """
    try:
        content = await file.read()
        with Image.open(io.BytesIO(content)) as pil_img:
            image_rgb = pil_img.convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}")

    m_data = state["metadata"].get(monument_id, {})
    m_name = m_data.get("monument_name", monument_id.replace("_", " ").title())
    verified_facts = m_data.get("structural_features_detected", [])

    explanation = gemini_service.explain_architecture(
        image=image_rgb,
        monument_name=m_name,
        verified_facts=verified_facts,
    )
    return explanation.dict()


# --- Phase 8.0B Dedicated Local Architectural Feature Recognition ---

@app.post("/api/recognition/local-features")
async def analyze_local_features_endpoint(file: UploadFile = File(...)):
    """
    Phase 8.0B Dedicated Local Architectural Feature Recognition & Geometric Verification:
    - Extracts multi-scale architectural regions (upper crown, arcade/columns, lower friezes, gradient saliency).
    - Extracts local CLIP embeddings per region crop.
    - Matches regions against 210 reference gallery views.
    - Performs classical SIFT keypoint extraction and RANSAC homography estimation.
    - Evaluates cross-modal alignment between global and localized evidence.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        with Image.open(io.BytesIO(content)) as raw_img:
            image_rgb = raw_img.convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}")

    img_vec = compute_clip_image_embedding(image_rgb)
    arch_prob = evaluate_architectural_gatekeeper(img_vec)

    query_matrix = np.expand_dims(img_vec, axis=0).astype(np.float32)
    raw_distances, raw_indices = state["faiss_index"].search(query_matrix, 5)

    global_cand = None
    if len(raw_indices[0]) > 0 and raw_indices[0][0] >= 0:
        idx_0 = int(raw_indices[0][0])
        lbl = state["labels"][idx_0]
        global_cand = {
            "monument_key": lbl["monument_key"],
            "monument_name": lbl["monument_name"],
            "similarity": float(raw_distances[0][0]),
        }

    local_results = local_feature_engine.match_local_features(
        image=image_rgb,
        reference_images=state.get("reference_items", []),
        top_k_candidates=5
    )

    hybrid_summary = local_feature_engine.evaluate_hybrid_evidence(
        global_candidate=global_cand,
        local_results=local_results,
        gatekeeper_score=arch_prob,
    )

    return {
        "global_candidate": global_cand,
        "gatekeeper_score": round(arch_prob, 4),
        "local_analysis": local_results,
        "hybrid_alignment": hybrid_summary,
    }


@app.get("/api/exceptions")
def get_exceptions_list():
    """Curator Exception Log: Returns flagged or ambiguous scans awaiting human oversight."""
    exceptions = load_exceptions_log()
    return {
        "total": len(exceptions),
        "exceptions": exceptions,
    }


CURATOR_API_KEY = os.environ.get("CURATOR_API_KEY", "").strip()


@app.post("/api/exceptions/{exception_id}/resolve")
def resolve_exception(
    exception_id: str,
    payload: ResolveExceptionRequest,
    x_curator_key: Optional[str] = Header(None, alias="X-Curator-Key"),
):
    """Allows an authorized curator to inspect and resolve a flagged exception item while preserving audit history."""
    if CURATOR_API_KEY and x_curator_key != CURATOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Valid X-Curator-Key header required to resolve curator exceptions."
        )

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


async def process_verification_pipeline(image_bytes: bytes, filename: str = "upload.jpg") -> VerificationResponse:
    """
    Core Phase 6.2 Advanced Recognition & Calibrated Uncertainty Pipeline.
    Can be invoked directly by FastAPI endpoints, web applications, or scripts.
    """
    # 0. Enforce upload size limit & prevent memory DOS
    MAX_UPLOAD_SIZE = 15 * 1024 * 1024  # 15 MB
    if len(image_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            detail="Payload too large: Image exceeds 15 MB limit."
        )

    # 1. Validate image bytes
    try:
        if not image_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        with Image.open(io.BytesIO(image_bytes)) as raw_img:
            raw_img.verify()

        with Image.open(io.BytesIO(image_bytes)) as valid_img:
            image_rgb = valid_img.convert("RGB")
            # Dynamic image dimension clamping to mitigate inference allocation spikes
            if image_rgb.width > 1024 or image_rgb.height > 1024:
                image_rgb.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
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

    # 4B. Conditional Local Architectural Feature & Geometric Corroboration (Tier 1C)
    local_features_data = None
    is_decisive_global = (
        best_score >= 0.85
        and uncertainty_res.similarity_margin >= 0.10
        and arch_prob >= 0.70
        and not uncertainty_res.gps_evidence.gps_conflict
    )
    is_non_monument = (arch_prob < 0.40 and best_score < 0.65) or (uncertainty_res.decision == DecisionState.NON_MONUMENT_REJECTED)
    should_run_local = (not is_decisive_global) and (not is_non_monument) and bool(state.get("reference_items"))

    if should_run_local:
        try:
            local_eval = local_feature_engine.match_local_features(
                image=image_rgb,
                reference_images=state["reference_items"],
                top_k_candidates=3
            )
            hybrid_eval = local_feature_engine.evaluate_hybrid_evidence(
                global_candidate={"monument_key": best_key, "similarity": best_score} if best_cand else None,
                local_results=local_eval,
                gatekeeper_score=arch_prob,
            )
            local_features_data = {
                "execution_mode": "TRIGGERED_AMBIGUOUS_SPECIMEN",
                "top_local_candidate": local_eval.get("top_candidate"),
                "regions_evaluated": local_eval.get("regions_evaluated", 0),
                "geometric_verification": local_eval.get("geometric_verification"),
                "sift_triggered": local_eval.get("sift_triggered", False),
                "alignment_status": hybrid_eval.get("alignment_status"),
                "alignment_explanation": hybrid_eval.get("explanation"),
                "override_applied": hybrid_eval.get("override_applied", False),
                "evidence_quality": hybrid_eval.get("evidence_quality"),
                "latency_ms": local_eval.get("latency_ms", 0.0),
            }

            # If initially flagged as UNCERTAIN_MATCH due to candidate competition,
            # allow local architectural feature evidence to corroborate high-confidence matches:
            if uncertainty_res.decision == DecisionState.UNCERTAIN_MATCH:
                corroborated_res = uncertainty_engine.evaluate(
                    image=image_rgb,
                    gatekeeper_score=arch_prob,
                    raw_distances=raw_distances[0],
                    raw_indices=raw_indices[0],
                    labels=state["labels"],
                    metadata=state["metadata"],
                    exif_gps=exif_gps,
                    local_feature_corroboration={
                        "alignment_status": hybrid_eval.get("alignment_status"),
                        "top_local_candidate": local_eval.get("top_candidate"),
                        "geometric_verification": local_eval.get("geometric_verification"),
                    },
                )
                if corroborated_res.decision == DecisionState.VERIFIED_MATCH:
                    uncertainty_res = corroborated_res
                    logger.info(
                        f"Local architectural feature corroboration confirmed VERIFIED_MATCH for {best_key} "
                        f"(top1_sim={best_score:.4f}, margin={uncertainty_res.similarity_margin:.4f})."
                    )
        except Exception as e:
            logger.warning(f"Local feature evaluation encountered non-fatal error: {e}")
    else:
        bypass_reason = "DECISIVE_GLOBAL_MATCH" if is_decisive_global else "NON_MONUMENT_REJECTED"
        local_features_data = {
            "execution_mode": "BYPASS_OPTIMIZED",
            "routing_reason": bypass_reason,
            "regions_evaluated": 0,
            "geometric_verification": {"status": "BYPASSED", "inliers_count": 0},
            "sift_triggered": False,
            "override_applied": False,
            "alignment_status": "DECISIVE_GLOBAL_MATCH" if is_decisive_global else "BYPASSED",
            "alignment_explanation": (
                "Decisive global CLIP alignment observed (high similarity, decisive margin, strong gatekeeper). "
                "Local feature extraction bypassed to maintain ~130ms low-latency execution."
                if is_decisive_global
                else "Non-monument scene rejected by architectural gatekeeper. Local feature processing bypassed."
            ),
            "latency_ms": 0.0,
        }

    # 5. Gemini 3.1 Flash-Lite Open-World Adjudication Stage (Phase 8.5F & 8.6B)
    tier2_analysis_dict = None
    gemini_adjudication = None
    is_out_of_catalog_identified = False
    is_catalog_metadata_only = False
    final_decision = uncertainty_res.decision
    adjudicated_membership: Optional[CatalogueMembershipResult] = None
    final_catalogue_status = CatalogueStatus.OUT_OF_CATALOG.value

    should_adjudicate = (
        gemini_service.is_available()
        and uncertainty_res.decision in [
            DecisionState.UNCERTAIN_MATCH,
            DecisionState.UNKNOWN_HERITAGE_SPECIMEN,
            DecisionState.REVIEW_REQUIRED,
        ]
        and arch_prob >= 0.40
    )

    if should_adjudicate:
        logger.info(
            f"Invoking Gemini 3.1 Flash-Lite Open-World Adjudication (decision={uncertainty_res.decision.value}, "
            f"arch_prob={arch_prob:.4f}, best_score={best_score:.4f}, top_cand={best_cand})..."
        )
        gemini_adjudication = gemini_service.adjudicate_monument(image_rgb)
        tier2_analysis_dict = gemini_adjudication.model_dump()

        # Shared Canonical Membership Lookup (Phase 8.6B Hotfix)
        adjudicated_membership = check_catalogue_membership(gemini_adjudication.proposed_identity)
        final_catalogue_status = adjudicated_membership.status.value

        # Conservative Adjudication Policy:
        # D. Non-monument rejection: If Gemini explicitly identifies image as non-heritage structure
        if not gemini_adjudication.is_heritage_structure:
            logger.info("Gemini adjudication determined specimen is NOT a heritage structure.")
            final_decision = DecisionState.NON_MONUMENT_REJECTED
            final_catalogue_status = CatalogueStatus.OUT_OF_CATALOG.value

        # B1. Identifiable Catalogued Metadata-Only Monument (e.g. Ajanta Caves, Golden Temple, Mysore Palace):
        elif (
            gemini_adjudication.is_heritage_structure
            and gemini_adjudication.proposed_identity
            and len(gemini_adjudication.proposed_identity.strip()) > 3
            and len(gemini_adjudication.visible_architectural_evidence.strip()) >= 20
            and gemini_adjudication.qualitative_confidence.upper() in ["HIGH", "MEDIUM"]
            and adjudicated_membership.status == CatalogueStatus.CATALOGUED_METADATA_ONLY
            and not gemini_adjudication.is_offline_fallback
        ):
            logger.info(
                f"Gemini adjudication confirmed CATALOGUED METADATA-ONLY monument: "
                f"'{gemini_adjudication.proposed_identity}' -> ID '{adjudicated_membership.monument_id}'"
            )
            final_decision = DecisionState.UNKNOWN_HERITAGE_SPECIMEN
            is_catalog_metadata_only = True
            is_out_of_catalog_identified = False
            final_catalogue_status = CatalogueStatus.CATALOGUED_METADATA_ONLY.value

        # B2. Identifiable Truly Out-of-Catalog Monument (e.g. Eiffel Tower):
        elif (
            gemini_adjudication.is_heritage_structure
            and gemini_adjudication.proposed_identity
            and len(gemini_adjudication.proposed_identity.strip()) > 3
            and len(gemini_adjudication.visible_architectural_evidence.strip()) >= 20
            and gemini_adjudication.qualitative_confidence.upper() in ["HIGH", "MEDIUM"]
            and adjudicated_membership.status == CatalogueStatus.OUT_OF_CATALOG
            and not gemini_adjudication.is_offline_fallback
        ):
            logger.info(
                f"Gemini adjudication confirmed OUT-OF-CATALOG monument: "
                f"'{gemini_adjudication.proposed_identity}' -> UNKNOWN_HERITAGE_SPECIMEN (OUT_OF_CATALOG)"
            )
            final_decision = DecisionState.UNKNOWN_HERITAGE_SPECIMEN
            is_out_of_catalog_identified = True
            is_catalog_metadata_only = False
            final_catalogue_status = CatalogueStatus.OUT_OF_CATALOG.value

        # B3. Flagship / Recognition-Ready Monument (e.g. Taj Mahal, Qutub Minar, Ajanta Caves confirmed under uncertainty):
        elif (
            gemini_adjudication.is_heritage_structure
            and gemini_adjudication.proposed_identity
            and len(gemini_adjudication.proposed_identity.strip()) > 3
            and len(gemini_adjudication.visible_architectural_evidence.strip()) >= 20
            and gemini_adjudication.qualitative_confidence.upper() in ["HIGH", "MEDIUM"]
            and adjudicated_membership.status == CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY
            and not gemini_adjudication.is_offline_fallback
        ):
            cand_match = next((c for c in top_candidates_agg if getattr(c, "monument_key", None) == best_key), None)
            cand_sim = getattr(cand_match, "max_similarity", 0.0) if cand_match else 0.0
            has_visual_support = (cand_match is not None and cand_sim >= 0.55) or (local_features_data.get("geometric_verification", {}).get("status") == "VERIFIED")
            
            if has_visual_support:
                logger.info(
                    f"Gemini adjudication confirmed RECOGNITION-READY catalog monument with visual support: "
                    f"'{gemini_adjudication.proposed_identity}' -> ID '{best_key}' (visual_sim={cand_sim:.4f})"
                )
                final_decision = DecisionState.VERIFIED_MATCH
                if cand_match:
                    best_cand = cand_match
                    best_score = max(best_score, getattr(cand_match, "max_similarity", 0.85))
                else:
                    best_score = max(best_score, 0.85)
                is_out_of_catalog_identified = False
                is_catalog_metadata_only = False
                final_catalogue_status = CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY.value
            else:
                logger.warning(
                    f"Adjudicated catalog monument '{best_key}' lacks visual support (cand_sim={cand_sim:.4f} < 0.55). "
                    f"Preventing forced VERIFIED_MATCH; classifying as UNKNOWN_HERITAGE_SPECIMEN."
                )
                final_decision = DecisionState.UNKNOWN_HERITAGE_SPECIMEN
                is_out_of_catalog_identified = True
                is_catalog_metadata_only = False
                final_catalogue_status = CatalogueStatus.OUT_OF_CATALOG.value

        # C. Uncertain identity / generic masonry: retain original uncertainty decision
        else:
            logger.info(
                f"Gemini adjudication retained original uncertainty decision ({uncertainty_res.decision.value})."
            )

    # 6. Handle Human Review Exception Logging
    exception_id = None
    if final_decision != DecisionState.VERIFIED_MATCH and (
        uncertainty_res.requires_human_review
        or final_decision in [DecisionState.UNCERTAIN_MATCH, DecisionState.UNKNOWN_HERITAGE_SPECIMEN, DecisionState.REVIEW_REQUIRED]
    ):
        exc_reason = (
            f"Out-of-catalog monument identified: {gemini_adjudication.proposed_identity}"
            if is_out_of_catalog_identified and gemini_adjudication and gemini_adjudication.proposed_identity
            else uncertainty_res.explanation
        )
        exception_id = record_exception_entry(
            filename=filename or "uploaded_specimen.jpg",
            gatekeeper_score=arch_prob,
            top_candidate=best_cand,
            reason=exc_reason,
            specimen_hash=specimen_hash,
            top_candidates_list=top_candidates_agg,
            similarity_margin=uncertainty_res.similarity_margin,
            reason_codes=uncertainty_res.reason_codes,
            calibration_status=uncertainty_res.calibration_status,
        )

    # 7. Map Final Adjudicated State to Backward-Compatible VerificationResponse
    decision = final_decision

    # --- CASE A: VERIFIED MATCH ---
    if decision == DecisionState.VERIFIED_MATCH and (best_key in state["metadata"] or best_key in state.get("catalogue_100", {})):
        m_data = state["metadata"].get(best_key) or state.get("catalogue_100", {}).get(best_key, {})
        catalog_id = CATALOG_ID_MAP.get(best_key, f"ASI-ARCH-{best_key[:3].upper()}-00")
        heuristic_conf_pct = round(min(best_score * 100.0, 99.8), 1)

        citations = None
        if "grounded_citations" in m_data and m_data["grounded_citations"]:
            citations = GroundedCitations(**m_data["grounded_citations"])

        # Determine tier: if resolved by Tier 2 adjudication, specify Tier 2
        if gemini_adjudication and uncertainty_res.decision != DecisionState.VERIFIED_MATCH:
            tier_str = f"TIER 2 // {gemini_service.model_name.upper()} ADJUDICATION"
            decision_expl = f"Candidate ambiguity resolved via Tier 2 Multimodal Adjudication ({gemini_service.model_name}): Confirmed '{best_name}'."
        else:
            tier_str = "TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX"
            decision_expl = uncertainty_res.explanation

        response_obj = VerificationResponse(
            is_monument=True,
            verification_status=DecisionState.VERIFIED_MATCH.value,
            is_uncertain=False,
            verification_tier=tier_str,
            confidence_score=heuristic_conf_pct,
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
            grounded_citations=citations,
            pipeline_telemetry=PipelineTelemetry(
                exif_gps=exif_gps,
                architectural_gatekeeper_score=arch_prob,
                top_3_candidates=top_3_telemetry,
                decision_reason=decision_expl,
                geo_boost_applied=geo_boost,
                margin_threshold=round(uncertainty_engine.calibration.uncertainty_margin_threshold, 4),
            ),
            human_review_flagged=False,
            exception_id=None,
            uncertainty=uncertainty_res,
            tier2_analysis=tier2_analysis_dict,
            local_features=local_features_data,
            out_of_catalog_identified=False,
            catalogue_status=CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY.value,
        )

    # --- CASE B: UNCERTAIN MATCH (CANDIDATE COMPETITION) ---
    elif decision == DecisionState.UNCERTAIN_MATCH:
        m_data = state["metadata"].get(best_key, {})
        catalog_id = CATALOG_ID_MAP.get(best_key, f"ASI-ARCH-{best_key[:3].upper()}-00")

        response_obj = VerificationResponse(
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
                margin_threshold=round(uncertainty_engine.calibration.uncertainty_margin_threshold, 4),
            ),
            human_review_flagged=True,
            exception_id=exception_id,
            uncertainty=uncertainty_res,
            tier2_analysis=tier2_analysis_dict,
            local_features=local_features_data,
            out_of_catalog_identified=False,
            catalogue_status=CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY.value if best_key in state["metadata"] else CatalogueStatus.OUT_OF_CATALOG.value,
        )

    # --- CASE C: UNKNOWN HERITAGE SPECIMEN ---
    elif decision == DecisionState.UNKNOWN_HERITAGE_SPECIMEN:
        if is_catalog_metadata_only and adjudicated_membership and gemini_adjudication:
            mon_name = adjudicated_membership.monument_name or gemini_adjudication.proposed_identity
            loc_name = adjudicated_membership.location or gemini_adjudication.proposed_location
            v_tier = f"CATALOGUED — METADATA ONLY // {gemini_service.model_name.upper()}"
            features_list = gemini_adjudication.distinguishing_features or [
                gemini_adjudication.visible_architectural_evidence
            ]
            rej_msg = (
                f"Specimen catalogued in 100-Site Heritage Register ('{mon_name}'). "
                f"Metadata verified; visual identification by {gemini_service.model_name} (Tier 1 vector anchors pending field photographic survey)."
            )
            cat_id = (adjudicated_membership.monument_id or "SITE").upper()
            coords = adjudicated_membership.coordinates
            entry = adjudicated_membership.catalog_entry or {}
            arch_style = entry.get("architectural_style")
            built_era = entry.get("historical_period")
            hist_sum = entry.get("verified_description")
            pres_stat = entry.get("preservation_status")
            status_val = CatalogueStatus.CATALOGUED_METADATA_ONLY.value
            is_mon = True
            is_ooc = False

        elif is_out_of_catalog_identified and gemini_adjudication:
            mon_name = gemini_adjudication.proposed_identity
            loc_name = gemini_adjudication.proposed_location or "Geographic location pending curatorial confirmation"
            v_tier = f"OUT-OF-CATALOG HERITAGE IDENTIFIED // {gemini_service.model_name.upper()}"
            features_list = gemini_adjudication.distinguishing_features or [
                gemini_adjudication.visible_architectural_evidence
            ]
            rej_msg = (
                f"Specimen visually identified as out-of-catalog heritage site '{mon_name}'. "
                f"Curatorial verification and catalogue expansion recommended."
            )
            cat_id = None
            coords = None
            arch_style = None
            built_era = None
            hist_sum = None
            pres_stat = None
            status_val = CatalogueStatus.OUT_OF_CATALOG.value
            is_mon = True
            is_ooc = True

        else:
            mon_name = "Unindexed / Ambiguous Heritage Site"
            loc_name = None
            v_tier = "UNKNOWN SPECIMEN // UNINDEXED OR AMBIGUOUS HERITAGE SITE"
            features_list = []
            rej_msg = uncertainty_res.explanation
            cat_id = None
            coords = None
            arch_style = None
            built_era = None
            hist_sum = None
            pres_stat = None
            status_val = CatalogueStatus.OUT_OF_CATALOG.value
            is_mon = False
            is_ooc = False

        response_obj = VerificationResponse(
            is_monument=is_mon,
            verification_status=DecisionState.UNKNOWN_HERITAGE_SPECIMEN.value,
            is_uncertain=True,
            verification_tier=v_tier,
            confidence_score=round(best_score * 100.0, 1),
            monument_name=mon_name,
            catalog_id=cat_id,
            location=loc_name,
            coordinates=coords,
            architectural_style=arch_style,
            built_by_or_era=built_era,
            historical_summary=hist_sum,
            preservation_status=pres_stat,
            structural_features_detected=features_list,
            rejection_message=rej_msg,
            out_of_catalog_identified=is_ooc,
            catalogue_status=status_val,
            pipeline_telemetry=PipelineTelemetry(
                exif_gps=exif_gps,
                architectural_gatekeeper_score=arch_prob,
                top_3_candidates=top_3_telemetry,
                decision_reason=(
                    f"Catalogue metadata-only monument identified by {gemini_service.model_name}: {mon_name}"
                    if is_catalog_metadata_only
                    else (
                        f"Out-of-catalog heritage monument adjudicated by {gemini_service.model_name}: {mon_name}"
                        if is_out_of_catalog_identified
                        else "Explicit Uncertainty State Triggered (SIH 2025 Compliance). Flagged for human review."
                    )
                ),
                geo_boost_applied=geo_boost,
                margin_threshold=round(uncertainty_engine.calibration.uncertainty_margin_threshold, 4),
            ),
            human_review_flagged=True,
            exception_id=exception_id,
            uncertainty=uncertainty_res,
            tier2_analysis=tier2_analysis_dict,
            local_features=local_features_data,
        )

    # --- CASE D: REVIEW REQUIRED (GEODETIC CONFLICT OR DEGRADED QUALITY) ---
    elif decision == DecisionState.REVIEW_REQUIRED:
        response_obj = VerificationResponse(
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
                margin_threshold=round(uncertainty_engine.calibration.uncertainty_margin_threshold, 4),
            ),
            human_review_flagged=True,
            exception_id=exception_id,
            uncertainty=uncertainty_res,
            tier2_analysis=tier2_analysis_dict,
            local_features=local_features_data,
            out_of_catalog_identified=False,
            catalogue_status=CatalogueStatus.CATALOGUED_AND_RECOGNITION_READY.value if best_key in state["metadata"] else CatalogueStatus.OUT_OF_CATALOG.value,
        )

    # --- CASE E: NON-MONUMENT REJECTED ---
    else:
        response_obj = VerificationResponse(
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
                margin_threshold=round(uncertainty_engine.calibration.uncertainty_margin_threshold, 4),
            ),
            human_review_flagged=False,
            exception_id=None,
            uncertainty=uncertainty_res,
            tier2_analysis=tier2_analysis_dict,
            local_features=local_features_data,
            out_of_catalog_identified=False,
            catalogue_status=CatalogueStatus.OUT_OF_CATALOG.value,
        )

    # 8. Asynchronous / Non-blocking Shadow Evaluation of Candidate Policy D
    if shadow_engine.is_enabled():
        try:
            req_id = f"req_{specimen_hash}_{uuid.uuid4().hex[:8]}"
            shadow_engine.submit_shadow_evaluation(
                request_id=req_id,
                image=image_rgb,
                top1_key=best_key,
                top1_sim=best_score,
                margin=uncertainty_res.similarity_margin,
                gatekeeper_score=arch_prob,
                policy_a_decision=decision.value,
                policy_a_monument=best_key,
                reference_items=state.get("reference_items"),
                clip_model=state.get("clip_model"),
                clip_processor=state.get("clip_processor"),
            )
        except Exception as shadow_exc:
            logger.warning(f"Shadow staging submission failed silently without affecting response: {shadow_exc}")

    return response_obj


@app.post("/api/verify-monument", response_model=VerificationResponse)
async def verify_monument(file: UploadFile = File(...)):
    """
    FastAPI endpoint for monument verification.
    """
    image_bytes = await file.read()
    return await process_verification_pipeline(image_bytes, filename=file.filename or "upload.jpg")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
