"""Two raw-only CNL frontends and an assisted API; no evaluation labels."""
import re
import unicodedata
from uir_common.contracts import canonical_digest, reject_gold
from uir_common.representation import TypedRequest
from projects.uir_base.scripts.next_frontend import expression

EN = re.compile(r"verify (?P<entity>[A-Z][A-Z0-9._-]{0,15}) (?P<attribute>revenue|net_income|operating_income) (?P<period>(?:19|20)\d{2})")
KO = re.compile(r"(?P<entity>[A-Z][A-Z0-9._-]{0,15})의 (?P<period>(?:19|20)\d{2})년 (?P<attribute>매출|순이익|영업이익) 검증")
ATTRIBUTES = {"매출": "revenue", "순이익": "net_income", "영업이익": "operating_income"}


def normalize_predicate(node):
    if node is None: return None
    op = node.get("op")
    if op == "NOT":
        value = normalize_predicate(node["arg"])
        return value["arg"] if value.get("op") == "NOT" else {"op": op, "arg": value}
    if op in {"AND", "OR"}:
        children = []
        for child in node["args"]:
            child = normalize_predicate(child)
            children.extend(child["args"] if child.get("op") == op else [child])
        return {"op": op, "args": sorted(children, key=canonical_digest)}
    return dict(node)


def parse_raw(text):
    """Dedicated CNL parser. Unsupported requests clarify at the caller."""
    text = unicodedata.normalize("NFC", text).strip()
    parts = re.split(r"\s+(only if|unless|if|조건:)\s*", text, maxsplit=1)
    base = parts[0]
    unit_match = re.search(r"\s+(?:in|단위) (USD|KRW|EUR|percent|1)$", base)
    unit = unit_match.group(1) if unit_match else None
    if unit_match: base = base[:unit_match.start()]
    found = EN.fullmatch(base) or KO.fullmatch(base)
    if found is None: raise ValueError("CLARIFICATION: UNSUPPORTED_CNL")
    parsed = found.groupdict()
    parsed["attribute"] = ATTRIBUTES.get(parsed["attribute"], parsed["attribute"])
    predicate = expression(parts[2]) if len(parts) == 3 else None
    if len(parts) == 3 and parts[1] == "unless":
        predicate = {"op": "NOT", "arg": predicate}
    return {**parsed, "unit": unit, "predicate": normalize_predicate(predicate)}


def compile_shared(text, authority, source, *, assisted=None, action="read"):
    reject_gold(assisted)
    slots = assisted if assisted is not None else parse_raw(text)
    return TypedRequest(**slots, action=action, policy_snapshot=authority["version"], evidence_snapshot=source["version"])


def specialized_plan(text, authority, source, *, assisted=None, action="read"):
    """Equivalent structured pipeline, explicitly no shared-IR serialization.

The lexical parser, policy and support guard are shared to avoid making the
control weaker. It still has a task-specific intermediate dict, as real systems
do; only the cross-backend public typed UIR artifact is removed.
"""
    reject_gold(assisted)
    slots = assisted if assisted is not None else parse_raw(text)
    return {**slots, "action": action, "policy_snapshot": authority["version"], "evidence_snapshot": source["version"],
            "version": "uir-representation-vNext-1"}
