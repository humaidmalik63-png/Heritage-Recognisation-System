"""
Phase 8.5D: Gemini 3.1 Flash-Lite Migration & Multimodal Live Validation Runner
Workspace: C:\\Users\\humai\\Heritage PJ
"""

import io
import json
import logging
import os
import sys
import time
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase_8_5d_validation")

from gemini_service import gemini_service, GeminiTier2Service, telemetry_manager, DEFAULT_MODEL_NAME

TEST_SPECIMENS = [
    {
        "key": "eiffel_tower",
        "name": "Eiffel Tower",
        "path": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "eiffel_tower.jpg",
        "expected_catalog": False,
    },
    {
        "key": "colosseum",
        "name": "Colosseum",
        "path": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "colosseum.jpg",
        "expected_catalog": False,
    },
    {
        "key": "mysore_palace",
        "name": "Mysore Palace",
        "path": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "mysore_palace.jpg",
        "expected_catalog": False,
    },
    {
        "key": "red_fort",
        "name": "Red Fort",
        "path": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "red_fort.jpg",
        "expected_catalog": False,
    },
    {
        "key": "golden_temple",
        "name": "Golden Temple",
        "path": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "golden_temple.jpg",
        "expected_catalog": False,
    },
]


def run_validation():
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "configured_model": gemini_service.model_name,
        "is_service_available": gemini_service.is_available(),
        "live_text_request": None,
        "live_single_image_request": None,
        "five_monument_image_tests": [],
        "offline_fallback_tests": [],
        "telemetry_stats": None,
    }

    logger.info("=" * 80)
    logger.info(f"PHASE 8.5D: GEMINI MODEL MIGRATION VALIDATION ({gemini_service.model_name})")
    logger.info("=" * 80)

    # -------------------------------------------------------------------------
    # 1. Live Text Request
    # -------------------------------------------------------------------------
    logger.info("\n--- [Step 1] Live Text Request Test ---")
    t0 = time.perf_counter()
    text_prompt = "In 2 sentences, describe the structural function of an Indo-Islamic corbelled dome in Mughal architecture."
    try:
        resp = gemini_service.client.models.generate_content(
            model=gemini_service.model_name,
            contents=text_prompt,
        )
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        in_tok = getattr(resp.usage_metadata, "prompt_token_count", None) if hasattr(resp, "usage_metadata") else None
        out_tok = getattr(resp.usage_metadata, "candidates_token_count", None) if hasattr(resp, "usage_metadata") else None
        
        results["live_text_request"] = {
            "success": True,
            "status_code": 200,
            "model": gemini_service.model_name,
            "prompt": text_prompt,
            "response": resp.text.strip() if resp and resp.text else "",
            "latency_ms": latency_ms,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "total_tokens": (in_tok + out_tok) if (in_tok and out_tok) else None,
        }
        logger.info(f"[PASSED] Text Request in {latency_ms} ms (Tokens: {in_tok} in, {out_tok} out).")
        logger.info(f"Response: {resp.text[:120]}...")
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        logger.error(f"[FAILED] Text request failed: {exc}")
        results["live_text_request"] = {
            "success": False,
            "model": gemini_service.model_name,
            "error": str(exc),
            "latency_ms": latency_ms,
        }

    # -------------------------------------------------------------------------
    # 2. Live Single Image Request
    # -------------------------------------------------------------------------
    logger.info("\n--- [Step 2] Live Single Image Request Test ---")
    first_specimen = TEST_SPECIMENS[0]
    img = Image.open(first_specimen["path"]).convert("RGB")
    t0 = time.perf_counter()
    analysis = gemini_service.analyze_unknown_heritage(img)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    results["live_single_image_request"] = {
        "specimen": first_specimen["name"],
        "model": gemini_service.model_name,
        "is_offline_fallback": analysis.is_offline_fallback,
        "proposed_identity": analysis.proposed_identity,
        "is_catalog_monument": analysis.is_catalog_monument,
        "visual_evidence": analysis.visual_evidence,
        "confidence_description": analysis.confidence_description,
        "uncertainty_reason": analysis.uncertainty_reason,
        "latency_ms": latency_ms,
    }
    logger.info(f"[PASSED] Single Image Request ({first_specimen['name']}): Identity={analysis.proposed_identity}, is_catalog={analysis.is_catalog_monument}, fallback={analysis.is_offline_fallback} ({latency_ms} ms)")

    # -------------------------------------------------------------------------
    # 3. Five Monument Image Tests
    # -------------------------------------------------------------------------
    logger.info("\n--- [Step 3] Five Monument Image Tests ---")
    for spec in TEST_SPECIMENS:
        logger.info(f"\nEvaluating Specimen: {spec['name']} ({spec['path'].name})...")
        spec_img = Image.open(spec["path"]).convert("RGB")
        
        t0 = time.perf_counter()
        spec_analysis = gemini_service.analyze_unknown_heritage(spec_img)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        entry = {
            "key": spec["key"],
            "name": spec["name"],
            "file": str(spec["path"]),
            "model": gemini_service.model_name,
            "proposed_identity": spec_analysis.proposed_identity,
            "is_catalog_monument": spec_analysis.is_catalog_monument,
            "expected_is_catalog": spec["expected_catalog"],
            "catalog_membership_correct": (spec_analysis.is_catalog_monument == spec["expected_catalog"]),
            "visual_evidence": spec_analysis.visual_evidence,
            "confidence_description": spec_analysis.confidence_description,
            "uncertainty_reason": spec_analysis.uncertainty_reason,
            "visible_observations": spec_analysis.visible_observations,
            "candidate_styles": spec_analysis.candidate_styles,
            "is_offline_fallback": spec_analysis.is_offline_fallback,
            "latency_ms": latency_ms,
        }
        results["five_monument_image_tests"].append(entry)
        logger.info(f"-> Identity: {spec_analysis.proposed_identity}")
        logger.info(f"-> Is Catalog Monument: {spec_analysis.is_catalog_monument} (Expected: {spec['expected_catalog']})")
        logger.info(f"-> Confidence Description: {spec_analysis.confidence_description}")
        logger.info(f"-> Latency: {latency_ms} ms | Fallback: {spec_analysis.is_offline_fallback}")

    # -------------------------------------------------------------------------
    # 4. Offline Fallback Tests
    # -------------------------------------------------------------------------
    logger.info("\n--- [Step 4] Offline Fallback Engine Tests ---")
    offline_service = GeminiTier2Service(api_key="", client_override=None)
    for spec in TEST_SPECIMENS[:2]:
        spec_img = Image.open(spec["path"]).convert("RGB")
        t0 = time.perf_counter()
        off_analysis = offline_service.analyze_unknown_heritage(spec_img)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        off_entry = {
            "specimen": spec["name"],
            "is_offline_fallback": off_analysis.is_offline_fallback,
            "proposed_identity": off_analysis.proposed_identity,
            "is_catalog_monument": off_analysis.is_catalog_monument,
            "visual_evidence": off_analysis.visual_evidence,
            "confidence_description": off_analysis.confidence_description,
            "curatorial_caveat": off_analysis.curatorial_caveat,
            "latency_ms": latency_ms,
        }
        results["offline_fallback_tests"].append(off_entry)
        logger.info(f"[OFFLINE PASSED] {spec['name']}: fallback={off_analysis.is_offline_fallback}, latency={latency_ms} ms")

    # -------------------------------------------------------------------------
    # 5. Telemetry Snapshot
    # -------------------------------------------------------------------------
    results["telemetry_stats"] = telemetry_manager.get_public_stats()
    
    # Save output to JSON
    out_file = BASE_DIR / "phase_8_5d_gemini_migration_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\n[SAVED] Comprehensive validation results stored in {out_file}")


if __name__ == "__main__":
    run_validation()

