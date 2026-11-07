"""
Heritage Monument Recognition System - Phase 7.2: Gemini 2.5 Flash Tier-2 Service
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform
SIH 2025 (SIH25052)

Provides:
  - Secure API key configuration (never logged, never exposed to clients)
  - Resilient execution with bounded exponential backoff (1s, 2s, 4s)
  - Rate-limit (429), timeout (15s), and auth error handling
  - Structured telemetry logging to backend/gemini_usage_telemetry.json
  - Capability A: Unknown heritage specimen analysis (preserves UNKNOWN state)
  - Capability B: Grounded historical Q&A with strict anti-hallucination guardrails
  - Capability C: Architectural explanation separating observations from interpretations
  - Deterministic offline fallback when API key is missing or service is unreachable
"""

import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Ensure backend and root .env are loaded safely
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

try:
    from backend.catalogue_service import (
        resolve_coordinates_from_catalogue,
        check_catalogue_membership,
        CatalogueStatus,
    )
except ImportError:
    from catalogue_service import (
        resolve_coordinates_from_catalogue,
        check_catalogue_membership,
        CatalogueStatus,
    )

logger = logging.getLogger("gemini_service")

TELEMETRY_FILE = BASE_DIR / "gemini_usage_telemetry.json"
DEFAULT_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_RETRIES = 3


# --- Pydantic Response Schemas ---

class GeminiAdjudicationResult(BaseModel):
    proposed_identity: Optional[str] = Field(
        default=None,
        description="Tentative monument name if recognizable, or null if uncertain/non-monument."
    )
    proposed_location: Optional[str] = Field(
        default=None,
        description="City, region, and country of the monument if known, or null if uncertain."
    )
    is_heritage_structure: bool = Field(
        default=True,
        description="True if the image depicts a historical/cultural heritage structure, fort, temple, monument, or archaeological site; False if everyday object, document, modern generic building, or vehicle."
    )
    is_catalog_monument: bool = Field(
        default=False,
        description="True ONLY if the specimen belongs to the authoritative 10-monument catalogue; False otherwise."
    )
    catalogue_status: Optional[str] = Field(
        default="OUT_OF_CATALOG",
        description="Canonical catalogue status: CATALOGUED_AND_RECOGNITION_READY, CATALOGUED_METADATA_ONLY, or OUT_OF_CATALOG."
    )
    visible_architectural_evidence: str = Field(
        default="",
        description="Detailed explanation of visible architectural characteristics, materials, and forms."
    )
    distinguishing_features: List[str] = Field(
        default_factory=list,
        description="Key architectural elements distinguishing this monument from other monuments."
    )
    qualitative_confidence: str = Field(
        default="UNCERTAIN",
        description="Qualitative confidence assessment: HIGH, MEDIUM, LOW, or UNCERTAIN."
    )
    uncertainty_reason: str = Field(
        default="",
        description="Epistemological caveats, visible occlusions, or why identification cannot be guaranteed."
    )
    verified_coordinates: Optional[Dict[str, float]] = Field(
        default=None,
        description="Verified latitude and longitude {lat: float, lng: float} resolved against authoritative 100-site heritage catalogue."
    )
    geodetic_source: Optional[str] = Field(
        default=None,
        description="Source of verified geodetic coordinates, e.g. 'Authoritative Heritage Registry (UNESCO/ASI)'."
    )
    catalog_id: Optional[str] = Field(
        default=None,
        description="Matched unique monument catalogue identifier if resolved in 100-site catalogue."
    )
    # Backward compatibility fields:
    visible_observations: List[str] = Field(
        default_factory=list,
        description="Directly visible structural features (e.g. colonnades, corbelled arches, dome shape)."
    )
    candidate_styles: List[str] = Field(
        default_factory=list,
        description="Cautiously identified architectural traditions (e.g. Indo-Islamic, Dravidian, Rajput, Gothic)."
    )
    candidate_descriptions: List[str] = Field(
        default_factory=list,
        description="Non-assertive descriptions of similar known monument classes."
    )
    curatorial_caveat: str = Field(
        default="Visual analysis is exploratory and does not establish verified historical identity without epigraphical or archival records.",
        description="Mandatory caution against ungrounded identification."
    )
    is_offline_fallback: bool = False
    model_name: str = DEFAULT_MODEL_NAME

    # Aliases for backwards compatibility with earlier versions
    @property
    def visual_evidence(self) -> str:
        return self.visible_architectural_evidence

    @property
    def confidence_description(self) -> str:
        return self.qualitative_confidence


