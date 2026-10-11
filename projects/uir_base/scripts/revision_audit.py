"""Independent read-only re-scoring of historical raw evidence (W00-W03/W11).

Never calls historical aggregate writers. Gold is loaded only in this evaluator.
Stored score/correct/unsupported/schema flags are deliberately not trusted.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "Cargo.toml").is_file())
BASE = ROOT / "projects/uir_base/results"
FROZEN = BASE / "uir_phase4d/frozen_inputs"
DEFAULT_OUT = BASE / "mdpi_revision_2026_10_11"
CLAIM_FIELDS = ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance")
SCHEMA = {
    "type": "object", "required": ["answer", "claims"],
    "properties": {"answer": {"type": "string"}, "claims": {"type": "array", "items": {
        "type": "object", "required": ["claim_type", "entity_id", "attribute", "value", "provenance"],
        "properties": {k: {"type": "string"} for k in CLAIM_FIELDS}}}}
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def unique(rows):
    result = {r["case_id"]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate case IDs")
    return result


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]) if rows else fields or [])
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def parse(text):
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except (ValueError, TypeError):
        return None


def extract(text):
    obj = parse(text)
    if obj is not None:
        return obj
    left, right = text.find("{"), text.rfind("}")
    return parse(text[left:right+1]) if 0 <= left < right else None


def key(claim):
    return tuple(str(claim.get(k, "")) for k in CLAIM_FIELDS)


def claim_set(obj):
    return {key(c) for c in (obj or {}).get("claims", []) if isinstance(c, dict)} if isinstance((obj or {}).get("claims", []), list) else set()


def wilson(k, n):
    if not n:
        return None, None
    z = 1.959963984540054
    p, d = k/n, 1+z*z/n
    centre = (p+z*z/(2*n))/d
    spread = z/d*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return max(0., centre-spread), min(1., centre+spread)


def eligible(gold):
    return gold.get("expected_outcome") == "COMMIT" and not any(gold.get(k, False) for k in ("is_adversarial", "is_invalid_entity", "is_policy_violation"))


def score_claims(final, raw, runtime, gold, pipeline, invoked, latency):
    """Two independent axes: claim-set utility and whole-output assessment gaps."""
    parsed, raw_parsed = extract(final), extract(raw)
    rejected = not final.strip() or final.lstrip().upper().startswith("REJECTED:")
    emitted = claim_set(parsed) if not rejected else set()
    raw_emitted = claim_set(raw_parsed)
    catalog = {key(c) for c in runtime.get("context_claims", [])}
    required = {key(c) for c in gold.get("expected_claims", [])}
    supported = emitted & catalog
    relevant = supported & required
    unsupported = emitted - catalog
    policy_failure = bool(emitted) and (gold.get("is_policy_violation", False) or gold.get("is_invalid_entity", False))
    # Nonempty prose isn't proof of factual support. Don't silently score it safe.
    unassessed = not rejected and (parsed is None or bool(str(parsed.get("answer", "")).strip())) and pipeline != "C8_FINAL_UIR_B6"
    claim_safe = not unsupported and not policy_failure
    full = bool(required) and emitted == required and claim_safe
    partial = bool(relevant) and claim_safe and not full
    state = "FULL" if full else "PARTIAL" if partial else "NONE"
    e = eligible(gold)
    recall = len(relevant)/len(required) if required else None
    return {
        "case_id": runtime["case_id"], "pipeline": pipeline, "language": runtime.get("language", "unknown"),
        "source_cluster": runtime.get("source_row_hash", runtime["case_id"]),
        "stratum": gold.get("stratum", "unknown"), "commit_eligible": e,
        "accepted": not rejected, "nonempty_accepted": not rejected and bool(emitted),
        "model_invoked": bool(invoked), "safe_claim_answered": bool(emitted) and claim_safe,
        "unassessed_prose": bool(unassessed), "whole_output_safety_verified": not rejected and claim_safe and not unassessed,
        "unsupported_accepted": bool(unsupported), "policy_or_entity_violation": policy_failure,
        "raw_emitted_claims": len(raw_emitted), "accepted_emitted_claims": len(emitted),
        "supported_claims": len(supported), "relevant_claims": len(relevant), "gold_required_claims": len(required),
        "recall": recall, "complete": full and e, "partial": partial and e,
        "claim_state": state, "actual_output_state": "ABSTAIN" if rejected else "NONEMPTY_CLAIMS" if emitted else "PROSE_OR_EMPTY_CLAIMS",
        "end_to_end_ms": latency, "raw_claim_keys": json.dumps(sorted(raw_emitted)),
        "accepted_claim_keys": json.dumps(sorted(emitted)), "gold_required_keys": json.dumps(sorted(required)),
    }


def summarize_internal(rows):
    result = []
    for pipeline, group in itertools.groupby(sorted(rows, key=lambda r: r["pipeline"]), key=lambda r: r["pipeline"]):
        rs = list(group); es = [r for r in rs if r["commit_eligible"]]
        assert all(r["gold_required_claims"] > 0 for r in es)
        n, ne = len(rs), len(es)
        full = sum(r["complete"] for r in es); partial = sum(r["partial"] for r in es)
        macro = sum(r["recall"] for r in es)/ne
        cca = full/ne
        assert macro+1e-12 >= cca
        unsupported = sum(r["unsupported_accepted"] for r in rs)
        nonempty = sum(r["nonempty_accepted"] for r in rs)
        low, high = wilson(unsupported, n)
        clo, chi = wilson(unsupported, nonempty)
        result.append({"pipeline": pipeline, "N_all": n, "N_eligible": ne,
            "N_accepted": sum(r["accepted"] for r in rs), "N_nonempty_claims": nonempty,
            "N_model_invoked": sum(r["model_invoked"] for r in rs),
            "N_safe_claim_answered": sum(r["safe_claim_answered"] for r in rs),
            "N_unassessed_prose": sum(r["unassessed_prose"] for r in rs),
            "full": full, "partial": partial, "none": ne-full-partial,
            "CCA": cca, "macro_required_claim_recall": macro,
            "micro_required_claim_recall": sum(r["relevant_claims"] for r in es)/sum(r["gold_required_claims"] for r in es),
            "claim_supported_coverage": (full+partial)/ne,
            "unsupported_accepted_cases": unsupported, "AUCR_all_requests": unsupported/n,
            "AUCR_nonempty_accepted": unsupported/nonempty if nonempty else None,
            "AUCR_all_ci_low": low, "AUCR_all_ci_high": high,
            "AUCR_accepted_ci_low": clo, "AUCR_accepted_ci_high": chi,
            "scope": "structured_claim_array_only; unassessed prose is NOT verified safe"})
    return result


def yes_no(value):
    tokens = re.findall(r"\b(yes|no)\b", str(value).lower())
    return tokens[0].title() if tokens and all(x == tokens[0] for x in tokens) else None


def score_halu(raw, model, pipeline, runtime, gold):
    obj = extract(raw)
    if pipeline == "C1":
        raw_label = yes_no(raw)
        valid = raw_label is not None
        final = raw_label if valid else None
        reason = "native_label" if valid else "invalid_or_ambiguous_label"
    elif model == "Phi-3.5":
        raw_label = yes_no((obj or {}).get("judgement", ""))
        quote = str((obj or {}).get("evidence_quote", "")).strip()
        valid = raw_label is not None and bool(quote) and quote.lower() in runtime["knowledge"].lower()
        final = raw_label if valid else None
        reason = "exact_quote_contract" if valid else "schema_or_missing_label_or_nonmatching_quote"
    else:
        raw_label = yes_no((obj or {}).get("overall_hallucination", ""))
        evaluations = (obj or {}).get("claim_evaluations", [])
        # Validate types, IDs and complete coverage. No default No on parse failure.
        from evaluation.uir_phase4d.adapters.halueval_adapter import halueval_prompt_phase4d
        _, _, meta = halueval_prompt_phase4d(runtime, "H2_UIR_CONTRACT")
        ids = {x.get("claim_id") for x in evaluations if isinstance(x, dict)} if isinstance(evaluations, list) else set()
        valid = raw_label is not None and bool(evaluations) and ids == set(meta["c_chunks"])
        if valid:
            valid = all(isinstance(x, dict) and isinstance(x.get("supported"), bool) and (not x["supported"] or x.get("evidence_id") in meta["k_chunks"]) for x in evaluations)
        final = ("Yes" if any(not x["supported"] for x in evaluations) else "No") if valid else None
        reason = "reference_contract; lexical support is not semantic entailment" if valid else "malformed_or_incomplete_reference_contract"
    raw_correct = raw_label == gold["gold_judgement"]
    final_correct = final == gold["gold_judgement"]
    return {"case_id": runtime["case_id"], "model": model, "pipeline": pipeline,
        "gold_label": gold["gold_judgement"], "raw_label": raw_label, "raw_correct": raw_correct,
        "raw_json_valid": parse(raw) is not None, "contract_valid": valid,
        "projected_answer": final, "final_correct": final_correct,
        "accepted": valid, "e2e_correct": valid and final_correct,
        "raw_correct_and_valid": raw_correct and valid, "error_reason": reason,
        "raw_response_sha256": hashlib.sha256(raw.encode()).hexdigest()}


def aggregate_halu(rows):
    aggregates, transitions = [], []
    for (model, pipeline), group in itertools.groupby(sorted(rows, key=lambda r: (r["model"], r["pipeline"])), key=lambda r: (r["model"], r["pipeline"])):
        rs = list(group); n = len(rs)
        nc, nv, nj = (sum(r[k] for r in rs) for k in ("raw_correct", "contract_valid", "raw_correct_and_valid"))
        assert max(0, nc+nv-n) <= nj <= min(nc, nv)
        aggregates.append({"model": model, "pipeline": pipeline, "N": n,
            "n_raw_correct": nc, "n_contract_valid": nv, "n_intersection": nj,
            "n_e2e_correct": sum(r["e2e_correct"] for r in rs), "n_raw_label_missing": sum(r["raw_label"] is None for r in rs),
            "raw_semantic_accuracy": nc/n, "contract_validity": nv/n,
            "accepted_e2e_accuracy": sum(r["e2e_correct"] for r in rs)/n,
            "intersection_lower_bound": max(0,nc+nv-n), "e2e_definition": "contract_valid AND final_correct"})
        for c in (False, True):
            for v in (False, True):
                transitions.append({"model": model, "pipeline": pipeline, "table": "raw_correct_by_contract_valid", "left": c, "right": v,
                    "count": sum(r["raw_correct"] == c and r["contract_valid"] == v for r in rs)})
        for c in (False, True):
            for f in (False, True):
                transitions.append({"model": model, "pipeline": pipeline, "table": "raw_correct_to_final_correct", "left": c, "right": f,
                    "count": sum(r["raw_correct"] == c and r["final_correct"] == f for r in rs)})
    return aggregates, transitions


def paired(rows):
    import numpy as np
    from scipy.stats import binomtest
    by_pipeline = defaultdict(dict)
    for r in rows:
        if r["commit_eligible"]:
            by_pipeline[r["pipeline"]][r["case_id"]] = r
    target = by_pipeline["C8_FINAL_UIR_B6"]
    result = []
    for pipeline in sorted(by_pipeline):
        if pipeline == "C8_FINAL_UIR_B6":
            continue
        other = by_pipeline[pipeline]
        assert set(other) == set(target)
        for metric in ("complete", "safe_claim_answered"):
            pairs = [(bool(other[k][metric]), bool(target[k][metric])) for k in sorted(target)]
            counts = Counter(pairs); n01, n10 = counts[False, True], counts[True, False]
            p = float(binomtest(min(n01,n10), n01+n10).pvalue) if n01+n10 else 1.0
            clusters = defaultdict(list)
            for cid, (a,b) in zip(sorted(target),pairs):
                clusters[target[cid]["source_cluster"]].append(int(b)-int(a))
            values = np.array([(sum(v),len(v)) for v in clusters.values()], dtype=float)
            rng = np.random.default_rng(20261011)
            draws = rng.integers(0,len(values),size=(10000,len(values)))
            sampled = values[draws].sum(axis=1)
            differences = sampled[:,0]/sampled[:,1]
            ci_low,ci_high = np.quantile(differences,[0.025,0.975])
            result.append({"baseline": pipeline, "target": "C8_FINAL_UIR_B6", "metric": metric,
                "N": len(pairs), "n00": counts[False,False], "n01": n01, "n10": n10, "n11": counts[True,True],
                "risk_difference": (n01-n10)/len(pairs), "p_exact": p,
                "paired_cluster_ci_low": float(ci_low), "paired_cluster_ci_high": float(ci_high),
                "N_source_clusters": len(clusters), "bootstrap_seed": 20261011, "bootstrap_repetitions": 10000,
                "p_holm": None, "family": "all_18_C8_vs_baseline_complete_and_claim_coverage", "interpretation": "difference test; not equivalence"})
    running = 0.
    for rank, row in enumerate(sorted(result, key=lambda r: r["p_exact"])):
        running = max(running, min(1.,row["p_exact"]*(len(result)-rank)))
        row["p_holm"] = running
    return result


def run(out):
    from jsonschema import Draft202012Validator
    validator = Draft202012Validator(SCHEMA)
    out.mkdir(parents=True, exist_ok=True)
    sources = [FROZEN/"strong_runtime_600.jsonl", FROZEN/"strong_scoring_600.jsonl",
        BASE/"uir_phase4d/per_case_evidence_actual.jsonl", BASE/"uir_phase4f/d1_constrained_raw_600.jsonl",
        FROZEN/"halueval_qa_runtime_200.jsonl", FROZEN/"halueval_qa_scoring_200.jsonl"]
    runtime, gold = (unique(read(p)) for p in sources[:2])
    assert set(runtime) == set(gold) and len(runtime) == 600
    evidence = read(sources[2]); seen = set(); scored = []; latency_rows = []
    for r in evidence:
        pair = r["pipeline"], r["case_id"]
        if pair in seen:
            raise ValueError(f"duplicate {pair}")
        seen.add(pair)
        g = r.get("generation", {}); t = r.get("timing", {})
        scored.append(score_claims(r["final_output"], g.get("raw_response", ""), runtime[r["case_id"]], gold[r["case_id"]], r["pipeline"], r["model_invoked"], t.get("end_to_end_ms")))
        latency_rows.append({"case_id": r["case_id"], "pipeline": r["pipeline"], "model_invoked": r["model_invoked"],
            "model_ms": t.get("model_ms"), "end_to_end_ms": t.get("end_to_end_ms"),
            "compiler_ms": t.get("compiler_ms"), "policy_ms": t.get("policy_eval_ms"), "retrieval_ms": t.get("retrieval_ms"),
            "validation_ms": t.get("validation_ms"), "input_tokens": g.get("input_tokens"), "output_tokens": g.get("output_tokens"),
            "cold_warm": "NOT_RECORDED", "repetitions": 1, "batch_latency_shared": True})
    assert len(evidence) == 5400
    d1_audit = []
    d1_rows = read(sources[3])
    assert set(unique(d1_rows)) == set(runtime)
    for r in d1_rows:
        raw = r["raw_response"]; obj = parse(raw)
        valid = obj is not None and validator.is_valid(obj)
        d1_audit.append({"case_id": r["case_id"], "raw_json_valid": obj is not None, "raw_schema_valid": valid,
            "stored_schema_valid": r.get("schema_valid"), "flag_disagrees": valid != r.get("schema_valid"),
            "raw_response_sha256": hashlib.sha256(raw.encode()).hexdigest()})
        scored.append(score_claims(raw, raw, runtime[r["case_id"]], gold[r["case_id"]], "D1_EXTERNAL_CONSTRAINED_DECODING", True, r.get("latency_ms")))
    assert len(d1_audit) == 600
    hrs, hgs = (unique(read(p)) for p in sources[4:6])
    halu_rows = []
    for model in ("Phi-3.5", "Qwen2.5-7B"):
        for pipeline in ("C1", "C8"):
            path = BASE / (f"uir_phase4d/halueval_predictions_actual_{pipeline}.jsonl" if model == "Phi-3.5" else f"uir_phase4e/qwen_halueval_{pipeline}_raw.jsonl")
            sources.append(path)
            rs = unique(read(path)); assert set(rs) == set(hrs)
            for cid, row in rs.items():
                raw = row.get("raw_response", row.get("generation", {}).get("raw_response", ""))
                halu_rows.append(score_halu(raw, model, pipeline, hrs[cid], hgs[cid]))
    summary = summarize_internal(scored)
    hsummary, transitions = aggregate_halu(halu_rows)
    write_csv(out/"metrics_case_level.csv", scored)
    write_csv(out/"internal_utility_recomputed.csv", summary)
    write_csv(out/"d1_schema_case_audit.csv", d1_audit)
    write_csv(out/"halueval_case_audit.csv", halu_rows)
    write_csv(out/"halueval_recomputed.csv", hsummary)
    write_csv(out/"halueval_transition_tables.csv", transitions)
    write_csv(out/"paired_statistics.csv", paired(scored))
    write_csv(out/"latency_case_results.csv", latency_rows)
    import numpy as np
    latency_summary=[]
    for pipeline in sorted({r["pipeline"] for r in latency_rows}):
        for subset in ("all_workload","model_invoked"):
            rs=[r for r in latency_rows if r["pipeline"]==pipeline and (subset=="all_workload" or r["model_invoked"])]
            times=[r["end_to_end_ms"] for r in rs if r["end_to_end_ms"] is not None]
            latency_summary.append({"pipeline":pipeline,"subset":subset,"N":len(rs),"N_timed":len(times),
                "mean_ms":float(np.mean(times)) if times else None,"p50_ms":float(np.quantile(times,.5)) if times else None,
                "p95_ms":float(np.quantile(times,.95)) if times else None,"p99_ms":float(np.quantile(times,.99)) if times else None,
                "interpretation":"historical matched-batch workload latency; not transformer speedup"})
    write_csv(out/"latency_summary.csv",latency_summary)
    cohorts = [{"case_id": cid, "internal_600": True, "adversarial_subset": bool(g["is_adversarial"]),
        "commit_eligible_subset": eligible(g), "stratum": g["stratum"], "source_row_hash": g["source_row_hash"]} for cid, g in sorted(gold.items())]
    write_csv(out/"cohort_manifest.csv", cohorts)
    manifest = {"release": "mdpi_revision_2026_10_11", "evaluator": str(Path(__file__).relative_to(ROOT)), "evaluator_sha256": digest(__file__),
        "inference_rerun": False, "evidence_kind": "historical_actual_model_captures_on_constructed_benchmarks; not real-user logs",
        "sources": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in sources],
        "cohorts": {"internal": 600, "eligible_subset": sum(eligible(g) for g in gold.values()), "adversarial_subset": sum(g["is_adversarial"] for g in gold.values())},
        "D1": {"N": 600, "raw_json_valid": sum(r["raw_json_valid"] for r in d1_audit), "raw_schema_valid": sum(r["raw_schema_valid"] for r in d1_audit)},
        "HaluEval": hsummary, "internal": summary,
        "limitations": ["Prose outside structured claims has not been independently adjudicated", "No human annotations fabricated", "Matched replays are not fresh model runs", "Historical model revisions/metadata are not independently verified by hashes"]}
    write_json(out/"evidence_manifest.json", manifest)
    mh = digest(out/"evidence_manifest.json")
    table_dir = out/"generated_tables"; table_dir.mkdir(exist_ok=True)
    table = [f"% evidence_manifest_sha256: {mh}", r"\begin{tabular}{lrrr}", r"Condition & N & CCA & Macro recall \\"]
    for row in summary:
        name = row["pipeline"].replace("_", r"\_")
        table.append(f"{name} & {row['N_eligible']} & {row['CCA']:.6f} & {row['macro_required_claim_recall']:.6f} " + r"\\")
    table.append(r"\end{tabular}")
    (table_dir/"internal_utility.tex").write_text("\n".join(table)+"\n")
    (out/"generated_metrics.tex").write_text(f"% evidence_manifest_sha256: {mh}\n" + r"\newcommand{\DOneSchemaValidCount}{"+str(manifest["D1"]["raw_schema_valid"])+"}\n"+r"\newcommand{\DOneTotalCount}{600}"+"\n")
    write_csv(out/"claim_evidence_map.csv", [{"manuscript_location": "tab:internal_utility", "claim": "CCA and recall", "case_file": "metrics_case_level.csv", "aggregate_file": "internal_utility_recomputed.csv", "manifest_sha256": mh},
        {"manuscript_location": "tab:external_results", "claim": "HaluEval accuracy/validity/intersection", "case_file": "halueval_case_audit.csv", "aggregate_file": "halueval_recomputed.csv", "manifest_sha256": mh},
        {"manuscript_location": "tab:grammar_comparison", "claim": "D1 schema validity", "case_file": "d1_schema_case_audit.csv", "aggregate_file": "evidence_manifest.json", "manifest_sha256": mh}])
    print(json.dumps({"release": manifest["release"], "D1": manifest["D1"], "HaluEval": hsummary}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    run(parser.parse_args().out)
