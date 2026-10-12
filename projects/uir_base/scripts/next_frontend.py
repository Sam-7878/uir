"""Raw-only restricted bilingual CNL v2; not a free-NL accuracy experiment."""
from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
import re
import unicodedata

from projects.uir_base.scripts.contract_frontend import compile_cnl
from uir_common.contracts import canonical_digest, reject_gold, transition

FIELDS = {"verified_provenance": "verified_provenance", "approval": "approval",
          "entity_verified": "entity_verified", "value": "value", "출처확인": "verified_provenance",
          "승인": "approval", "기업확인": "entity_verified", "값": "value"}
ALIASES = {"그리고": "AND", "또는": "OR", "아님": "NOT", "참": "true", "거짓": "false"}
TOKEN = re.compile(r"\s*(>=|<=|==|!=|[()<>]|-?\d+(?:\.\d+)?|[A-Za-z_가-힣]+)")


def expression(text):
    tokens = []
    pos = 0
    while pos < len(text.strip()):
        found = TOKEN.match(text, pos)
        if found is None:
            raise ValueError("Unsupported condition token")
        token = found.group(1)
        tokens.append(ALIASES.get(token, token))
        pos = found.end()
    if len(tokens) > 128:
        raise ValueError("Condition resource limit")
    index = 0

    def atom(depth):
        nonlocal index
        if depth > 16 or index >= len(tokens):
            raise ValueError("Incomplete or too deeply nested condition")
        token = tokens[index]; index += 1
        if token == "NOT":
            return {"op": "NOT", "arg": atom(depth + 1)}
        if token == "(":
            node = disjunction(depth + 1)
            if index >= len(tokens) or tokens[index] != ")":
                raise ValueError("Unbalanced condition")
            index += 1
            return node
        if token not in FIELDS:
            raise ValueError("Unknown condition field")
        field = FIELDS[token]
        op, value, kind = "==", True, "BOOLEAN"
        if index < len(tokens) and tokens[index] in {"==", "!=", ">", "<", ">=", "<="}:
            op = tokens[index]; index += 1
            if index >= len(tokens):
                raise ValueError("Missing comparison operand")
            operand = tokens[index]; index += 1
            if operand in {"true", "false"}:
                value = operand == "true"
            elif re.fullmatch(r"-?\d+(?:\.\d+)?", operand):
                value = format(Decimal(operand).normalize(), "f"); kind = "DECIMAL"
            else:
                raise ValueError("Unsupported comparison operand")
        if (field == "value") != (kind == "DECIMAL") or (kind == "BOOLEAN" and op not in {"==", "!="}):
            raise ValueError("Condition operand type mismatch")
        return {"field": field, "op": op, "type": kind, "value": value}

    def conjunction(depth):
        nonlocal index
        node = atom(depth)
        while index < len(tokens) and tokens[index] == "AND":
            index += 1; node = {"op": "AND", "args": [node, atom(depth)]}
        return node

    def disjunction(depth):
        nonlocal index
        node = conjunction(depth)
        while index < len(tokens) and tokens[index] == "OR":
            index += 1; node = {"op": "OR", "args": [node, conjunction(depth)]}
        return node

    result = disjunction(0)
    if index != len(tokens):
        raise ValueError("Unconsumed condition tokens")
    return result


def compile_raw(text, *, policy_snapshot, evidence_snapshot):
    text = unicodedata.normalize("NFC", text).strip()
    parts = re.split(r"\s+(only if|unless|if|조건:)\s*", text, maxsplit=1)
    base = parts[0]
    unit_match = re.search(r"\s+(?:in|단위) ([A-Z]{3}|percent|1)$", base)
    unit = unit_match.group(1) if unit_match else None
    if unit_match:
        base = base[:unit_match.start()]
    try:
        contract = compile_cnl(base, policy_snapshot=policy_snapshot, evidence_snapshot=evidence_snapshot)
        condition = expression(parts[2]) if len(parts) == 3 else None
        if len(parts) == 3 and parts[1] == "unless":
            condition = {"op": "NOT", "arg": condition}
    except ValueError as exc:
        return {"status": "CLARIFICATION_REQUIRED", "reason": str(exc), "uir": None}
    uir = {"schema_version": "uir-cnl-v2", "input_route": "raw_only",
           "contract": asdict(contract), "unit": unit,
           "system_constraints": ["verified_provenance"], "user_condition": condition}
    return {"status": "OK", "uir": uir, "semantic_digest": canonical_digest(uir)}


def evaluate_condition(node, context):
    reject_gold(context)
    if node is None:
        return True
    if node["op"] == "NOT":
        return not evaluate_condition(node["arg"], context)
    if node["op"] in {"AND", "OR"}:
        values = [evaluate_condition(child, context) for child in node["args"]]
        return all(values) if node["op"] == "AND" else any(values)
    if node["field"] not in context:
        raise ValueError("Missing observable condition input")
    actual = context[node["field"]]
    expected = node["value"]
    if node["type"] == "DECIMAL":
        actual, expected = Decimal(str(actual)), Decimal(expected)
        if not actual.is_finite():
            raise ValueError("Nonfinite observable input")
    elif not isinstance(actual, bool):
        raise ValueError("Boolean observable input required")
    return {"==": lambda: actual == expected, "!=": lambda: actual != expected,
            ">": lambda: actual > expected, "<": lambda: actual < expected,
            ">=": lambda: actual >= expected, "<=": lambda: actual <= expected}[node["op"]]()


def sandbox_action(*, action="read", policy="ALLOW", approved=False,
                   bound_snapshot="p1", current_snapshot="p1"):
    """In-memory action opportunity: no operating-system or external tool effects."""
    if action not in {"read", "write"}:
        raise ValueError("Unknown sandbox capability")
    state = transition(policy=policy, action=action, approved=approved,
                       snapshot_current=bound_snapshot == current_snapshot,
                       required_count=1, selected_count=1)
    executed = state.value == "FULL_VERIFIED_ANSWER"
    return {"action": action, "policy": policy, "state": state.value,
            "attempted": True, "executed": executed, "blocked": not executed,
            "bound_snapshot": bound_snapshot, "current_snapshot": current_snapshot,
            "effect": {"read_result": "public-fixture"} if executed and action == "read"
            else {"fixture_write": "committed"} if executed else {}}
