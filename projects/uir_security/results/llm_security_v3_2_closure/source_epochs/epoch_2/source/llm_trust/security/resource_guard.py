"""Resource Guard: Deterministic Budget Enforcement."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ResourceBudget:
    max_input_tokens: int = 4096
    max_output_tokens: int = 1024
    max_retrievals: int = 5
    max_tool_calls: int = 0
    timeout_ms: int = 10000
    max_depth: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_retrievals": self.max_retrievals,
            "max_tool_calls": self.max_tool_calls,
            "timeout_ms": self.timeout_ms,
            "max_depth": self.max_depth,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResourceBudget:
        return cls(
            max_input_tokens=int(data.get("max_input_tokens", 4096)),
            max_output_tokens=int(data.get("max_output_tokens", 1024)),
            max_retrievals=int(data.get("max_retrievals", 5)),
            max_tool_calls=int(data.get("max_tool_calls", 0)),
            timeout_ms=int(data.get("timeout_ms", 10000)),
            max_depth=int(data.get("max_depth", 3)),
        )


@dataclass
class ResourceTracker:
    budget: ResourceBudget
    start_time_ns: int = 0
    consumed_input_tokens: int = 0
    consumed_output_tokens: int = 0
    consumed_retrievals: int = 0
    consumed_tool_calls: int = 0
    current_depth: int = 1

    def __post_init__(self):
        if self.start_time_ns == 0:
            self.start_time_ns = time.perf_counter_ns()

    def elapsed_ms(self) -> float:
        return (time.perf_counter_ns() - self.start_time_ns) / 1_000_000.0

    def check_and_consume_retrieval(self, count: int = 1) -> Tuple[bool, str]:
        if self.consumed_retrievals + count > self.budget.max_retrievals:
            return (
                False,
                f"RESOURCE_BUDGET_EXCEEDED: Retrieval limit {self.budget.max_retrievals} exceeded (requested: {self.consumed_retrievals + count}).",
            )
        self.consumed_retrievals += count
        return True, ""

    def check_and_consume_tool_call(self, count: int = 1) -> Tuple[bool, str]:
        if self.consumed_tool_calls + count > self.budget.max_tool_calls:
            return (
                False,
                f"RESOURCE_BUDGET_EXCEEDED: Tool call limit {self.budget.max_tool_calls} exceeded (requested: {self.consumed_tool_calls + count}).",
            )
        self.consumed_tool_calls += count
        return True, ""

    def check_and_consume_tokens(self, input_tokens: int, output_tokens: int = 0) -> Tuple[bool, str]:
        if self.consumed_input_tokens + input_tokens > self.budget.max_input_tokens:
            return (
                False,
                f"RESOURCE_BUDGET_EXCEEDED: Input token limit {self.budget.max_input_tokens} exceeded.",
            )
        if self.consumed_output_tokens + output_tokens > self.budget.max_output_tokens:
            return (
                False,
                f"RESOURCE_BUDGET_EXCEEDED: Output token limit {self.budget.max_output_tokens} exceeded.",
            )
        self.consumed_input_tokens += input_tokens
        self.consumed_output_tokens += output_tokens
        return True, ""

    def check_timeout(self) -> Tuple[bool, str]:
        if self.elapsed_ms() > self.budget.timeout_ms:
            return (
                False,
                f"RESOURCE_BUDGET_EXCEEDED: Execution timeout ({self.budget.timeout_ms}ms) exceeded.",
            )
        return True, ""

    def check_depth(self, depth: int) -> Tuple[bool, str]:
        if depth > self.budget.max_depth:
            return (
                False,
                f"RESOURCE_BUDGET_EXCEEDED: Agent recursion depth {self.budget.max_depth} exceeded.",
            )
        self.current_depth = depth
        return True, ""
