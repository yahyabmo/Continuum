import json
from fractions import Fraction
from pathlib import Path

import pytest

from continuum.timeaxis import Clip, Grid, split

CASES = json.loads((Path(__file__).parent / "timeaxis_cases.json").read_text(encoding="utf-8"))


def grid(name: str) -> Grid:
    g = CASES["grids"][name]
    return Grid(Fraction(g["start"]), Fraction(g["step"]), g["n"])


@pytest.mark.parametrize("case", CASES["cases"])
def test_shared_cases(case):
    g = grid(case["grid"])
    k, t, w = Fraction(case["k"]), Fraction(case["t"]), Fraction(case["w"])
    assert g.time(k) == t
    assert g.index(t) == k
    assert g.tex(t) == w
    assert g.tex_to_time(w) == t


def test_slices_sit_at_voxel_centres():
    g = grid("volume")
    assert [g.tex(g.time(k)) * g.n for k in (0, 1, 299)] == [
        Fraction(1, 2),
        Fraction(3, 2),
        Fraction(599, 2),
    ]


def test_frame_times_use_the_fixed_rate():
    clip = Clip(Fraction(60), 600, {})
    assert clip.frames.time(1) == Fraction(1, 60)
    assert clip.frames.time(599) == Fraction(599, 60)


def test_volume_slices_are_the_even_frames():
    clip = Clip(Fraction(60), 600, {"volume": grid("volume")})
    train, _ = split(clip.n_frames, 2)
    assert len(train) == clip.grids["volume"].n
    assert all(
        clip.frames.time(i) == clip.grids["volume"].time(k) for k, i in enumerate(train)
    )


def test_json_round_trip(tmp_path):
    clip = Clip(Fraction(60), 600, {"volume": grid("volume"), "zoom": grid("zoom")})
    path = tmp_path / "clip.json"
    clip.save(path)
    assert Clip.load(path) == clip


@pytest.mark.parametrize("keep_every, n_train", [(2, 300), (4, 150)])
def test_split_covers_every_frame_once(keep_every, n_train):
    train, held = split(600, keep_every)
    assert len(train) == n_train
    assert sorted(train + held) == list(range(600))


def test_invalid_values_are_refused():
    with pytest.raises(ValueError):
        Grid(Fraction(0), Fraction(0), 10)
    with pytest.raises(ValueError):
        Grid(Fraction(0), Fraction(1, 30), 0)
    with pytest.raises(ValueError):
        split(600, 1)
