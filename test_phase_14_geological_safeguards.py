"""
Phase 14 Geological Safeguards & Rock-Cut Heritage Evaluation Suite
Tests the 12 geological vs. architectural specimens required for production safeguard verification:
1. Natural sandstone cliff
2. Natural red rock formation
3. Honeycomb-weathered sandstone (tafoni)
4. Natural cave opening
5. Rock-cut temple facade (Ajanta / Ellora)
6. Carved archaeological entrance
7. Monument facade close-up (macro carving)
8. Partially eroded architectural carvings
9. Ordinary rocks resembling architectural patterns
10. Genuine Petra Al-Khazneh facade photograph
11. Genuine Ajanta cave photograph
12. Unknown geological formation
"""

import os
import sys
import io
import time
from pathlib import Path
from PIL import Image, ImageDraw

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BASE_DIR))

os.environ["CURATOR_API_KEY"] = "sih2025_curator_test_key_verified"
os.environ["DISABLE_RATE_LIMIT"] = "1"

from fastapi.testclient import TestClient
from backend.main import app, state, initialize_backend_resources


def generate_synthetic_specimen(category: str) -> bytes:
    """Generates synthetic specimens matching the visual patterns of each category."""
    img = Image.new("RGB", (320, 320), color=(180, 100, 70))
    draw = ImageDraw.Draw(img)

    if category == "sandstone_cliff":
        # Horizontal sedimentary strata lines
        for y in range(0, 320, 16):
            shade = 140 + (y % 40)
            draw.line([(0, y), (320, y + (y % 8) - 4)], fill=(shade + 20, shade - 20, 60), width=3)
    elif category == "red_rock":
        # Smooth rounded red monolith
        draw.ellipse([40, 40, 280, 280], fill=(190, 65, 45))
    elif category == "honeycomb_tafoni":
        # Weathered cavities / honeycomb holes
        for x in range(30, 300, 35):
            for y in range(30, 300, 35):
                draw.ellipse([x, y, x + 18, y + 14], fill=(70, 35, 25))
    elif category == "natural_cave":
        # Dark irregular cave mouth
        draw.ellipse([60, 80, 260, 260], fill=(20, 15, 15))
    elif category == "rock_cut_temple":
        # Carved columns, lintel, pediment cut into rock
        draw.rectangle([50, 40, 270, 80], fill=(210, 170, 130)) # Lintel
        for col_x in [70, 120, 190, 240]:
            draw.rectangle([col_x, 80, col_x + 20, 280], fill=(220, 180, 140)) # Columns
        draw.rectangle([130, 160, 180, 280], fill=(40, 25, 20)) # Portal
    elif category == "carved_entrance":
        # Symmetrical carved archway
        draw.rectangle([80, 100, 240, 280], fill=(160, 110, 80))
        draw.arc([80, 60, 240, 180], start=180, end=0, fill=(240, 200, 150), width=6)
        draw.rectangle([110, 120, 210, 280], fill=(30, 20, 15)) # Portal opening
    elif category == "facade_closeup":
        # Intricate relief carving / frieze
        for i in range(20, 300, 30):
            draw.rectangle([i, 60, i + 15, 260], fill=(230, 200, 160))
            draw.ellipse([i - 5, 40, i + 20, 65], fill=(210, 170, 130))
    elif category == "eroded_carvings":
        # Faded relief contours
        for i in range(30, 290, 40):
            draw.arc([i, 80, i + 35, 240], start=0, end=180, fill=(175, 125, 90), width=4)
    elif category == "rock_resembling_arch":
        # Natural vertical joints that look superficially like pillars
        for x in [60, 130, 210, 270]:
            draw.line([(x, 30), (x + 8, 290)], fill=(120, 70, 50), width=4)
    elif category == "petra_facade":
        # Iconic Al-Khazneh Corinthian pediment & urn
        draw.polygon([(160, 30), (70, 90), (250, 90)], fill=(225, 165, 125)) # Pediment
        for col_x in [80, 120, 190, 230]:
            draw.rectangle([col_x, 90, col_x + 18, 280], fill=(235, 175, 135)) # Columns
        draw.rectangle([135, 170, 175, 280], fill=(35, 20, 15)) # Deep chamber portal
    elif category == "ajanta_cave":
        # Horseshoe chaitya arch and pillared verandah
        draw.arc([90, 40, 230, 180], start=180, end=0, fill=(200, 155, 115), width=8)
        draw.ellipse([130, 90, 190, 150], fill=(25, 20, 18)) # Chaitya window
        for col_x in [70, 110, 200, 240]:
            draw.rectangle([col_x, 160, col_x + 16, 280], fill=(190, 145, 105))
    else: # unknown_geology
        # Chaotic irregular fractures
        for i in range(10):
            draw.line([(i * 30, (i * 47) % 300), (320 - i * 25, (i * 83) % 300)], fill=(110, 60, 40), width=3)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


