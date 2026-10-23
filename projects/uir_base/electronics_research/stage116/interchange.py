"""Finite S1 wire/native interchange; not an independent decision backend."""
from copy import deepcopy

from uir_common.contracts import canonical_digest, reject_gold
from uir_common.query_contract import VERSION


class InterchangeFailure(ValueError):
    pass


def _check(artifact, packet):
    reject_gold(packet)
    required = {"metadata", "semantics", "policy_constraints", "execution_contract", "output_contract", "semantic_digest"}
    if set(artifact) != required or not isinstance(artifact["metadata"], dict):
        raise InterchangeFailure("LOSS_OR_UNKNOWN_SECTION")
    bound = {k: artifact[k] for k in required - {"metadata", "semantic_digest"}}
    if canonical_digest(bound) != artifact["semantic_digest"]:
        raise InterchangeFailure("SEMANTIC_DIGEST_MISMATCH")
    execution = artifact["execution_contract"]
    if execution.get("version") != VERSION:
        raise InterchangeFailure("UNSUPPORTED_INSTRUCTION_VERSION")
    query = artifact["semantics"]
    if (set(query) != {"entity", "metric", "period", "unit", "predicate"}
            or any(not isinstance(query[k], str) for k in ("entity", "metric", "period", "unit"))):
        raise InterchangeFailure("UNSUPPORTED_QUERY_SHAPE")
    predicate = query["predicate"]
    if predicate is not None and (not isinstance(predicate, dict) or set(predicate) != {"op", "field", "value"}
            or predicate["op"] != "EQ_BOOL" or not isinstance(predicate["field"], str) or type(predicate["value"]) is not bool):
        raise InterchangeFailure("UNSUPPORTED_PREDICATE")
    policy = artifact["policy_constraints"]
    if (set(policy) != {"version", "action", "allowed_operations"} or policy["action"] not in {"read", "write"}
            or policy["allowed_operations"] != ["read", "PERCENT_DIV"]
            or artifact["output_contract"] != {"language": "CLOSED_FACT_LINES_S1", "partial": True, "dependency_closure": True}):
        raise InterchangeFailure("UNSUPPORTED_CONTRACT_INSTRUCTION")
    if execution["evidence_version"] != packet["current_evidence_version"] or artifact["policy_constraints"]["version"] != packet["authority"]["version"]:
        raise InterchangeFailure("SNAPSHOT_MISMATCH")
    evidence = {"version": execution["evidence_version"], "facts": execution["facts"], "trusted_provenance": execution["trusted_provenance"]}
    if canonical_digest(evidence) != packet["current_evidence_sha256"]:
        raise InterchangeFailure("EVIDENCE_BINDING_MISMATCH")


def to_native(packet):
    try:
        artifact = packet["artifact"]
        _check(artifact, packet)
        envelope = {k: deepcopy(packet[k]) for k in ("authority", "context", "current_evidence_version", "current_evidence_sha256")}
        envelope["transport_metadata"] = deepcopy(artifact["metadata"])
        envelope["private_plan"] = {k: deepcopy(artifact[v]) for k, v in
            {"query": "semantics", "permission": "policy_constraints", "evidence": "execution_contract", "display": "output_contract"}.items()}
        if set(packet) != {"artifact", *envelope.keys() - {"transport_metadata", "private_plan"}}:
            raise InterchangeFailure("UNKNOWN_ENVELOPE_FIELDS")
        return envelope
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, InterchangeFailure):
            raise
        raise InterchangeFailure("MALFORMED_PACKET") from exc


def to_uir(packet):
    try:
        if set(packet) != {"private_plan", "transport_metadata", "authority", "context", "current_evidence_version", "current_evidence_sha256"}:
            raise InterchangeFailure("UNKNOWN_NATIVE_ENVELOPE")
        plan = packet["private_plan"]
        if set(plan) != {"query", "permission", "evidence", "display"}:
            raise InterchangeFailure("LOSS_OR_UNKNOWN_NATIVE_FIELD")
        artifact = {k: deepcopy(plan[v]) for k, v in
            {"semantics": "query", "policy_constraints": "permission", "execution_contract": "evidence", "output_contract": "display"}.items()}
        artifact["semantic_digest"] = canonical_digest(artifact)
        artifact["metadata"] = deepcopy(packet["transport_metadata"])
        result = {k: deepcopy(packet[k]) for k in ("authority", "context", "current_evidence_version", "current_evidence_sha256")}
        result["artifact"] = artifact
        _check(artifact, result)
        return result
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, InterchangeFailure):
            raise
        raise InterchangeFailure("MALFORMED_NATIVE_PACKET") from exc
