"""Native specialized plan: same CNL/capabilities/decision engine, no UIR artifact."""
from uir_common.contracts import canonical_digest, reject_gold
from uir_common.query_contract import parse_raw, VERSION


def packet_for_specialized(row, source=None):
    reject_gold(row)
    source = source or row["source"]
    return {"private_plan": {"query": parse_raw(row["raw_user_request"]),
            "permission": {"version": row["authority"]["version"], "action": row["action"], "allowed_operations": ["read", "PERCENT_DIV"]},
            "evidence": {"version": VERSION, "evidence_version": source["version"], "facts": source["facts"], "trusted_provenance": source["trusted_provenance"]},
            "display": {"language": "CLOSED_FACT_LINES_S1", "partial": True, "dependency_closure": True}},
            "authority": row["authority"], "current_evidence_version": source["version"],
            "current_evidence_sha256": canonical_digest(source), "context": row["context"]}
