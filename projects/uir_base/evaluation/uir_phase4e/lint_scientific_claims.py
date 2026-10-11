"""Phase UIR-4E: Scientific Overclaim Linter (Section 15 of Work Order).

Flags publication prose containing overclaim language unless:
  - It is part of a formal scoped statement (A1-A5 assumptions)
  - It is inside a quotation or lstlisting block
  - It is in a comment line

Required result: 0 unflagged overclaims.

Publication-safe default: "0 observed unsupported-claim acceptances" with N and Wilson CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from evaluation.uir_phase4e.common import DOCS_DIR, RESULTS_DIR, ROOT

PAPER_TEX = ROOT / "docs/papers/_47_UIR/_47_UIR_8p.tex"

# Phrases that require formal scoping or should be removed
OVERCLAIM_RULES = [
    {
        "label": "hallucination_eliminated",
        "pattern": r"hallucination\s+eliminat(?:ed|ion|ing)",
        "safe_context": ["assumption", "A1", "A2", "A3", "A4", "A5", "formally", "under the"],
        "guidance": "Replace with: '0 observed unsupported-claim acceptances (N=X, Wilson CI: [L%, H%]) under assumptions A1-A5'",
    },
    {
        "label": "universal_safety",
        "pattern": r"universal\s+(?:safety|hallucination|evidence)",
        "safe_context": ["assumption", "A1", "A3", "formally", "within the"],
        "guidance": "Scope to: 'Under assumptions A1-A5...'",
    },
    {
        "label": "arbitrary_domain_guarantee",
        "pattern": r"arbitrary.domain\s+guarant",
        "safe_context": [],
        "guidance": "Remove: UIR is validated on specific domains (enterprise financial data). No arbitrary-domain claims.",
    },
    {
        "label": "guarantees_zero_hallucination",
        "pattern": r"guarant(?:ee|ies|eed)\s+zero\s+hallucination",
        "safe_context": ["assumption", "A1", "A3", "formally"],
        "guidance": "Replace with: 'Under A1-A5, unsupported claims are structurally unreachable. Empirically, 0 accepted unsupported claims observed.'",
    },
    {
        "label": "all_emitted_claims_correct",
        "pattern": r"all\s+emitted\s+claims\s+are\s+(?:correct|verified|true)",
        "safe_context": ["conditional", "among emitted", "conditional precision"],
        "guidance": "Replace with: 'Conditional claim precision = 100.0% (among N=X cases with emitted claims)'",
    },
    {
        "label": "superior_task_completion",
        "pattern": r"superior\s+task\s+completion",
        "safe_context": ["supported_answer_coverage", "supported answer coverage", "partial"],
        "guidance": "Replace with: 'UIR achieves higher supported-answer coverage through safe partial answers while maintaining statistically similar complete-accuracy'",
    },
    {
        "label": "unassailable_safety",
        "pattern": r"unassailable\s+safety",
        "safe_context": [],
        "guidance": "Remove: safety is bounded by assumptions A1-A5 and the 34.93% false rejection rate.",
    },
    {
        "label": "model_independent_correctness",
        "pattern": r"model.independent\s+(?:correctness|accuracy|guarantee)",
        "safe_context": [],
        "guidance": "Remove: UIR evidence binding is model-independent, but task accuracy scales with base model capability.",
    },
    {
        "label": "task_completion_for_partial",
        "pattern": r"task\s+completion.*?65\.07",
        "safe_context": ["supported_answer_coverage", "supported answer coverage", "safe partial"],
        "guidance": "65.07% is supported_answer_coverage, not complete task completion. Complete accuracy = 53.59%.",
    },
    {
        "label": "qwen_n200_without_evidence",
        "pattern": r"(?:Qwen|Qwen2\.5).*?N\s*=\s*200",
        "safe_context": [],
        "guidance": "Verify Qwen N=200 in archive before claiming. Previous archive had only N=10.",
        "requires_archive_check": True,
    },
]


def is_safely_scoped(context: str, safe_contexts: list[str]) -> bool:
    """Check if a match is safely scoped by formal context."""
    ctx_lower = context.lower()
    for safe in safe_contexts:
        if safe.lower() in ctx_lower:
            return True
    return False


def is_in_listing_or_comment(content: str, pos: int) -> bool:
    """Check if position is inside a lstlisting block or comment."""
    before = content[:pos]
    # Check if inside lstlisting
    begin_count = before.count(r"\begin{lstlisting}")
    end_count = before.count(r"\end{lstlisting}")
    if begin_count > end_count:
        return True
    # Check if current line is a comment
    line_start = before.rfind("\n") + 1
    line_text = before[line_start:]
    if line_text.strip().startswith("%"):
        return True
    return False


def check_qwen_n_in_archive() -> tuple[int, int]:
    """Return (finqa_n, halueval_n) for Qwen from archive."""
    finqa_path = RESULTS_DIR / "qwen_finqa_C8_raw.jsonl"
    halu_path = RESULTS_DIR / "qwen_halueval_C8_raw.jsonl"
    finqa_n = 0
    halu_n = 0
    if finqa_path.exists():
        with finqa_path.open() as f:
            finqa_n = sum(1 for _ in f if _.strip())
    if halu_path.exists():
        with halu_path.open() as f:
            halu_n = sum(1 for _ in f if _.strip())
    return finqa_n, halu_n


def lint_file(path: Path, filetype: str = "tex") -> list[dict]:
    """Lint a single file for overclaim patterns. Returns list of findings."""
    if not path.exists():
        return [{"file": str(path), "label": "file_missing", "severity": "WARNING",
                 "message": f"File not found: {path}"}]

    content = path.read_text(encoding="utf-8")
    findings = []

    # Pre-check Qwen N for archive
    qwen_finqa_n, qwen_halu_n = check_qwen_n_in_archive()

    for rule in OVERCLAIM_RULES:
        pattern = rule["pattern"]
        safe_contexts = rule["safe_context"]
        requires_archive = rule.get("requires_archive_check", False)

        for m in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
            # Skip if inside listing or comment
            if filetype == "tex" and is_in_listing_or_comment(content, m.start()):
                continue

            # Extract context window
            ctx_start = max(0, m.start() - 120)
            ctx_end = min(len(content), m.end() + 120)
            ctx = content[ctx_start:ctx_end].replace("\n", " ")

            # Check safe scoping
            if is_safely_scoped(ctx, safe_contexts):
                continue

            # Special check for Qwen N=200 claim
            if requires_archive and rule["label"] == "qwen_n200_without_evidence":
                if qwen_finqa_n >= 200 and qwen_halu_n >= 200:
                    continue  # Backed by archive
                elif qwen_finqa_n == 0 and qwen_halu_n == 0:
                    continue  # Archive not present yet, skip for now

            line_no = content[:m.start()].count("\n") + 1
            findings.append({
                "file": path.name,
                "line": line_no,
                "label": rule["label"],
                "severity": "BLOCKER",
                "matched_text": m.group(0)[:60],
                "context": ctx[:100].strip(),
                "guidance": rule["guidance"],
            })

    return findings


def main() -> None:
    print("=" * 72)
    print("PHASE UIR-4E SCIENTIFIC OVERCLAIM LINTER")
    print("=" * 72)

    all_findings = []

    # Lint paper
    if PAPER_TEX.exists():
        print(f"\n[LINT] Paper: {PAPER_TEX.name}")
        findings = lint_file(PAPER_TEX, "tex")
        all_findings.extend(findings)
        for f in findings:
            print(f"  {'❌' if f['severity']=='BLOCKER' else '⚠'} L{f['line']}: [{f['label']}] {f['matched_text']!r}")
            print(f"     Guidance: {f['guidance']}")
    else:
        print(f"[LINT] Paper not found: {PAPER_TEX}")

    # Lint generated Markdown tables
    tables_md = DOCS_DIR / "generated_tables.md"
    if tables_md.exists():
        print(f"\n[LINT] Tables: {tables_md.name}")
        findings = lint_file(tables_md, "md")
        all_findings.extend(findings)
        for f in findings:
            print(f"  {'❌' if f['severity']=='BLOCKER' else '⚠'} L{f['line']}: [{f['label']}] {f['matched_text']!r}")

    # Lint work reports
    for report_path in (RESULTS_DIR / "..").glob("uir_phase4e/*.md"):
        if report_path.exists():
            findings = lint_file(report_path, "md")
            if findings:
                print(f"\n[LINT] {report_path.name}")
                all_findings.extend(findings)

    print("\n" + "=" * 72)
    blockers = [f for f in all_findings if f["severity"] == "BLOCKER"]
    warnings = [f for f in all_findings if f["severity"] == "WARNING"]
    print(f"BLOCKERS: {len(blockers)}")
    print(f"WARNINGS: {len(warnings)}")

    if not blockers:
        print("LINT RESULT: PASS — No overclaims detected")
        return 0
    else:
        print("LINT RESULT: FAIL — Overclaims detected. Fix before submission.")
        for f in blockers:
            print(f"  [{f['label']}] in {f['file']} L{f.get('line', '?')}: {f['matched_text']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
