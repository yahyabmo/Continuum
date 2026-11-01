"""Reproduce the cross-fade table in one command.

The mask of this table uses the DIS flow of the CPU, so the values are provisional:
T1 will score again with the flow of the GPU.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
from pathlib import Path

import numpy as np

from continuum.baselines import brackets, crossfade
from continuum.flow import dis_magnitude
from continuum.metrics import PooledPsnr, motion_mask, person_mask
from continuum.prep import Take, normalise
from continuum.synth import toy_take
from continuum.timeaxis import split

RAW = Path("data/raw")


def noise_ceiling(take: Take, step: int = 10) -> float | None:
    """PSNR between neighbouring frames, on the background of both."""
    score = PooledPsnr()
    for i in range(0, len(take.frames) - 1, step):
        a, b = take.frames[i], take.frames[i + 1]
        background = ~(person_mask(a, take.plate) | person_mask(b, take.plate))
        score.add(a, b, background)
    return score.value


def score_crossfade(name: str, take: Take, keep_every: int = 2) -> dict:
    frames = take.frames
    train, held = split(len(frames), keep_every)
    moving, whole = PooledPsnr(), PooledPsnr()
    rows = brackets(train, held)
    for before, frame, after, tau in rows:
        output = crossfade(frames[before], frames[after], tau)
        mask = motion_mask(
            person_mask(frames[frame], take.plate),
            dis_magnitude(frames[before], frames[after]),
        )
        moving.add(output, frames[frame], mask)
        whole.add(output, frames[frame], np.ones(mask.shape, dtype=bool))
    return {
        "clip": name,
        "frames": len(frames),
        "keep_every": keep_every,
        "held": len(rows),
        "scored": moving.frames,
        "psnr_m": moving.value,
        "psnr_full": whole.value,
        "noise_ceiling": noise_ceiling(take),
    }


def commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def table(rows: list[dict]) -> str:
    lines = ["clip  frames  scored  PSNR-M  full  ceiling"]
    for r in rows:
        values = (r["psnr_m"], r["psnr_full"], r["noise_ceiling"])
        shown = ["  n/a" if v is None or math.isinf(v) else f"{v:5.2f}" for v in values]
        lines.append(f"{r['clip']:<5} {r['frames']:>6} {r['scored']:>7}  " + "  ".join(shown))
    return "\n".join(lines)


def raw_path(name: str) -> Path:
    found = sorted(p for p in RAW.glob(f"{name}.*") if p.suffix.lower() in (".mp4", ".mov"))
    if not found:
        raise SystemExit(f"no take named {name} in {RAW}")
    return found[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clips", nargs="*", help="take names in data/raw, such as C1 C2 C3")
    parser.add_argument("--demo", action="store_true", help="use the synthetic take")
    parser.add_argument("--out", type=Path, default=Path("results/crossfade.json"))
    args = parser.parse_args()
    if args.demo == bool(args.clips):
        parser.error("name some clips, or use --demo")

    if args.demo:
        rows = [score_crossfade("toy", toy_take())]
        print(table(rows))
        return

    rows = [score_crossfade(name, normalise(raw_path(name))) for name in args.clips]
    print(table(rows))
    report = {
        "test": "crossfade",
        "provisional": True,
        "flow": "dis",
        "commit": commit(),
        "machine": platform.processor() or platform.machine(),
        "rows": rows,
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
