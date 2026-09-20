"""Preserve the approved bitmap mark; add safe whitespace for tiny app/site icons.

The unpadded source lives under tools/ (not publicly served). Always regenerate
from it rather than repeatedly shrinking already-padded output.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def build():
    original = Image.open(ROOT / "tools/brand-mark-source.png").convert("RGBA")
    for filename, size in (("icon-192.png", 192), ("apple-touch-icon.png", 180)):
        mark = original.copy()
        mark.thumbnail((round(size * .72), round(size * .72)), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), "white")
        canvas.alpha_composite(mark, ((size-mark.width)//2, (size-mark.height)//2))
        canvas.convert("RGB").save(ROOT / "assets" / filename, optimize=True)


if __name__ == "__main__":
    build()
