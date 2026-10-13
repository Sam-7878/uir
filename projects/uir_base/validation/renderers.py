"""R06 aligned output-layer DEVELOPMENT inference; all old results immutable."""
import argparse
from collections import Counter
import json
import subprocess
import time
from jsonschema import Draft202012Validator
from uir_common.contracts import FIELDS, canonical_digest, reject_gold
from uir_common.representation import FULL_SCHEMA, REFERENCE_SCHEMA, claim_key, parse_candidate, valid_claim
from uir_common.ollama_client import OllamaClient
from .common import FROZEN, OLD, OUT, ROOT, check_frozen, csvfile, jsonl, load, read, sha, utc, write

PHI = ("phi3.5:latest", "61819fb370a3c1a9be6694869331e5f85f867a079e9271d66cb223acb81d04ba")
MODELS = {"Phi-3.5": PHI}
OPTIONS = {"temperature": 0, "seed": 20261012, "num_ctx": 8192, "num_predict": 512, "num_gpu": 99}


def packet(case):
    facts = {f"F{i:03d}": f for i, f in enumerate(case["context_claims"])}
    for fact in facts.values(): valid_claim(fact)
    body = {"case_id": case["case_id"], "raw_request": case["input"], "authorized_catalog": facts,
            "output_requirements": "return the entire supplied authorized catalog, preserving every field",
            "policy_snapshot": "ALREADY_PRE_EXECUTION_ALLOWED_ORACLE_DEVELOPMENT",
            "evidence_snapshot": canonical_digest(facts)}
    body["contract_digest"] = canonical_digest(body)
    reject_gold(body)
    return body


def prepare():
    check_frozen()
    invoked = {r["case_id"] for r in read(OLD / "fresh_matched/raw_requests_responses.jsonl") if r["model_invoked"]}
    cases = [packet(r) for r in read(FROZEN / "strong_runtime_600.jsonl") if r["case_id"] in invoked]
    if len(cases) != 272: raise ValueError("OLD_DEVELOPMENT_COHORT_MISMATCH")
    jsonl(OUT / "renderer_runtime_packets.jsonl", cases)
    write(OUT / "renderer_protocol.json", {"status": "FROZEN_BEFORE_NEW_DEVELOPMENT_INFERENCE", "created_at_utc": utc(),
          "N_cases": len(cases), "N_calls": 544, "model": MODELS, "conditions": ["SEVEN_FIELD_NATIVE", "FACT_ID_BINDING"],
          "derived_conditions": ["DETERMINISTIC_CATALOG", "FACT_ID_PARTIAL_OFF"],
          "cohort": "same previously observed 272 Phi invocations; oracle-like output layer DEVELOPMENT, never unused holdout",
          "schema": {"SEVEN_FIELD_NATIVE": FULL_SCHEMA, "FACT_ID_BINDING": REFERENCE_SCHEMA}, "options": OPTIONS, "thinking": False, "retries": 0,
          "primary_endpoint": "all declared authorized facts returned exactly, all 272 requests; incomplete/missing incorrect",
          "authority": "same supplied facts/policy/contract/output scope in all conditions",
          "scope": "not raw-only interpretation, non-oracle retrieval, or representation-layer causal effect",
          "source_sha256": sha(__file__), "shared_contract_sha256": sha(ROOT / "src/uir_common/representation.py"),
          "runtime_sha256": sha(OUT / "renderer_runtime_packets.jsonl"),
          "uncertainty": "exploratory development counts; no confirmatory generalization claim, no significance tuning",
          "old_0_of_418": "frozen five/seven-field confounded historical result remains unchanged"})
    print("544 prospective Phi DEVELOPMENT calls frozen, seven-field vs reference format.")


