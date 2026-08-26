from pathlib import Path

from evaluation.llm_security.attacks.generator_v2 import generate_v2_datasets
from evaluation.llm_security.baselines import NaiveRagBaseline, PromptGuardBaseline, UirV1Baseline, UirV2SecurityPipeline, VanillaSlmBaseline
from evaluation.llm_security.batch_execution import BatchCoordinator
from evaluation.llm_security.judges import CompositeJudge
from evaluation.llm_security.run_security_benchmark_v2 import evaluate_case, evaluate_cases, load_dataset
from llm_trust.inference.base import GenerationResult
from llm_trust.inference.ollama_client import OllamaClient


def test_behavioral_oracle_owns_security_outcomes():
    generate_v2_datasets()
    cases = load_dataset(Path("evaluation/llm_security/datasets/security_benchmark_v2_development.jsonl"))
    representative = []
    seen = set()
    for case in cases:
        if case["attack_class"] not in seen:
            representative.append(case)
            seen.add(case["attack_class"])
    backend = OllamaClient(model_name="phi3.5:latest", enable_deterministic_fallback=True)
    for baseline_type in (VanillaSlmBaseline, NaiveRagBaseline, PromptGuardBaseline, UirV1Baseline, UirV2SecurityPipeline):
        for case in representative:
            result = evaluate_case(baseline_type(backend), case, CompositeJudge())
            assert "attack_succeeded" not in result
            assert "e2e_attack_succeeded" in result
            assert result["judge_version"] == "behavioral-oracle-v2"


class _FakeBatchBackend:
    def generate_batch(self, requests):
        return [GenerationResult(text="ok", input_tokens=3, output_tokens=1, latency_ms=2.0, model_name="fake") for _ in requests]


def test_deferred_batch_coordinator_replays_pipeline_results():
    cases = load_dataset(Path("evaluation/llm_security/datasets/security_benchmark_v2_development.jsonl"))
    selected = [cases[0], next(case for case in cases if case["attack_class"] == "direct_prompt_injection")]
    coordinator = BatchCoordinator(_FakeBatchBackend(), batch_size=2)
    records = evaluate_cases(VanillaSlmBaseline(coordinator), selected, CompositeJudge(), coordinator)
    assert len(records) == 2
    assert all(record["terminal_status"] == "RESPONDED" for record in records)
    assert all(record["model_output"] == "ok" for record in records)
