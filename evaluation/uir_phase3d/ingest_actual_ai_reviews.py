#!/usr/bin/env python3
"""Validate actual engine outputs and compute pairwise/three-way agreement."""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; PACKETS=ROOT/"evaluation/uir_phase3d/audit_packets"; OUT=ROOT/"results/uir_phase3d"
REVIEWERS={"AI-R1":"AntiGravity Gemini 3.5 Flash","AI-R2":"AntiGravity Gemini 3.6 Flash","AI-R3":"AntiGravity Gemini 3.1 Pro"}
MODEL_SELECTORS={"AI-R1":"gemini-3.5-flash","AI-R2":"gemini-3.6-flash-high","AI-R3":"gemini-3.1-pro"}
FIELDS=["source_text_valid","language_valid","intent_valid","target_valid","conditions_valid","policy_valid","outcome_valid","claims_valid"]
ALLOWED={"1","0","NA"}
def read(path):
    with path.open(encoding="utf-8") as handle:return [json.loads(line) for line in handle if line.strip()]
def write_csv(path,rows,fields):
    with path.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def pair_stats(left,right):
    n=len(left); raw=sum(a==b for a,b in zip(left,right))/n; labels=sorted(ALLOWED)
    expected=sum((left.count(x)/n)*(right.count(x)/n) for x in labels)
    variance=len(set(left+right))>1
    return raw,((raw-expected)/(1-expected) if variance and expected<1 else None),(None if variance else "zero_marginal_variance")
def fleiss(values):
    n=len(values); cats=sorted(ALLOWED); p={c:sum(row.count(c) for row in values)/(3*n) for c in cats}
    observed=sum((sum(row.count(c)**2 for c in cats)-3)/(3*2) for row in values)/n; expected=sum(x*x for x in p.values())
    return None if expected==1 else (observed-expected)/(1-expected)
def validate_file(path,reviewer,engine,prompt_hash,case_ids):
    rows=read(path); indexed={}
    for row in rows:
        if row.get("reviewer_id")!=reviewer or row.get("engine")!=engine:raise ValueError(f"reviewer/engine mismatch in {path}")
        if row.get("prompt_template_sha256")!=prompt_hash:raise ValueError(f"prompt hash mismatch: {row.get('case_id')}")
        provenance=row.get("provenance",{})
        required=("session_run_id","timestamp","generation_interface","raw_response_sha256","temperature")
        if any(provenance.get(k) in (None,"") for k in required):raise ValueError(f"missing actual-model provenance: {row.get('case_id')}")
        if provenance.get("annotation_method")!="actual_model_generation":raise ValueError("rule-based/script annotation is not admissible")
        if provenance.get("temperature")!="not_exposed_by_antigravity_cli":raise ValueError(f"unverifiable temperature metadata: {row.get('case_id')}")
        if provenance.get("model_selector")!=MODEL_SELECTORS[reviewer]:raise ValueError(f"model selector mismatch: {row.get('case_id')}")
        cid=row.get("case_id"); judgment=row.get("judgment",{})
        if cid not in case_ids or cid in indexed or any(str(judgment.get(f,"" )).upper() not in ALLOWED for f in FIELDS):raise ValueError(f"invalid judgment: {cid}")
        if judgment.get("case_id")!=cid:raise ValueError(f"nested judgment case-ID mismatch: {cid}")
        if not isinstance(judgment.get("reconstructed"),dict) or not judgment.get("reasoning_summary","").strip():raise ValueError(f"reconstruction/rationale missing: {cid}")
        indexed[cid]=row
    if len(rows)!=1200:raise ValueError(f"{reviewer} must contain exactly 1200 rows, got {len(rows)}")
    if set(indexed)!=case_ids:raise ValueError(f"{reviewer} case coverage mismatch: {len(indexed)}/{len(case_ids)}")
    return indexed
