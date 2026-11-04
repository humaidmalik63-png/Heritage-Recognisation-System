"""
Heritage & Monument Recognition System - Dataset Seeder (Phase 1)
Downloads 4 high-quality reference exterior photos for 10 flagship Indian monuments.
Primary Source: Wikimedia Commons API (with proper User-Agent and 1280px rendering)
Fallback Source: DuckDuckGo Image Search (DDGS)
Integrity Check: PIL.Image.open().verify() + RGB conversion + dimension sanity checks.
"""

import json
import logging
import os
import sys
import io
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests
from PIL import Image

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("seed_dataset")

# Paths
BASE_DIR = Path(__file__).resolve().parent
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
DATASET_DIR = BASE_DIR / "dataset"

# Request headers complying with Wikimedia Foundation User-Agent policy
WIKIMEDIA_USER_AGENT = (
    "HeritageMonumentRecognitionSystem/1.0 "
    "(https://github.com/heritage-pj; contact: dev@heritagesystem.internal)"
)
STANDARD_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

TARGET_IMAGES_PER_MONUMENT = 4
MIN_IMAGE_DIMENSION = 400  # Minimum width and height for reference quality
REQUEST_TIMEOUT = 15


# Tailored search keywords for optimal exterior architectural angles
QUERY_OVERRIDES = {
    "gateway_of_india": "Gateway of India Mumbai",
    "charminar": "Charminar Hyderabad",
    "hampi_stone_chariot": "Hampi stone chariot Vittala",
    "victoria_memorial": "Victoria Memorial Kolkata exterior",
    "brihadeeswarar_temple": "Brihadisvara Temple",
}


def fetch_wikimedia_image_urls(monument_key: str, monument_name: str, max_candidates: int = 15) -> List[str]:
    """
    Search Wikimedia Commons API for high-resolution exterior reference photos.
    Requests pre-rendered 1280px thumbnails for fast, reliable, pristine downloads.
    """
    api_url = "https://commons.wikimedia.org/w/api.php"
    headers = {"User-Agent": WIKIMEDIA_USER_AGENT}
    
    search_query = QUERY_OVERRIDES.get(monument_key, monument_name)
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrnamespace": 6,  # 'File:' namespace
        "gsrlimit": max_candidates,
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": 1280,
        "format": "json",
    }
    
    urls = []
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                imageinfo_list = page_info.get("imageinfo", [])
                if not imageinfo_list:
                    continue
                info = imageinfo_list[0]
                mime = info.get("mime", "").lower()
                
                # Exclude vector graphics, audio, video, tiff
                if mime in ["image/jpeg", "image/png", "image/webp"]:
                    # Prefer the 1280px thumburl for faster, pristine web-ready download
                    target_url = info.get("thumburl") or info.get("url")
                    if target_url and target_url.startswith("http"):
                        # Clean off tracking params if present
                        clean_url = target_url.split("?")[0]
                        urls.append(clean_url)
    except Exception as exc:
        logger.warning(f"Wikimedia API search encountered an issue for '{monument_name}': {exc}")

    return urls


def fetch_ddg_image_urls(monument_name: str, max_candidates: int = 10) -> List[str]:
    """
    Fallback image fetcher using DuckDuckGo search.
    """
    urls = []
    try:
        from duckduckgo_search import DDGS
        query = f"{monument_name} landmark exterior day"
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=max_candidates))
            for item in results:
                url = item.get("image")
                if url and url.startswith("http"):
                    if not url.lower().endswith((".svg", ".gif", ".ico")):
                        urls.append(url)
    except Exception as exc:
        logger.warning(f"DuckDuckGo fallback search exception for '{monument_name}': {exc}")
    
    return urls


def download_and_validate_image(url: str, output_path: Path) -> bool:
    """
    Downloads image from URL, verifies integrity with PIL,
    converts to standard RGB JPEG, and persists to disk.
    """
    # Use Wikimedia User-Agent if targeting wikimedia, else standard
    headers = {
        "User-Agent": WIKIMEDIA_USER_AGENT if "wikimedia.org" in url else STANDARD_USER_AGENT,
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }
    try:
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, stream=True)
        if res.status_code != 200:
            logger.debug(f"HTTP {res.status_code} for {url}")
            return False

        content_bytes = res.content
        if len(content_bytes) < 8000:  # Skip tiny placeholder images (<8KB)
            return False

        # Phase 1: verify file integrity
        buf = io.BytesIO(content_bytes)
        with Image.open(buf) as raw_img:
            raw_img.verify()

        # Phase 2: open, verify dimensions and convert to RGB JPEG
        buf.seek(0)
        with Image.open(buf) as valid_img:
            width, height = valid_img.size
            if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                logger.debug(f"Image {url} rejected: dimensions ({width}x{height}) below {MIN_IMAGE_DIMENSION}px")
                return False
            
            rgb_image = valid_img.convert("RGB")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            rgb_image.save(output_path, "JPEG", quality=95)
            
        return True
    except Exception as exc:
        logger.debug(f"Failed to process image from {url}: {exc}")
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        return False


