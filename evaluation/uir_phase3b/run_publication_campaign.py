#!/usr/bin/env python3
"""Fail-closed clean runner for the final frozen-v2 + SEC B0--B6 campaign."""
from __future__ import annotations
import hashlib, json, os, platform, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"results/uir_phase3b"
FROZEN=OUT/"frozen_test_v2.jsonl"; MANIFEST=OUT/"FROZEN_TEST_V2_MANIFEST.json"; REAL=OUT/"real_fact_subset.jsonl"
CONFIG=ROOT/"evaluation/uir_slm/model_config/phi35_ollama.json"

def command(args, capture=False):
    return subprocess.run(args,cwd=ROOT,check=True,text=True,capture_output=capture)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def version(args):
    try:return command(args,True).stdout.strip()
    except Exception:return "unavailable"
def main():
    if not MANIFEST.exists(): print("BLOCKED: frozen-v2 manifest does not exist",file=sys.stderr); return 2
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not (manifest.get("frozen") and manifest.get("human_review_status")=="completed" and manifest.get("adjudicated") and manifest.get("reviewer_count")==2):
        print("BLOCKED: human review/adjudication/frozen-v2 gates are incomplete",file=sys.stderr); return 3
    if sha(FROZEN)!=manifest.get("dataset_sha256"): print("BLOCKED: frozen-v2 hash mismatch",file=sys.stderr); return 4
    real_manifest=json.loads((OUT/"real_fact_subset_manifest.json").read_text(encoding="utf-8"))
    if real_manifest.get("status")!="complete" or sha(REAL)!=real_manifest.get("dataset_sha256"):
        print("BLOCKED: real-world fact subset incomplete or hash mismatch",file=sys.stderr); return 5
    dirty=command(["git","status","--porcelain"],True).stdout.strip()
    if dirty: print("BLOCKED: final campaign requires a clean worktree",file=sys.stderr); return 6
    commit=command(["git","rev-parse","HEAD"],True).stdout.strip()
    if commit!=manifest["code_commit"]: print("BLOCKED: freeze commit differs from campaign commit",file=sys.stderr); return 7
    model_config=json.loads(CONFIG.read_text()); model=model_config["model"]
    if model not in version(["ollama","list"]): print(f"BLOCKED: Ollama model not installed: {model}",file=sys.stderr); return 8
    core=OUT/"uir_core_final.jsonl"; raw_v2=OUT/"campaign_frozen_v2.jsonl"; raw_real=OUT/"campaign_real_fact.jsonl"
    command(["cargo","run","--release","-p","poa-uir","--bin","uir-eval","--",str(FROZEN),str(core)])
    runner=str(ROOT/"evaluation/uir_slm/run_slm_campaign.py")
    common=[sys.executable,runner,"--uir-records",str(core),"--config",str(CONFIG),"--run-id","phase3b-final"]
    command([*common,"--dataset",str(FROZEN),"--suite","frozen_v2","--out",str(raw_v2)])
    command([*common,"--dataset",str(REAL),"--suite","real_fact","--out",str(raw_real)])
    combined=OUT/"campaign_raw.jsonl"; combined.write_bytes(raw_v2.read_bytes()+raw_real.read_bytes())
    command([sys.executable,str(ROOT/"evaluation/uir_phase3b/aggregate_final.py"),"--raw",str(combined),"--core",str(core),"--dataset",str(FROZEN),"--out",str(OUT)])
    model_description=version(["ollama","show",model,"--modelfile"])
    run={"status":"complete","publication_ready":True,"worktree_dirty":False,"commit":commit,
         "parser_hash":manifest["parser_source_sha256"],"dataset_hash":manifest["dataset_sha256"],
         "real_fact_subset_hash":real_manifest["dataset_sha256"],"sec_snapshot_hash":real_manifest["registry_sha256"],
         "model":model,"model_config_sha256":sha(CONFIG),"model_description_sha256":hashlib.sha256(model_description.encode()).hexdigest(),
         "os":platform.platform(),"cpu":platform.processor(),"ram_bytes":os.sysconf("SC_PAGE_SIZE")*os.sysconf("SC_PHYS_PAGES"),
         "gpu":version(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader"]),
         "rust":version(["rustc","--version"]),"python":sys.version,"ollama":version(["ollama","--version"]),
         "started_from_clean_commit":True,"completed_at":datetime.now(timezone.utc).isoformat(),"pipelines":[f"B{i}" for i in range(7)]}
    (OUT/"run_manifest.json").write_text(json.dumps(run,indent=2)+"\n",encoding="utf-8")
    manifest["publication_ready"]=True; manifest["final_slm_campaign_complete"]=True; manifest["real_world_fact_subset_complete"]=True
    manifest["all_primary_metrics_complete"]=True; manifest["statistics_complete"]=True
    MANIFEST.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    command([sys.executable,str(ROOT/"evaluation/uir_phase3b/publication_gate.py")])
    command([sys.executable,str(ROOT/"evaluation/uir_phase3b/generate_publication_report.py")])
    return 0
if __name__=="__main__": raise SystemExit(main())
