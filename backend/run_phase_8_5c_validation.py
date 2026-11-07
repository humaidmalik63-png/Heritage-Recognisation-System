"""
Phase 8.5C: High-Confidence Monument Disambiguation & Gemini Open-World Validation
Automated Validation Runner & Evidence Collector
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")

API_URL = "http://127.0.0.1:8000/api/verify-monument"
CATALOG_KEYS = [
    "taj_mahal", "qutub_minar", "charminar", "gateway_of_india", "victoria_memorial",
    "hampi_stone_chariot", "hawa_mahal", "konark_sun_temple", "brihadeeswarar_temple", "khajuraho"
]

def query_api(image_path: str):
    t0 = time.perf_counter()
    with open(image_path, "rb") as f:
        resp = requests.post(
            API_URL,
            files={"file": (Path(image_path).name, f, "image/jpeg" if image_path.endswith(".jpg") else "image/png")}
        )
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return resp.status_code, resp.json(), latency_ms

def run_gemini_live_test(image_path: str, model_name: str, api_key: str):
    import concurrent.futures
    t0 = time.perf_counter()
    from google import genai

    client = genai.Client(api_key=api_key)
    prompt = (
        "You are an expert cultural heritage architectural analyst for the Visual Heritage Recognition Platform. "
        "Analyze this monument image and provide: "
        "1. Identified monument name and location (or explicitly declare UNCERTAIN if unclear). "
        "2. Catalog membership check: Does this monument belong to this 10-monument catalogue: "
        "[Taj Mahal, Qutub Minar, Charminar, Gateway of India, Victoria Memorial, Hampi Stone Chariot, "
        "Hawa Mahal, Konark Sun Temple, Brihadeeswarar Temple, Khajuraho]? (Answer YES or NO). "
        "3. Specific architectural visual evidence supporting your identification. "
        "4. Confidence rating (HIGH, MEDIUM, LOW) with an explicit note of any visual ambiguities."
    )

    pil_img = Image.open(image_path).convert("RGB")
    pil_img.thumbnail((800, 800))
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(client.models.generate_content, model=model_name, contents=[prompt, pil_img])
            response = fut.result(timeout=12.0)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "success": True,
            "model": model_name,
            "latency_ms": latency_ms,
            "text": response.text.strip(),
            "error": None
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        clean_err = str(e).replace(api_key, "[REDACTED_API_KEY]")
        return {
            "success": False,
            "model": model_name,
            "latency_ms": latency_ms,
            "text": None,
            "error": clean_err[:250]
        }

def run_gemini_offline_test(image_path: str):
    sys.path.insert(0, str(WORKSPACE))
    from backend.gemini_service import GeminiTier2Service
    
    t0 = time.perf_counter()
    # Explicitly instantiate without API key
    offline_service = GeminiTier2Service(api_key="")
    pil_img = Image.open(image_path).convert("RGB")
    res = offline_service.analyze_unknown_heritage(pil_img)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "latency_ms": latency_ms,
        "is_offline_fallback": res.is_offline_fallback,
        "visible_observations": res.visible_observations,
        "candidate_styles": res.candidate_styles,
        "visual_evidence": res.visual_evidence,
        "curatorial_caveat": res.curatorial_caveat,
    }

def main():
    print("=" * 80)
    print("PHASE 8.5C FULL VALIDATION SUITE EXECUTION")
    print("=" * 80)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task_1_qutub_disambiguation": {},
        "task_2_threshold_display": {},
        "task_3_out_of_catalog_validation": [],
        "task_4_gemini_live_validation": {},
        "task_5_gemini_offline_fallback": [],
        "task_7_complete_test_matrix": {},
    }

    # -------------------------------------------------------------------------
    # TASK 1: Qutub Minar Reference Disambiguation Case
    # -------------------------------------------------------------------------
    print("\n--- [TASK 1] Qutub Minar Reference Disambiguation ---")
    qutub_ref_path = r"C:\Users\humai\Pictures\Screenshots\Screenshot 2026-10-01 002328.png"
    code, qutub_data, lat = query_api(qutub_ref_path)
    qutub_unc = qutub_data.get("uncertainty", {})
    results["task_1_qutub_disambiguation"] = {
        "specimen_path": qutub_ref_path,
        "http_code": code,
        "verification_status": qutub_data.get("verification_status"),
        "monument_name": qutub_data.get("monument_name"),
        "confidence_score": qutub_data.get("confidence_score"),
        "top1_similarity": qutub_unc.get("top1_similarity"),
        "top2_similarity": qutub_unc.get("top2_similarity"),
        "similarity_margin": qutub_unc.get("similarity_margin"),
        "margin_threshold": qutub_unc.get("margin_threshold"),
        "gatekeeper_score": qutub_unc.get("gatekeeper_score"),
        "reason_codes": qutub_unc.get("reason_codes"),
        "explanation": qutub_unc.get("explanation"),
        "local_features": qutub_data.get("local_features"),
        "latency_ms": lat,
    }
    print(f"Qutub Minar Status: {qutub_data.get('verification_status')} (Conf: {qutub_data.get('confidence_score')}%)")
    print(f"Margin: {qutub_unc.get('similarity_margin')} (Threshold: {qutub_unc.get('margin_threshold')})")
    print(f"Explanation: {qutub_unc.get('explanation')}")

    # -------------------------------------------------------------------------
    # TASK 2: Threshold Display Verification
    # -------------------------------------------------------------------------
    print("\n--- [TASK 2] Threshold Display Invariant Verification ---")
    pt = qutub_data.get("pipeline_telemetry", {})
    results["task_2_threshold_display"] = {
        "uncertainty_margin_threshold": qutub_unc.get("margin_threshold"),
        "pipeline_telemetry_margin_threshold": pt.get("margin_threshold"),
        "explanation_threshold_str": "0.08" if "0.08" in qutub_unc.get("explanation", "") or "0.08" in str(qutub_unc.get("margin_threshold")) else "MATCH",
        "authoritative_config_threshold": 0.08,
        "threshold_match_verified": (qutub_unc.get("margin_threshold") == 0.08 and pt.get("margin_threshold") == 0.08)
    }
    print(f"Uncertainty margin_threshold: {qutub_unc.get('margin_threshold')}")
    print(f"Pipeline Telemetry margin_threshold: {pt.get('margin_threshold')}")
    print(f"Consistency Confirmed: {results['task_2_threshold_display']['threshold_match_verified']}")

    # -------------------------------------------------------------------------
    # TASK 3: Out-of-Catalog Monument Validation (8 specimens)
    # -------------------------------------------------------------------------
    print("\n--- [TASK 3] Out-of-Catalog Monument Validation ---")
    ooc_specimens = [
        ("mysore_palace", "backend/datasets/phase_8_5c_ooc_eval/mysore_palace.jpg", "Indian Heritage", "Mysore Palace, Karnataka"),
        ("red_fort", "backend/datasets/phase_8_5c_ooc_eval/red_fort.jpg", "Indian Heritage", "Red Fort, Delhi"),
        ("india_gate", "backend/datasets/phase_8_5c_ooc_eval/india_gate.jpg", "Indian Heritage", "India Gate, New Delhi"),
        ("golden_temple", "backend/datasets/phase_8_5c_ooc_eval/golden_temple.jpg", "Indian Heritage", "Harmandir Sahib, Amritsar"),
        ("eiffel_tower", "backend/datasets/phase_8_5c_ooc_eval/eiffel_tower.jpg", "International Heritage", "Eiffel Tower, Paris"),
        ("colosseum", "backend/datasets/phase_8_5c_ooc_eval/colosseum.jpg", "International Heritage", "Colosseum, Rome"),
        ("statue_of_liberty", "backend/datasets/phase_8_5c_ooc_eval/statue_of_liberty.jpg", "International Heritage", "Statue of Liberty, New York"),
        ("big_ben", "backend/datasets/phase_8_5c_ooc_eval/big_ben.jpg", "International Heritage", "Big Ben / Elizabeth Tower, London"),
    ]

    for mon_key, path, origin, true_name in ooc_specimens:
        code, data, lat = query_api(path)
        unc = data.get("uncertainty", {})
        cands = unc.get("top_candidates", [])
        top1_c = cands[0] if len(cands) > 0 else {}
        top2_c = cands[1] if len(cands) > 1 else {}
        rec = {
            "key": mon_key,
            "true_name": true_name,
            "origin": origin,
            "file_path": path,
            "top1_candidate": top1_c.get("monument_name", "None"),
            "top1_similarity": unc.get("top1_similarity", 0.0),
            "top2_candidate": top2_c.get("monument_name", "None"),
            "top2_similarity": unc.get("top2_similarity", 0.0),
            "margin": unc.get("similarity_margin", 0.0),
            "gatekeeper_score": unc.get("gatekeeper_score", 0.0),
            "local_feature_evidence": data.get("local_features", {}).get("execution_mode"),
            "final_decision": data.get("verification_status"),
            "latency_ms": lat,
            "false_catalog_attribution_prevented": data.get("verification_status") != "VERIFIED_MATCH",
        }
        results["task_3_out_of_catalog_validation"].append(rec)
        print(f"[{origin}] {true_name:<25} -> Decision: {rec['final_decision']:<25} | Top1: {rec['top1_candidate']} ({rec['top1_similarity']:.4f}) | Latency: {lat}ms")

    # -------------------------------------------------------------------------
    # TASK 4: Gemini Live Validation (2.5 Flash Deprecation Audit + 3.8 Flash Visual Analysis)
    # -------------------------------------------------------------------------
    print("\n--- [TASK 4] Gemini Live Validation ---")
    api_key = os.environ.get("GEMINI_API_KEY", "")
    
    # 4A. Audit gemini-2.5-flash deprecation
    g25_res = run_gemini_live_test(ooc_specimens[4][1], "gemini-2.5-flash", api_key)
    print(f"Gemini 2.5 Flash Attempt: Success={g25_res['success']}, Latency={g25_res['latency_ms']}ms")
    print(f"Gemini 2.5 Flash Diagnostic Error: {g25_res['error'][:140]}...")

    # 4B. Run live visual open-world analysis with current Google model gemini-3.8-flash
    g38_live_results = []
    for mon_key, path, origin, true_name in ooc_specimens:
        print(f"Sending {true_name} to Gemini Live...")
        g_res = run_gemini_live_test(path, "gemini-3.8-flash", api_key)
        g38_live_results.append({
            "monument_key": mon_key,
            "true_name": true_name,
            "model": "gemini-3.8-flash",
            "latency_ms": g_res["latency_ms"],
            "success": g_res["success"],
            "analysis_text": g_res["text"],
            "error": g_res["error"]
        })
        preview_str = (g_res['text'] or g_res['error'] or 'No response')[:120].replace('\n', ' ')
        print(f"  Result ({g_res['latency_ms']}ms): {preview_str}...\n")

    results["task_4_gemini_live_validation"] = {
        "gemini_2_5_flash_audit": g25_res,
        "gemini_3_8_flash_live_results": g38_live_results,
    }

    # -------------------------------------------------------------------------
    # TASK 5: Gemini Offline Fallback Validation (4 monuments without API key)
    # -------------------------------------------------------------------------
    print("\n--- [TASK 5] Gemini Offline Fallback Validation ---")
    offline_targets = [
        ("eiffel_tower", "backend/datasets/phase_8_5c_ooc_eval/eiffel_tower.jpg"),
        ("colosseum", "backend/datasets/phase_8_5c_ooc_eval/colosseum.jpg"),
        ("mysore_palace", "backend/datasets/phase_8_5c_ooc_eval/mysore_palace.jpg"),
        ("golden_temple", "backend/datasets/phase_8_5c_ooc_eval/golden_temple.jpg"),
    ]
    for mon_key, path in offline_targets:
        off_res = run_gemini_offline_test(path)
        rec = {
            "monument_key": mon_key,
            "is_offline_fallback": off_res["is_offline_fallback"],
            "visible_observations_count": len(off_res["visible_observations"]),
            "candidate_styles": off_res["candidate_styles"],
            "visual_evidence": off_res["visual_evidence"],
            "curatorial_caveat": off_res["curatorial_caveat"],
            "latency_ms": off_res["latency_ms"],
        }
        results["task_5_gemini_offline_fallback"].append(rec)
        print(f"Offline {mon_key:<15} | Fallback Flag: {rec['is_offline_fallback']} | Latency: {rec['latency_ms']}ms | Caveat: {rec['curatorial_caveat'][:80]}...")

    # -------------------------------------------------------------------------
    # TASK 7: Complete Test Matrix (Catalogue Positives, OOC Indian, International, Non-Monuments, Ambiguous)
    # -------------------------------------------------------------------------
    print("\n--- [TASK 7] Complete Test Matrix ---")
    matrix_groups = {
        "A_catalogue_positives": [
            ("Taj Mahal", "backend/dataset/taj_mahal/img_1.jpg"),
            ("Qutub Minar", "backend/dataset/qutub_minar/img_1.jpg"),
            ("Charminar", "backend/dataset/charminar/img_1.jpg"),
            ("Hawa Mahal", "backend/dataset/hawa_mahal/img_1.jpg"),
            ("Konark Sun Temple", "backend/dataset/konark_sun_temple/img_1.jpg"),
        ],
        "B_out_of_catalog_indian": [
            ("Mysore Palace", "backend/datasets/phase_8_5c_ooc_eval/mysore_palace.jpg"),
            ("Red Fort", "backend/datasets/phase_8_5c_ooc_eval/red_fort.jpg"),
            ("India Gate", "backend/datasets/phase_8_5c_ooc_eval/india_gate.jpg"),
            ("Golden Temple", "backend/datasets/phase_8_5c_ooc_eval/golden_temple.jpg"),
        ],
        "C_international_heritage": [
            ("Eiffel Tower", "backend/datasets/phase_8_5c_ooc_eval/eiffel_tower.jpg"),
            ("Colosseum", "backend/datasets/phase_8_5c_ooc_eval/colosseum.jpg"),
            ("Statue of Liberty", "backend/datasets/phase_8_5c_ooc_eval/statue_of_liberty.jpg"),
            ("Big Ben", "backend/datasets/phase_8_5c_ooc_eval/big_ben.jpg"),
        ],
        "D_non_monuments": [
            ("Mathematics Paper", r"C:\Users\humai\Pictures\Screenshots\CSE 306 screenshot.png"),
            ("Receipt Distractor", "backend/datasets/receipt_distractor.jpg"),
            ("Ordinary Building", "backend/datasets/independent_final_test_v4/split_d_063_non_monument.jpg"),
            ("Everyday Object", "backend/datasets/independent_final_test_v4/split_d_064_non_monument.jpg"),
        ],
        "E_ambiguous_and_stress_cases": [
            ("Qutub Minar (Close View)", qutub_ref_path),
            ("Hampi Architectural View", "backend/datasets/independent_final_test_v4/split_d_019_hampi_stone_chariot.jpg"),
            ("Mysore Palace (Indo-Saracenic)", "backend/datasets/independent_final_test_v4/split_d_086_mysore_palace.jpg"),
        ]
    }

    matrix_out = {}
    for group_name, items in matrix_groups.items():
        matrix_out[group_name] = []
        print(f"\nGroup: {group_name}")
        for name, path in items:
            code, data, lat = query_api(path)
            unc = data.get("uncertainty", {})
            rec = {
                "name": name,
                "path": path,
                "verification_status": data.get("verification_status"),
                "monument_name": data.get("monument_name"),
                "confidence_score": data.get("confidence_score"),
                "top1_similarity": unc.get("top1_similarity"),
                "similarity_margin": unc.get("similarity_margin"),
                "gatekeeper_score": unc.get("gatekeeper_score"),
                "latency_ms": lat,
            }
            matrix_out[group_name].append(rec)
            print(f"  {name:<28} -> {rec['verification_status']:<25} | Sim: {rec['top1_similarity']} | Margin: {rec['similarity_margin']} | GK: {rec['gatekeeper_score']} | {lat}ms")

    results["task_7_complete_test_matrix"] = matrix_out

    # Save results to JSON
    out_json = BASE_DIR / "phase_8_5c_results.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved complete machine-readable results to {out_json}")

if __name__ == "__main__":
    main()
