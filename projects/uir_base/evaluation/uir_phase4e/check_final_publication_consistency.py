"""Phase UIR-4E: Final Publication Consistency Checker (Section 14 of Work Order).

Compares per-case JSONL → aggregate CSVs → statistical CSVs → generated tables → manuscript.
Fails on any mismatch or forbidden terminology (Sections 14, 15 of Work Order).

Required result: 0 blockers, 0 warnings.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from evaluation.uir_phase4e.common import (
    DOCS_DIR, P4D_PER_CASE, RESULTS_DIR, ROOT, read_jsonl,
)

PAPER_TEX = ROOT / "docs/papers/_47_UIR/_47_UIR_8p.tex"
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


def read_csv_dict(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_phase4d_preserved() -> None:
    print("[CHECK] Phase 4D immutability...")
    p4d_dir = ROOT / "results/uir_phase4d"
    required = [
        "per_case_evidence_actual.jsonl",
        "strong_baseline_summary_actual.csv",
        "PHASE4D_RUN_MANIFEST.json",
    ]
    for fname in required:
        if (p4d_dir / fname).exists():
            ok(f"Phase 4D {fname} preserved")
        else:
            fail(f"Phase 4D {fname} missing (must be preserved!)")


def check_rescore_consistency() -> None:
    print("[CHECK] Rescore consistency (per-case JSONL → aggregate CSV)...")
    per_case_path = RESULTS_DIR / "per_case_scored_final.jsonl"
    summary_path = RESULTS_DIR / "strong_baseline_summary_final.csv"

    if not per_case_path.exists():
        fail("per_case_scored_final.jsonl not found — rescore not complete")
        return
    if not summary_path.exists():
        fail("strong_baseline_summary_final.csv not found — rescore not complete")
        return

    rows = read_jsonl(per_case_path)
    summary = read_csv_dict(summary_path)

    # Recompute key metrics from per-case and compare to CSV
    by_pipe: dict[str, list[Any]] = {}
    for r in rows:
        by_pipe.setdefault(r["pipeline"], []).append(r)

    for agg in summary:
        pipe = agg["pipeline"]
        pipe_rows = by_pipe.get(pipe, [])
        if not pipe_rows:
            warn(f"Pipeline {pipe} in summary CSV but not in per-case JSONL")
            continue

        n = len(pipe_rows)
        recomp_unsup = sum(1 for r in pipe_rows if r.get("unsupported_claim", False)) / n
        csv_unsup = float(agg.get("unsupported_claim_accept_rate", 0))
        if abs(recomp_unsup - csv_unsup) > 0.001:
            fail(f"{pipe}: unsupported_claim_accept_rate mismatch: "
                 f"recomputed={recomp_unsup:.4f} vs CSV={csv_unsup:.4f}")
        else:
            ok(f"{pipe}: unsupported_claim_accept_rate={csv_unsup:.4f} consistent")

        commit_rows = [r for r in pipe_rows if r.get("commit_eligible", False)]
        n_commit = len(commit_rows)
        if n_commit > 0:
            recomp_complete = sum(1 for r in commit_rows if r.get("is_complete", False)) / n_commit
            csv_complete = float(agg.get("complete_claim_set_accuracy", 0))
            if abs(recomp_complete - csv_complete) > 0.001:
                fail(f"{pipe}: complete_claim_set_accuracy mismatch: "
                     f"recomputed={recomp_complete:.4f} vs CSV={csv_complete:.4f}")


def check_metric_labels_in_csv() -> None:
    print("[CHECK] Metric label correctness in CSVs...")
    summary_path = RESULTS_DIR / "strong_baseline_summary_final.csv"
    if not summary_path.exists():
        warn("strong_baseline_summary_final.csv not found")
        return

    summary = read_csv_dict(summary_path)
    required_cols = [
        "complete_claim_set_accuracy",
        "supported_answer_coverage",
        "safe_partial_answer_rate",
        "no_verified_answer_rate",
    ]
    if summary:
        cols = list(summary[0].keys())
        for col in required_cols:
            if col in cols:
                ok(f"Metric column '{col}' present")
            else:
                fail(f"Required metric column '{col}' missing from summary CSV")

        if "task_completion" in cols:
            fail("Forbidden column 'task_completion' found in summary CSV — use complete_claim_set_accuracy or supported_answer_coverage")


def check_qwen_n200() -> None:
    print("[CHECK] Qwen N=200 compliance...")
    required = [
        "qwen_finqa_C1_raw.jsonl",
        "qwen_finqa_C8_raw.jsonl",
        "qwen_halueval_C1_raw.jsonl",
        "qwen_halueval_C8_raw.jsonl",
    ]
    for fname in required:
        path = RESULTS_DIR / fname
        if not path.exists():
            fail(f"Qwen raw file missing: {fname}")
            continue
        rows = read_jsonl(path)
        n = len(rows)
        if n < 200:
            fail(f"{fname}: N={n} < 200 — Qwen N=200 claim not supported by archive")
        else:
            ok(f"{fname}: N={n} ≥ 200 ✓")

    # Check external_generalization_final.csv for N claims
    ext_path = RESULTS_DIR / "external_generalization_final.csv"
    if ext_path.exists():
        ext = read_csv_dict(ext_path)
        for r in ext:
            if "Qwen" in r.get("model", "") or "qwen" in r.get("model", ""):
                n = int(r.get("test_cases", 0))
                if n < 200:
                    fail(f"external_generalization_final.csv: Qwen {r['dataset']} N={n} < 200 in summary")


def check_c3_terminology() -> None:
    print("[CHECK] C3 terminology (BLOCKER 8)...")
    # Check paper
    if PAPER_TEX.exists():
        content = PAPER_TEX.read_text(encoding="utf-8")
        forbidden = ["JSON Schema Structured Decoding", "constrained decoding"]
        for phrase in forbidden:
            # Allow if inside \begin{lstlisting} or in comment context
            occ = [m.start() for m in re.finditer(re.escape(phrase), content, re.IGNORECASE)]
            for pos in occ:
                ctx = content[max(0, pos - 50):pos + 50]
                # Skip if inside listing block or comment
                if "lstlisting" in ctx or "%" in ctx[:50]:
                    continue
                fail(f"Paper contains forbidden C3 term '{phrase}' near: '{ctx[:80].strip()}'")

    # Check generated tables
    tables_md = DOCS_DIR / "generated_tables.md"
    if tables_md.exists():
        content = tables_md.read_text(encoding="utf-8")
        if "JSON Schema Structured Decoding" in content:
            fail("generated_tables.md contains forbidden C3 label 'JSON Schema Structured Decoding'")
        else:
            ok("C3 terminology correct in generated_tables.md")


def check_constrained_decoding() -> None:
    print("[CHECK] D1 constrained decoding baseline...")
    d1_path = RESULTS_DIR / "external_constrained_decoding_summary.csv"
    if not d1_path.exists():
        fail("external_constrained_decoding_summary.csv missing — D1 constrained decoding not run")
    else:
        rows = read_csv_dict(d1_path)
        if not rows:
            fail("external_constrained_decoding_summary.csv is empty")
        else:
            r = rows[0]
            pkg = r.get("package", "")
            if "format" not in pkg.lower() and "constrained" not in pkg.lower():
                warn(f"D1 package '{pkg}' may not be a genuine constrained decoding library")
            ok(f"D1 baseline present: {pkg} v{r.get('package_version', 'unknown')}")


def check_overclaims_in_paper() -> None:
    print("[CHECK] Scientific overclaims in paper...")
    if not PAPER_TEX.exists():
        warn("Paper not found for overclaim check")
        return

    content = PAPER_TEX.read_text(encoding="utf-8")
    # Remove comment lines
    content_no_comments = "\n".join(
        line for line in content.splitlines()
        if not line.strip().startswith("%")
    )

    overclaim_patterns = [
        ("universal hallucination elimination", r"universal hallucination eliminat"),
        ("arbitrary-domain guarantee", r"arbitrary.domain guarant"),
        ("guarantees zero hallucination", r"guarantees? zero hallucination"),
        ("all emitted claims are correct", r"all emitted claims are correct"),
        ("unassailable safety", r"unassailable safety"),
    ]
    for label, pattern in overclaim_patterns:
        matches = list(re.finditer(pattern, content_no_comments, re.IGNORECASE))
        for m in matches:
            ctx = content_no_comments[max(0, m.start()-40):m.start()+60].strip()
            # Skip if inside formal scope
            if "A1" in ctx or "assumption" in ctx.lower() or "formally" in ctx.lower():
                ok(f"Scoped overclaim '{label}' — in formal context, acceptable")
            else:
                fail(f"Unscoped overclaim in paper: '{label}' at: '{ctx[:80]}'")

    ok("Overclaim check complete")


def check_manuscript_numbers() -> None:
    print("[CHECK] Key manuscript numbers vs corrected CSVs...")
    summary_path = RESULTS_DIR / "strong_baseline_summary_final.csv"
    if not summary_path.exists():
        warn("Summary CSV not ready — skipping manuscript number check")
        return

    summary = read_csv_dict(summary_path)
    c8 = next((r for r in summary if "C8" in r.get("pipeline", "")), None)
    c1 = next((r for r in summary if "C1" in r.get("pipeline", "")), None)
    if not c8 or not c1:
        warn("C8 or C1 not found in summary CSV")
        return

    if not PAPER_TEX.exists():
        return

    content = PAPER_TEX.read_text(encoding="utf-8")

    # Check C8 unsupported should be 0.00%
    c8_unsup = float(c8.get("unsupported_claim_accept_rate", 0))
    if c8_unsup > 0.001:
        fail(f"C8 unsupported_claim_accept_rate={c8_unsup:.4f} should be 0.0")
    else:
        ok(f"C8 unsupported_claim_accept_rate=0.00% verified")

    # Check that paper no longer claims "+11.96% task completion superiority"
    if "+11.96" in content and "task completion" in content:
        # Check if properly scoped
        idx = content.find("+11.96")
        ctx = content[max(0, idx-100):idx+150]
        if "supported_answer_coverage" not in ctx and "supported answer coverage" not in ctx.lower():
            fail("Paper contains '+11.96%' but may be mislabeled as 'task completion' rather than 'supported_answer_coverage'")
    else:
        ok("No mislabeled +11.96% task completion in paper")

    # Check Qwen N: paper should not claim Qwen N=200 unless actually N=200
    qwen_finqa_path = RESULTS_DIR / "qwen_finqa_C8_raw.jsonl"
    if qwen_finqa_path.exists():
        qwen_n = len(read_jsonl(qwen_finqa_path))
        if qwen_n < 200 and "N=200" in content and "HaluEval" in content:
            fail(f"Paper claims Qwen N=200 but archive has only N={qwen_n}")


def main() -> None:
    print("=" * 72)
    print("PHASE UIR-4E PUBLICATION CONSISTENCY CHECK")
    print("=" * 72)

    check_phase4d_preserved()
    check_rescore_consistency()
    check_metric_labels_in_csv()
    check_qwen_n200()
    check_c3_terminology()
    check_constrained_decoding()
    check_overclaims_in_paper()
    check_manuscript_numbers()

    print("=" * 72)
    print(f"BLOCKERS: {len(BLOCKERS)}")
    for b in BLOCKERS:
        print(f"  {b}")
    print(f"WARNINGS: {len(WARNINGS)}")
    for w in WARNINGS:
        print(f"  {w}")
    print("=" * 72)

    if not BLOCKERS and not WARNINGS:
        print("RESULT: READY_FOR_MANUSCRIPT_DRAFT_FINAL")
        return 0
    elif not BLOCKERS:
        print("RESULT: WARNINGS_ONLY — Review and resolve warnings before submission")
        return 0
    else:
        print("RESULT: BLOCKED — Resolve all BLOCKERS before manuscript submission")
        return 1


if __name__ == "__main__":
    sys.exit(main())
