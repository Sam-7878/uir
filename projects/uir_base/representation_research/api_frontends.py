"""New structured JSON frontend, not a new free-natural-language parser."""
from uir_common.contracts import canonical_digest, reject_gold
from uir_common.query_contract import make_artifact, VERSION


def typed_query(payload):
    reject_gold(payload)
    if set(payload) != {"entity", "metric", "period", "unit", "predicate"}:
        raise ValueError("API_FIELDS")
    if not all(isinstance(payload[k], str) and payload[k] for k in ("entity", "metric", "period", "unit")):
        raise ValueError("API_STRING_TYPES")
    if len(payload["period"]) != 4 or not payload["period"].isdigit() or payload["predicate"] is not None:
        raise ValueError("API_PERIOD_OR_PREDICATE_FRAGMENT")
    return dict(payload)


def shared(payload, authority, source):
    return {"artifact": make_artifact(typed_query(payload), authority, source), "authority": authority,
            "current_evidence_version": source["version"], "current_evidence_sha256": canonical_digest(source), "context": {}}


def specialized(payload, authority, source):
    return {"private_plan": {"query": typed_query(payload),
            "permission": {"version": authority["version"], "action": "read", "allowed_operations": ["read", "PERCENT_DIV"]},
            "evidence": {"version": VERSION, "evidence_version": source["version"], "facts": source["facts"], "trusted_provenance": source["trusted_provenance"]},
            "display": {"language": "CLOSED_FACT_LINES_S1", "partial": True, "dependency_closure": True}},
            "authority": authority, "current_evidence_version": source["version"], "current_evidence_sha256": canonical_digest(source), "context": {}}
