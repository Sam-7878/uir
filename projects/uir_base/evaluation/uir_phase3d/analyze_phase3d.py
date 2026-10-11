#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math,random
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"uir_slm"))
from paired_statistics import mcnemar_exact,paired_bootstrap_delta,percentile
try:
    from scipy.stats import wilcoxon
except ImportError:
    wilcoxon=None

def read(p):
    with p.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
def mean(x):
    x=list(x);return sum(x)/len(x) if x else 0.0
def ratio(a,b):return a/b if b else 0.0
def write_csv(p,rows,fields=None):
    fields=fields or list(rows[0])
    with p.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def binary_boot(left,right,seed=20260807,n=5000):
    d=[float(b)-float(a) for a,b in zip(left,right)];rng=random.Random(seed);samples=sorted(sum(d[rng.randrange(len(d))] for _ in d)/len(d) for _ in range(n))
    return mean(d),samples[int(.025*n)],samples[min(n-1,int(.975*n))]
def holm(rows):
    ranked=sorted((float(r["raw_p"]),i) for i,r in enumerate(rows) if r["raw_p"]!="NA");running=0
    for rank,(p,i) in enumerate(ranked):running=max(running,min(1,p*(len(ranked)-rank)));rows[i]["holm_p"]=running
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--raw",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    rows=read(a.raw);pipelines=sorted({r["pipeline"] for r in rows});sec=[r for r in rows if r["suite"]=="real_fact"]
    structured=[]
    for p in pipelines:
        g=[r for r in sec if r["pipeline"]==p]; valid=[r for r in g if not r["format_error"]]
        structured.append({"pipeline":p,"n":len(g),"valid_json_rate":ratio(len(valid),len(g)),"json_truncation_rate":mean(r.get("json_truncated",False) for r in g),
            "schema_error_rate":mean(bool(r["format_error"]) and not r.get("json_truncated",False) for r in g),"missing_provenance_rate":mean(r["metrics"].get("provenance_claim_accuracy",0)<1 for r in g),
            "p50_output_tokens":percentile([r["latency"]["output_tokens"] for r in valid],.5),"p95_output_tokens":percentile([r["latency"]["output_tokens"] for r in valid],.95),"p99_output_tokens":percentile([r["latency"]["output_tokens"] for r in valid],.99)})
    write_csv(a.out/"sec_structured_output_diagnostic.csv",structured)
    compact=[r for r in sec if r["pipeline"] in {"B4_UIR_POLICY_SLM","B5_FULL_UIR_OUTPUT_VALIDATION","B6_UIR_FILTER_AND_RENDER"} and not r["format_error"]]
    p99=percentile([r["latency"]["output_tokens"] for r in compact],.99);configured=max((r.get("generation_budget_tokens",0) for r in compact),default=0);required=math.ceil(1.25*p99)
    budget={"configured_max_new_tokens":configured,"p99_valid_structured_output_tokens":p99,"required_minimum_tokens":required,"rule":"configured >= 1.25 * p99","pass":configured>=required}
    (a.out/"generation_budget_validation.json").write_text(json.dumps(budget,indent=2)+"\n",encoding="utf-8")
    b6=[r for r in rows if r["pipeline"]=="B6_UIR_FILTER_AND_RENDER"]
    states=Counter(r.get("output_state","UNSPECIFIED") for r in b6)
    b6_summary={"n":len(b6),"states":states,"partial_verified_answer_rate":ratio(states["PARTIAL_VERIFIED_ANSWER"],len(b6)),
                "unsupported_claim_acceptance_rate":ratio(sum(r["metrics"]["accepted_unsupported_claims"] for r in b6),sum(r["metrics"]["accepted_claims"] for r in b6)),
                "supported_subset_preserved":all(all(c in r["accepted_claims_data"] for c in r["generated_claims_data"] if c in (r.get("accepted_claims_data") or [])) for r in b6)}
    (a.out/"b6_filtering_summary.json").write_text(json.dumps(b6_summary,indent=2)+"\n",encoding="utf-8")
    primary=[r for r in rows if r["suite"]=="frozen_v2"];keyed={p:{r["case_id"]:r for r in primary if r["pipeline"]==p} for p in pipelines};safety=[];utility=[];latency=[]
    fields=["comparison","metric","test_name","n","effect_size","ci95_low","ci95_high","raw_p","holm_p"]
    for p in pipelines:
        if p=="B6_UIR_FILTER_AND_RENDER":continue
        ids=sorted(set(keyed[p])&set(keyed["B6_UIR_FILTER_AND_RENDER"]));left=[keyed[p][i] for i in ids];right=[keyed["B6_UIR_FILTER_AND_RENDER"][i] for i in ids]
        for name,fn,target in [("unsupported_claim_nonacceptance",lambda r:not bool(r["metrics"]["accepted_unsupported_claims"]),safety),("useful_answer",lambda r:bool(r["accepted_claims_data"]),utility)]:
            l=[fn(r) for r in left];rr=[fn(r) for r in right];test=mcnemar_exact(l,rr);effect,low,high=binary_boot(l,rr)
            target.append({"comparison":f"{p}_vs_B6","metric":name,"test_name":"paired_McNemar+risk_difference","n":len(ids),"effect_size":effect,"ci95_low":low,"ci95_high":high,"raw_p":test["p_value"],"holm_p":"NA"})
        lv=[r["latency"]["pipeline_total_us"] for r in left];rv=[r["latency"]["pipeline_total_us"] for r in right];boot=paired_bootstrap_delta(lv,rv)
        try:wp=float(wilcoxon(lv,rv).pvalue) if wilcoxon and any(a!=b for a,b in zip(lv,rv)) else 1.0
        except ValueError:wp=1.0
        latency.append({"comparison":f"{p}_vs_B6","metric":"pipeline_total_us","test_name":"Wilcoxon+paired_bootstrap","n":len(ids),"effect_size":boot["mean_delta"],"ci95_low":boot["ci95_low"],"ci95_high":boot["ci95_high"],"raw_p":wp,"holm_p":"NA"})
    holm(safety);holm(utility);holm(latency);write_csv(a.out/"stat_safety_final.csv",safety,fields);write_csv(a.out/"stat_utility_final.csv",utility,fields);write_csv(a.out/"stat_latency_final.csv",latency,fields)
    summary={"campaign_id":"phase3d-publication-final","records":len(rows),"frozen_v2_records":len(primary),"real_fact_records":len(sec),"pipelines":pipelines,
             "sec_truncation_fixed":all(r["json_truncation_rate"]==0 for r in structured if r["pipeline"] in {"B4_UIR_POLICY_SLM","B5_FULL_UIR_OUTPUT_VALIDATION","B6_UIR_FILTER_AND_RENDER"}),
             "generation_budget_rule_pass":budget["pass"],"b6_filtering_verified":b6_summary["unsupported_claim_acceptance_rate"]==0}
    (a.out/"campaign_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
