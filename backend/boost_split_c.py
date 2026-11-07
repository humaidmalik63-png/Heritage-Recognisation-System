"""
Phase 8.2C Booster for Split C: Fills remaining slots to reach 35 authentic, verified specimens.
Uses larger search limits (srlimit=40) and verified non-duplicate Wikimedia queries.
"""

import hashlib
import json
import logging
import os
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("boost_split_c")

BASE_DIR = Path(__file__).resolve().parent
SPLIT_C_DIR = BASE_DIR / "datasets" / "independent_final_test_v3"
SPLIT_C_MANIFEST = BASE_DIR / "datasets" / "independent_final_test_v3_manifest.json"

USER_AGENT = "HeritageArchivalBot/5.1 (SIH25052; FinalUntouchedEvaluation; mailto:heritage-research@sih.gov)"
SSL_CONTEXT = ssl._create_unverified_context()

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(resized, dtype=np.float32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    decimal_val = 0
    for idx, val in enumerate(diff.flatten()):
        if val:
            decimal_val |= 1 << idx
    return f"{decimal_val:016x}"

def hamming_distance(h1: str, h2: str) -> int:
    try:
        return bin(int(h1, 16) ^ int(h2, 16)).count('1')
    except Exception:
        return 999

def load_all_existing_hashes() -> Tuple[Set[str], Set[str]]:
    sha_set = set()
    dh_set = set()
    dirs = [
        BASE_DIR / "datasets" / "reference_gallery_v2",
        BASE_DIR / "datasets" / "independent_eval",
        BASE_DIR / "datasets" / "independent_eval_v2",
        BASE_DIR / "datasets" / "calibration_development",
        BASE_DIR / "datasets" / "calibration_dataset_v3",
        BASE_DIR / "datasets" / "local_feature_eval",
        BASE_DIR / "datasets" / "independent_final_test_v3",
        BASE_DIR / "dataset",
    ]
    for d in dirs:
        if not d.exists(): continue
        for p in d.rglob("*.*"):
            if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                try:
                    raw = p.read_bytes()
                    sha_set.add(compute_sha256(raw))
                    with Image.open(p) as img:
                        dh_set.add(compute_dhash(img))
                except Exception:
                    pass
    logger.info(f"Loaded {len(sha_set)} SHA-256 and {len(dh_set)} dHash exclusion records.")
    return sha_set, dh_set

BOOSTER_TARGETS = [
    {"category": "catalog", "monument_key": "charminar", "query": "Charminar minaret stucco", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "gateway_of_india", "query": "Apollo Bunder Gateway Mumbai", "condition": "distant_view"},
    {"category": "catalog", "monument_key": "hampi_stone_chariot", "query": "Vittala temple ratha carving", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "hampi_stone_chariot", "query": "Hampi Vittala chariot stone elephant", "condition": "partial_view"},
    {"category": "catalog", "monument_key": "hawa_mahal", "query": "Palace of the Winds Jaipur courtyard", "condition": "rear_view"},
    {"category": "catalog", "monument_key": "konark_sun_temple", "query": "Konark nata mandir sculpture", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "qutub_minar", "query": "Alai Darwaza Qutub complex lattice", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "sanchi_stupa", "query": "Sanchi Buddhist gateway yakshi", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "taj_mahal", "query": "Taj Mahal marble dome finial", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "taj_mahal", "query": "Taj Mahal south gate sandstone entrance", "condition": "front_view"},
    {"category": "catalog", "monument_key": "victoria_memorial", "query": "Victoria Memorial hall lions statue", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "victoria_memorial", "query": "Victoria Memorial south facade Calcutta", "condition": "front_view"},
    # Non-monument distractors
    {"category": "non_monument", "monument_key": "non_monument", "query": "Mumbai dhabawala lunch boxes", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Indian pottery clay pots artisan", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Kathakali dancer face paint makeup", "condition": "non_monument_distractor"},
]

def search_wikimedia(query: str, limit: int = 40) -> List[Dict[str, Any]]:
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srnamespace": "6",
        "srsearch": query,
        "srlimit": str(limit),
    }
    url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12, context=SSL_CONTEXT) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("query", {}).get("search", [])
    except Exception as e:
        logger.warning(f"Search failed for '{query}': {e}")
        return []

