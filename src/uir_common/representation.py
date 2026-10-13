"""Domain-neutral vNext policy/evidence/output contract. No scoring dependencies.

Trusted catalog/authority are inputs. Soundness is relative to those inputs, not
real-world truth, OS isolation, unrestricted language, or model completeness.
"""
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import json
from jsonschema import Draft202012Validator
from .contracts import FIELDS, canonical_digest, derive, NumericFact, reject_gold, transition

CLAIM_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": list(FIELDS),
    "properties": {k: {"type": "string", "minLength": 1 if k in {"claim_type", "entity_id", "attribute", "value", "provenance"} else 0} for k in FIELDS},
}
FULL_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["contract_digest", "claims"],
               "properties": {"contract_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                              "claims": {"type": "array", "maxItems": 32, "items": CLAIM_SCHEMA}}}
REFERENCE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["contract_digest", "fact_ids"],
                    "properties": {"contract_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                   "fact_ids": {"type": "array", "maxItems": 32, "uniqueItems": True, "items": {"type": "string", "minLength": 1}}}}


@dataclass(frozen=True)
class TypedRequest:
    entity: str
    attribute: str
    period: str
    unit: str | None
    predicate: dict | None
    action: str
    policy_snapshot: str
    evidence_snapshot: str
    version: str = "uir-representation-vNext-1"

    @property
    def digest(self):
        return canonical_digest(asdict(self))

    def plan(self):
        return asdict(self)

    def artifact(self, metadata=None):
        return {"metadata": metadata or {}, "semantics": {k: getattr(self, k) for k in ("entity", "attribute", "period", "unit", "predicate")},
                "policy_constraints": {"snapshot": self.policy_snapshot, "action": self.action},
                "execution_contract": {"evidence_snapshot": self.evidence_snapshot, "version": self.version},
                "output_contract": {"fields": list(FIELDS), "accepted_renderer": "deterministic_bound_claims"},
                "semantic_digest": self.digest}

    @classmethod
    def from_artifact(cls, artifact):
        reject_gold(artifact)
        if set(artifact) != {"metadata", "semantics", "policy_constraints", "execution_contract", "output_contract", "semantic_digest"}:
            raise ValueError("INVALID_ARTIFACT_SECTIONS")
        if artifact["output_contract"] != {"fields": list(FIELDS), "accepted_renderer": "deterministic_bound_claims"}:
            raise ValueError("OUTPUT_CONTRACT_MISMATCH")
        policy, execution = artifact["policy_constraints"], artifact["execution_contract"]
        request = cls(**artifact["semantics"], action=policy["action"], policy_snapshot=policy["snapshot"],
                      evidence_snapshot=execution["evidence_snapshot"], version=execution["version"])
        if request.digest != artifact["semantic_digest"]:
            raise ValueError("ARTIFACT_SEMANTIC_DIGEST_MISMATCH")
        return request


def claim_key(claim):
    return tuple(claim[k] for k in FIELDS)


def valid_claim(claim):
    Draft202012Validator(CLAIM_SCHEMA).validate(claim)
    if claim["claim_type"] in {"numeric_claim", "derived_claim"}:
        if not claim["unit"] or not claim["period"] or claim["unit"] == "unknown" or claim["period"] == "unknown":
            raise ValueError("UNKNOWN_OR_MISSING_UNIT_PERIOD")
        try:
            if not Decimal(claim["value"]).is_finite():
                raise ValueError("NONFINITE_NUMERIC_VALUE")
        except InvalidOperation as exc:
            raise ValueError("NONNUMERIC_VALUE") from exc


def catalog(claims, version, *, dependencies=None, derivations=None):
    reject_gold(claims)
    result = {}; seen = set()
    for claim in claims:
        valid_claim(claim); key = claim_key(claim)
        if key in seen:
            raise ValueError("DUPLICATE_CATALOG_CLAIM")
        seen.add(key)
        result["F-" + canonical_digest({"snapshot": version, "claim": claim})[:24]] = dict(claim)
    return {"version": version, "facts": result, "dependencies": dependencies or {}, "derivations": derivations or {}}


def predicate_value(node, context):
    if node is None:
        return True
    if node.get("op") == "NOT":
        return not predicate_value(node["arg"], context)
    if node.get("op") in {"AND", "OR"}:
        values = [predicate_value(n, context) for n in node["args"]]
        return all(values) if node["op"] == "AND" else any(values)
    if node["field"] not in context:
        raise ValueError("UNKNOWN_CONDITION_VALUE")
    left, right = context[node["field"]], node["value"]
    if node["type"] == "DECIMAL":
        left, right = Decimal(str(left)), Decimal(str(right))
        if not left.is_finite() or not right.is_finite():
            raise ValueError("NONFINITE_CONDITION")
    elif type(left) is not bool or type(right) is not bool:
        raise ValueError("CONDITION_TYPE_MISMATCH")
    return {"==": lambda: left == right, "!=": lambda: left != right, ">": lambda: left > right,
            "<": lambda: left < right, ">=": lambda: left >= right, "<=": lambda: left <= right}[node["op"]]()


def eligible_facts(plan, source):
    """Selection uses only typed request and authoritative catalog, never gold."""
    reject_gold(plan); reject_gold(source)
    selected = {fid: claim for fid, claim in source["facts"].items()
            if claim["entity_id"] == plan["entity"] and claim["attribute"] == plan["attribute"]
            and claim["period"] == plan["period"] and (plan["unit"] is None or claim["unit"] == plan["unit"])}
    visiting = set(); visited = set()
    def closure(ref):
        if ref in visiting: raise ValueError("DEPENDENCY_CYCLE")
        if ref in visited: return
        visiting.add(ref)
        claim = source["facts"][ref]
        for dep in source.get("dependencies", {}).get(ref, []):
            if dep not in source["facts"]: raise ValueError("UNKNOWN_DEPENDENCY")
            operand = source["facts"][dep]
            if operand["entity_id"] != plan["entity"] or operand["period"] != plan["period"]:
                raise ValueError("DEPENDENCY_AUTHORITY_SCOPE_MISMATCH")
            selected[dep] = operand
            closure(dep)
        if claim["claim_type"] == "derived_claim":
            if ref not in source.get("derivations", {}) or not source.get("dependencies", {}).get(ref):
                raise ValueError("DERIVED_DEFINITION_MISSING")
            facts = {d: NumericFact(c["value"], c["unit"], c["period"], c["provenance"]) for d, c in selected.items() if d != ref}
            result = derive(source["derivations"][ref], facts)
            if (set(result["operand_ids"]) != set(source["dependencies"][ref]) or
                    Decimal(result["value"]) != Decimal(claim["value"]) or result["unit"] != claim["unit"]):
                raise ValueError("DERIVED_SUPPORT_MISMATCH")
        visiting.remove(ref); visited.add(ref)
    for ref in list(selected): closure(ref)
    return selected


def admissible(plan, source, authority, context):
    if plan["policy_snapshot"] != authority["version"] or plan["evidence_snapshot"] != source["version"]:
        return "QUARANTINE"
    try:
        if not predicate_value(plan["predicate"], context):
            return "DENY"
    except (ValueError, KeyError, TypeError):
        return "CLARIFICATION"
    policy = authority["decision"]
    state = transition(policy=policy, action=plan["action"], approved=authority.get("approved", False))
    if state.value != "NO_VERIFIED_ANSWER":
        return state.value
    # Conflicting authoritative assertions require quarantine, not model choice.
    try:
        selected = eligible_facts(plan, source)
    except (ValueError, KeyError, InvalidOperation):
        return "QUARANTINE"
    grouped = {}
    for claim in selected.values():
        key = (claim["claim_type"], claim["entity_id"], claim["attribute"], claim["period"], claim["unit"])
        if key in grouped and grouped[key] != claim["value"]:
            return "QUARANTINE"
        grouped[key] = claim["value"]
    return "ADMISSIBLE"


def parse_candidate(text, mode):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj: raise ValueError("DUPLICATE_JSON_KEY")
            obj[key] = value
        return obj
    value = json.loads(text, object_pairs_hook=unique)
    Draft202012Validator(REFERENCE_SCHEMA if mode == "reference" else FULL_SCHEMA).validate(value)
    return value


def accept(plan, source, authority, context, candidate, *, mode="reference", partial=True, identity=None):
    """Common guard for shared-IR and equivalent specialized pipelines."""
    digest = identity or canonical_digest(plan)
    gate = admissible(plan, source, authority, context)
    required = eligible_facts(plan, source) if gate == "ADMISSIBLE" else {}
    errors = []; selected = {}; native = candidate
    if gate == "ADMISSIBLE":
        try:
            parsed = parse_candidate(candidate, mode)
            if parsed["contract_digest"] != digest:
                raise ValueError("REQUEST_RESPONSE_IDENTITY_MISMATCH")
            if mode == "reference":
                for ref in parsed["fact_ids"]:
                    if ref in required:
                        selected[ref] = required[ref]
                    else:
                        errors.append("UNKNOWN_OR_OUT_OF_SCOPE_REFERENCE")
            else:
                seen = set()
                for claim in parsed["claims"]:
                    valid_claim(claim); key = claim_key(claim)
                    if key in seen: raise ValueError("DUPLICATE_CANDIDATE_CLAIM")
                    seen.add(key)
                    refs = [r for r, trusted in required.items() if claim_key(trusted) == key]
                    if refs: selected[refs[0]] = claim
                    else: errors.append("EXACT_SUPPORT_MISMATCH")
        except Exception as exc:
            selected = {}
            errors.append(type(exc).__name__ + ":" + str(exc).splitlines()[0])
        # A derived claim is not independently valid if its operand closure is absent.
        changed = True
        while changed:
            changed = False
            for ref in list(selected):
                dependencies = source.get("dependencies", {}).get(ref, [])
                if selected[ref]["claim_type"] == "derived_claim" and not dependencies:
                    errors.append("DERIVED_FACT_DEPENDENCIES_MISSING"); del selected[ref]; changed = True
                elif any(d not in selected for d in dependencies):
                    errors.append("DEPENDENCY_CLOSURE_MISSING"); del selected[ref]; changed = True
        state = transition(required_count=len(required), selected_count=len(selected), partial=partial).value
    else:
        state = gate
    if state not in {"FULL_VERIFIED_ANSWER", "PARTIAL_VERIFIED_ANSWER"}:
        selected = {}
    claims = list(selected.values())
    # No unchecked model prose or provenance is forwarded to the user.
    rendered = json.dumps({"state": state, "claims": claims, "contract_digest": digest}, ensure_ascii=False, sort_keys=True)
    return {"state": state, "authorization": gate, "eligible_fact_ids": sorted(required), "accepted_fact_ids": sorted(selected),
            "accepted_claims": claims, "accepted_rendered_text": rendered, "native_candidate": native,
            "candidate_errors": errors, "contract_digest": digest,
            "full_output_scope": "DETERMINISTIC_BOUND_CLAIM_RENDERER", "native_prose_assessment": "NOT_MEASURED"}


def deterministic_candidate(plan, source, digest):
    return json.dumps({"contract_digest": digest, "fact_ids": sorted(eligible_facts(plan, source))})
