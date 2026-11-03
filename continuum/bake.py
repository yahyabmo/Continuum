"""Bake a take into the volume the browser renders: one slice per training frame.

RGB stays as filmed and the alpha holds the mask, so that the page can show either
the object alone or the whole image from the same texture.
"""

from __future__ import annotations

import argparse
import gzip
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from continuum.bench import load_take
from continuum.planes import rough_alpha
from continuum.prep import FPS, Take
from continuum.synth import toy_take

STRIDE = 2


def bake(take: Take, stride: int = STRIDE) -> np.ndarray:
    """Slices in time order, rows from top to bottom, RGBA per pixel."""
    frames = take.frames[::stride]
    volume = np.empty((*frames.shape[:3], 4), dtype=np.uint8)
    volume[..., :3] = frames
    for i, frame in enumerate(frames):
        volume[i, ..., 3] = rough_alpha(frame, take.plate)
    return volume


def export(take: Take, out: Path, fps: int = FPS, stride: int = STRIDE) -> None:
    out.mkdir(parents=True, exist_ok=True)
    volume = bake(take, stride)
    depth, height, width, _ = volume.shape
    with gzip.open(out / "volume.bin.gz", "wb", compresslevel=6) as f:
        f.write(volume.tobytes())
    layout = {
        "width": width,
        "height": height,
        "depth": depth,
        "grid": {"start": "0", "step": str(Fraction(stride, fps)), "n": depth},
    }
    (out / "volume.json").write_text(json.dumps(layout, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clip", nargs="?", help="take name in data/raw, such as C1")
    parser.add_argument("--demo", action="store_true", help="use the synthetic take")
    args = parser.parse_args()
    if args.demo == bool(args.clip):
        parser.error("name a clip, or use --demo")
    name = "demo" if args.demo else args.clip
    take = toy_take() if args.demo else load_take(args.clip)
    export(take, Path("web/public/clips") / name)


if __name__ == "__main__":
    main()
