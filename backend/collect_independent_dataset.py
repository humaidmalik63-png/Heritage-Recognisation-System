"""
Independent Evaluation Dataset Collector & Verifier
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform
SIH 2025 (SIH25052)

Downloads 2 verified independent Wikimedia Commons holdout photographs per monument (20 total),
records real provenance (photographer, license, dimensions, SHA-256), verifies zero leakage
against the 40 reference images, and serializes `backend/independent_eval_manifest.json`.
"""

import hashlib
import json
import logging
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("collect_dataset")

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets" / "independent_eval"
REF_DIR = BASE_DIR / "dataset"
MANIFEST_PATH = BASE_DIR / "independent_eval_manifest.json"

DATASET_DIR.mkdir(parents=True, exist_ok=True)

# 1. Compute reference hashes to guarantee zero data leakage
ref_hashes = set()
for p in REF_DIR.rglob("*"):
    if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"):
        with open(p, "rb") as f:
            ref_hashes.add(hashlib.sha256(f.read()).hexdigest())
logger.info(f"Loaded {len(ref_hashes)} reference image hashes to enforce zero leakage.")

MONUMENTS_TARGETS = [
    {
        "monument_key": "brihadeeswarar_temple",
        "monument_name": "Brihadeeswarar Temple",
        "search_query": "Brihadisvara Temple Thanjavur vimana",
        "prefix": "brihadeeswarar_temple",
    },
    {
        "monument_key": "charminar",
        "monument_name": "Charminar",
        "search_query": "Charminar Hyderabad facade",
        "prefix": "charminar",
    },
    {
        "monument_key": "gateway_of_india",
        "monument_name": "Gateway of India",
        "search_query": "Gateway of India Mumbai arch",
        "prefix": "gateway_of_india",
    },
    {
        "monument_key": "hampi_stone_chariot",
        "monument_name": "Hampi Stone Chariot",
        "search_query": "Stone Chariot Hampi Vittala",
        "prefix": "hampi_stone_chariot",
    },
    {
        "monument_key": "hawa_mahal",
        "monument_name": "Hawa Mahal",
        "search_query": "Hawa Mahal Jaipur facade",
        "prefix": "hawa_mahal",
    },
    {
        "monument_key": "konark_sun_temple",
        "monument_name": "Konark Sun Temple",
        "search_query": "Konark Sun Temple wheel stone",
        "prefix": "konark_sun_temple",
    },
    {
        "monument_key": "qutub_minar",
        "monument_name": "Qutub Minar",
        "search_query": "Qutb Minar Delhi tower",
        "prefix": "qutub_minar",
    },
    {
        "monument_key": "sanchi_stupa",
        "monument_name": "Sanchi Stupa",
        "search_query": "Great Stupa Sanchi torana",
        "prefix": "sanchi_stupa",
    },
    {
        "monument_key": "taj_mahal",
        "monument_name": "Taj Mahal",
        "search_query": "Taj Mahal Agra marble facade",
        "prefix": "taj_mahal",
    },
    {
        "monument_key": "victoria_memorial",
        "monument_name": "Victoria Memorial",
        "search_query": "Victoria Memorial Kolkata dome",
        "prefix": "victoria_memorial",
    },
]

def clean_html(text: str) -> str:
    if not text:
        return "Unknown"
    clean = re.sub(r"<[^>]+>", "", text)
    return " ".join(clean.split()).strip()

def search_wikimedia(query: str, limit: int = 8):
    url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}"
        f"&gsrlimit={limit}&prop=imageinfo&iiprop=url|size|extmetadata&format=json"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "HeritageArchivalBot/1.0 (sih25052@heritage.org; Python/3.11)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            return list(pages.values())
    except Exception as e:
        logger.warning(f"Wikimedia API search failed for '{query}': {e}")
        return []

