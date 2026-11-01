"""Test T1 of docs/EVALUATION.md: does RIFE beat the cross-fade on a clip?

The models run on a GPU, so they come in as functions: this file only holds the
protocol, and it can be tested without them.
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

import numpy as np

from continuum.baselines import brackets, crossfade
from continuum.bench import noise_ceiling
from continuum.metrics import PooledPsnr, motion_mask, person_mask
from continuum.prep import Take
from continuum.timeaxis import split

GAIN_DB = 1.0
EPE_RATIO = 0.8
CLIPS_NEEDED = 4

Interpolate = Callable[[np.ndarray, np.ndarray, Fraction], np.ndarray]
FlowNorm = Callable[[np.ndarray, np.ndarray], np.ndarray]
Flow = Callable[[np.ndarray, np.ndarray], np.ndarray]


class MeanError:
    def __init__(self) -> None:
        self.total = 0.0
        self.count = 0

    def add(self, errors: np.ndarray) -> None:
        self.total += float(errors.sum())
        self.count += errors.size

    @property
    def value(self) -> float | None:
        return self.total / self.count if self.count else None


def score_clip(
    name: str,
    take: Take,
    interpolate: Interpolate,
    train_flow: FlowNorm,
    score_flow: Flow,
    keep_every: int = 2,
) -> dict:
    frames = take.frames
    train, held = split(len(frames), keep_every)
    moving = {"crossfade": PooledPsnr(), "rife": PooledPsnr()}
    whole = {"crossfade": PooledPsnr(), "rife": PooledPsnr()}
    epe = {"crossfade": MeanError(), "rife": MeanError()}
    energy = {}
    rows = brackets(train, held)
    for before, frame, after, tau in rows:
        a, b, truth = frames[before], frames[after], frames[frame]
        norm = train_flow(a, b)
        mask = motion_mask(person_mask(truth, take.plate), norm)
        energy[frame] = float(norm[mask].sum())
        outputs = {"crossfade": crossfade(a, b, tau), "rife": interpolate(a, b, tau)}
        true_flow = score_flow(a, truth) if mask.any() else None
        for method, output in outputs.items():
            moving[method].add(output, truth, mask)
            whole[method].add(output, truth, np.ones(mask.shape, dtype=bool))
            if true_flow is not None:
                gap = np.linalg.norm(score_flow(a, output) - true_flow, axis=2)
                epe[method].add(gap[mask])

    row = {
        "clip": name,
        "keep_every": keep_every,
        "held": len(rows),
        "scored": moving["rife"].frames,
        "psnr_m": {k: v.value for k, v in moving.items()},
        "psnr_full": {k: v.value for k, v in whole.items()},
        "epe_m": {k: v.value for k, v in epe.items()},
        "noise_ceiling": noise_ceiling(take),
        "energy": energy,
    }
    row["validated"] = validated(row)
    return row


def validated(row: dict) -> bool:
    """A clip counts if RIFE gains enough on both measures."""
    psnr, epe = row["psnr_m"], row["epe_m"]
    if None in (psnr["rife"], psnr["crossfade"], epe["rife"], epe["crossfade"]):
        return False
    return (
        psnr["rife"] - psnr["crossfade"] >= GAIN_DB and epe["rife"] <= EPE_RATIO * epe["crossfade"]
    )


def verdict(rows: list[dict]) -> dict:
    count = sum(row["validated"] for row in rows)
    return {"validated": count, "clips": len(rows), "passed": count >= CLIPS_NEEDED}
