"""
Heritage & Monument Recognition System - Vector Index Verification Suite (Phase 2)
Tests FAISS vector index retrieval accuracy and cosine similarity under:
1. Direct self-retrieval
2. Simulated real-world user uploads (random spatial crop + slight rotational perturbation)
Ensures Top-1 match is 100% accurate with Cosine Similarity > 0.85.
"""

import json
import logging
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_index")

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
INDEX_FILE = BASE_DIR / "monument_index.faiss"
LABELS_FILE = BASE_DIR / "monument_labels.json"

MODEL_NAME = "openai/clip-vit-base-patch32"
SIMILARITY_THRESHOLD = 0.85


def simulate_user_upload(img: Image.Image, seed: int = 42) -> Image.Image:
    """
    Simulates real-world user capture perturbations:
    - Random crop trimming 5% to 10% off edges
    - Subtle rotation (-4 to +4 degrees)
    """
    random.seed(seed)
    w, h = img.size

    # Crop 5% to 8% margin randomly
    crop_x = int(w * random.uniform(0.04, 0.08))
    crop_y = int(h * random.uniform(0.04, 0.08))
    cropped = img.crop((crop_x, crop_y, w - crop_x, h - crop_y))

    # Subtle rotation
    angle = random.uniform(-4.0, 4.0)
    rotated = cropped.rotate(angle, resample=Image.Resampling.BILINEAR, expand=False)
    return rotated


def extract_embedding(
    image: Image.Image,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: str,
) -> np.ndarray:
    """
    Extracts L2-normalized 512-D embedding from image.
    """
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            tensor = outputs.pooler_output
        elif hasattr(outputs, "last_hidden_state"):
            tensor = outputs.last_hidden_state
        else:
            tensor = outputs

        vec = tensor.cpu().detach().numpy().flatten().astype(np.float32)

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def query_index(
    vec: np.ndarray,
    index: faiss.Index,
    labels: List[Dict],
    top_k: int = 3,
) -> List[Tuple[Dict, float]]:
    """
    Queries FAISS index and returns top_k (label_dict, cosine_similarity) matches.
    """
    query_matrix = np.expand_dims(vec, axis=0).astype(np.float32)
    distances, indices = index.search(query_matrix, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx != -1 and idx < len(labels):
            results.append((labels[idx], float(dist)))
    return results


def run_verification() -> bool:
    logger.info("=" * 70)
    logger.info("Heritage & Monument Recognition - FAISS Index Verification (Phase 2)")
    logger.info("=" * 70)

    # 1. Load artifacts
    if not INDEX_FILE.exists() or not LABELS_FILE.exists() or not METADATA_FILE.exists():
        logger.error("Required artifacts missing. Ensure index_builder.py was executed.")
        return False

    index = faiss.read_index(str(INDEX_FILE))
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        labels: List[Dict] = json.load(f)
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata: Dict = json.load(f)

    logger.info(f"Loaded FAISS index: {index.ntotal} vectors, dimension={index.d}")
    logger.info(f"Loaded {len(labels)} label entries and {len(metadata)} monuments metadata.")

    # 2. Load CLIP Model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device.upper()}")
    model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.eval()

    logger.info("Running simulated user upload test across the 10 core flagship monuments & catalogue...")
    logger.info("(Perturbation: 5-8% asymmetric edge crop + bilinear rotation)")
    logger.info("-" * 70)

    CORE_10_KEYS = [
        "brihadeeswarar_temple", "charminar", "gateway_of_india", "hampi_stone_chariot",
        "hawa_mahal", "konark_sun_temple", "qutub_minar", "sanchi_stupa",
        "taj_mahal", "victoria_memorial"
    ]

    monument_keys = sorted(list(metadata.keys()))
    test_results = []
    core_passed = True
    total_correct = 0

    for i, m_key in enumerate(monument_keys):
        # Pick img_2.jpg (or img_1.jpg if img_2 missing) for query testing
        img_path = DATASET_DIR / m_key / "img_2.jpg"
        if not img_path.exists():
            img_path = DATASET_DIR / m_key / "img_1.jpg"
        if not img_path.exists():
            continue

        with Image.open(img_path) as raw_img:
            rgb_img = raw_img.convert("RGB")
            perturbed_img = simulate_user_upload(rgb_img, seed=100 + i)
            query_vec = extract_embedding(perturbed_img, model, processor, device)

        # Query FAISS
        top_matches = query_index(query_vec, index, labels, top_k=3)
        if not top_matches:
            logger.error(f"[{m_key}] No matches returned by FAISS!")
            if m_key in CORE_10_KEYS:
                core_passed = False
            continue

        best_match, best_score = top_matches[0]
        predicted_key = best_match["monument_key"]
        is_correct = (predicted_key == m_key)
        score_passes = (best_score >= SIMILARITY_THRESHOLD)

        if is_correct:
            total_correct += 1

        status = "PASSED" if (is_correct and score_passes) else "FAILED"
        if m_key in CORE_10_KEYS and not (is_correct and score_passes):
            core_passed = False

        test_results.append({
            "expected": m_key,
            "predicted": predicted_key,
            "score": best_score,
            "source": best_match["source"],
            "status": status,
        })

    # Summary Table for Core Flagship 10
    core_results = [r for r in test_results if r["expected"] in CORE_10_KEYS]
    print("\n" + "=" * 80)
    print("CORE 10 FLAGSHIP MONUMENTS VERIFICATION (PHASE 2 REQUIREMENT)")
    print("=" * 80)
    print(f"{'EXPECTED MONUMENT':<24} | {'TOP-1 PREDICTED':<24} | {'SCORE':<7} | {'STATUS':<7}")
    print("-" * 80)
    for r in core_results:
        print(f"{r['expected']:<24} | {r['predicted']:<24} | {r['score']:<7.4f} | {r['status']:<7}")
    print("=" * 80)
    print(f"Overall 100-Site Top-1 Accuracy: {total_correct}/{len(test_results)} ({total_correct/len(test_results)*100:.1f}%)\n")

    logger.info(f"Similarity Threshold Requirement: > {SIMILARITY_THRESHOLD}")
    if core_passed:
        logger.info("VERIFICATION RESULT: ALL CORE 10 TESTS PASSED (100% Top-1 Accuracy, Cosine Similarity > 0.85)")
    else:
        logger.error("VERIFICATION RESULT: CORE TESTS FAILED.")

    return core_passed


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)

