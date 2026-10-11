"""Verify capture integrity and independently replay paired AI agreement.

This checks recorded artifacts, not the truth of AI judgments or human validation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import jsonschema

from uir_common.ollama_client import sha256_text
from uir_common.paths import repo_root
from projects.uir_base.scripts.setup_local_models import write_json


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    out = args.run_dir.resolve(); root = repo_root()
    manifest = json.loads((out / "review_manifest.json").read_text(encoding="utf-8"))
    expected_status = "AI_REVIEW_CAPTURE_COMPLETE_NOT_HUMAN_VALIDATION"
    assert manifest["status"] == expected_status
    assert manifest["human_completed"] is False and manifest["W08_human_requirement_satisfied"] is False
    for filename, expected in manifest["output_sha256"].items():
        assert sha(out / filename) == expected, filename
    assert sha(root / "projects/uir_base/scripts/run_local_ai_review.py") == manifest["reviewer_code_sha256"]
    assert sha(root / "src/uir_common/ollama_client.py") == manifest["local_client_code_sha256"]
    assert sha(root / "projects/uir_base/evaluation/uir_phase4d/runtime/uir_compiler.py") == manifest["compiler_sha256"]
    assert sha(root / "projects/uir_base/evaluation/uir_phase4d/runtime/policy_rules.yaml") == manifest["policy_sha256"]
    base = root / "projects/uir_base/results/mdpi_revision_2026_10_11"
    assert sha(base / "annotation_packets/H1_blinded_cases.jsonl") == manifest["packet_sha256"]
    assert sha(out / "review_packets.jsonl") == manifest["review_packets_sha256"]
    mapping = json.loads((out / "case_id_mapping_evaluator_only.json").read_text(encoding="utf-8"))
    packets = {p["case_id"]: p for p in (json.loads(line) for line in (out / "review_packets.jsonl").read_text(encoding="utf-8").splitlines())}
    assert len(mapping) == len(packets) == manifest["N"]
    schema = manifest["schema"]
    fields = [f for f, spec in schema["properties"].items() if "enum" in spec]
    records = {}
    for reviewer, model in manifest["reviewers"].items():
        rows = [json.loads(line) for line in (out / f"{reviewer}_raw_reviews.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(rows) == manifest["N"]
        assert {r["case_id"] for r in rows} == set(mapping.values())
        assert len({r["case_id"] for r in rows}) == len(rows)
        for r in rows:
            assert r["reviewer_type"] == "AI_MODEL_NOT_HUMAN"
            assert r["model"] == model and r["model_digest"] == manifest["models"][reviewer]["digest"]
            assert r["other_reviewer_results_accessible"] is False
            packet = packets[r["blinded_case_id"]]
            assert mapping[r["blinded_case_id"]] == r["case_id"]
            assert r["case_id"] not in json.dumps(packet, ensure_ascii=False)
            payload = {"model": model, "messages": [{"role": "system", "content": manifest["rubric"]},
                       {"role": "user", "content": json.dumps(packet, ensure_ascii=False, sort_keys=True)}],
                       "format": schema, "stream": False, "keep_alive": "10m", "options": manifest["options"]}
            assert sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True)) == r["request_sha256"]
            response = r.get("response")
            valid = False
            if response is not None:
                raw = response.get("message", {}).get("content", "")
                assert sha256_text(raw) == r["raw_content_sha256"]
                try:
                    label = json.loads(raw)
                    jsonschema.validate(label, schema)
                    valid = (response.get("done") is True and response.get("done_reason") == "stop" and
                             (not label["request_quote"] or label["request_quote"] in packet["raw_input"]))
                except (ValueError, TypeError, jsonschema.ValidationError):
                    label = None
                if valid:
                    assert response["model"] == model and response["eval_count"] > 0
                    assert label == r["label"]
            assert valid == r["valid"]
        records[reviewer] = {r["case_id"]: r for r in rows}
    # Count CSV records, not physical lines: explanations can contain newlines.
    with (out / "AI_labels.csv").open(encoding="utf-8", newline="") as source:
        csv_rows = list(csv.DictReader(source))
    assert len(csv_rows) == manifest["N_attempted"]
    assert len({(r["reviewer_id"], r["case_id"]) for r in csv_rows}) == len(csv_rows)
    for row in csv_rows:
        raw_record = records[row["reviewer_id"]][row["case_id"]]
        assert row["reviewer_type"] == "AI_MODEL_NOT_HUMAN"
        assert row["valid"] == str(raw_record["valid"])
        for field in fields:
            assert row[field] == (raw_record["label"][field] if raw_record["valid"] else "")
    stats = json.loads((out / "AI_agreement.json").read_text(encoding="utf-8"))
    for field in fields:
        pairs = [(records["AI_J1"][cid]["label"][field], records["AI_J2"][cid]["label"][field])
                 for cid in mapping.values() if records["AI_J1"][cid]["valid"] and records["AI_J2"][cid]["valid"]]
        n = len(pairs); equal = sum(a == b for a, b in pairs)
        observed = Fraction(equal, n) if n else None
        counts_a = Counter(a for a, _ in pairs); counts_b = Counter(b for _, b in pairs)
        expected = Fraction(sum(counts_a[v] * counts_b[v] for v in set(counts_a) | set(counts_b)), n * n) if n else None
        kappa = (observed - expected) / (1 - expected) if n and expected < 1 else None
        actual = stats["fields"][field]
        assert actual["N_jointly_valid"] == n and actual["N_agree"] == equal
        assert actual["N_missing_or_invalid_pair"] == manifest["N"] - n
        if n:
            assert math.isclose(float(observed), actual["agreement_jointly_valid"], abs_tol=1e-12)
        if kappa is None:
            assert actual["cohen_kappa_jointly_valid"] is None
        else:
            assert math.isclose(float(kappa), actual["cohen_kappa_jointly_valid"], abs_tol=1e-12)
    unresolved = json.loads((out / "AI_unresolved_cases.json").read_text(encoding="utf-8"))
    assert len(unresolved) == manifest["N_unresolved_cases"]
    assert all(r["final_label"] is None for r in unresolved)
    report = {"status": "INTEGRITY_AND_AGREEMENT_REPLAY_PASS_NOT_SEMANTIC_VALIDATION",
              "N_cases": manifest["N"], "N_responses": manifest["N_attempted"], "N_valid": manifest["N_valid"],
              "N_unresolved": len(unresolved), "human_completed": False,
              "review_manifest_sha256": sha(out / "review_manifest.json"), "verifier_sha256": sha(Path(__file__)),
              "checked": ["source/code/output hashes", "full paired case coverage", "isolated prompt reconstruction",
                          "strict schema/quote/finish validity", "raw labels", "exact-rational agreement/kappa replay"]}
    write_json(out / "verification_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
