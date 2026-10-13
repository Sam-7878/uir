"""S-stage public query contract and restricted raw-language compiler.

This module defines syntax/transport, not the independent interpreters' decisions.
No evaluator or scoring imports are permitted here.
"""
import re
from .contracts import canonical_digest, reject_gold

VERSION = "uir-query-contract-S1"
METRICS = {"자산": "assets", "매출": "revenue", "순이익": "profit", "이익률": "margin"}
SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["metadata", "semantics", "policy_constraints", "execution_contract", "output_contract", "semantic_digest"],
          "properties": {"metadata": {"type": "object"}, "semantics": {"type": "object"},
                         "policy_constraints": {"type": "object"}, "execution_contract": {"type": "object"},
                         "output_contract": {"type": "object"}, "semantic_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}}


def parse_raw(raw):
    """Declared CNL only; raw Korean is actually Korean. No trusted slots."""
    english = re.fullmatch(r"(?:Please )?show ([A-Z][A-Z0-9_]*) (assets|revenue|profit|margin) for (20\d\d) in (USD|EUR|percent)(?: if (active|approved) (is|is not) true)?\.", raw)
    korean = re.fullmatch(r"(?:부탁드립니다\. )?([A-Z][A-Z0-9_]*)의 (20\d\d)년 (자산|매출|순이익|이익률)을 (USD|EUR|percent) 단위로 보여 주세요(?:\. 단, (활성|승인) 상태가 (참|거짓)일 때만)?\.", raw)
    if english:
        entity, metric, period, unit, field, negation = english.groups()
        predicate = None if field is None else {"op": "EQ_BOOL", "field": field, "value": negation == "is"}
    elif korean:
        entity, period, metric, unit, field, value = korean.groups()
        metric = METRICS[metric]
        predicate = None if field is None else {"op": "EQ_BOOL", "field": {"활성": "active", "승인": "approved"}[field], "value": value == "참"}
    else:
        raise ValueError("CLARIFICATION_UNSUPPORTED_RAW_LANGUAGE")
    return {"entity": entity, "metric": metric, "period": period, "unit": unit, "predicate": predicate}


def make_artifact(semantics, authority, source, *, action="read"):
    reject_gold(semantics)
    reject_gold(authority)
    reject_gold(source)
    body = {"semantics": semantics,
            "policy_constraints": {"version": authority["version"], "action": action, "allowed_operations": ["read", "PERCENT_DIV"]},
            "execution_contract": {"version": VERSION, "evidence_version": source["version"], "facts": source["facts"],
                                   "trusted_provenance": source["trusted_provenance"]},
            "output_contract": {"language": "CLOSED_FACT_LINES_S1", "partial": True, "dependency_closure": True}}
    return {"metadata": {}, **body, "semantic_digest": canonical_digest(body)}


def semantic_key(semantics):
    return canonical_digest(semantics)


def public_line(fact):
    """Complete approved user-visible grammar, including citation, with no extra prose."""
    return f"{fact['entity']} | {fact['metric']} | {fact['period']} | {fact['value']} {fact['unit']} | source={fact['provenance']}"
