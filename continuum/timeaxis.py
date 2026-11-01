"""The single definition of t, in seconds of clip, shared by every module.

Times are exact fractions, so that a slice and the frame it comes from never
drift apart. A texture coordinate w puts slice k at the centre of its voxel,
w = (k + 1/2) / n: reading the texture at the time of a slice returns that slice.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True)
class Grid:
    """Evenly spaced samples of t: sample k sits at start + k * step."""

    start: Fraction
    step: Fraction
    n: int

    def __post_init__(self) -> None:
        if self.step <= 0:
            raise ValueError("step must be positive")
        if self.n <= 0:
            raise ValueError("n must be positive")

    def time(self, k: Fraction | int) -> Fraction:
        return self.start + k * self.step

    def index(self, t: Fraction | int) -> Fraction:
        return (t - self.start) / self.step

    def tex(self, t: Fraction | int) -> Fraction:
        return (self.index(t) + Fraction(1, 2)) / self.n

    def tex_to_time(self, w: Fraction | int) -> Fraction:
        return self.time(w * self.n - Fraction(1, 2))


@dataclass(frozen=True)
class Clip:
    """A clip at a fixed frame rate, and the time grids built from it."""

    fps: Fraction
    n_frames: int
    grids: dict[str, Grid]

    @property
    def frames(self) -> Grid:
        return Grid(Fraction(0), 1 / self.fps, self.n_frames)

    def to_json(self) -> str:
        return json.dumps(
            {
                "fps": str(self.fps),
                "n_frames": self.n_frames,
                "grids": {
                    name: {"start": str(g.start), "step": str(g.step), "n": g.n}
                    for name, g in self.grids.items()
                },
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, text: str) -> Clip:
        data = json.loads(text)
        return cls(
            fps=Fraction(data["fps"]),
            n_frames=data["n_frames"],
            grids={
                name: Grid(Fraction(g["start"]), Fraction(g["step"]), g["n"])
                for name, g in data["grids"].items()
            },
        )

    def save(self, path: Path) -> None:
        path.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Clip:
        return cls.from_json(path.read_text(encoding="utf-8"))


def split(n_frames: int, keep_every: int) -> tuple[list[int], list[int]]:
    """Split frame indices into training frames and held-out frames."""
    if keep_every < 2:
        raise ValueError("keep_every must be at least 2")
    train = list(range(0, n_frames, keep_every))
    held = [i for i in range(n_frames) if i % keep_every != 0]
    return train, held
