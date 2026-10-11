"""Vanilla SLM Baseline Adapter for HETE V3.2."""
from __future__ import annotations

import time
from typing import Any, Dict

from llm_trust.inference.base import BaseInferenceBackend
from llm_trust.security.resource_tracker import ResourceBudget, ResourceTracker
from ..harness.agency_harness import MockToolExecutor, ToolProposalParser
from ..schema.runtime_case import RuntimeCase


class VanillaSlmBaselineAdapter:
    """Bare SLM inference without zero-trust security boundaries."""

    def __init__(self, backend: BaseInferenceBackend):
        self.backend = backend
        self.mock_executor = MockToolExecutor()

    def run_case(self, case: RuntimeCase | Dict[str, Any]) -> Dict[str, Any]:
        self.mock_executor = MockToolExecutor()
        start_ns = time.perf_counter_ns()
        c = case if isinstance(case, RuntimeCase) else RuntimeCase.from_dict(case)

        tracker = ResourceTracker(ResourceBudget())
        tracker.track_input(c.user_input)

        gen = self.backend.generate(
            prompt=c.user_input,
            system_prompt="You are a helpful assistant.",
            max_new_tokens=384,
            temperature=0.0,
        )

        tracker.usage.input_tokens = gen.input_tokens
        tracker.usage.output_tokens = gen.output_tokens
        proposals = ToolProposalParser.parse(gen.text)
        tracker.track_tool_proposal(len(proposals))

        executed = []
        mutations = []
        # Bare SLM has no CapabilityGate; proposed tools execute unconstrained
        for p in proposals:
            res = self.mock_executor.execute(p["name"], p.get("args", {}), principal=c.principal_id)
            tracker.track_tool_execution(1)
            executed.append({"name": p["name"], "args": p.get("args", {}), "result": res})
            if res.get("mutation"):
                mutations.append(res["mutation"])

        elapsed = (time.perf_counter_ns() - start_ns) / 1_000_000.0
        return {
            "case_id": c.case_id,
            "baseline": "Vanilla SLM",
            "language": c.language,
            "principal_id": c.principal_id,
            "model_output": gen.text,
            "final_output": gen.text,
            "terminal_status": "ALLOWED",
            "proposed_tool_calls": proposals,
            "executed_tool_calls": executed,
            "mock_state_mutations": mutations,
            "accepted_evidence_ids": [],
            "tokens_used": gen.input_tokens + gen.output_tokens,
            "resource_usage": {
                "input_tokens": tracker.usage.input_tokens,
                "output_tokens": tracker.usage.output_tokens,
                "total_tokens": tracker.usage.total_tokens,
                "tool_proposals": tracker.usage.tool_proposals,
                "tool_executions": tracker.usage.tool_executions,
                "elapsed_ms": tracker.usage.elapsed_ms,
            },
            "latency_ms": elapsed,
        }
