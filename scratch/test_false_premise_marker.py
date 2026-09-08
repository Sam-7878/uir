import json
import re

pattern = re.compile(
    r"(?i)(전제하에|기정사실|사실에\s*따라|사실에\s*기반하여|부도\s*처리|채권단\s*청산|완전\s*파산|파산하여|자본잠식|매출\s*(?:이\s*)?0원|매출\s*제로|청산\s*절차|assuming.*(?:insolvency|bankruptcy|dissolution)|accepting\s+as\s+true.*(?:dissolution|zero\s+revenue|insolvency)|declared\s+insolvency)"
)

# Test on 850 cases in custom_heldout_v3_1.jsonl
with open("/mnt/d/_Work/goat_bank/uir/evaluation/llm_security_v3_1/datasets/custom_heldout_v3_1.jsonl", "r", encoding="utf-8") as f:
    run_cases = [json.loads(line) for line in f if line.strip()]

with open("/mnt/d/_Work/goat_bank/uir/evaluation/llm_security_v3_1/datasets/oracle_heldout_v3_1.jsonl", "r", encoding="utf-8") as f:
    ora_cases = [json.loads(line) for line in f if line.strip()]

benign_matches = []
attack_matches = []

for r, o in zip(run_cases, ora_cases):
    txt = r["user_input"]
    m = pattern.search(txt)
    if o["is_attack"]:
        if m:
            attack_matches.append((o["attack_class"], o["original_case_id"], txt, m.group()))
    else:
        if m:
            benign_matches.append((o["original_case_id"], txt, m.group()))

print(f"Benign matches (False Positives): {len(benign_matches)}")
for cid, txt, matched in benign_matches:
    print(f"  {cid}: matched '{matched}' in '{txt}'")

print(f"\nAttack matches: {len(attack_matches)}")
from collections import Counter
print("Attack classes matched:", Counter([a[0] for a in attack_matches]))
