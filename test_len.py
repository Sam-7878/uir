import json
from pathlib import Path
from evaluation.uir_phase4d.adapters.finqa_adapter import finqa_prompt_phase4d
from evaluation.uir_phase4d.adapters.halueval_adapter import halueval_prompt_phase4d

finqa_path = Path("uir/results/uir_phase4d/frozen_inputs/finqa_runtime_200.jsonl")
halu_path = Path("uir/results/uir_phase4d/frozen_inputs/halueval_qa_runtime_200.jsonl")

if finqa_path.exists():
    r = json.loads(finqa_path.read_text(encoding="utf-8").splitlines()[0])
    sys_p, p, cat = finqa_prompt_phase4d(r, "C1_NAIVE_RAG")
    print(f"FinQA C1 prompt chars: {len(p)}, words: {len(p.split())}")
    sys_p8, p8, cat8 = finqa_prompt_phase4d(r, "C8_FINAL_UIR_B6")
    print(f"FinQA C8 prompt chars: {len(p8)}, words: {len(p8.split())}, catalog size: {len(cat8)}")

if halu_path.exists():
    r = json.loads(halu_path.read_text(encoding="utf-8").splitlines()[0])
    sys_p, p, _ = halueval_prompt_phase4d(r, "H0_NATIVE")
    print(f"HaluEval C1 prompt chars: {len(p)}, words: {len(p.split())}")
    sys_p8, p8, _ = halueval_prompt_phase4d(r, "H2_UIR_CONTRACT")
    print(f"HaluEval C8 prompt chars: {len(p8)}, words: {len(p8.split())}")