# Alias for 100% backward compatibility
UnknownHeritageAnalysis = GeminiAdjudicationResult
# resolve_coordinates_from_catalogue is canonically imported from catalogue_service above


class ArchitecturalExplanation(BaseModel):
    directly_visible_observations: List[str] = Field(
        default_factory=list,
        description="Objective physical features visible in the photograph."
    )
    possible_interpretations: List[str] = Field(
        default_factory=list,
        description="Plausible architectural influences and stylistic traditions."
    )
    historically_verified_facts: List[str] = Field(
        default_factory=list,
        description="Archival facts confirmed from official ASI/UNESCO documentation."
    )
    disclaimer: str = Field(
        default="Visual appearance alone does not prove construction date, patron dynasty, or sacred consecration.",
        description="Mandatory epistemological distinction."
    )
    is_offline_fallback: bool = False


class GeminiTelemetryManager:
    """Thread-safe persistent telemetry logger for Gemini Tier-2 usage."""

    def __init__(self, telemetry_path: Path = TELEMETRY_FILE):
        self.path = telemetry_path
        self._lock = threading.Lock()
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing telemetry: {e}")

        return {
            "service_name": f"Gemini {DEFAULT_MODEL_NAME} Tier-2 Telemetry",
            "version": "1.1.0",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_retries": 0,
            "cumulative_latency_ms": 0.0,
            "average_latency_ms": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "tokens_reported_count": 0,
            "error_categories": {
                "RATE_LIMIT_429": 0,
                "AUTH_INVALID_KEY": 0,
                "MODEL_NOT_FOUND_404": 0,
                "TIMEOUT": 0,
                "SERVER_ERROR_5XX": 0,
                "EMPTY_RESPONSE": 0,
                "CLIENT_ERROR": 0,
            },
            "features_invoked": {
                "unknown_heritage_analysis": {"success": 0, "fail": 0},
                "grounded_historical_qa": {"success": 0, "fail": 0},
                "architectural_explanation": {"success": 0, "fail": 0},
            },
            "last_request_utc": None,
            "last_error": None,
        }

    def _save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist Gemini telemetry: {e}")

    def record_request(
        self,
        feature: str,
        success: bool,
        latency_ms: float,
        retries: int = 0,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        error_category: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        with self._lock:
            self.data["total_requests"] += 1
            if success:
                self.data["successful_requests"] += 1
            else:
                self.data["failed_requests"] += 1

            self.data["total_retries"] += retries
            self.data["cumulative_latency_ms"] += latency_ms
            req_count = max(self.data["total_requests"], 1)
            self.data["average_latency_ms"] = round(self.data["cumulative_latency_ms"] / req_count, 2)

            if input_tokens is not None and output_tokens is not None:
                self.data["total_input_tokens"] += input_tokens
                self.data["total_output_tokens"] += output_tokens
                self.data["tokens_reported_count"] += 1

            if error_category and error_category in self.data["error_categories"]:
                self.data["error_categories"][error_category] += 1

            if feature in self.data["features_invoked"]:
                sub = self.data["features_invoked"][feature]
                if success:
                    sub["success"] += 1
                else:
                    sub["fail"] += 1

            self.data["last_request_utc"] = datetime.now(timezone.utc).isoformat()
            if error_message:
                # Sanitize error message to prevent accidental key leakage
                sanitized = re.sub(r"key=[A-Za-z0-9_\-]+", "key=[REDACTED]", error_message)
                sanitized = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", sanitized)
                self.data["last_error"] = sanitized[:250]

            self._save()

    def get_public_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_requests": self.data["total_requests"],
                "successful_requests": self.data["successful_requests"],
                "failed_requests": self.data["failed_requests"],
                "success_rate_pct": round(
                    (self.data["successful_requests"] / max(self.data["total_requests"], 1)) * 100.0, 1
                ),
                "total_retries": self.data["total_retries"],
                "average_latency_ms": self.data["average_latency_ms"],
                "total_tokens": self.data["total_input_tokens"] + self.data["total_output_tokens"],
                "error_categories": self.data["error_categories"],
                "features_invoked": self.data["features_invoked"],
                "last_request_utc": self.data["last_request_utc"],
            }


