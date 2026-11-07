"""
Phase 8.5F — Gemini-Assisted Open-World Adjudication Evaluation Matrix
Tests 14 specimens across 4 critical validation categories:
  Category 1: Out-of-Catalog Indian Heritage (4): Golden Temple, Mysore Palace, Red Fort, India Gate
  Category 2: Out-of-Catalog International Heritage (4): Eiffel Tower, Colosseum, Statue of Liberty, Big Ben
  Category 3: In-Catalog Ground-Truth Positives (3): Taj Mahal, Qutub Minar, Charminar
  Category 4: Non-Monuments / Negative Controls (3): Mathematics Paper, Receipt Distractor, Modern Ordinary Building
"""

import json
import logging
import sys
import time
from pathlib import Path
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_8_5f")

BASE_URL = "http://127.0.0.1:8000"

SPECIMEN_SPEC = [
    # Category 1: Out-of-Catalog Indian
    {
        "id": "OOC_IND_01",
        "category": "Out-of-Catalog Indian Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "Golden Temple",
        "path": "backend/datasets/phase_8_5c_ooc_eval/golden_temple.jpg",
        "expected_identity_contains": ["golden temple", "harmandir"],
    },
    {
        "id": "OOC_IND_02",
        "category": "Out-of-Catalog Indian Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "Mysore Palace",
        "path": "backend/datasets/phase_8_5c_ooc_eval/mysore_palace.jpg",
        "expected_identity_contains": ["mysore", "ambavilas"],
    },
    {
        "id": "OOC_IND_03",
        "category": "Out-of-Catalog Indian Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "Red Fort",
        "path": "backend/datasets/phase_8_5c_ooc_eval/red_fort.jpg",
        "expected_identity_contains": ["red fort", "lal qila"],
    },
    {
        "id": "OOC_IND_04",
        "category": "Out-of-Catalog Indian Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "India Gate",
        "path": "backend/datasets/phase_8_5c_ooc_eval/india_gate.jpg",
        "expected_identity_contains": ["india gate", "all india war memorial"],
    },

    # Category 2: Out-of-Catalog International
    {
        "id": "OOC_INT_01",
        "category": "Out-of-Catalog International Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "Eiffel Tower",
        "path": "backend/datasets/phase_8_5c_ooc_eval/eiffel_tower.jpg",
        "expected_identity_contains": ["eiffel", "tour eiffel"],
    },
    {
        "id": "OOC_INT_02",
        "category": "Out-of-Catalog International Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "Colosseum",
        "path": "backend/datasets/phase_8_5c_ooc_eval/colosseum.jpg",
        "expected_identity_contains": ["colosseum", "flavian amphitheatre"],
    },
    {
        "id": "OOC_INT_03",
        "category": "Out-of-Catalog International Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "Statue of Liberty",
        "path": "backend/datasets/phase_8_5c_ooc_eval/statue_of_liberty.jpg",
        "expected_identity_contains": ["statue of liberty", "liberty"],
    },
    {
        "id": "OOC_INT_04",
        "category": "Out-of-Catalog International Heritage",
        "expected_type": "OUT_OF_CATALOG",
        "name": "Big Ben",
        "path": "backend/datasets/phase_8_5c_ooc_eval/big_ben.jpg",
        "expected_identity_contains": ["big ben", "elizabeth tower", "westminster"],
    },

    # Category 3: Catalog Positives
    {
        "id": "CAT_POS_01",
        "category": "In-Catalog Ground-Truth Positive",
        "expected_type": "VERIFIED_MATCH",
        "name": "Taj Mahal",
        "path": "backend/dataset/taj_mahal/ref_01.jpg",
        "expected_catalog_key": "taj_mahal",
    },
    {
        "id": "CAT_POS_02",
        "category": "In-Catalog Ground-Truth Positive",
        "expected_type": "VERIFIED_MATCH",
        "name": "Qutub Minar",
        "path": "backend/dataset/qutub_minar/ref_01.jpg",
        "expected_catalog_key": "qutub_minar",
    },
    {
        "id": "CAT_POS_03",
        "category": "In-Catalog Ground-Truth Positive",
        "expected_type": "VERIFIED_MATCH",
        "name": "Charminar",
        "path": "backend/dataset/charminar/ref_01.jpg",
        "expected_catalog_key": "charminar",
    },

    # Category 4: Non-Monuments / Negative Controls
    {
        "id": "NON_MON_01",
        "category": "Non-Monument Negative Control",
        "expected_type": "NON_MONUMENT_REJECTED",
        "name": "Mathematics Paper",
        "path": "backend/datasets/phase_8_5f_specimens/mathematics_paper.jpg",
    },
    {
        "id": "NON_MON_02",
        "category": "Non-Monument Negative Control",
        "expected_type": "NON_MONUMENT_REJECTED",
        "name": "Receipt Distractor",
        "path": "backend/datasets/receipt_distractor.jpg",
    },
    {
        "id": "NON_MON_03",
        "category": "Non-Monument Negative Control",
        "expected_type": "NON_MONUMENT_REJECTED",
        "name": "Ordinary Modern Building",
        "path": "backend/datasets/phase_8_5f_specimens/ordinary_building.jpg",
    },
]


