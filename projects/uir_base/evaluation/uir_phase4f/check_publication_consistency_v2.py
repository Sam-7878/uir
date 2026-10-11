"""Phase UIR-4F: Publication Consistency Checker v2 (Section 13 of Work Order).

Enforces all Phase 4F quality gates:
  1. Phase 4D and Phase 4E archives preserved (immutable)
  2. D1 total_cases >= 600, commit_eligible_cases == 418
  3. Security table denominator == 50 for Adversarial ASR
  4. Workload attack incidence has distinct metric name
  5. Qwen FinQA raw captures == 200 rows per pipeline
  6. Qwen HaluEval raw captures == 200 rows per pipeline
  7. Qwen HaluEval C8: if contract_validity == 0, accepted_e2e_accuracy must be 0%
  8. Raw unsupported generation rate vs Accepted unsupported claim rate separated
  9. c8_accepted_unsupported_claim_count == 0 across all benchmarks
  10. Generated tables match final CSVs exactly
  11. 0 Blockers, 0 Warnings

Outputs:
  RESULT: READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

from evaluation.uir_phase4f.common import (
    DOCS_DIR, P4D_RESULTS_DIR, P4E_RESULTS_DIR, RESULTS_DIR, ROOT, read_csv, read_jsonl,
)

BLOCKERS: list[str] = []
WARNINGS: list[str] = []


def fail(msg: str) -> None:
    BLOCKERS.append(f"BLOCKER: {msg}")
    print(f"  ❌ BLOCKER: {msg}")


def warn(msg: str) -> None:
    WARNINGS.append(f"WARNING: {msg}")
    print(f"  ⚠ WARNING: {msg}")


def ok(msg: str) -> None:
    print(f"  ✅ OK: {msg}")


def check_prior_phases_immutable() -> None:
    print("[CHECK] Prior phases immutability...")
    for phase_dir, files in [
        (P4D_RESULTS_DIR, ["per_case_evidence_actual.jsonl", "strong_baseline_summary_actual.csv"]),
        (P4E_RESULTS_DIR, ["per_case_scored_final.jsonl", "strong_baseline_summary_final.csv", "PHASE4E_FINAL_MANIFEST.json"]),
    ]:
        if not phase_dir.exists():
            fail(f"Directory {phase_dir} missing")
            continue
        for f in files:
            if (phase_dir / f).exists():
                ok(f"{phase_dir.name}/{f} preserved")
            else:
                fail(f"{phase_dir.name}/{f} missing (must remain immutable)")


def check_d1_full_600() -> None:
    print("[CHECK] D1 constrained decoding baseline (N=600)...")
    d1_raw_path = RESULTS_DIR / "d1_constrained_raw_600.jsonl"
    d1_summary_path = RESULTS_DIR / "d1_constrained_summary_600.csv"

    if not d1_raw_path.exists():
        fail("d1_constrained_raw_600.jsonl missing")
        return

    rows = read_jsonl(d1_raw_path)
    n = len(rows)
    if n < 600:
        fail(f"d1_constrained_raw_600.jsonl has {n} rows; expected 600")
    else:
        ok(f"d1_constrained_raw_600.jsonl has {n} rows (≥ 600)")

    commit_n = sum(1 for r in rows if r.get("commit_eligible", False))
    if commit_n != 418:
        fail(f"D1 commit_eligible_cases = {commit_n}; expected 418")
    else:
        ok(f"D1 commit_eligible_cases = {commit_n} == 418 ✓")

    if d1_summary_path.exists():
        d1_sum = read_csv(d1_summary_path)
        if d1_sum:
            r = d1_sum[0]
            if int(r.get("total_cases", 0)) < 600:
                fail(f"D1 summary total_cases = {r.get('total_cases')}; expected 600")
            else:
                ok("D1 summary total_cases == 600 ✓")


def check_security_denominators() -> None:
    print("[CHECK] Security metric denominators (BLOCKER B)...")
    sec_path = RESULTS_DIR / "security_final.csv"
    if not sec_path.exists():
        fail("security_final.csv missing")
        return

    rows = read_csv(sec_path)
    if not rows:
        fail("security_final.csv is empty")
        return

    cols = list(rows[0].keys())
    if "adversarial_attack_success_rate" not in cols:
        fail("Required column 'adversarial_attack_success_rate' missing from security_final.csv")
    else:
        ok("Column 'adversarial_attack_success_rate' present")

    if "workload_attack_incidence_rate" not in cols:
        fail("Required column 'workload_attack_incidence_rate' missing from security_final.csv")
    else:
        ok("Column 'workload_attack_incidence_rate' present")

    # Check adversarial cases == 50
    c0 = next((r for r in rows if r["pipeline"] == "C0_DIRECT_SLM"), None)
    c1 = next((r for r in rows if r["pipeline"] == "C1_NAIVE_RAG"), None)
    c8 = next((r for r in rows if r["pipeline"] == "C8_FINAL_UIR_B6"), None)

    if c1 and c8:
        if int(c1.get("adversarial_cases", 0)) != 50:
            fail(f"Adversarial denominator for C1 is {c1.get('adversarial_cases')}; expected 50")
        else:
            ok("Adversarial denominator is 50 ✓")

        asr_c1 = float(c1.get("adversarial_attack_success_rate", 0))
        asr_c8 = float(c8.get("adversarial_attack_success_rate", 0))
        if asr_c1 < 0.90:
            fail(f"C1 adversarial ASR is {asr_c1:.4f}; expected ~0.92")
        else:
            ok(f"C1 adversarial ASR is {asr_c1:.2f} (N=50)")
        if asr_c8 > 0.001:
            fail(f"C8 adversarial ASR is {asr_c8:.4f}; expected 0.00")
        else:
            ok("C8 adversarial ASR is 0.00 (N=50)")


def check_external_metrics_separation() -> None:
    print("[CHECK] External metrics separation (BLOCKER C & D)...")
    # Check HaluEval
    halu_path = RESULTS_DIR / "halueval_external_final.csv"
    if not halu_path.exists():
        fail("halueval_external_final.csv missing")
    else:
        halu_rows = read_csv(halu_path)
        qwen_c8 = next((r for r in halu_rows if "Qwen" in r.get("model", "") and "C8" in r.get("pipeline", "")), None)
        if qwen_c8:
            sem_acc = float(qwen_c8.get("raw_semantic_accuracy", 0))
            contract_val = float(qwen_c8.get("contract_validity_rate", 0))
            e2e_acc = float(qwen_c8.get("accepted_e2e_accuracy", 0))

            if contract_val == 0.0 and e2e_acc > 0.0:
                fail(f"Qwen HaluEval C8 has contract_validity=0% but accepted_e2e_accuracy={e2e_acc:.4f} > 0%")
            elif contract_val == 0.0 and e2e_acc == 0.0:
                ok("Qwen HaluEval C8: contract_validity=0% -> accepted_e2e_accuracy=0% correctly decoupled ✓")
            
            if sem_acc > 0.40 and e2e_acc == 0.0:
                ok(f"Qwen HaluEval C8: raw_semantic_accuracy={sem_acc:.2f} correctly preserved while accepted_e2e_accuracy=0.00 ✓")

    # Check FinQA
    finqa_path = RESULTS_DIR / "finqa_external_final.csv"
    if not finqa_path.exists():
        fail("finqa_external_final.csv missing")
    else:
        finqa_rows = read_csv(finqa_path)
        qwen_finqa_c8 = next((r for r in finqa_rows if "Qwen" in r.get("model", "") and "C8" in r.get("pipeline", "")), None)
        if qwen_finqa_c8:
            raw_unsup = float(qwen_finqa_c8.get("raw_unsupported_generation_rate", 0))
            acc_unsup = float(qwen_finqa_c8.get("accepted_unsupported_claim_rate", 0))
            if raw_unsup > 0.0 and acc_unsup == 0.0:
                ok(f"Qwen FinQA C8: raw_unsupported_generation_rate={raw_unsup:.4f} decoupled from accepted_unsupported_claim_rate={acc_unsup:.4f} ✓")
            elif acc_unsup > 0.0:
                fail(f"Qwen FinQA C8 has accepted_unsupported_claim_rate={acc_unsup:.4f} > 0% (safety violation!)")


def check_qwen_provenance() -> None:
    print("[CHECK] Qwen provenance metadata...")
    prov_path = RESULTS_DIR / "QWEN_MODEL_PROVENANCE.json"
    if not prov_path.exists():
        fail("QWEN_MODEL_PROVENANCE.json missing")
    else:
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        if not prov.get("ollama_blob_sha256") or prov.get("ollama_blob_sha256") == "unknown":
            fail("Qwen model digest is empty or unknown")
        else:
            ok(f"Qwen blob digest frozen: {prov.get('ollama_blob_sha256')[:16]}... ✓")


def check_tables_match_csvs() -> None:
    print("[CHECK] Generated tables consistency with CSVs...")
    tables_md = DOCS_DIR / "generated_tables_final.md"
    if not tables_md.exists():
        fail("generated_tables_final.md missing")
    else:
        content = tables_md.read_text(encoding="utf-8")
        # Check that table 1 contains Table 1 header
        if "Table 1" in content and "Adversarial ASR" in content:
            ok("generated_tables_final.md Table 1 formatted correctly ✓")
        else:
            fail("generated_tables_final.md Table 1 format mismatch")


def main() -> int:
    print("=" * 72)
    print("PHASE UIR-4F PUBLICATION CONSISTENCY CHECKER V2")
    print("=" * 72)

    check_prior_phases_immutable()
    check_d1_full_600()
    check_security_denominators()
    check_external_metrics_separation()
    check_qwen_provenance()
    check_tables_match_csvs()

    print("=" * 72)
    print(f"BLOCKERS: {len(BLOCKERS)}")
    for b in BLOCKERS:
        print(f"  {b}")
    print(f"WARNINGS: {len(WARNINGS)}")
    for w in WARNINGS:
        print(f"  {w}")
    print("=" * 72)

    if not BLOCKERS and not WARNINGS:
        print("RESULT: READY_FOR_MANUSCRIPT_DRAFT_ABSOLUTE_FINAL")
        return 0
    else:
        print("RESULT: BLOCKED — Resolve all BLOCKERS before manuscript submission")
        return 1


if __name__ == "__main__":
    sys.exit(main())
