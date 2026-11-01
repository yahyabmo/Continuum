import math

import numpy as np
import pytest

from continuum.metrics import (
    PooledPsnr,
    beta,
    motion_mask,
    person_mask,
    psnr,
    select_beta_frames,
)


def test_psnr_of_a_known_error():
    assert psnr(255.0**2) == pytest.approx(0.0)
    assert psnr(0.0) == math.inf


def test_pooled_psnr_pools_errors_and_skips_empty_masks():
    reference = np.zeros((2, 2, 3), dtype=np.uint8)
    full = np.ones((2, 2), dtype=bool)
    score = PooledPsnr()
    score.add(np.full((2, 2, 3), 10, dtype=np.uint8), reference, full)
    score.add(np.full((2, 2, 3), 20, dtype=np.uint8), reference, full)
    score.add(np.full((2, 2, 3), 90, dtype=np.uint8), reference, np.zeros((2, 2), dtype=bool))
    assert score.frames == 2
    assert score.value == pytest.approx(psnr((10**2 + 20**2) / 2))


def test_pooled_psnr_without_any_pixel_has_no_value():
    assert PooledPsnr().value is None


def test_beta_is_one_for_the_crossfade_and_zero_for_the_truth():
    rng = np.random.default_rng(0)
    truth = rng.integers(0, 255, (16, 16, 3)).astype(np.float64)
    faded = truth + rng.normal(0, 20, truth.shape)
    mask = np.ones((16, 16), dtype=bool)
    assert beta(faded, truth, faded, mask) == pytest.approx(1.0)
    assert beta(truth, truth, faded, mask) == pytest.approx(0.0)
    assert beta((truth + faded) / 2, truth, faded, mask) == pytest.approx(0.5)


def test_beta_needs_a_mask_and_an_error():
    truth = np.zeros((4, 4, 3))
    assert beta(truth, truth, truth + 1, np.zeros((4, 4), dtype=bool)) is None
    assert beta(truth, truth, truth, np.ones((4, 4), dtype=bool)) is None


def test_person_mask_is_dilated_and_ignores_small_differences():
    plate = np.full((32, 32, 3), 100, dtype=np.uint8)
    frame = plate.copy()
    frame[16, 16] = 200
    frame[2, 2] = 105
    mask = person_mask(frame, plate)
    assert mask[16, 16] and mask[16, 20]
    assert not mask[2, 2]


def test_motion_mask_needs_the_person_and_the_motion():
    person = np.array([[True, True, False]])
    flow = np.array([[3.0, 1.0, 3.0]])
    assert motion_mask(person, flow).tolist() == [[True, False, False]]


def test_beta_frames_follow_the_rule():
    energies = {
        "C1": {i: 100.0 - i for i in range(0, 200, 2)},
        "C2": {i: 50.0 - i for i in range(1, 200, 2)},
        "C3": {i: 40.0 - i for i in range(1, 200, 2)},
        "C4": {i: 30.0 - i for i in range(1, 200, 2)},
    }
    chosen = select_beta_frames(energies)
    assert len(chosen) == 10
    for clip in energies:
        frames = sorted(f for c, f in chosen if c == clip)
        assert len(frames) <= 3
        assert all(b - a >= 20 for a, b in zip(frames, frames[1:], strict=False))
    assert ("C1", 0) in chosen
