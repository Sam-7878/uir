"""Predeclared all-case endpoints and finite family-paired descriptive analysis."""
from collections import defaultdict
import json
import random
from .common import csvfile, jsonl, load, read, sha, write


def score(out):
    from .experiment import check_freeze, parse_response
    from .baseline import unique_rows
    check_freeze(out)
    manifest = load(out / "fresh_execution_manifest.json")
    if sha(out / "fresh_model_raw.jsonl") != manifest["capture_sha256"] or sha(out / "factorial_saved_outputs.jsonl") != manifest["output_sha256"]:
        raise ValueError("CAPTURE_HASH_MISMATCH")
    rows = read(out / "factorial_saved_outputs.jsonl")
    captures = {r["request_hash"]: r for r in read(out / "fresh_model_raw.jsonl")}
    unique_rows(rows, ("case_id", "condition_id"))
    gold = {r["case_id"]: r for r in read(out / "evaluator_only/query_aware_gold.jsonl")}
    if len(rows) != 16 * len(gold):
        raise ValueError("MISSING_FACTORIAL_CASES")
    records = []
    for row in rows:
        expected = set(gold[row["case_id"]]["expected_ids"])
        selected = set(row["selector_ids"])
        accepted = set(row["approved"]["fact_ids"])
        for field in ("selector_capture_hash", "renderer_capture_hash"):
            key = row[field]
            if key is not None and key not in captures:
                raise ValueError("MISSING_RAW_RESPONSE")
        if row["selector_capture_hash"] is not None:
            raw, error = parse_response(captures[row["selector_capture_hash"]]["response"], "fact_ids")
            if raw != row["selector_ids"] or error != row["selector_error"]:
                raise ValueError("RAW_SELECTOR_REPLAY_MISMATCH")
        records.append({"case_id": row["case_id"], "condition_id": row["condition_id"], "family": row["family"],
                        "raw_selector_exact": selected == expected, "accepted_exact": accepted == expected,
                        "accepted_unsupported_count": len(accepted - expected), "raw_irrelevant_count": len(selected - expected),
                        "catalog_copied": bool(selected) and selected == set(row["all_authorized_catalog_ids"]),
                        "supported_coverage": len(accepted & expected) / len(expected), "invalid_response": bool(row["selector_error"] or row["renderer_error"]),
                        "false_denial": bool(expected) and not accepted, "accepted_output_nonempty": bool(row["approved"]["user_visible_output"]),
                        "whole_output_scope": "CLOSED_FACT_LINES_S1", "native_prose_AUCR": "NOT_MEASURED", "evidence_kind": "DEVELOPMENT"})
    csvfile(out / "query_aware_case_metrics.csv", records)
    grouped = defaultdict(list)
    for record in records:
        grouped[record["condition_id"]].append(record)
    summaries = []
    for condition, entries in sorted(grouped.items()):
        summaries.append({"condition": condition, "N": len(entries), "N_raw_selector_exact": sum(r["raw_selector_exact"] for r in entries),
                          "N_accepted_exact": sum(r["accepted_exact"] for r in entries), "N_false_denial": sum(r["false_denial"] for r in entries),
                          "N_raw_irrelevant": sum(r["raw_irrelevant_count"] > 0 for r in entries), "N_catalog_copied": sum(r["catalog_copied"] for r in entries),
                          "N_invalid": sum(r["invalid_response"] for r in entries), "N_accepted_unsupported": sum(r["accepted_unsupported_count"] > 0 for r in entries),
                          "coverage_mean": sum(r["supported_coverage"] for r in entries) / len(entries), "native_prose_AUCR": "NOT_MEASURED",
                          "scope": "24_SYNTHETIC_DEVELOPMENT_NOT_CONFIRMATORY"})
    csvfile(out / "query_aware_summary.csv", summaries)
    a_name = "UIR_SHARED_TYPED|deterministic|template|non_oracle_pool"
    b_name = "UIR_SHARED_TYPED|SLM|template|non_oracle_pool"
    indexed = {(r["condition_id"], r["case_id"]): r for r in records}
    paired = defaultdict(list)
    for cid in gold:
        a, b = indexed[a_name, cid], indexed[b_name, cid]
        paired[a["family"]].append(int(b["accepted_exact"]) - int(a["accepted_exact"]))
    means = [sum(values)/len(values) for values in paired.values()]
    rng = random.Random(13013)
    samples = sorted(sum(rng.choice(means) for _ in means)/len(means) for _ in range(1000))
    equality = []
    for row in rows:
        if row["representation"] != "UIR_SHARED_TYPED":
            continue
        twin = row["condition_id"].replace("UIR_SHARED_TYPED", "SPECIALIZED_EQUIVALENT")
        counterpart = next(r for r in rows if r["case_id"] == row["case_id"] and r["condition_id"] == twin)
        equality.append(row["approved"] == counterpart["approved"] and row["selector_ids"] == counterpart["selector_ids"])
    write(out / "paired_analysis.json", {"primary_contrast": "SLM-minus-deterministic accepted exact set, template/non-oracle",
          "difference": sum(means)/len(means), "descriptive_family_bootstrap_95_interval": [samples[24], samples[974]],
          "family_clusters": len(means), "N_repr_pairs": len(equality), "N_repr_equal": sum(equality), "multiplicity": "one primary, other cells descriptive",
          "general_equivalence_or_generalization": False, "actual_calls": manifest["actual_model_calls"], "GPU_model_replay_calls": 0})
    print(json.dumps({"summaries": summaries, "representation_pairs_equal": sum(equality)}))
