"""Blinded packets, historical replay diagnostics and external failure inventory.

All experiments here are labelled deterministic replay or post-hoc diagnostics.
They are never mixed with historical GPU inference as fresh model evidence.
"""
from __future__ import annotations
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from projects.uir_base.scripts.revision_audit import BASE, DEFAULT_OUT, FROZEN, ROOT, extract, read, unique, key, write_csv, write_json, digest, score_claims, summarize_internal


def blinded_packets(out):
    runtime = unique(read(FROZEN/"strong_runtime_600.jsonl"))
    gold = unique(read(FROZEN/"strong_scoring_600.jsonl"))
    strata = defaultdict(list)
    for cid, r in runtime.items():
        strata[gold[cid]["stratum"], r["language"]].append(cid)
    rng = random.Random(20261011)
    ids = []
    for stratum in sorted(strata):
        ids += rng.sample(sorted(strata[stratum]), min(10, len(strata[stratum])))
    ids.sort()
    packet_dir = out/"annotation_packets"; packet_dir.mkdir(exist_ok=True)
    packet = [runtime[cid] for cid in ids]
    for annotator in ("H1", "H2"):
        with (packet_dir/f"{annotator}_blinded_cases.jsonl").open("w", encoding="utf-8") as f:
            for r in packet:
                # Case ID is needed for joining but no stratum, gold or AI label is given.
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True)+"\n")
        write_csv(packet_dir/f"{annotator}_labels_template.csv", [{"case_id": cid, "annotator_id": annotator,
            "parseable": "", "intent": "", "entity": "", "attribute": "", "period": "", "conditions_valid": "",
            "policy_decision": "", "ambiguity": "", "explanation": "", "minutes_spent": ""} for cid in ids])
    write_csv(out/"human_labels.csv", [], ["case_id", "annotator_id", "decision", "explanation", "reviewed_at"])
    write_csv(out/"adjudication.csv", [], ["case_id", "H1_original", "H2_original", "adjudicator_id", "final_decision", "reason"])
    write_json(packet_dir/"sampling_manifest.json", {"seed": 20261011, "N": len(ids), "case_ids": ids,
        "sampling": "post-hoc stratified 10 per stratum x language; not prospective validation",
        "human_completed": False, "independent_reviewers_required": 2,
        "runtime_sha256": digest(FROZEN/"strong_runtime_600.jsonl")})


def replay(out):
    from evaluation.uir_phase4d.pipelines import build_internal_request
    runtime = unique(read(FROZEN/"strong_runtime_600.jsonl")); gold = unique(read(FROZEN/"strong_scoring_600.jsonl"))
    historical = {(r["pipeline"],r["case_id"]): r for r in read(BASE/"uir_phase4d/per_case_evidence_actual.jsonl")}
    d1 = unique(read(BASE/"uir_phase4f/d1_constrained_raw_600.jsonl"))
    rows = []
    for condition in ("NO_LLM_TRUSTED_SLOT_TEMPLATE", "C5_SAME_PROJECTION_REPLAY", "D1_CANDIDATE_REBINDING_REPLAY", "C8_NO_PARTIAL_REPLAY"):
        for cid, case in sorted(runtime.items()):
            # Runtime gating uses only request, registry and external policy.
            gate = build_internal_request("C8_FINAL_UIR_B6", case)
            facts = case.get("context_claims", []); source = ""; raw = ""; selected = []
            if gate["invoke"]:
                if condition == "NO_LLM_TRUSTED_SLOT_TEMPLATE":
                    selected = facts
                elif condition == "C5_SAME_PROJECTION_REPLAY":
                    record = historical["C5_GUARDRAIL_STYLE",cid]
                    source = digest(BASE/"uir_phase4d/per_case_evidence_actual.jsonl") if not rows else "same_frozen_capture"
                    raw = record["generation"]["raw_response"]
                    obj = extract(raw) or {}
                    proposed = obj.get("claims", [])
                    if isinstance(proposed, list):
                        keys = {key(c) for c in proposed if isinstance(c, dict)}
                        selected = [f for f in facts if key(f) in keys]
                elif condition == "D1_CANDIDATE_REBINDING_REPLAY":
                    raw = d1[cid]["raw_response"]; proposed = (extract(raw) or {}).get("claims", [])
                    if isinstance(proposed, list):
                        selectors = {(str(c.get("entity_id", "")), str(c.get("attribute", "")), str(c.get("period", ""))) for c in proposed if isinstance(c, dict)}
                        selected = [f for f in facts if (str(f.get("entity_id", "")),str(f.get("attribute", "")),str(f.get("period", ""))) in selectors]
                else:
                    record = historical["C8_FINAL_UIR_B6",cid]; raw = record["generation"]["raw_response"]
                    refs = (extract(raw) or {}).get("fact_refs", [])
                    if isinstance(refs, list):
                        selected = [f for idx,f in enumerate(facts,1) if f"fact_{idx:03d}" in refs]
                    # Completeness is runtime catalog completeness, NOT evaluator gold.
                    if len({key(f) for f in selected}) != len({key(f) for f in facts}):
                        selected = []
            final = json.dumps({"answer":"Deterministically rendered trusted facts.", "claims":selected}) if selected else "REJECTED: no verified claim"
            row = score_claims(final, raw, case, gold[cid], condition, False, None)
            row["unassessed_prose"] = False
            row["whole_output_safety_verified"] = bool(selected)
            row["evidence_kind"] = "deterministic_historical_replay_not_fresh_model_inference"
            row["source_capture"] = source
            rows.append(row)
    write_csv(out/"ablation_case_results.csv", rows)
    write_csv(out/"matched_replay_summary.csv", summarize_internal(rows))


