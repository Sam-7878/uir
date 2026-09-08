import json
from evaluation.llm_security_v3_1.schema.runtime_case import RuntimeCase
from evaluation.llm_security_v3_1.schema.oracle_case import OracleCase
from evaluation.llm_security_v3_1.baselines.uir_v3_1_security import UirV31SecurityPipeline
from evaluation.llm_security_v3_1.judges.security_evaluator import SecurityEvaluator
from llm_trust.inference.ollama_client import OllamaClient

backend = OllamaClient(
    model_name="phi3.5:latest",
    endpoint="http://localhost:11434",
    timeout_seconds=30.0,
    enable_deterministic_fallback=False,
)

pipeline = UirV31SecurityPipeline(backend=backend)
evaluator = SecurityEvaluator()

# Test heldout-atk-0777 and heldout-atk-0738
with open("/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/custom/evaluated_pairs.jsonl", "r", encoding="utf-8") as f:
    pairs = [json.loads(line) for line in f if line.strip()]

for idx in [1, 7]:
    pair = pairs[idx]
    rc = RuntimeCase.from_dict(pair["runtime"])
    oc = OracleCase.from_dict(pair["oracle"])
    rec = pipeline.run_case(rc)
    eval_res = evaluator.evaluate_case(rec, oc)
    print(f"Index {idx} ({oc.original_case_id}):")
    print(f"  terminal_status: {rec.get('terminal_status')}")
    print(f"  policy_outcome: {rec.get('policy_outcome')}")
    print(f"  guard_events: {rec.get('guard_events')}")
    print(f"  model_compromised: {eval_res.get('model_compromised')}")
    print(f"  e2e_attack_succeeded: {eval_res.get('e2e_attack_succeeded')}")
    assert eval_res.get('e2e_attack_succeeded') is False, f"Expected E2E attack to fail on {oc.original_case_id}"

# Also test a benign case dynamically
benign_idx = next(i for i, p in enumerate(pairs) if not p["oracle"]["is_attack"])
pair_benign = pairs[benign_idx]
rc_b = RuntimeCase.from_dict(pair_benign["runtime"])
oc_b = OracleCase.from_dict(pair_benign["oracle"])
rec_b = pipeline.run_case(rc_b)
eval_res_b = evaluator.evaluate_case(rec_b, oc_b)
print(f"\nBenign Index {benign_idx} ({oc_b.original_case_id}):")
print(f"  terminal_status: {rec_b.get('terminal_status')}")
print(f"  final_output: {rec_b.get('final_output')[:100]}...")
print(f"  benign_success: {eval_res_b.get('benign_success')}")
assert eval_res_b.get('benign_success') is True, f"Expected benign to succeed on index {benign_idx}"

print("\nALL CHECKS PASSED!")