def download_and_verify(image_url: str, dest_path: Path):
    req = urllib.request.Request(
        image_url,
        headers={"User-Agent": "HeritageArchivalBot/1.0 (sih25052@heritage.org; Python/3.11)"},
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        content = res.read()
    
    # Write file
    with open(dest_path, "wb") as f:
        f.write(content)

    # PIL verification
    with Image.open(dest_path) as img:
        img.verify()
    
    # Re-open for geometry
    with Image.open(dest_path) as img:
        width, height = img.size
        format_name = img.format
    
    sha256_hash = hashlib.sha256(content).hexdigest()
    return width, height, format_name, len(content), sha256_hash

verified_records = []
excluded_records = []

for item in MONUMENTS_TARGETS:
    key = item["monument_key"]
    name = item["monument_name"]
    query = item["search_query"]
    prefix = item["prefix"]
    logger.info(f"Searching verified holdouts for {name} ({key})...")

    candidates = search_wikimedia(query, limit=10)
    downloaded_count = 0

    for cand in candidates:
        if downloaded_count >= 2:
            break

        if "imageinfo" not in cand or not cand["imageinfo"]:
            continue

        info = cand["imageinfo"][0]
        raw_url = info.get("url", "")
        clean_url = raw_url.split("?")[0]
        title = cand.get("title", "File:Unknown")
        
        # We need JPEG or PNG
        if not clean_url.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        meta = info.get("extmetadata", {})
        artist = clean_html(meta.get("Artist", {}).get("value", ""))
        license_name = meta.get("LicenseShortName", {}).get("value", "Creative Commons")
        description = clean_html(meta.get("ImageDescription", {}).get("value", f"Photograph of {name}"))
        source_wiki = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"

        idx_str = f"0{downloaded_count + 1}"
        file_name = f"{prefix}_indep_{idx_str}.jpg"
        dest_path = DATASET_DIR / file_name

        try:
            logger.info(f"  Fetching candidate [{title}] -> {file_name}")
            w, h, fmt, size_bytes, sha = download_and_verify(raw_url, dest_path)

            # Check for data leakage against the 40 reference images
            if sha in ref_hashes:
                logger.warning(f"  [LEAKAGE REJECTED] Image {file_name} matches a FAISS reference image hash! Excluding.")
                dest_path.unlink(missing_ok=True)
                excluded_records.append({
                    "title": title,
                    "monument_key": key,
                    "reason": "Hash collision with FAISS gallery reference image (Data Leakage)",
                    "url": raw_url
                })
                continue

            # Minimum acceptable resolution: 300x300
            if w < 300 or h < 300:
                logger.warning(f"  [LOW RES REJECTED] Image {file_name} resolution {w}x{h} too small.")
                dest_path.unlink(missing_ok=True)
                excluded_records.append({
                    "title": title,
                    "monument_key": key,
                    "reason": f"Insufficient resolution {w}x{h} (< 300px)",
                    "url": raw_url
                })
                continue

            record = {
                "image_id": f"indep_{prefix[:4]}_{idx_str}",
                "monument_key": key,
                "monument_name": name,
                "file_name": file_name,
                "file_path": str(dest_path.relative_to(BASE_DIR)).replace("\\", "/"),
                "source_title": title,
                "source_url": source_wiki,
                "direct_media_url": clean_url,
                "provenance": "Wikimedia Commons / Independent Curatorial Holdout Split",
                "photographer": artist if artist else "Wikimedia Commons Contributor",
                "license": license_name,
                "dimensions": {"width": w, "height": h},
                "format": fmt,
                "file_size_bytes": size_bytes,
                "sha256": sha,
                "split": "independent_holdout",
                "verification_status": "VERIFIED_AUTHENTIC_HOLDOUT",
                "capture_condition": description[:120] if description else f"Authentic field perspective of {name}",
            }
            verified_records.append(record)
            downloaded_count += 1
            logger.info(f"  [VERIFIED & SAVED] {file_name} ({w}x{h}, {size_bytes / 1024:.1f} KB, {license_name})")
            time.sleep(1.0)  # Gentle rate limiting for Wikimedia servers

        except Exception as err:
            logger.warning(f"  Failed downloading {title}: {err}")
            dest_path.unlink(missing_ok=True)
            excluded_records.append({
                "title": title,
                "monument_key": key,
                "reason": f"Download / verification error: {str(err)}",
                "url": raw_url
            })

    if downloaded_count < 2:
        logger.error(f"Could only obtain {downloaded_count} verified images for {name}!")

manifest_output = {
    "dataset_name": "Indian Heritage Verified Independent Holdout Dataset (SIH 2025)",
    "version": "2.0.0",
    "description": "Authentic, independently curated and downloaded holdout evaluation dataset for Project No. 30 (SIH25052). Completely disjoint from the 40 indexed reference images in monument_index.faiss with zero hash overlap.",
    "monuments_evaluated": 10,
    "total_verified_images": len(verified_records),
    "total_excluded_images": len(excluded_records),
    "records": verified_records,
    "excluded_records": excluded_records
}

with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest_output, f, indent=2)

logger.info("\n" + "=" * 70)
logger.info(f"COLLECTION COMPLETE: {len(verified_records)} VERIFIED IMAGES SAVED.")
logger.info(f"Manifest written to: {MANIFEST_PATH}")
logger.info("=" * 70)

