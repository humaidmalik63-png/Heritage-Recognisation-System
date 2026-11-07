"""
Phase 8.0A: Vector Index Rebuild & Multi-View Alignment Engine
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform
SIH 2025 (SIH25052)

Extracts 512-dimensional CLIP embeddings using openai/clip-vit-base-patch32
across the 200 verified reference photographs in `backend/datasets/reference_gallery_v2/`,
normalizes embeddings, computes structural-view-anchored normalized centroids,
and exports:
  - `backend/monument_index.faiss` (active index)
  - `backend/monument_labels.json` (active labels)
  - `backend/datasets/monument_index_v2.faiss` (versioned backup)
  - `backend/datasets/monument_labels_v2.json` (versioned backup)
Also synchronizes reference images to `backend/dataset/` to guarantee client thumbnail previews.
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# Ensure backend directory is in path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# UTF-8 stdout configuration for Windows cp1252 compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rebuild_faiss_v2")

GALLERY_DIR = BASE_DIR / "datasets" / "reference_gallery_v2"
MANIFEST_FILE = BASE_DIR / "reference_gallery_manifest.json"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"
ACTIVE_INDEX_PATH = BASE_DIR / "monument_index.faiss"
ACTIVE_LABELS_PATH = BASE_DIR / "monument_labels.json"
V2_INDEX_PATH = BASE_DIR / "datasets" / "monument_index_v2.faiss"
V2_LABELS_PATH = BASE_DIR / "datasets" / "monument_labels_v2.json"
PREVIEW_DATASET_DIR = BASE_DIR / "dataset"

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDING_DIM = 512


def extract_clip_embedding(
    image: Image.Image,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: str,
) -> np.ndarray:
    """Extracts and L2-normalizes a 512-D visual feature embedding from an image."""
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


def rebuild_index_v2() -> Tuple[int, int, int]:
    logger.info("=" * 80)
    logger.info("REBUILDING FAISS INDEX WITH MULTI-VIEW REFERENCE GALLERY (v2.0)")
    logger.info("=" * 80)

    if not GALLERY_DIR.exists():
        raise FileNotFoundError(f"Reference gallery directory not found: {GALLERY_DIR}")
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(f"Gallery manifest not found: {MANIFEST_FILE}")
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Metadata file not found: {METADATA_FILE}")

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        manifest_records = {r["image_id"]: r for r in manifest_data["records"]}

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Target compute device: {device.upper()}")
    logger.info(f"Loading CLIP model and processor: {MODEL_NAME}...")

    model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.eval()

    all_vectors: List[np.ndarray] = []
    labels_records: List[Dict[str, Any]] = []

    monument_keys = sorted(list(metadata.keys()))
    logger.info(f"Processing {len(monument_keys)} monuments...")

    total_images_indexed = 0
    total_centroids_indexed = 0

    for monument_key in monument_keys:
        mon_dir = GALLERY_DIR / monument_key
        if not mon_dir.is_dir():
            logger.warning(f"Monument directory {mon_dir} not found. Skipping.")
            continue

        image_files = sorted(list(mon_dir.glob("*.jpg")) + list(mon_dir.glob("*.jpeg")) + list(mon_dir.glob("*.png")))
        if not image_files:
            logger.warning(f"No image files in {mon_dir}. Skipping.")
            continue

        logger.info(f"[{monument_key}] Embedding {len(image_files)} reference photographs...")

        monument_structural_vectors: List[np.ndarray] = []
        monument_all_vectors: List[np.ndarray] = []

        for img_path in image_files:
            try:
                with Image.open(img_path) as img:
                    rgb_img = img.convert("RGB")
                    vec = extract_clip_embedding(rgb_img, model, processor, device)

                monument_all_vectors.append(vec)
                current_idx = len(all_vectors)
                all_vectors.append(vec)

                # Match metadata from manifest
                fname = img_path.name
                img_num = fname.replace("ref_", "").split(".")[0]
                img_id = f"ref_{monument_key}_{img_num}"
                m_rec = manifest_records.get(img_id, {})

                view_type = m_rec.get("view_type", "full_structure")
                is_structural = m_rec.get("is_structural_view", True)
                lighting = m_rec.get("lighting_condition", "daylight")

                if is_structural:
                    monument_structural_vectors.append(vec)

                labels_records.append({
                    "index_id": current_idx,
                    "monument_key": monument_key,
                    "monument_name": metadata[monument_key]["monument_name"],
                    "source": f"{monument_key}/{fname}",
                    "file_path": f"datasets/reference_gallery_v2/{monument_key}/{fname}",
                    "is_centroid": False,
                    "view_type": view_type,
                    "is_structural_view": is_structural,
                    "lighting_condition": lighting,
                    "image_id": img_id,
                })
                total_images_indexed += 1

                # Sync preview file to backend/dataset/<monument>/ for client preview
                dest_preview = PREVIEW_DATASET_DIR / monument_key / fname
                dest_preview.parent.mkdir(parents=True, exist_ok=True)
                if not dest_preview.exists():
                    shutil.copy2(img_path, dest_preview)

            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")

        # Compute centroid anchor using structural/contextual views to prevent detail skew
        vectors_for_centroid = monument_structural_vectors if monument_structural_vectors else monument_all_vectors
        if vectors_for_centroid:
            centroid_vec = np.mean(vectors_for_centroid, axis=0)
            c_norm = np.linalg.norm(centroid_vec)
            if c_norm > 0:
                centroid_vec = (centroid_vec / c_norm).astype(np.float32)

            centroid_idx = len(all_vectors)
            all_vectors.append(centroid_vec)

            labels_records.append({
                "index_id": centroid_idx,
                "monument_key": monument_key,
                "monument_name": metadata[monument_key]["monument_name"],
                "source": f"{monument_key}/centroid",
                "file_path": f"datasets/reference_gallery_v2/{monument_key}/centroid",
                "is_centroid": True,
                "view_type": "centroid_anchor",
                "is_structural_view": True,
                "lighting_condition": "normalized_aggregate",
                "image_id": f"centroid_{monument_key}",
            })
            total_centroids_indexed += 1
            logger.info(f"[{monument_key}] -> Added {len(image_files)} image vectors + 1 structural centroid anchor.")

    # Assemble and build FAISS index
    vectors_matrix = np.vstack(all_vectors).astype(np.float32)
    total_vectors, dim = vectors_matrix.shape
    logger.info(f"Total vector matrix shape: {vectors_matrix.shape}")

    logger.info(f"Building FAISS IndexFlatIP({dim})...")
    index = faiss.IndexFlatIP(dim)
    index.add(vectors_matrix)

    # Write active index and labels
    faiss.write_index(index, str(ACTIVE_INDEX_PATH))
    logger.info(f"Wrote active index to {ACTIVE_INDEX_PATH} ({ACTIVE_INDEX_PATH.stat().st_size / 1024:.2f} KB)")

    with open(ACTIVE_LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(labels_records, f, indent=2)
    logger.info(f"Wrote active labels to {ACTIVE_LABELS_PATH} ({len(labels_records)} records)")

    # Write versioned backup copies
    faiss.write_index(index, str(V2_INDEX_PATH))
    with open(V2_LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(labels_records, f, indent=2)
    logger.info(f"Wrote versioned backup index to {V2_INDEX_PATH}")

    logger.info("=" * 80)
    logger.info("FAISS INDEX REBUILD V2 COMPLETE!")
    logger.info(f"  - Monuments indexed: {len(monument_keys)}")
    logger.info(f"  - Reference images : {total_images_indexed}")
    logger.info(f"  - Centroids        : {total_centroids_indexed}")
    logger.info(f"  - Total vectors    : {index.ntotal}")
    logger.info("=" * 80)

    return total_images_indexed, total_centroids_indexed, index.ntotal


if __name__ == "__main__":
    rebuild_index_v2()

