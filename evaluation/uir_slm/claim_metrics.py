#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation

CLAIM_TYPES = {"entity_claim", "attribute_claim", "numeric_claim", "relation_claim", "temporal_claim", "provenance_claim"}
FIELDS = ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance")


def parse_output(text: str) -> tuple[str, list[dict], str | None]:
    candidate = text.strip(); match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if match: candidate = match.group(0)
    try: payload = json.loads(candidate)
    except json.JSONDecodeError as error: return text, [], f"SLM_FORMAT_ERROR:{error.msg}"
    claims = payload.get("claims", [])
    if not isinstance(claims, list): return str(payload.get("answer", "")), [], "SLM_FORMAT_ERROR:claims_not_array"
    normalized = []
    for claim in claims:
        if not isinstance(claim, dict) or claim.get("claim_type") not in CLAIM_TYPES: continue
        normalized.append({field: "" if claim.get(field) is None else str(claim.get(field, "")).strip() for field in FIELDS})
    return str(payload.get("answer", "")), normalized, None


def claim_key(claim: dict) -> tuple[str, ...]: return tuple(str(claim.get(field, "")).strip() for field in FIELDS)


def evaluate_claims(expected: list[dict], generated: list[dict], accepted: list[dict] | None = None) -> dict:
    expected_keys = {claim_key(item) for item in expected}; generated_keys = [claim_key(item) for item in generated]; supported = sum(key in expected_keys for key in generated_keys); required = sum(key in set(generated_keys) for key in expected_keys); total = len(generated_keys); accepted_claims = generated if accepted is None else accepted; accepted_unsupported = sum(claim_key(item) not in expected_keys for item in accepted_claims)
    result = {"generated_claims": total, "supported_claims": supported, "required_claims": len(expected_keys), "recalled_claims": required, "unsupported_claims": total - supported, "accepted_claims": len(accepted_claims), "accepted_unsupported_claims": accepted_unsupported, "claim_precision": supported / total if total else (1.0 if not expected_keys else 0.0), "claim_recall": required / len(expected_keys) if expected_keys else 1.0, "unsupported_claim_rate": (total - supported) / total if total else 0.0, "unsupported_claim_acceptance_rate": accepted_unsupported / len(accepted_claims) if accepted_claims else 0.0}
    for claim_type in CLAIM_TYPES:
        subset = [item for item in generated if item["claim_type"] == claim_type]; expected_subset = {claim_key(item) for item in expected if item.get("claim_type") == claim_type}; result[f"{claim_type}_accuracy"] = sum(claim_key(item) in expected_subset for item in subset) / len(subset) if subset else (1.0 if not expected_subset else 0.0)
    numeric = [item for item in generated if item["claim_type"] == "numeric_claim"]
    expected_numeric = {claim_key(item) for item in expected if item.get("claim_type") == "numeric_claim"}
    result["numeric_exact_match"] = sum(claim_key(item) in expected_numeric for item in numeric) / len(numeric) if numeric else (1.0 if not expected_numeric else 0.0)
    result["entity_accuracy"] = result["entity_claim_accuracy"]; result["relation_accuracy"] = result["relation_claim_accuracy"]; result["temporal_accuracy"] = result["temporal_claim_accuracy"]; result["provenance_accuracy"] = result["provenance_claim_accuracy"]
    return result


def validate_against_facts(generated: list[dict], facts: list[dict]) -> tuple[list[dict], list[dict]]:
    allowed = {claim_key(item) for item in facts}; accepted = [item for item in generated if claim_key(item) in allowed]; rejected = [item for item in generated if claim_key(item) not in allowed]; return accepted, rejected


def numeric_dimensions(expected: list[dict], generated: list[dict]) -> dict:
    expected_numeric = [item for item in expected if item.get("claim_type") == "numeric_claim"] or expected; generated_numeric = [item for item in generated if item.get("claim_type") == "numeric_claim"]
    exact = unit = sign = relative = 0
    for target in expected_numeric:
        candidates = [item for item in generated_numeric if item.get("entity_id") == target.get("entity_id") and item.get("attribute") == target.get("attribute") and item.get("period") == target.get("period")]
        if not candidates: continue
        item = candidates[0]; exact += item.get("value") == target.get("value"); unit += item.get("unit") == target.get("unit")
        try: sign += (Decimal(item["value"]) >= 0) == (Decimal(target["value"]) >= 0)
        except (InvalidOperation, KeyError): pass
        if target.get("attribute") in {"year_over_year_delta", "gdp_to_population_ratio"}: relative += item.get("value") == target.get("value")
        else: relative += 1
    total = len(expected_numeric)
    return {"numeric_exact_match": exact / total if total else 1.0, "unit_accuracy": unit / total if total else 1.0, "sign_accuracy": sign / total if total else 1.0, "relative_change_accuracy": relative / total if total else 1.0}