SPECIMENS = [
    {
        "id": "SPEC-01",
        "name": "Natural Sandstone Cliff",
        "category": "sandstone_cliff",
        "is_human_made": False,
        "is_monument": False,
        "expected_dispositions": ["NON_MONUMENT_REJECTED", "REVIEW_REQUIRED"],
        "must_not_attribute": ["petra", "Petra Archaeological Park"],
    },
    {
        "id": "SPEC-02",
        "name": "Natural Red Rock Formation",
        "category": "red_rock",
        "is_human_made": False,
        "is_monument": False,
        "expected_dispositions": ["NON_MONUMENT_REJECTED", "REVIEW_REQUIRED"],
        "must_not_attribute": ["petra", "Petra Archaeological Park"],
    },
    {
        "id": "SPEC-03",
        "name": "Honeycomb-Weathered Sandstone (Tafoni)",
        "category": "honeycomb_tafoni",
        "is_human_made": False,
        "is_monument": False,
        "expected_dispositions": ["NON_MONUMENT_REJECTED", "REVIEW_REQUIRED"],
        "must_not_attribute": ["petra", "Petra Archaeological Park"],
    },
    {
        "id": "SPEC-04",
        "name": "Natural Cave Opening",
        "category": "natural_cave",
        "is_human_made": False,
        "is_monument": False,
        "expected_dispositions": ["NON_MONUMENT_REJECTED", "REVIEW_REQUIRED"],
        "must_not_attribute": ["petra", "ajanta_caves", "ellora_caves"],
    },
    {
        "id": "SPEC-05",
        "name": "Rock-Cut Temple Facade (Ajanta/Ellora Style)",
        "category": "rock_cut_temple",
        "is_human_made": True,
        "is_monument": True,
        "expected_dispositions": ["VERIFIED_MATCH", "UNKNOWN_HERITAGE_SPECIMEN", "REVIEW_REQUIRED"],
        "must_not_attribute": [],
    },
    {
        "id": "SPEC-06",
        "name": "Carved Archaeological Entrance",
        "category": "carved_entrance",
        "is_human_made": True,
        "is_monument": True,
        "expected_dispositions": ["VERIFIED_MATCH", "UNKNOWN_HERITAGE_SPECIMEN", "REVIEW_REQUIRED"],
        "must_not_attribute": [],
    },
    {
        "id": "SPEC-07",
        "name": "Monument Facade Close-up (Macro Carving)",
        "category": "facade_closeup",
        "is_human_made": True,
        "is_monument": True,
        "expected_dispositions": ["VERIFIED_MATCH", "UNKNOWN_HERITAGE_SPECIMEN", "REVIEW_REQUIRED"],
        "must_not_attribute": [], # Must NOT be hard-rejected
    },
    {
        "id": "SPEC-08",
        "name": "Partially Eroded Architectural Carvings",
        "category": "eroded_carvings",
        "is_human_made": True,
        "is_monument": True,
        "expected_dispositions": ["REVIEW_REQUIRED", "UNKNOWN_HERITAGE_SPECIMEN", "VERIFIED_MATCH"],
        "must_not_attribute": [],
    },
    {
        "id": "SPEC-09",
        "name": "Ordinary Rocks Resembling Architectural Patterns",
        "category": "rock_resembling_arch",
        "is_human_made": False,
        "is_monument": False,
        "expected_dispositions": ["NON_MONUMENT_REJECTED", "REVIEW_REQUIRED"],
        "must_not_attribute": ["petra", "Petra Archaeological Park"],
    },
    {
        "id": "SPEC-10",
        "name": "Genuine Petra Al-Khazneh Facade Photograph",
        "category": "petra_facade",
        "is_human_made": True,
        "is_monument": True,
        "expected_dispositions": ["VERIFIED_MATCH", "UNKNOWN_HERITAGE_SPECIMEN", "REVIEW_REQUIRED"],
        "must_not_attribute": [],
    },
    {
        "id": "SPEC-11",
        "name": "Genuine Ajanta Cave Photograph",
        "category": "ajanta_cave",
        "is_human_made": True,
        "is_monument": True,
        "expected_dispositions": ["VERIFIED_MATCH", "UNKNOWN_HERITAGE_SPECIMEN", "REVIEW_REQUIRED"],
        "must_not_attribute": [],
    },
    {
        "id": "SPEC-12",
        "name": "Unknown Geological Formation",
        "category": "unknown_geology",
        "is_human_made": False,
        "is_monument": False,
        "expected_dispositions": ["NON_MONUMENT_REJECTED", "REVIEW_REQUIRED"],
        "must_not_attribute": ["petra", "ajanta_caves", "taj_mahal"],
    },
]


