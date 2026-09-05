from evaluation.uir_phase4d.common import read_jsonl, FROZEN_DIR
import os
print("FROZEN_DIR is:", FROZEN_DIR)
print("Exists?", FROZEN_DIR.exists())
if FROZEN_DIR.exists():
    print("Files:", os.listdir(FROZEN_DIR))


cases = read_jsonl(FROZEN_DIR / "strong_runtime_600.jsonl")
print(f"Loaded {len(cases)} frozen runtime cases.")
for p in ["C0_DIRECT_SLM", "C1_NAIVE_RAG", "C2_RAG_EXISTENCE_CHECK", "C3_JSON_SCHEMA_STRUCTURED", "C5_GUARDRAIL_STYLE", "C6_CORRECTIVE_RETRIEVAL", "C7_GRAPH_STRUCTURED_RAG", "C8_FINAL_UIR_B6"]:
    reqs = [build_internal_request(p, c) for c in cases]
    invoked = sum(r["invoke"] for r in reqs)
    print(f"{p}: {invoked}/{len(cases)} invoked")
