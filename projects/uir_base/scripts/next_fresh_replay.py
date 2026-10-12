"""Offline replay of captured matched candidates, never fresh model inference."""
from pathlib import Path
import json
from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import DEFAULT


def replay(root=DEFAULT, out=None):
    from evaluation.uir_phase4d.pipelines import build_internal_request
    source = root / "fresh_matched"
    protocol = json.loads((root / "fresh_matched_protocol.json").read_text())
    manifest = json.loads((source / "fresh_run_manifest.json").read_text())
    capture = source / "raw_requests_responses.jsonl"
    if a.digest(capture) != manifest["raw_capture_sha256"]:
        raise ValueError("Raw candidate hash mismatch")
    records = a.read(capture)
    if len(records) != 600 or {r["case_id"] for r in records} != set(protocol["case_ids"]):
        raise ValueError("Missing/duplicate captured cases")
    runtime, gold = (a.unique(a.read(a.FROZEN / name)) for name in ("strong_runtime_600.jsonl", "strong_scoring_600.jsonl"))
    rows = []; missing = {}; finish = {}; malformed = 0
    for record in records:
        cid = record["case_id"]; case = runtime[cid]
        gate = build_internal_request("C8_FINAL_UIR_B6", case)
        if gate["invoke"] != record["model_invoked"]:
            raise ValueError("Common preexecution gate mismatch")
        raw = (record["response"] or {}).get("message", {}).get("content", "")
        facts = case.get("context_claims", []) if gate["invoke"] else []
        if gate["invoke"]:
            reason = (record["response"] or {}).get("done_reason", "NOT_RECORDED")
            finish[reason] = finish.get(reason, 0) + 1
            proposed = a.extract(raw)
            malformed += proposed is None
            for field in a.CLAIM_FIELDS:
                if proposed and any(field not in c for c in proposed.get("claims", []) if isinstance(c, dict)):
                    missing[field] = missing.get(field, 0) + 1
        keys = a.claim_set(a.extract(raw)); selected = [f for f in facts if a.key(f) in keys]
        projected = json.dumps({"answer": "", "claims": selected}, ensure_ascii=False) if selected else "REJECTED: no verified claim"
        template = json.dumps({"answer": "", "claims": facts}, ensure_ascii=False) if facts else "REJECTED: no authorized fact"
        outputs = dict(zip(protocol["conditions"], (template, raw or "REJECTED: model not invoked or failed", projected,
                       projected if {a.key(f) for f in selected} == {a.key(f) for f in facts} else "REJECTED: incomplete catalog")))
        for condition, final in outputs.items():
            row = a.score_claims(final, raw, case, gold[cid], condition, record["model_invoked"] if condition != protocol["conditions"][0] else False, None)
            row["evidence_kind"] = "deterministic_execution" if condition == protocol["conditions"][0] else "fresh_model_inference"
            row["output_scope"] = "native prose unassessed" if condition == protocol["conditions"][1] else "deterministically rendered structured claims"
            rows.append(row)
    out = out or root / "fresh_matched_offline_replay"
    out.mkdir(exist_ok=False)
    a.write_csv(out / "matched_case_results.csv", rows)
    a.write_csv(out / "matched_summary.csv", a.summarize_internal(rows))
    comparisons = {name: a.digest(out / name) == a.digest(source / name) for name in ("matched_case_results.csv", "matched_summary.csv")}
    if not all(comparisons.values()):
        raise ValueError("Offline fresh-capture metric mismatch")
    a.write_json(out / "verification.json", {"status": "OFFLINE_CAPTURE_REPLAY_PASS_NOT_MODEL_RERUN", "equal": comparisons,
        "N_requests": len(records), "N_model_calls": sum(r["model_invoked"] for r in records), "finish_reasons": finish,
        "N_no_extractable_object": malformed, "missing_field_cases_nonexclusive": missing,
        "runtime_schema_required": protocol["format"]["properties"]["claims"]["items"]["required"],
        "scorer_bound_fields": list(a.CLAIM_FIELDS), "inference_calls_in_this_replay": 0,
        "scope_warning": "five-required-field syntax constraint vs seven-field exact support; not an unbiased model or IR contribution estimate"})
    print(json.dumps(comparisons))


if __name__ == "__main__":
    replay()
