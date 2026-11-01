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


BAR_WIDTH = 14
BAR_HEIGHT = 40
BAR_TOP = HEIGHT // 4 + 40


def bar_left(frame: int, speed: float = 3.0) -> int:
    """Left edge of the bar: it goes back and forth across the image."""
    span = WIDTH - BAR_WIDTH
    phase = (frame * speed) % (2 * span)
    return round(phase if phase < span else 2 * span - phase)


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
    bar = _texture(rng, BAR_HEIGHT, BAR_WIDTH, 210, 255)
    top, bottom, left, right = HEIGHT // 4, HEIGHT * 3 // 4, WIDTH // 4, WIDTH * 3 // 4
    frames = np.empty((n_frames, HEIGHT, WIDTH, 3), dtype=np.uint8)
    for i in range(n_frames):
        frame = plate.copy()
        frame[top:bottom, left:right] = body[top:bottom, left:right]
        x = bar_left(i, speed)
        frame[BAR_TOP : BAR_TOP + BAR_HEIGHT, x : x + BAR_WIDTH] = bar
        if noise:
            frame = np.clip(frame + rng.normal(0, noise, frame.shape), 0, 255).astype(np.uint8)
        frames[i] = frame
    return Take(frames, plate)
