#!/usr/bin/env python3
"""Validate dual-human review, calculate field agreement, adjudicate, and freeze v2."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("source_text_valid", "language_valid", "intent_valid", "target_valid", "conditions_valid",
          "policy_valid", "outcome_valid", "claims_valid")
ALLOWED = {"1", "0", "NA"}
FIELD_TARGET = {"source_text_valid": "source_text", "language_valid": "language", "intent_valid": "expected_intent",
                "target_valid": "expected_target", "conditions_valid": "expected_conditions",
                "policy_valid": "expected_policy_decision", "outcome_valid": "expected_outcome",
                "claims_valid": "required_claims"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parser_hash() -> str:
    paths = [*sorted((ROOT / "crates/poa-uir/src/frontend").glob("*.rs")),
             ROOT / "crates/poa-uir/src/resolution.rs", ROOT / "crates/poa-uir/src/output_contract.rs"]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def automated_validate(rows: list[dict]) -> None:
    required = {"case_id", "category", "language", "source_text", "expected_intent", "expected_target",
                "expected_conditions", "expected_policy_decision", "expected_outcome", "required_claims", "verified_facts"}
    if len(rows) != 1200 or len({r["case_id"] for r in rows}) != len(rows):
        raise ValueError("candidate must contain 1,200 unique cases")
    if Counter(r["language"] for r in rows) != {"ko": 600, "en": 600}:
        raise ValueError("candidate must be KO/EN balanced")
    for row in rows:
        missing = required - row.keys()
        if missing or not row["source_text"].strip() or row["language"] not in {"ko", "en"}:
            raise ValueError(f"invalid candidate {row.get('case_id')}: missing={sorted(missing)}")
    pairs: dict[str, list[dict]] = {}
    for row in rows:
        if row["category"] == "parallel_semantic": pairs.setdefault(row.get("pair_id", ""), []).append(row)
    if len(pairs) != 200 or "" in pairs:
        raise ValueError("parallel_semantic must define 200 explicit KO/EN pairs")
    for pair_id, pair in pairs.items():
        comparable = lambda r: (r["expected_intent"], r["expected_target"], r["expected_conditions"],
                                r["expected_policy_decision"], r["expected_outcome"], r["required_claims"])
        if len(pair) != 2 or {r["language"] for r in pair} != {"ko", "en"} or comparable(pair[0]) != comparable(pair[1]):
            raise ValueError(f"invalid parallel pair: {pair_id}")


def kappa(left: list[str], right: list[str]) -> tuple[float, float]:
    raw = sum(a == b for a, b in zip(left, right)) / len(left)
    labels = sorted(ALLOWED); expected = sum((left.count(v) / len(left)) * (right.count(v) / len(right)) for v in labels)
    return raw, ((raw - expected) / (1 - expected) if expected < 1 else 1.0)


def reviewed(rows: list[dict]) -> dict[str, dict]:
    return {r["case_id"]: r for r in rows if all(r.get(field, "").strip().upper() in ALLOWED for field in FIELDS)}


def review_evidence(candidate: list[dict], review_dir: Path, out: Path) -> tuple[set[str], dict[tuple[str, str], dict]]:
    reviews = [read_csv(review_dir / f"review_R{i}.csv") for i in (1, 2)]
    if {r.get("reviewer_id") for r in reviews[0]} != {"R1"} or {r.get("reviewer_id") for r in reviews[1]} != {"R2"}:
        raise ValueError("reviewer IDs must be the anonymous, distinct IDs R1 and R2")
    indexed = [reviewed(r) for r in reviews]; common = set(indexed[0]) & set(indexed[1])
    if len(common) < 400:
        raise ValueError(f"dual-human review coverage {len(common)}/1200 is below 400")
    by_id = {r["case_id"]: r for r in candidate}; counts = Counter(by_id[c]["category"] for c in common)
    missing_categories = {c for c in {r["category"] for r in candidate} if counts[c] < 30}
    languages = Counter(by_id[c]["language"] for c in common)
    if missing_categories or min(languages.values(), default=0) < len(common) * 0.45:
        raise ValueError(f"review sample is not stratified: categories={sorted(missing_categories)}, languages={languages}")
    agreement = []
    for field in FIELDS:
        left = [indexed[0][c][field].upper() for c in sorted(common)]
        right = [indexed[1][c][field].upper() for c in sorted(common)]
        raw, score = kappa(left, right)
        agreement.append({"field": field, "n": len(common), "raw_agreement": f"{raw:.9f}", "cohens_kappa": f"{score:.9f}"})
    out.mkdir(parents=True, exist_ok=True)
    with (out / "reviewer_agreement.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=agreement[0]); writer.writeheader(); writer.writerows(agreement)
    adjudication = {(r["case_id"], r["field"]): r for r in read_csv(review_dir / "adjudication.csv") if r.get("case_id")}
    for case_id in common:
        for field in FIELDS:
            a, b = indexed[0][case_id][field].upper(), indexed[1][case_id][field].upper()
            if a != b and (case_id, field) not in adjudication:
                raise ValueError(f"unadjudicated disagreement: {case_id}/{field}")
            if a == b == "0" and (case_id, field) not in adjudication:
                raise ValueError(f"agreed-invalid ground truth requires correction: {case_id}/{field}")
    return common, adjudication


def apply_adjudication(rows: list[dict], adjudication: dict[tuple[str, str], dict]) -> list[dict]:
    final = json.loads(json.dumps(rows))
    for row in final:
        for field in FIELDS:
            item = adjudication.get((row["case_id"], field))
            if not item: continue
            value = item["final_value"].strip().upper()
            if value not in ALLOWED or not item["reason"].strip():
                raise ValueError(f"invalid adjudication: {row['case_id']}/{field}")
            if value == "0":
                target = FIELD_TARGET[field]
                original = json.dumps(row[target], ensure_ascii=False, sort_keys=True)
                if item["original_value"].strip() != original or not item["adjudicated_value"].strip():
                    raise ValueError(f"correction audit mismatch: {row['case_id']}/{field}")
                corrected = json.loads(item["adjudicated_value"])
                row[target] = corrected
                if field == "claims_valid" and isinstance(corrected, dict):
                    row["required_claims"] = corrected["required_claims"]; row["verified_facts"] = corrected["verified_facts"]
    return final


def campaign_record(row: dict) -> dict:
    commit = row["expected_outcome"] == "COMMIT"
    policy_valid = row["expected_policy_decision"] == "PERMIT" and row["category"] != "adversarial"
    return {**row, "input": row["source_text"], "expected_semantics": {"intent": row["expected_intent"],
            "target": row["expected_target"], "action": "verify_fact",
            "metric": row["required_claims"][0]["attribute"] if row["required_claims"] else "",
            "period": row["required_claims"][0]["period"] if row["required_claims"] else None},
            "expected_claims": row["required_claims"], "context_claims": row["required_claims"],
            "entity_valid": row["category"] != "invalid_entity", "policy_valid": policy_valid,
            "uir_ready": commit, "split": row["category"]}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--candidate", type=Path, default=ROOT / "evaluation/uir_phase3b/candidate_v2_0.jsonl")
    parser.add_argument("--review-dir", type=Path, default=ROOT / "evaluation/uir_phase3b/review")
    parser.add_argument("--out", type=Path, default=ROOT / "results/uir_phase3b"); parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args(); candidate = read_jsonl(args.candidate); automated_validate(candidate)
    try: common, adjudication = review_evidence(candidate, args.review_dir, args.out)
    except ValueError as error:
        print(f"BLOCKED: {error}", file=sys.stderr); return 2
    if not args.freeze: return 0
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if dirty: print("BLOCKED: clean committed worktree required before freeze", file=sys.stderr); return 3
    final = [campaign_record(r) for r in apply_adjudication(candidate, adjudication)]
    content = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in final).encode()
    (args.out / "frozen_test_v2.jsonl").write_bytes(content)
    with (args.out / "adjudication_final.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["case_id", "field", "r1_value", "r2_value", "final_value", "reason", "original_value", "adjudicated_value"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(adjudication.values())
    agreement = read_csv(args.out / "reviewer_agreement.csv")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {"artifact_state": "frozen", "frozen": True, "publication_ready": False,
                "human_review_status": "completed", "reviewer_count": 2,
                "review_coverage": len(common) / len(candidate), "agreement_summary": agreement,
                "adjudicated": True, "case_count": len(final), "dataset_sha256": hashlib.sha256(content).hexdigest(),
                "parser_source_sha256": parser_hash(), "code_commit": commit,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "note": "publication_ready remains false until real-fact and B0-B6 campaign gates pass"}
    (args.out / "FROZEN_TEST_V2_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
