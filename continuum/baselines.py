"""Reference methods that every other method has to beat."""

from __future__ import annotations

from bisect import bisect_left
from fractions import Fraction

import numpy as np


def brackets(train: list[int], held: list[int]) -> list[tuple[int, int, int, Fraction]]:
    """Pair each held-out frame with its training neighbours: (before, frame, after, tau).

    A held-out frame past the last training frame has no neighbour after it and is skipped.
    """
    rows = []
    for frame in held:
        j = bisect_left(train, frame)
        if 0 < j < len(train):
            before, after = train[j - 1], train[j]
            rows.append((before, frame, after, Fraction(frame - before, after - before)))
    return rows


def crossfade(before: np.ndarray, after: np.ndarray, tau: Fraction) -> np.ndarray:
    return (1 - float(tau)) * before.astype(np.float32) + float(tau) * after.astype(np.float32)
