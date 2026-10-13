"""S raw-to-approved-output replay; no model/network calls or author approval."""
import json
from .common import read, load, sha, write, utc
from .evaluation import packet_for, closed_output
from .specialized import packet_for_specialized
from .experiment import check_freeze, parse_response, presented_source
from .baseline import unique_rows
from .interpreter_python import interpret


def reconstruct(out):
    check_freeze(out)
    rows = read(out / "factorial_saved_outputs.jsonl")
    unique_rows(rows, ("condition_id", "case_id"))
    runtime = {r["case_id"]: r for r in read(out / "runtime/query_aware_dev.jsonl")}
    captured = read(out / "fresh_model_raw.jsonl")
    unique_rows(captured, ("request_hash",))
    captures = {r["request_hash"]: r for r in captured}
    for row in rows:
        original = runtime[row["case_id"]]
        source = presented_source(original, row["evidence"])
        packet = packet_for(original, source) if row["representation"] == "UIR_SHARED_TYPED" else packet_for_specialized(original, source)
        expected = interpret(packet)
        selected = expected["fact_ids"]
        if row["selector_capture_hash"]:
            selected, error = parse_response(captures[row["selector_capture_hash"]]["response"], "fact_ids")
            if error != row["selector_error"]:
                raise ValueError("SELECTOR_REPLAY_ERROR_MISMATCH")
        if selected != row["selector_ids"]:
            raise ValueError("SELECTOR_REPLAY_MISMATCH")
        lines = row["raw_user_visible_candidate"]
        if row["renderer_capture_hash"]:
            actual, error = parse_response(captures[row["renderer_capture_hash"]]["response"], "lines")
            if actual != lines or error != row["renderer_error"]:
                raise ValueError("RENDERER_RAW_REPLAY_MISMATCH")
        kept = sorted(set(selected) & set(expected["fact_ids"]))
        if closed_output(lines, packet, kept) != row["approved"]:
            raise ValueError("WHOLE_APPROVED_OUTPUT_REPLAY_MISMATCH")
    return {"status": "S_CPU_RAW_TO_APPROVED_REPLAY_PASS", "created_at_utc": utc(), "N_saved_factorial": len(rows),
            "N_actual_captures": len(captured), "GPU_calls_in_replay": 0, "same_host": True}
