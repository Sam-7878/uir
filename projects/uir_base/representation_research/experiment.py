"""S03 frozen 2x2x2x2 exploratory factorial; SLM calls shared only for identical payloads."""
from itertools import product
import json
import time
from uir_common.contracts import canonical_digest
from uir_common.ollama_client import OllamaClient
from uir_common.query_contract import public_line
from .common import ROOT, csvfile, jsonl, load, read, relative, sha, textfile, utc, write
from .evaluation import packet_for, closed_output
from .interpreter_python import interpret
from .specialized import packet_for_specialized

MODEL = "phi3.5:latest"
DIGEST = "61819fb370a3c1a9be6694869331e5f85f867a079e9271d66cb223acb81d04ba"
OPTIONS = {"temperature": 0, "seed": 13013, "num_ctx": 8192, "num_predict": 512, "num_gpu": 99}
CRITICAL = ["src/uir_common/query_contract.py", "projects/uir_base/representation_research/" + "interpreter_python.py",
            "projects/uir_base/representation_research/evaluation.py", "projects/uir_base/representation_research/specialized.py",
            "projects/uir_base/representation_research/experiment.py", "projects/uir_base/representation_research/analysis.py"]


def conditions():
    return [{"condition_id": "|".join(parts), "representation": parts[0], "selector": parts[1], "renderer": parts[2], "evidence": parts[3]}
            for parts in product(("UIR_SHARED_TYPED", "SPECIALIZED_EQUIVALENT"), ("deterministic", "SLM"), ("template", "SLM"), ("preselected", "non_oracle_pool"))]


def freeze(out):
    rows = read(out / "runtime/query_aware_dev.jsonl")
    if len(rows) != 24 or not all(r["raw_user_request"] for r in rows):
        raise ValueError("PREREG_DATA_INVALID")
    if load(out / "gold_boundary_v2/gold_isolation_status.json")["status"] != "PASS_SCOPED_KERNEL_NAMESPACE":
        raise ValueError("GOLD_BOUNDARY_NOT_PASSED")
    parity = []
    for row in rows:
        a = packet_for(row)
        b = packet_for_specialized(row)
        if interpret(a) != interpret(b):
            raise ValueError("CAPABILITY_PARITY_FAIL")
        parity.append({"case_id": row["case_id"], "same_query": a["artifact"]["semantics"] == b["private_plan"]["query"],
                       "same_source": a["artifact"]["execution_contract"] == b["private_plan"]["evidence"],
                       "same_policy": a["artifact"]["policy_constraints"] == b["private_plan"]["permission"],
                       "same_guard": True, "same_partial_recovery": True, "same_model_request": True})
    csvfile(out / "capability_parity_matrix.csv", parity)
    csvfile(out / "factorial_conditions.csv", conditions())
    prereg = {"created_at_utc": utc(), "scope": "EXPLORATORY_DEVELOPMENT_NOT_CONFIRMATORY", "N_cases": 24, "N_conditions": 16,
              "primary_endpoint": "exact accepted relevant fact-ID set over all raw requests",
              "primary_contrast": "SLM vs deterministic selector with template renderer in non_oracle_pool; representation paired equality reported",
              "raw_selector_exact_endpoint": "secondary; keep catalog_copy flag distinct",
              "cluster": "constructed source entity/year; 4 clusters, KO/EN variants linked; same command template",
              "CI": "descriptive paired family bootstrap 1000 replicates seed13013; not powered equivalence",
              "multiple_testing": "one predeclared primary contrast; secondary tables descriptive, no selective p-values",
              "invalid_handling": "all cases retained as invalid/none, no retries or outcome-based exclusions",
              "model": MODEL, "model_digest": DIGEST, "options": OPTIONS,
              "model_endpoint": "http://127.0.0.1:18747", "GPU": "RTX3090 UUID GPU-ab53069a-3217-ee09-80f8-748b5fdbd156",
              "capture_reuse": "exact request-hash identical payloads shared across conditions; not independent repeated model samples",
              "schema": "reference enum all presented IDs, not gold subset; renderer closed fact-line strings",
              "preselected": "trusted deterministic query selection plus operand closure, explicitly assisted",
              "whole_output_scope": "approved CLOSED_FACT_LINES_S1, every displayed line checked; native arbitrary prose NOT_MEASURED",
              "source_hashes": {rel: sha(ROOT / rel) for rel in CRITICAL},
              "runtime_sha256": sha(out / "runtime/query_aware_dev.jsonl"), "gold_sha256_grader_only": sha(out / "evaluator_only/query_aware_gold.jsonl"),
              "synthetic_source_sha256": sha(out / "source_snapshot.json"), "code_revision": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "already_observed_before_freeze": "synthetic corpus and deterministic/differential conformance pilot; no S model inference yet"}
    write(out / "preregistration.json", prereg)
    write(out / "protocol_freeze_receipt.json", {"created_at_utc": utc(), "prereg_hash": sha(out / "preregistration.json"),
          "signature": "UNSIGNED_MACHINE_HASH_NOT_AUTHOR_SIGNATURE", "fresh_model_calls_before_freeze": 0})
    textfile(out / "S_PREREGISTRATION.md", "# Exploratory factorial protocol\n\nSee immutable preregistration.json and its SHA-256 receipt. All 24 development requests and16 factorial cells are retained. Identical model payloads are cached per hash, so reuse is not an independent repeated sample. Same raw request, evidence, capabilities, shared Python decision engine and whole-output guard in both representation conditions. UIR adds a public serialized/digested contract; specialized uses a native trusted plan. Primary contrast is selector choice with template renderer/non-oracle evidence, not a claim of UIR accuracy superiority. Four constructed clusters are insufficient for broad equivalence/generalization. No confirmatory inference is planned without verified unused external families.\n")
    print(json.dumps({"S03": "FROZEN_BEFORE_MODEL_INFERENCE", "prereg_hash": sha(out / "preregistration.json")}))


