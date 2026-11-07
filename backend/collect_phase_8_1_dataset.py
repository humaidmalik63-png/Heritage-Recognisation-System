"""
Phase 8.1: Large-Scale Independent Dataset Collection & Integrity Pipeline
Project No. 30: Visual Heritage Recognition Platform (SIH 2025 - SIH25052)

Curates an authentic, independently sourced photographic dataset from Wikimedia Commons
with strict source-grouped splitting into:
1. Development Dataset (for calibration fitting & threshold optimization)
2. Final Independent Test Dataset v2 (for unbiased validation)

Guarantees:
- 0 SHA-256 collisions with Reference Gallery (200 images)
- 0 SHA-256 collisions with Holdout v1 (20 images)
- 0 SHA-256 collisions with Local Feature Eval (24 images)
- 0 SHA-256 collisions between Dev and Test v2
- Full provenance, attribution, CC license, and perceptual hash (dHash) logging
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("collect_phase_8_1")

BASE_DIR = Path(__file__).resolve().parent
DEV_DIR = BASE_DIR / "datasets" / "calibration_development"
TEST_V2_DIR = BASE_DIR / "datasets" / "independent_eval_v2"
REF_DIR = BASE_DIR / "datasets" / "reference_gallery_v2"
HOLDOUT_V1_DIR = BASE_DIR / "datasets" / "independent_eval"
LOCAL_FEAT_DIR = BASE_DIR / "datasets" / "local_feature_eval"

DEV_MANIFEST = BASE_DIR / "datasets" / "development_manifest.json"
TEST_V2_MANIFEST = BASE_DIR / "datasets" / "independent_eval_v2_manifest.json"
INTEGRITY_REPORT = BASE_DIR / "datasets" / "dataset_integrity_report.json"

USER_AGENT = "HeritageArchivalBot/3.0 (SIH25052; CalibrationResearch; mailto:heritage-research@sih.gov)"


def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
    """Computes difference hash (dHash) for perceptual similarity comparison."""
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(resized, dtype=np.float32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    decimal_val = 0
    for idx, val in enumerate(diff.flatten()):
        if val:
            decimal_val |= 1 << idx
    return f"{decimal_val:016x}"


# Load existing reference and holdout hashes to enforce zero leakage
def load_exclusion_hashes() -> Tuple[Set[str], Set[str]]:
    sha_exclusions = set()
    dhash_exclusions = set()

    for p in list(REF_DIR.rglob("*.jpg")) + list(HOLDOUT_V1_DIR.rglob("*.jpg")) + list(LOCAL_FEAT_DIR.rglob("*.jpg")):
        try:
            raw = p.read_bytes()
            sha_exclusions.add(hashlib.sha256(raw).hexdigest())
            with Image.open(p) as im:
                dhash_exclusions.add(compute_dhash(im))
        except Exception:
            pass

    return sha_exclusions, dhash_exclusions


# Diverse search queries across 10 catalog monuments, out-of-catalog monuments, and non-monuments
CURATION_QUERIES = [
    # 1. Taj Mahal
    {"monument_key": "taj_mahal", "monument_name": "Taj Mahal", "query": "Taj Mahal Agra facade daylight", "view": "front_view"},
    {"monument_key": "taj_mahal", "monument_name": "Taj Mahal", "query": "Taj Mahal Yamuna river perspective", "view": "rear_view"},
    {"monument_key": "taj_mahal", "monument_name": "Taj Mahal", "query": "Taj Mahal arch detail calligraphy", "view": "architectural_detail"},
    {"monument_key": "taj_mahal", "monument_name": "Taj Mahal", "query": "Taj Mahal garden fountain view", "view": "distant_view"},
    {"monument_key": "taj_mahal", "monument_name": "Taj Mahal", "query": "Taj Mahal marble minaret dome", "view": "side_view"},
    {"monument_key": "taj_mahal", "monument_name": "Taj Mahal", "query": "Taj Mahal twilight dusk reflection", "view": "twilight_view"},

    # 2. Qutub Minar
    {"monument_key": "qutub_minar", "monument_name": "Qutub Minar", "query": "Qutb Minar tower Delhi daylight", "view": "full_structure"},
    {"monument_key": "qutub_minar", "monument_name": "Qutub Minar", "query": "Qutub Minar balcony carving sandstone", "view": "architectural_detail"},
    {"monument_key": "qutub_minar", "monument_name": "Qutub Minar", "query": "Qutb Minar angle upward perspective", "view": "angle_view"},
    {"monument_key": "qutub_minar", "monument_name": "Qutub Minar", "query": "Qutub Minar complex courtyard arches", "view": "partial_structure"},
    {"monument_key": "qutub_minar", "monument_name": "Qutub Minar", "query": "Qutb Minar fluted balcony brackets", "view": "architectural_detail"},
    {"monument_key": "qutub_minar", "monument_name": "Qutub Minar", "query": "Qutb Minar distant trees park", "view": "distant_view"},

    # 3. Hawa Mahal
    {"monument_key": "hawa_mahal", "monument_name": "Hawa Mahal", "query": "Hawa Mahal Jaipur street facade", "view": "front_view"},
    {"monument_key": "hawa_mahal", "monument_name": "Hawa Mahal", "query": "Hawa Mahal jharokha window lattice", "view": "architectural_detail"},
    {"monument_key": "hawa_mahal", "monument_name": "Hawa Mahal", "query": "Hawa Mahal side angle street", "view": "side_view"},
    {"monument_key": "hawa_mahal", "monument_name": "Hawa Mahal", "query": "Hawa Mahal inner courtyard view", "view": "partial_structure"},
    {"monument_key": "hawa_mahal", "monument_name": "Hawa Mahal", "query": "Hawa Mahal dome finial roof detail", "view": "architectural_detail"},
    {"monument_key": "hawa_mahal", "monument_name": "Hawa Mahal", "query": "Hawa Mahal morning sunshine pink", "view": "front_view"},

    # 4. Konark Sun Temple
    {"monument_key": "konark_sun_temple", "monument_name": "Konark Sun Temple", "query": "Konark Sun Temple Jagamohana stone", "view": "full_structure"},
    {"monument_key": "konark_sun_temple", "monument_name": "Konark Sun Temple", "query": "Konark Sun Temple wheel stone carving", "view": "close_up_carving"},
    {"monument_key": "konark_sun_temple", "monument_name": "Konark Sun Temple", "query": "Konark Sun Temple horse sculpture platform", "view": "architectural_detail"},
    {"monument_key": "konark_sun_temple", "monument_name": "Konark Sun Temple", "query": "Konark temple ruins landscape perspective", "view": "distant_view"},
    {"monument_key": "konark_sun_temple", "monument_name": "Konark Sun Temple", "query": "Konark dancers sculpture relief", "view": "architectural_detail"},
    {"monument_key": "konark_sun_temple", "monument_name": "Konark Sun Temple", "query": "Konark Sun temple plinth frieze", "view": "architectural_detail"},

    # 5. Gateway of India
    {"monument_key": "gateway_of_india", "monument_name": "Gateway of India", "query": "Gateway of India Mumbai sea harbor", "view": "front_view"},
    {"monument_key": "gateway_of_india", "monument_name": "Gateway of India", "query": "Gateway of India archway basalt stone", "view": "architectural_detail"},
    {"monument_key": "gateway_of_india", "monument_name": "Gateway of India", "query": "Gateway of India angle harbor boats", "view": "side_view"},
    {"monument_key": "gateway_of_india", "monument_name": "Gateway of India", "query": "Gateway of India promenade wide perspective", "view": "distant_view"},
    {"monument_key": "gateway_of_india", "monument_name": "Gateway of India", "query": "Gateway of India dome turret detail", "view": "architectural_detail"},
    {"monument_key": "gateway_of_india", "monument_name": "Gateway of India", "query": "Gateway of India evening lights Mumbai", "view": "twilight_view"},

    # 6. Charminar
    {"monument_key": "charminar", "monument_name": "Charminar", "query": "Charminar Hyderabad facade daylight", "view": "front_view"},
    {"monument_key": "charminar", "monument_name": "Charminar", "query": "Charminar minaret balcony stucco detail", "view": "architectural_detail"},
    {"monument_key": "charminar", "monument_name": "Charminar", "query": "Charminar market street angle", "view": "side_view"},
    {"monument_key": "charminar", "monument_name": "Charminar", "query": "Charminar arch perspective traffic", "view": "partial_structure"},
    {"monument_key": "charminar", "monument_name": "Charminar", "query": "Charminar clock face arcade dome", "view": "architectural_detail"},
    {"monument_key": "charminar", "monument_name": "Charminar", "query": "Charminar illuminated night Hyderabad", "view": "night_view"},

    # 7. Hampi Stone Chariot
    {"monument_key": "hampi_stone_chariot", "monument_name": "Hampi Stone Chariot", "query": "Hampi stone chariot Vittala temple daylight", "view": "full_structure"},
    {"monument_key": "hampi_stone_chariot", "monument_name": "Hampi Stone Chariot", "query": "Hampi chariot stone wheel carving detail", "view": "close_up_carving"},
    {"monument_key": "hampi_stone_chariot", "monument_name": "Hampi Stone Chariot", "query": "Vittala temple stone chariot side perspective", "view": "side_view"},
    {"monument_key": "hampi_stone_chariot", "monument_name": "Hampi Stone Chariot", "query": "Hampi chariot elephant sculpture front", "view": "architectural_detail"},
    {"monument_key": "hampi_stone_chariot", "monument_name": "Hampi Stone Chariot", "query": "Hampi Vittala complex courtyard chariot", "view": "distant_view"},
    {"monument_key": "hampi_stone_chariot", "monument_name": "Hampi Stone Chariot", "query": "Hampi stone chariot tower superstructure", "view": "architectural_detail"},

    # 8. Sanchi Stupa
    {"monument_key": "sanchi_stupa", "monument_name": "Sanchi Stupa", "query": "Sanchi Great Stupa dome torana daylight", "view": "full_structure"},
    {"monument_key": "sanchi_stupa", "monument_name": "Sanchi Stupa", "query": "Sanchi Stupa torana gateway relief carving", "view": "close_up_carving"},
    {"monument_key": "sanchi_stupa", "monument_name": "Sanchi Stupa", "query": "Sanchi Stupa side circular railing", "view": "side_view"},
    {"monument_key": "sanchi_stupa", "monument_name": "Sanchi Stupa", "query": "Sanchi Stupa hill landscape distant view", "view": "distant_view"},
    {"monument_key": "sanchi_stupa", "monument_name": "Sanchi Stupa", "query": "Sanchi Stupa south gateway pillar lions", "view": "architectural_detail"},
    {"monument_key": "sanchi_stupa", "monument_name": "Sanchi Stupa", "query": "Sanchi Buddhist sanctuary stupa stairs", "view": "partial_structure"},

    # 9. Victoria Memorial
    {"monument_key": "victoria_memorial", "monument_name": "Victoria Memorial", "query": "Victoria Memorial Kolkata marble facade lake", "view": "front_view"},
    {"monument_key": "victoria_memorial", "monument_name": "Victoria Memorial", "query": "Victoria Memorial dome bronze angel", "view": "architectural_detail"},
    {"monument_key": "victoria_memorial", "monument_name": "Victoria Memorial", "query": "Victoria Memorial colonnade garden side", "view": "side_view"},
    {"monument_key": "victoria_memorial", "monument_name": "Victoria Memorial", "query": "Victoria Memorial reflective pool distant", "view": "distant_view"},
    {"monument_key": "victoria_memorial", "monument_name": "Victoria Memorial", "query": "Victoria Memorial portico lions statue", "view": "architectural_detail"},
    {"monument_key": "victoria_memorial", "monument_name": "Victoria Memorial", "query": "Victoria Memorial night lighting Kolkata", "view": "night_view"},

    # 10. Brihadeeswarar Temple
    {"monument_key": "brihadeeswarar_temple", "monument_name": "Brihadeeswarar Temple", "query": "Brihadisvara Temple Thanjavur vimana daylight", "view": "full_structure"},
    {"monument_key": "brihadeeswarar_temple", "monument_name": "Brihadeeswarar Temple", "query": "Brihadeeswarar Temple gopuram stone sculptures", "view": "architectural_detail"},
    {"monument_key": "brihadeeswarar_temple", "monument_name": "Brihadeeswarar Temple", "query": "Brihadisvara Temple courtyard side angle", "view": "side_view"},
    {"monument_key": "brihadeeswarar_temple", "monument_name": "Brihadeeswarar Temple", "query": "Brihadeeswarar Nandi mandapam stone bull", "view": "architectural_detail"},
    {"monument_key": "brihadeeswarar_temple", "monument_name": "Brihadeeswarar Temple", "query": "Thanjavur Big Temple vimana apex kumbam", "view": "architectural_detail"},
    {"monument_key": "brihadeeswarar_temple", "monument_name": "Brihadeeswarar Temple", "query": "Brihadeeswarar Temple distant entrance walkway", "view": "distant_view"},

    # 11. Unknown Heritage Specimens (Out-of-catalog Indian Monuments)
    {"monument_key": "unknown_heritage", "monument_name": "Red Fort Delhi", "query": "Red Fort Delhi Lahori Gate facade", "view": "out_of_catalog_heritage"},
    {"monument_key": "unknown_heritage", "monument_name": "Meenakshi Temple", "query": "Meenakshi Temple Madurai gopuram colorful", "view": "out_of_catalog_heritage"},
    {"monument_key": "unknown_heritage", "monument_name": "Ellora Caves Kailasa", "query": "Ellora Caves Kailasa rock cut temple", "view": "out_of_catalog_heritage"},
    {"monument_key": "unknown_heritage", "monument_name": "Ajanta Caves", "query": "Ajanta Caves cliff entrance facade", "view": "out_of_catalog_heritage"},
    {"monument_key": "unknown_heritage", "monument_name": "Gol Gumbaz", "query": "Gol Gumbaz Bijapur dome exterior", "view": "out_of_catalog_heritage"},
    {"monument_key": "unknown_heritage", "monument_name": "Shore Temple Mahabalipuram", "query": "Shore Temple Mahabalipuram granite", "view": "out_of_catalog_heritage"},
    {"monument_key": "unknown_heritage", "monument_name": "Humayuns Tomb", "query": "Humayuns Tomb Delhi garden tomb", "view": "out_of_catalog_heritage"},
    {"monument_key": "unknown_heritage", "monument_name": "Fatehpur Sikri", "query": "Fatehpur Sikri Buland Darwaza gate", "view": "out_of_catalog_heritage"},

    # 12. Non-Monument Distractors (Rejection Testing)
    {"monument_key": "non_monument", "monument_name": "Modern Glass Skyscraper", "query": "modern glass office skyscraper building facade", "view": "non_monument_distractor"},
    {"monument_key": "non_monument", "monument_name": "Highway Road Traffic", "query": "highway expressway asphalt road cars", "view": "non_monument_distractor"},
    {"monument_key": "non_monument", "monument_name": "Natural Mountain Forest", "query": "mountain peak green pine forest landscape", "view": "non_monument_distractor"},
    {"monument_key": "non_monument", "monument_name": "Indoor Living Room", "query": "modern domestic living room couch interior", "view": "non_monument_distractor"},
    {"monument_key": "non_monument", "monument_name": "Traditional Indian Cuisine", "query": "indian food curry thali brass plate", "view": "non_monument_distractor"},
    {"monument_key": "non_monument", "monument_name": "Bengal Tiger Wildlife", "query": "bengal tiger wild forest india", "view": "non_monument_distractor"},
    {"monument_key": "non_monument", "monument_name": "Crowded City Market", "query": "crowded shopping bazaar vegetable market india", "view": "non_monument_distractor"},
    {"monument_key": "non_monument", "monument_name": "Modern Electric Train", "query": "electric passenger locomotive train railway", "view": "non_monument_distractor"},
]


def search_wikimedia_commons(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Searches Wikimedia Commons API politely with exponential backoff on 429."""
    base_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrlimit": limit,
        "gsrnamespace": "6",
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": "1280",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            results = []
            for _, pdata in pages.items():
                if "imageinfo" in pdata and len(pdata["imageinfo"]) > 0:
                    info = pdata["imageinfo"][0]
                    thumb_url = info.get("thumburl", info.get("url"))
                    meta = info.get("extmetadata", {})
                    author = meta.get("Artist", {}).get("value", "Wikimedia Contributor")
                    clean_author = re.sub(r"<[^>]+>", "", author).strip()[:50] or "Wikimedia Contributor"
                    license_name = meta.get("LicenseShortName", {}).get("value", "CC BY-SA")
                    results.append({
                        "title": pdata.get("title", ""),
                        "thumb_url": thumb_url,
                        "full_url": info.get("url", thumb_url),
                        "author": clean_author,
                        "license": license_name,
                        "width": info.get("thumbwidth", info.get("width", 800)),
                        "height": info.get("thumbheight", info.get("height", 600)),
                    })
            return results
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_sec = 2.0 * (attempt + 1)
                time.sleep(wait_sec)
            else:
                return []
        except Exception:
            return []
    return []


