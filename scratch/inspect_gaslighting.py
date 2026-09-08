import json

with open("/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/custom/evaluated_pairs.jsonl") as f:
    eval_pairs = [json.loads(line) for line in f if line.strip()]

gaslighting_cases = []
classes = {}
for idx, p in enumerate(eval_pairs):
    ora = p["oracle"]
    cls = ora.get("attack_class")
    classes[cls] = classes.get(cls, 0) + 1
    if cls == "gaslighting_false_premise":
        gaslighting_cases.append((idx, ora["original_case_id"], p["runtime"]["user_input"]))

print("Class counts in evaluated_pairs:")
for c, cnt in classes.items():
    print(f"  {c}: {cnt}")

print(f"\nTotal gaslighting cases in 120 pairs: {len(gaslighting_cases)}")
for idx, cid, inp in gaslighting_cases:
    print(f"[{idx}] {cid}: {inp}")
