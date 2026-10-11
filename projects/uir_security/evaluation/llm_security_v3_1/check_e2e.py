import json
from pathlib import Path

raw_file = Path("/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/phi35/raw_run_hete_uir_v3_1_security_phi35.jsonl")
if raw_file.exists():
    lines = [json.loads(line) for line in raw_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    e2e_cases = [l for l in lines if l.get('e2e_verdict')]
    print(f"Found {len(e2e_cases)} E2E attack cases:")
    for c in e2e_cases:
        print("Case ID:", c.get("case_id"), "Opaque ID:", c.get("opaque_case_id"))
        print("Status:", c.get("failure_status"))
        print("Guard events:", c.get("guard_events"))
        print("Output:", repr(c.get("final_accepted_output")[:150]))
