#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/"results/uir_phase3d"
def main():
    data={"phase3c_artifact_label":"Phase3C-script-audit","preserved":True,"actual_model_audit":False,
          "admissible_claim":"agreement among three independently implemented validation scripts",
          "forbidden_claims":["agreement among three independent AI model reviewers","cross-model semantic annotation agreement","Opus/Sonnet/Gemini model-based review"],
          "reason":"ai_r1_review.py, ai_r2_review.py, and ai_r3_review.py generate judgments with deterministic local rules and do not invoke the named engines",
          "replacement_evidence_required":["actual_ai_review_R1.jsonl","actual_ai_review_R2.jsonl","actual_ai_review_R3.jsonl"]}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"SCRIPT_AUDIT_RECLASSIFICATION.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
