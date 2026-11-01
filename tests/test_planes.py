import json

import cv2
import numpy as np

from continuum.planes import COLUMNS, COUNT, atlas, export, stride
from continuum.prep import HEIGHT, WIDTH
from continuum.synth import toy_take
from continuum.timeaxis import Clip


def test_the_planes_fit_in_the_clip_at_an_exact_step():
    assert stride(600) == 9
    assert (COUNT - 1) * stride(600) < 600


def test_each_plane_lands_in_its_cell():
    take = toy_take(n_frames=128, noise=0.0)
    sheet = atlas(take)
    assert sheet.shape == (8 * HEIGHT, COLUMNS * WIDTH, 4)
    plane = 9
    top, left = (plane // COLUMNS) * HEIGHT, (plane % COLUMNS) * WIDTH
    cell = sheet[top : top + HEIGHT, left : left + WIDTH, :3]
    assert np.array_equal(cell, take.frames[plane * stride(128)])


def test_the_background_is_transparent_and_the_body_is_not():
    sheet = atlas(toy_take(n_frames=128, noise=0.0))
    assert sheet[4, 4, 3] == 0
    assert sheet[HEIGHT // 2, WIDTH // 2, 3] == 255


def test_export_writes_what_the_page_reads(tmp_path):
    export(toy_take(n_frames=128, noise=0.0), tmp_path)
    image = cv2.imread(str(tmp_path / "atlas.webp"), cv2.IMREAD_UNCHANGED)
    assert image.shape == (8 * HEIGHT, COLUMNS * WIDTH, 4)
    grid = Clip.load(tmp_path / "clip.json").grids["planes"]
    assert grid.n == COUNT
    assert float(grid.step) == stride(128) / 60
    layout = json.loads((tmp_path / "planes.json").read_text(encoding="utf-8"))
    assert layout == {"columns": COLUMNS, "width": WIDTH, "height": HEIGHT}