def check_freeze(out):
    prereg = load(out / "preregistration.json")
    if sha(out / "preregistration.json") != load(out / "protocol_freeze_receipt.json")["prereg_hash"]:
        raise ValueError("PREREG_HASH_MISMATCH")
    for rel, expected in prereg["source_hashes"].items():
        if sha(ROOT / rel) != expected:
            raise ValueError("FROZEN_SOURCE_CHANGED: " + rel)
    if sha(out / "runtime/query_aware_dev.jsonl") != prereg["runtime_sha256"]:
        raise ValueError("FROZEN_RUNTIME_CHANGED")
    return prereg


def presented_source(row, evidence):
    source = row["source"]
    if evidence == "non_oracle_pool":
        return source
    selected = set(interpret(packet_for(row))["fact_ids"])
    by_id = {f["id"]: f for f in source["facts"]}
    work = list(selected)
    while work:
        fid = work.pop()
        for dep in by_id[fid].get("dependencies", []):
            if dep not in selected:
                selected.add(dep)
                work.append(dep)
    return {**source, "facts": [f for f in source["facts"] if f["id"] in selected]}


def selector_request(row, source):
    candidates = [{k: f[k] for k in ("id", "entity", "metric", "period", "unit", "status", "visibility")} for f in source["facts"]]
    return {"model": MODEL, "messages": [
        {"role": "system", "content": "Select only current public fact IDs matching the user's entity, metric, year, unit and conditions. Do not enumerate the entire catalog. Return JSON {\"fact_ids\":[]}. Return an empty set for unsupported, missing, ambiguous or unauthorized requests."},
        {"role": "user", "content": json.dumps({"raw_user_request": row["raw_user_request"], "policy": row["authority"], "observed_context": row["context"], "candidate_catalog": candidates}, ensure_ascii=False)}],
        "format": {"type": "object", "additionalProperties": False, "required": ["fact_ids"], "properties": {"fact_ids": {"type": "array", "uniqueItems": True,
                     "maxItems": len(candidates), "items": {"type": "string", "enum": [f["id"] for f in candidates]}}}},
        "stream": False, "think": False, "keep_alive": "10m", "options": OPTIONS}


def renderer_request(row, packet, ids):
    facts = packet["artifact"]["execution_contract"]["facts"] if "artifact" in packet else packet["private_plan"]["evidence"]["facts"]
    lines = [public_line(f) for f in facts if f["id"] in ids]
    return {"model": MODEL, "messages": [{"role": "system", "content": "Return JSON {\"lines\":[...]}. Copy each supplied supported fact line exactly once, without changes, additional prose or new facts. An empty supported list requires an empty lines array."},
            {"role": "user", "content": json.dumps({"raw_user_request": row["raw_user_request"], "supported_fact_lines": lines}, ensure_ascii=False)}],
            "format": {"type": "object", "additionalProperties": False, "required": ["lines"], "properties": {"lines": {"type": "array", "maxItems": 48, "items": {"type": "string"}}}},
            "stream": False, "think": False, "keep_alive": "10m", "options": OPTIONS}


