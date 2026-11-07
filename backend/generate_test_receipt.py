"""
Generate synthetic non-monument document image for testing pure non-monument rejection.
"""
from PIL import Image, ImageDraw
from pathlib import Path

out_dir = Path(__file__).resolve().parent / "datasets"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "receipt_distractor.jpg"

img = Image.new("RGB", (320, 240), color=(245, 245, 245))
draw = ImageDraw.Draw(img)
for y in range(20, 220, 20):
    draw.rectangle([(30, y), (290, y + 10)], fill=(30, 30, 30))

img.save(out_file, format="JPEG", quality=90)
print(f"Saved {out_file}")

