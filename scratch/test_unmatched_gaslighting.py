import json
import re

pattern = re.compile(
    r"(?i)(전제하에|기정사실|사실에\s*따라|사실에\s*기반하여|부도\s*처리|채권단\s*청산|완전\s*파산|파산하여|자본잠식|매출\s*(?:이\s*)?0원|매출\s*제로|청산\s*절차|assuming.*(?:insolvency|bankruptcy|dissolution)|accepting\s+as\s+true.*(?:dissolution|zero\s+revenue|insolvency)|declared\s+insolvency)"
)

with open("/mnt/d/_Work/goat_bank/uir/evaluation/llm_security_v3_1/datasets/custom_heldout_v3_1.jsonl", "r", encoding="utf-8") as f:
    run_cases = [json.loads(line) for line in f if line.strip()]

with open("/mnt/d/_Work/goat_bank/uir/evaluation/llm_security_v3_1/datasets/oracle_heldout_v3_1.jsonl", "r", encoding="utf-8") as f:
    ora_cases = [json.loads(line) for line in f if line.strip()]

unmatched = []
for r, o in zip(run_cases, ora_cases):
    if o.get("attack_class") == "gaslighting_false_premise":
        txt = r["user_input"]
        if not pattern.search(txt):
            unmatched.append((o["original_case_id"], txt, o.get("forbidden_output_patterns", [])))

print(f"Total unmatched gaslighting: {len(unmatched)}")
for cid, txt, forb in unmatched[:15]:
    print(f"  {cid}: forbidden={forb} | input='{txt}'")
