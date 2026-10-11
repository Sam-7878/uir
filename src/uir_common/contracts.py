"""Small reference execution contract (revision v1, not historical inference).

No evaluator, expected-answer or project dependency belongs in this module.
Fact trust and policy authority are explicit inputs, not inferred from model text.
"""
from __future__ import annotations
import hashlib
import json
import unicodedata
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN
from enum import StrEnum
from typing import Mapping
import rfc8785

FIELDS = ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance")
FORBIDDEN = {"expected_claims", "expected_outcome", "gold_label", "gold_answer", "gold_program", "gold_judgement", "scoring_only", "adjudication", "is_adversarial", "is_policy_violation", "is_invalid_entity"}


def reject_gold(value):
    if isinstance(value, dict):
        keys = {unicodedata.normalize("NFKC", str(k)).casefold().replace("-", "_") for k in value}
        if (FORBIDDEN & keys or keys & {"gold", "expected", "ground_truth", "groundtruth"}
                or any(k.startswith(("gold_", "expected_", "ground_truth_", "groundtruth_"))
                       or k.endswith("_gold") for k in keys)):
            raise ValueError("Evaluation-only fields at runtime boundary")
        for child in value.values():
            reject_gold(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_gold(child)


def normalize(value):
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        result = {normalize(k): normalize(v) for k, v in value.items()}
        if len(result) != len(value):
            raise ValueError("Unicode normalization key collision")
        return result
    if isinstance(value, (tuple, list)):
        return [normalize(v) for v in value]
    return value


def canonical_digest(value):
    return hashlib.sha256(rfc8785.dumps(normalize(value))).hexdigest()


@dataclass(frozen=True)
class RuntimeContract:
    entity: str
    attribute: str
    period: str
    policy_snapshot: str
    evidence_snapshot: str
    action: str = "read"
    version: str = "uir-reference-v1"

    @property
    def digest(self):
        # Language, raw text, timing and case IDs are frontend/audit metadata.
        return canonical_digest(asdict(self))


class State(StrEnum):
    QUARANTINE = "QUARANTINE"
    CLARIFICATION = "CLARIFICATION"
    DENY = "DENY"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    READ_ONLY = "READ_ONLY"
    FULL = "FULL_VERIFIED_ANSWER"
    PARTIAL = "PARTIAL_VERIFIED_ANSWER"
    NONE = "NO_VERIFIED_ANSWER"


def transition(*, quarantined=False, compiles=True, policy="ALLOW", action="read", approved=False,
               snapshot_current=True, required_count=0, selected_count=0, partial=True):
    if policy not in {"ALLOW", "DENY", "REQUIRE_APPROVAL", "READ_ONLY"}:
        raise ValueError("Unknown policy decision")
    if selected_count < 0 or required_count < 0 or selected_count > required_count:
        raise ValueError("Invalid claim counts")
    if quarantined or not snapshot_current:
        return State.QUARANTINE
    if not compiles:
        return State.CLARIFICATION
    if policy == "DENY":
        return State.DENY
    if policy == "REQUIRE_APPROVAL" and not approved:
        return State.APPROVAL_PENDING
    if policy == "READ_ONLY" and action != "read":
        return State.READ_ONLY
    if selected_count == 0:
        return State.NONE
    if selected_count == required_count:
        return State.FULL
    return State.PARTIAL if partial else State.NONE


def matches(fact, contract):
    return str(fact.get("entity_id", "")) == contract.entity and str(fact.get("attribute", "")) == contract.attribute and str(fact.get("period", "")) == contract.period


def bind_references(contract: RuntimeContract, facts: Mapping[str, dict], refs: list[str], *, policy="ALLOW", approved=False,
                    snapshot_current=True, partial=True):
    reject_gold(facts)
    required = {k: v for k, v in facts.items() if matches(v, contract)}
    # Unknown references cannot expand authority; copied values always come from facts.
    selected = [k for k in dict.fromkeys(refs) if k in required]
    state = transition(policy=policy, action=contract.action, approved=approved, snapshot_current=snapshot_current,
                       required_count=len(required), selected_count=len(selected), partial=partial)
    claims = [{k: str(required[ref].get(k, "")) for k in FIELDS} for ref in selected] if state in {State.FULL, State.PARTIAL} else []
    return {"state": state.value, "claims": claims, "fact_refs": selected if claims else [], "contract_digest": contract.digest}


@dataclass(frozen=True)
class NumericFact:
    value: str
    unit: str
    period: str
    provenance: str


def derive(expression: dict, facts: Mapping[str, NumericFact], *, scale=6):
    """Bounded DAG arithmetic; operands and units remain part of provenance.

No arbitrary literal operands, code evaluation, cross-period arithmetic or powers.
add/sub require same units; division of same units produces dimensionless value.
"""
    if not 0 <= scale <= 12:
        raise ValueError("Unsupported precision")
    visited = 0
    operand_ids = set()

    def walk(node, depth=0):
        nonlocal visited
        visited += 1
        if visited > 32 or depth > 8:
            raise ValueError("Expression resource limit")
        if isinstance(node, str):
            if node not in facts:
                raise ValueError("Unknown operand")
            fact = facts[node]
            value = Decimal(fact.value)
            if not value.is_finite() or abs(value) > Decimal("1e30"):
                raise ValueError("Invalid numeric operand")
            operand_ids.add(node)
            return value, fact.unit, fact.period
        if not isinstance(node, dict) or set(node) != {"op", "args"} or not isinstance(node["args"], list) or len(node["args"]) != 2:
            raise ValueError("Malformed arithmetic node")
        op = node["op"]
        if op not in {"add", "subtract", "multiply", "divide"}:
            raise ValueError("Unsupported operation")
        a, ua, pa = walk(node["args"][0], depth+1)
        b, ub, pb = walk(node["args"][1], depth+1)
        if pa != pb:
            raise ValueError("Temporal binding mismatch")
        if op in {"add", "subtract"} and ua != ub:
            raise ValueError("Unit mismatch")
        if op == "divide" and b == 0:
            raise ValueError("Division by zero")
        value = a+b if op == "add" else a-b if op == "subtract" else a*b if op == "multiply" else a/b
        unit = ua if op in {"add", "subtract"} else f"{ua}*{ub}" if op == "multiply" else "1" if ua == ub else f"{ua}/{ub}"
        if not value.is_finite() or abs(value) > Decimal("1e30"):
            raise ValueError("Overflow")
        return value, unit, pa

    try:
        with localcontext() as context:
            context.prec = 48
            value, unit, period = walk(expression)
            value = value.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise ValueError("Invalid arithmetic") from exc
    operands = {k: asdict(facts[k]) for k in sorted(operand_ids)}
    return {"value": str(value), "unit": unit, "period": period, "operand_ids": sorted(operand_ids),
            "expression": expression, "rounding": "ROUND_HALF_EVEN", "scale": scale,
            "provenance_digest": canonical_digest({"expression": expression, "operands": operands, "scale": scale, "rounding": "ROUND_HALF_EVEN"})}
