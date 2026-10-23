"""Generation-only runtime. Does not import gold_reference or open source gold."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

from uir_common.contracts import canonical_digest, reject_gold
from uir_common.query_contract import make_artifact, public_line
from uir_common.ollama_client import OllamaClient
from projects.uir_base.representation_research.interpreter_python import interpret
from projects.uir_base.representation_research.evaluation import closed_output
from .interchange import to_native


def compile_query(raw):
    english = re.fullmatch(r"At ([^,]+), return ([A-Za-z0-9_]+) for ([A-Z_]+) in ([A-Z_]+)\.", raw)
    korean = re.fullmatch(r"([^ ]+) 기준 ([A-Z_]+)의 ([A-Za-z0-9_]+) 항목을 ([A-Z_]+) 단위로 응답하세요\.", raw)
    if english:
        period, metric, entity, unit = english.groups()
    elif korean:
        period, entity, metric, unit = korean.groups()
    else:
        raise ValueError("CLARIFICATION_UNSUPPORTED_CNL")
    return {"entity": entity, "metric": metric, "period": period, "unit": unit, "predicate": None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--probe-gold", type=Path, required=True)
    parser.add_argument("--mode", choices=("probe", "infer"), required=True)
    parser.add_argument("--grammar", choices=("pilot", "release_snapshot"), default="pilot")
    parser.add_argument("--split", choices=("DEVELOPMENT_NEW_SOURCE_PILOT", "SECONDARY_SLM_FIRST_EXPOSURE"), default="DEVELOPMENT_NEW_SOURCE_PILOT")
    args = parser.parse_args()
    query_parser = compile_query
    if args.grammar == "release_snapshot":
        from .confirm_runtime import parse_release_query
        query_parser = parse_release_query
    try:
        args.probe_gold.read_bytes()
    except (PermissionError, FileNotFoundError):
        pass
    else:
        raise RuntimeError("GOLD_VISIBLE_TO_RUNTIME")
    rows = [json.loads(x) for x in args.runtime.read_text().splitlines() if x.strip()]
    reject_gold(rows)
    print(json.dumps({"type": "boundary", "gold_read": "BLOCKED", "runtime_sha256": hashlib.sha256(args.runtime.read_bytes()).hexdigest(),
                      "fd_scope": "CLOSED_INHERITED_FDS", "network_scope": "HOST_LOOPBACK_SHARED_NOT_NETWORK_ISOLATED"}), flush=True)
    if args.mode == "probe":
        if args.grammar == "release_snapshot":
            return  # boundary-only probe: no primary case decisions or LLM calls
        for row in rows:
            try:
                semantics = query_parser(row["raw_user_request"])
                artifact = make_artifact(semantics, row["authority"], row["source"])
                result = interpret({"artifact": artifact, "authority": row["authority"], "context": {},
                                    "current_evidence_version": row["source"]["version"], "current_evidence_sha256": canonical_digest(row["source"])})
            except ValueError:
                result = {"state": "CLARIFICATION", "fact_ids": []}
            print(json.dumps({"case_id": row["case_id"], "result": result}, sort_keys=True), flush=True)
        return
    client = OllamaClient("http://127.0.0.1:18747")
    model = "phi3.5:latest"
    installed = {m["name"]: m for m in client.get("/api/tags")["models"]}
    if installed.get(model, {}).get("digest") != "61819fb370a3c1a9be6694869331e5f85f867a079e9271d66cb223acb81d04ba":
        raise ValueError("PHI_ARTIFACT_CHANGED")
    cache = {}
    def call(messages, field):
        request = {"model": model, "messages": messages, "stream": False, "keep_alive": "10m", "format": "json",
                   "options": {"temperature": 0, "seed": 116, "num_ctx": 8192, "num_predict": 512, "num_gpu": 99}}
        key = canonical_digest(request)
        if key not in cache:
            start = time.perf_counter_ns()
            response = client.post("/api/chat", request)
            print(json.dumps({"type": "model_capture", "request_hash": key, "request": request, "response": response,
                              "model_digest": installed[model]["digest"], "latency_ms": (time.perf_counter_ns() - start) / 1e6}), flush=True)
            cache[key] = response
        response = cache[key]
        try:
            if response.get("done_reason") != "stop": raise ValueError("INCOMPLETE")
            values = json.loads(response["message"]["content"])[field]
            if not isinstance(values, list) or not all(isinstance(x, str) for x in values): raise ValueError("TYPE")
            return values, key, None
        except (ValueError, KeyError, TypeError):
            return [], key, "INVALID_OR_INCOMPLETE"
    for row in rows:
        try:
            semantics = query_parser(row["raw_user_request"])
            artifact = make_artifact(semantics, row["authority"], row["source"])
            packet = {"artifact": artifact, "authority": row["authority"], "context": {},
                      "current_evidence_version": row["source"]["version"], "current_evidence_sha256": canonical_digest(row["source"])}
        except ValueError:
            for representation in ("UIR", "SPECIALIZED"):
                for selector in ("DETERMINISTIC", "SLM"):
                    for renderer in ("TEMPLATE", "SLM"):
                        print(json.dumps({"type": "outcome", "case_id": row["case_id"], "representation": representation, "selector": selector,
                                          "renderer": renderer, "compile_error": True, "fact_ids": [], "raw_selector_ids": [], "display": ""}), flush=True)
            continue
        for representation in ("UIR", "SPECIALIZED"):
            actual = json.loads(json.dumps(packet)) if representation == "UIR" else to_native(packet)
            normative = interpret(actual)["fact_ids"]
            for selector in ("DETERMINISTIC", "SLM"):
                selected, selector_hash, error = normative, None, None
                if selector == "SLM":
                    selected, selector_hash, error = call([
                        {"role": "system", "content": 'Select only current public facts requested by the raw user query. Return JSON {"fact_ids":[]}. Do not enumerate the catalog.'},
                        {"role": "user", "content": json.dumps({"raw_user_request": row["raw_user_request"], "authority": row["authority"], "catalog": row["source"]["facts"]}, ensure_ascii=False)}], "fact_ids")
                kept = sorted(set(selected) & set(normative))
                for renderer in ("TEMPLATE", "SLM"):
                    lines = [public_line(f) for f in row["source"]["facts"] if f["id"] in kept]
                    renderer_hash, render_error = None, None
                    if renderer == "SLM":
                        lines, renderer_hash, render_error = call([
                            {"role": "system", "content": 'Copy every supplied supported line exactly. No other prose. Return JSON {"lines":[]}.'},
                            {"role": "user", "content": json.dumps({"raw_user_request": row["raw_user_request"], "supported_lines": lines}, ensure_ascii=False)}], "lines")
                    approved = closed_output(lines, actual, kept)
                    print(json.dumps({"type": "outcome", "case_id": row["case_id"], "representation": representation, "selector": selector,
                                      "renderer": renderer, "fact_ids": approved["fact_ids"], "display": approved["user_visible_output"], "state": approved["state"],
                                      "raw_selector_ids": selected, "candidate_lines": lines, "selector_capture": selector_hash, "renderer_capture": renderer_hash,
                                      "selector_error": error, "renderer_error": render_error, "scope": "CLOSED_FACT_LINES_S1", "split": args.split}), flush=True)
    print(json.dumps({"type": "end", "actual_model_calls": len(cache), "allocation": client.get("/api/ps")}), flush=True)


if __name__ == "__main__":
    main()
