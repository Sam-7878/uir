#!/usr/bin/env python3
"""Run actual Phi-3.5 pipelines on frozen official FinQA and HaluEval-QA rows."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable

from evaluation.uir_phase4c.common import (
    EXTERNAL_PIPELINES, FROZEN_DIR, MAX_NEW_TOKENS, MODEL_ID, MODEL_REVISION,
    RESULTS_DIR, ROOT, SEED, read_jsonl, sha256_file, sha256_text, write_json,
    write_jsonl,
)
from evaluation.uir_phase4c.inference import ActualPhiGenerator, Invocation
from evaluation.uir_phase4c.official_benchmarks import (
    apply_halueval_uir, execute_finqa_program, execute_finqa_tool,
    execute_halueval_tool, extract_program, finqa_prompt, finqa_tool_final,
    finqa_tool_request, halueval_prompt, halueval_tool_final,
    halueval_tool_request, halueval_uir_prompt, parse_final_answer,
    parse_yes_no,
)


def _base(case: dict[str, Any], pipeline: str) -> dict[str, Any]:
    return {
        "case_id": case["case_id"], "pipeline": pipeline,
        "source_dataset": case["source_dataset"], "source_original_id": case["source_original_id"],
        "source_file_sha256": case["source_file_sha256"], "source_row_hash": case["source_row_hash"],
        "runtime_fields": [key for key in case if key not in {"case_id", "source_dataset", "source_original_id", "source_file_sha256", "source_row_hash", "source_index"}],
        "scoring_only_fields": ["FinQA.qa.program", "FinQA.qa.exe_ans", "FinQA.qa.gold_inds"] if case["source_dataset"] == "FinQA" else ["HaluEval candidate provenance label"],
        "model_invoked": True,
    }


def _timing(started: int, ended: int, model_rows: list[dict[str, Any]]) -> dict[str, Any]:
    first_start = min(row["model_timing"]["start_ns"] for row in model_rows)
    last_end = max(row["model_timing"]["end_ns"] for row in model_rows)
    measured_model_ms = sum(row["model_timing"]["model_ms"] for row in model_rows)
    return {
        "start_ns": first_start, "end_ns": last_end, "end_to_end_ms": measured_model_ms,
        "model_ms": measured_model_ms,
        "retrieval_ms": 0.0, "policy_ms": 0.0, "validation_ms": 0.0,
        "model_batch_ids": [row["model_timing"]["batch_id"] for row in model_rows],
    }


def _normal_finqa(generator: ActualPhiGenerator, cases: list[dict[str, Any]], pipeline: str) -> list[dict[str, Any]]:
    states, calls = {}, []
    for case in cases:
        started = time.perf_counter_ns(); system, prompt, retrieved = finqa_prompt(case, pipeline)
        states[case["case_id"]] = (case, started, prompt, retrieved)
        calls.append(Invocation(case["case_id"], prompt, system))
    generated = generator.run(calls)
    records = []
    for row in generated:
        case, started, prompt, retrieved = states[row["case_id"]]
        ended = time.perf_counter_ns(); record = _base(case, pipeline)
        record.update({"pipeline_prompt_hash": row["prompt_sha256"], "prompt_text_or_content_ref": prompt, "retrieved_context_ids": retrieved, "tool_calls": [], "policy_decision": "REPORT_EXISTS" if pipeline == "C2_RAG_EXISTENCE_CHECK" else "UNCHECKED", "verified_fact_ids": [], "generation": row["generation"], "raw_model_response_hash": row["generation"]["raw_response_sha256"], "prediction": parse_final_answer(row["generation"]["raw_response"]), "predicted_program": "", "program_execution": {"status": "not_requested"}, "timing": _timing(started, ended, [row]), "resource": row["resource"]})
        records.append(record)
    return records


def _finqa_c8(generator: ActualPhiGenerator, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    states, calls = {}, []
    for case in cases:
        started = time.perf_counter_ns(); system, prompt, retrieved = finqa_prompt(case, "C8_FINAL_UIR_B6")
        states[case["case_id"]] = (case, started, prompt, retrieved)
        calls.append(Invocation(case["case_id"], prompt, system))
    records = []
    for row in generator.run(calls):
        case, started, prompt, retrieved = states[row["case_id"]]
        program = extract_program(row["generation"]["raw_response"])
        execution = execute_finqa_program(program, case)
        prediction = str(execution.get("value", "INVALID")) if execution["status"] == "success" else "INVALID"
        ended = time.perf_counter_ns(); record = _base(case, "C8_FINAL_UIR_B6")
        record.update({"pipeline_prompt_hash": row["prompt_sha256"], "prompt_text_or_content_ref": prompt, "retrieved_context_ids": retrieved, "tool_calls": [], "policy_decision": "UIR_PROGRAM_ACCEPT" if execution["status"] == "success" else "UIR_FAIL_CLOSED", "verified_fact_ids": retrieved if execution["status"] == "success" else [], "generation": row["generation"], "raw_model_response_hash": row["generation"]["raw_response_sha256"], "prediction": prediction, "predicted_program": program, "program_execution": execution, "timing": _timing(started, ended, [row]), "resource": row["resource"]})
        records.append(record)
    return records


def _finqa_c4(generator: ActualPhiGenerator, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    states, first_calls = {}, []
    for case in cases:
        started = time.perf_counter_ns(); system, prompt, source_text = finqa_tool_request(case)
        states[case["case_id"]] = {"case": case, "started": started, "first_prompt": prompt, "source_text": source_text}
        first_calls.append(Invocation(case["case_id"], prompt, system))
    first_rows = generator.run(first_calls); second_calls = []
    for first in first_rows:
        state = states[first["case_id"]]; request, result = execute_finqa_tool(first["generation"]["raw_response"], state["source_text"])
        system, prompt = finqa_tool_final(state["case"], request, result)
        state.update({"first": first, "request": request, "result": result, "final_prompt": prompt})
        second_calls.append(Invocation(first["case_id"], prompt, system))
    second_rows = {row["case_id"]: row for row in generator.run(second_calls)}; records = []
    for case_id, state in states.items():
        case, first, second = state["case"], state["first"], second_rows[case_id]
        ended = time.perf_counter_ns(); record = _base(case, "C4_TOOL_CALLING_AGENT")
        trace = {"model_tool_request": state["request"], "tool_result": state["result"], "model_final_response": second["generation"]["raw_response"]}
        record.update({"pipeline_prompt_hash": second["prompt_sha256"], "prompt_text_or_content_ref": state["final_prompt"], "retrieved_context_ids": ["authoritative_local_calculator"], "tool_calls": [trace], "model_tool_request": state["request"], "policy_decision": "TOOL_EXECUTED", "verified_fact_ids": ["authoritative_local_calculator"] if state["result"].get("status") == "success" else [], "tool_selection_generation": first["generation"], "generation": second["generation"], "raw_model_response_hash": second["generation"]["raw_response_sha256"], "prediction": parse_final_answer(second["generation"]["raw_response"]), "predicted_program": "", "program_execution": state["result"], "timing": _timing(state["started"], ended, [first, second]), "resource": {"peak_vram_mb": max(first["resource"]["peak_vram_mb"], second["resource"]["peak_vram_mb"])}})
        records.append(record)
    return records


def run_finqa(generator: ActualPhiGenerator, force: bool) -> None:
    cases = read_jsonl(FROZEN_DIR / "finqa_runtime_200.jsonl")
    for pipeline in EXTERNAL_PIPELINES:
        short = pipeline.split("_")[0]; output = RESULTS_DIR / f"finqa_predictions_actual_{short}.jsonl"
        if output.exists() and not force and len(read_jsonl(output)) == len(cases):
            print(f"[resume] FinQA {short}"); continue
        print(f"[run] FinQA {short}")
        if pipeline == "C4_TOOL_CALLING_AGENT": records = _finqa_c4(generator, cases)
        elif pipeline == "C8_FINAL_UIR_B6": records = _finqa_c8(generator, cases)
        else: records = _normal_finqa(generator, cases, pipeline)
        write_jsonl(output, records)


def _normal_halueval(generator: ActualPhiGenerator, cases: list[dict[str, Any]], pipeline: str) -> list[dict[str, Any]]:
    states, calls = {}, []
    for case in cases:
        started = time.perf_counter_ns()
        if pipeline == "C8_FINAL_UIR_B6": system, prompt, retrieved = halueval_uir_prompt(case)
        else: system, prompt, retrieved = halueval_prompt(case, pipeline)
        states[case["case_id"]] = (case, started, prompt, retrieved)
        calls.append(Invocation(case["case_id"], prompt, system))
    records = []
    for row in generator.run(calls):
        case, started, prompt, retrieved = states[row["case_id"]]
        if pipeline == "C8_FINAL_UIR_B6": prediction, quote = apply_halueval_uir(row["generation"]["raw_response"], case["knowledge"])
        else: prediction, quote = parse_yes_no(row["generation"]["raw_response"]), ""
        ended = time.perf_counter_ns(); record = _base(case, pipeline)
        record.update({"pipeline_prompt_hash": row["prompt_sha256"], "prompt_text_or_content_ref": prompt, "retrieved_context_ids": retrieved, "tool_calls": [], "policy_decision": "UIR_OUTPUT_ACCEPT" if pipeline == "C8_FINAL_UIR_B6" and prediction != "INVALID" else ("UIR_FAIL_CLOSED" if pipeline == "C8_FINAL_UIR_B6" else "JUDGE_GENERATED"), "verified_fact_ids": retrieved if quote else [], "generation": row["generation"], "raw_model_response_hash": row["generation"]["raw_response_sha256"], "prediction": prediction, "evidence_quote": quote, "timing": _timing(started, ended, [row]), "resource": row["resource"]})
        records.append(record)
    return records


def _halueval_c4(generator: ActualPhiGenerator, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    states, first_calls = {}, []
    for case in cases:
        started = time.perf_counter_ns(); system, prompt = halueval_tool_request(case)
        states[case["case_id"]] = {"case": case, "started": started, "first_prompt": prompt}
        first_calls.append(Invocation(case["case_id"], prompt, system))
    first_rows = generator.run(first_calls); second_calls = []
    for first in first_rows:
        state = states[first["case_id"]]; request, result = execute_halueval_tool(state["case"], first["generation"]["raw_response"])
        system, prompt = halueval_tool_final(state["case"], request, result)
        state.update({"first": first, "request": request, "result": result, "final_prompt": prompt})
        second_calls.append(Invocation(first["case_id"], prompt, system))
    second_rows = {row["case_id"]: row for row in generator.run(second_calls)}; records = []
    for case_id, state in states.items():
        case, first, second = state["case"], state["first"], second_rows[case_id]
        ended = time.perf_counter_ns(); record = _base(case, "C4_TOOL_CALLING_AGENT")
        trace = {"model_tool_request": state["request"], "tool_result": state["result"], "model_final_response": second["generation"]["raw_response"]}
        record.update({"pipeline_prompt_hash": second["prompt_sha256"], "prompt_text_or_content_ref": state["final_prompt"], "retrieved_context_ids": ["official_knowledge"], "tool_calls": [trace], "model_tool_request": state["request"], "policy_decision": "TOOL_EXECUTED", "verified_fact_ids": ["official_knowledge"] if state["result"].get("status") == "success" else [], "tool_selection_generation": first["generation"], "generation": second["generation"], "raw_model_response_hash": second["generation"]["raw_response_sha256"], "prediction": parse_yes_no(second["generation"]["raw_response"]), "timing": _timing(state["started"], ended, [first, second]), "resource": {"peak_vram_mb": max(first["resource"]["peak_vram_mb"], second["resource"]["peak_vram_mb"])}})
        records.append(record)
    return records


def run_halueval(generator: ActualPhiGenerator, force: bool) -> None:
    cases = read_jsonl(FROZEN_DIR / "halueval_qa_runtime_200.jsonl")
    for pipeline in EXTERNAL_PIPELINES:
        short = pipeline.split("_")[0]; output = RESULTS_DIR / f"halueval_predictions_actual_{short}.jsonl"
        if output.exists() and not force and len(read_jsonl(output)) == len(cases):
            print(f"[resume] HaluEval {short}"); continue
        print(f"[run] HaluEval {short}")
        records = _halueval_c4(generator, cases) if pipeline == "C4_TOOL_CALLING_AGENT" else _normal_halueval(generator, cases, pipeline)
        write_jsonl(output, records)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--benchmark", choices=("finqa", "halueval", "all"), default="all"); parser.add_argument("--batch-size", type=int, default=4); parser.add_argument("--model-path"); parser.add_argument("--force", action="store_true"); args = parser.parse_args()
    generator = ActualPhiGenerator(model_path=args.model_path, batch_size=args.batch_size); runtime = generator.load()
    started = datetime.now(timezone.utc).isoformat()
    if args.benchmark in {"finqa", "all"}: run_finqa(generator, args.force)
    if args.benchmark in {"halueval", "all"}: run_halueval(generator, args.force)
    manifest = {"phase": "UIR-4C", "campaign": "official_benchmarks", "started_at_utc": started, "completed_at_utc": datetime.now(timezone.utc).isoformat(), "model": MODEL_ID, "hf_revision": MODEL_REVISION, "seed": SEED, "runtime": runtime, "benchmark": args.benchmark, "input_hashes": {"finqa": sha256_file(FROZEN_DIR / "finqa_runtime_200.jsonl"), "halueval": sha256_file(FROZEN_DIR / "halueval_qa_runtime_200.jsonl")}}
    write_json(RESULTS_DIR / "official_inference_manifest.json", manifest)
    print(json.dumps({"status": "OFFICIAL_ACTUAL_GENERATION_COMPLETE", "benchmark": args.benchmark}, sort_keys=True))


if __name__ == "__main__":
    main()
