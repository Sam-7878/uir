"""Vanilla SLM Baseline Adapter."""
from __future__ import annotations

import time
from typing import Any, Dict

from llm_trust.inference.base import BaseInferenceBackend
from evaluation.llm_security_v3_1.schema.runtime_case import RuntimeCase


class VanillaSlmBaselineAdapter:
    def __init__(self, backend: BaseInferenceBackend):
        self.backend = backend

    def run_case(self, case: RuntimeCase | Dict[str, Any]) -> Dict[str, Any]:
        start_ns = time.perf_counter_ns()
        c = case if isinstance(case, RuntimeCase) else RuntimeCase.from_dict(case)

        gen = self.backend.generate(
            prompt=c.user_input,
            system_prompt="You are a helpful assistant.",
            max_new_tokens=128,
            temperature=0.0,
        )

        elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000.0
        return {
            "case_id": c.case_id,
            "baseline": "Vanilla SLM",
            "language": c.language,
            "principal_id": c.principal_id,
            "model_output": gen.text,
            "final_output": gen.text,
            "terminal_status": "ALLOWED",
            "proposed_tool_calls": [],
            "executed_tool_calls": [],
            "accepted_evidence_ids": [],
            "tokens_used": gen.input_tokens + gen.output_tokens,
            "latency_ms": elapsed,
        }
