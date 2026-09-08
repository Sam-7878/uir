import json

run_file = "/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/phi35/raw_run_hete_uir_v3_1_security_phi35.jsonl"
with open(run_file, "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

for idx in [1, 7, 14, 20, 34, 56]:
    if idx < len(records):
        r = records[idx]
        print(f"[{idx}] {r['case_id']}:")
        print(f"  status: {r['policy_outcome']}")
        print(f"  mcr: {r['mcr_verdict']}, e2e: {r['e2e_verdict']}")
        print(f"  guard_events: {r['guard_events']}")
        print(f"  final: {r['final_accepted_output'][:120]}")