def download_and_verify_image(url: str, dest_path: Path) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Downloads image, verifies PIL validity, and computes SHA-256 and dHash."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw_bytes = resp.read()

            if len(raw_bytes) < 3000:
                return False, None, None, None

            dest_path.write_bytes(raw_bytes)

            with Image.open(dest_path) as im:
                im.verify()

            with Image.open(dest_path) as im:
                im_rgb = im.convert("RGB")
                w, h = im_rgb.size
                dhash_val = compute_dhash(im_rgb)

            sha256_val = hashlib.sha256(raw_bytes).hexdigest()
            return True, sha256_val, dhash_val, f"{w}x{h}"
        except Exception:
            time.sleep(1.0)
    return False, None, None, None


def execute_curation():
    DEV_DIR.mkdir(parents=True, exist_ok=True)
    TEST_V2_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Step 1: Loading existing reference and holdout hashes...")
    sha_exclusions, dhash_exclusions = load_exclusion_hashes()
    logger.info(f"Loaded {len(sha_exclusions)} reference/holdout SHA-256 hashes to prevent data leakage.")

    downloaded_records: List[Dict[str, Any]] = []
    seen_shas = set(sha_exclusions)
    seen_titles = set()

    logger.info(f"Step 2: Harvesting authentic photographs across {len(CURATION_QUERIES)} target queries...")
    temp_pool_dir = BASE_DIR / "datasets" / "_temp_pool"
    temp_pool_dir.mkdir(parents=True, exist_ok=True)

    specimen_counter = 0

    for q_idx, q_item in enumerate(CURATION_QUERIES, 1):
        m_key = q_item["monument_key"]
        m_name = q_item["monument_name"]
        query_text = q_item["query"]
        view_type = q_item["view"]

        logger.info(f"[{q_idx}/{len(CURATION_QUERIES)}] Querying: '{query_text}'...")
        hits = search_wikimedia_commons(query_text, limit=4)
        time.sleep(0.5)

        for hit in hits:
            title = hit["title"]
            if title in seen_titles:
                continue
            seen_titles.add(title)

            thumb_url = hit["thumb_url"]
            if not thumb_url:
                continue

            specimen_counter += 1
            temp_filename = f"specimen_{specimen_counter:04d}.jpg"
            temp_path = temp_pool_dir / temp_filename

            valid, sha256_val, dhash_val, dims = download_and_verify_image(thumb_url, temp_path)
            if not valid or not sha256_val:
                continue

            if sha256_val in seen_shas:
                logger.debug(f"  [Leakage Intercepted] Image already in reference/holdout: {title}")
                temp_path.unlink(missing_ok=True)
                continue

            seen_shas.add(sha256_val)

            downloaded_records.append({
                "raw_file": temp_filename,
                "temp_path": str(temp_path),
                "monument_key": m_key,
                "monument_name": m_name,
                "query": query_text,
                "view_type": view_type,
                "source_title": title,
                "source_url": hit["full_url"],
                "author": hit["author"],
                "license": hit["license"],
                "sha256": sha256_val,
                "dhash": dhash_val,
                "dimensions": dims,
            })

    logger.info(f"Successfully harvested and verified {len(downloaded_records)} distinct authentic images.")

    # Step 3: Source-Grouped Splitting (Group by author / source sequence to prevent same-session leakage)
    # 60% Development, 40% Independent Test v2
    author_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in downloaded_records:
        key = f"{r['monument_key']}___{r['author']}"
        author_groups.setdefault(key, []).append(r)

    dev_records: List[Dict[str, Any]] = []
    test_v2_records: List[Dict[str, Any]] = []

    dev_counts: Dict[str, int] = {}
    test_counts: Dict[str, int] = {}

    # Deterministic pseudo-random split using sorted group keys and hash
    for grp_key, grp_items in sorted(author_groups.items()):
        grp_hash = int(hashlib.md5(grp_key.encode("utf-8")).hexdigest()[:4], 16)
        m_k = grp_items[0]["monument_key"]

        # Assign to dev or test aiming for 60/40 ratio per monument
        d_cnt = dev_counts.get(m_k, 0)
        t_cnt = test_counts.get(m_k, 0)

        assign_to_test = False
        if (d_cnt + t_cnt) > 0 and (t_cnt / (d_cnt + t_cnt)) < 0.38:
            assign_to_test = True
        elif grp_hash % 10 < 4:
            assign_to_test = True

        if assign_to_test:
            for item in grp_items:
                test_v2_records.append(item)
                test_counts[m_k] = test_counts.get(m_k, 0) + 1
        else:
            for item in grp_items:
                dev_records.append(item)
                dev_counts[m_k] = dev_counts.get(m_k, 0) + 1

    logger.info(f"Split results: Development = {len(dev_records)} images, Independent Test v2 = {len(test_v2_records)} images.")

    # Move files and finalize manifests
    final_dev_manifest: List[Dict[str, Any]] = []
    for idx, item in enumerate(dev_records, 1):
        m_k = item["monument_key"]
        dest_filename = f"dev_{m_k}_{idx:03d}.jpg"
        dest_path = DEV_DIR / dest_filename
        Path(item["temp_path"]).replace(dest_path)

        final_dev_manifest.append({
            "specimen_id": f"dev_{m_k}_{idx:03d}",
            "monument_key": m_k,
            "monument_name": item["monument_name"],
            "ground_truth_label": m_k,
            "filename": dest_filename,
            "relative_path": f"datasets/calibration_development/{dest_filename}",
            "view_type": item["view_type"],
            "source_url": item["source_url"],
            "author": item["author"],
            "license": item["license"],
            "sha256": item["sha256"],
            "perceptual_hash_dhash": item["dhash"],
            "dimensions": item["dimensions"],
            "split": "calibration_development",
        })

    final_test_manifest: List[Dict[str, Any]] = []
    for idx, item in enumerate(test_v2_records, 1):
        m_k = item["monument_key"]
        dest_filename = f"test2_{m_k}_{idx:03d}.jpg"
        dest_path = TEST_V2_DIR / dest_filename
        Path(item["temp_path"]).replace(dest_path)

        final_test_manifest.append({
            "specimen_id": f"test2_{m_k}_{idx:03d}",
            "monument_key": m_k,
            "monument_name": item["monument_name"],
            "ground_truth_label": m_k,
            "filename": dest_filename,
            "relative_path": f"datasets/independent_eval_v2/{dest_filename}",
            "view_type": item["view_type"],
            "source_url": item["source_url"],
            "author": item["author"],
            "license": item["license"],
            "sha256": item["sha256"],
            "perceptual_hash_dhash": item["dhash"],
            "dimensions": item["dimensions"],
            "split": "independent_eval_v2",
        })

    # Clean up temp pool
    temp_pool_dir.rmdir()

    # Save manifests
    with open(DEV_MANIFEST, "w", encoding="utf-8") as f:
        json.dump({
            "dataset_name": "Phase 8.1 Calibration Development Dataset",
            "version": "1.0.0",
            "description": "Independently collected authentic specimens for confidence calibration and threshold optimization.",
            "total_specimens": len(final_dev_manifest),
            "counts_per_class": dev_counts,
            "records": final_dev_manifest,
        }, f, indent=2)

    with open(TEST_V2_MANIFEST, "w", encoding="utf-8") as f:
        json.dump({
            "dataset_name": "Phase 8.1 Independent Evaluation Dataset v2",
            "version": "2.0.0",
            "description": "Unbiased held-out test dataset strictly isolated from calibration model training and threshold tuning.",
            "total_specimens": len(final_test_manifest),
            "counts_per_class": test_counts,
            "records": final_test_manifest,
        }, f, indent=2)

    # Cross-verify zero leakage
    dev_shas = {x["sha256"] for x in final_dev_manifest}
    test_shas = {x["sha256"] for x in final_test_manifest}
    leakage_dev_ref = dev_shas.intersection(sha_exclusions)
    leakage_test_ref = test_shas.intersection(sha_exclusions)
    leakage_dev_test = dev_shas.intersection(test_shas)

    integrity_report_data = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_harvested_authentic": len(downloaded_records),
        "development_specimens": len(final_dev_manifest),
        "independent_test_v2_specimens": len(final_test_manifest),
        "reference_gallery_specimens": 200,
        "holdout_v1_specimens": 20,
        "leakage_checks": {
            "dev_vs_reference_gallery_collisions": len(leakage_dev_ref),
            "test_v2_vs_reference_gallery_collisions": len(leakage_test_ref),
            "dev_vs_test_v2_collisions": len(leakage_dev_test),
            "zero_leakage_verified": len(leakage_dev_ref) == 0 and len(leakage_test_ref) == 0 and len(leakage_dev_test) == 0,
        },
        "monument_distribution": {
            "development": dev_counts,
            "independent_test_v2": test_counts,
        },
    }

    with open(INTEGRITY_REPORT, "w", encoding="utf-8") as f:
        json.dump(integrity_report_data, f, indent=2)

    logger.info("Step 4: Dataset Integrity Report successfully written.")
    logger.info(f"Dev/Ref Collisions: {len(leakage_dev_ref)}, Test/Ref Collisions: {len(leakage_test_ref)}, Dev/Test Collisions: {len(leakage_dev_test)}")
    logger.info(f"Zero leakage status: {integrity_report_data['leakage_checks']['zero_leakage_verified']}")


if __name__ == "__main__":
    execute_curation()