def execute():
    protocol = load(OUT / "renderer_protocol.json")
    for path, digest in ((__file__, protocol["source_sha256"]), (ROOT / "src/uir_common/representation.py", protocol["shared_contract_sha256"]),
                         (OUT / "renderer_runtime_packets.jsonl", protocol["runtime_sha256"])):
        if sha(path) != digest: raise ValueError("FROZEN_RENDERER_DEPENDENCY_CHANGED")
    client = OllamaClient("http://127.0.0.1:18747")
    installed = {r["name"]: r for r in client.get("/api/tags")["models"]}
    model, digest = PHI
    if installed.get(model, {}).get("digest") != digest: raise ValueError("PHI_ARTIFACT_MISMATCH")
    info = client.post("/api/show", {"model": model})
    gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name,uuid,memory.used", "--format=csv,noheader"], text=True)
    if "GPU-ab53069a-3217-ee09-80f8-748b5fdbd156" not in gpu: raise RuntimeError("RTX3090_NOT_PRESENT")
    rows = read(OUT / "renderer_runtime_packets.jsonl")
    path = OUT / "renderer_fresh_raw.jsonl"
    with path.open("x", encoding="utf-8") as sink:
        for condition in protocol["conditions"]:
            for i, case in enumerate(rows):
                reject_gold(case)
                system = ("You are an output formatter for an already authorized catalog, not a policy solver. "
                          "Return JSON only, no descriptions, no additional keys. Copy contract_digest exactly. "
                          "SEVEN_FIELD_NATIVE means every catalog fact as a claims item with all seven string fields, "
                          "including unit and period; empty values are copied only if present in the catalog. "
                          "FACT_ID_BINDING means all supplied fact IDs as fact_ids, not numbers or invented prose.")
                request = {"model": model, "messages": [{"role": "system", "content": system + " Condition: " + condition},
                            {"role": "user", "content": json.dumps(case, ensure_ascii=False)}],
                           "format": protocol["schema"][condition], "stream": False, "think": False, "keep_alive": "10m", "options": OPTIONS}
                start_wall = time.time_ns(); start = time.perf_counter_ns()
                response = None; error = None
                try: response = client.post("/api/chat", request)
                except Exception as exc: error = type(exc).__name__ + ":" + str(exc)
                record = {"case_id": case["case_id"], "condition": condition, "model": "Phi-3.5", "model_digest": digest,
                          "request": request, "response": response, "error": error, "retry": 0,
                          "start_wall_ns": start_wall, "end_wall_ns": time.time_ns(), "duration_ms": (time.perf_counter_ns()-start)/1e6,
                          "cold_load_inclusive": condition == protocol["conditions"][0] and i == 0,
                          "evidence_kind": "fresh_model_inference", "split": "DEVELOPMENT"}
                sink.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"); sink.flush()
                if (i+1) % 20 == 0: print(condition, i+1, "/272", (response or {}).get("done_reason"), flush=True)
    allocation = client.get("/api/ps")
    if not any(r["name"] == model and r.get("size_vram", 0) > 0 for r in allocation["models"]):
        raise RuntimeError("GPU_ALLOCATION_NOT_CONFIRMED")
    write(OUT / "renderer_execution_manifest.json", {"status": "CAPTURE_COMPLETE_DEVELOPMENT", "created_at_utc": utc(), "N_calls": 544,
          "raw_sha256": sha(path), "protocol_sha256": sha(OUT / "renderer_protocol.json"), "model": installed[model],
          "gpu_before": gpu, "allocation": allocation, "server": client.get("/api/version"),
          "template_sha256": canonical_digest(info.get("template", "")), "parameters": info.get("parameters"),
          "remote_inference": False, "human_validation": False})
    client.post("/api/generate", {"model": model, "keep_alive": 0})


