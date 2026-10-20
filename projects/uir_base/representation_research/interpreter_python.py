"""Independent Python S1 reference decisions (does not import prior accept())."""
import re
from uir_common.contracts import canonical_digest, reject_gold
from uir_common.query_contract import VERSION


def interpret(packet):
    """Finite closed-world semantics; integer facts and exact integer percentages."""
    try:
        reject_gold(packet)
        if "private_plan" in packet:
            # Capability-equivalent specialized control uses a native in-process
            # plan and the same decision engine, not a public UIR serialization.
            native = packet["private_plan"]
            if set(native) != {"query", "permission", "evidence", "display"}:
                raise ValueError("PRIVATE_PLAN_FIELDS")
            query, policy, execution, output = [native[k] for k in ("query", "permission", "evidence", "display")]
        else:
            artifact = packet["artifact"]
            if set(artifact) != {"metadata", "semantics", "policy_constraints", "execution_contract", "output_contract", "semantic_digest"}:
                raise ValueError("SECTIONS")
            bound = {k: artifact[k] for k in ("semantics", "policy_constraints", "execution_contract", "output_contract")}
            if canonical_digest(bound) != artifact["semantic_digest"]:
                raise ValueError("DIGEST")
            query, policy, execution, output = [artifact[k] for k in ("semantics", "policy_constraints", "execution_contract", "output_contract")]
        if (execution["version"] != VERSION or set(query) != {"entity", "metric", "period", "unit", "predicate"}
                or output != {"language": "CLOSED_FACT_LINES_S1", "partial": True, "dependency_closure": True}
                or policy["allowed_operations"] != ["read", "PERCENT_DIV"] or policy["action"] not in {"read", "write"}):
            raise ValueError("VERSION_OR_SCHEMA")
        authority = packet["authority"]
        if policy["version"] != authority["version"] or execution["evidence_version"] != packet["current_evidence_version"]:
            raise ValueError("STALE_SNAPSHOT")
        evidence = {"version": execution["evidence_version"], "facts": execution["facts"], "trusted_provenance": execution["trusted_provenance"]}
        if canonical_digest(evidence) != packet["current_evidence_sha256"]:
            raise ValueError("EVIDENCE_ROOT_MISMATCH")
        predicate = query["predicate"]
        if predicate is not None:
            if (set(predicate) != {"op", "field", "value"} or predicate["op"] != "EQ_BOOL"
                    or not isinstance(predicate["field"], str)
                    or type(predicate["value"]) is not bool or type(packet["context"].get(predicate["field"])) is not bool):
                return {"state": "CLARIFICATION", "fact_ids": []}
            if packet["context"][predicate["field"]] != predicate["value"]:
                return {"state": "DENY", "fact_ids": []}
        decision = authority["decision"]
        if decision == "DENY":
            return {"state": "DENY", "fact_ids": []}
        if decision == "APPROVAL" and authority.get("approved") is not True:
            return {"state": "APPROVAL_PENDING", "fact_ids": []}
        if decision == "READ_ONLY" and policy["action"] == "write":
            return {"state": "READ_ONLY", "fact_ids": []}
        if decision not in {"ALLOW", "APPROVAL", "READ_ONLY"}:
            raise ValueError("UNKNOWN_POLICY")
        if policy["action"] not in policy["allowed_operations"]:
            return {"state": "DENY", "fact_ids": []}
        facts = execution["facts"]
        by_id = {f["id"]: f for f in facts}
        if len(by_id) != len(facts):
            raise ValueError("DUPLICATE_FACT")
        allowed = [f for f in facts if f["entity"] == query["entity"] and f["metric"] == query["metric"]
                   and f["period"] == query["period"] and f["unit"] == query["unit"]
                   and f["status"] == "current" and f["visibility"] == "public"]
        if len({f["value"] for f in allowed}) > 1:
            raise ValueError("CONFLICT")
        visiting = set()
        complete = set()

        def supported(fid):
            if fid in visiting:
                raise ValueError("DEPENDENCY_CYCLE")
            if fid in complete:
                return True
            fact = by_id.get(fid)
            if fact is None:
                return False
            if fact["status"] != "current" or fact["visibility"] != "public":
                return False
            if fact["entity"] != query["entity"] or fact["period"] != query["period"]:
                raise ValueError("DEPENDENCY_SCOPE")
            if fact["provenance"] not in execution["trusted_provenance"]:
                raise ValueError("UNTRUSTED_PROVENANCE")
            if not isinstance(fact["value"], str) or re.fullmatch(r"-?[0-9]+", fact["value"]) is None:
                raise ValueError("NONINTEGER_FACT")
            if not -(2**127) <= int(fact["value"]) < 2**127:
                raise ValueError("INTEGER_RANGE")
            visiting.add(fid)
            deps = fact.get("dependencies", [])
            if not all(supported(dep) for dep in deps):
                visiting.remove(fid)
                return False
            if "operation" in fact:
                if fact["operation"] != "PERCENT_DIV" or len(deps) != 2 or fact["unit"] != "percent":
                    raise ValueError("UNKNOWN_DERIVATION")
                numerator, denominator = [by_id[d] for d in deps]
                if numerator["unit"] != denominator["unit"] or numerator["unit"] not in {"USD", "EUR"}:
                    raise ValueError("DERIVATION_UNIT")
                divisor = int(denominator["value"])
                if divisor == 0:
                    raise ValueError("ZERO_DENOMINATOR")
                # S1 wire semantics use checked i128 intermediates, not Decimal
                # context precision or an unbounded Python arithmetic extension.
                scaled = int(numerator["value"]) * 100
                if not -(2**127) <= scaled < 2**127:
                    raise ValueError("INTEGER_INTERMEDIATE_RANGE")
                if scaled % divisor != 0 or scaled // divisor != int(fact["value"]):
                    raise ValueError("DERIVATION_VALUE")
            elif deps:
                raise ValueError("UNDEFINED_DEPENDENCY")
            visiting.remove(fid)
            complete.add(fid)
            return True

        accepted = sorted({f["id"] for f in allowed if supported(f["id"])})
        if not accepted:
            return {"state": "NO_VERIFIED_ANSWER", "fact_ids": []}
        return {"state": "FULL_VERIFIED_ANSWER", "fact_ids": accepted}
    except (ValueError, KeyError, TypeError, ArithmeticError):
        return {"state": "QUARANTINE", "fact_ids": []}
