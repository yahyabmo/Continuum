"""A synthetic take whose truth is known, used to test the bench without a video.

A bar sweeps in front of a textured body: the hard case of the real clips, a limb
that passes in front of the torso.
"""

from __future__ import annotations

import numpy as np

from continuum.prep import CLIP_SECONDS, FPS, HEIGHT, WIDTH, Take


def _texture(rng: np.random.Generator, height: int, width: int, low: int, high: int) -> np.ndarray:
    coarse = rng.integers(low, high, size=(height // 8 + 2, width // 8 + 2, 3), dtype=np.uint8)
    return np.kron(coarse, np.ones((8, 8, 1), dtype=np.uint8))[:height, :width]


def toy_take(
    n_frames: int = CLIP_SECONDS * FPS,
    speed: float = 3.0,
    noise: float = 1.0,
    seed: int = 0,
) -> Take:
    """Render a take; speed is in pixels per frame at the full frame rate."""
    rng = np.random.default_rng(seed)
    plate = _texture(rng, HEIGHT, WIDTH, 40, 90)
    body = _texture(rng, HEIGHT, WIDTH, 120, 200)
    bar = _texture(rng, HEIGHT, WIDTH, 210, 255)
    top, bottom, left, right = HEIGHT // 4, HEIGHT * 3 // 4, WIDTH // 4, WIDTH * 3 // 4
    bar_width = 14
    span = WIDTH - bar_width
    frames = np.empty((n_frames, HEIGHT, WIDTH, 3), dtype=np.uint8)
    for i in range(n_frames):
        frame = plate.copy()
        frame[top:bottom, left:right] = body[top:bottom, left:right]
        phase = (i * speed) % (2 * span)
        x = round(phase if phase < span else 2 * span - phase)
        frame[top + 40 : top + 80, x : x + bar_width] = bar[top + 40 : top + 80, x : x + bar_width]
        if noise:
            frame = np.clip(frame + rng.normal(0, noise, frame.shape), 0, 255).astype(np.uint8)
        frames[i] = frame
    return Take(frames, plate)