def external_diagnostics(out):
    errors = []; cases = []
    for task in ("finqa", "halueval"):
        for cond in ("C1", "C8"):
            path = BASE/f"uir_phase4e/qwen_{task}_{cond}_raw.jsonl"
            for r in read(path):
                raw = r["raw_response"]; obj = extract(raw)
                category = "empty_output" if not raw.strip() else "json_truncated_or_missing" if cond == "C8" and obj is None else "not_strict_answer" if cond == "C1" and task == "finqa" and not re.fullmatch(r"\s*[-+]?\d+(?:\.\d+)?%?\s*",raw) else "requires_task_specific_semantic_evaluation"
                errors.append({"case_id": r["case_id"], "dataset":task, "model":"Qwen2.5-7B", "condition":cond,
                    "category":category, "stored_max_tokens": r.get("max_tokens"), "json_parseable":obj is not None,
                    "truncation_suspected":cond=="C8" and raw.rstrip().endswith((",", ":", "[")) or (cond=="C8" and raw.count("{")>raw.count("}")),
                    "finish_reason_recorded":False, "unsupported_claim_metric_available":False,
                    "raw_response_sha256":r["raw_response_sha256"], "source_file":str(path.relative_to(ROOT))})
    for name in ("finqa", "halueval_qa"):
        path = FROZEN/f"{name}_runtime_200.jsonl"
        for r in read(path):
            cases.append({"dataset":name,"case_id":r["case_id"],"source_original_id":r.get("source_original_id"),
                "source_index":r.get("source_index"),"source_row_hash":r.get("source_row_hash")})
    write_csv(out/"external_error_taxonomy.csv", errors)
    write_json(out/"external_case_manifest.json", {"cases":cases,"cohort_kind":"historical_subset; NOT new holdout", "provenance_source": str((BASE/"uir_phase4d/OFFICIAL_BENCHMARK_PROVENANCE.json").relative_to(ROOT))})
    # New holdout candidates are disjoint from frozen external source rows.
    import hashlib
    selected = {r.get("source_index") for r in read(FROZEN/"finqa_runtime_200.jsonl")}
    official = json.loads((ROOT/"projects/uir_base/evaluation/uir_phase4c/official_sources/FinQA/test.json").read_text())
    candidates = [idx for idx in range(len(official)) if idx not in selected]
    rng = random.Random(20261011); holdout = rng.sample(candidates, 200)
    write_json(out/"new_holdout_protocol.json", {"seed":20261011,"dataset":"FinQA/test.json","source_sha256":digest(ROOT/"projects/uir_base/evaluation/uir_phase4c/official_sources/FinQA/test.json"),
        "source_indices":sorted(holdout),"disjoint_from_historical_200":not(set(holdout)&selected),
        "status":"FROZEN_NOT_EXECUTED", "development_only":"Use the historical 200 for adapter development; no prompt/validator tuning on this new holdout", "models":["microsoft/Phi-3.5-mini-instruct","Qwen/Qwen2.5-7B-Instruct"]})


def languages(out):
    from evaluation.uir_phase4d.runtime.uir_compiler import UIRCompiler
    compiler=UIRCompiler(); groups=defaultdict(list)
    for r in read(FROZEN/"strong_runtime_600.jsonl"):
        result=compiler.compile(raw_text=r["input"],requested_entity=r["requested_entity"],requested_attribute=r["requested_attribute"],requested_period=r["requested_period"],language=r["language"])
        groups[r["language"]].append(result)
    write_csv(out/"language_breakdown.csv", [{"language":lang,"N":len(rs),"compile_success":sum(r.compiles for r in rs),
        "annotation_independent_correctness":"NOT_HUMAN_VALIDATED", "scope":"historical trusted slot metadata supplied; not free-NL semantic accuracy"} for lang,rs in sorted(groups.items())])


def boundary():
    from uir_common.contracts import RuntimeContract, bind_references, reject_gold
    # Audit hook enforces file access separation in this interpreter.
    def deny_gold(event,args):
        if event=="open" and isinstance(args[0],(str,bytes)):
            path=str(args[0]).lower()
            if "scoring_" in path or "gold" in Path(path).name:
                raise PermissionError("evaluation gold inaccessible in runtime test")
    sys.addaudithook(deny_gold)
    runtime=read(FROZEN/"strong_runtime_600.jsonl")
    for r in runtime:
        reject_gold(r)
        contract=RuntimeContract(r["requested_entity"],r["requested_attribute"],r["requested_period"],"fixture-policy","fixture-evidence")
        catalog={str(i):f for i,f in enumerate(r.get("context_claims",[]))}
        bind_references(contract,catalog,list(catalog))
    try:
        (FROZEN/"strong_scoring_600.jsonl").read_text()
    except PermissionError:
        print("PASS: 600 runtime contracts/projections; evaluation gold open actively denied")
    else:
        raise AssertionError("Gold access not denied")


def main():
    if len(sys.argv)>1 and sys.argv[1]=="gold-boundary":
        boundary();return
    DEFAULT_OUT.mkdir(parents=True,exist_ok=True)
    blinded_packets(DEFAULT_OUT); replay(DEFAULT_OUT); external_diagnostics(DEFAULT_OUT); languages(DEFAULT_OUT)
    print("Generated blinded packets, matched deterministic replays and external diagnostics")


if __name__=="__main__":
    main()