def run_evaluation():
    print("=" * 80)
    print("PHASE 14: GEOLOGICAL SAFEGUARDS & ROCK-CUT HERITAGE EVALUATION")
    print("=" * 80)

    initialize_backend_resources()
    client = TestClient(app)

    results = []
    all_passed = True

    print(f"\n{'ID':<8} {'Specimen':<34} {'Status':<25} {'Gatekeeper':<12} {'Top Cand':<20} {'Attribution'}")
    print("-" * 110)

    for spec in SPECIMENS:
        img_bytes = generate_synthetic_specimen(spec["category"])
        resp = client.post(
            "/api/verify-monument",
            files={"file": (f"{spec['id'].lower()}.jpg", img_bytes, "image/jpeg")}
        )
        assert resp.status_code == 200, f"HTTP Error {resp.status_code}: {resp.text}"
        data = resp.json()

        v_status = data.get("verification_status")
        gk_score = data.get("pipeline_telemetry", {}).get("architectural_gatekeeper_score", 0.0)
        mon_name = data.get("monument_name") or "None"
        mon_key = data.get("monument_key") or "None"
        geo_assessment = data.get("geological_assessment") or "N/A"
        citations = data.get("grounded_citations")

        # Validation assertions
        is_disp_valid = v_status in spec["expected_dispositions"]
        is_attr_forbidden = any(
            bad.lower() in mon_name.lower() or bad.lower() in mon_key.lower()
            for bad in spec["must_not_attribute"]
        ) and v_status == "VERIFIED_MATCH"

        passed = is_disp_valid and not is_attr_forbidden
        if not passed:
            all_passed = False

        status_flag = "[PASS]" if passed else "[FAIL]"

        print(
            f"{spec['id']:<8} {spec['name'][:32]:<34} {v_status:<25} {gk_score*100:>5.1f}%      {mon_name[:18]:<20} {status_flag}"
        )

        results.append({
            "specimen": spec,
            "response": data,
            "passed": passed,
        })

    print("-" * 110)
    summary_status = "ALL 12 SPECIMENS PASSED EVALUATION" if all_passed else "SOME SPECIMENS FAILED"
    print(f"VERDICT: {summary_status}")
    print("=" * 80)

    return all_passed, results


if __name__ == "__main__":
    success, _ = run_evaluation()
    sys.exit(0 if success else 1)

