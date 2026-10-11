#!/usr/bin/env python3
"""Run authentic C0-C8 Phi-3.5 inference over a pre-registered shared set."""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.uir_phase4c.common import (
    FROZEN_DIR, MAX_NEW_TOKENS, MODEL_ID, MODEL_REVISION, PIPELINES, RAW_DIR,
    RESULTS_DIR, ROOT, SEED, read_jsonl, sha256_file, sha256_text, write_json,
    write_jsonl,
)
from evaluation.uir_phase4c.inference import ActualPhiGenerator, Invocation
from evaluation.uir_phase4c.pipelines import (
    apply_internal_transition, build_internal_request, build_tool_final,
    build_tool_request, context_ids, execute_internal_tool,
)


def _rejected_record(case: dict[str, Any], pipeline: str, plan: dict[str, Any], start_ns: int, end_ns: int) -> dict[str, Any]:
    final_output = plan["final_output"]
    return {
        "case_id": case["case_id"], "source_dataset": case["source_dataset"], "source_row_hash": case["source_row_hash"], "stratum": case["stratum"], "language": case["language"], "pipeline": pipeline,
        "prompt_sha256": sha256_text(""), "prompt_text_or_content_ref": "", "retrieved_context_ids": plan.get("retrieved_context_ids", []), "tool_calls": [], "policy_decision": plan["policy_decision"], "verified_fact_ids": plan.get("verified_fact_ids", []), "model_invoked": False,
        "generation": {"model": MODEL_ID, "hf_revision": MODEL_REVISION, "seed": SEED, "do_sample": False, "max_new_tokens": MAX_NEW_TOKENS, "raw_response": "", "raw_response_sha256": sha256_text(""), "input_tokens": 0, "output_tokens": 0, "finish_reason": "not_invoked"},
        "final_output": final_output,
        "timing": {"start_ns": start_ns, "end_ns": end_ns, "end_to_end_ms": (end_ns - start_ns) / 1_000_000.0, "model_ms": 0.0, "retrieval_ms": 0.0, "policy_ms": (end_ns - start_ns) / 1_000_000.0, "validation_ms": 0.0},
        "resource": {"peak_vram_mb": 0.0},
    }


def _run_standard(generator: ActualPhiGenerator, cases: list[dict[str, Any]], pipeline: str) -> list[dict[str, Any]]:
    queued: list[tuple[dict[str, Any], dict[str, Any], int, int]] = []
    records: list[dict[str, Any]] = []
    invocations: list[Invocation] = []
    for case in cases:
        start_ns = time.perf_counter_ns()
        retrieval_start = time.perf_counter_ns()
        plan = build_internal_request(pipeline, case)
        retrieval_ms = (time.perf_counter_ns() - retrieval_start) / 1_000_000.0
        if not plan["invoke"]:
            records.append(_rejected_record(case, pipeline, plan, start_ns, time.perf_counter_ns()))
            continue
        queued.append((case, plan, start_ns, time.perf_counter_ns()))
        invocations.append(Invocation(case["case_id"], plan["prompt"], plan["system"]))
    generated = generator.run(invocations)
    generated_by_id = {row["case_id"]: row for row in generated}
    for case, plan, start_ns, prepared_ns in queued:
        generated_row = generated_by_id[case["case_id"]]
        validation_start = time.perf_counter_ns()
        raw = generated_row["generation"]["raw_response"]
        final_output, selected_refs = apply_internal_transition(pipeline, case, raw)
        end_ns = time.perf_counter_ns()
        validation_ms = (end_ns - validation_start) / 1_000_000.0
        model_timing = generated_row["model_timing"]
        preprocess_ms = (prepared_ns - start_ns) / 1_000_000.0
        records.append({
            "case_id": case["case_id"], "source_dataset": case["source_dataset"], "source_row_hash": case["source_row_hash"], "stratum": case["stratum"], "language": case["language"], "pipeline": pipeline,
            "prompt_sha256": generated_row["prompt_sha256"], "prompt_text_or_content_ref": plan["prompt"], "retrieved_context_ids": plan.get("retrieved_context_ids", []), "tool_calls": [], "policy_decision": plan["policy_decision"], "verified_fact_ids": selected_refs or plan.get("verified_fact_ids", []), "model_invoked": True,
            "generation": generated_row["generation"], "final_output": final_output,
            "timing": {"start_ns": model_timing["start_ns"], "end_ns": model_timing["end_ns"], "end_to_end_ms": preprocess_ms + model_timing["model_ms"] + validation_ms, "model_ms": model_timing["model_ms"], "retrieval_ms": preprocess_ms, "policy_ms": 0.0, "validation_ms": validation_ms, "model_batch_id": model_timing["batch_id"], "model_batch_size": model_timing["batch_size"]},
            "resource": generated_row["resource"],
        })
    return sorted(records, key=lambda row: row["case_id"])


