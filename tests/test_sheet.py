import numpy as np

from continuum.sheet import COLUMNS, contact_sheet


def test_one_thumbnail_every_half_second():
    frames = np.zeros((300, 32, 18, 3), dtype=np.uint8)
    sheet = contact_sheet(frames, fps=60)
    assert sheet.shape == (2 * 32, COLUMNS * 18, 3)


def test_each_thumbnail_carries_its_time():
    frames = np.zeros((60, 64, 64, 3), dtype=np.uint8)
    sheet = contact_sheet(frames, fps=60)
    assert sheet[:, :64].any()
    assert not sheet[:, 128:].any()
