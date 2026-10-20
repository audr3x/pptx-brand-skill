#!/usr/bin/env python3
"""Rasterize the Title Slide Day Crop from assets/template.pptx to a 16:9 PNG.

The PPTX stores Day_Crop_5 as a tall SVG (256 x 940). PowerPoint stretches it
across the 10.00 x 5.625 in cover. This script does the same stretch so
Google Slides createImage can place a PNG full-bleed.
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PPTX = ROOT / "assets" / "template.pptx"
OUT = ROOT / "assets" / "logos" / "cover-gradient.png"
SVG_MEMBER = "ppt/media/image1.svg"

# Stops from gradient-day-crop.svg after the layout transform
# (offset 0 gold at the bottom, offset 1 navy-blue at the top).
STOPS = [
    (0.00, (0x14, 0x59, 0xA9)),
    (0.05, (0x14, 0x59, 0xA9)),
    (0.45, (0x70, 0xC9, 0xD3)),
    (0.70, (0xCA, 0xE5, 0xCE)),
    (0.85, (0xEE, 0xED, 0xB6)),
    (0.95, (0xFC, 0xE5, 0x94)),
    (1.00, (0xFC, 0xE1, 0x8B)),
]
NATIVE = (256, 940)
SLIDE_PX = (1920, 1080)


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _color_at(t: float) -> tuple[int, int, int]:
    t = min(1.0, max(0.0, t))
    for i in range(1, len(STOPS)):
        t0, c0 = STOPS[i - 1]
        t1, c1 = STOPS[i]
        if t <= t1:
            u = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return _lerp(c0, c1, u)
    return STOPS[-1][1]


def render() -> Image.Image:
    if not PPTX.is_file():
        raise SystemExit(f"PPTX not found: {PPTX}")
    with ZipFile(PPTX) as zf:
        if SVG_MEMBER not in zf.namelist():
            raise SystemExit(f"{SVG_MEMBER} missing from {PPTX}")
    native = Image.new("RGB", NATIVE)
    pix = native.load()
    width, height = NATIVE
    for y in range(height):
        color = _color_at(y / (height - 1))
        for x in range(width):
            pix[x, y] = color
    return native.resize(SLIDE_PX, Image.Resampling.LANCZOS)


def main() -> int:
    image = render()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} {image.size[0]}x{image.size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
