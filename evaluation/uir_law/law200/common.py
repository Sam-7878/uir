"""Shared deterministic I/O and integrity helpers for LAW-200."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
CORPUS_DIR = DATA_DIR / "corpus"
SOURCE_RESPONSE_DIR = DATA_DIR / "source_responses"
RESULTS_DIR = PACKAGE_ROOT / "results"
RAW_DIR = RESULTS_DIR / "raw"
AGGREGATE_DIR = RESULTS_DIR / "aggregate"
TABLES_DIR = RESULTS_DIR / "tables"

SEED = 20260911
FORBIDDEN_RUNTIME_KEYS = {
    "expected_status",
    "is_valid",
    "category",
    "expected_action",
    "gold_case_name",
    "gold_citation",
    "attack_label",
    "oracle_outcome",
    "mutation_type",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: JSON object required")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(canonical_json(row) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={REPO_ROOT}", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def environment_manifest() -> dict[str, Any]:
    return {
        "captured_at": utc_now(),
        "git_commit": git_commit(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "kernel": platform.release(),
        "random_seed": SEED,
        "hardware": hardware_summary(),
    }


def hardware_summary() -> dict[str, Any]:
    """Capture reproducibility hardware without claiming an unobservable backend."""
    cpu_model = platform.processor() or "UNAVAILABLE"
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                cpu_model = line.split(":", 1)[1].strip()
                break
    try:
        memory_bytes = int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        memory_bytes = None
    gpu: dict[str, Any] = {"status": "UNAVAILABLE", "reason": "nvidia-smi_not_found"}
    executable = shutil.which("nvidia-smi")
    if executable:
        probe = subprocess.run(
            [executable, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            gpu = {"status": "DETECTED", "devices": probe.stdout.strip().splitlines()}
        else:
            gpu = {
                "status": "UNAVAILABLE",
                "reason": "nvidia-smi_probe_failed_or_blocked",
                "exit_code": probe.returncode,
            }
    return {
        "cpu_model": cpu_model,
        "logical_cpu_count": os.cpu_count(),
        "visible_memory_bytes": memory_bytes,
        "gpu_probe": gpu,
        "inference_accelerator_observation": "Not recoverable from a post-run probe; no GPU/CPU backend claim is made.",
    }
