"""
Inspect all 20 out-of-catalog heritage images in Split D.
"""
import sys
from pathlib import Path
import json

WORKSPACE = Path(__file__).resolve().parent.parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
from backend.investigate_phase_8_5b import post_image

ooc_dir = WORKSPACE / "backend" / "datasets" / "independent_final_test_v4"
ooc_images = sorted([
    f for f in ooc_dir.glob("split_d_*.jpg")
    if any(k in f.name for k in [
        "ajanta", "ellora", "fatehpur", "gol_gumbaz", "jaisalmer",
        "meenakshi", "modhera", "mysore", "rani_ki_vav", "chennakeshava"
    ])
])

print(f"Found {len(ooc_images)} out-of-catalog heritage images in Split D.\n")

results = []
for img_path in ooc_images:
    status, resp = post_image(img_path)
    u = resp.get("uncertainty", {})
    top_cand = u.get("top_candidates", [])
    top1 = top_cand[0] if top_cand else {}
    top2 = top_cand[1] if len(top_cand) > 1 else {}
    
    res_item = {
        "file": img_path.name,
        "status": resp.get("verification_status"),
        "top1_monument": top1.get("monument_name"),
        "top1_sim": u.get("top1_similarity"),
        "top2_sim": u.get("top2_similarity"),
        "margin": u.get("similarity_margin"),
        "gatekeeper": u.get("gatekeeper_score"),
    }
    results.append(res_item)
    print(f"{img_path.name[:35]:35s} | Status: {res_item['status']:25s} | Top1: {res_item['top1_sim']:.4f} ({res_item['top1_monument'][:15]}) | Margin: {res_item['margin']:.4f} | GK: {res_item['gatekeeper']:.4f}")

out_path = WORKSPACE / "backend" / "phase_8_5b_split_d_ooc_survey.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\nSurvey saved to {out_path}")
