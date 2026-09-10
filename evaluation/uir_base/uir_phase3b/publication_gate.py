#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"results/uir_phase3b"
def main():
    frozen=json.loads((OUT/"FROZEN_TEST_V2_MANIFEST.json").read_text()) if (OUT/"FROZEN_TEST_V2_MANIFEST.json").exists() else {}
    real=json.loads((OUT/"real_fact_subset_manifest.json").read_text()) if (OUT/"real_fact_subset_manifest.json").exists() else {}
    run=json.loads((OUT/"run_manifest.json").read_text()) if (OUT/"run_manifest.json").exists() else {}
    checks={"human_review_completed":frozen.get("human_review_status")=="completed" and frozen.get("reviewer_count")==2,
            "adjudication_completed":bool(frozen.get("adjudicated")),"frozen_v2":bool(frozen.get("frozen")),
            "dataset_sha256_set":bool(frozen.get("dataset_sha256")),"parser_sha256_fixed":bool(frozen.get("parser_source_sha256")),
            "clean_commit":run.get("worktree_dirty") is False,"final_slm_campaign_complete":bool(frozen.get("final_slm_campaign_complete")),
            "real_world_fact_subset_complete":real.get("status")=="complete","all_primary_metrics_complete":bool(frozen.get("all_primary_metrics_complete")),
            "statistics_complete":bool(frozen.get("statistics_complete"))}
    result={"publication_ready":all(checks.values()),"checks":checks,"blocking_checks":[k for k,v in checks.items() if not v]}
    OUT.mkdir(parents=True,exist_ok=True); (OUT/"PUBLICATION_GATE.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True)); return 0 if result["publication_ready"] else 2
if __name__=="__main__": raise SystemExit(main())
