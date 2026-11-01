"""Push a kernel with the continuum package inlined, so that it runs this checkout."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KAGGLE = Path(sys.executable).with_name("kaggle")

HEADER = """import pathlib as _pathlib, sys as _sys
_package = _pathlib.Path("/tmp/bundle/continuum")
_package.mkdir(parents=True, exist_ok=True)
for _name, _text in {sources!r}.items():
    (_package / _name).write_text(_text)
_sys.path.insert(0, "/tmp/bundle")
COMMIT = {commit!r}

"""


def commit() -> str:
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "continuum"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    return head + "+local" if dirty else head


def main() -> None:
    name, seconds = sys.argv[1], sys.argv[2]
    folder = ROOT / "kaggle" / name
    meta = json.loads((folder / "kernel-metadata.json").read_text(encoding="utf-8"))
    code = (folder / meta["code_file"]).read_text(encoding="utf-8")
    sources = {
        p.name: p.read_text(encoding="utf-8") for p in sorted((ROOT / "continuum").glob("*.py"))
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "kernel-metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        text = HEADER.format(sources=sources, commit=commit()) + code
        (out / meta["code_file"]).write_text(text, encoding="utf-8")
        subprocess.run([KAGGLE, "kernels", "push", "-p", tmp, "-t", seconds], check=True)


if __name__ == "__main__":
    main()
