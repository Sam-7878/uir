import json
from llm_trust.inference.ollama_client import OllamaClient
from evaluation.llm_security_v3_1.baselines.uir_v3_1_security import UirV31SecurityPipeline
from evaluation.llm_security_v3_1.judges.security_evaluator import SecurityEvaluator
from evaluation.llm_security_v3_1.schema.runtime_case import RuntimeCase
from evaluation.llm_security_v3_1.schema.oracle_case import OracleCase

def main():
    with open('/mnt/d/_Work/goat_bank/uir/results/llm_security_v3_1/raw_runs/custom/evaluated_pairs.jsonl') as f:
        pairs = [json.loads(line) for line in f]

    backend = OllamaClient(model_name='phi3.5:latest', enable_deterministic_fallback=False)
    pipeline = UirV31SecurityPipeline(backend=backend)
    evaluator = SecurityEvaluator()

    benign_pairs = [(RuntimeCase(**p['runtime']), OracleCase(**p['oracle'])) for p in pairs if not p['oracle']['is_attack']][:5]
    print(f"Testing {len(benign_pairs)} benign pairs with updated pipeline...", flush=True)
    util_count = 0
    for idx, (rc, oc) in enumerate(benign_pairs):
        rec = pipeline.run_case(rc)
        res = evaluator.evaluate_case(rec, oc)
        if res['benign_success']:
            util_count += 1
        print(f"Case {idx+1}/{len(benign_pairs)}: util={res['benign_success']}, target={oc.target_entities}, matched={res.get('evidence_matched')}, status={rec.get('terminal_status')}", flush=True)

    rate = (util_count / len(benign_pairs)) * 100
    print(f"Final Benign Utility: {util_count} / {len(benign_pairs)} ({rate:.1f}%)")

if __name__ == '__main__':
    main()
