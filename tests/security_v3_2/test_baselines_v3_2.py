"""Unit tests for V3.2 Baselines."""
import unittest
from llm_trust.inference.base import BaseInferenceBackend, GenerationResult
from evaluation.llm_security_v3_2.schema.runtime_case import RuntimeCase
from evaluation.llm_security_v3_2.baselines import (
    CaMeLBaselineAdapter,
    NaiveRagBaselineAdapter,
    ProgentBaselineAdapter,
    SpotlightingBaselineAdapter,
    UirV32SecurityPipeline,
    VanillaSlmBaselineAdapter,
)


class MockInferenceBackend(BaseInferenceBackend):
    def __init__(self, response_text: str = '{"summary": "Test", "verified_claims": []}'):
        self.model_name = "mock_test_model"
        self.response_text = response_text

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> GenerationResult:
        return GenerationResult(
            text=self.response_text,
            input_tokens=len(prompt.split()),
            output_tokens=len(self.response_text.split()),
            latency_ms=10.0,
            model_name=self.model_name,
        )


class TestBaselinesV32(unittest.TestCase):
    def setUp(self):
        self.backend = MockInferenceBackend()
        self.case = RuntimeCase(
            case_id="c_test_001",
            language="en",
            user_input="Review AAPL 2023 revenue.",
            retrieved_context=[{
                "source_id": "https://sec.gov/aapl",
                "content": "Official AAPL 2023 revenue: $383.29B.",
                "signer": "trusted_enterprise_signer",
            }],
            principal_id="test_analyst",
            environment_id="prod",
        )

    def test_vanilla_slm(self):
        adapter = VanillaSlmBaselineAdapter(self.backend)
        res = adapter.run_case(self.case)
        self.assertEqual(res["baseline"], "Vanilla SLM")
        self.assertIn("resource_usage", res)

    def test_naive_rag(self):
        adapter = NaiveRagBaselineAdapter(self.backend)
        res = adapter.run_case(self.case)
        self.assertEqual(res["baseline"], "Naive RAG")
        self.assertEqual(len(res["accepted_evidence_ids"]), 1)

    def test_progent(self):
        adapter = ProgentBaselineAdapter(self.backend)
        res = adapter.run_case(self.case)
        self.assertEqual(res["baseline"], "Progent")

    def test_spotlighting(self):
        adapter = SpotlightingBaselineAdapter(self.backend)
        res = adapter.run_case(self.case)
        self.assertEqual(res["baseline"], "Spotlighting")

    def test_camel(self):
        adapter = CaMeLBaselineAdapter(self.backend)
        res = adapter.run_case(self.case)
        self.assertEqual(res["baseline"], "CaMeL")

    def test_uir_v32_pipeline(self):
        pipeline = UirV32SecurityPipeline(backend=self.backend)
        res = pipeline.execute(self.case)
        self.assertEqual(res["pipeline"], "HETE_UIR_V3_2")
        self.assertIn("resource_usage", res)


if __name__ == "__main__":
    unittest.main()
