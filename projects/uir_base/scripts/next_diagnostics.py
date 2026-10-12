"""Post-hoc failure taxonomy, without changing any frozen primary metric."""
from collections import Counter
import json
import re
from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import DEFAULT, jsonl
from projects.uir_base.scripts.next_benchmark_adapter import STEP


def run():
    out = DEFAULT / "finqa_holdout_v2"
    target = out / "posthoc_failure_diagnostics.jsonl"
    if target.exists():
        raise FileExistsError("Keep diagnostics versions distinct")
    records = a.read(out / "raw_requests_responses.jsonl")
    results = {(r["model"], r["condition"], r["case_id"]): r for r in a.read(out / "case_results.jsonl")}
    rows = []
    for record in records:
        response = record["response"] or {}; raw = response.get("message", {}).get("content", "")
        parsed = a.parse(raw); scored = results[record["model"], record["condition"], record["case_id"]]
        markers = list(re.finditer(r"FINAL_ANSWER:\s*([-+]?\d+(?:,\d{3})*(?:\.\d+)?%?|yes|no)", raw, re.I))
        distinct = {m.group(1).lower().replace(",", "") for m in markers}
        literal_status = "PRESENT" if len(distinct) == 1 else "AMBIGUOUS" if distinct else "MISSING"
        program = parsed.get("program") if isinstance(parsed, dict) else None
        rows.append({"case_id": record["case_id"], "model": record["model"], "condition": record["condition"],
            "strict_json": parsed is not None, "completed_answer_marker_status": literal_status,
            "completed_answer_marker_literals": sorted(distinct), "trailing_prose_after_marker": bool(markers and raw[markers[-1].end():].strip()),
            "percent_literal_present": any(v.endswith("%") for v in distinct),
            "program_field_present": isinstance(program, str), "executable_operator_syntax_present": bool(isinstance(program, str) and STEP.search(program)),
            "program_parse_status": "VALIDATED_BY_ADAPTER" if scored.get("execution_status") == "SUCCESS" else "INVALID_OR_UNSUPPORTED" if program is not None else "MISSING",
            "contract_status": scored["contract_status"], "execution_status": scored["execution_status"], "error_reason": scored.get("reason"),
            "frozen_primary_end_to_end_match": scored["end_to_end_match"], "finished": scored["finished"],
            "finish_reason": response.get("done_reason", "NOT_RECORDED"),
            "truncation_status": "CONFIRMED_TOKEN_LIMIT" if response.get("done_reason") == "length" else "NOT_TOKEN_LIMIT" if response.get("done_reason") == "stop" else "UNASSESSABLE",
            "source_ref": "raw_requests_responses.jsonl#" + record["case_id"], "evidence_kind": "historical_reanalysis_of_new_capture",
            "diagnostic_status": "POSTHOC_NOT_NEW_PRIMARY_SCORER", "unsupported_claims": "NOT_MEASURED"})
    jsonl(target, rows)
    a.write_json(out / "posthoc_diagnostic_summary.json", {"N_requests": len(rows), "raw_capture_sha256": a.digest(out / "raw_requests_responses.jsonl"),
        "primary_metrics_unchanged": True, "diagnostic_only": True,
        "program_rejection_reasons": dict(Counter(r["error_reason"] or "NONE" for r in rows if r["condition"] == "C8_ARITHMETIC_CONTRACT")),
        "marker_present_but_adapter_missing": sum(r["completed_answer_marker_status"] == "PRESENT" and results[r["model"], r["condition"], r["case_id"]]["semantic_label_status"] == "MISSING" for r in rows),
        "interpretation": "strict end-marker extraction and percent/benchmark-unit ambiguity confound pure reasoning attribution; program string schema does not enforce DSL syntax",
        "future_changes": "develop on declared development data; new prospective protocol/version and unused holdout required, never quietly rescore or rerun this holdout as confirmatory"})


if __name__ == "__main__":
    run()
