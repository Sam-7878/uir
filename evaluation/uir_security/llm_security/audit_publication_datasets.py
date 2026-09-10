"""Independent and cross-split audit for frozen publication datasets."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .audit_dataset import load


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEV = ROOT / "evaluation/llm_security/datasets/security_benchmark_v2_development.jsonl"
DEFAULT_HELDOUT = ROOT / "evaluation/llm_security/datasets/security_benchmark_v2_heldout.jsonl"


def _visible_leakage(row: dict[str, Any]) -> bool:
    prompt = str(row.get("prompt", "")).lower()
    # Canary-bearing exfiltration prompts necessarily mention the secret source;
    # leakage here means evaluator-only verdict vocabulary/class identifiers.
    evaluator_terms = {str(row.get("attack_class", "")).lower(), "e2e_attack_succeeded", "model_compromised"}
    return any(term and term in prompt for term in evaluator_terms)


def audit_split(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    prompts = [str(row.get("prompt", "")) for row in rows]
    ids = [str(row.get("case_id", "")) for row in rows]
    benign = [row for row in rows if row.get("attack_class") == "valid_benign"]
    attacks = [row for row in rows if row.get("attack_class") != "valid_benign"]
    fixture_value_mismatches = []
    fixture_citation_mismatches = []
    for row in benign:
        fixtures = row.get("trusted_evidence_fixture", [])
        fixture_blob = " ".join(str(item.get("content", "")) for item in fixtures).lower()
        required_values = [str(value).lower() for value in row.get("expected_answer", {}).get("required_values", [])]
        if not required_values or not all(value in fixture_blob for value in required_values):
            fixture_value_mismatches.append(row["case_id"])
        fixture_ids = {str(item.get("source_id", "")) for item in fixtures}
        if not fixture_ids or not fixture_ids.issubset(set(row.get("allowed_evidence_ids", []))):
            fixture_citation_mismatches.append(row["case_id"])
    failures = {
        "duplicate_prompts": len(prompts) - len(set(prompts)),
        "duplicate_case_ids": len(ids) - len(set(ids)),
        "goal_leakage_cases": [row["case_id"] for row in rows if _visible_leakage(row)],
        "benign_without_fixture": [row["case_id"] for row in benign if not row.get("trusted_evidence_fixture")],
        "benign_fixture_value_mismatches": fixture_value_mismatches,
        "benign_fixture_citation_mismatches": fixture_citation_mismatches,
        "attack_without_machine_goal": [row["case_id"] for row in attacks if not isinstance(row.get("attack_goal"), dict) or not row["attack_goal"].get("type")],
    }
    passed = not any(failures.values())
    return {
        "status": "PASS" if passed else "FAIL", "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "case_count": len(rows), "language_counts": dict(Counter(row.get("language") for row in rows)),
        "attack_class_counts": dict(Counter(row.get("attack_class") for row in rows)), "checks": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development", type=Path, default=DEFAULT_DEV)
    parser.add_argument("--heldout", type=Path, default=DEFAULT_HELDOUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    dev, heldout = load(args.development), load(args.heldout)
    development = audit_split(dev, args.development); heldout_result = audit_split(heldout, args.heldout)
    dev_prompts, heldout_prompts = {row["prompt"] for row in dev}, {row["prompt"] for row in heldout}
    dev_ids, heldout_ids = {row["case_id"] for row in dev}, {row["case_id"] for row in heldout}
    # Literal held-out prompt text must not appear in judge source.
    judge_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "evaluation/llm_security/judges").glob("*.py"))
    literal_templates = [row["case_id"] for row in heldout if row["prompt"] in judge_text]
    cross = {
        "status": "PASS", "shared_prompt_count": len(dev_prompts & heldout_prompts),
        "shared_case_id_count": len(dev_ids & heldout_ids), "heldout_prompts_literal_in_judges": literal_templates,
    }
    if cross["shared_prompt_count"] or cross["shared_case_id_count"] or literal_templates:
        cross["status"] = "FAIL"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "dataset_audit_development.json": development,
        "dataset_audit_heldout.json": heldout_result,
        "dataset_cross_split_audit.json": cross,
    }
    for name, result in outputs.items():
        (args.output_dir / name).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    status = "PASS" if all(result["status"] == "PASS" for result in outputs.values()) else "FAIL"
    print(json.dumps({"status": status, "development": len(dev), "heldout": len(heldout)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
