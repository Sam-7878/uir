"""Resource Tracker and Dynamic Budget Guard for HETE V3.2.

Work Order Mandate §7:
1. Dynamic runtime tracking of:
   - input tokens
   - output tokens
   - retrieval operations
   - tool proposals
   - tool executions
   - recursion / agent steps
   - wall-clock time
2. Budget exceed produces BLOCKED_RESOURCE_EXHAUSTED from actual accumulated usage.
3. Realistic resource attack stimuli: long-context flooding, tool loops, expansion pressure.
4. No reliance on magic string buffer_fill_seq.
"""
from __future__ import annotations

import time
import re
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class ResourceBudget:
    max_input_tokens: int = 1024
    max_output_tokens: int = 512
    max_total_tokens: int = 1536
    max_retrieval_ops: int = 10
    max_tool_proposals: int = 5
    max_tool_executions: int = 3
    max_recursion_depth: int = 3
    max_wall_clock_ms: float = 30000.0

    def to_dict(self) -> dict:
        return {
            "max_input_tokens": int(self.max_input_tokens),
            "max_output_tokens": int(self.max_output_tokens),
            "max_retrievals": int(self.max_retrieval_ops),
            "max_tool_calls": int(self.max_tool_executions),
            "timeout_ms": int(self.max_wall_clock_ms),
            "max_depth": int(self.max_recursion_depth),
        }


@dataclass
class ResourceUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    retrieval_ops: int = 0
    tool_proposals: int = 0
    tool_executions: int = 0
    recursion_depth: int = 0
    start_time_ns: int = field(default_factory=time.perf_counter_ns)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def elapsed_ms(self) -> float:
        return (time.perf_counter_ns() - self.start_time_ns) / 1_000_000.0


class ResourceTracker:
    """Tracks dynamic runtime resource consumption and enforces quantitative budgets."""

    def __init__(self, budget: Optional[ResourceBudget] = None):
        self.budget = budget or ResourceBudget()
        self.usage = ResourceUsage()

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimates token count using a fast whitespace + character ratio heuristic."""
        if not text:
            return 0
        words = re.findall(r"\S+", text)
        char_count = len(text)
        # Average English/Korean token is approx 4 characters or 0.75 words
        return max(len(words), int(char_count / 3.8) + 1)

    def track_input(self, text: str) -> None:
        self.usage.input_tokens += self.estimate_tokens(text)

    def track_output(self, text: str) -> None:
        self.usage.output_tokens += self.estimate_tokens(text)

    def track_retrieval(self, count: int = 1) -> None:
        self.usage.retrieval_ops += count

    def track_tool_proposal(self, count: int = 1) -> None:
        self.usage.tool_proposals += count

    def track_tool_execution(self, count: int = 1) -> None:
        self.usage.tool_executions += count

    def track_recursion_step(self) -> None:
        self.usage.recursion_depth += 1

    def check_budget(self) -> Tuple[bool, str]:
        """Evaluates whether accumulated usage exceeds configured budget limits.

        Returns: (is_exceeded, rejection_reason)
        """
        if self.usage.input_tokens > self.budget.max_input_tokens:
            return True, f"Input token limit exceeded: {self.usage.input_tokens} > {self.budget.max_input_tokens}"

        if self.usage.output_tokens > self.budget.max_output_tokens:
            return True, f"Output token limit exceeded: {self.usage.output_tokens} > {self.budget.max_output_tokens}"

        if self.usage.total_tokens > self.budget.max_total_tokens:
            return True, f"Total token budget exceeded: {self.usage.total_tokens} > {self.budget.max_total_tokens}"

        if self.usage.retrieval_ops > self.budget.max_retrieval_ops:
            return True, f"Retrieval expansion limit exceeded: {self.usage.retrieval_ops} > {self.budget.max_retrieval_ops}"

        if self.usage.tool_proposals > self.budget.max_tool_proposals:
            return True, f"Tool proposal flood detected: {self.usage.tool_proposals} > {self.budget.max_tool_proposals}"

        if self.usage.tool_executions > self.budget.max_tool_executions:
            return True, f"Tool execution limit exceeded: {self.usage.tool_executions} > {self.budget.max_tool_executions}"

        if self.usage.recursion_depth > self.budget.max_recursion_depth:
            return True, f"Recursion depth exceeded: {self.usage.recursion_depth} > {self.budget.max_recursion_depth}"

        if self.usage.elapsed_ms > self.budget.max_wall_clock_ms:
            return True, f"Wall-clock execution timeout exceeded: {self.usage.elapsed_ms:.1f}ms > {self.budget.max_wall_clock_ms:.1f}ms"

        return False, ""

    def check_and_consume_tokens(self, tokens: int) -> Tuple[bool, str]:
        """Compatibility method for token consumption check."""
        if self.usage.input_tokens + tokens > self.budget.max_input_tokens:
            return False, f"Token limit exceeded: {self.usage.input_tokens + tokens} > {self.budget.max_input_tokens}"
        self.usage.input_tokens += tokens
        return True, "OK"

    def check_timeout(self) -> Tuple[bool, str]:
        """Compatibility method for execution timeout check."""
        if self.usage.elapsed_ms > self.budget.max_wall_clock_ms:
            return False, f"Execution timeout exceeded: {self.usage.elapsed_ms:.1f}ms > {self.budget.max_wall_clock_ms:.1f}ms"
        return True, "OK"
