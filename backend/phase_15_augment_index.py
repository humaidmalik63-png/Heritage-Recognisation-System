"""
Phase 15 — Augmented FAISS Index Builder
-----------------------------------------
Extends the production FAISS index with geometrically-transformed anchor variants
to reduce false NON_MONUMENT_REJECTION for partial, occluded, and close-up views.

Augmentation pipeline per source image:
  - 0° (original)          : baseline
  - ±90° rotation           : covers side/portrait vs landscape crops
  - 70% / 85% center crop   : simulates zoomed-in architectural detail shots
  - 130% / 150% scale up    : simulates distant/scaled-down views
  - slight brightness shift  : handles over/under-exposed field photos

Produces: monument_index_v2.faiss + monument_labels_v2.json
        (placed alongside the existing v1 index so main.py can be switched via a flag)
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
SOURCE_DATASET_DIR = BASE_DIR / "dataset"              # original 10-monument dataset
OUTPUT_INDEX = BASE_DIR / "monument_index_v2.faiss"
OUTPUT_LABELS = BASE_DIR / "monument_labels_v2.json"
METADATA_FILE = BASE_DIR / "monuments_metadata.json"

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDING_DIM = 512

logger = logging.getLogger("phase15_augment")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Augmentation transforms applied to each source image
AUGMENTATIONS = [
    ("0deg_crop_full",    lambda img: img),                                     # original
    ("90deg_cw",          lambda img: img.rotate(-90, expand=True)),            # rotate clockwise
    ("90deg_ccw",         lambda img: img.rotate(90, expand=True)),             # rotate counter-clockwise
    ("70center_crop",     lambda img: _crop_center(img, 0.70)),                 # zoomed-in detail
    ("85center_crop",     lambda img: _crop_center(img, 0.85)),                 # tighter detail shot
    ("130pct_scale_up",   lambda img: _scale(img, 1.30)),                       # simulates closer distance
    ("150pct_scale_up",   lambda img: _scale(img, 1.50)),                       # extreme close-up
    ("bright_plus_15",    lambda img: _adjust_brightness(img, 1.15)),           # slightly over-exposed
    ("dark_minus_10",     lambda img: _adjust_brightness(img, 0.90)),           # slightly under-exposed
]


def _crop_center(img: Image.Image, ratio: float) -> Image.Image:
    w, h = img.size
    nw, nh = int(w * ratio), int(h * ratio)
    left = (w - nw) // 2
    top = (h - nh) // 2
    return img.crop((left, top, left + nw, top + nh))


def _scale(img: Image.Image, factor: float) -> Image.Image:
    """Scale image then downscale back to original size (simulates crop region)."""
    new_w = int(img.width * factor)
    new_h = int(img.height * factor)
    scaled = img.resize((new_w, new_h), Image.LANCZOS)
    return scaled.resize(img.size, Image.LANCZOS)


def _adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)


def extract_embedding(
    image: Image.Image,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: str,
) -> np.ndarray:
    """Extract and L2-normalize a 512-D CLIP embedding."""
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
    if norm > 1e-8:
        vec = vec / norm
    return vec


def build_augmented_index() -> Tuple[int, int]:
    logger.info("=" * 70)
    logger.info("PHASE 15 — AUGMENTED FAISS INDEX BUILDER")
    logger.info("=" * 70)

    # ── Load metadata ────────────────────────────────────────────────────
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Metadata file missing at {METADATA_FILE}")
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata: Dict = json.load(f)

    # ── Device setup ─────────────────────────────────────────────────────
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Compute device: {device.upper()}")
    logger.info(f"Loading CLIP model: {MODEL_NAME} ...")
    clip_model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
    clip_processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    clip_model.eval()

    # ── Collect source images per monument ───────────────────────────────
    all_vectors: List[np.ndarray] = []
    labels_records: List[Dict] = []
    total_processed = 0

    for monument_key in sorted(metadata.keys()):
        monument_dir = SOURCE_DATASET_DIR / monument_key
        if not monument_dir.is_dir():
            logger.warning(f"Skipping '{monument_key}': directory not found.")
            continue

        jpg_files = sorted(monument_dir.glob("*.jpg"))
        if not jpg_files:
            logger.warning(f"Skipping '{monument_key}': no .jpg files found.")
            continue

        meta = metadata[monument_key]
        view_type = meta.get("view_type", "full_structure")
        logger.info(f"\nProcessing '{monument_key}' — {len(jpg_files)} source image(s), view={view_type}")

        for src_idx, img_path in enumerate(jpg_files):
            try:
                img = Image.open(img_path).convert("RGB")
            except Exception as exc:
                logger.warning(f"  Cannot open {img_path.name}: {exc}")
                continue

            base_name = img_path.stem  # e.g. "ref_01"

            for aug_name, transform_fn in AUGMENTATIONS:
                augmented = transform_fn(img)
                vec = extract_embedding(augmented, clip_model, clip_processor, device)
                all_vectors.append(vec)

                labels_records.append({
                    "index_id": len(all_vectors) - 1,
                    "monument_key": monument_key,
                    "monument_name": meta.get("name", monument_key.replace("_", " ").title()),
                    "image_id": f"{base_name}_{aug_name}",
                    "view_type": aug_name,
                    "source_file": img_path.name,
                    "augmentation": aug_name,
                })

            total_processed += 1
            if (src_idx + 1) % 5 == 0 or src_idx + 1 == len(jpg_files):
                logger.info(f"  Progress: {src_idx + 1}/{len(jpg_files)} source images done")

    logger.info(f"\nTotal embeddings extracted: {len(all_vectors)}")

    # ── Build FAISS index ────────────────────────────────────────────────
    if not all_vectors:
        raise RuntimeError("No embeddings generated — aborting.")

    embeddings_np = np.vstack(all_vectors).astype("float32")
    logger.info(f"Embedding matrix shape: {embeddings_np.shape}")

    index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner Product = Cosine (vectors already L2-normalized)
    index.add(embeddings_np)
    faiss.write_index(index, str(OUTPUT_INDEX))
    logger.info(f"Wrote FAISS index → {OUTPUT_INDEX} ({index.ntotal} vectors)")

    # ── Write labels ─────────────────────────────────────────────────────
    with open(OUTPUT_LABELS, "w", encoding="utf-8") as f:
        json.dump(labels_records, f, indent=2)
    logger.info(f"Wrote labels mapping → {OUTPUT_LABELS} ({len(labels_records)} entries)")

    # ── Summary stats ────────────────────────────────────────────────────
    by_monument: Dict[str, int] = {}
    by_view: Dict[str, int] = {}
    for rec in labels_records:
        mk = rec["monument_key"]
        vt = rec["view_type"]
        by_monument[mk] = by_monument.get(mk, 0) + 1
        by_view[vt] = by_view.get(vt, 0) + 1

    logger.info("\n=== Augmentation summary ===")
    logger.info(f"Monuments indexed: {len(by_monument)} (was 10)")
    logger.info(f"Total anchors: {len(labels_records)} (was 210)")
    logger.info(f"Expansion factor: {len(labels_records) / 210:.1f}x")
    logger.info("\nPer monument:")
    for mk, count in sorted(by_monument.items(), key=lambda x: -x[1]):
        logger.info(f"  {mk}: {count} anchors")
    logger.info("\nPer augmentation type:")
    for vt, count in sorted(by_view.items(), key=lambda x: -x[1]):
        logger.info(f"  {vt}: {count} anchors")

    logger.info("\n✓ Phase 15 augmented index build complete.")
    return len(all_vectors), len(labels_records)


if __name__ == "__main__":
    build_augmented_index()
