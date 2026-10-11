"""Initialize PHASE4C_PARENT_MANIFEST.json preserving Phase-4C baseline reference."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from evaluation.uir_phase4d.common import P4C_RESULTS_DIR, RESULTS_DIR, ROOT, sha256_file, write_json


def record_manifest() -> None:
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(ROOT), "status", "--short"], text=True).strip()

    tracked_files = [
        "per_case_evidence_actual.jsonl",
        "strong_baseline_summary_actual.csv",
        "PUBLICATION_CONSISTENCY_PHASE4C.md",
        "run_manifest_phase4c.json",
        "stat_safety_actual.csv",
        "stat_utility_actual.csv",
        "stat_latency_actual.csv",
        "GOLD_ACCESS_AUDIT.md",
        "OFFICIAL_BENCHMARK_PROVENANCE.json",
    ]

    records = {}
    for name in tracked_files:
        p = P4C_RESULTS_DIR / name
        if p.exists():
            records[name] = {
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
                "modified_iso": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
            }

    manifest = {
        "phase": "UIR-4D-BASELINE-PRESERVATION",
        "parent_phase": "UIR-4C",
        "parent_status": "AUTHENTIC_EXECUTION_BASELINE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "git_status": status,
        "parent_evidence_directory": str(P4C_RESULTS_DIR.resolve()),
        "parent_files": records,
        "inviolability_assertion": "results/uir_phase4c/ remains strictly read-only and immutable for comparison.",
    }

    out_path = RESULTS_DIR / "PHASE4C_PARENT_MANIFEST.json"
    write_json(out_path, manifest)
    print(f"Parent manifest created successfully: {out_path} ({len(records)} files tracked)")


if __name__ == "__main__":
    record_manifest()
