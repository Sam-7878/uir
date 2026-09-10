#!/usr/bin/env python3
"""Aggregate final Phase-3B semantic, safety, utility, factuality and statistics."""
from __future__ import annotations
import argparse, csv, json, math, random
from collections import defaultdict
from pathlib import Path

from sys import path as sys_path
sys_path.insert(0, str(Path(__file__).resolve().parents[1] / "uir_slm"))
from paired_statistics import mcnemar_exact, paired_bootstrap_delta, percentile

def read(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
def ratio(a,b): return a/b if b else 0.0
def mean(xs):
    xs=list(xs); return sum(xs)/len(xs) if xs else 0.0
def write_csv(path, rows, fields=None):
    fields=fields or list(rows[0])
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
def summary(group):
    generated=sum(r["metrics"]["generated_claims"] for r in group); supported=sum(r["metrics"]["supported_claims"] for r in group)
    required=sum(r["metrics"]["required_claims"] for r in group); recalled=sum(r["metrics"]["recalled_claims"] for r in group)
    accepted=sum(r["metrics"]["accepted_claims"] for r in group); bad=sum(r["metrics"]["accepted_unsupported_claims"] for r in group)
    commits=[r for r in group if r["expected_outcome"]=="COMMIT"]
    return {"n":len(group),"outcome_accuracy":mean(r["correct_outcome"] for r in group),
            "claim_precision":ratio(accepted-bad,accepted),"claim_recall":ratio(recalled,required),
            "useful_answer_rate":ratio(sum(bool(r["accepted_claims_data"]) for r in commits),len(commits)),
            "complete_rejection_rate":mean(r["actual_outcome"]=="REJECT" for r in group),
            "partial_answer_rate":mean(bool(r.get("partial_answer")) for r in group),
            "unsupported_claim_acceptance_rate":ratio(bad,accepted),
            "invalid_entity_far":ratio(sum(not r.get("entity_valid",True) and r["actual_outcome"]=="COMMIT" for r in group),sum(not r.get("entity_valid",True) for r in group)),
            "attack_success_rate":ratio(sum(r.get("attack_success",False) for r in group),sum(r.get("expected_outcome")=="REJECT" for r in group)),
            "policy_bypass_rate":ratio(sum(r.get("policy_bypass",False) for r in group),sum(not r.get("policy_valid",True) for r in group)),
            "renderer_on_reject_rate":ratio(sum(r.get("renderer_invocation_on_reject_path",False) for r in group),sum(r["expected_outcome"]=="REJECT" for r in group)),
            "entity_lock_violation_rate":mean(r.get("entity_lock_violation",False) for r in group)}
def holm(rows):
    eligible=sorted([(float(r["raw_p"]),i) for i,r in enumerate(rows) if r["raw_p"]!="NA"])
    running=0.0; m=len(eligible)
    for rank,(p,i) in enumerate(eligible): running=max(running,min(1.0,p*(m-rank))); rows[i]["holm_p"]=running
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",type=Path,required=True); ap.add_argument("--core",type=Path,required=True); ap.add_argument("--dataset",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    raw=read(a.raw); core=read(a.core); dataset={r["case_id"]:r for r in read(a.dataset)}
    (a.out/"outputs_raw.jsonl").write_bytes(a.raw.read_bytes())
    claims=[]
    for r in raw:
        accepted={json.dumps(x,sort_keys=True) for x in r["accepted_claims_data"]}
        claims += [{"case_id":r["case_id"],"pipeline":r["pipeline"],"suite":r["suite"],"claim":c,"accepted":json.dumps(c,sort_keys=True) in accepted} for c in r["generated_claims_data"]]
    (a.out/"claims_raw.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in claims),encoding="utf-8")
    pipelines=sorted({r["pipeline"] for r in raw}); primary=[r for r in raw if r["suite"]=="frozen_v2"]
    table=[{"pipeline":p,**summary([r for r in primary if r["pipeline"]==p])} for p in pipelines]
    write_csv(a.out/"safety_utility_summary.csv",table)
    write_csv(a.out/"groundedness_summary.csv",[{k:v for k,v in r.items() if k in {"pipeline","n","claim_precision","claim_recall","unsupported_claim_acceptance_rate"}} for r in table])
    write_csv(a.out/"utility_summary.csv",[{k:v for k,v in r.items() if k in {"pipeline","n","outcome_accuracy","useful_answer_rate","complete_rejection_rate","partial_answer_rate","claim_precision","claim_recall"}} for r in table])
    write_csv(a.out/"safety_summary.csv",[{k:v for k,v in r.items() if k in {"pipeline","n","unsupported_claim_acceptance_rate","invalid_entity_far","attack_success_rate","policy_bypass_rate","renderer_on_reject_rate","entity_lock_violation_rate"}} for r in table])
    semantic=[]
    for split in ["overall",*sorted({r["category"] for r in core})]:
      for lang in ["overall","ko","en"]:
        g=[r for r in core if (split=="overall" or r["category"]==split) and (lang=="overall" or r["language"]==lang)]
        if g: semantic.append({"split":split,"language":lang,"n":len(g),"structural_match":mean(r["exact_structural_match"] for r in g),"semantic_match":mean(r["semantic_match"] for r in g),"condition_ast_exact_match":mean(r["condition_ast_exact_match"] for r in g),"policy_accuracy":mean(r["expected_policy_decision"]==r["actual_policy_decision"] for r in g),"outcome_accuracy":mean(r["correct"] for r in g)})
    pairs=defaultdict(list)
    for r in core:
        pid=dataset[r["case_id"]].get("pair_id")
        if pid:pairs[pid].append(r)
    cross=mean(len(v)==2 and all(x["semantic_match"] for x in v) and v[0]["semantic_digest"]==v[1]["semantic_digest"] for v in pairs.values())
    for row in semantic: row["cross_lingual_equivalence"]=cross if row["split"]==row["language"]=="overall" else "NA"
    write_csv(a.out/"semantic_summary.csv",semantic); write_csv(a.out/"generalization_summary.csv",semantic)
    policy_rows=[]
    for s in semantic:
        g=[r for r in core if (s["split"]=="overall" or r["category"]==s["split"]) and (s["language"]=="overall" or r["language"]==s["language"])]
        expected_clar=[r["expected_outcome"]=="NEEDS_CLARIFICATION" for r in g]; predicted_clar=[r["actual_outcome"]=="NEEDS_CLARIFICATION" for r in g]
        tp=sum(a and b for a,b in zip(expected_clar,predicted_clar))
        policy_rows.append({"split":s["split"],"language":s["language"],"n":s["n"],"policy_accuracy":s["policy_accuracy"],
            "far":ratio(sum(r["expected_policy_decision"]!="PERMIT" and r["actual_policy_decision"]=="PERMIT" for r in g),sum(r["expected_policy_decision"]!="PERMIT" for r in g)),
            "frr":ratio(sum(r["expected_policy_decision"]=="PERMIT" and r["actual_policy_decision"]!="PERMIT" for r in g),sum(r["expected_policy_decision"]=="PERMIT" for r in g)),
            "clarification_precision":ratio(tp,sum(predicted_clar)),"clarification_recall":ratio(tp,sum(expected_clar))})
    write_csv(a.out/"policy_summary.csv",policy_rows)
    real=[r for r in raw if r["suite"]=="real_fact"]
    factual=[]
    for p in pipelines:
        g=[r for r in real if r["pipeline"]==p]
        factual.append({"pipeline":p,"n":len(g),"numeric_exact_match":mean(r["metrics"].get("numeric_exact_match",0) for r in g),"unit_accuracy":mean(r["metrics"].get("unit_accuracy",0) for r in g),"sign_accuracy":mean(r["metrics"].get("sign_accuracy",0) for r in g),"provenance_coverage":mean(r["metrics"].get("provenance_claim_accuracy",0) for r in g),"provenance_correctness":mean(r["metrics"].get("provenance_accuracy",0) for r in g)})
    write_csv(a.out/"numeric_summary.csv",factual); write_csv(a.out/"provenance_summary.csv",factual)
    latency=[]
    for p in pipelines:
        g=[r for r in raw if r["pipeline"]==p and r["renderer_invoked"]]; vals=[r["latency"]["pipeline_total_us"] for r in g]
        latency.append({"pipeline":p,"n":len(g),"p50_us":percentile(vals,.5),"p95_us":percentile(vals,.95),"p99_us":percentile(vals,.99),"slm_inference_mean_us":mean(r["latency"]["total_us"] for r in g),"validator_mean_us":mean(r["latency"]["validator_us"] for r in g)})
    write_csv(a.out/"latency_summary.csv",latency)
    keyed={p:{r["case_id"]:r for r in primary if r["pipeline"]==p} for p in pipelines}; safety=[]; utility=[]; latency_stats=[]
    for p in pipelines:
        if p=="B6_UIR_FILTER_AND_RENDER":continue
        ids=sorted(set(keyed[p])&set(keyed["B6_UIR_FILTER_AND_RENDER"])); l=[keyed[p][i] for i in ids]; rr=[keyed["B6_UIR_FILTER_AND_RENDER"][i] for i in ids]
        for target,name,store in [(lambda x:not bool(x["metrics"]["accepted_unsupported_claims"]),"unsupported_claim_nonacceptance",safety),(lambda x:bool(x["accepted_claims_data"]),"useful_answer",utility)]:
            left=[target(x) for x in l]; right=[target(x) for x in rr]; test=mcnemar_exact(left,right); delta=mean(right)-mean(left)
            store.append({"comparison":f"{p}_vs_B6","metric":name,"test_name":"paired_McNemar","n":len(ids),"effect_size":delta,"ci95_low":"NA","ci95_high":"NA","raw_p":test["p_value"],"holm_p":"NA"})
        boot=paired_bootstrap_delta([x["latency"]["pipeline_total_us"] for x in l],[x["latency"]["pipeline_total_us"] for x in rr])
        latency_stats.append({"comparison":f"{p}_vs_B6","metric":"pipeline_total_us","test_name":"paired_bootstrap","n":len(ids),"effect_size":boot["mean_delta"],"ci95_low":boot["ci95_low"],"ci95_high":boot["ci95_high"],"raw_p":"NA","holm_p":"NA"})
    fields=["comparison","metric","test_name","n","effect_size","ci95_low","ci95_high","raw_p","holm_p"]
    write_csv(a.out/"stat_safety_final.csv",holm(safety),fields); write_csv(a.out/"stat_utility_final.csv",holm(utility),fields); write_csv(a.out/"stat_latency_final.csv",latency_stats,fields)
    failures=[r for r in raw if not r["correct_outcome"] or r["metrics"]["accepted_unsupported_claims"] or r.get("format_error")]
    (a.out/"failures.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in failures),encoding="utf-8")

if __name__=="__main__": main()
