"""Revision reference CNL, deliberately narrower than unrestricted natural language."""
import re
import unicodedata
from uir_common.contracts import RuntimeContract

EN = re.compile(r"verify (?P<entity>[A-Z][A-Z0-9._-]{0,15}) (?P<metric>revenue|net_income|operating_income) (?P<year>(?:19|20)\d{2})", re.ASCII)
KO = re.compile(r"(?P<entity>[A-Z][A-Z0-9._-]{0,15})의 (?P<year>(?:19|20)\d{2})년 (?P<metric>매출|순이익|영업이익) 검증")
METRICS = {"매출": "revenue", "순이익": "net_income", "영업이익": "operating_income"}


def compile_cnl(text, *, policy_snapshot, evidence_snapshot):
    text = unicodedata.normalize("NFC", text).strip()
    matched = EN.fullmatch(text) or KO.fullmatch(text)
    if matched is None:
        raise ValueError("CLARIFICATION: outside reference CNL grammar")
    slots = matched.groupdict()
    return RuntimeContract(slots["entity"], METRICS.get(slots["metric"], slots["metric"]), slots["year"], policy_snapshot, evidence_snapshot)