def _run_tool_agent(generator: ActualPhiGenerator, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    first_requests = []
    for case in cases:
        started = time.perf_counter_ns()
        system, prompt = build_tool_request(case)
        state[case["case_id"]] = {"case": case, "started": started, "first_system": system, "first_prompt": prompt}
        first_requests.append(Invocation(case["case_id"], prompt, system))
    first_outputs = generator.run(first_requests)
    second_requests = []
    for generated in first_outputs:
        item = state[generated["case_id"]]
        tool_started = time.perf_counter_ns()
        model_request, tool_result = execute_internal_tool(item["case"], generated["generation"]["raw_response"])
        tool_ms = (time.perf_counter_ns() - tool_started) / 1_000_000.0
        system, prompt = build_tool_final(item["case"], model_request, tool_result)
        item.update({"first": generated, "model_tool_request": model_request, "tool_result": tool_result, "tool_ms": tool_ms, "final_system": system, "final_prompt": prompt})
        second_requests.append(Invocation(generated["case_id"], prompt, system))
    second_outputs = {row["case_id"]: row for row in generator.run(second_requests)}
    records = []
    for case_id, item in state.items():
        case = item["case"]
        first, second = item["first"], second_outputs[case_id]
        raw = second["generation"]["raw_response"]
        final_output, _ = apply_internal_transition("C4_TOOL_CALLING_AGENT", case, raw)
        end_ns = time.perf_counter_ns()
        tool_call = {"model_tool_request": item["model_tool_request"], "tool_result": item["tool_result"], "model_final_response": raw}
        records.append({
            "case_id": case_id, "source_dataset": case["source_dataset"], "source_row_hash": case["source_row_hash"], "stratum": case["stratum"], "language": case["language"], "pipeline": "C4_TOOL_CALLING_AGENT",
            "prompt_sha256": second["prompt_sha256"], "prompt_text_or_content_ref": item["final_prompt"], "retrieved_context_ids": context_ids(case), "tool_calls": [tool_call], "model_tool_request": item["model_tool_request"], "policy_decision": "TOOL_EXECUTED", "verified_fact_ids": context_ids(case) if item["tool_result"].get("status") == "success" else [], "model_invoked": True,
            "tool_selection_generation": first["generation"], "generation": second["generation"], "final_output": final_output,
            "timing": {"start_ns": first["model_timing"]["start_ns"], "end_ns": second["model_timing"]["end_ns"], "end_to_end_ms": first["model_timing"]["model_ms"] + item["tool_ms"] + second["model_timing"]["model_ms"], "model_ms": first["model_timing"]["model_ms"] + second["model_timing"]["model_ms"], "retrieval_ms": item["tool_ms"], "policy_ms": 0.0, "validation_ms": 0.0, "model_batch_id": second["model_timing"]["batch_id"], "model_batch_size": second["model_timing"]["batch_size"]},
            "resource": {"peak_vram_mb": max(first["resource"]["peak_vram_mb"], second["resource"]["peak_vram_mb"])},
        })
    return sorted(records, key=lambda row: row["case_id"])


def _git_state() -> dict[str, Any]:
    def capture(*args: str) -> str:
        return subprocess.check_output(args, cwd=ROOT, text=True).strip()
    return {"commit": capture("git", "rev-parse", "HEAD"), "status_at_start": capture("git", "status", "--short")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--model-path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    dataset = FROZEN_DIR / ("smoke_runtime_100.jsonl" if args.stage == "smoke" else "strong_runtime_600.jsonl")
    if not dataset.exists():
        raise FileNotFoundError("run freeze_inputs.py before model inference")
    cases = read_jsonl(dataset)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True); RAW_DIR.mkdir(parents=True, exist_ok=True)
    generator = ActualPhiGenerator(model_path=args.model_path, batch_size=args.batch_size)
    runtime = generator.load()
    manifest = {
        "phase": "UIR-4C", "stage": args.stage, "started_at_utc": datetime.now(timezone.utc).isoformat(), "model": MODEL_ID, "hf_revision": MODEL_REVISION,
        "generation": {"seed": SEED, "do_sample": False, "temperature": 0.0, "max_new_tokens": MAX_NEW_TOKENS, "batch_size": args.batch_size},
        "runtime": runtime, "platform": platform.platform(), "python": platform.python_version(), "dataset": str(dataset.relative_to(ROOT)), "dataset_sha256": sha256_file(dataset), "shared_cases": len(cases), "pipelines": list(PIPELINES), "git": _git_state(),
    }
    for pipeline in PIPELINES:
        output = RAW_DIR / f"{args.stage}_{pipeline}.jsonl"
        if output.exists() and not args.force and len(read_jsonl(output)) == len(cases):
            print(f"[resume] {pipeline}: existing complete capture", flush=True)
            continue
        print(f"[run] {pipeline}: {len(cases)} cases", flush=True)
        records = _run_tool_agent(generator, cases) if pipeline == "C4_TOOL_CALLING_AGENT" else _run_standard(generator, cases, pipeline)
        write_jsonl(output, records)
    manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["raw_capture_hashes"] = {pipeline: sha256_file(RAW_DIR / f"{args.stage}_{pipeline}.jsonl") for pipeline in PIPELINES}
    write_json(RESULTS_DIR / f"ACTUAL_INFERENCE_MANIFEST_{args.stage}.json", manifest)
    if args.stage == "full":
        write_json(RESULTS_DIR / "ACTUAL_INFERENCE_MANIFEST.json", manifest)
    print(json.dumps({"status": "ACTUAL_GENERATION_COMPLETE", "stage": args.stage, "cases": len(cases), "records": len(cases) * len(PIPELINES)}, sort_keys=True))


if __name__ == "__main__":
    main()
