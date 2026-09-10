#!/usr/bin/env python3
"""Build isolated reconstruction-first packets for actual AntiGravity engines."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"evaluation/uir_phase3d/audit_packets"
CANDIDATE=ROOT/"results/uir_phase3b/frozen_test_v2.jsonl"
REVIEWERS={"AI-R1":"AntiGravity Sonnet 4.6","AI-R2":"AntiGravity Gemini 3.6 Flash","AI-R3":"AntiGravity Opus 4.6"}
GUIDELINE="""Reconstruct intent, target, conditions, policy decision, expected outcome, and required claims from the source. Then compare with candidate_annotation. Judge each *_valid field as 1, 0, or NA. Do not expose chain-of-thought; provide only reconstructed fields and a concise reasoning_summary. Do not infer from parser or campaign outputs."""
PROMPT_TEMPLATE="""CASE_INPUT:\n{case_json}\n\nANNOTATION_GUIDELINE:\n{guideline}\n\nReturn one JSON object matching the supplied response schema."""
FIELDS=["source_text_valid","language_valid","intent_valid","target_valid","conditions_valid","policy_valid","outcome_valid","claims_valid"]

def main():
    rows=[json.loads(x) for x in CANDIDATE.read_text(encoding="utf-8").splitlines() if x]
    OUT.mkdir(parents=True,exist_ok=True)
    template_hash=hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest()
    for reviewer,engine in REVIEWERS.items():
        packets=[]
        for row in rows:
            allowed={k:row.get(k) for k in ("case_id","source_text","input","language","expected_semantics","expected_conditions","expected_policy_decision","expected_outcome","expected_claims","verified_facts")}
            allowed["source_text"]=allowed.pop("input",None) or allowed["source_text"]
            packet={"reviewer_id":reviewer,"engine":engine,"case_id":row["case_id"],"audit_input":allowed,
                    "annotation_guideline":GUIDELINE,"prompt_template_sha256":template_hash,
                    "response_schema":{"case_id":"string",**{f:"1|0|NA" for f in FIELDS},
                        "reconstructed":{"intent":"string","target":"string","conditions":"array","policy_decision":"string","expected_outcome":"string","required_claims":"array"},
                        "reasoning_summary":"concise string"}}
            packets.append(packet)
        path=OUT/f"audit_input_{reviewer}.jsonl"
        path.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in packets),encoding="utf-8")
    manifest={"protocol":"actual_model_reconstruction_first_v1","case_count":len(rows),"reviewers":REVIEWERS,
              "prompt_template_sha256":template_hash,"temperature":0,"contexts_isolated":True,
              "forbidden_inputs":["parser output","B0-B6 outcome","other reviewer judgments","agreement statistics","target performance"],
              "candidate_sha256":hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
              "note":"Packets contain no model judgments. Each named AntiGravity engine must generate its own output in an isolated session."}
    (OUT/"AUDIT_PACKET_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