def run_evaluation():
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    # Health verification
    h = client.get("/api/health")
    if h.status_code != 200:
        logger.error(f"Backend unhealthy: {h.status_code}")
        sys.exit(1)
    health_info = h.json()
    logger.info(f"Connected to backend. Health: {health_info}")

    results = []
    category_summary = {}

    for idx, spec in enumerate(SPECIMEN_SPEC, 1):
        spec_path = Path(spec["path"])
        if not spec_path.exists():
            logger.error(f"Specimen file missing: {spec_path}")
            results.append({
                "specimen": spec,
                "status": "ERROR_FILE_NOT_FOUND"
            })
            continue

        logger.info(f"\n--- [{idx}/{len(SPECIMEN_SPEC)}] Evaluating: {spec['name']} ({spec['category']}) ---")
        t0 = time.perf_counter()

        with open(spec_path, "rb") as f:
            resp = client.post(
                "/api/verify-monument",
                files={"file": (spec_path.name, f, "image/jpeg")}
            )

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        if resp.status_code != 200:
            logger.error(f"Request failed: {resp.status_code} - {resp.text}")
            results.append({
                "specimen": spec,
                "status": "HTTP_ERROR",
                "status_code": resp.status_code,
                "latency_ms": latency_ms
            })
            continue

        data = resp.json()
        decision_state = data.get("verification_status")
        tier = data.get("verification_tier")
        monument_name = data.get("monument_name")
        out_of_catalog_id = data.get("out_of_catalog_identified", False)
        gatekeeper_score = data.get("pipeline_telemetry", {}).get("architectural_gatekeeper_score", 0.0)
        top1 = data.get("pipeline_telemetry", {}).get("top_3_candidates", [{}])[0] if data.get("pipeline_telemetry", {}).get("top_3_candidates") else {}
        tier2 = data.get("tier2_analysis")

        # Evaluate correctness
        passed = False
        evaluation_note = ""

        if spec["expected_type"] == "OUT_OF_CATALOG":
            # Must be UNKNOWN_HERITAGE_SPECIMEN with out_of_catalog_identified = True
            is_identified = (
                decision_state == "UNKNOWN_HERITAGE_SPECIMEN"
                and out_of_catalog_id is True
                and tier2 is not None
            )
            # Check identity match
            identity_match = False
            if is_identified and tier2.get("proposed_identity"):
                prop = tier2.get("proposed_identity").lower()
                identity_match = any(e in prop for e in spec.get("expected_identity_contains", []))

            passed = is_identified and identity_match
            evaluation_note = (
                f"Resolved Identity: '{tier2.get('proposed_identity') if tier2 else 'None'}' "
                f"(Location: {tier2.get('proposed_location') if tier2 else 'None'}), "
                f"Confidence: {tier2.get('qualitative_confidence') if tier2 else 'None'}, "
                f"Catalog Competition Top-1: {top1.get('monument_name')} ({top1.get('cosine_similarity', 0.0):.4f})"
            )

        elif spec["expected_type"] == "VERIFIED_MATCH":
            passed = (
                decision_state == "VERIFIED_MATCH"
                and data.get("monument_key") == spec.get("expected_catalog_key")
            )
            evaluation_note = (
                f"Matched: '{monument_name}' (Catalog Key: {data.get('monument_key')}), "
                f"Confidence: {data.get('confidence_score')}%, "
                f"Tier: {tier}"
            )

        elif spec["expected_type"] == "NON_MONUMENT_REJECTED":
            passed = (
                decision_state == "NON_MONUMENT_REJECTED"
                and data.get("is_monument") is False
            )
            evaluation_note = (
                f"Rejected Non-Monument: Gatekeeper={gatekeeper_score:.4f}, "
                f"Decision={decision_state}, Tier={tier}"
            )

        status_str = "PASS" if passed else "FAIL"
        logger.info(
            f"[{status_str}] {spec['name']} | Decision: {decision_state} | "
            f"OutOfCatalog: {out_of_catalog_id} | Latency: {latency_ms}ms"
        )
        logger.info(f"   Details: {evaluation_note}")

        res_record = {
            "specimen_id": spec["id"],
            "name": spec["name"],
            "category": spec["category"],
            "expected_type": spec["expected_type"],
            "passed": passed,
            "decision_status": decision_state,
            "verification_tier": tier,
            "monument_name": monument_name,
            "out_of_catalog_identified": out_of_catalog_id,
            "gatekeeper_score": gatekeeper_score,
            "latency_ms": latency_ms,
            "evaluation_note": evaluation_note,
            "top1_candidate": top1,
            "tier2_analysis": tier2,
        }
        results.append(res_record)

        # Update category tally
        cat = spec["category"]
        if cat not in category_summary:
            category_summary[cat] = {"total": 0, "passed": 0}
        category_summary[cat]["total"] += 1
        if passed:
            category_summary[cat]["passed"] += 1

    total_specs = len(results)
    total_passed = sum(1 for r in results if r.get("passed"))
    accuracy = (total_passed / total_specs) * 100 if total_specs > 0 else 0

    eval_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": "PHASE_8_5F_GEMINI_OPEN_WORLD_ADJUDICATION",
        "model": health_info.get("gemini_tier2_model"),
        "total_specimens": total_specs,
        "total_passed": total_passed,
        "accuracy_pct": round(accuracy, 2),
        "category_summary": category_summary,
        "detailed_results": results,
    }

    out_file = Path("backend/phase_8_5f_adjudication_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("\n" + "=" * 75)
    logger.info(f"EVALUATION COMPLETE: {total_passed}/{total_specs} Passed ({accuracy:.1f}%)")
    for cat, stats in category_summary.items():
        logger.info(f"  * {cat}: {stats['passed']}/{stats['total']} ({stats['passed']/stats['total']*100:.1f}%)")
    logger.info(f"Results written to: {out_file}")
    logger.info("=" * 75)


if __name__ == "__main__":
    run_evaluation()

