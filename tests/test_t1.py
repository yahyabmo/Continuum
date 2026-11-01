import numpy as np
import pytest

from continuum.baselines import brackets, crossfade
from continuum.synth import toy_take
from continuum.t1 import MeanError, score_clip, validated, verdict
from continuum.timeaxis import split


def fake_flow(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Two channels that depend on the images, enough to compare two flows."""
    difference = b.astype(np.float64) - a.astype(np.float64)
    return difference[..., :2]


def fake_norm(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.linalg.norm(fake_flow(a, b), axis=2)


def row(rife: float, fade: float, rife_epe: float, fade_epe: float) -> dict:
    return {
        "psnr_m": {"rife": rife, "crossfade": fade},
        "epe_m": {"rife": rife_epe, "crossfade": fade_epe},
    }


def test_a_method_equal_to_the_crossfade_is_not_validated():
    take = toy_take(n_frames=30)
    result = score_clip("toy", take, crossfade, fake_norm, fake_flow)
    assert result["psnr_m"]["rife"] == pytest.approx(result["psnr_m"]["crossfade"])
    assert result["epe_m"]["rife"] == pytest.approx(result["epe_m"]["crossfade"])
    assert not result["validated"]


def test_a_perfect_method_is_validated():
    take = toy_take(n_frames=30)
    train, held = split(30, 2)
    truths = iter(take.frames[row[1]] for row in brackets(train, held))
    result = score_clip("toy", take, lambda a, b, tau: next(truths), fake_norm, fake_flow)
    assert result["epe_m"]["rife"] == 0
    assert result["validated"]


def test_only_motion_counts_in_the_energy():
    take = toy_take(n_frames=30)
    result = score_clip("toy", take, crossfade, fake_norm, fake_flow)
    assert set(result["energy"]) == {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27}
    assert max(result["energy"].values()) > 0


@pytest.mark.parametrize(
    "values, expected",
    [
        ((31.0, 30.0, 0.8, 1.0), True),
        ((30.9, 30.0, 0.8, 1.0), False),
        ((31.0, 30.0, 0.81, 1.0), False),
        ((None, 30.0, 0.8, 1.0), False),
    ],
)
def test_validation_needs_both_gains(values, expected):
    assert validated(row(*values)) is expected


def test_the_verdict_needs_four_clips():
    assert verdict([{"validated": True}] * 4 + [{"validated": False}] * 2)["passed"]
    assert not verdict([{"validated": True}] * 3 + [{"validated": False}] * 3)["passed"]


def test_mean_error_without_values_has_no_value():
    assert MeanError().value is None
