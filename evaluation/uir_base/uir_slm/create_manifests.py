#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ollama_client import OllamaClient


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results/uir_slm"))
    parser.add_argument("--config", type=Path, default=Path("evaluation/uir_slm/model_config/phi35_ollama.json"))
    parser.add_argument("--frozen-manifest", type=Path, default=Path("evaluation/uir_external/FROZEN_TEST_MANIFEST.json"))
    parser.add_argument("--registry-manifest", type=Path, default=Path("evaluation/uir_external/REGISTRY_MANIFEST.json"))
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    frozen = json.loads(args.frozen_manifest.read_text(encoding="utf-8")); registry = json.loads(args.registry_manifest.read_text(encoding="utf-8"))
    client = OllamaClient(args.config); model = client.show()
    model_manifest = {"configured_model": client.config["model"], "config_sha256": sha256(args.config), "ollama": model}
    run_manifest = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "source_commit": git("rev-parse", "HEAD"), "worktree_clean_at_start": not bool(git("status", "--porcelain")), "platform": platform.platform(), "python": platform.python_version(), "frozen_dataset_sha256": frozen["dataset_sha256"], "registry_sha256": registry["sha256"], "commands": ["cargo run -p poa-uir --bin uir-eval -- <frozen> <uir-records>", "python evaluation/uir_slm/run_slm_campaign.py ...", "python evaluation/uir_slm/aggregate_results.py ..."]}
    (args.out / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.out / "model_manifest.json").write_text(json.dumps(model_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.out / "frozen_test_manifest.json").write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"commit": run_manifest["source_commit"], "clean": run_manifest["worktree_clean_at_start"], "model": client.config["model"]}, sort_keys=True))


if __name__ == "__main__": main()
