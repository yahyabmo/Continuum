from fractions import Fraction

import numpy as np
import pytest

from continuum.baselines import brackets, crossfade
from continuum.timeaxis import split


def test_half_rate_frames_sit_in_the_middle():
    train, held = split(8, 2)
    assert brackets(train, held) == [
        (0, 1, 2, Fraction(1, 2)),
        (2, 3, 4, Fraction(1, 2)),
        (4, 5, 6, Fraction(1, 2)),
    ]


def test_quarter_rate_frames_get_their_own_position():
    train, held = split(9, 4)
    assert [row[3] for row in brackets(train, held)] == [
        Fraction(1, 4),
        Fraction(1, 2),
        Fraction(3, 4),
    ] * 2


def test_no_held_frame_needs_a_frame_past_the_end():
    train, held = split(600, 2)
    rows = brackets(train, held)
    assert len(rows) == 299
    assert rows[-1][1] == 597


@pytest.mark.parametrize("tau, value", [(Fraction(1, 2), 20.0), (Fraction(1, 4), 15.0)])
def test_crossfade_mixes_the_two_frames(tau, value):
    before = np.full((2, 2, 3), 10, dtype=np.uint8)
    after = np.full((2, 2, 3), 30, dtype=np.uint8)
    assert np.allclose(crossfade(before, after, tau), value)
