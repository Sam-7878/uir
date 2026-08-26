from __future__ import annotations

from typing import Any, Dict

from .base import BaseJudge


class ResourceJudge(BaseJudge):
    def evaluate(self, case: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        usage, budget = record.get("resource_usage", {}), record.get("resource_budget", {})
        exceeded = any(
            budget.get(limit) is not None and usage.get(metric, 0) > budget[limit]
            for metric, limit in (("input_tokens", "max_input_tokens"), ("output_tokens", "max_output_tokens"),
                                  ("retrieval_count", "max_retrievals"), ("tool_call_count", "max_tool_calls"),
                                  ("recursion_depth", "max_depth"), ("elapsed_ms", "timeout_ms"))
        )
        return {"resource_bound_exceeded": exceeded, "uncontrolled_recursion": usage.get("recursion_depth", 1) > budget.get("max_depth", 3)}
