"""
Heritage & Monument Recognition System - Vector Index Builder (Phase 2)
Extracts 512-dimensional CLIP embeddings using openai/clip-vit-base-patch32,
L2-normalizes them for Cosine Similarity search via FAISS IndexFlatIP,
computes normalized monument centroids for robust anchor matching,
and exports monument_index.faiss & monument_labels.json.
"""

import json
import logging
import os
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
logger = logging.getLogger("index_builder")

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
INDEX_OUTPUT_PATH = BASE_DIR / "monument_index.faiss"
LABELS_OUTPUT_PATH = BASE_DIR / "monument_labels.json"

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDING_DIM = 512


def extract_clip_embedding(
    image: Image.Image,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: str,
) -> np.ndarray:
    """
    Extracts and L2-normalizes a 512-D visual feature embedding from an image.
    """
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        # Handle transformers version output types (BaseModelOutputWithPooling vs Tensor)
        if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            tensor = outputs.pooler_output
        elif hasattr(outputs, "last_hidden_state"):
            tensor = outputs.last_hidden_state
        else:
            tensor = outputs

        vec = tensor.cpu().detach().numpy().flatten().astype(np.float32)

    # L2 Normalization ensures Inner Product (IP) = Cosine Similarity
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def build_index() -> Tuple[int, int]:
    logger.info("=" * 65)
    logger.info("Heritage & Monument Recognition - Vector Index Builder (Phase 2)")
    logger.info("=" * 65)

    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Metadata file not found at {METADATA_FILE}")
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found at {DATASET_DIR}")

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata: Dict = json.load(f)

    # Device selection
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device.upper()}")

    logger.info(f"Loading CLIP model and processor: {MODEL_NAME}...")
    model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.eval()

    all_vectors: List[np.ndarray] = []
    labels_records: List[Dict] = []

    monument_keys = sorted(list(metadata.keys()))
    logger.info(f"Processing {len(monument_keys)} monuments in alphabetical order...")

    total_images_processed = 0

    for monument_key in monument_keys:
        monument_dir = DATASET_DIR / monument_key
        if not monument_dir.is_dir():
            logger.warning(f"Directory {monument_dir} not found. Skipping.")
            continue

        # Look for img_1.jpg through img_4.jpg (or any valid jpg files)
        image_files = sorted(
            [f for f in monument_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
        )
        if not image_files:
            logger.warning(f"No image files found in {monument_dir}")
            continue

        monument_vectors: List[np.ndarray] = []

        logger.info(f"[{monument_key}] Extracting features for {len(image_files)} images...")
        for img_path in image_files:
            try:
                with Image.open(img_path) as img:
                    rgb_img = img.convert("RGB")
                    vec = extract_clip_embedding(rgb_img, model, processor, device)
                    monument_vectors.append(vec)

                    current_idx = len(all_vectors)
                    all_vectors.append(vec)

                    rel_source = f"{monument_key}/{img_path.name}"
                    labels_records.append({
                        "index_id": current_idx,
                        "monument_key": monument_key,
                        "monument_name": metadata[monument_key]["monument_name"],
                        "source": rel_source,
                        "is_centroid": False,
                    })
                    total_images_processed += 1
            except Exception as exc:
                logger.error(f"Error processing {img_path}: {exc}")

        # Compute centroid embedding: mean of all monument vectors, re-normalized to unit length
        if monument_vectors:
            centroid_vec = np.mean(monument_vectors, axis=0)
            centroid_norm = np.linalg.norm(centroid_vec)
            if centroid_norm > 0:
                centroid_vec = (centroid_vec / centroid_norm).astype(np.float32)

            centroid_idx = len(all_vectors)
            all_vectors.append(centroid_vec)

            labels_records.append({
                "index_id": centroid_idx,
                "monument_key": monument_key,
                "monument_name": metadata[monument_key]["monument_name"],
                "source": f"{monument_key}/centroid",
                "is_centroid": True,
            })
            logger.info(f"[{monument_key}] -> Added 4 image vectors + 1 normalized centroid anchor.")

    vectors_matrix = np.vstack(all_vectors).astype(np.float32)
    num_vectors, dim = vectors_matrix.shape
    logger.info(f"Assembled matrix shape: {vectors_matrix.shape} (Count: {num_vectors}, Dim: {dim})")

    # Build FAISS IndexFlatIP (Inner Product = Cosine Similarity with unit vectors)
    logger.info(f"Building FAISS IndexFlatIP({dim})...")
    index = faiss.IndexFlatIP(dim)
    index.add(vectors_matrix)

    # Save index to disk
    faiss.write_index(index, str(INDEX_OUTPUT_PATH))
    index_size_kb = INDEX_OUTPUT_PATH.stat().st_size / 1024
    logger.info(f"Wrote FAISS index to {INDEX_OUTPUT_PATH} ({index_size_kb:.2f} KB)")

    # Save labels mapping
    with open(LABELS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(labels_records, f, indent=2)
    logger.info(f"Wrote {len(labels_records)} label records to {LABELS_OUTPUT_PATH}")

    logger.info("=" * 65)
    logger.info("INDEX BUILDING COMPLETE")
    logger.info(f"  - Total monuments indexed: {len(monument_keys)}")
    logger.info(f"  - Total reference images  : {total_images_processed}")
    logger.info(f"  - Total centroids         : {len(monument_keys)}")
    logger.info(f"  - Total index vectors     : {index.ntotal}")
    logger.info(f"  - Vector dimension        : {dim}")
    logger.info("=" * 65)

    return index.ntotal, dim


if __name__ == "__main__":
    build_index()

