import json

from continuum.measure import entries, wait_for_measure


def write(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_an_absent_journal_is_empty(tmp_path):
    assert entries(tmp_path / "web.jsonl") == []


def test_only_a_measure_written_after_the_start_counts(tmp_path):
    path = tmp_path / "web.jsonl"
    write(path, [{"type": "mesure", "p95": 1}, {"type": "volume"}, {"type": "mesure", "p95": 2}])
    assert wait_for_measure(path, skip=1, timeout=1)["p95"] == 2


def test_no_new_measure_gives_up(tmp_path):
    path = tmp_path / "web.jsonl"
    write(path, [{"type": "mesure", "p95": 1}])
    assert wait_for_measure(path, skip=1, timeout=0.6) is None