def main():
    ap=argparse.ArgumentParser()
    for reviewer in REVIEWERS:ap.add_argument(f"--{reviewer.lower().replace('-','')}",type=Path,required=True)
    a=ap.parse_args(); manifest=json.loads((PACKETS/"AUDIT_PACKET_MANIFEST.json").read_text()); case_ids={x["case_id"] for x in read(PACKETS/"audit_input_AI-R1.jsonl")}
    files={"AI-R1":a.air1,"AI-R2":a.air2,"AI-R3":a.air3}; data={r:validate_file(files[r],r,REVIEWERS[r],manifest["prompt_template_sha256"],case_ids) for r in REVIEWERS}
    shared=set.intersection(*(set(x) for x in data.values())); covered=set.union(*(set(x) for x in data.values()))
    if len(case_ids)!=1200 or shared!=case_ids or covered!=case_ids:raise ValueError(f"coverage insufficient: shared={len(shared)}, any={len(covered)}/{len(case_ids)}")
    agreement=[]; disagreements=[]; pattern_counts=Counter()
    for field in FIELDS:
        ordered=sorted(shared); values={r:[str(data[r][c]["judgment"][field]).upper() for c in ordered] for r in REVIEWERS}
        pair_results={}
        for left,right in (("AI-R1","AI-R2"),("AI-R1","AI-R3"),("AI-R2","AI-R3")):
            raw,kappa,reason=pair_stats(values[left],values[right]);pair_results[f"{left}_{right}_raw"]=raw;pair_results[f"{left}_{right}_kappa"]=kappa if kappa is not None else "NA";pair_results[f"{left}_{right}_reason"]=reason or "computed"
        rows3=[[values[r][i] for r in REVIEWERS] for i in range(len(ordered))]; three=sum(len(set(x))==1 for x in rows3)/len(rows3); fk=fleiss(rows3)
        agreement.append({"field":field,"n":len(ordered),"three_way_raw_agreement":three,"fleiss_kappa":fk if fk is not None else "NA","fleiss_reason":"computed" if fk is not None else "zero_marginal_variance",**pair_results})
        for i,cid in enumerate(ordered):
            vals=rows3[i]
            if len(set(vals))>1:
                counts=Counter(vals); majority,status=(counts.most_common(1)[0][0],"majority_resolved") if counts.most_common(1)[0][1]>=2 else ("NA","unresolved")
                if vals[0]==vals[1]:pattern="R1 == R2 != R3"
                elif vals[0]==vals[2]:pattern="R1 == R3 != R2"
                elif vals[1]==vals[2]:pattern="R2 == R3 != R1"
                else:pattern="all three disagree"
                pattern_counts[pattern]+=1
                disagreements.append({"case_id":cid,"field":field,"pattern":pattern,"r1_judgment":vals[0],"r2_judgment":vals[1],"r3_judgment":vals[2],"majority":majority,
                    "r1_rationale":data["AI-R1"][cid]["judgment"]["reasoning_summary"],"r2_rationale":data["AI-R2"][cid]["judgment"]["reasoning_summary"],"r3_rationale":data["AI-R3"][cid]["judgment"]["reasoning_summary"],"status":status})
    OUT.mkdir(parents=True,exist_ok=True)
    fields=list(agreement[0]);write_csv(OUT/"actual_ai_agreement.csv",agreement,fields)
    dfields=["case_id","field","pattern","r1_judgment","r2_judgment","r3_judgment","majority","r1_rationale","r2_rationale","r3_rationale","status"]
    write_csv(OUT/"actual_ai_adjudication.csv",disagreements,dfields)
    for reviewer,path in files.items():(OUT/f"actual_ai_review_{reviewer[-2:]}.jsonl").write_bytes(path.read_bytes())
    summary={"status":"complete","protocol":"triple_independent_actual_model_audit","shared_three_model_cases":len(shared),"any_model_cases":len(covered),
             "full_1200x3":all(len(x)==1200 for x in data.values()),"provenance_validated":True,"agreement_statistics_valid":len(agreement)==len(FIELDS),
             "reviewers":{r:{"engine":REVIEWERS[r],"model_selector":MODEL_SELECTORS[r],"rows":len(data[r])} for r in REVIEWERS},
             "disagreement_records":len(disagreements),"disagreement_patterns":dict(sorted(pattern_counts.items())),"unresolved":sum(x["status"]=="unresolved" for x in disagreements),
             "review_file_sha256":{r:hashlib.sha256(files[r].read_bytes()).hexdigest() for r in REVIEWERS},"script_generated_judgments_admitted":False}
    (OUT/"actual_ai_audit_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
