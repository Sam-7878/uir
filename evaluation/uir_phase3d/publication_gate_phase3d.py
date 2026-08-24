#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/"results/uir_phase3d";P3B=ROOT/"results/uir_phase3b"
def load(p):return json.loads(p.read_text()) if p.exists() else {}
def main():
    audit=load(OUT/"actual_ai_audit_summary.json");validation=load(OUT/"role_separated_validation.json");stats_validation=load(OUT/"agreement_statistics_validation.json");campaign=load(OUT/"campaign_summary.json");budget=load(OUT/"generation_budget_validation.json");b6=load(OUT/"b6_filtering_summary.json");tests=load(OUT/"b6_integration_tests.json");frozen=load(P3B/"FROZEN_TEST_V2_MANIFEST.json")
    frozen_ok=(P3B/"frozen_test_v2.jsonl").exists() and hashlib.sha256((P3B/"frozen_test_v2.jsonl").read_bytes()).hexdigest()==frozen.get("dataset_sha256")
    checks={"actual_multi_model_audit_complete":audit.get("status")=="complete" and audit.get("full_1200x3") is True and audit.get("shared_three_model_cases")==1200,
            "model_review_provenance_recorded":audit.get("provenance_validated") is True and validation.get("role_separated_actual_model_audit_valid") is True,
            "agreement_statistics_valid":(OUT/"actual_ai_agreement.csv").exists() and audit.get("agreement_statistics_valid") is True and stats_validation.get("status")=="PASS",
            "frozen_v2_integrity_verified":frozen_ok,"SEC_truncation_fixed":campaign.get("sec_truncation_fixed") and budget.get("pass"),
            "real_fact_campaign_complete":campaign.get("real_fact_records")==1400,"B6_filtering_verified":campaign.get("b6_filtering_verified") and tests.get("status")=="passed",
            "B0_B6_final_campaign_complete":campaign.get("records")==9800 and len(campaign.get("pipelines",[]))==7,
            "final_statistics_complete":all((OUT/x).exists() for x in ("stat_safety_final.csv","stat_utility_final.csv","stat_latency_final.csv"))}
    data={"status":"READY_FOR_MANUSCRIPT_DRAFT" if all(checks.values()) else "BLOCKED_PUBLICATION_EVIDENCE_INCOMPLETE","publication_ready":all(checks.values()),"checks":checks,"blocking_checks":[k for k,v in checks.items() if not v],
          "phase3c_script_audit_reclassified":True,"forbidden_claim":"Phase3C rule-based files are not actual AI-model judgments"}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"PUBLICATION_GATE_PHASE3D.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8");print(json.dumps(data,sort_keys=True));return 0 if data["publication_ready"] else 2
if __name__=="__main__":raise SystemExit(main())
