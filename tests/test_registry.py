import json
from pathlib import Path

from continuum.registry import END, NONE, START, render, split, stray_measures, update

ROOT = Path(__file__).resolve().parent.parent


def report(validated: bool) -> dict:
    row = {
        "clip": "C1",
        "scored": 280,
        "psnr_m": {"crossfade": 25.0, "rife": 28.5},
        "epe_m": {"crossfade": 1.5, "rife": 0.9},
        "validated": validated,
    }
    return {
        "commit": "abc1234",
        "rows": [row],
        "verdict": {"validated": 1, "clips": 1, "passed": False},
    }


def test_the_readme_shows_exactly_what_results_holds():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert split(readme)[1] == render(ROOT / "results")


def test_the_readme_has_no_measure_outside_the_results_block():
    assert stray_measures((ROOT / "README.md").read_text(encoding="utf-8")) == []


def test_without_results_nothing_is_published(tmp_path):
    assert render(tmp_path) == NONE


def test_a_t1_report_becomes_a_table(tmp_path):
    (tmp_path / "t1.json").write_text(json.dumps(report(True)))
    table = render(tmp_path)
    assert "| C1 | 280 | 25,00 | 28,50 | 1,50 | 0,90 | oui |" in table
    assert "1 clips validés sur 1" in table
    assert "`abc1234`" in table


def test_a_hand_typed_measure_is_caught():
    text = f"Le champ gagne 3,2 dB.\n{START}\n{NONE}\n{END}\n"
    assert stray_measures(text) == ["3,2 dB"]


def test_update_rewrites_only_the_block(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(f"avant\n{START}\nancien\n{END}\naprès\n", encoding="utf-8")
    update(readme, tmp_path)
    assert readme.read_text(encoding="utf-8") == f"avant\n{START}\n{NONE}\n{END}\naprès\n"