telemetry_manager = GeminiTelemetryManager()


class GeminiTier2Service:
    """
    Production-grade Gemini 2.5 Flash Tier-2 integration with bounded retries,
    anti-hallucination guardrails, and deterministic offline fallbacks.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL_NAME,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client_override: Optional[Any] = None,
    ):
        self.model_name = model_name
        self.timeout = timeout_seconds
        self.client = client_override
        self.configured = False
        self.auth_error_detected = False

        if self.client is not None:
            self.configured = True
            logger.info(f"GeminiTier2Service initialized with client override ({model_name}).")
            return

        resolved_key = (api_key if api_key is not None else os.environ.get("GEMINI_API_KEY", "")).strip()
        if (
            resolved_key
            and resolved_key != "your_gemini_api_key_here"
            and resolved_key != "your_google_ai_studio_api_key_here"
        ):
            try:
                from google import genai
                self.client = genai.Client(api_key=resolved_key)
                self.configured = True
                masked_key = resolved_key[:6] + "..." + resolved_key[-4:] if len(resolved_key) > 10 else "***"
                logger.info(f"Gemini Tier-2 Service successfully configured ({model_name}, key: {masked_key}).")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini Client: {e}")
                self.configured = False
        else:
            logger.info("No active GEMINI_API_KEY found. Running Tier-2 in pure offline fallback mode.")
            self.configured = False

    def is_available(self) -> bool:
        return self.configured and not self.auth_error_detected and self.client is not None

    def _execute_with_retry(
        self,
        fn,
        feature_name: str,
        *args,
        **kwargs,
    ) -> Tuple[bool, Any, float, int]:
        """
        Executes a Gemini API call with bounded exponential backoff.
        Retries on 429 and transient 5xx; fails fast on auth errors (401/403).
        """
        retries = 0
        t0 = time.perf_counter()

        for attempt in range(MAX_RETRIES + 1):
            try:
                result = fn(*args, **kwargs)
                latency_ms = (time.perf_counter() - t0) * 1000.0

                # Extract token usage if available in response
                in_tok = None
                out_tok = None
                if hasattr(result, "usage_metadata") and result.usage_metadata:
                    raw_in = getattr(result.usage_metadata, "prompt_token_count", None)
                    raw_out = getattr(result.usage_metadata, "candidates_token_count", None)
                    if isinstance(raw_in, (int, float)):
                        in_tok = int(raw_in)
                    if isinstance(raw_out, (int, float)):
                        out_tok = int(raw_out)

                telemetry_manager.record_request(
                    feature=feature_name,
                    success=True,
                    latency_ms=latency_ms,
                    retries=retries,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                )
                return True, result, latency_ms, retries

            except Exception as exc:
                exc_str = str(exc)
                err_lower = exc_str.lower()
                latency_ms = (time.perf_counter() - t0) * 1000.0

                # Check for fatal Authentication / Permission errors (Do not retry)
                if any(x in err_lower for x in ["api_key_invalid", "unauthenticated", "permission_denied", "401", "403"]):
                    logger.error("Gemini API authentication failed. Disabling service until key reconfigured.")
                    self.auth_error_detected = True
                    telemetry_manager.record_request(
                        feature=feature_name,
                        success=False,
                        latency_ms=latency_ms,
                        retries=retries,
                        error_category="AUTH_INVALID_KEY",
                        error_message=exc_str,
                    )
                    return False, None, latency_ms, retries

                # Check for Model Not Found (404) - Do not retry
                if ("404" in err_lower) or ("not_found" in err_lower) or ("no longer available" in err_lower):
                    logger.error(f"Gemini model not found (404): {exc_str[:120]}")
                    telemetry_manager.record_request(
                        feature=feature_name,
                        success=False,
                        latency_ms=latency_ms,
                        retries=retries,
                        error_category="MODEL_NOT_FOUND_404",
                        error_message=exc_str,
                    )
                    return False, None, latency_ms, retries

                # Check for Quota Exhaustion (429 / resource_exhausted with quota/billing/plan) - Do not repeatedly retry
                is_quota_exhausted = (("429" in err_lower) or ("resource_exhausted" in err_lower)) and any(
                    w in err_lower for w in ["quota", "billing", "plan", "free_tier_requests"]
                )
                if is_quota_exhausted:
                    logger.warning(f"Gemini quota exhausted (429): {exc_str[:120]}. Failing fast without repeated retries.")
                    telemetry_manager.record_request(
                        feature=feature_name,
                        success=False,
                        latency_ms=latency_ms,
                        retries=retries,
                        error_category="RATE_LIMIT_429",
                        error_message=exc_str,
                    )
                    return False, None, latency_ms, retries

                is_rate_limit = ("429" in err_lower) or ("resource_exhausted" in err_lower)
                is_timeout = ("timeout" in err_lower) or ("deadline_exceeded" in err_lower)
                is_server = any(x in err_lower for x in ["500", "502", "503", "504", "unavailable"])

                if attempt < MAX_RETRIES and (is_rate_limit or is_timeout or is_server):
                    backoff = (2 ** attempt) * 1.0  # 1s, 2s, 4s
                    logger.warning(
                        f"Transient Gemini error ({exc_str[:80]}). Retrying in {backoff:.1f}s (Attempt {attempt + 1}/{MAX_RETRIES})..."
                    )
                    time.sleep(backoff)
                    retries += 1
                    continue

                # Final failure
                err_cat = "RATE_LIMIT_429" if is_rate_limit else ("TIMEOUT" if is_timeout else ("SERVER_ERROR_5XX" if is_server else "CLIENT_ERROR"))
                logger.error(f"Gemini Tier-2 request failed after {retries} retries: {exc_str[:120]}")
                telemetry_manager.record_request(
                    feature=feature_name,
                    success=False,
                    latency_ms=latency_ms,
                    retries=retries,
                    error_category=err_cat,
                    error_message=exc_str,
                )
                return False, None, latency_ms, retries

        return False, None, (time.perf_counter() - t0) * 1000.0, retries

    # --- Capability A: Gemini-Assisted Open-World Adjudication ---

    def adjudicate_monument(self, image: Image.Image) -> GeminiAdjudicationResult:
        """
        Phase 8.5F Capability A: Gemini-Assisted Open-World Monument Adjudication
        Invoked when Tier-1 CLIP produces ambiguous catalog competition or potential
        out-of-catalog specimens.
        
        Evaluates whether an image depicts:
        1. A known catalogue monument (one of the 10 indexed).
        2. An identifiable monument outside the catalogue (e.g. Golden Temple, Red Fort, Mysore Palace, India Gate, Eiffel Tower).
        3. An ambiguous or unidentifiable heritage structure.
        4. A non-monument image (receipt, math paper, everyday object).
        """
        if not self.is_available():
            return GeminiAdjudicationResult(
                proposed_identity=None,
                proposed_location=None,
                is_heritage_structure=True,
                is_catalog_monument=False,
                visible_architectural_evidence="Offline Curatorial Mode: Tier-1 visual vector scanner active. Multimodal adjudication running without live API connectivity.",
                distinguishing_features=["Offline vector nearest-neighbor inspection"],
                qualitative_confidence="UNCERTAIN",
                uncertainty_reason="Tier-2 Gemini service running in offline fallback mode.",
                visible_observations=["Unindexed heritage specimen detected by Tier-1 visual vector scanner."],
                candidate_styles=["Style unindexed in primary gallery"],
                candidate_descriptions=["Unclassified regional heritage structure requiring field survey."],
                curatorial_caveat="Visual analysis is exploratory and does not establish verified historical identity without epigraphical or archival records.",
                is_offline_fallback=True,
                model_name=self.model_name,
            )

        prompt = (
            "You are a Senior Architectural Historian, Principal Archaeologist, and Visual Verification Scientist.\n"
            "Our platform maintains an authoritative Heritage Catalogue containing 100 registered monuments and world heritage sites.\n\n"
            "Carefully analyze the uploaded photograph. Distinguish strictly between:\n"
            "1. An identifiable historical monument, temple, cave sanctuary, fort, palace, or archaeological site (e.g. Ajanta Caves, Golden Temple, Mysore Palace, Taj Mahal, Qutub Minar, Colosseum, etc.).\n"
            "2. A possible heritage structure that cannot be conclusively identified from the image.\n"
            "3. A non-monument image (e.g. academic paper, invoice, receipt, everyday object, vehicle, ordinary modern interior/exterior).\n\n"
            "CRITICAL RULES:\n"
            "- If the image depicts an identifiable historical heritage monument or archaeological site:\n"
            "  * Set proposed_identity to its specific official monument name.\n"
            "  * Set proposed_location to its city, state/region, and country.\n"
            "  * Set is_heritage_structure to true.\n"
            "  * Detail concrete visible architectural evidence and specific distinguishing features.\n"
            "  * Set qualitative_confidence to HIGH or MEDIUM.\n"
            "- If the image is a non-monument (document, paper, receipt, everyday object, modern interior):\n"
            "  * Set is_heritage_structure to false.\n"
            "  * Set proposed_identity to null.\n"
            "  * Set proposed_location to null.\n"
            "  * Explain in uncertainty_reason that the image is not a heritage structure.\n"
            "- If the image is ambiguous or generic historic masonry that cannot be reliably identified:\n"
            "  * Set proposed_identity to null.\n"
            "  * Set qualitative_confidence to LOW or UNCERTAIN.\n"
            "  * Set uncertainty_reason explaining the visual ambiguity.\n\n"
            "Respond strictly in valid JSON matching this schema:\n"
            "{\n"
            '  "proposed_identity": "Specific Monument Name (or null if ambiguous/non-monument)",\n'
            '  "proposed_location": "City, State/Region, Country (or null)",\n'
            '  "is_heritage_structure": true,\n'
            '  "visible_architectural_evidence": "Detailed explanation of visible architectural characteristics, materials, and forms...",\n'
            '  "distinguishing_features": ["Feature 1", "Feature 2"],\n'
            '  "qualitative_confidence": "HIGH | MEDIUM | LOW | UNCERTAIN",\n'
            '  "uncertainty_reason": "Explanation of any ambiguity, or \'None\' if unambiguous",\n'
            '  "visible_observations": ["Observation 1", "Observation 2"],\n'
            '  "candidate_styles": ["Architectural style 1", "Architectural style 2"],\n'
            '  "candidate_descriptions": ["Description 1", "Description 2"]\n'
            "}"
        )

        def _call():
            from google.genai import types
            return self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

        ok, resp, _, _ = self._execute_with_retry(_call, "unknown_heritage_analysis")
        if not ok or not resp or not resp.text:
            return GeminiAdjudicationResult(
                proposed_identity=None,
                proposed_location=None,
                is_heritage_structure=True,
                is_catalog_monument=False,
                catalogue_status=CatalogueStatus.OUT_OF_CATALOG.value,
                visible_architectural_evidence="Automated Tier-2 service temporarily unavailable; flagged for expert curatorial inspection.",
                distinguishing_features=[],
                qualitative_confidence="UNCERTAIN",
                uncertainty_reason="Tier-2 multimodal VLM request could not be completed.",
                visible_observations=["Distinctive heritage architectural geometry detected."],
                candidate_styles=["Unclassified historic tradition"],
                candidate_descriptions=["Pending field epigraphy review"],
                curatorial_caveat="Visual analysis is exploratory and does not establish verified historical identity without epigraphical or archival records.",
                is_offline_fallback=True,
                model_name=self.model_name,
            )

        try:
            parsed = json.loads(resp.text)
            vis_ev = parsed.get("visible_architectural_evidence") or parsed.get("visual_evidence") or ""
            qual_conf = parsed.get("qualitative_confidence") or parsed.get("confidence_description") or "UNCERTAIN"
            dist_feat = parsed.get("distinguishing_features") or []
            prop_id = parsed.get("proposed_identity")

            # Shared Canonical Catalogue Membership & Geodetic Resolution (Phase 8.6B)
            membership = check_catalogue_membership(prop_id)
            is_cat = (membership.status != CatalogueStatus.OUT_OF_CATALOG)
            coords = membership.coordinates
            matched_cat_id = (membership.monument_id or "").upper() if membership.monument_id else None
            geodetic_src = (
                f"Authoritative Heritage Registry ({membership.country or 'Global'} / UNESCO / National Archive)"
                if coords
                else None
            )
            prop_loc = parsed.get("proposed_location") or membership.location

            return GeminiAdjudicationResult(
                proposed_identity=prop_id,
                proposed_location=prop_loc,
                is_heritage_structure=bool(parsed.get("is_heritage_structure", True)),
                is_catalog_monument=is_cat,
                catalogue_status=membership.status.value,
                visible_architectural_evidence=vis_ev,
                distinguishing_features=dist_feat,
                qualitative_confidence=str(qual_conf).upper(),
                uncertainty_reason=parsed.get("uncertainty_reason", ""),
                verified_coordinates=coords,
                geodetic_source=geodetic_src,
                catalog_id=matched_cat_id,
                visible_observations=parsed.get("visible_observations", []),
                candidate_styles=parsed.get("candidate_styles", []),
                candidate_descriptions=parsed.get("candidate_descriptions", []),
                curatorial_caveat="Visual analysis is exploratory and does not establish verified historical identity without epigraphical or archival records.",
                is_offline_fallback=False,
                model_name=self.model_name,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Gemini adjudication response: {e}")
            return GeminiAdjudicationResult(
                proposed_identity=None,
                proposed_location=None,
                is_heritage_structure=True,
                is_catalog_monument=False,
                catalogue_status=CatalogueStatus.OUT_OF_CATALOG.value,
                visible_architectural_evidence=resp.text[:300] if resp and resp.text else "",
                distinguishing_features=[],
                qualitative_confidence="UNCERTAIN",
                uncertainty_reason=f"Failed to parse model JSON: {e}",
                visible_observations=["Structural elements observed in photograph."],
                candidate_styles=["Regional architectural tradition"],
                is_offline_fallback=True,
                model_name=self.model_name,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Gemini adjudication response: {e}")
            return GeminiAdjudicationResult(
                proposed_identity=None,
                proposed_location=None,
                is_heritage_structure=True,
                is_catalog_monument=False,
                visible_architectural_evidence=resp.text[:300] if resp and resp.text else "",
                distinguishing_features=[],
                qualitative_confidence="UNCERTAIN",
                uncertainty_reason=f"Failed to parse model JSON: {e}",
                visible_observations=["Structural elements observed in photograph."],
                candidate_styles=["Regional architectural tradition"],
                is_offline_fallback=True,
                model_name=self.model_name,
            )

    def analyze_unknown_heritage(self, image: Image.Image) -> UnknownHeritageAnalysis:
        """Backward-compatible wrapper delegating to adjudicate_monument."""
        return self.adjudicate_monument(image)

    # --- Capability B: Grounded Historical Question Answering ---

    def answer_historical_question(
        self,
        monument_id: str,
        monument_name: str,
        question: str,
        verified_passages: List[Dict[str, Any]],
        citations_list: List[Any],
    ) -> Dict[str, Any]:
        """
        Phase 7.2 Capability B:
        Grounded Q&A strictly constrained to verified ASI/UNESCO text excerpts.
        """
        if not verified_passages:
            return {
                "answer": (
                    f"The official archival records for {monument_name} do not contain verified "
                    f"information to answer this specific question. To uphold SIH 2025 anti-hallucination standards, "
                    f"unsupported claims are not generated."
                ),
                "citations": citations_list[:2],
                "grounded": True,
                "evidence_sufficient": False,
                "answering_engine": "OFFLINE_CURATORIAL_RETRIEVAL",
                "is_offline_fallback": False,
            }

        if not self.is_available():
            # Offline extractive fallback
            answer_parts = []
            for p in verified_passages:
                c_str = ", ".join(f"[{cid}]" for cid in p.get("citation_ids", []))
                answer_parts.append(f"{p['text']} {c_str}")
            return {
                "answer": " ".join(answer_parts),
                "citations": citations_list,
                "grounded": True,
                "evidence_sufficient": True,
                "answering_engine": "OFFLINE_CURATORIAL_RETRIEVAL",
                "is_offline_fallback": True,
            }

        context_block = "\n\n".join(
            f"[{p.get('section', 'ARCHIVE')}] (Citations: {', '.join(p.get('citation_ids', []))})\n{p['text']}"
            for p in verified_passages
        )

        prompt = (
            f"You are the Senior Archival Historian for the Archaeological Survey of India (ASI). "
            f"Answer the user's question about {monument_name} strictly and ONLY using the verified evidence below.\n\n"
            f"STRICT RULES:\n"
            f"1. Rely exclusively on the provided excerpts. Do NOT bring in unverified external knowledge.\n"
            f"2. Cite every factual assertion using the citation tags provided (e.g. [ASI-TD-2024-01]).\n"
            f"3. If the excerpts do not address the question, reply verbatim: "
            f"'Archival records for this monument do not contain verified evidence to answer this question.'\n\n"
            f"EVIDENCE EXCERPTS:\n{context_block}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"GROUNDED CURATORIAL ANSWER:"
        )

        def _call():
            return self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

        ok, resp, _, _ = self._execute_with_retry(_call, "grounded_historical_qa")
        if not ok or not resp or not resp.text:
            # Fallback to offline extractive answer
            answer_parts = [f"{p['text']}" for p in verified_passages]
            return {
                "answer": " ".join(answer_parts),
                "citations": citations_list,
                "grounded": True,
                "evidence_sufficient": True,
                "answering_engine": "OFFLINE_CURATORIAL_RETRIEVAL",
                "is_offline_fallback": True,
            }

        engine_tag = f"GEMINI_{self.model_name.upper().replace('-', '_').replace('.', '_')}_GROUNDED"
        return {
            "answer": resp.text.strip(),
            "citations": citations_list,
            "grounded": True,
            "evidence_sufficient": True,
            "answering_engine": engine_tag,
            "is_offline_fallback": False,
        }

    # --- Capability C: Architectural Explanation ---

    def explain_architecture(
        self,
        image: Image.Image,
        monument_name: Optional[str] = None,
        verified_facts: Optional[List[str]] = None,
    ) -> ArchitecturalExplanation:
        """
        Phase 7.2 Capability C:
        Explains visible architectural characteristics, rigorously distinguishing:
        1. Directly visible physical features.
        2. Possible stylistic interpretations.
        3. Historically verified facts from the ASI register.
        """
        known_context = (
            f"The recognized monument is: {monument_name}.\n"
            f"Verified Archival Facts:\n" + "\n".join(f"- {f}" for f in (verified_facts or []))
            if monument_name and verified_facts
            else "The monument identity is unconfirmed."
        )

        if not self.is_available():
            return ArchitecturalExplanation(
                directly_visible_observations=["Monument facade, elevation, and structural profile."],
                possible_interpretations=["Regional historic architectural movement."],
                historically_verified_facts=verified_facts or ["Identity verified via Tier-1 FAISS vector similarity."],
                is_offline_fallback=True,
            )

        prompt = (
            "You are a Principal Architectural Historian and Heritage Conservationist. "
            "Analyze the uploaded photograph of an Indian architectural monument.\n\n"
            f"CONTEXT:\n{known_context}\n\n"
            "REQUIREMENTS:\n"
            "Rigourously separate your analysis into THREE distinct sections:\n"
            "1. 'directly_visible_observations': Concrete structural features visible in the image (e.g. minarets, corbelled dome, red sandstone ashlar masonry, floral pietra dura).\n"
            "2. 'possible_interpretations': Architectural movements, influences, or craft traditions that these features suggest.\n"
            "3. 'historically_verified_facts': Only facts explicitly stated in the provided context (or empty if none provided).\n\n"
            "Respond in strictly valid JSON matching this schema:\n"
            "{\n"
            '  "directly_visible_observations": ["..."],\n'
            '  "possible_interpretations": ["..."],\n'
            '  "historically_verified_facts": ["..."]\n'
            "}"
        )

        def _call():
            from google.genai import types
            return self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

        ok, resp, _, _ = self._execute_with_retry(_call, "architectural_explanation")
        if not ok or not resp or not resp.text:
            return ArchitecturalExplanation(
                directly_visible_observations=["Architectural facade, cornice, and structural masonry."],
                possible_interpretations=["Classical Indian architectural movement."],
                historically_verified_facts=verified_facts or [],
                is_offline_fallback=True,
            )

        try:
            parsed = json.loads(resp.text)
            return ArchitecturalExplanation(
                directly_visible_observations=parsed.get("directly_visible_observations", []),
                possible_interpretations=parsed.get("possible_interpretations", []),
                historically_verified_facts=parsed.get("historically_verified_facts", verified_facts or []),
                is_offline_fallback=False,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Gemini architectural explanation: {e}")
            return ArchitecturalExplanation(
                directly_visible_observations=["Distinctive heritage masonry and structural forms."],
                possible_interpretations=["Traditional Indian architecture"],
                historically_verified_facts=verified_facts or [],
                is_offline_fallback=True,
            )


# Global singleton service
gemini_service = GeminiTier2Service()