def seed_monument_images(monument_key: str, monument_info: Dict) -> int:
    """
    Seeds 4 valid reference images for a given monument.
    """
    monument_name = monument_info["monument_name"]
    monument_dir = DATASET_DIR / monument_key
    monument_dir.mkdir(parents=True, exist_ok=True)

    # Check existing valid images
    existing_count = 0
    for idx in range(1, TARGET_IMAGES_PER_MONUMENT + 1):
        target_file = monument_dir / f"img_{idx}.jpg"
        if target_file.exists():
            try:
                with Image.open(target_file) as check_img:
                    check_img.verify()
                existing_count += 1
            except Exception:
                target_file.unlink(missing_ok=True)

    if existing_count >= TARGET_IMAGES_PER_MONUMENT:
        logger.info(f"[{monument_name}] Already has {existing_count}/{TARGET_IMAGES_PER_MONUMENT} verified reference images.")
        return existing_count

    logger.info(f"[{monument_name}] Fetching reference images (current: {existing_count}/{TARGET_IMAGES_PER_MONUMENT})...")

    # 1. Fetch from Wikimedia Commons
    urls = fetch_wikimedia_image_urls(monument_key, monument_name, max_candidates=15)
    logger.info(f"[{monument_name}] Wikimedia returned {len(urls)} candidate URLs.")

    # 2. Supplement from DuckDuckGo if needed
    if len(urls) < TARGET_IMAGES_PER_MONUMENT:
        logger.info(f"[{monument_name}] Querying DuckDuckGo fallback...")
        ddg_urls = fetch_ddg_image_urls(monument_name, max_candidates=10)
        for u in ddg_urls:
            if u not in urls:
                urls.append(u)
        logger.info(f"[{monument_name}] Total candidate URLs: {len(urls)}")

    # 3. Download, verify and save
    current_idx = existing_count + 1
    for url in urls:
        if current_idx > TARGET_IMAGES_PER_MONUMENT:
            break
        target_path = monument_dir / f"img_{current_idx}.jpg"
        logger.info(f"[{monument_name}] Downloading img_{current_idx}.jpg...")
        success = download_and_validate_image(url, target_path)
        if success:
            logger.info(f"[{monument_name}] -> Verified & saved {target_path.name}")
            current_idx += 1
            time.sleep(0.3)  # Respectful rate limiting
        else:
            logger.debug(f"[{monument_name}] Skipped candidate URL {url}")

    final_count = sum(1 for i in range(1, TARGET_IMAGES_PER_MONUMENT + 1) if (monument_dir / f"img_{i}.jpg").exists())
    return final_count


def main():
    logger.info("=" * 65)
    logger.info("Heritage & Monument Recognition System - Dataset Seeder (Phase 1)")
    logger.info("=" * 65)

    if not METADATA_FILE.exists():
        logger.error(f"Metadata file missing at {METADATA_FILE}")
        sys.exit(1)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata: Dict = json.load(f)

    logger.info(f"Loaded metadata for {len(metadata)} monuments from {METADATA_FILE.name}")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    summary = {}
    for key, info in metadata.items():
        count = seed_monument_images(key, info)
        summary[key] = count

    logger.info("=" * 65)
    logger.info("DATASET SEEDING SUMMARY")
    logger.info("=" * 65)
    all_complete = True
    for key, count in summary.items():
        status = "PASSED" if count >= TARGET_IMAGES_PER_MONUMENT else "FAILED"
        if count < TARGET_IMAGES_PER_MONUMENT:
            all_complete = False
        logger.info(f"  - {key:<25}: {count}/{TARGET_IMAGES_PER_MONUMENT} images [{status}]")

    logger.info("=" * 65)
    if all_complete:
        logger.info("STATUS: SUCCESS - All 10 monuments seeded with 4 verified images each!")
    else:
        logger.warning("STATUS: WARNING - Some monuments require manual re-seeding.")


if __name__ == "__main__":
    main()
