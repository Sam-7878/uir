"""Role-separated, source-first AI/CNL development pilot; never silently confirmatory.

Qwen sees question briefs without values/IDs/gold. Ministral sees raw requests and
original documents without proposed labels. Phi runs in a mount-isolated worker.
Scorer-only code re-reads raw source independently of runtime decisions.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import time

from uir_common.contracts import canonical_digest
from uir_common.ollama_client import OllamaClient
from .artifacts import RunStore
from ..policy import ROOT, sha, utc, write_once
from .gold_reference import source_values, reference_gold
from .source_catalog import build_catalog
from .runner import DOCS

DESIGNER = "qwen3:4b-instruct-2507-q4_K_M"
REVIEWER = "ministral-3:14b"
PYTHON = "/usr/bin/python3.14"


def namespace_args(runtime_dir, gold_path, *, hidden=True, overlay=None, mode="probe"):
    site = Path(sys.prefix) / "lib/python3.14/site-packages"
    args = ["bwrap", "--unshare-all", "--share-net", "--die-with-parent", "--new-session", "--clearenv",
            "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
            "--ro-bind", str(site), "/deps", "--ro-bind", str(ROOT / "src"), "/app/src",
            "--ro-bind", str(ROOT / "Cargo.toml"), "/app/Cargo.toml",
            "--ro-bind", str(ROOT / "projects/uir_base/representation_research"), "/app/projects/uir_base/representation_research",
            "--ro-bind", str(Path(__file__).parent), "/app/projects/uir_base/electronics_research/stage116",
            "--ro-bind", str(runtime_dir), "/input", "--dir", str(gold_path.parent),
            "--ro-bind", str(overlay or gold_path), str(gold_path)]
    if hidden:
        args += ["--tmpfs", str(gold_path.parent)]
    args += ["--setenv", "PYTHONPATH", "/app:/app/src:/deps", "--setenv", "HOME", "/tmp", "--setenv", "PATH", "/usr/bin:/bin",
             "--chdir", "/app", PYTHON, "-S", "-m", "projects.uir_base.electronics_research.stage116.role_runtime",
             "--runtime", "/input/runtime.jsonl", "--probe-gold", str(gold_path), "--mode", mode]
    return args


def role_call(store, client, installed, name, model, messages, schema, *, budget):
    request = {"model": model, "messages": messages, "format": schema, "stream": False, "think": False, "keep_alive": "0s",
               "options": {"temperature": 0, "seed": 11623, "num_ctx": 16384, "num_predict": budget, "num_gpu": 99}}
    start = time.perf_counter_ns()
    result = client.post("/api/chat", request, timeout=600)
    store.write("curation/" + name + "_capture.json", {"request": request, "request_hash": canonical_digest(request), "response": result,
                "model_digest": installed[model]["digest"], "elapsed_ms": (time.perf_counter_ns() - start) / 1e6,
                "role": name, "role_context_isolated": True, "independent_human": False, "timestamp_utc": utc()})
    if result.get("done_reason") != "stop":
        raise ValueError(name + "_INCOMPLETE_OUTPUT_RETAINED")
    return json.loads(result["message"]["content"])


def prepare(directory):
    store = RunStore(directory)
    store.create()
    for name in ("runtime", "private_evaluator_only", "curation", "isolation", "experiments", "scoring", "preregistration"):
        store.path(name).mkdir()
    cargo = ROOT / "projects/uir_base/results/116_electronics_confirmatory_2026_10_23/run_20261023T084603Z/source_registry/bytes/cargo_Cargo.toml"
    treasury = ROOT / "projects/uir_base/results/116_electronics_confirmatory_2026_10_23/run_20261023T085231Z/source_registry/bytes/treasury_debt_2024_first5.json"
    values = source_values(treasury, cargo)
    store.write("source_lineage.json", {str(p.relative_to(ROOT)): sha(p) for p in (cargo, treasury)})
    store.write("code_snapshot.json", {str(p.relative_to(ROOT)): sha(p) for p in Path(__file__).parent.glob("*.py")})
    # This protocol precedes all curation/model responses. No claim of powered confirmation.
    store.write("preregistration/pilot_protocol.json", {"status": "FROZEN_DEVELOPMENT_PILOT_NOT_CONFIRMATORY", "N": 24,
                "families": ["US-Treasury:DebtToPenny", "GitHub:rust-lang/cargo"], "independent_parent_clusters": 2,
                "curation": {"designer": DESIGNER, "blind_semantic_reviewer": REVIEWER, "runtime": "phi3.5:latest"},
                "gold_source": "SCORER_ONLY_ORIGINAL_JSON_TOML_PLUS_DECLARED_CNL", "candidate_values_in_designer_prompt": False,
                "gold_in_reviewer_prompt": False, "review_pass_rule": "24_CASE_COORDINATES_AGREE_EXACTLY_NO_DROPPING",
                "holdout": "FUTURE_NEW_PARENT_FAMILIES_AND_TEMPLATE_FAMILIES_REQUIRED", "promote_pilot_to_confirmation": False,
                "method_review": "AI_ONLY_ROLE_SEPARATION_NOT_INDEPENDENT_TEAM_OR_HUMAN", "native_prose_AUCR": "NOT_MEASURED",
                "independent_implementation_identity": "DETERMINISTIC_SCORER_AND_RUNTIME_SEPARATE_CODE_SAME_CODING_AGENT"})
    protocol_hash = sha(store.path("preregistration/pilot_protocol.json"))
    store.write("preregistration/pilot_freeze_receipt.json", {"protocol_sha256": protocol_hash, "model_calls_before_freeze": 0,
                "signature": "MACHINE_HASH_NOT_AUTHOR_SIGNATURE", "created_at_utc": utc()})
    facts = build_catalog(treasury, cargo)
    treasury_targets = [r for r in values if r["entity"] == "US_TREASURY"][:6]
    cargo_targets = [r for r in values if r["entity"] == "CARGO"][:6]
    briefs = []
    for i, target in enumerate(treasury_targets + cargo_targets):
        for language in ("EN", "KO"):
            briefs.append({"case_id": f"P116-{i:02}-{language}", "language": language, **{k: target[k] for k in ("entity", "metric", "period", "unit")}})
    client = OllamaClient("http://127.0.0.1:18747")
    installed = {m["name"]: m for m in client.get("/api/tags")["models"]}
    store.write("curation/role_model_manifest.json", {k: installed[k] for k in (DESIGNER, REVIEWER, "phi3.5:latest")})
    schema = {"type": "object", "required": ["requests"], "properties": {"requests": {"type": "array", "minItems": 24, "maxItems": 24,
              "items": {"type": "object", "required": ["case_id", "raw_user_request"], "properties": {"case_id": {"type": "string"}, "raw_user_request": {"type": "string"}}}}}}
    answer = role_call(store, client, installed, "question_designer", DESIGNER, [
        {"role": "system", "content": 'Write one exact controlled-language query per brief, preserving every field. EN grammar: "At <period>, return <metric> for <entity> in <unit>." KO grammar: "<period> 기준 <entity>의 <metric> 항목을 <unit> 단위로 응답하세요." Keep entity/metric/unit identifiers unchanged. Do not provide answers or IDs. Output JSON {"requests":[{"case_id":"...","raw_user_request":"..."}]}.'},
        {"role": "user", "content": json.dumps({"briefs": briefs}, ensure_ascii=False)}], schema, budget=3072)
    requests = answer["requests"]
    print(json.dumps({"phase": "designer_captured", "requests": len(requests)}), flush=True)
    if len(requests) != 24 or {r["case_id"] for r in requests} != {r["case_id"] for r in briefs}:
        raise ValueError("CURATOR_ROW_IDS_INVALID_NO_SILENT_REPAIR")
    gold = []
    for row in requests:
        gold.append({"case_id": row["case_id"], **reference_gold(row["raw_user_request"], values)})
    store.jsonl("private_evaluator_only/gold.jsonl", gold)
    review_schema = {"type": "object", "required": ["annotations"], "properties": {"annotations": {"type": "array", "minItems": 24, "maxItems": 24,
                     "items": {"type": "object", "required": ["case_id", "entity", "metric", "period", "unit"],
                     "properties": {k: {"type": "string"} for k in ("case_id", "entity", "metric", "period", "unit")}}}}}
    reviewed = role_call(store, client, installed, "blind_semantic_reviewer", REVIEWER, [
        {"role": "system", "content": 'Independently annotate each raw query using the original source documents. Do not answer with numeric values. Return JSON {"annotations":[{"case_id":"...","entity":"...","metric":"...","period":"...","unit":"..."}]}. Entity identifiers US_TREASURY and CARGO denote the respective sources. USD_CENT means exact USD multiplied by100; Cargo numeric version components use COUNT and edition uses YEAR. Do not see or infer another judge label. Preserve literal requested identifiers.'},
        {"role": "user", "content": json.dumps({"requests": requests, "treasury_original": json.loads(treasury.read_text()), "cargo_original_toml": cargo.read_text()}, ensure_ascii=False)}], review_schema, budget=4096)
    annotations = reviewed["annotations"]
    by_id = {r["case_id"]: r for r in annotations}
    agreements = [{"case_id": g["case_id"], "agrees": all(by_id.get(g["case_id"], {}).get(k) == v for k, v in g["semantics"].items())} for g in gold]
    passed = len(annotations) == len(by_id) == 24 and all(r["agrees"] for r in agreements)
    print(json.dumps({"phase": "blind_review", "agree": sum(r["agrees"] for r in agreements), "N": 24}), flush=True)
    store.write("curation/agreement.json", {"N": 24, "agree": sum(r["agrees"] for r in agreements), "case_results": agreements,
                "human_ground_truth": False, "semantic_uncertainty": "AI_AGREEMENT_IS_NOT_TRUTH", "all_rows_retained": True,
                "curation_gate": "PASS_SCOPED_AI_CNL" if passed else "BLOCKED_DISAGREEMENT_NO_SILENT_FILTER"})
    runtime = []
    for row in requests:
        # Facts from both domains and all dates/metrics are always supplied, never a gold subset.
        runtime.append({**row, "authority": {"version": "P116-1", "decision": "ALLOW", "approved": False},
                        "source": {"version": "SOURCE116-PILOT-1", "facts": facts, "trusted_provenance": sorted({f["provenance"] for f in facts})},
                        "family": "US-Treasury:DebtToPenny" if "US_TREASURY" in row["raw_user_request"] else "GitHub:rust-lang/cargo",
                        "split": "DEVELOPMENT_NEW_SOURCE_PILOT", "rights_class": "PRIVATE"})
    store.jsonl("runtime/runtime.jsonl", runtime)
    for g in gold:
        relevant = [f for f in facts if all(f[k] == v for k, v in g["semantics"].items())]
        if len(relevant) != 1 or relevant[0]["value"] != g["value"] or len(facts) - len(relevant) < 3:
            raise ValueError("SCORER_RAW_SOURCE_REGISTRY_DISAGREEMENT_OR_NO_DISTRACTORS")
    store.write("scoring/reference_gate.json", {"raw_source_reextraction_matches": True, "runtime_guard_or_interpreter_used_by_scorer": False,
                "all_catalog_equals_gold": False, "case_N": 24, "catalog_size": len(facts), "minimum_distractors": len(facts) - 1,
                "implementation_staff_independent": False, "scoring_gold_hidden_from_runtime": "PENDING_KERNEL_TEST"})
    if not passed:
        return store, False
    gold_path = store.path("private_evaluator_only/gold.jsonl")
    changed = [{**g, "value": "WRONG_LABEL", "semantics": {"entity": "WRONG"}} for g in gold]
    store.jsonl("private_evaluator_only/mutated_gold.jsonl", changed)
    commands = [("positive", namespace_args(store.path("runtime"), gold_path, hidden=False)),
                ("hidden", namespace_args(store.path("runtime"), gold_path)),
                ("mutated", namespace_args(store.path("runtime"), gold_path, overlay=store.path("private_evaluator_only/mutated_gold.jsonl")))]
    probes = {}
    for name, args in commands:
        result = subprocess.run(args, text=True, capture_output=True, close_fds=True, timeout=60)
        probes[name] = {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        store.write("isolation/" + name + ".json", probes[name])
    isolated = (probes["positive"]["returncode"] != 0 and "GOLD_VISIBLE_TO_RUNTIME" in probes["positive"]["stderr"]
                and probes["hidden"]["returncode"] == probes["mutated"]["returncode"] == 0
                and probes["hidden"]["stdout"] == probes["mutated"]["stdout"])
    print(json.dumps({"phase": "kernel_gold_boundary", "passed": isolated}), flush=True)
    store.write("isolation/gold_boundary_receipt.json", {"status": "PASS_SCOPED_KERNEL_MOUNT" if isolated else "BLOCKED",
                "positive_control_gold_visible_rejected": probes["positive"]["returncode"] != 0,
                "actual_gold_canonical_path_overlaid_then_hidden": True, "canonical_label_mutation_invariance": isolated,
                "host_workspace_not_mounted": True, "network": "HOST_LOOPBACK_SHARED_NOT_NETWORK_ISOLATED", "inherited_fds": "CLOSED",
                "threat_assumptions": "TRUSTED_HOST_KERNEL_AND_LOCAL_OLLAMA_SERVER_NO_HOST_ROOT_COMPROMISE", "runtime_model_calls": 0})
    return store, isolated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--infer-pilot", action="store_true")
    args = parser.parse_args()
    store, ready = prepare(args.results_dir)
    if args.infer_pilot and ready:
        print(json.dumps({"phase": "pilot_factorial_started", "split": "DEVELOPMENT_NOT_CONFIRMATORY"}), flush=True)
        command = namespace_args(store.path("runtime"), store.path("private_evaluator_only/gold.jsonl"), mode="infer")
        with store.path("experiments/runtime_capture.jsonl").open("x") as output, store.path("experiments/runtime_stderr.log").open("x") as error:
            result = subprocess.run(command, stdout=output, stderr=error, text=True, close_fds=True, timeout=1800)
        store.write("experiments/runtime_receipt.json", {"returncode": result.returncode, "gold_boundary_used": True,
                    "split": "DEVELOPMENT_NEW_SOURCE_PILOT_NOT_CONFIRMATORY"})
    store.write("README.md", "# LOCAL ONLY role-separated AI/CNL development pilot\n\nQwen question design, Ministral blinded annotation, raw-source machine scorer and gold-hidden Phi runtime. Never promote this observed pilot into confirmation.\n")
    report = DOCS / ("ROLE_SEPARATED_PILOT_" + store.directory.name + ".md")
    write_once(report, "# Role-separated pilot checkpoint\n\n"
               f"Run `{store.directory.relative_to(ROOT)}`. Ready for pilot after curation/OS checks: `{ready}`. "
               "Actual model role captures, semantic disagreements, namespace positive/negative and canonical-label mutation probes are retained. "
               "New scalar sources and question phrasing only; this is AI_ONLY controlled-language development, not human semantic truth, independent research staff or a powered confirmatory experiment. "
               "Two parent families remain inadequate for a broad inferential generalization claim; future confirmation needs new source/template families and its own preregistration/precision review.\n")
    store.write("work_report_lineage.json", {str(report.relative_to(ROOT)): sha(report)})
    store.seal()
    print(json.dumps({"run": str(store.directory), "pilot_gate_ready": ready, "verified_files": store.verify()}))


if __name__ == "__main__":
    main()
