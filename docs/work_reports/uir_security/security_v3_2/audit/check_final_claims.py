#!/usr/bin/env python3
"""Reject obsolete or overstated claims from the V3.2 submission surfaces."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]

DEFAULT_FILES = (
    REPO / "docs/papers/_47_1_UIR_for_ZTA/_47.1_UIR_ZTA.tex",
    REPO / "docs/papers/_47_1_UIR_for_ZTA/v3_2_evidence.tex",
    REPO / "docs/security_v3_2/HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md",
    REPO / "docs/security_v3_2/ADAPTIVE_ATTACK_PROTOCOL.md",
    REPO / "docs/security_v3_2/AGENTDOJO_PROVENANCE.md",
    REPO / "docs/security_v3_2/BASELINE_FIDELITY_REPORT.md",
    REPO / "docs/security_v3_2/HUMAN_REVIEW_PROTOCOL.md",
    REPO / "docs/security_v3_2/OUTPUT_GUARD_VALIDATION_REPORT.md",
    REPO / "docs/security_v3_2/README_REPRODUCE.md",
)


@dataclass(frozen=True)
class Rule:
    rule_id: str
    pattern: re.Pattern[str]
    message: str


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    line: int
    text: str
    message: str


def rx(value: str) -> re.Pattern[str]:
    return re.compile(value, re.IGNORECASE)


RULES = (
    Rule("stale-n-120", rx(r"\bN\s*=\s*120\b"), "obsolete primary population"),
    Rule("stale-n-240", rx(r"\bN\s*=\s*240\b"), "obsolete primary population"),
    Rule("stale-90-attacks", rx(r"\b90\s+(?:adversarial\s+)?attacks?\b"), "obsolete attack population"),
    Rule("stale-30-benign", rx(r"\b30\s+(?:valid\s+)?benign(?:\s+(?:cases|tasks))?\b"), "obsolete primary benign population"),
    Rule("stale-adaptive-seeds", rx(r"\b30\s+adaptive\s+seeds?\b"), "obsolete total adaptive scale"),
    Rule("stale-adaptive-queries", rx(r"(?<![0-9,])600\s+(?:actual\s+)?adaptive\s+quer(?:y|ies)\b"), "obsolete adaptive query total"),
    Rule("stale-ablation-count", rx(r"\b9\s+(?:full[- ](?:size|population)\s+)?ablation(?:\s+configurations?)?\b"), "obsolete ablation count"),
    Rule("stale-adaptive-rate", rx(r"\b18\.3\s*\\?%"), "obsolete adaptive result"),
    Rule("stale-utility-rate", rx(r"\b88\.3\s*\\?%"), "obsolete utility result"),
    Rule("unsupported-human", rx(r"\bdual[- ]blinded\s+human\b"), "unsupported human-validation claim"),
    Rule("observed-kappa", rx(r"\bCohen(?:'|’)?s\s+(?:\\?\$?\\?kappa|kappa)\b"), "Cohen's kappa presented as V3.2 evidence"),
    Rule("public-agentdojo", rx(r"\bpublic\s+AgentDojo\s+benchmark\b"), "public AgentDojo presented as executed evidence"),
    Rule("camel-superiority", rx(r"HETE\s+outperforms\s+CaMeL"), "unsupported official CaMeL superiority"),
    Rule("progent-superiority", rx(r"HETE\s+outperforms\s+Progent"), "unsupported official Progent superiority"),
    Rule("stale-context-output-pair", rx(r"Context\s+Firewall\s*\+\s*OutputGuard"), "unexecuted final paired ablation"),
    Rule("stale-entity-output-pair", rx(r"Entity\s+Verifier\s*\+\s*OutputGuard"), "unexecuted final paired ablation"),
    Rule("pending-gate", rx(r"Final\s+submission\s+requires\s+the\s+scientific-validity\s+gate"), "closure gate described as pending"),
    Rule("universal-mcr-thesis", rx(r"Architectural\s+Containment\s+Thesis\s*\([^\n]*MCR\s*>"), "MCR > E2E-ASR presented as a universal thesis"),
)


ARCHIVE_MARKERS = rx(r"\b(?:historical|archived|archive|prior\s+V3\.1|obsolete|superseded|pre-final)\b")
NEGATION_MARKERS = rx(
    r"\b(?:no|not|never|without|withdrawn|does\s+not|do\s+not|is\s+not|are\s+not|was\s+not|were\s+not|cannot)\b"
)
AMENDMENT_MARKERS = rx(r"\b(?:amendment|interruption|interrupted|checkpoint|first\s+30)\b")


def is_allowed(rule: Rule, context: str) -> bool:
    """Permit explicit archival, negative-scope, and interruption-history mentions."""
    if ARCHIVE_MARKERS.search(context):
        return True
    if rule.rule_id in {"observed-kappa", "public-agentdojo", "stale-n-240", "stale-n-120"}:
        return bool(NEGATION_MARKERS.search(context))
    if rule.rule_id == "stale-adaptive-seeds":
        return bool(AMENDMENT_MARKERS.search(context))
    if rule.rule_id == "stale-30-benign":
        # Only primary/held-out claims are prohibited; small supplemental suites are valid.
        return not rx(r"\b(?:primary|held[- ]out|population|benchmark)\b").search(context)
    return False


def scan_file(path: Path) -> list[Finding]:
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[Finding] = []
    for index, line in enumerate(lines):
        context = " ".join(lines[max(0, index - 1) : min(len(lines), index + 2)])
        for rule in RULES:
            if rule.pattern.search(line) and not is_allowed(rule, context):
                findings.append(
                    Finding(
                        rule.rule_id,
                        path.relative_to(REPO).as_posix(),
                        index + 1,
                        line.strip(),
                        rule.message,
                    )
                )
    return findings


def resolve_files(values: list[str]) -> list[Path]:
    if not values:
        return list(DEFAULT_FILES)
    files: list[Path] = []
    for value in values:
        path = Path(value)
        if not path.is_absolute():
            path = REPO / path
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.suffix.lower() in {".md", ".tex"}))
        else:
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="Submission files or directories; defaults to canonical sources")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    args = parser.parse_args()
    files = resolve_files(args.paths)
    missing = [str(path) for path in files if not path.is_file()]
    findings = [finding for path in files if path.is_file() for finding in scan_file(path)]
    result = {
        "passed": not findings and not missing,
        "files_scanned": len(files),
        "finding_count": len(findings),
        "missing": missing,
        "findings": [asdict(finding) for finding in findings],
    }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif result["passed"]:
        print(f"PASS: scanned {len(files)} final submission files; 0 stale claims")
    else:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.rule_id}: {finding.text}")
        for path in missing:
            print(f"MISSING: {path}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
