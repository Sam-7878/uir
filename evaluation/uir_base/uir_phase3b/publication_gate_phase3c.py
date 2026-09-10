#!/usr/bin/env python3
"""Phase 3C publication gate with corrected terminology and triple-AI validation checks."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_3B = ROOT / "results/uir_phase3b"
OUT_3C = ROOT / "results/uir_phase3c"


def main() -> int:
    frozen = json.loads((OUT_3B / "FROZEN_TEST_V2_MANIFEST.json").read_text()) if (OUT_3B / "FROZEN_TEST_V2_MANIFEST.json").exists() else {}
    real = json.loads((OUT_3B / "real_fact_subset_manifest.json").read_text()) if (OUT_3B / "real_fact_subset_manifest.json").exists() else {}
    run = json.loads((OUT_3B / "run_manifest.json").read_text()) if (OUT_3B / "run_manifest.json").exists() else {}
    protocol = json.loads((OUT_3C / "REVIEW_PROTOCOL.json").read_text()) if (OUT_3C / "REVIEW_PROTOCOL.json").exists() else {}

    checks = {
        # Corrected: ai_review_completed replaces human_review_completed
        "ai_review_completed": protocol.get("ai_review_completed", False),
        "ai_review_independence_recorded": protocol.get("review_protocol") == "triple_independent_ai_agent_validation",
        "review_statistics_valid": (OUT_3C / "reviewer_agreement_corrected.csv").exists(),
        "frozen_v2": bool(frozen.get("frozen")),
        "dataset_sha256_set": bool(frozen.get("dataset_sha256")),
        "parser_sha256_fixed": bool(frozen.get("parser_source_sha256")),
        "clean_commit": run.get("worktree_dirty") is False,
        "final_slm_campaign_complete": bool(frozen.get("final_slm_campaign_complete")),
        "real_world_fact_subset_complete": real.get("status") == "complete",
        "all_primary_metrics_complete": bool(frozen.get("all_primary_metrics_complete")),
        "statistics_complete": bool(frozen.get("statistics_complete")),
        # Phase 3C specific
        "ai3_audit_completed": (OUT_3C / "AI_R3_AUDIT.csv").exists(),
        "tri_agent_agreement_computed": (OUT_3C / "tri_agent_agreement.csv").exists(),
        "tri_agent_adjudication_completed": (OUT_3C / "tri_agent_adjudication.csv").exists(),
    }

    blocking = [k for k, v in checks.items() if not v]
    publication_ready = len(blocking) == 0
    readiness_level = "READY_TRIPLE_AI_VALIDATED" if publication_ready else "BLOCKED"

    result = {
        "publication_ready": publication_ready,
        "readiness_level": readiness_level,
        "checks": checks,
        "blocking_checks": blocking,
    }

    OUT_3C.mkdir(parents=True, exist_ok=True)
    (OUT_3C / "PUBLICATION_GATE_PHASE3C.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if publication_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
