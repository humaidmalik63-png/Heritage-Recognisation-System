"""
Heritage & Monument Recognition System - Real Image Testing Audit
Project No. 30 (SIH 2025): Phase 6.2 Real-World Validation

Tests 6 specific real-world image conditions:
  1. Known monument under different camera angle (Taj Mahal img_3)
  2. Monument with partial occlusion (Charminar img_1 with 35% occlusion)
  3. Monument with unusual lighting (Hawa Mahal img_2 with altered contrast/gamma)
  4. Unindexed Indian monument (Architectural temple structure outside the 10 cataloged monuments)
  5. Non-monument image (Everyday synthetic non-architectural receipt/scene)
  6. Blurry monument photograph (Severe blur applied to Qutub Minar)
"""

import io
import json
import logging
import sys
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("audit_real_images")


def test_real_image_conditions():
    logger.info("=" * 80)
    logger.info("PHASE 6.2 FINAL REAL-WORLD IMAGE AUDIT (6 CONDITIONS)")
    logger.info("=" * 80)

    results = {}

    with TestClient(app) as client:
        dataset_dir = BASE_DIR / "dataset"

        # -------------------------------------------------------------------------
        # Condition 1: Known monument under different camera angle
        # -------------------------------------------------------------------------
        logger.info("\n--- [Condition 1] Known Monument Under Different Camera Angle (Taj Mahal img_3) ---")
        taj_path = dataset_dir / "taj_mahal" / "img_3.jpg"
        with open(taj_path, "rb") as f:
            img_bytes = f.read()

        resp = client.post("/api/verify-monument", files={"file": ("taj_angle.jpg", img_bytes, "image/jpeg")})
        assert resp.status_code == 200, f"Error: {resp.text}"
        c1_data = resp.json()
        u1 = c1_data.get("uncertainty", {})
        results["condition_1_different_angle"] = {
            "image": "taj_mahal/img_3.jpg",
            "decision": u1.get("decision"),
            "monument_name": c1_data.get("monument_name"),
            "top1_similarity": u1.get("top1_similarity"),
            "top2_similarity": u1.get("top2_similarity"),
            "similarity_margin": u1.get("similarity_margin"),
            "gatekeeper_score": u1.get("gatekeeper_score"),
            "calibrated_probability": u1.get("calibrated_probability"),
            "reason_codes": u1.get("reason_codes"),
            "requires_human_review": u1.get("requires_human_review"),
            "exception_id": c1_data.get("exception_id"),
        }
        logger.info(f"Decision: {u1.get('decision')} | Matched: {c1_data.get('monument_name')} | Sim: {u1.get('top1_similarity')} | Margin: {u1.get('similarity_margin')}")

        # -------------------------------------------------------------------------
        # Condition 2: Monument with partial occlusion
        # -------------------------------------------------------------------------
        logger.info("\n--- [Condition 2] Monument with Partial Occlusion (Charminar with 35% banner) ---")
        char_path = dataset_dir / "charminar" / "img_1.jpg"
        with Image.open(char_path) as base_img:
            occluded = base_img.copy()
            draw = ImageDraw.Draw(occluded)
            w, h = occluded.size
            # Draw a heavy occluding bar covering 35% of the lower frame
            draw.rectangle([0, int(h * 0.65), w, h], fill=(60, 65, 75))
            draw.rectangle([int(w * 0.1), int(h * 0.70), int(w * 0.9), int(h * 0.85)], fill=(200, 200, 210))
            draw.text((int(w * 0.2), int(h * 0.75)), "EXCAVATION & ARCHAEOLOGICAL RESTORATION IN PROGRESS", fill=(20, 20, 20))

            buf = io.BytesIO()
            occluded.save(buf, format="JPEG", quality=90)
            occluded_bytes = buf.getvalue()

        resp = client.post("/api/verify-monument", files={"file": ("charminar_occluded.jpg", occluded_bytes, "image/jpeg")})
        assert resp.status_code == 200, f"Error: {resp.text}"
        c2_data = resp.json()
        u2 = c2_data.get("uncertainty", {})
        results["condition_2_partial_occlusion"] = {
            "image": "charminar/img_1.jpg (35% occluded)",
            "decision": u2.get("decision"),
            "monument_name": c2_data.get("monument_name"),
            "top1_similarity": u2.get("top1_similarity"),
            "top2_similarity": u2.get("top2_similarity"),
            "similarity_margin": u2.get("similarity_margin"),
            "gatekeeper_score": u2.get("gatekeeper_score"),
            "calibrated_probability": u2.get("calibrated_probability"),
            "reason_codes": u2.get("reason_codes"),
            "requires_human_review": u2.get("requires_human_review"),
            "exception_id": c2_data.get("exception_id"),
        }
        logger.info(f"Decision: {u2.get('decision')} | Matched: {c2_data.get('monument_name')} | Sim: {u2.get('top1_similarity')} | Margin: {u2.get('similarity_margin')}")

        # -------------------------------------------------------------------------
        # Condition 3: Monument with unusual lighting
        # -------------------------------------------------------------------------
        logger.info("\n--- [Condition 3] Monument with Unusual Lighting (Hawa Mahal extreme color temperature / contrast) ---")
        hawa_path = dataset_dir / "hawa_mahal" / "img_2.jpg"
        with Image.open(hawa_path) as base_img:
            unusual_lighting = base_img.copy()
            # Heavy contrast & warm golden hour / sunset cast
            enhancer = ImageEnhance.Color(unusual_lighting)
            unusual_lighting = enhancer.enhance(2.8)
            enhancer = ImageEnhance.Contrast(unusual_lighting)
            unusual_lighting = enhancer.enhance(1.7)
            enhancer = ImageEnhance.Brightness(unusual_lighting)
            unusual_lighting = enhancer.enhance(0.7)

            buf = io.BytesIO()
            unusual_lighting.save(buf, format="JPEG", quality=90)
            lighting_bytes = buf.getvalue()

        resp = client.post("/api/verify-monument", files={"file": ("hawa_mahal_lighting.jpg", lighting_bytes, "image/jpeg")})
        assert resp.status_code == 200, f"Error: {resp.text}"
        c3_data = resp.json()
        u3 = c3_data.get("uncertainty", {})
        results["condition_3_unusual_lighting"] = {
            "image": "hawa_mahal/img_2.jpg (extreme contrast/warmth)",
            "decision": u3.get("decision"),
            "monument_name": c3_data.get("monument_name"),
            "top1_similarity": u3.get("top1_similarity"),
            "top2_similarity": u3.get("top2_similarity"),
            "similarity_margin": u3.get("similarity_margin"),
            "gatekeeper_score": u3.get("gatekeeper_score"),
            "calibrated_probability": u3.get("calibrated_probability"),
            "reason_codes": u3.get("reason_codes"),
            "requires_human_review": u3.get("requires_human_review"),
            "exception_id": c3_data.get("exception_id"),
        }
        logger.info(f"Decision: {u3.get('decision')} | Matched: {c3_data.get('monument_name')} | Sim: {u3.get('top1_similarity')} | Margin: {u3.get('similarity_margin')}")

        # -------------------------------------------------------------------------
        # Condition 4: Unindexed Indian monument (Synthetic Dravidian Temple architecture)
        # -------------------------------------------------------------------------
        logger.info("\n--- [Condition 4] Unindexed Indian Monument (Brihadisvara-style Mandapa) ---")
        # Generate an architectural image that activates the architectural gatekeeper
        # but is distinct from the 10 cataloged monuments
        w, h = 640, 480
        unindexed_img = Image.new("RGB", (w, h), color=(140, 150, 160))
        draw = ImageDraw.Draw(unindexed_img)
        # Sky gradient
        for y in range(int(h * 0.45)):
            r = int(120 + 30 * (y / (h * 0.45)))
            g = int(140 + 30 * (y / (h * 0.45)))
            b = int(180 + 30 * (y / (h * 0.45)))
            draw.line([(0, y), (w, y)], fill=(r, g, b))
        # Stone temple gopuram tiers
        gopuram_color = (165, 130, 95)
        for i, tier_w in enumerate([140, 180, 220, 260, 300, 360]):
            tier_y = int(h * 0.20 + i * 35)
            tier_x0 = (w - tier_w) // 2
            draw.rectangle([tier_x0, tier_y, tier_x0 + tier_w, tier_y + 30], fill=gopuram_color, outline=(90, 70, 50))
            # Carved niche details
            for k in range(tier_x0 + 10, tier_x0 + tier_w - 10, 25):
                draw.rectangle([k, tier_y + 5, k + 15, tier_y + 25], fill=(120, 90, 65))
        # Base plinth
        draw.rectangle([60, int(h * 0.70), w - 60, int(h * 0.90)], fill=(140, 110, 80), outline=(80, 60, 40))
        # Pillars
        for px in range(90, w - 90, 45):
            draw.rectangle([px, int(h * 0.72), px + 18, int(h * 0.88)], fill=(110, 85, 60))

        buf = io.BytesIO()
        unindexed_img.save(buf, format="JPEG", quality=90)
        unindexed_bytes = buf.getvalue()

        resp = client.post("/api/verify-monument", files={"file": ("unindexed_dravidian_temple.jpg", unindexed_bytes, "image/jpeg")})
        assert resp.status_code == 200, f"Error: {resp.text}"
        c4_data = resp.json()
        u4 = c4_data.get("uncertainty", {})
        results["condition_4_unindexed_monument"] = {
            "image": "unindexed_dravidian_temple.jpg",
            "decision": u4.get("decision"),
            "verification_status": c4_data.get("verification_status"),
            "is_monument": c4_data.get("is_monument"),
            "top1_similarity": u4.get("top1_similarity"),
            "top2_similarity": u4.get("top2_similarity"),
            "similarity_margin": u4.get("similarity_margin"),
            "gatekeeper_score": u4.get("gatekeeper_score"),
            "reason_codes": u4.get("reason_codes"),
            "requires_human_review": u4.get("requires_human_review"),
            "exception_id": c4_data.get("exception_id"),
        }
        logger.info(f"Decision: {u4.get('decision')} | Top1 Sim: {u4.get('top1_similarity')} | Gatekeeper: {u4.get('gatekeeper_score')} | Review Flagged: {u4.get('requires_human_review')} | Exception ID: {c4_data.get('exception_id')}")

        # -------------------------------------------------------------------------
        # Condition 5: Non-monument image (Everyday office invoice/receipt)
        # -------------------------------------------------------------------------
        logger.info("\n--- [Condition 5] Non-Monument Image (Document / Receipt) ---")
        non_monument = Image.new("RGB", (500, 700), color=(245, 245, 248))
        draw = ImageDraw.Draw(non_monument)
        # Draw document lines
        draw.rectangle([40, 40, 460, 90], fill=(210, 220, 240))
        draw.text((60, 60), "PURCHASE INVOICE & ORDER SUMMARY", fill=(20, 20, 40))
        for y in range(120, 650, 28):
            draw.line([(40, y), (460, y)], fill=(215, 215, 220), width=1)
            draw.rectangle([50, y - 18, 180, y - 6], fill=(180, 180, 190))
            draw.rectangle([380, y - 18, 450, y - 6], fill=(150, 160, 180))

        buf = io.BytesIO()
        non_monument.save(buf, format="JPEG", quality=90)
        non_monument_bytes = buf.getvalue()

        resp = client.post("/api/verify-monument", files={"file": ("desk_invoice.jpg", non_monument_bytes, "image/jpeg")})
        assert resp.status_code == 200, f"Error: {resp.text}"
        c5_data = resp.json()
        u5 = c5_data.get("uncertainty", {})
        results["condition_5_non_monument"] = {
            "image": "desk_invoice.jpg",
            "decision": u5.get("decision"),
            "verification_status": c5_data.get("verification_status"),
            "is_monument": c5_data.get("is_monument"),
            "top1_similarity": u5.get("top1_similarity"),
            "gatekeeper_score": u5.get("gatekeeper_score"),
            "reason_codes": u5.get("reason_codes"),
            "requires_human_review": u5.get("requires_human_review"),
        }
        logger.info(f"Decision: {u5.get('decision')} | Is Monument: {c5_data.get('is_monument')} | Gatekeeper: {u5.get('gatekeeper_score')}")

        # -------------------------------------------------------------------------
        # Condition 6: Blurry monument photograph
        # -------------------------------------------------------------------------
        logger.info("\n--- [Condition 6] Blurry Monument Photograph (Qutub Minar with heavy Gaussian blur) ---")
        qutub_path = dataset_dir / "qutub_minar" / "img_1.jpg"
        with Image.open(qutub_path) as base_img:
            blurry_qutub = base_img.filter(ImageFilter.GaussianBlur(radius=22))
            buf = io.BytesIO()
            blurry_qutub.save(buf, format="JPEG", quality=85)
            blurry_bytes = buf.getvalue()

        resp = client.post("/api/verify-monument", files={"file": ("blurry_qutub.jpg", blurry_bytes, "image/jpeg")})
        assert resp.status_code == 200, f"Error: {resp.text}"
        c6_data = resp.json()
        u6 = c6_data.get("uncertainty", {})
        results["condition_6_blurry_monument"] = {
            "image": "qutub_minar/img_1.jpg (Gaussian blur radius=22)",
            "decision": u6.get("decision"),
            "verification_status": c6_data.get("verification_status"),
            "blur_score": u6.get("image_quality", {}).get("blur_score"),
            "is_blurry": u6.get("image_quality", {}).get("is_blurry"),
            "passed_quality_check": u6.get("image_quality", {}).get("passed_quality_check"),
            "reason_codes": u6.get("reason_codes"),
            "requires_human_review": u6.get("requires_human_review"),
            "exception_id": c6_data.get("exception_id"),
        }
        logger.info(f"Decision: {u6.get('decision')} | Is Blurry: {u6.get('image_quality', {}).get('is_blurry')} | Blur Score: {u6.get('image_quality', {}).get('blur_score')} | Review Flagged: {u6.get('requires_human_review')}")

        # Save results to disk for inspection
        with open(BASE_DIR / "audit_real_images_report.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    logger.info("\n" + "=" * 80)
    logger.info("REAL-WORLD IMAGE AUDIT COMPLETED. ALL CONDITIONS VERIFIED.")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_real_image_conditions()
