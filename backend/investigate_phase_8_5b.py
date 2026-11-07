"""
Phase 8.5B Deep Investigation Script
Inspects current pipeline behavior on:
1. Eiffel Tower (Screenshot 2026-10-01 005544.png)
2. Mysore Palace (split_d_086_mysore_palace.jpg)
3. Taj Mahal (taj_mahal/img_1.jpg)
4. Charminar (charminar/img_1.jpg)
5. Mathematics document (Screenshot 2026-10-01 005418.png)
6. Ambiguous catalog specimen (split_d_019_hampi_stone_chariot.jpg)
"""

import sys
import json
import time
from pathlib import Path
import urllib.request
import mimetypes

WORKSPACE = Path(__file__).resolve().parent.parent
BACKEND_URL = "http://127.0.0.1:8000"

def post_image(img_path: Path):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = img_path.name
    content_type = mimetypes.guess_type(str(img_path))[0] or "application/octet-stream"

    with open(img_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BACKEND_URL}/api/verify-monument",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def main():
    test_files = [
        ("Eiffel Tower (Out-of-Catalog)", Path(r"C:\Users\humai\Pictures\Screenshots\Screenshot 2026-10-01 005544.png")),
        ("Mysore Palace (Out-of-Catalog)", WORKSPACE / "backend" / "datasets" / "independent_final_test_v4" / "split_d_086_mysore_palace.jpg"),
        ("Taj Mahal (Catalog Positive)", WORKSPACE / "backend" / "dataset" / "taj_mahal" / "img_1.jpg"),
        ("Charminar (Catalog Positive)", WORKSPACE / "backend" / "dataset" / "charminar" / "img_1.jpg"),
        ("Math Document (Non-Monument)", Path(r"C:\Users\humai\Pictures\Screenshots\Screenshot 2026-10-01 005418.png")),
        ("Hampi Ambiguous (Catalog Ambiguous)", WORKSPACE / "backend" / "datasets" / "independent_final_test_v4" / "split_d_019_hampi_stone_chariot.jpg"),
    ]

    print("==========================================================================================")
    print("PHASE 8.5B BASELINE INVESTIGATION")
    print("==========================================================================================")
    
    baseline_results = {}

    for label, path in test_files:
        if not path.exists():
            print(f"ERROR: File not found: {path}")
            continue

        status, resp = post_image(path)
        u = resp.get("uncertainty", {})
        top_cand = u.get("top_candidates", [])
        cands_summary = [f"{c['monument_name']} ({c['max_similarity']:.4f})" for c in top_cand[:3]]
        
        print(f"\n--- {label} ({path.name}) ---")
        print(f"HTTP Status: {status}")
        print(f"Decision State: {resp.get('verification_status')}")
        print(f"Top Candidate: {resp.get('monument_name')} ({resp.get('monument_key')})")
        print(f"Confidence Score: {resp.get('confidence_score')}")
        print(f"Gatekeeper Score: {u.get('gatekeeper_score')}")
        print(f"Top 1 Sim: {u.get('top1_similarity')}")
        print(f"Top 2 Sim: {u.get('top2_similarity')}")
        print(f"Margin: {u.get('similarity_margin')}")
        print(f"Reason Codes: {u.get('reason_codes')}")
        print(f"Top Candidates: {', '.join(cands_summary)}")
        print(f"Decision Reason: {u.get('explanation')}")

        baseline_results[label] = {
            "file": path.name,
            "verification_status": resp.get("verification_status"),
            "monument_name": resp.get("monument_name"),
            "monument_key": resp.get("monument_key"),
            "confidence_score": resp.get("confidence_score"),
            "gatekeeper_score": u.get("gatekeeper_score"),
            "top1_similarity": u.get("top1_similarity"),
            "top2_similarity": u.get("top2_similarity"),
            "similarity_margin": u.get("similarity_margin"),
            "reason_codes": u.get("reason_codes"),
            "explanation": u.get("explanation"),
            "candidates": cands_summary
        }

    out_file = WORKSPACE / "backend" / "phase_8_5b_baseline_investigation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(baseline_results, f, indent=2)
    print(f"\nSaved baseline investigation to: {out_file}")

if __name__ == "__main__":
    main()


def inspect_details():
    test_files = [
        ("Eiffel Tower", Path(r"C:\Users\humai\Pictures\Screenshots\Screenshot 2026-10-01 005544.png")),
        ("Mysore Palace", WORKSPACE / "backend" / "datasets" / "independent_final_test_v4" / "split_d_086_mysore_palace.jpg"),
        ("Math Document", Path(r"C:\Users\humai\Pictures\Screenshots\Screenshot 2026-10-01 005418.png")),
    ]
    for label, p in test_files:
        status, resp = post_image(p)
        print(f"\n==================== {label} ====================")
        print("Decision State:", resp.get("verification_status"))
        print("Verification Tier:", resp.get("verification_tier"))
        print("Local Features:", json.dumps(resp.get("local_features"), indent=2))
        print("Tier 2 Analysis:", json.dumps(resp.get("tier2_analysis"), indent=2))

if __name__ == "__main__":
    inspect_details()


def compare_sift():
    p_hampi = WORKSPACE / "backend" / "datasets" / "independent_final_test_v4" / "split_d_019_hampi_stone_chariot.jpg"
    p_mysore = WORKSPACE / "backend" / "datasets" / "independent_final_test_v4" / "split_d_086_mysore_palace.jpg"
    
    for p in [p_hampi, p_mysore]:
        status, r = post_image(p)
        lf = r.get("local_features", {})
        gv = lf.get("geometric_verification", {})
        print(f"\n{p.name}:")
        print(f"  Decision: {r.get('verification_status')}")
        print(f"  Top Candidate: {r.get('monument_name')}")
        print(f"  Top1 Sim: {r.get('uncertainty', {}).get('top1_similarity')}")
        print(f"  Top2 Sim: {r.get('uncertainty', {}).get('top2_similarity')}")
        print(f"  Margin: {r.get('uncertainty', {}).get('similarity_margin')}")
        print(f"  SIFT Inliers: {gv.get('inliers_count')}")
        print(f"  SIFT Status: {gv.get('status')}")
        print(f"  Alignment: {lf.get('alignment_status')}")

if __name__ == "__main__":
    compare_sift()


def test_user_artifact():
    p = Path(r"C:\Users\humai\.gemini\antigravity\brain\65f04f8f-d136-410f-b3f3-0096c601b0ae\.user_uploaded\media_1793820638249_4b1deae5.png")
    if p.exists():
        status, r = post_image(p)
        print("\n--- User Uploaded Artifact ---")
        print("Status:", r.get("verification_status"))
        print("Monument:", r.get("monument_name"))
        print("Gatekeeper:", r.get("pipeline_telemetry", {}).get("architectural_gatekeeper_score"))
        print("Top1 Sim:", r.get("uncertainty", {}).get("top1_similarity"))
        print("Top2 Sim:", r.get("uncertainty", {}).get("top2_similarity"))
        print("Margin:", r.get("uncertainty", {}).get("similarity_margin"))

if __name__ == "__main__":
    test_user_artifact()
