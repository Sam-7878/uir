#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/"evaluation"/"uir_generalization"; RESULTS=ROOT/"results"/"uir_phase3"; REPORT=ROOT/"docs"/"work_reports"/"uir_phase3"/"LEAKAGE_REPORT.md"
def load(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def norm(s): return re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ",s.casefold())).strip()
def ngrams(s,n=5):
    t=norm(s).split(); return {tuple(t[i:i+n]) for i in range(max(0,len(t)-n+1))}
def main():
    dev=load(BASE/"dev"/"dev_generalization_v1.jsonl"); test=load(BASE/"candidate"/"frozen_test_v2_candidate.jsonl")
    dev_text={r["source_text"] for r in dev}; dev_norm={norm(x) for x in dev_text}; dev_templates={r["template_id"] for r in dev}; dev_entities={r["expected_target"] for r in dev}
    exact=sum(r["source_text"] in dev_text for r in test); normalized=sum(norm(r["source_text"]) in dev_norm for r in test)
    template=len(dev_templates & {r["template_id"] for r in test}); entity=len(dev_entities & {r["expected_target"] for r in test})
    dg=set().union(*(ngrams(x) for x in dev_text)); tg=set().union(*(ngrams(r["source_text"]) for r in test)); ng=len(dg&tg)/len(tg) if tg else 0
    result={"status":"PASS" if not (exact or normalized or template) else "FAIL","candidate_not_frozen":True,"template_overlap":template,"exact_text_overlap":exact,"normalized_text_overlap":normalized,"five_gram_overlap_rate":ng,"entity_overlap":entity,"lexicon_overlap_note":"category lexicon overlap expected; entity instances excluded from SemanticLexicon"}
    RESULTS.mkdir(parents=True,exist_ok=True); REPORT.parent.mkdir(parents=True,exist_ok=True)
    (RESULTS/"leakage_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    REPORT.write_text("# Phase 3 leakage report\n\n"+"\n".join(f"- {k}: `{v}`" for k,v in result.items())+"\n",encoding="utf-8")
if __name__=="__main__": main()
