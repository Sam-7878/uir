#!/usr/bin/env python3
"""Clean, hash-bound Phase3D Phi-3.5 B0--B6 campaign runner."""
from __future__ import annotations
import argparse,fcntl,hashlib,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/"results/uir_phase3d";P3B=ROOT/"results/uir_phase3b";CONFIG=ROOT/"evaluation/uir_slm/model_config/phi35_ollama.json"
WORKERS=8
def run(args,capture=False):return subprocess.run(args,cwd=ROOT,check=True,text=True,capture_output=capture)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate_campaign(path,expected_rows):
    rows=[]
    for line_number,line in enumerate(path.open(encoding="utf-8"),1):
        try:rows.append(json.loads(line))
        except json.JSONDecodeError as exc:raise SystemExit(f"invalid JSON in {path}:{line_number}: {exc}") from exc
    pairs={(row["case_id"],row["pipeline"]) for row in rows}
    if len(rows)!=expected_rows or len(pairs)!=expected_rows:
        raise SystemExit(f"campaign integrity failure for {path}: rows={len(rows)}, unique_pairs={len(pairs)}, expected={expected_rows}")
def atomic_concat(paths,target):
    temporary=target.with_name(target.name+".partial")
    with temporary.open("wb") as handle:
        for path in paths:handle.write(path.read_bytes())
        handle.flush();os.fsync(handle.fileno())
    temporary.replace(target)
def version(args):
    try:return run(args,True).stdout.strip()
    except Exception:return "unavailable"
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--finalize-only",action="store_true");ap.add_argument("--execution-commit");ap.add_argument("--started-clean",action="store_true");a=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    lock_path=OUT/".phase3d_campaign.lock"
    lock_handle=lock_path.open("w",encoding="utf-8")
    try:
        fcntl.flock(lock_handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(f"another Phase3D campaign holds {lock_path}")
    lock_handle.write(f"pid={os.getpid()}\n")
    lock_handle.flush()
    frozen=P3B/"frozen_test_v2.jsonl";real=P3B/"real_fact_subset.jsonl";manifest=json.loads((P3B/"FROZEN_TEST_V2_MANIFEST.json").read_text());parser_freeze=json.loads((ROOT/"evaluation/uir_phase3b/PARSER_FREEZE.json").read_text())
    if sha(frozen)!=manifest["dataset_sha256"] or manifest["parser_source_sha256"]!=parser_freeze["parser_source_sha256"]:raise SystemExit("frozen-v2/parser integrity failure")
    if not a.finalize_only and run(["git","status","--porcelain"],True).stdout.strip():raise SystemExit("Phase3D final campaign requires a clean worktree")
    config=json.loads(CONFIG.read_text());model=config["model"]
    if model not in version(["ollama","list"]):raise SystemExit(f"Ollama model unavailable: {model}")
    core=OUT/"uir_core_final.jsonl";raw_v2=OUT/"campaign_frozen_v2.jsonl";raw_sec=OUT/"campaign_real_fact.jsonl"
    execution_commit=a.execution_commit or run(["git","rev-parse","HEAD"],True).stdout.strip()
    if not a.finalize_only:
        run(["cargo","run","--release","-p","poa-uir","--bin","uir-eval","--",str(frozen),str(core)])
        runner=str(ROOT/"evaluation/uir_phase3d/run_slm_campaign_parallel.py");common=[sys.executable,runner,"--uir-records",str(core),"--config",str(CONFIG),"--run-id","phase3d-publication-final","--workers",str(WORKERS)]
        run([*common,"--dataset",str(frozen),"--suite","frozen_v2","--out",str(raw_v2)])
        run([*common,"--dataset",str(real),"--suite","real_fact","--out",str(raw_sec)])
    validate_campaign(raw_v2,8400);validate_campaign(raw_sec,1400)
    combined=OUT/"campaign_raw.jsonl";atomic_concat([raw_v2,raw_sec],combined);validate_campaign(combined,9800)
    run([sys.executable,str(ROOT/"evaluation/uir_phase3b/aggregate_final.py"),"--raw",str(combined),"--core",str(core),"--dataset",str(frozen),"--out",str(OUT)])
    run([sys.executable,str(ROOT/"evaluation/uir_phase3d/analyze_phase3d.py"),"--raw",str(combined),"--out",str(OUT)])
    run([sys.executable,str(ROOT/"evaluation/uir_phase3d/validate_b6_invariants.py")])
    model_description=version(["ollama","show",model,"--modelfile"])
    postprocessing_commit=run(["git","rev-parse","HEAD"],True).stdout.strip()
    run_manifest={"campaign_id":"phase3d-publication-final","status":"complete","started_from_clean_commit":a.started_clean or not a.finalize_only,"worktree_dirty_at_start":False,"commit":execution_commit,"postprocessing_commit":postprocessing_commit,"workers":WORKERS,
        "dataset_sha256":sha(frozen),"parser_source_sha256":manifest["parser_source_sha256"],"real_fact_subset_sha256":sha(real),"model":model,
        "model_config_sha256":sha(CONFIG),"model_description_sha256":hashlib.sha256(model_description.encode()).hexdigest(),"generation_config":config["deterministic"],
        "os":platform.platform(),"cpu":platform.processor(),"ram_bytes":os.sysconf("SC_PAGE_SIZE")*os.sysconf("SC_PHYS_PAGES"),"gpu":version(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader"]),
        "rust":version(["rustc","--version"]),"python":sys.version,"ollama":version(["ollama","--version"]),"completed_at":datetime.now(timezone.utc).isoformat()}
    (OUT/"run_manifest_phase3d.json").write_text(json.dumps(run_manifest,indent=2)+"\n",encoding="utf-8")
    subprocess.run([sys.executable,str(ROOT/"evaluation/uir_phase3d/publication_gate_phase3d.py")],cwd=ROOT)
    run([sys.executable,str(ROOT/"evaluation/uir_phase3d/generate_phase3d_report.py")])
if __name__=="__main__":main()
