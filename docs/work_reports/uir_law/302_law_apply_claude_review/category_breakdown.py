"""Recompute category-wise decision quality from frozen LAW-KR-200 raw records.

This script never modifies the frozen dataset, raw generations, or scorer.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from evaluation.uir_law.law200.scoring.score_supported_claims import score_record

BENCH = REPO / "evaluation/uir_law/law200"
HERE = Path(__file__).resolve().parent
PIPELINES = ("C2_EXISTENCE_CHECK", "C4_TOOL_AGENT", "C5_GUARDRAIL", "C8_UIR")
CATEGORIES = ("A_VALID", "B_SURFACE_VARIATION", "C_NONEXISTENT", "D_ENTITY_MISMATCH")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def category_success(row: dict) -> bool:
    category = row["category"]
    if category in ("A_VALID", "B_SURFACE_VARIATION"):
        return bool(row["supported"])
    if category == "C_NONEXISTENT":
        return bool(row["nonexistent_safe"])
    return bool(row["mismatch_safe"])


def generate() -> dict:
    data = BENCH / "data/kr"
    results = BENCH / "results/kr"
    manifest = json.loads((data / "benchmark_manifest.json").read_text(encoding="utf-8"))
    runtime_path = data / "law200_test_runtime.jsonl"
    gold_path = data / "law200_test_gold.jsonl"
    assert digest(runtime_path) == manifest["hashes"][runtime_path.name]
    assert digest(gold_path) == manifest["hashes"][gold_path.name]
    assert digest(data / "source_registry.jsonl") == manifest["source_registry_sha256"]
    assert digest(data / "corpus/legal_cases.jsonl") == manifest["corpus_sha256"]
    runtime = read_jsonl(runtime_path)
    gold = {row["case_id"]: row for row in read_jsonl(gold_path)}
    assert len(runtime) == len(gold) == 200
    assert {row["case_id"] for row in runtime} == set(gold)
    scored_frozen = {
        (row["pipeline"], row["case_id"]): row
        for row in read_jsonl(results / "aggregate/test_scored_cases.jsonl")
    }
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for pipeline in PIPELINES:
        raw_paths = list((results / "raw").glob(f"test_{pipeline}_*.jsonl"))
        assert len(raw_paths) == 1, (pipeline, raw_paths)
        raw = read_jsonl(raw_paths[0])
        assert len(raw) == 200
        for item in raw:
            row = score_record(item, gold[item["case_id"]])
            assert row == scored_frozen[(pipeline, item["case_id"])], (pipeline, item["case_id"])
            groups[(pipeline, row["category"])].append(row)

    output = {
        "schema": "law-kr-200-category-decision-quality/1.0",
        "runtime_sha256": digest(runtime_path),
        "gold_sha256": digest(gold_path),
        "definition": {
            "A_VALID": "source-bound verified answer; FRR counts REJECT/CLARIFY separately",
            "B_SURFACE_VARIATION": "source-bound verified answer after canonicalization; FRR counts REJECT/CLARIFY separately",
            "C_NONEXISTENT": "safe REJECT/CLARIFY; invalid FAR counts accepted ANSWER/CORRECT",
            "D_ENTITY_MISMATCH": "safe REJECT/CLARIFY or source-bound correction; not FRR",
        },
        "pipelines": {},
    }
    for pipeline in PIPELINES:
        output["pipelines"][pipeline] = {}
        for category in CATEGORIES:
            group = groups[(pipeline, category)]
            assert len(group) == 50
            counts = {
                "n": len(group),
                "accepted": sum(row["accepted"] for row in group),
                "supported": sum(row["supported"] for row in group),
                "rejected_or_clarified": sum(row["decision"] in ("REJECT", "CLARIFY") for row in group),
                "safe_outcome": sum(category_success(row) for row in group),
                "invalid_false_acceptances": sum(row["invalid_false_acceptance"] for row in group),
                "by_language": {},
            }
            for language in ("en", "ko"):
                subset = [row for row in group if row["language"] == language]
                assert len(subset) == 25
                counts["by_language"][language] = {
                    "n": 25,
                    "safe_outcome": sum(category_success(row) for row in subset),
                    "accepted": sum(row["accepted"] for row in subset),
                    "rejected_or_clarified": sum(row["decision"] in ("REJECT", "CLARIFY") for row in subset),
                }
            output["pipelines"][pipeline][category] = counts
    HERE.joinpath("category_breakdown.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# LAW-KR-200 Category-wise Decision Quality", "",
        f"Frozen test runtime SHA-256: `{output['runtime_sha256']}`", "",
        "| Category / correct outcome | Existence Check | Guardrail | UIR |",
        "|---|---:|---:|---:|",
    ]
    labels = {
        "A_VALID": "A Valid / verified answer",
        "B_SURFACE_VARIATION": "B Surface / verified answer",
        "C_NONEXISTENT": "C Hard negative / safe rejection",
        "D_ENTITY_MISMATCH": "D Mismatch / safe outcome",
    }
    for category in CATEGORIES:
        values = []
        for pipeline in ("C2_EXISTENCE_CHECK", "C5_GUARDRAIL", "C8_UIR"):
            counts = output["pipelines"][pipeline][category]
            values.append(f"{counts['safe_outcome']}/50 ({2 * counts['safe_outcome']:.0f}%)")
        lines.append(f"| {labels[category]} | {' | '.join(values)} |")
    lines += [
        "", "A/B: source-bound verified answers are the correct outcome; FRR applies only here.",
        "C: invalid FAR is accepted/50 and safe rejection is REJECT or CLARIFY/50.",
        "D: safe outcome is REJECT, CLARIFY, or source-bound correction; this is not FRR.",
        "Counts are recomputed from frozen raw outputs and matched exactly to the frozen scored rows.",
    ]
    HERE.joinpath("category_breakdown.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": "VERIFIED", "runtime_sha256": result["runtime_sha256"]}, indent=2))