def evaluate(candidate, case, condition, *, partial=True, finished=True):
    catalog = case["authorized_catalog"]; errors = []; accepted = []
    try:
        if not finished: raise ValueError("INCOMPLETE_RESPONSE")
        parsed = parse_candidate(candidate, "reference" if condition == "FACT_ID_BINDING" else "full")
        if parsed["contract_digest"] != case["contract_digest"]: raise ValueError("CONTRACT_IDENTITY_MISMATCH")
        if condition == "FACT_ID_BINDING":
            accepted = [catalog[r] for r in parsed["fact_ids"] if r in catalog]
            errors.extend("UNKNOWN_REFERENCE" for r in parsed["fact_ids"] if r not in catalog)
        else:
            unique = set()
            for claim in parsed["claims"]:
                valid_claim(claim); key = claim_key(claim)
                if key in unique: raise ValueError("DUPLICATE_CLAIM")
                unique.add(key)
            # Native syntax condition records its own unsupported values, rather than crediting projection.
            accepted = parsed["claims"]
    except Exception as exc:
        errors.append(type(exc).__name__ + ":" + str(exc).splitlines()[0]); accepted = []
    required = {claim_key(c) for c in catalog.values()}
    emitted = {claim_key(c) for c in accepted}
    full = bool(required) and emitted == required
    unsupported = bool(emitted - required)
    if not partial and not full: accepted = []; emitted = set(); unsupported = False
    return {"complete": full, "partial": bool(emitted) and not full and not unsupported, "accepted_nonempty": bool(emitted),
            "structured_unsupported": unsupported, "errors": errors,
            "accepted_claims": accepted, "rendered": json.dumps({"claims": accepted}, ensure_ascii=False, sort_keys=True),
            "native_prose_AUCR": "NOT_MEASURED"}


def score():
    manifest = load(OUT / "renderer_execution_manifest.json")
    if sha(OUT / "renderer_fresh_raw.jsonl") != manifest["raw_sha256"]: raise ValueError("RENDERER_RAW_CHANGED")
    cases = {r["case_id"]: r for r in read(OUT / "renderer_runtime_packets.jsonl")}
    captures = read(OUT / "renderer_fresh_raw.jsonl")
    if len({(r["case_id"], r["condition"]) for r in captures}) != 544: raise ValueError("MISSING_DUPLICATE_RENDERER_CAPTURE")
    results = []
    for row in captures:
        response = row["response"] or {}; raw = response.get("message", {}).get("content", "")
        finished = response.get("done") is True and response.get("done_reason") == "stop"
        conditions = [row["condition"]] + (["FACT_ID_PARTIAL_OFF"] if row["condition"] == "FACT_ID_BINDING" else [])
        for condition in conditions:
            score = evaluate(raw, cases[row["case_id"]], row["condition"], partial=condition != "FACT_ID_PARTIAL_OFF", finished=finished)
            results.append({"case_id": row["case_id"], "condition": condition, "finished": finished, "finish_reason": response.get("done_reason", "MISSING"),
                            "evidence_kind": "fresh_model_inference" if condition != "FACT_ID_PARTIAL_OFF" else "counterfactual_replay",
                            **{k: v for k, v in score.items() if k not in {"accepted_claims", "rendered"}}})
    for cid, case in cases.items():
        results.append({"case_id": cid, "condition": "DETERMINISTIC_CATALOG", "finished": True, "finish_reason": "NOT_APPLICABLE",
                        "evidence_kind": "deterministic_execution", "complete": True, "partial": False, "accepted_nonempty": True,
                        "structured_unsupported": False, "errors": [], "native_prose_AUCR": "NOT_MEASURED"})
    csvfile(OUT / "renderer_results.csv", results)
    conditions = sorted({r["condition"] for r in results})
    summary = [{"condition": c, "N": len([r for r in results if r["condition"] == c]),
                "N_complete": sum(r["complete"] for r in results if r["condition"] == c),
                "N_partial": sum(r["partial"] for r in results if r["condition"] == c),
                "N_accepted_nonempty": sum(r["accepted_nonempty"] for r in results if r["condition"] == c),
                "N_structured_unsupported": sum(r["structured_unsupported"] for r in results if r["condition"] == c),
                "N_model_calls": 272 if c in {"SEVEN_FIELD_NATIVE", "FACT_ID_BINDING"} else 0,
                "scope": "preselected oracle-like output-layer development, not representation causal comparison",
                "native_prose_AUCR": "NOT_MEASURED"} for c in conditions]
    csvfile(OUT / "renderer_summary.csv", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--prepare", action="store_true"); parser.add_argument("--execute", action="store_true"); parser.add_argument("--score", action="store_true")
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.execute: execute()
    elif args.score: score()
    else: parser.error("Use explicit --prepare / --execute / --score")
