"""Vanilla SLM Baseline: Direct prompt execution without security layers."""
from __future__ import annotations

import time
from typing import Any, Dict

from llm_trust.inference.base import BaseInferenceBackend
from ..execution import attach_generation, new_execution_record
from .output_contract import MAX_NEW_TOKENS, add_output_contract


class VanillaSlmBaseline:
    """Baseline 1: no deterministic guardrails or policy gates."""

    def __init__(self, backend: BaseInferenceBackend):
        self.backend = backend

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter_ns()
        generated = self.backend.generate(
            prompt=add_output_contract(case["prompt"]), system_prompt="", max_new_tokens=MAX_NEW_TOKENS
        )
        record = new_execution_record(case, "Vanilla SLM")
        measured_ms = (time.perf_counter_ns() - started) / 1_000_000.0
        attach_generation(record, generated.text, generated.input_tokens, generated.output_tokens,
                          max(measured_ms, generated.latency_ms), generated.model_name)
        record["policy_outcome"] = "NO_EXTERNAL_POLICY"
        return record
