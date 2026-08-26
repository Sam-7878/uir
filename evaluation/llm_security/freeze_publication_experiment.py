"""Capture the immutable environment and data identity before production runs."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from llm_trust.inference.phi35_transformers import DEFAULT_MODEL_PATH
from .audit_publication_datasets import DEFAULT_DEV, DEFAULT_HELDOUT


ROOT = Path(__file__).resolve().parents[2]


def command(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    status = command("git", "status", "--porcelain")
    if status and not args.allow_dirty:
        raise RuntimeError("freeze requires a clean committed worktree")
    snapshots = sorted(DEFAULT_MODEL_PATH.iterdir())
    if not snapshots:
        raise FileNotFoundError(DEFAULT_MODEL_PATH)
    snapshot = snapshots[-1]
    try:
        import torch
        torch_version = torch.__version__; cuda_runtime = torch.version.cuda
    except Exception as exc:
        raise RuntimeError(f"PyTorch runtime unavailable: {exc}") from exc
    gpu = command("nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader")
    manifest = {
        "schema_version": "uir-publication-manifest-v2", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": command("git", "rev-parse", "HEAD"), "git_status": status,
        "dataset_dev_path": str(DEFAULT_DEV), "dataset_dev_sha256": sha256(DEFAULT_DEV),
        "dataset_heldout_path": str(DEFAULT_HELDOUT), "dataset_heldout_sha256": sha256(DEFAULT_HELDOUT),
        "model": "microsoft/Phi-3.5-mini-instruct", "model_revision": snapshot.name, "model_path": str(snapshot),
        "quantization": "bitsandbytes NF4 double-quant", "attention": "eager", "use_cache": True,
        "decoding": {"do_sample": False, "temperature": 0.0, "top_p": None, "max_input_tokens": 2048, "max_new_tokens": 128},
        "runs": 3, "seed_base": 20260826,
        "runtime": {
            "python": sys.version.split()[0], "pytorch": torch_version, "transformers": package_version("transformers"),
            "bitsandbytes": package_version("bitsandbytes"), "cuda_runtime": cuda_runtime, "gpu": gpu,
            "os": platform.platform(), "kernel": platform.release(), "wsl": Path("/proc/version").read_text(encoding="utf-8").strip(),
        },
        "failure_policy": {"tolerance": 0.0, "categories": ["MODEL_ERROR", "CUDA_OOM", "TIMEOUT", "INVALID_OUTPUT", "BACKEND_ERROR"]},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"git_commit": manifest["git_commit"], "model_revision": manifest["model_revision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
