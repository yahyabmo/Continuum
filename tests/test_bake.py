import gzip
import json
from fractions import Fraction

import numpy as np

from continuum.bake import bake, export
from continuum.planes import rough_alpha
from continuum.prep import HEIGHT, WIDTH
from continuum.synth import toy_take
from continuum.timeaxis import Grid


def test_one_slice_per_training_frame():
    take = toy_take(n_frames=20, noise=0.0)
    volume = bake(take)
    assert volume.shape == (10, HEIGHT, WIDTH, 4)
    assert np.array_equal(volume[3, ..., :3], take.frames[6])


def test_the_alpha_is_the_mask_and_the_colour_stays_as_filmed():
    take = toy_take(n_frames=4, noise=0.0)
    volume = bake(take)
    assert np.array_equal(volume[1, ..., 3], rough_alpha(take.frames[2], take.plate))
    assert np.array_equal(volume[1, 4, 4, :3], take.frames[2, 4, 4])
    assert volume[1, 4, 4, 3] == 0


def test_export_writes_the_volume_and_its_time_grid(tmp_path):
    export(toy_take(n_frames=20, noise=0.0), tmp_path)
    with gzip.open(tmp_path / "volume.bin.gz") as f:
        data = f.read()
    layout = json.loads((tmp_path / "volume.json").read_text(encoding="utf-8"))
    assert len(data) == layout["width"] * layout["height"] * layout["depth"] * 4
    grid = Grid(Fraction(layout["grid"]["start"]), Fraction(layout["grid"]["step"]), 10)
    assert grid.time(1) == Fraction(2, 60)
