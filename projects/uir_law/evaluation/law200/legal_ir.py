"""Typed legal UIR construction and deterministic entity binding."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any

US_CITATION_RE = re.compile(r"(?<!\d)(\d{1,3})\s+U\.?\s*S\.?\s+(\d{1,4})(?!\d)", re.IGNORECASE)
KR_CASE_NUMBER_RE = re.compile(r"(?<!\d)(\d{4}[가-힣]{1,5}\d{1,7})(?!\d)")
ENTITY_PATTERN = r"(?:\d{1,3}\s+U\.?\s*S\.?\s+\d{1,4}|\d{4}[가-힣]{1,5}\d{1,7})"
CASE_BEFORE_CITATION_RE = re.compile(
    r"(?:^|[:：])\s*(?:please\s+)?(?:summarize|explain|analy[sz]e|describe)?\s*"
    rf"(?P<name>[A-Z가-힣(][^\n]{{1,160}}?)\s*\(\s*{ENTITY_PATTERN}\s*\)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LegalUIR:
    schema: str
    domain: str
    intent: str
    entity_type: str
    citation: str | None
    claimed_case_name: str | None
    language_hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BindingDecision:
    status: str
    reason: str
    citation: str | None
    source_id: str | None
    canonical_case_name: str | None
    registry_record: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("registry_record", None)
        return value


def canonicalize_citation(volume: str | int, page: str | int) -> str:
    return f"{int(volume)} U.S. {int(page)}"


def extract_citation(text: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", text)
    match = US_CITATION_RE.search(normalized)
    if match:
        return canonicalize_citation(match.group(1), match.group(2))
    korean = KR_CASE_NUMBER_RE.search(normalized)
    return korean.group(1) if korean else None


def detect_language(text: str) -> str:
    return "ko" if re.search(r"[가-힣]", text) else "en"


def extract_claimed_case_name(text: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", text).strip()
    match = CASE_BEFORE_CITATION_RE.search(normalized)
    if not match:
        return None
    name = match.group("name").strip(" \t\n,.:;\"'“”‘’")
    lowered = name.lower()
    prefixes = (
        "판례 ", "사건 ", "decision in ", "the decision in ", "case ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    return name or None


def compile_legal_uir(text: str) -> LegalUIR:
    lowered = text.lower()
    intent = "SUMMARIZE" if any(token in lowered for token in ("summar", "explain", "describe", "요약", "설명", "핵심")) else "RETRIEVE"
    return LegalUIR(
        schema="law-uir/1.0",
        domain="LAW",
        intent=intent,
        entity_type="CASE",
        citation=extract_citation(text),
        claimed_case_name=extract_claimed_case_name(text),
        language_hint=detect_language(text),
    )


def normalize_case_name(value: str) -> str:
    # NFKD decomposes Hangul syllables into Jamo outside the [가-힣] token
    # range used below. NFKC normalizes presentation variants while preserving
    # searchable Korean syllables.
    value = unicodedata.normalize("NFKC", value).lower()
    value = value.replace(" versus ", " v ").replace(" vs. ", " v ").replace(" v. ", " v ")
    tokens = re.findall(r"[a-z0-9가-힣]+", value)
    ignored = {"the", "of", "and", "in", "re", "ex", "rel", "v", "사건", "판결"}
    return " ".join(token for token in tokens if token not in ignored)


def case_names_match(claimed: str, canonical: str) -> bool:
    left, right = normalize_case_name(claimed), normalize_case_name(canonical)
    if not left or not right:
        return False
    if left == right or left in right or right in left:
        return True
    left_tokens, right_tokens = set(left.split()), set(right.split())
    overlap = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    return overlap >= 0.75 or SequenceMatcher(None, left, right).ratio() >= 0.86


def registry_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(record["citation_canonical"]): record
        for record in records
        if int(record.get("lookup_status", 0)) == 200
    }


def verify_entity(uir: LegalUIR, records: list[dict[str, Any]]) -> BindingDecision:
    if not uir.citation:
        return BindingDecision("REJECT", "CITATION_PARSE_FAILED", None, None, None, None)
    record = registry_index(records).get(uir.citation)
    if record is None:
        return BindingDecision("REJECT", "CITATION_NOT_FOUND", uir.citation, None, None, None)
    case_name = str(record.get("case_name", ""))
    if uir.claimed_case_name and not case_names_match(uir.claimed_case_name, case_name):
        return BindingDecision(
            "REJECT", "ENTITY_BINDING_MISMATCH", uir.citation,
            str(record.get("source_id")), case_name, record,
        )
    return BindingDecision(
        "VERIFIED", "AUTHORITATIVE_BINDING_OK", uir.citation,
        str(record.get("source_id")), case_name, record,
    )
