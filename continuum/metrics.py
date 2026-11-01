"""Measures defined in docs/EVALUATION.md."""

from __future__ import annotations

import math

import cv2
import numpy as np

PEAK = 255.0
# 4 px at 640 px high, at the 384 px high of the scoring resolution.
MOTION_THRESHOLD = 2.4
PERSON_THRESHOLD = 12
PERSON_DILATION = 5


def psnr(mse: float) -> float:
    return math.inf if mse == 0 else 10 * math.log10(PEAK**2 / mse)


class PooledPsnr:
    """PSNR on the squared error pooled over a clip; empty masks count for nothing."""

    def __init__(self) -> None:
        self.squared_error = 0.0
        self.values = 0
        self.frames = 0

    def add(self, output: np.ndarray, reference: np.ndarray, mask: np.ndarray) -> None:
        if not mask.any():
            return
        error = output.astype(np.float64)[mask] - reference.astype(np.float64)[mask]
        self.squared_error += float(np.sum(error**2))
        self.values += error.size
        self.frames += 1

    @property
    def value(self) -> float | None:
        return psnr(self.squared_error / self.values) if self.values else None


def foreground(frame: np.ndarray, plate: np.ndarray) -> np.ndarray:
    """Pixels that differ from the empty background."""
    difference = np.abs(frame.astype(np.int16) - plate.astype(np.int16)).max(axis=2)
    return difference > PERSON_THRESHOLD


def person_mask(frame: np.ndarray, plate: np.ndarray) -> np.ndarray:
    """The foreground, dilated: scoring must not miss the edges of the person."""
    size = 2 * PERSON_DILATION + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.dilate(foreground(frame, plate).astype(np.uint8), kernel).astype(bool)


def motion_mask(person: np.ndarray, flow_magnitude: np.ndarray) -> np.ndarray:
    return person & (flow_magnitude > MOTION_THRESHOLD)


def beta(
    output: np.ndarray, reference: np.ndarray, crossfaded: np.ndarray, mask: np.ndarray
) -> float | None:
    """Double contour in colour: 1 for the cross-fade, 0 for a perfect image."""
    if not mask.any():
        return None
    r = reference.astype(np.float64)[mask]
    g = output.astype(np.float64)[mask] - r
    c = crossfaded.astype(np.float64)[mask] - r
    norm = float(np.sum(c * c))
    return float(np.sum(g * c)) / norm if norm else None


def select_beta_frames(
    energies: dict[str, dict[int, float]],
    count: int = 10,
    per_clip: int = 3,
    min_gap: int = 20,
) -> list[tuple[str, int]]:
    """Apply the rule of docs/EVALUATION.md: the highest energies, spread out."""
    ranked = sorted(
        ((e, clip, frame) for clip, rows in energies.items() for frame, e in rows.items()),
        key=lambda row: (-row[0], row[1], row[2]),
    )
    chosen: list[tuple[str, int]] = []
    for _, clip, frame in ranked:
        same = [f for c, f in chosen if c == clip]
        if len(same) < per_clip and all(abs(frame - f) >= min_gap for f in same):
            chosen.append((clip, frame))
            if len(chosen) == count:
                break
    return chosen
