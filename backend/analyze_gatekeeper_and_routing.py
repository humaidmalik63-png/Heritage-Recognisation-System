"""
Diagnostic script to inspect embeddings, quality metrics, and gatekeeper dot products.
"""
import sys
from pathlib import Path
import json

WORKSPACE = Path(__file__).resolve().parent.parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

MODEL_NAME = "openai/clip-vit-base-patch32"
device = "cpu"

print("Loading CLIP...")
clip_model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
clip_processor = CLIPProcessor.from_pretrained(MODEL_NAME)
clip_model.eval()

from backend.main import POSITIVE_PROMPTS, NEGATIVE_PROMPTS, GATEKEEPER_SCALE
from backend.uncertainty import inspect_image_quality

def get_text_vector(prompts):
    inp = clip_processor(text=prompts, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        out = clip_model.get_text_features(**inp)
        t = out.pooler_output if hasattr(out, "pooler_output") and out.pooler_output is not None else out
        v = t.cpu().numpy()
        v = v / np.linalg.norm(v, axis=1, keepdims=True)
        mean_v = np.mean(v, axis=0)
        return mean_v / np.linalg.norm(mean_v)

pos_vec = get_text_vector(POSITIVE_PROMPTS)
neg_vec = get_text_vector(NEGATIVE_PROMPTS)

def analyze_image(path):
    img = Image.open(path).convert("RGB")
    q = inspect_image_quality(img)
    
    inp = clip_processor(images=img, return_tensors="pt").to(device)
    with torch.no_grad():
        out = clip_model.get_image_features(**inp)
        t = out.pooler_output if hasattr(out, "pooler_output") and out.pooler_output is not None else out
        vec = t.cpu().numpy()[0]
        vec = vec / np.linalg.norm(vec)

    sim_pos = float(np.dot(vec, pos_vec))
    sim_neg = float(np.dot(vec, neg_vec))
    diff = sim_pos - sim_neg
    exp_pos = np.exp(sim_pos * GATEKEEPER_SCALE)
    exp_neg = np.exp(sim_neg * GATEKEEPER_SCALE)
    gk = float(exp_pos / (exp_pos + exp_neg))

    print(f"\nImage: {path.name}")
    print(f"  Quality: {q}")
    print(f"  sim_pos: {sim_pos:.4f}, sim_neg: {sim_neg:.4f}, diff (pos - neg): {diff:.4f}")
    print(f"  Gatekeeper Score: {gk:.4f}")

analyze_image(Path(r"C:\Users\humai\Pictures\Screenshots\Screenshot 2026-10-01 005418.png"))
analyze_image(Path(r"C:\Users\humai\Pictures\Screenshots\Screenshot 2026-10-01 005544.png"))
analyze_image(WORKSPACE / "backend" / "datasets" / "independent_final_test_v4" / "split_d_086_mysore_palace.jpg")
analyze_image(WORKSPACE / "backend" / "dataset" / "taj_mahal" / "img_1.jpg")