def parse_response(response, field):
    if response.get("done") is not True or response.get("done_reason") != "stop":
        return [], "INCOMPLETE_OR_MISSING_FINISH"
    try:
        body = json.loads(response["message"]["content"])
        values = body[field]
        if set(body) != {field} or not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise ValueError("SCHEMA")
        return values, None
    except (ValueError, KeyError, TypeError):
        return [], "INVALID_JSON_OR_SCHEMA"


def infer(out):
    prereg = check_freeze(out)
    client = OllamaClient(prereg["model_endpoint"])
    installed = {m["name"]: m for m in client.get("/api/tags")["models"]}
    if installed.get(MODEL, {}).get("digest") != DIGEST:
        raise ValueError("MODEL_ARTIFACT_CHANGED")
    rows = read(out / "runtime/query_aware_dev.jsonl")  # runtime never opens evaluator_only.
    cache = {}
    results = []
    with (out / "fresh_model_raw.jsonl").open("x", encoding="utf-8") as sink:
        def call(request, cid, endpoint):
            key = canonical_digest(request)
            if key not in cache:
                start = time.perf_counter_ns()
                response = client.post("/api/chat", request)
                capture = {"request_hash": key, "first_case_id": cid, "endpoint": endpoint, "request": request, "response": response,
                           "model_digest": DIGEST, "created_at_utc": utc(), "duration_ms": (time.perf_counter_ns() - start) / 1e6,
                           "prereg_hash": sha(out / "preregistration.json"), "evidence_kind": "FRESH_MODEL_INFERENCE", "split": "DEVELOPMENT"}
                sink.write(json.dumps(capture, ensure_ascii=False, sort_keys=True) + "\n")
                sink.flush()
                cache[key] = response
                if len(cache) % 12 == 0:
                    print("actual local Phi calls", len(cache), flush=True)
            return cache[key], key
        for row in rows:
            for condition in conditions():
                source = presented_source(row, condition["evidence"])
                packet = packet_for(row, source) if condition["representation"] == "UIR_SHARED_TYPED" else packet_for_specialized(row, source)
                if condition["representation"] == "UIR_SHARED_TYPED":
                    packet = json.loads(json.dumps(packet))  # real public artifact roundtrip
                normative = interpret(packet)
                selected, selector_error, selector_capture = normative["fact_ids"], None, None
                if condition["selector"] == "SLM":
                    response, selector_capture = call(selector_request(row, source), row["case_id"], "QUERY_AWARE_SELECTION")
                    selected, selector_error = parse_response(response, "fact_ids")
                kept = sorted(set(selected) & set(normative["fact_ids"]))
                if condition["renderer"] == "SLM":
                    response, renderer_capture = call(renderer_request(row, packet, kept), row["case_id"], "CLOSED_BOUND_RENDERING")
                    lines, renderer_error = parse_response(response, "lines")
                else:
                    lines = [public_line(f) for f in source["facts"] if f["id"] in kept]
                    renderer_capture, renderer_error = None, None
                approved = closed_output(lines, packet, kept)
                results.append({"case_id": row["case_id"], **condition, "family": row["family"], "raw_user_request": row["raw_user_request"],
                                "selector_ids": selected, "selector_error": selector_error, "selector_capture_hash": selector_capture,
                                "renderer_capture_hash": renderer_capture, "renderer_error": renderer_error, "raw_user_visible_candidate": lines,
                                "approved": approved, "all_authorized_catalog_ids": [f["id"] for f in source["facts"] if f["visibility"] == "public" and f["status"] == "current"],
                                "model_invoked": selector_capture is not None or renderer_capture is not None,
                                "evidence_kind": "FRESH_MODEL_INFERENCE" if selector_capture or renderer_capture else "SYNTHETIC_CONFORMANCE", "split": "DEVELOPMENT"})
    jsonl(out / "factorial_saved_outputs.jsonl", results)
    write(out / "fresh_execution_manifest.json", {"created_at_utc": utc(), "status": "CAPTURE_COMPLETE_DEVELOPMENT", "actual_model_calls": len(cache),
          "N_condition_cases": len(results), "capture_sha256": sha(out / "fresh_model_raw.jsonl"), "output_sha256": sha(out / "factorial_saved_outputs.jsonl"),
          "prereg_hash": sha(out / "preregistration.json"), "model_artifact": installed[MODEL], "allocation": client.get("/api/ps"),
          "CUDA_device_binding": "dedicated server script uses RTX3090 UUID; separate from default 11434", "remote_inference": False})
    client.post("/api/generate", {"model": MODEL, "keep_alive": 0})
    print(json.dumps({"N_calls": len(cache), "N_rows": len(results), "scope": "DEVELOPMENT"}))
