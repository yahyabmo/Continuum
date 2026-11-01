"""Report what a Kaggle GPU session really provides, in run.json."""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request

import torch


def memory_gb() -> float:
    with open("/proc/meminfo", encoding="utf-8") as f:
        kb = int(f.readline().split()[1])
    return round(kb / 1024**2, 1)


def internet() -> bool:
    try:
        urllib.request.urlopen("https://huggingface.co", timeout=10)
    except OSError:
        return False
    return True


def stress(device: str, seconds: float = 20.0) -> dict:
    """Run matrix products on one GPU and report their speed and peak memory."""
    torch.cuda.reset_peak_memory_stats(device)
    a = torch.rand(4096, 4096, device=device)
    steps = 0
    start = time.perf_counter()
    while time.perf_counter() - start < seconds:
        b = a @ a
        torch.cuda.synchronize(device)
        steps += 1
    del b
    return {
        "products_per_second": round(steps / (time.perf_counter() - start), 2),
        "peak_memory_gb": round(torch.cuda.max_memory_allocated(device) / 1024**3, 2),
    }


def main() -> None:
    disk = shutil.disk_usage("/kaggle/working")
    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "cpu_count": os.cpu_count(),
        "memory_gb": memory_gb(),
        "disk_free_gb": round(disk.free / 1024**3, 1),
        "internet": internet(),
        "gpu_count": torch.cuda.device_count(),
        "gpus": [],
    }
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        report["gpus"].append(
            {
                "name": props.name,
                "memory_gb": round(props.total_memory / 1024**3, 2),
                **stress(f"cuda:{i}"),
            }
        )
    if shutil.which("nvidia-smi"):
        report["nvidia_smi"] = subprocess.run(
            ["nvidia-smi", "-L"], capture_output=True, text=True, check=False
        ).stdout.strip()

    with open("/kaggle/working/run.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
