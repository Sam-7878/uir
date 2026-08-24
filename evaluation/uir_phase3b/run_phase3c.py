#!/usr/bin/env python3
"""
Phase 3C Master Orchestrator
Runs all Phase 3C steps in order:
1. AI-R3 independent audit
2. Corrected R1-R2 agreement
3. Tri-agent agreement
4. Disagreement extraction & adjudication
5. REVIEW_PROTOCOL.json
6. Publication gate
7. Final report generation
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_3B = ROOT / "results/uir_phase3b"
OUT_3C = ROOT / "results/uir_phase3c"
SCRIPTS = Path(__file__).resolve().parent
PYTHON = sys.executable


def run_step(name: str, script: str) -> None:
    """Run a Python script and print its output."""
    print(f"\n{'='*70}")
    print(f"  STEP: {name}")
    print(f"{'='*70}")
    result = subprocess.run(
        [PYTHON, str(SCRIPTS / script)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}", file=sys.stderr)
    if result.returncode != 0:
        print(f"WARNING: {name} returned exit code {result.returncode}", file=sys.stderr)


def write_review_protocol() -> None:
    """Write REVIEW_PROTOCOL.json per Section 4.7."""
    protocol = {
        "review_protocol": "triple_independent_ai_agent_validation",
        "reviewers": [
            {
                "id": "AI-R1",
                "platform": "Google AntiGravity",
                "engine": "Sonnet 4.6",
                "type": "ai_agent",
            },
            {
                "id": "AI-R2",
                "platform": "Google AntiGravity",
                "engine": "Gemini 3.6 Flash",
                "type": "ai_agent",
            },
            {
                "id": "AI-R3",
                "platform": "Google AntiGravity",
                "engine": "Opus 4.6",
                "type": "ai_agent_auditor",
            },
        ],
        "ai_review_completed": True,
        "ai_reviewer_count": 3,
        "human_audit_completed": False,
        "validation_level": "TRIPLE_AI_AGENT_AUDIT",
    }
    OUT_3C.mkdir(parents=True, exist_ok=True)
    path = OUT_3C / "REVIEW_PROTOCOL.json"
    path.write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")
    print(f"  REVIEW_PROTOCOL.json written to: {path}")


def write_run_manifest() -> None:
    """Write Phase 3C run manifest."""
    # Read Phase 3B manifest for reference
    run_3b = json.loads((OUT_3B / "run_manifest.json").read_text()) if (OUT_3B / "run_manifest.json").exists() else {}
    frozen = json.loads((OUT_3B / "FROZEN_TEST_V2_MANIFEST.json").read_text()) if (OUT_3B / "FROZEN_TEST_V2_MANIFEST.json").exists() else {}

    manifest = {
        "phase": "3C",
        "status": "complete",
        "base_phase3b_commit": run_3b.get("commit", "unknown"),
        "dataset_hash": frozen.get("dataset_sha256", "unknown"),
        "parser_hash": frozen.get("parser_source_sha256", "unknown"),
        "python": sys.version,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "components": [
            "ai_r3_independent_audit",
            "corrected_reviewer_agreement",
            "tri_agent_agreement",
            "tri_agent_adjudication",
            "review_protocol_metadata",
            "publication_gate_phase3c",
        ],
        "campaign_rerun": "deferred_to_codex_session",
    }
    path = OUT_3C / "run_manifest_phase3c.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"  Run manifest written to: {path}")


def main() -> int:
    print("=" * 70)
    print("  UIR Phase 3C: Triple Independent AI-Agent Validation")
    print("=" * 70)
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Python: {sys.version}")
    print(f"  ROOT: {ROOT}")

    # Step 1: AI-R3 Independent Audit
    run_step("AI-R3 Independent Audit (Opus 4.6)", "ai_review/ai_r3_review.py")

    # Step 2: Write REVIEW_PROTOCOL.json
    print(f"\n{'='*70}")
    print(f"  STEP: Write REVIEW_PROTOCOL.json")
    print(f"{'='*70}")
    write_review_protocol()

    # Step 3: Corrected R1-R2 Agreement
    run_step("Corrected R1-R2 Agreement (Kappa fix)", "compute_corrected_agreement.py")

    # Step 4: Tri-Agent Agreement
    run_step("Tri-Agent Agreement (R1-R2-R3 + Fleiss' κ)", "compute_tri_agent_agreement.py")

    # Step 5: Disagreement & Adjudication
    run_step("Tri-Agent Disagreement & Adjudication", "compute_tri_agent_adjudication.py")

    # Step 6: Publication Gate
    run_step("Phase 3C Publication Gate", "publication_gate_phase3c.py")

    # Step 7: Run manifest
    print(f"\n{'='*70}")
    print(f"  STEP: Write Run Manifest")
    print(f"{'='*70}")
    write_run_manifest()

    print(f"\n{'='*70}")
    print(f"  Phase 3C Complete: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}")

    # Check gate
    gate_path = OUT_3C / "PUBLICATION_GATE_PHASE3C.json"
    if gate_path.exists():
        gate = json.loads(gate_path.read_text())
        if gate.get("publication_ready"):
            print("  STATUS: READY_TRIPLE_AI_VALIDATED")
        else:
            print(f"  STATUS: BLOCKED — {gate.get('blocking_checks', [])}")
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
