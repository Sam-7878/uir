import json

eval_file = "/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/custom/evaluated_pairs.jsonl"
with open(eval_file, "r", encoding="utf-8") as f:
    eval_pairs = [json.loads(line) for line in f if line.strip()]

run_file = "/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/phi35/raw_run_hete_uir_v3_1_security_phi35.jsonl"
with open(run_file, "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

print(f"Total evaluated pairs: {len(eval_pairs)}, Completed records: {len(records)}")

for idx, rec in enumerate(records):
    pair = eval_pairs[idx]
    ora = pair["oracle"]
    is_atk = ora["is_attack"]
    atk_cls = ora["attack_class"]
    cid = ora["original_case_id"]
    e2e = rec["e2e_verdict"]
    mcr = rec["mcr_verdict"]
    util = rec["utility_verdict"]
    if is_atk and e2e:
        print(f"FAILED DEFENSE (E2E=True): idx={idx}, cid={cid}, class={atk_cls}")
        print(f"  Final output: {rec['final_accepted_output']}")
    elif not is_atk and not util:
        print(f"FAILED BENIGN (Util=False): idx={idx}, cid={cid}")
        print(f"  Final output: {rec['final_accepted_output']}")

benigns = [records[i] for i in range(len(records)) if not eval_pairs[i]["oracle"]["is_attack"]]
benign_pass = sum(1 for b in benigns if b["utility_verdict"])
print(f"Benign progress: {benign_pass}/{len(benigns)} ({(benign_pass/len(benigns)*100.0) if benigns else 0:.1f}%)")

attacks = [records[i] for i in range(len(records)) if eval_pairs[i]["oracle"]["is_attack"]]
e2e_count = sum(1 for a in attacks if a["e2e_verdict"])
mcr_count = sum(1 for a in attacks if a["mcr_verdict"])
print(f"Attack progress: total={len(attacks)}, mcr={mcr_count}, e2e={e2e_count}")
