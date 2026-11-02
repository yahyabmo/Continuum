import json

import numpy as np

from continuum import bench
from continuum.baselines import brackets, crossfade
from continuum.bench import noise_ceiling, score_crossfade, table
from continuum.flow import dis_magnitude
from continuum.metrics import beta, motion_mask, person_mask
from continuum.synth import BAR_HEIGHT, BAR_TOP, BAR_WIDTH, bar_left, toy_take
from continuum.timeaxis import split


def test_crossfade_is_scored_on_every_moving_held_frame():
    take = toy_take(n_frames=60)
    row = score_crossfade("toy", take)
    assert row["held"] == 29
    assert 0 < row["scored"] <= 29
    assert row["psnr_m"] < row["noise_ceiling"]


def test_the_motion_mask_makes_the_task_harder_than_the_full_image():
    row = score_crossfade("toy", toy_take(n_frames=60))
    assert row["psnr_m"] < row["psnr_full"]


def test_a_faster_gesture_is_harder_for_the_crossfade():
    slow = score_crossfade("slow", toy_take(n_frames=60, speed=2.0))
    fast = score_crossfade("fast", toy_take(n_frames=60, speed=6.0))
    assert fast["psnr_m"] < slow["psnr_m"]


def test_the_ceiling_follows_the_sensor_noise():
    assert noise_ceiling(toy_take(n_frames=60, noise=1.0)) > noise_ceiling(
        toy_take(n_frames=60, noise=4.0)
    )


def test_beta_separates_the_crossfade_from_the_truth_on_the_toy():
    take = toy_take(n_frames=60)
    train, held = split(60, 2)
    before, frame, after, tau = brackets(train, held)[10]
    truth = take.frames[frame]
    faded = crossfade(take.frames[before], take.frames[after], tau)
    mask = motion_mask(
        person_mask(truth, take.plate), dis_magnitude(take.frames[before], take.frames[after])
    )
    assert mask.any()
    assert beta(faded, truth, faded, mask) == 1.0
    assert beta(truth.astype(np.float32), truth, faded, mask) == 0.0


def test_the_texture_of_the_bar_moves_with_the_bar():
    frames = toy_take(n_frames=110, noise=0.0).frames
    rows = slice(BAR_TOP, BAR_TOP + BAR_HEIGHT)
    patches = [frames[i, rows, bar_left(i) : bar_left(i) + BAR_WIDTH] for i in (100, 102)]
    assert bar_left(100) != bar_left(102)
    assert np.array_equal(patches[0], patches[1])


def test_the_table_shows_a_missing_value():
    row = {
        "clip": "C1",
        "frames": 600,
        "scored": 0,
        "psnr_m": None,
        "psnr_full": 30.0,
        "noise_ceiling": 40.0,
    }
    assert "n/a" in table([row])


def test_load_take_reads_the_plate_and_the_start_of_a_clip(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(bench, "RAW", tmp_path)
    monkeypatch.setattr(bench, "CLIPS", tmp_path / "clips.json")
    monkeypatch.setattr(bench, "normalise", lambda *args: calls.append(args))
    for name in ("C1", "plaque1", "C2"):
        (tmp_path / f"{name}.mp4").touch()
    (tmp_path / "clips.json").write_text(json.dumps({"C1": {"plate": "plaque1", "start": 4.5}}))
    bench.load_take("C1")
    bench.load_take("C2")
    assert calls == [
        (tmp_path / "C1.mp4", tmp_path / "plaque1.mp4", 4.5),
        (tmp_path / "C2.mp4", None, 3),
    ]
