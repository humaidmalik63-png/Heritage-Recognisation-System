# Scan all screenshots in Screenshots directory
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parent.parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from backend.investigate_phase_8_5b import post_image

p_dir = Path(r"C:\Users\humai\Pictures\Screenshots")
for f in sorted(p_dir.glob("Screenshot 2026-10-01*.png")):
    status, r = post_image(f)
    v_status = r.get("verification_status")
    m_name = str(r.get("monument_name"))[:18]
    gk = r.get("pipeline_telemetry", {}).get("architectural_gatekeeper_score")
    sim = r.get("uncertainty", {}).get("top1_similarity")
    margin = r.get("uncertainty", {}).get("similarity_margin")
    print(f"{f.name[:32]:32s} | Status: {v_status:25s} | Top: {m_name:18s} | GK: {gk} | Sim: {sim} | Margin: {margin}")
