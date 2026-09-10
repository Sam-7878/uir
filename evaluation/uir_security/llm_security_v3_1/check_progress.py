import json
from pathlib import Path

eval_file = Path("/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/custom/evaluated_pairs.jsonl")
raw_file = Path("/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/phi35/raw_run_hete_uir_v3_1_security_phi35.jsonl")

if eval_file.exists():
    eval_pairs = [json.loads(line) for line in eval_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    ben_total = sum(1 for p in eval_pairs if not p["oracle"]["is_attack"])
    print(f"Total dataset: {len(eval_pairs)} cases ({ben_total} benign, {len(eval_pairs)-ben_total} attacks)")

if raw_file.exists():
    lines = [json.loads(line) for line in raw_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"HETE progress: {len(lines)}/120 written to disk")
    if lines:
        last = lines[-1]
        print(f"Last written: {last.get('case_id')} ({last.get('opaque_case_id')}) -> status={last.get('failure_status')}, util={last.get('utility_verdict')}")
        ben_seen = [l for l in lines if l.get('case_id', '').startswith('heldout-benign')]
        ben_ok = sum(1 for l in ben_seen if l.get('utility_verdict'))
        atk_seen = [l for l in lines if not l.get('case_id', '').startswith('heldout-benign')]
        mcr_count = sum(1 for l in atk_seen if l.get('mcr_verdict'))
        e2e_count = sum(1 for l in atk_seen if l.get('e2e_verdict'))
        print(f"Benign: {ben_ok}/{len(ben_seen)} ({ben_ok/max(1, len(ben_seen))*100:.1f}%) | Attacks: {len(atk_seen)} seen, MCR={mcr_count}, E2E={e2e_count}")
