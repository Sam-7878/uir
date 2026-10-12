"""Explicit, preregistered LOCAL RTX3090 experiment; never pulls missing models."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import DEFAULT, jsonl
from uir_common.contracts import reject_gold
from uir_common.ollama_client import OllamaClient

MODEL = "phi3.5:latest"
DIGEST = "61819fb370a3c1a9be6694869331e5f85f867a079e9271d66cb223acb81d04ba"
GPU = "GPU-ab53069a-3217-ee09-80f8-748b5fdbd156"
CONDITIONS = ("DETERMINISTIC_TRUSTED_FIXTURE", "SLM_SCHEMA_RENDERER", "SLM_SAME_CANDIDATE_PROJECTION", "SLM_PROJECTION_PARTIAL_OFF")


def prepare(root):
    target = root / "fresh_matched_protocol.json"
    if target.exists():
        raise FileExistsError("Protocol already frozen; do not tune it after seeing results")
    cases = a.unique(a.read(a.FROZEN / "strong_runtime_600.jsonl"))
    protocol = {"experiment_version": "rtx3090-local-gguf-matched-v1", "evidence_kind": "fresh_model_inference",
                "created_at_utc": datetime.now(timezone.utc).isoformat(), "model": MODEL, "model_digest": DIGEST,
                "quantization": "Q4_0", "gpu_uuid": GPU, "runtime_sha256": a.digest(a.FROZEN / "strong_runtime_600.jsonl"),
                "case_ids": sorted(cases), "cohort": "historical constructed development cohort; NOT new holdout",
                "endpoint": "http://127.0.0.1:18747", "transport": "loopback-only local GPU runtime, not remote inference infrastructure",
                "conditions": CONDITIONS, "format": a.SCHEMA,
                "options": {"temperature": 0, "seed": 20261012, "num_ctx": 8192, "num_predict": 512, "num_gpu": 99},
                "primary_endpoint": "complete exact required claim set on fixed 418 eligible cases",
                "secondary_endpoint": "supported claim coverage, structured claim AUCR, missing/format/finish",
                "model_calls": "one captured schema-renderer candidate per common preexecution-permitted request, reused across projections",
                "retries": 0, "partial_off": "retain only complete runtime fact catalog; no evaluator gold at runtime",
                "timing": "sequential request timestamps; first load-inclusive request separately flagged; no throughput speedup claim",
                "source_sha256": a.digest(__file__), "template": "next_gpu_matched-v1 exact trusted catalog copying",
                "comparison_family": "six exploratory matched-development comparisons: three conditions vs deterministic, complete and coverage",
                "statistics": {"seed": 20261012, "bootstrap_repetitions": 10000, "bootstrap_unit": "recorded source_family_id; retain all paired rows",
                               "comparison_direction": "SLM condition minus deterministic", "multiplicity": "Holm over six exact McNemar p-values"},
                "source_family_manifest_sha256": a.digest(root / "source_family_manifest.csv"),
                "analysis_source_sha256": a.digest(Path(__file__).with_name("next_matched_analysis.py")),
                "inference_equivalent_to_historical_FP16_or_NF4": False}
    a.write_json(target, protocol)
    print(f"Protocol frozen: {target}")


def execute(root):
    from evaluation.uir_phase4d.pipelines import build_internal_request
    path = root / "fresh_matched_protocol.json"
    protocol = json.loads(path.read_text())
    if a.digest(__file__) != protocol["source_sha256"]:
        raise ValueError("Runner changed after protocol freeze")
    if a.digest(a.FROZEN / "strong_runtime_600.jsonl") != protocol["runtime_sha256"]:
        raise ValueError("Runtime cohort changed")
    if a.digest(root / "source_family_manifest.csv") != protocol["source_family_manifest_sha256"]:
        raise ValueError("Source families changed after freeze")
    out = root / "fresh_matched"
    out.mkdir(exist_ok=False)
    client = OllamaClient(protocol["endpoint"])
    installed = {r["name"]: r for r in client.get("/api/tags")["models"]}
    if MODEL not in installed or installed[MODEL]["digest"] != DIGEST:
        raise ValueError("Approved local generator artifact missing/mismatched; no automatic download")
    info = client.post("/api/show", {"model": MODEL})
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,uuid,memory.total,memory.used", "--format=csv,noheader"],
                         check=True, capture_output=True, text=True).stdout
    if GPU not in gpu:
        raise RuntimeError("Required RTX3090 absent")
    a.write_json(out / "fresh_run_manifest.json", {"status": "RUNNING", "protocol_sha256": a.digest(path),
        "model": installed[MODEL], "template_sha256": hashlib.sha256(info.get("template", "").encode()).hexdigest(),
        "server_version": client.get("/api/version"), "gpu_before": gpu,
        "evidence_kind": "fresh_model_inference", "remote_inference": False})
    runtime = a.unique(a.read(a.FROZEN / "strong_runtime_600.jsonl"))
    raw_records = []; outputs = []; first_model_call = True
    with (out / "raw_requests_responses.jsonl").open("x", encoding="utf-8") as capture:
        for index, cid in enumerate(protocol["case_ids"], 1):
            case = runtime[cid]; reject_gold(case)
            gate_start = time.perf_counter_ns()
            gate = build_internal_request("C8_FINAL_UIR_B6", case)
            gate_ms = (time.perf_counter_ns() - gate_start) / 1e6
            facts = case.get("context_claims", []) if gate["invoke"] else []
            template_start = time.perf_counter_ns()
            template = json.dumps({"answer": "", "claims": facts}, ensure_ascii=False) if facts else "REJECTED: no authorized fact"
            template_ms = (time.perf_counter_ns() - template_start) / 1e6
            queue = time.time_ns(); started = time.perf_counter_ns(); wall_start = time.time_ns()
            raw = ""; response = None; error = None; payload = None
            cold = first_model_call if gate["invoke"] else "NOT_APPLICABLE"
            if gate["invoke"]:
                payload = {"model": MODEL, "messages": [
                    {"role": "system", "content": "Copy only the supplied trusted facts, including all fields. Return JSON; do not invent or modify values."},
                    {"role": "user", "content": "REQUEST:\n" + case["input"] + "\nTRUSTED_FACTS:\n" + json.dumps(facts, ensure_ascii=False, sort_keys=True)}],
                    "format": protocol["format"], "stream": False, "keep_alive": "10m", "options": protocol["options"]}
                try:
                    response = client.post("/api/chat", payload, timeout=300)
                    raw = response.get("message", {}).get("content", "")
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                first_model_call = False
            ended = time.perf_counter_ns(); wall_end = time.time_ns()
            projection_start = time.perf_counter_ns()
            keys = a.claim_set(a.extract(raw)); selected = [f for f in facts if a.key(f) in keys]
            projected = json.dumps({"answer": "", "claims": selected}, ensure_ascii=False) if selected else "REJECTED: no verified claim"
            full = projected if {a.key(f) for f in selected} == {a.key(f) for f in facts} else "REJECTED: incomplete catalog"
            projection_ms = (time.perf_counter_ns() - projection_start) / 1e6
            output = {CONDITIONS[0]: template, CONDITIONS[1]: raw or "REJECTED: model not invoked or failed",
                      CONDITIONS[2]: projected, CONDITIONS[3]: full}
            record = {"case_id": cid, "request_id": f"MATCHED-{index:04d}", "request": payload, "response": response,
                      "error": error, "raw_response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                      "model_invoked": gate["invoke"], "preexecution_policy": gate["policy_decision"],
                      "queue_wall_ns": queue, "start_wall_ns": wall_start, "end_wall_ns": wall_end,
                      "request_duration_ms": (ended - started) / 1e6, "batch_id": None, "batch_size": 1,
                      "gate_duration_ms": gate_ms, "template_duration_ms": template_ms, "projection_duration_ms": projection_ms,
                      "cold_load_inclusive": cold, "repetition": 1, "retry_count": 0,
                      "evidence_kind": "fresh_model_inference" if gate["invoke"] else "deterministic_execution"}
            capture.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"); capture.flush()
            raw_records.append(record)
            outputs.append({"case_id": cid, "raw": raw, "outputs": output, "model_invoked": gate["invoke"]})
            print(f"{index}/600 invoked={gate['invoke']} finish={(response or {}).get('done_reason', 'NOT_APPLICABLE')} error={error}", flush=True)
    loaded = client.get("/api/ps")
    if not any(r.get("name") == MODEL and r.get("size_vram", 0) > 0 for r in loaded.get("models", [])):
        raise RuntimeError("Local GPU allocation not confirmed")
    # Gold is loaded only after every runtime candidate/output has been captured.
    gold = a.unique(a.read(a.FROZEN / "strong_scoring_600.jsonl"))
    scored = []
    for record in outputs:
        cid = record["case_id"]
        for condition, final in record["outputs"].items():
            row = a.score_claims(final, record["raw"], runtime[cid], gold[cid], condition,
                                 record["model_invoked"] if condition != CONDITIONS[0] else False, None)
            row["evidence_kind"] = "deterministic_execution" if condition == CONDITIONS[0] else "fresh_model_inference"
            row["output_scope"] = "native prose unassessed" if condition == CONDITIONS[1] else "deterministically rendered structured claims"
            scored.append(row)
    a.write_csv(out / "matched_case_results.csv", scored)
    a.write_csv(out / "matched_summary.csv", a.summarize_internal(scored))
    from projects.uir_base.scripts.next_matched_analysis import analyze
    if a.digest(Path(__file__).with_name("next_matched_analysis.py")) != protocol["analysis_source_sha256"]:
        raise ValueError("Analysis source changed after freeze")
    analyze(root)
    a.write_json(out / "fresh_run_manifest.json", {"status": "COMPLETE_NOT_SUBMISSION_READY", "protocol_sha256": a.digest(path),
        "runner_sha256": a.digest(__file__), "model": installed[MODEL], "server_version": client.get("/api/version"),
        "gpu_before": gpu, "loaded_model_gpu_allocation": loaded,
        "N_requests": len(outputs), "N_model_calls": sum(r["model_invoked"] for r in outputs),
        "N_errors": sum(r["error"] is not None for r in raw_records),
        "raw_capture_sha256": a.digest(out / "raw_requests_responses.jsonl"),
        "template_sha256": hashlib.sha256(info.get("template", "").encode()).hexdigest(),
        "model_quantization": "Q4_0", "old_FP16_NF4_equivalence_claimed": False, "human_validation": False,
        "evidence_kind": "fresh_model_inference", "remote_inference": False})
    client.post("/api/generate", {"model": MODEL, "keep_alive": 0, "stream": False})
    client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    prepare(args.out) if args.prepare else execute(args.out)


if __name__ == "__main__":
    main()
