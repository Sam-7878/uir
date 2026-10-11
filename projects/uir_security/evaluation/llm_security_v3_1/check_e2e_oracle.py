import json
from pathlib import Path

eval_file = Path("/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/custom/evaluated_pairs.jsonl")
eval_pairs = [json.loads(line) for line in eval_file.read_text(encoding="utf-8").splitlines() if line.strip()]

for p in eval_pairs:
    cid = p["oracle"]["original_case_id"]
    if cid in ["heldout-atk-0777", "heldout-atk-0738"]:
        print(f"=== {cid} ===")
        print("Attack class:", p["oracle"]["attack_class"])
        print("Forbidden patterns:", p["oracle"]["forbidden_output_patterns"])
        print("User input:", repr(p["runtime"]["user_input"]))
