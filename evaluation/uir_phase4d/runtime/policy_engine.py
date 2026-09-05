"""Executable Policy Evaluation Engine (Assumption A2).

Evaluates user queries and requested actions against the authoritative policy store.
Execution is dynamically computed from query text and request metadata;
it NEVER relies on dataset-level flags (e.g. policy_valid).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from evaluation.uir_phase4d.common import ROOT

RULES_PATH = ROOT / "evaluation/uir_phase4d/runtime/policy_rules.yaml"


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    READ_ONLY = "READ_ONLY"


@dataclass(frozen=True)
class PolicyEvaluationResult:
    decision: PolicyDecision
    reason: str
    rule_id: str | None


class PolicyEngine:
    def __init__(self, rules_file: Path | None = None) -> None:
        path = rules_file or RULES_PATH
        if not path.exists():
            raise FileNotFoundError(f"Policy rules specification not found at {path}")
        self._config = yaml.safe_load(path.read_text(encoding="utf-8"))
        self._disallowed_patterns = [
            (item["id"], re.compile(item["pattern_regex"]), item["description"], item["decision"])
            for item in self._config.get("disallowed_request_patterns", [])
        ]
        self._confidential_attrs = set(self._config.get("confidential_attributes", []))
        self._public_attrs = set(self._config.get("public_attributes", []))

    def list_rules(self) -> list[str]:
        return [item[0] for item in self._disallowed_patterns]

    def evaluate(
        self,
        request_text: str,
        principal: str = "standard_analyst",
        requested_attribute: str = "",
        action: str = "AUDIT_VERIFY",
    ) -> PolicyEvaluationResult:
        # 1. Check disallowed pattern in request
        for rule_id, pattern, desc, dec in self._disallowed_patterns:
            if pattern.search(request_text):
                return PolicyEvaluationResult(
                    decision=PolicyDecision(dec),
                    reason=f"Violates policy rule {rule_id}: {desc}",
                    rule_id=rule_id,
                )

        # 2. Check confidential attributes
        if requested_attribute and requested_attribute.lower() in self._confidential_attrs:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                reason=f"Access to confidential attribute '{requested_attribute}' prohibited by information barrier",
                rule_id="POL-CONFIDENTIAL",
            )

        # 3. Default check
        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="Request complies with standard financial disclosure policy",
            rule_id="POL-DEFAULT-ALLOW",
        )
