import json
import re

pattern = re.compile(
    r"(?i)("
    r"전제하에|기정사실|사실에\s*따라|사실에\s*기반하여|사실을\s*바탕으로|"
    r"부도\s*처리|채권단\s*청산|완전\s*파산|파산하여|파산했다는|법정\s*관리|영업\s*정지|"
    r"자본잠식|매출\s*(?:이\s*)?0원|매출\s*제로|청산\s*절차|"
    r"premised\s+on|predicated\s+on|under\s+the\s+established\s+premise|"
    r"assuming.*(?:insolvency|bankruptcy|dissolution|shut\s+down|zero\s+revenue)|"
    r"accepting\s+as\s+true.*(?:dissolution|zero\s+revenue|insolvency|bankruptcy)|"
    r"declared\s+insolvency|complete\s+insolvency|total\s+insolvency|catastrophic\s+bankruptcy|"
    r"went\s+bankrupt|liquidat(?:ed|ion)|revoked.*corporate\s+charter|forcibly\s+nationalized|"
    r"zero\s+earnings\s+and\s+default|ceased\s+operations\s+following"
    r")"
)

with open("/mnt/d/_Work/goat_bank/uir/evaluation/llm_security_v3_1/datasets/custom_heldout_v3_1.jsonl", "r", encoding="utf-8") as f:
    run_cases = [json.loads(line) for line in f if line.strip()]

with open("/mnt/d/_Work/goat_bank/uir/evaluation/llm_security_v3_1/datasets/oracle_heldout_v3_1.jsonl", "r", encoding="utf-8") as f:
    ora_cases = [json.loads(line) for line in f if line.strip()]

benign_matches = []
attack_matches = []
gaslighting_total = 0

for r, o in zip(run_cases, ora_cases):
    txt = r["user_input"]
    m = pattern.search(txt)
    is_atk = o["is_attack"]
    atk_cls = o.get("attack_class", "")
    if atk_cls == "gaslighting_false_premise":
        gaslighting_total += 1
    if is_atk:
        if m:
            attack_matches.append((atk_cls, o["original_case_id"], txt, m.group()))
    else:
        if m:
            benign_matches.append((o["original_case_id"], txt, m.group()))

print(f"Benign matches (False Positives): {len(benign_matches)}")
for cid, txt, matched in benign_matches:
    print(f"  {cid}: matched '{matched}' in '{txt}'")

from collections import Counter
c = Counter([a[0] for a in attack_matches])
print(f"Gaslighting caught: {c.get('gaslighting_false_premise', 0)} / {gaslighting_total}")
print("Other attacks caught:", {k: v for k, v in c.items() if k != 'gaslighting_false_premise'})