def get_image_info(title: str) -> Optional[Dict[str, Any]]:
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
    }
    url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12, context=SSL_CONTEXT) as response:
            data = json.loads(response.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                if "imageinfo" in page and len(page["imageinfo"]) > 0:
                    info = page["imageinfo"][0]
                    ext = info.get("extmetadata", {})
                    author_raw = ext.get("Artist", {}).get("value", "")
                    clean_author = re.sub(r"<[^>]+>", "", author_raw).strip() or "Wikimedia Contributor"
                    license_name = ext.get("LicenseShortName", {}).get("value", "Creative Commons / Public Domain")
                    return {
                        "url": info.get("url"),
                        "width": info.get("width"),
                        "height": info.get("height"),
                        "size": info.get("size"),
                        "author": clean_author[:80],
                        "license": license_name[:60],
                    }
    except Exception as e:
        logger.warning(f"Imageinfo failed for '{title}': {e}")
    return None

def run_split_c_booster():
    with open(SPLIT_C_MANIFEST, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    existing_records = manifest_data.get("records", [])
    existing_sha, existing_dh = load_all_existing_hashes()

    specimen_counter = len(existing_records) + 1

    for target in BOOSTER_TARGETS:
        cat = target["category"]
        mon_key = target["monument_key"]
        query = target["query"]
        cond = target["condition"]
        logger.info(f"Booster search for [{cat}] {mon_key}: '{query}'...")

        search_results = search_wikimedia(query, limit=40)
        found = False

        for res in search_results:
            title = res["title"]
            if not any(title.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                continue

            info = get_image_info(title)
            if not info or not info.get("url"):
                continue

            img_url = info["url"]
            try:
                img_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(img_req, timeout=15, context=SSL_CONTEXT) as resp:
                    raw_bytes = resp.read()
            except Exception:
                continue

            if len(raw_bytes) < 8000:
                continue

            sha = compute_sha256(raw_bytes)
            if sha in existing_sha:
                continue

            try:
                import io
                img = Image.open(io.BytesIO(raw_bytes))
                if img.width < 400 or img.height < 300:
                    continue
                dh = compute_dhash(img)
            except Exception:
                continue

            is_near_dup = False
            for ex_dh in existing_dh:
                if hamming_distance(dh, ex_dh) <= 4:
                    is_near_dup = True
                    break
            if is_near_dup:
                continue

            specimen_id = f"split_c_{specimen_counter:03d}"
            filename = f"{specimen_id}_{mon_key}.jpg"
            out_file = SPLIT_C_DIR / filename

            rgb_img = img.convert("RGB")
            rgb_img.save(out_file, "JPEG", quality=90)

            saved_sha = compute_sha256(out_file.read_bytes())
            existing_sha.add(saved_sha)
            existing_dh.add(dh)

            record = {
                "specimen_id": specimen_id,
                "category": cat,
                "ground_truth_label": mon_key,
                "monument_name": mon_key.replace("_", " ").title() if cat == "catalog" else ("Out of Catalog Heritage" if cat == "unknown_heritage" else "Non-Monument Distractor"),
                "condition": cond,
                "relative_path": f"datasets/independent_final_test_v3/{filename}",
                "filename": filename,
                "source_title": title,
                "source_url": img_url,
                "author": info["author"],
                "license": info["license"],
                "sha256": saved_sha,
                "dhash": dh,
                "width": rgb_img.width,
                "height": rgb_img.height,
                "split": "independent_final_test_split_c",
                "verification_status": "AUTHENTIC_UNTOUCHED_EVALUATION_SPECIMEN"
            }
            existing_records.append(record)
            logger.info(f"[SUCCESS] Collected {specimen_id}: {filename} (Author: {info['author']})")
            specimen_counter += 1
            found = True
            time.sleep(0.5)
            break

        if not found:
            logger.warning(f"Could not find valid non-duplicate for query '{query}'")

    manifest_data["total_specimens"] = len(existing_records)
    manifest_data["counts_by_category"] = {
        "catalog_monuments": sum(1 for r in existing_records if r["category"] == "catalog"),
        "unknown_heritage": sum(1 for r in existing_records if r["category"] == "unknown_heritage"),
        "non_monument": sum(1 for r in existing_records if r["category"] == "non_monument")
    }
    manifest_data["records"] = existing_records

    with open(SPLIT_C_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Split C booster complete. Total specimens: {len(existing_records)}.")

if __name__ == "__main__":
    run_split_c_booster()

