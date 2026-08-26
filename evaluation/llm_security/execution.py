"""Observable execution records and a non-destructive mock tool executor.

Pipelines own these records; only judges may derive attack or utility outcomes.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


TERMINAL_STATUSES = {"RESPONDED", "BLOCKED", "ERROR", "TIMEOUT"}


def new_execution_record(case: Dict[str, Any], baseline: str) -> Dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "baseline": baseline,
        "attack_class": case["attack_class"],
        "language": case.get("language", "unknown"),
        "policy_outcome": "NOT_EVALUATED",
        "model_output": "",
        "final_output": "",
        "tool_calls": [],
        "retrieved_evidence_ids": [item.get("source_id", "unknown") for item in case.get("context", [])],
        "accepted_evidence_ids": [],
        "blocked_evidence_ids": [],
        "data_disclosures": [],
        "resource_usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "retrieval_count": len(case.get("context", [])),
            "tool_call_count": 0,
            "recursion_depth": 1,
            "elapsed_ms": 0.0,
        },
        "guard_events": [],
        "terminal_status": "ERROR",
    }


def add_guard_event(record: Dict[str, Any], component: str, decision: str, detail: str = "") -> None:
    record["guard_events"].append({"component": component, "decision": decision, "detail": detail})


def attach_generation(record: Dict[str, Any], text: str, input_tokens: int, output_tokens: int, elapsed_ms: float, model_name: str) -> None:
    record["model_output"] = text
    record["final_output"] = text
    record["resource_usage"].update({
        "input_tokens": int(input_tokens), "output_tokens": int(output_tokens),
        "elapsed_ms": float(elapsed_ms),
    })
    record["model_name"] = model_name
    record["terminal_status"] = "RESPONDED"


class MockToolExecutor:
    """Records proposed and attempted tool calls without performing real side effects."""

    def execute(self, proposals: Iterable[Dict[str, Any]], allowed_capabilities: Iterable[str]) -> List[Dict[str, Any]]:
        allowed = set(allowed_capabilities)
        calls: List[Dict[str, Any]] = []
        for proposal in proposals:
            capability = str(proposal.get("capability", ""))
            authorized = capability in allowed
            calls.append({
                "name": proposal.get("name", "unknown"),
                "capability": capability,
                "proposed": True,
                "attempted": True,
                "executed": authorized,
                "authorization": "PERMITTED" if authorized else "DENIED",
            })
        return calls
