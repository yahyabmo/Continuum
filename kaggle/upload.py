"""Send the named raw takes and data/raw/clips.json to the private dataset read by T1.

Only the takes named on the command line leave this machine: python kaggle/upload.py C1 plaque1
Another folder than data/raw can be given first: python kaggle/upload.py --from DIR C1
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DATASET = "yahyabelhajjam/continuum-clips"
KAGGLE = Path(sys.executable).with_name("kaggle")


def takes(raw: Path, names: list[str]) -> list[Path]:
    found = []
    for name in names:
        matches = [p for p in raw.glob(f"{name}.*") if p.suffix.lower() in (".mp4", ".mov")]
        if len(matches) != 1:
            raise SystemExit(f"expected one take named {name} in {raw}, found {len(matches)}")
        found.append(matches[0])
    return found


def exists() -> bool:
    status = [KAGGLE, "datasets", "status", DATASET]
    return subprocess.run(status, capture_output=True, text=True).returncode == 0


def main() -> None:
    args = sys.argv[1:]
    raw = RAW
    if args[:1] == ["--from"]:
        raw, args = Path(args[1]), args[2:]
    files = takes(raw, args) + [raw / "clips.json"]
    with tempfile.TemporaryDirectory() as tmp:
        for path in files:
            shutil.copy2(path, tmp)
        meta = {"title": "continuum-clips", "id": DATASET, "licenses": [{"name": "other"}]}
        (Path(tmp) / "dataset-metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        if exists():
            command = ["datasets", "version", "-p", tmp, "-m", " ".join(args)]
        else:
            command = ["datasets", "create", "-p", tmp]
        subprocess.run([KAGGLE, *command], check=True)


if __name__ == "__main__":
    main()
