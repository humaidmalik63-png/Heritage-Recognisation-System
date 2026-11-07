import urllib.request
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TEST_CASES = [
    {
        "name": "Ajanta Caves",
        "image": BASE_DIR / "datasets" / "independent_final_test_v4" / "split_d_085_ajanta_caves.jpg",
        "expected_catalogue_status": "CATALOGUED_METADATA_ONLY",
        "expected_out_of_catalog": False,
        "expected_tier_contains": "METADATA ONLY",
    },
    {
        "name": "Eiffel Tower",
        "image": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "eiffel_tower.jpg",
        "expected_catalogue_status": "OUT_OF_CATALOG",
        "expected_out_of_catalog": True,
        "expected_tier_contains": "OUT-OF-CATALOG",
    },
    {
        "name": "Golden Temple",
        "image": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "golden_temple.jpg",
        "expected_catalogue_status": "CATALOGUED_METADATA_ONLY",
        "expected_out_of_catalog": False,
        "expected_tier_contains": "METADATA ONLY",
    },
    {
        "name": "Mysore Palace",
        "image": BASE_DIR / "datasets" / "phase_8_5c_ooc_eval" / "mysore_palace.jpg",
        "expected_catalogue_status": "CATALOGUED_METADATA_ONLY",
        "expected_out_of_catalog": False,
        "expected_tier_contains": "METADATA ONLY",
    },
    {
        "name": "Taj Mahal",
        "image": BASE_DIR / "datasets" / "independent_final_test_v4" / "split_d_041_taj_mahal.jpg",
        "expected_catalogue_status": "CATALOGUED_AND_RECOGNITION_READY",
        "expected_out_of_catalog": False,
        "expected_tier_contains": "TIER 1",
    },
    {
        "name": "Qutub Minar",
        "image": BASE_DIR / "datasets" / "reference_gallery_v2" / "qutub_minar" / "ref_01.jpg",
        "expected_catalogue_status": "CATALOGUED_AND_RECOGNITION_READY",
        "expected_out_of_catalog": False,
        "expected_tier_contains": "TIER 1",
    },
]

def send_image_to_verify(image_path: Path):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = image_path.name
    with open(image_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/verify-monument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 70)
    print("PHASE 8.6B — LIVE BACKEND VERIFICATION OF CATALOGUE MEMBERSHIP HOTFIX")
    print("=" * 70)

    all_passed = True
    results_summary = []

    for tc in TEST_CASES:
        name = tc["name"]
        img_path = tc["image"]
        if not img_path.exists():
            print(f"[ERROR] Image not found: {img_path}")
            all_passed = False
            continue

        print(f"\nEvaluating: {name} (Specimen: {img_path.name})...")
        try:
            res = send_image_to_verify(img_path)
            cat_status = res.get("catalogue_status")
            ooc = res.get("out_of_catalog_identified")
            tier = res.get("verification_tier")
            status = res.get("verification_status")
            mon_name = res.get("monument_name")
            coords = res.get("coordinates")
            rej_msg = res.get("rejection_message")

            print(f"  -> Monument Name:       {mon_name}")
            print(f"  -> Verification Status: {status}")
            print(f"  -> Catalogue Status:    {cat_status}")
            print(f"  -> Out-of-Catalog Flag: {ooc}")
            print(f"  -> Verification Tier:   {tier}")
            print(f"  -> Coordinates:         {coords}")

            # Verify expectations
            exp_status = tc["expected_catalogue_status"]
            exp_ooc = tc["expected_out_of_catalog"]
            exp_tier_kw = tc["expected_tier_contains"]

            status_ok = (cat_status == exp_status)
            ooc_ok = (ooc == exp_ooc)
            tier_ok = (exp_tier_kw in (tier or ""))

            if status_ok and ooc_ok and tier_ok:
                print(f"  [PASS] {name} passed all criteria.")
            else:
                print(f"  [FAIL] {name} mismatch:")
                if not status_ok:
                    print(f"         Expected catalogue_status='{exp_status}', got '{cat_status}'")
                if not ooc_ok:
                    print(f"         Expected out_of_catalog_identified={exp_ooc}, got {ooc}")
                if not tier_ok:
                    print(f"         Expected tier containing '{exp_tier_kw}', got '{tier}'")
                all_passed = False

            results_summary.append({
                "test": name,
                "status": "PASS" if (status_ok and ooc_ok and tier_ok) else "FAIL",
                "monument_name": mon_name,
                "catalogue_status": cat_status,
                "out_of_catalog_identified": ooc,
                "verification_tier": tier,
                "coordinates": coords,
            })

        except Exception as exc:
            print(f"  [ERROR] Request failed: {exc}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL 6 LIVE TARGET SPECIMENS SATISFIED MEMBERSHIP CRITERIA (100% PASS)!")
    else:
        print("SOME TESTS FAILED. PLEASE REVIEW LOGS.")
    print("=" * 70)

    # Save summary
    with open(BASE_DIR / "phase_8_6b_live_eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
