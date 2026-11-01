"""Cut a take into evenly spaced planes for the first page of the site.

The alpha comes from the difference to the plate: it is rough, and it only serves
until the real alpha exists.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np

from continuum.bench import raw_path
from continuum.metrics import person_mask
from continuum.prep import FPS, Take, normalise
from continuum.synth import toy_take
from continuum.timeaxis import Clip, Grid

COUNT = 64
COLUMNS = 8
SOFTNESS = 5
QUALITY = 90


def stride(n_frames: int, count: int = COUNT) -> int:
    """Frames between two planes: an exact step, so that t stays evenly spaced."""
    return (n_frames - 1) // (count - 1)


def rough_alpha(frame: np.ndarray, plate: np.ndarray) -> np.ndarray:
    mask = person_mask(frame, plate).astype(np.uint8) * 255
    return cv2.GaussianBlur(mask, (0, 0), SOFTNESS)


def atlas(take: Take, count: int = COUNT, columns: int = COLUMNS) -> np.ndarray:
    """Lay the planes out in an RGBA image, left to right and top to bottom."""
    _, height, width, _ = take.frames.shape
    rows = -(-count // columns)
    sheet = np.zeros((rows * height, columns * width, 4), dtype=np.uint8)
    step = stride(len(take.frames), count)
    for i in range(count):
        frame = take.frames[i * step]
        top, left = (i // columns) * height, (i % columns) * width
        sheet[top : top + height, left : left + width, :3] = frame
        sheet[top : top + height, left : left + width, 3] = rough_alpha(frame, take.plate)
    return sheet


def export(take: Take, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    n_frames, height, width, _ = take.frames.shape
    step = Fraction(stride(n_frames), FPS)
    bgra = cv2.cvtColor(atlas(take), cv2.COLOR_RGBA2BGRA)
    cv2.imwrite(str(out / "atlas.webp"), bgra, [cv2.IMWRITE_WEBP_QUALITY, QUALITY])
    clip = Clip(Fraction(FPS), n_frames, {"planes": Grid(Fraction(0), step, COUNT)})
    clip.save(out / "clip.json")
    layout = {"columns": COLUMNS, "width": width, "height": height}
    (out / "planes.json").write_text(json.dumps(layout, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clip", nargs="?", help="take name in data/raw, such as C1")
    parser.add_argument("--demo", action="store_true", help="use the synthetic take")
    args = parser.parse_args()
    if args.demo == bool(args.clip):
        parser.error("name a clip, or use --demo")
    name = "demo" if args.demo else args.clip
    take = toy_take() if args.demo else normalise(raw_path(args.clip))
    export(take, Path("web/public/clips") / name)


if __name__ == "__main__":
    main()
