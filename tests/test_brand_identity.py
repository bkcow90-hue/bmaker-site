"""Small icons need breathing room; published company facts come from the ledger."""
import csv
import re
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]

def test_small_icons_have_even_safe_margins():
    for file in ("icon-192.png", "apple-touch-icon.png"):
        image = Image.open(ROOT / "assets" / file).convert("RGB")
        assert image.width == image.height
        # Ignore near-white antialiasing; every coloured edge needs breathing room.
        diff = ImageChops.difference(image, Image.new("RGB", image.size, "white"))
        mask = diff.convert("L").point(lambda value: 255 if value > 25 else 0)
        box = mask.getbbox()
        assert box is not None
        left, top, right, bottom = box
        assert min(left, top, image.width-right, image.height-bottom) >= image.width * .10, (file, box)
        assert right-left >= image.width*.60

def test_company_summary_includes_both_business_forms_from_source():
    with (ROOT / "data/cases.source.csv").open(encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["사이트 공개"] == "Y"]
    for name in ("index.html", "llms.txt", "llms-full.txt"):
        text = (ROOT / name).read_text(encoding="utf-8")
        plain = re.sub(r"<[^>]+>", "", text)
        for kind in ("개인", "법인"):
            count = sum(r["사업 형태"] == kind for r in rows)
            assert re.search(rf"{kind}사업자\s*{count}건", plain), name
