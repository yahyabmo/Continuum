"""Turn a raw phone take into frames ready for measurement.

The plate, the empty background, comes from a separate take of the same scene, or
else from the first seconds of the take. An uneven frame rate would shift the truth
of a held-out frame, so every take is checked before use.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import av
import cv2
import numpy as np

FPS = 60
LEAD_SECONDS = 3
CLIP_SECONDS = 10
WIDTH, HEIGHT = 216, 384
HDR_TRANSFERS = {16: "PQ", 18: "HLG"}


@dataclass(frozen=True)
class Probe:
    width: int
    height: int
    n_frames: int
    fps: float
    irregular: float
    transfer: int

    @property
    def seconds(self) -> float:
        return self.n_frames / self.fps


@dataclass(frozen=True)
class Take:
    frames: np.ndarray
    plate: np.ndarray


def timing(gaps: np.ndarray) -> tuple[float, float]:
    """Frame rate, and share of the gaps between frames that stray from the usual one.

    The first gap is a start-up delay of the camera, and the lead is cut anyway.
    """
    median = float(np.median(gaps))
    return 1 / median, float(np.mean(np.abs(gaps[1:] / median - 1) > 0.25))


def probe(path: Path) -> Probe:
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        first = next(container.decode(stream))
        container.seek(0)
        pts = sorted(p.pts for p in container.demux(stream) if p.pts is not None)
        time_base = float(stream.time_base)
    fps, irregular = timing(np.diff(np.array(pts, dtype=np.float64)) * time_base)
    width, height = first.width, first.height
    if first.rotation % 180:
        width, height = height, width
    return Probe(
        width=width,
        height=height,
        n_frames=len(pts),
        fps=fps,
        irregular=irregular,
        transfer=first.color_trc,
    )


def check(p: Probe, seconds: float = LEAD_SECONDS + CLIP_SECONDS) -> list[str]:
    """List what makes a take unusable; an empty list means it is fine."""
    problems = []
    if abs(p.fps - FPS) > 1:
        problems.append(f"{p.fps:.2f} fps instead of {FPS}")
    if p.irregular > 0.002:
        problems.append(f"{p.irregular:.1%} of the frame gaps are irregular")
    if p.transfer in HDR_TRANSFERS:
        problems.append(f"HDR video ({HDR_TRANSFERS[p.transfer]})")
    if p.height <= p.width:
        problems.append(f"not vertical ({p.width}x{p.height})")
    if p.height < HEIGHT:
        problems.append(f"too small ({p.width}x{p.height})")
    if p.seconds < seconds:
        problems.append(f"{p.seconds:.1f} s long, {seconds} s needed")
    return problems


def upright(image: np.ndarray, rotation: int) -> np.ndarray:
    """Apply the display rotation of a frame, given in degrees counterclockwise."""
    return np.rot90(image, k=rotation // 90) if rotation else image


def _fit(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """Crop to the target ratio around the centre, then scale down."""
    h, w = image.shape[:2]
    keep_w = min(w, round(h * width / height))
    keep_h = min(h, round(w * height / width))
    left, top = (w - keep_w) // 2, (h - keep_h) // 2
    crop = image[top : top + keep_h, left : left + keep_w]
    return cv2.resize(crop, (width, height), interpolation=cv2.INTER_AREA)


def decode(path: Path, width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    frames = []
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        for frame in container.decode(stream):
            image = upright(frame.to_ndarray(format="rgb24"), frame.rotation)
            frames.append(_fit(image, width, height))
    return np.stack(frames)


def _checked(path: Path, seconds: float) -> None:
    problems = check(probe(path), seconds)
    if problems:
        raise ValueError(f"{path.name}: " + "; ".join(problems))


def normalise(path: Path, plate: Path | None = None, start: float = LEAD_SECONDS) -> Take:
    """Decode a checked take and keep the clip that begins start seconds in."""
    _checked(path, start + CLIP_SECONDS)
    frames = decode(path)
    first = round(start * FPS)
    if plate is None:
        if first < FPS:
            raise ValueError(f"{path.name}: a lead of {start} s is too short for a plate")
        # The last half second of the lead may already show the person arriving.
        background = np.median(frames[: first - FPS // 2], axis=0)
    else:
        _checked(plate, 1)
        background = np.median(decode(plate), axis=0)
    return Take(frames[first : first + CLIP_SECONDS * FPS], background.astype(np.uint8))


def main() -> None:
    path = Path(sys.argv[1])
    p = probe(path)
    print(f"{path.name}: {p.width}x{p.height}, {p.fps:.2f} fps, {p.seconds:.1f} s")
    print(f"irregular gaps: {p.irregular:.1%}, transfer: {p.transfer}")
    problems = check(p)
    print("usable" if not problems else "\n".join(f"problem: {x}" for x in problems))


if __name__ == "__main__":
    main()
