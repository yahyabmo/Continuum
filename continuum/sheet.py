"""A contact sheet of a raw take: one image every half second, with its time.

It serves to choose by eye where each clip starts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from continuum.bench import raw_path
from continuum.prep import decode, probe

EVERY = 0.5
COLUMNS = 8
THUMB_WIDTH, THUMB_HEIGHT = 108, 192
OUT = Path("data/sheets")


def label(image: np.ndarray, text: str) -> None:
    position = (4, image.shape[0] - 6)
    for colour, width in (((0, 0, 0), 3), ((255, 255, 255), 1)):
        cv2.putText(image, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.45, colour, width)


def contact_sheet(frames: np.ndarray, fps: float, every: float = EVERY) -> np.ndarray:
    step = max(1, round(every * fps))
    picked = list(range(0, len(frames), step))
    rows = -(-len(picked) // COLUMNS)
    _, height, width, _ = frames.shape
    sheet = np.zeros((rows * height, COLUMNS * width, 3), dtype=np.uint8)
    for n, i in enumerate(picked):
        image = frames[i].copy()
        label(image, f"{i / fps:.1f} s".replace(".", ","))
        top, left = (n // COLUMNS) * height, (n % COLUMNS) * width
        sheet[top : top + height, left : left + width] = image
    return sheet


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:]:
        path = raw_path(name)
        sheet = contact_sheet(decode(path, THUMB_WIDTH, THUMB_HEIGHT), probe(path).fps)
        out = OUT / f"{name}.jpg"
        cv2.imwrite(
            str(out), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85]
        )
        print(out)


if __name__ == "__main__":
    main()
