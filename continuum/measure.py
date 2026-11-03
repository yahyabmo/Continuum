"""Measure the frame times of the page in a real Chrome window, on the GPU of this machine.

The page must be served by the development server (make web), which writes the result
to data/journal/web.jsonl. A window opens on the screen for about fifteen seconds.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

JOURNAL = Path("data/journal/web.jsonl")
SERVER = "http://localhost:5180/"


def entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def wait_for_measure(path: Path, skip: int, timeout: float) -> dict | None:
    """The first measure written after the first skip entries, or None after timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for entry in entries(path)[skip:]:
            if entry.get("type") == "mesure":
                return entry
        time.sleep(0.5)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip", default="demo")
    parser.add_argument("--rendu", default="volume")
    parser.add_argument("--size", default="1280,720", help="window size, such as 1280,720")
    args = parser.parse_args()
    try:
        urllib.request.urlopen(SERVER, timeout=5)
    except urllib.error.URLError:
        raise SystemExit(f"nothing answers on {SERVER}: start the page with make web") from None

    url = f"{SERVER}?clip={args.clip}&rendu={args.rendu}&mesure=1"
    skip = len(entries(JOURNAL))
    with tempfile.TemporaryDirectory() as profile:
        chrome = subprocess.Popen(
            [
                "google-chrome",
                f"--user-data-dir={profile}",
                "--no-first-run",
                "--no-default-browser-check",
                f"--window-size={args.size}",
                f"--app={url}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            result = wait_for_measure(JOURNAL, skip, timeout=90)
        finally:
            os.killpg(chrome.pid, signal.SIGTERM)
            chrome.wait(timeout=10)
    if result is None:
        raise SystemExit("no measure arrived in the journal within 90 s")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
