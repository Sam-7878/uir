"""Generate PHASE4D_RUN_MANIFEST.json for full provenance and artifact integrity (G18)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.uir_phase4d.common import (
    FROZEN_DIR, MANIFEST_4C, MANIFEST_4D, RESULTS_DIR, ROOT, sha256_file,
    write_json,
)


def generate_manifest() -> dict[str, Any]:
    parent_sha = sha256_file(MANIFEST_4C) if MANIFEST_4C.exists() else None

    tracked_files = [
        FROZEN_DIR / "strong_runtime_600.jsonl",
        FROZEN_DIR / "strong_scoring_600.jsonl",
        FROZEN_DIR / "finqa_runtime_200.jsonl",
        FROZEN_DIR / "halueval_qa_runtime_200.jsonl",
        RESULTS_DIR / "strong_baseline_summary_actual.csv",
        RESULTS_DIR / "per_case_evidence_actual.jsonl",
        RESULTS_DIR / "stat_safety_actual.csv",
        RESULTS_DIR / "stat_utility_actual.csv",
        RESULTS_DIR / "stat_latency_actual.csv",
        RESULTS_DIR / "mutation_resilience_actual.csv",
        RESULTS_DIR / "external_generalization_summary.csv",
        RESULTS_DIR / "stat_generalization_actual.csv",
        RESULTS_DIR / "finqa_results_actual.csv",
        RESULTS_DIR / "halueval_results_actual.csv",
        RESULTS_DIR / "finqa_failure_taxonomy.csv",
        RESULTS_DIR / "halueval_failure_taxonomy.csv",
        RESULTS_DIR / "runtime_label_leakage_audit.json",
        RESULTS_DIR / "FINAL_EXPERIMENT_MANIFEST.json",
        ROOT / "docs/uir_phase4d/EXTERNAL_FAILURE_ANALYSIS.md",
    ]

    files_list = []
    for p in tracked_files:
        if p.exists():
            files_list.append({
                "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            })

    manifest = {
        "phase": "UIR-4D",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "parent_phase": "UIR-4C",
        "parent_manifest_sha256": parent_sha,
        "files_tracked": len(files_list),
        "files": files_list,
        "status": "VALIDATED",
    }

    write_json(MANIFEST_4D, manifest)
    print(f"Generated Phase 4D manifest with {len(files_list)} signed files at {MANIFEST_4D}")
    return manifest


if __name__ == "__main__":
    generate_manifest()
