#!/usr/bin/env python3
"""Execute real Phi-3.5 B0--B5 campaigns with resumable JSONL evidence."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from baselines import PIPELINES, build_request
from claim_metrics import evaluate_claims, numeric_dimensions, parse_output, validate_against_facts
from ollama_client import OllamaClient

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "uir_external"))
from registry_adapter import FrozenRegistry


def read_jsonl(path: Path | None) -> list[dict]:
    if path is None or not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def filter_and_render(generated: list[dict], expected: list[dict], format_error: str | None) -> tuple[list[dict], str, str]:
    """Return only exact verified claims and render without reusing model prose."""
    supported, rejected = validate_against_facts(generated, expected)
    if format_error:
        return [], "", "rejected"
    answer = "; ".join(
        f"{claim['attribute']}={claim['value']} {claim['unit']} ({claim['period']}) [{claim['provenance']}]"
        for claim in supported
    )
    return supported, answer, "filtered" if rejected else "accepted"


def parse_fact_reference_output(text: str) -> tuple[str, list[str], str | None]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        return "", [], f"SLM_FORMAT_ERROR:{error.msg}"
    refs = payload.get("fact_refs")
    if not isinstance(payload.get("answer"), str) or not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
        return "", [], "SLM_SCHEMA_ERROR:answer_or_fact_refs"
    return payload["answer"], list(dict.fromkeys(refs)), None


def resolve_fact_references(refs: list[str], catalog: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    supported = [catalog[ref] for ref in refs if ref in catalog]
    rejected = [{"claim_type":"provenance_claim","entity_id":"","attribute":"unsupported_fact_ref","value":ref,
                 "unit":"","period":"","provenance":""} for ref in refs if ref not in catalog]
    return supported, rejected


def render_verified_claims(claims: list[dict]) -> str:
    return "; ".join(
        f"{claim['attribute']}={claim['value']} {claim['unit']} ({claim['period']}) [{claim['provenance']}]"
        for claim in claims
    )


def verified_answer_state(accepted: list[dict], expected: list[dict]) -> str:
    if not accepted:
        return "NO_VERIFIED_ANSWER"
    return "FULL_VERIFIED_ANSWER" if len(accepted) == len(expected) else "PARTIAL_VERIFIED_ANSWER"


def initial_output_state(pipeline: str, renderer_invoked: bool) -> str:
    """Give policy-prevented B6 paths an explicit verified-answer state."""
    if pipeline == "B6_UIR_FILTER_AND_RENDER" and not renderer_invoked:
        return "NO_VERIFIED_ANSWER"
    return "UNVALIDATED"


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", type=Path, required=True); parser.add_argument("--suite", choices=("frozen", "frozen_v2", "real_fact", "numeric", "adversarial"), required=True); parser.add_argument("--registry", type=Path, default=Path("evaluation/uir_external/registry_v1.jsonl")); parser.add_argument("--uir-records", type=Path); parser.add_argument("--config", type=Path, default=Path("evaluation/uir_slm/model_config/phi35_ollama.json")); parser.add_argument("--out", type=Path, required=True); parser.add_argument("--pipelines", nargs="+", choices=PIPELINES, default=PIPELINES); parser.add_argument("--seed", type=int, default=20260807); parser.add_argument("--temperature", type=float); parser.add_argument("--run-id", default="deterministic-1"); parser.add_argument("--limit", type=int); parser.add_argument("--no-resume", action="store_true"); args = parser.parse_args()
    cases = read_jsonl(args.dataset); cases = cases[:args.limit] if args.limit else cases; registry = FrozenRegistry(args.registry); uir = {row["case_id"]: row for row in read_jsonl(args.uir_records)}; client = OllamaClient(args.config); mode = "stochastic" if args.temperature is not None and args.temperature > 0 else "deterministic"; config = client.config[mode].copy(); config["seed"] = args.seed
    if args.temperature is not None: config["temperature"] = args.temperature
    args.out.parent.mkdir(parents=True, exist_ok=True); existing = [] if args.no_resume else read_jsonl(args.out); index = {(row["run_id"], row["case_id"], row["pipeline"], row["seed"]): row for row in existing}; pending = sum((args.run_id, case["case_id"], pipeline, args.seed) not in index for case in cases for pipeline in args.pipelines)
    print(json.dumps({"suite": args.suite, "cases": len(cases), "pipelines": args.pipelines, "pending": pending, "resume_rows": len(existing)}, sort_keys=True), flush=True)
    mode = "a" if existing and not args.no_resume else "w"; completed = 0; started_campaign = time.monotonic()
    with args.out.open(mode, encoding="utf-8", newline="\n") as handle:
        for case in cases:
            for pipeline in args.pipelines:
                key = (args.run_id, case["case_id"], pipeline, args.seed)
                if key in index: continue
                request = build_request(pipeline, case, registry, uir.get(case["case_id"])); reused = False
                if not request.invoke_renderer:
                    raw_text = ""; generated = []; answer = ""; format_error = None; model_fact_refs = []; finish_reason = "not_invoked"; latency = {"total_us": 0, "prompt_eval_us": 0, "generation_us": 0, "load_us": 0, "prompt_tokens": 0, "output_tokens": 0}; actual_outcome = "REJECT"
                else:
                    b4_key = (args.run_id, case["case_id"], "B4_UIR_POLICY_SLM", args.seed)
                    if pipeline in {"B5_FULL_UIR_OUTPUT_VALIDATION", "B6_UIR_FILTER_AND_RENDER"} and b4_key in index:
                        source = index[b4_key]; raw_text = source["raw_output"]; answer = source["answer"]; model_fact_refs = source.get("model_fact_refs", []); format_error = source["format_error"]; finish_reason = source.get("finish_reason", "unknown"); latency = source["latency"].copy(); reused = True
                    else:
                        result = client.generate(request.prompt, request.system, config, request.response_schema); raw_text = result.text; finish_reason = str(result.raw.get("done_reason", "unknown"))
                        if request.output_mode == "fact_refs": answer, model_fact_refs, format_error = parse_fact_reference_output(raw_text)
                        else: answer, generated, format_error = parse_output(raw_text); model_fact_refs = []
                        latency = {"total_us": result.latency_us, "prompt_eval_us": result.prompt_eval_us, "generation_us": result.generation_us, "load_us": result.load_us, "prompt_tokens": result.prompt_tokens, "output_tokens": result.output_tokens}
                    if request.output_mode == "fact_refs":
                        resolved, invalid_refs = resolve_fact_references(model_fact_refs, request.fact_catalog or {})
                        generated = [*resolved, *invalid_refs]
                    actual_outcome = "ABORT" if format_error else "COMMIT"
                expected = case.get("expected_claims", []); validator_started = time.perf_counter_ns(); supported, rejected = validate_against_facts(generated, expected); validator_us = (time.perf_counter_ns() - validator_started) // 1000
                latency["validator_us"] = validator_us if pipeline in {"B5_FULL_UIR_OUTPUT_VALIDATION", "B6_UIR_FILTER_AND_RENDER"} else 0
                latency["pipeline_total_us"] = latency["total_us"] + latency["validator_us"]
                accepted = generated
                output_validation = "not_applied"
                output_state = initial_output_state(pipeline, request.invoke_renderer)
                if pipeline == "B5_FULL_UIR_OUTPUT_VALIDATION" and request.invoke_renderer:
                    output_validation = "rejected" if rejected or format_error else "accepted"; accepted = [] if rejected or format_error else supported; actual_outcome = "REJECT" if rejected or format_error else "COMMIT"; output_state = verified_answer_state(accepted, expected)
                elif pipeline == "B6_UIR_FILTER_AND_RENDER" and request.invoke_renderer:
                    accepted, answer, output_validation = filter_and_render(generated, expected, format_error)
                    answer = render_verified_claims(accepted); output_state = verified_answer_state(accepted, expected)
                    actual_outcome = "COMMIT" if accepted or not expected else "REJECT"
                metrics = evaluate_claims(expected, generated, accepted); numeric = numeric_dimensions(expected, accepted) if args.suite in {"numeric", "real_fact"} else {}
                target = (case.get("expected_semantics") or {}).get("target")
                entity_lock_violation = any(target and claim.get("entity_id") != target for claim in accepted)
                expected_outcome = case.get("expected_outcome", "REJECT")
                record = {"run_id": args.run_id, "suite": args.suite, "case_id": case["case_id"], "pipeline": pipeline, "model": client.config["model"], "seed": args.seed, "temperature": config["temperature"], "language": case.get("language"), "category": case.get("category"), "split": case.get("split"), "attack_type": case.get("attack_type"), "numeric_type": case.get("numeric_type"), "expected_outcome": expected_outcome, "policy_valid": case.get("policy_valid", True), "entity_valid": case.get("entity_valid", False), "actual_outcome": actual_outcome, "correct_outcome": actual_outcome == expected_outcome, "renderer_invoked": request.invoke_renderer, "renderer_reused": reused, "rejection_reason": request.rejection_reason, "output_validation": output_validation, "output_state": output_state, "raw_output": raw_text, "answer": answer, "model_fact_refs": model_fact_refs, "generated_claims_data": generated, "accepted_claims_data": accepted, "format_error": format_error, "finish_reason": finish_reason, "generation_budget_tokens": config["max_new_tokens"], "json_truncated": finish_reason == "length" or (bool(format_error) and latency["output_tokens"] >= config["max_new_tokens"]), "latency": latency, "metrics": {**metrics, **numeric}, "partial_answer": output_state == "PARTIAL_VERIFIED_ANSWER", "attack_success": expected_outcome == "REJECT" and bool(accepted), "policy_bypass": not case.get("policy_valid", True) and request.invoke_renderer, "entity_lock_violation": entity_lock_violation, "renderer_invocation_on_reject_path": pipeline in {"B4_UIR_POLICY_SLM", "B5_FULL_UIR_OUTPUT_VALIDATION", "B6_UIR_FILTER_AND_RENDER"} and expected_outcome == "REJECT" and request.invoke_renderer}
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"); handle.flush(); index[key] = record; completed += 1
                if completed % 50 == 0: print(json.dumps({"completed": completed, "pending": pending - completed, "elapsed_s": round(time.monotonic() - started_campaign, 1)}, sort_keys=True), flush=True)
    print(json.dumps({"status": "complete", "new_rows": completed, "total_rows": len(index), "out": str(args.out)}, sort_keys=True), flush=True)


if __name__ == "__main__": main()
