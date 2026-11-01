"""Fetch the model weights once: the other kernels read them from this output."""

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

WORK = Path("/kaggle/working")
RIFE_DRIVE_ID = "1ZKjcbmt1hypiFprJPIKW0Tt0lr_2i7bg"  # Practical-RIFE 4.25
SEA_RAFT_REPO = "MemorySlices/Tartan-C-T-TSKH-spring540x960-M"


def pip(*packages: str) -> None:
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", *packages], check=True)


def fetch_rife() -> None:
    import gdown

    archive = WORK / "rife.zip"
    gdown.download(id=RIFE_DRIVE_ID, output=str(archive), quiet=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(WORK / "rife")
    archive.unlink()


def fetch_sea_raft() -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(SEA_RAFT_REPO, local_dir=WORK / "sea-raft")


def main() -> None:
    pip("gdown", "huggingface_hub")
    fetch_rife()
    fetch_sea_raft()
    files = {
        str(p.relative_to(WORK)): {
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in sorted(WORK.rglob("*"))
        if p.is_file() and ".cache" not in p.parts and p.name != "run.json"
    }
    (WORK / "run.json").write_text(json.dumps(files, indent=2), encoding="utf-8")
    print(json.dumps(files, indent=2))


if __name__ == "__main__":
    main()
