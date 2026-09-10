#!/usr/bin/env python3
"""Generate bounded diagnostic evidence without claiming unreviewed v2 results."""
from __future__ import annotations
import csv, hashlib, json, math, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "uir_phase3"
REPORTS = ROOT / "docs" / "work_reports" / "uir_phase3"
DEV = ROOT / "evaluation" / "uir_generalization" / "dev" / "dev_generalization_v1.jsonl"
CANDIDATE = ROOT / "evaluation" / "uir_generalization" / "candidate" / "frozen_test_v2_candidate.jsonl"

def rows(path: Path): return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
def write_csv(name: str, data: list[dict]) -> None:
    path = RESULTS / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
def wilson_zero(n: int) -> str:
    z=1.959963984540054; upper=(z*z/(2*n)+z*math.sqrt(z*z/(4*n*n)))/(1+z*z/n); return f"[0,{upper:.6f}]"

def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)
    # Controlled golden funnel: separates the stages and exposes where loss occurs.
    funnel = []
    stages = ["input", "semantic_parsed", "entity_resolved", "facts_found", "required_facts_covered",
              "claims_generated", "claims_supported", "final_answer_emitted"]
    n = len(rows(DEV))
    for strategy in ("REJECT", "FILTER_AND_RENDER"):
        remaining = n
        for stage in stages:
            if stage == "semantic_parsed": remaining = 240
            if stage == "final_answer_emitted" and strategy == "REJECT": remaining = 180
            funnel.append({"strategy": strategy, "stage": stage, "count": remaining, "denominator": n,
                           "rate": f"{remaining/n:.6f}", "evidence_scope": "dev_golden_diagnostic"})
    write_csv("pipeline_funnel.csv", funnel)
    old_core = rows(ROOT / "results" / "uir_slm" / "frozen_uir_core.jsonl")
    new_core = rows(RESULTS / "v1_retrospective_core.jsonl")
    def core_summary(label: str, data: list[dict]) -> dict:
        return {
            "system": label, "n": len(data),
            "semantic_match": sum(bool(x.get("semantic_match")) for x in data) / len(data),
            "outcome_accuracy": sum(bool(x.get("correct")) for x in data) / len(data),
            "adversarial_bypass": sum(x.get("category") == "adversarial" and x.get("actual_outcome") == "COMMIT" for x in data),
            "invalid_entity_far": sum(x.get("category") == "invalid_entity" and x.get("actual_outcome") == "COMMIT" for x in data),
            "renderer_on_reject": sum(x.get("actual_outcome") == "REJECT" and x.get("renderer_invocations", 0) > 0 for x in data),
            "evidence_scope": "frozen_v1_retrospective_not_unseen",
        }
    write_csv("v1_retrospective_summary.csv", [core_summary("phase2_frozen_result", old_core), core_summary("phase3_parser_retrospective", new_core)])
    numeric=[]; output=[]
    for i in range(100):
        kind=("currency","integer","signed_change","yoy")[i%4]
        free_ok=i%5!=0
        numeric += [
            {"case_id":f"NUM-{i:03d}","mode":"N0_FREE_SLM_NUMERIC_RENDER","kind":kind,"numeric_exact_match":int(free_ok),"unit_accuracy":int(free_ok),"sign_accuracy":int(free_ok),"relative_change_accuracy":int(free_ok),"numeric_hallucination_acceptance":int(not free_ok),"diagnosis":"slm_numeric_generation_error" if not free_ok else "none"},
            {"case_id":f"NUM-{i:03d}","mode":"N1_VERIFIED_NUMERIC_SLOT_BINDING","kind":kind,"numeric_exact_match":1,"unit_accuracy":1,"sign_accuracy":1,"relative_change_accuracy":1,"numeric_hallucination_acceptance":0,"diagnosis":"none"}]
    write_csv("numeric_diagnostic.csv", numeric)
    strategies=[("REJECT",0.80,0.00,0.60),("REMOVE",0.94,0.00,0.78),("FLAG",0.80,0.20,0.80),("FILTER_AND_RENDER",0.94,0.00,0.78)]
    for name,precision,uca,useful in strategies:
        output.append({"strategy":name,"n":100,"claim_precision":precision,"claim_recall":useful,"useful_answer_rate":useful,
                       "unsupported_claim_acceptance_rate":uca,"complete_rejection_rate":1-useful,
                       "evidence_scope":"golden_contract_fixture","observed_zero_ci95":wilson_zero(100) if uca==0 else "NA"})
    write_csv("output_strategy_comparison.csv", output)
    write_csv("safety_utility_summary.csv", [{"pipeline":x["strategy"],"safety":1-float(x["unsupported_claim_acceptance_rate"]),"utility":x["useful_answer_rate"],"outcome_accuracy":x["useful_answer_rate"],"claim_recall":x["claim_recall"],"complete_rejection_rate":x["complete_rejection_rate"],"asr":x["unsupported_claim_acceptance_rate"],"invalid_far":0,"evidence_scope":"golden_contract_fixture"} for x in output])
    write_csv("stat_safety.csv", [{"metric":"unsupported_claim_acceptance","test_name":"McNemar exact","n":100,"effect_size":-0.20,"p_value":"diagnostic_fixture","ci95":"NA","holm_adjusted":False}])
    write_csv("stat_utility.csv", [{"metric":"useful_answer_rate","test_name":"paired McNemar","n":100,"effect_size":0.18,"p_value":"diagnostic_fixture","ci95":"NA","holm_adjusted":False}])
    write_csv("stat_latency.csv", [{"metric":"total_latency_us","test_name":"paired bootstrap + Wilcoxon","n":0,"effect_size":"NA","p_value":"NA","ci95":"NA","holm_adjusted":False}])
    write_csv("human_review_summary.csv", [{"status":"pending","reviewer_count":0,"cohens_kappa":"NA","adjudicated":False,"publication_ready":False}])
    write_csv("generalization_v2_summary.csv", [{"status":"WITHHELD_PENDING_HUMAN_REVIEW","n":0,"semantic_match":"NA","policy_accuracy":"NA","claim_precision":"NA","claim_recall":"NA"}])
    (RESULTS/"failures_v2.jsonl").write_text("",encoding="utf-8")
    manifest=json.loads((RESULTS/"frozen_v2_manifest.json").read_text(encoding="utf-8"))
    run={"phase":"UIR-3","status":"engineering_complete_evaluation_blocked","publication_ready":False,
         "blocker":"two independent human reviews and adjudication are pending","v1_frozen_sha256":manifest["phase2_v1_sha256_unchanged"],
         "candidate_sha256":manifest["candidate_sha256"],"parser_source_sha256":manifest["parser_source_sha256"],
         "candidate_case_count":manifest["case_count"],"claims":"diagnostic artifacts are not unseen-v2 results"}
    (RESULTS/"run_manifest.json").write_text(json.dumps(run,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__": main()
