import av
import numpy as np
import pytest

from continuum.prep import (
    CLIP_SECONDS,
    FPS,
    HEIGHT,
    LEAD_SECONDS,
    WIDTH,
    Probe,
    check,
    normalise,
    probe,
    upright,
)


def fine(**changes) -> Probe:
    values = dict(width=1080, height=1920, n_frames=800, fps=60.0, dropped=0.0, transfer=1)
    return Probe(**{**values, **changes})


def write_take(path, n_frames):
    """Encode a vertical take where the person appears after the lead."""
    with av.open(str(path), "w") as container:
        stream = container.add_stream("libx264", rate=FPS)
        stream.width, stream.height, stream.pix_fmt = 216, 384, "yuv420p"
        lead = LEAD_SECONDS * FPS
        for i in range(n_frames):
            image = np.full((384, 216, 3), 60, dtype=np.uint8)
            if i >= lead:
                image[100:200, 60:150] = 220
            frame = av.VideoFrame.from_ndarray(image, format="rgb24")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def test_a_good_take_has_no_problem():
    assert check(fine()) == []


@pytest.mark.parametrize(
    "changes, word",
    [
        ({"fps": 30.0}, "fps"),
        ({"dropped": 0.01}, "dropped"),
        ({"transfer": 16}, "HDR"),
        ({"width": 1920, "height": 1080}, "vertical"),
        ({"width": 180, "height": 320}, "small"),
        ({"n_frames": 300}, "long"),
    ],
)
def test_each_defect_is_reported(changes, word):
    problems = check(fine(**changes))
    assert len(problems) == 1
    assert word in problems[0]


def test_probe_reads_a_real_file(tmp_path):
    path = tmp_path / "take.mp4"
    write_take(path, 120)
    p = probe(path)
    assert (p.width, p.height, p.n_frames) == (216, 384, 120)
    assert p.fps == pytest.approx(60, abs=0.5)


def test_normalise_keeps_the_clip_after_the_lead_and_builds_the_plate(tmp_path):
    path = tmp_path / "take.mp4"
    write_take(path, (LEAD_SECONDS + CLIP_SECONDS) * FPS)
    take = normalise(path)
    assert take.frames.shape == (CLIP_SECONDS * FPS, HEIGHT, WIDTH, 3)
    assert take.plate.shape == (HEIGHT, WIDTH, 3)
    assert abs(int(take.plate[150, 100, 0]) - 60) < 8
    assert abs(int(take.frames[0, 150, 100, 0]) - 220) < 20


def test_a_short_take_is_refused(tmp_path):
    path = tmp_path / "take.mp4"
    write_take(path, 120)
    with pytest.raises(ValueError, match="long"):
        normalise(path)


def test_a_phone_rotation_of_minus_90_turns_the_image_clockwise():
    image = np.zeros((2, 3), dtype=np.uint8)
    image[0, 0] = 1
    turned = upright(image, -90)
    assert turned.shape == (3, 2)
    assert turned[0, 1] == 1


def test_a_half_turn_is_the_same_in_both_directions():
    image = np.arange(6, dtype=np.uint8).reshape(2, 3)
    assert np.array_equal(upright(image, 180), upright(image, -180))
    assert np.array_equal(upright(image, 0), image)
