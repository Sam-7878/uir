"""Credential-safe client for 국가법령정보 공동활용 판례 APIs."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evaluation.uir_law.law200.common import PACKAGE_ROOT, REPO_ROOT, canonical_json, sha256_bytes, sha256_text, utc_now, write_json

SEARCH_ENDPOINT = "https://www.law.go.kr/DRF/lawSearch.do"
SERVICE_ENDPOINT = "https://www.law.go.kr/DRF/lawService.do"
KR_DATA_DIR = PACKAGE_ROOT / "data" / "kr"
KR_RESPONSE_DIR = KR_DATA_DIR / "source_responses"
DEFAULT_KEY_FILE = REPO_ROOT / "local_security" / "open.law.go.kr.txt"


class LawGoKrError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchSnapshot:
    body: dict[str, Any]
    raw_path: Path
    raw_sha256: str
    retrieved_at: str
    safe_parameters: dict[str, str]


class LawGoKrClient:
    def __init__(self, key_file: Path = DEFAULT_KEY_FILE, timeout: int = 120):
        self.credential = os.environ.get("LAW_GO_KR_OC")
        if not self.credential and key_file.exists():
            self.credential = key_file.read_text(encoding="utf-8-sig").strip()
        if not self.credential:
            raise LawGoKrError("LAW_GO_KR_OC or local_security/open.law.go.kr.txt is required")
        self.timeout = timeout

    def search(self, label: str, **parameters: str | int) -> SearchSnapshot:
        safe = {key: str(value) for key, value in parameters.items()}
        request_parameters = {"OC": self.credential, "target": "prec", "type": "JSON", **safe}
        query = urllib.parse.urlencode(request_parameters)
        request = urllib.request.Request(f"{SEARCH_ENDPOINT}?{query}", headers={"User-Agent": "UIR-LAW-KR/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                status = response.status
        except urllib.error.HTTPError as exc:
            raise LawGoKrError(f"law.go.kr HTTP {exc.code}; request URL suppressed") from None
        except urllib.error.URLError as exc:
            raise LawGoKrError(f"law.go.kr transport failure: {type(exc.reason).__name__}; request URL suppressed") from None
        if status != 200:
            raise LawGoKrError(f"law.go.kr unexpected HTTP {status}")
        try:
            body = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise LawGoKrError("law.go.kr returned invalid JSON") from exc
        if not isinstance(body, dict) or not isinstance(body.get("PrecSearch"), dict):
            raise LawGoKrError("law.go.kr response lacks PrecSearch")
        # The official response repeats OC inside per-record detail links. Keep
        # the authoritative JSON content, but remove the credential before any
        # byte reaches the repository or a result artifact.
        body = redact_credential(body, self.credential)
        persisted_raw = canonical_json(body).encode("utf-8")
        digest = sha256_bytes(persisted_raw)
        retrieved_at = utc_now()
        KR_RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = KR_RESPONSE_DIR / f"{label}_{digest[:16]}.json"
        raw_path.write_bytes(persisted_raw)
        write_json(raw_path.with_suffix(".metadata.json"), {
            "endpoint": SEARCH_ENDPOINT,
            "safe_parameters": safe,
            "credential_parameter_omitted": "OC",
            "credential_redacted_from_response_links": True,
            "http_status": status,
            "retrieved_at": retrieved_at,
            "raw_sha256": digest,
        })
        return SearchSnapshot(body, raw_path, digest, retrieved_at, safe)


def redact_credential(value: Any, credential: str) -> Any:
    """Recursively redact OC from decoded API content before persistence."""
    if isinstance(value, dict):
        return {key: redact_credential(item, credential) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_credential(item, credential) for item in value]
    if isinstance(value, str):
        return value.replace(credential, "[REDACTED_OC]")
    return value


def result_rows(snapshot: SearchSnapshot) -> list[dict[str, Any]]:
    value = snapshot.body["PrecSearch"].get("prec", [])
    if isinstance(value, dict):
        return [value]
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def exact_case_number(row: dict[str, Any]) -> str:
    compact = re.sub(r"[^0-9가-힣]", "", str(row.get("사건번호") or ""))
    match = re.search(r"\d{4}[가-힣]{1,5}\d{1,7}", compact)
    return match.group(0) if match else compact


def valid_record(row: dict[str, Any], snapshot: SearchSnapshot) -> dict[str, Any]:
    case_number = exact_case_number(row)
    serial = row.get("판례일련번호") or row.get("판례정보일련번호") or row.get("id")
    entry_hash = sha256_text(canonical_json(row))
    return {
        "jurisdiction": "KR",
        "citation_raw": case_number,
        "citation_canonical": case_number,
        "case_name": str(row.get("사건명") or ""),
        "court": str(row.get("법원명") or ("대법원" if str(row.get("사건번호") or "").startswith("대법원-") else "")),
        "date_filed": str(row.get("선고일자") or ""),
        "decision_type": str(row.get("판결유형") or ""),
        "law_go_kr_prec_id": serial,
        "lookup_status": 200,
        "http_status": 200,
        "verification_outcome": "FOUND",
        "source_uri": f"https://www.law.go.kr/precInfoP.do?precSeq={serial}",
        "retrieved_at": snapshot.retrieved_at,
        "response_sha256": entry_hash,
        "raw_batch_sha256": snapshot.raw_sha256,
        "raw_response_file": str(snapshot.raw_path.relative_to(PACKAGE_ROOT)),
        "source_id": f"lawgo:prec:{serial}",
    }


def not_found_record(case_number: str, mutation: dict[str, Any], snapshot: SearchSnapshot, observed_numbers: list[str]) -> dict[str, Any]:
    evidence = {
        "candidate_case_number": case_number,
        "observed_exact_case_numbers": sorted(observed_numbers),
        "raw_batch_sha256": snapshot.raw_sha256,
    }
    return {
        "jurisdiction": "KR",
        "citation_raw": case_number,
        "citation_canonical": case_number,
        "case_name": "",
        "court": "",
        "date_filed": "",
        "decision_type": "",
        "law_go_kr_prec_id": None,
        "lookup_status": 404,
        "http_status": 200,
        "verification_outcome": "NOT_FOUND_EXACT_CASE_NUMBER",
        "result_count_for_exact_case_number": 0,
        "source_uri": SEARCH_ENDPOINT,
        "retrieved_at": snapshot.retrieved_at,
        "response_sha256": sha256_text(canonical_json(evidence)),
        "raw_batch_sha256": snapshot.raw_sha256,
        "raw_response_file": str(snapshot.raw_path.relative_to(PACKAGE_ROOT)),
        "source_id": f"lawgo:case-number:{sha256_text(case_number)[:16]}",
        "mutation": mutation,
    }
