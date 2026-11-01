"""T1 with the flows of the GPU: SEA-RAFT for the mask, RAFT to score, RIFE to beat."""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "av"], check=True)

import numpy as np
import torch
import torch.nn.functional as F
from safetensors import safe_open
from safetensors.torch import load_file
from torchvision.models.optical_flow import Raft_Large_Weights, raft_large

from continuum.metrics import select_beta_frames
from continuum.synth import BAR_HEIGHT, BAR_TOP, BAR_WIDTH, bar_left, toy_take
from continuum.t1 import score_clip, verdict

WORK = Path("/kaggle/working")
RIFE_URL, RIFE_SHA = (
    "https://github.com/hzwer/Practical-RIFE",
    "bbfd2ea90910789a860ea3e2b32a240cd577b75e",
)
SEA_RAFT_URL, SEA_RAFT_SHA = (
    "https://github.com/princeton-vl/SEA-RAFT",
    "9137517ba24e628442aec097d3afe71d03503b75",
)
SEA_RAFT_SCALE = 0

torch.set_grad_enabled(False)
torch.manual_seed(0)
device = torch.device("cuda")


def clone(url: str, sha: str) -> Path:
    path = Path("/tmp") / url.rsplit("/", 1)[1]
    subprocess.run(["git", "clone", "--quiet", url, str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "checkout", "--quiet", sha], check=True)
    return path


def weights(relative: str) -> Path:
    return next(p for p in Path("/kaggle/input").rglob(relative))


def tensor(image: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(np.asarray(image, dtype=np.float32)).permute(2, 0, 1)[None].to(device)


class Rife:
    def __init__(self) -> None:
        repo = clone(RIFE_URL, RIFE_SHA)
        shutil.copytree(weights("train_log/flownet.pkl").parent, repo / "train_log")
        sys.path.insert(0, str(repo))
        from train_log.RIFE_HDv3 import Model

        self.model = Model()
        self.model.load_model(str(repo / "train_log"), -1)
        self.model.eval()
        self.model.device()

    def __call__(self, before: np.ndarray, after: np.ndarray, tau) -> np.ndarray:
        a, b = tensor(before) / 255, tensor(after) / 255
        h, w = a.shape[2:]
        padding = (0, ((w - 1) // 64 + 1) * 64 - w, 0, ((h - 1) // 64 + 1) * 64 - h)
        output = self.model.inference(F.pad(a, padding), F.pad(b, padding), float(tau), 1.0)
        image = (output[0, :, :h, :w].clamp(0, 1) * 255).permute(1, 2, 0)
        return image.cpu().numpy()


class SeaRaft:
    def __init__(self) -> None:
        repo = clone(SEA_RAFT_URL, SEA_RAFT_SHA)
        sys.path.insert(0, str(repo / "core"))
        from raft import RAFT

        config = json.loads((repo / "config/eval/spring-M.json").read_text(encoding="utf-8"))
        self.args = SimpleNamespace(**config)
        self.model = RAFT(self.args)
        path = weights("sea-raft/model.safetensors")
        with safe_open(path, framework="pt") as f:
            aliases = set(f.metadata())
        # The file stores each shared layer once and lists its other names as aliases.
        result = self.model.load_state_dict(load_file(path), strict=False)
        if result.unexpected_keys or set(result.missing_keys) - aliases:
            raise RuntimeError(f"SEA-RAFT weights do not fit the model: {result}")
        self.model.to(device).eval()

    def __call__(self, before: np.ndarray, after: np.ndarray, scale: int = SEA_RAFT_SCALE):
        size = 2.0**scale
        a = F.interpolate(tensor(before), scale_factor=size, mode="bilinear")
        b = F.interpolate(tensor(after), scale_factor=size, mode="bilinear")
        flow = self.model(a, b, iters=self.args.iters, test_mode=True)["flow"][-1]
        flow = F.interpolate(flow, scale_factor=1 / size, mode="bilinear") / size
        return flow[0].norm(dim=0).cpu().numpy()


class ScoreFlow:
    """RAFT of torchvision: it enters no method, so it can judge them."""

    def __init__(self) -> None:
        self.model = raft_large(weights=Raft_Large_Weights.DEFAULT).to(device).eval()

    def __call__(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        a, b = tensor(before) / 127.5 - 1, tensor(after) / 127.5 - 1
        return self.model(a, b)[-1][0].permute(1, 2, 0).cpu().numpy()


def lock() -> dict:
    return {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "rife": RIFE_SHA,
        "sea_raft": SEA_RAFT_SHA,
        "packages": subprocess.run(
            [sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True
        ).stdout.splitlines(),
    }


def flow_check(sea_raft: SeaRaft, take) -> dict:
    """On the toy the bar moves 6 px between training frames: which scale finds it?"""
    a, b = take.frames[100], take.frames[102]
    rows, x = slice(BAR_TOP, BAR_TOP + BAR_HEIGHT), bar_left(100)
    return {str(s): float(np.median(sea_raft(a, b, s)[rows, x : x + BAR_WIDTH])) for s in (0, 1)}


def main() -> None:
    started = time.perf_counter()
    rife, sea_raft, score_flow = Rife(), SeaRaft(), ScoreFlow()
    take = toy_take()
    checks = flow_check(sea_raft, take)
    rows = [score_clip("toy", take, rife, sea_raft, score_flow)]
    energies = {row["clip"]: {int(k): v for k, v in row.pop("energy").items()} for row in rows}
    report = {
        "commit": COMMIT,  # noqa: F821
        "provisional": True,
        "seed": 0,
        "gpu": torch.cuda.get_device_name(0),
        "seconds": round(time.perf_counter() - started, 1),
        "peak_memory_gb": round(torch.cuda.max_memory_allocated() / 1024**3, 2),
        "flow_check_median_px": checks,
        "rows": rows,
        "verdict": verdict(rows),
        "beta_frames": select_beta_frames(energies),
    }
    (WORK / "t1.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (WORK / "lock.json").write_text(json.dumps(lock(), indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
