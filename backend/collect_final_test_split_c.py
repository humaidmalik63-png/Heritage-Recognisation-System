"""
Phase 8.2C: Collection of Genuinely Untouched Final Evaluation Dataset (Split C)
Collects 35 authentic, openly licensed photographs from Wikimedia Commons:
- 20 catalog monument images (2 per monument across 10 canonical classes)
- 7 out-of-catalog Indian heritage monuments (e.g., Meenakshi Temple, Golconda Fort, Ellora Caves, etc.)
- 8 non-monument distractors (everyday Indian scenes: tea stall, autorickshaw, peacock, etc.)

Strictly verifies:
- ZERO SHA-256 match with Reference Gallery, Dev v1, Calib v3, Test v2, Holdout v1
- ZERO perceptual dHash near-match (Hamming distance > 4) with all existing datasets
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
logger = logging.getLogger("collect_split_c")

BASE_DIR = Path(__file__).resolve().parent
SPLIT_C_DIR = BASE_DIR / "datasets" / "independent_final_test_v3"
SPLIT_C_MANIFEST = BASE_DIR / "datasets" / "independent_final_test_v3_manifest.json"

USER_AGENT = "HeritageArchivalBot/5.0 (SIH25052; FinalUntouchedEvaluation; mailto:heritage-research@sih.gov)"
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

# Search targets for Split C
TARGET_SPECIMENS = [
    # 1. Brihadeeswarar Temple (2 images)
    {"category": "catalog", "monument_key": "brihadeeswarar_temple", "query": "Brihadisvara Temple gopuram", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "brihadeeswarar_temple", "query": "Thanjavur Temple courtyard", "condition": "side_view"},
    # 2. Charminar (2 images)
    {"category": "catalog", "monument_key": "charminar", "query": "Charminar archway Hyderabad", "condition": "close_up_carving"},
    {"category": "catalog", "monument_key": "charminar", "query": "Charminar daylight view", "condition": "front_view"},
    # 3. Gateway of India (2 images)
    {"category": "catalog", "monument_key": "gateway_of_india", "query": "Gateway of India Mumbai boat harbor", "condition": "distant_view"},
    {"category": "catalog", "monument_key": "gateway_of_india", "query": "Gateway of India bas-relief", "condition": "architectural_carving"},
    # 4. Hampi Stone Chariot (2 images)
    {"category": "catalog", "monument_key": "hampi_stone_chariot", "query": "Hampi Vittala temple chariot wheel stone", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "hampi_stone_chariot", "query": "Stone chariot Hampi twilight", "condition": "night_view"},
    # 5. Hawa Mahal (2 images)
    {"category": "catalog", "monument_key": "hawa_mahal", "query": "Hawa Mahal jharokha window", "condition": "close_up_carving"},
    {"category": "catalog", "monument_key": "hawa_mahal", "query": "Hawa Mahal Jaipur angle street", "condition": "unusual_angle"},
    # 6. Konark Sun Temple (2 images)
    {"category": "catalog", "monument_key": "konark_sun_temple", "query": "Konark Sun Temple wheel relief carving", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "konark_sun_temple", "query": "Konark Sun temple ruins side", "condition": "side_view"},
    # 7. Qutub Minar (2 images)
    {"category": "catalog", "monument_key": "qutub_minar", "query": "Qutb Minar balcony calligraphy sandstone", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "qutub_minar", "query": "Qutub Minar complex iron pillar", "condition": "full_structure"},
    # 8. Sanchi Stupa (2 images)
    {"category": "catalog", "monument_key": "sanchi_stupa", "query": "Sanchi Stupa South Gateway torana relief", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "sanchi_stupa", "query": "Great Stupa Sanchi dome balustrade", "condition": "partial_view"},
    # 9. Taj Mahal (2 images)
    {"category": "catalog", "monument_key": "taj_mahal", "query": "Taj Mahal minaret marble inlay detail", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "taj_mahal", "query": "Taj Mahal Yamuna river rear perspective", "condition": "rear_view"},
    # 10. Victoria Memorial (2 images)
    {"category": "catalog", "monument_key": "victoria_memorial", "query": "Victoria Memorial Kolkata Angel statue bronze dome", "condition": "architectural_carving"},
    {"category": "catalog", "monument_key": "victoria_memorial", "query": "Victoria Memorial garden lake reflection", "condition": "distant_view"},

    # Unknown Heritage Monuments (7 images)
    {"category": "unknown_heritage", "monument_key": "unknown_heritage", "query": "Meenakshi Temple Madurai gopuram sculptures", "condition": "out_of_catalog_heritage"},
    {"category": "unknown_heritage", "monument_key": "unknown_heritage", "query": "Golconda Fort Hyderabad fortress ruins", "condition": "out_of_catalog_heritage"},
    {"category": "unknown_heritage", "monument_key": "unknown_heritage", "query": "Kailasa Temple Ellora Caves rock cut", "condition": "out_of_catalog_heritage"},
    {"category": "unknown_heritage", "monument_key": "unknown_heritage", "query": "Fatehpur Sikri Buland Darwaza gateway", "condition": "out_of_catalog_heritage"},
    {"category": "unknown_heritage", "monument_key": "unknown_heritage", "query": "Modhera Sun Temple Gujarat stepped tank", "condition": "out_of_catalog_heritage"},
    {"category": "unknown_heritage", "monument_key": "unknown_heritage", "query": "Elephanta Caves Trimurti Shiva sculpture", "condition": "out_of_catalog_heritage"},
    {"category": "unknown_heritage", "monument_key": "unknown_heritage", "query": "Pattadakal temples group Karnataka", "condition": "out_of_catalog_heritage"},

    # Non-Monument Distractors (8 images)
    {"category": "non_monument", "monument_key": "non_monument", "query": "Indian tea stall chai roadside", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Auto rickshaw India street", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Peacock plumage Indian wildlife", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Spices market bazaar India colourful", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Handloom weaving silk sari Varanasi", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Indian thali meal traditional food", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Banyan tree aerial roots India", "condition": "non_monument_distractor"},
    {"category": "non_monument", "monument_key": "non_monument", "query": "Kolkata yellow taxi vintage street", "condition": "non_monument_distractor"},
]

def search_wikimedia(query: str, limit: int = 8) -> List[Dict[str, Any]]:
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

def download_and_validate_specimens():
    SPLIT_C_DIR.mkdir(parents=True, exist_ok=True)
    existing_sha, existing_dh = load_all_existing_hashes()

    manifest_records = []
    specimen_counter = 1

    for target in TARGET_SPECIMENS:
        cat = target["category"]
        mon_key = target["monument_key"]
        query = target["query"]
        cond = target["condition"]
        logger.info(f"Searching for target [{cat}] {mon_key}: '{query}'...")

        search_results = search_wikimedia(query, limit=10)
        found_specimen = False

        for res in search_results:
            title = res["title"]
            if not any(title.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                continue

            info = get_image_info(title)
            if not info or not info.get("url"):
                continue

            # Fetch image bytes
            img_url = info["url"]
            try:
                img_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(img_req, timeout=15, context=SSL_CONTEXT) as resp:
                    raw_bytes = resp.read()
            except Exception as e:
                logger.warning(f"Download failed for {title}: {e}")
                continue

            if len(raw_bytes) < 8000:
                continue

            # Check SHA-256 collision
            sha = compute_sha256(raw_bytes)
            if sha in existing_sha:
                logger.info(f"Duplicate SHA-256 for {title}, skipping...")
                continue

            # Verify image opening and dHash
            try:
                import io
                img = Image.open(io.BytesIO(raw_bytes))
                img_format = img.format or "JPEG"
                if img.width < 400 or img.height < 300:
                    continue
                dh = compute_dhash(img)
            except Exception as e:
                logger.warning(f"Corrupt image {title}: {e}")
                continue

            # Check perceptual dHash collision
            is_near_dup = False
            for ex_dh in existing_dh:
                if hamming_distance(dh, ex_dh) <= 4:
                    is_near_dup = True
                    break
            if is_near_dup:
                logger.info(f"Near-duplicate dHash for {title}, skipping...")
                continue

            # Success! Save image
            specimen_id = f"split_c_{specimen_counter:03d}"
            filename = f"{specimen_id}_{mon_key}.jpg"
            out_file = SPLIT_C_DIR / filename

            # Save normalized RGB JPEG
            rgb_img = img.convert("RGB")
            rgb_img.save(out_file, "JPEG", quality=90)

            # Update exclusions
            saved_bytes = out_file.read_bytes()
            saved_sha = compute_sha256(saved_bytes)
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
            manifest_records.append(record)
            logger.info(f"[SUCCESS] Collected {specimen_id}: {filename} (Author: {info['author']})")
            specimen_counter += 1
            found_specimen = True
            time.sleep(0.5)
            break

        if not found_specimen:
            logger.error(f"[WARNING] Could not find valid non-duplicate specimen for '{query}'!")

    logger.info(f"Successfully collected {len(manifest_records)} specimens for Split C.")
    manifest_data = {
        "title": "Phase 8.2C Genuinely Untouched Independent Final Evaluation Dataset (Split C)",
        "version": "1.0.0",
        "description": "Genuinely untouched final evaluation split. Strictly excluded from model fitting, tuning, or selection.",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_specimens": len(manifest_records),
        "counts_by_category": {
            "catalog_monuments": sum(1 for r in manifest_records if r["category"] == "catalog"),
            "unknown_heritage": sum(1 for r in manifest_records if r["category"] == "unknown_heritage"),
            "non_monument": sum(1 for r in manifest_records if r["category"] == "non_monument")
        },
        "records": manifest_records
    }

    with open(SPLIT_C_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Saved manifest to {SPLIT_C_MANIFEST}")

if __name__ == "__main__":
    download_and_validate_specimens()
