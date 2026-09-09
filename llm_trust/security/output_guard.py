"""Output Guard: Schema Validation, Evidence Citation Check, and Data Loss Prevention (DLP)."""
from __future__ import annotations

import json
import re
import math
from .quantity import parse_quantity
from jsonschema import Draft202012Validator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..evidence.provenance import EvidenceRecord


class OutputValidationStatus(str, Enum):
    VALID = "VALID"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    UNSUPPORTED_CLAIMS = "UNSUPPORTED_CLAIMS"
    DLP_VIOLATION = "DLP_VIOLATION"
    UNAUTHORIZED_CODE_EMISSION = "UNAUTHORIZED_CODE_EMISSION"


@dataclass(frozen=True)
class OutputGuardVerdict:
    status: OutputValidationStatus
    is_safe: bool
    sanitized_output: str
    filtered_claims: List[str] = field(default_factory=list)
    dlp_findings: List[str] = field(default_factory=list)
    rejection_reason: str = ""


class OutputGuard:
    """Validates model-generated output at egress before downstream consumption."""

    # Sensitive patterns that must never leak to output (DLP)
    DLP_PATTERNS = {
        "API_KEY": re.compile(r"(?i)(api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?|sk-[a-zA-Z0-9]{20,})"),
        "PRIVATE_KEY": re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA|PRIVATE) KEY-----"),
        "CREDENTIAL": re.compile(r"(?i)(password|passwd|secret)\s*[:=]\s*['\"][^'\"]{4,}['\"]"),
        "INTERNAL_SSN_RRN": re.compile(r"\b\d{6}-[1-4]\d{6}\b"),
        "SYSTEM_PROMPT_LEAK": re.compile(r"(?i)(you are an ai assistant designed by|system instruction: you must|system prompt dump|you are a strictly constrained verification and reporting engine)"),
        "UNVERIFIED_INSOLVENCY_CLAIM": re.compile(r"(?i)(부도\s*처리|채권단\s*청산|완전\s*파산|파산하여|자본잠식|매출\s*제로|zero\s+revenue|declared\s+insolvency|catastrophic\s+bankruptcy)"),
    }

    # Code / command injection patterns
    CODE_EXECUTION_PATTERNS = [
        re.compile(r"(?i)(os\.system|subprocess\.Popen|eval\(|exec\(|__import__|rm\s+-rf|DROP\s+TABLE)"),
    ]

    def validate(
        self,
        raw_output: str,
        expected_schema_id: Optional[str] = None,
        admissible_evidence_ids: Optional[Set[str]] = None,
        strict_citations: bool = True,
        block_executable_code: bool = True,
        confidential_tokens: Optional[Set[str]] = None,
        evidence_claims: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> OutputGuardVerdict:
        """Enforces schema, DLP, and factual citation constraints on raw model outputs."""
        stripped = raw_output.strip()
        dlp_findings: List[str] = []

        # 1. DLP Scan
        for leak_type, pattern in self.DLP_PATTERNS.items():
            if pattern.search(raw_output):
                dlp_findings.append(leak_type)

        if confidential_tokens:
            for token in confidential_tokens:
                if token and token in raw_output:
                    dlp_findings.append("PROTECTED_SECRET")

        if dlp_findings:
            return OutputGuardVerdict(
                status=OutputValidationStatus.DLP_VIOLATION,
                is_safe=False,
                sanitized_output="[RESPONSE_SUPPRESSED_BY_DLP_POLICY]",
                dlp_findings=dlp_findings,
                rejection_reason=f"Output contained sensitive data matching policy violation: {dlp_findings}",
            )

        # 2. Dangerous Code / Command Generation Scan
        if block_executable_code:
            for pattern in self.CODE_EXECUTION_PATTERNS:
                if pattern.search(raw_output):
                    return OutputGuardVerdict(
                        status=OutputValidationStatus.UNAUTHORIZED_CODE_EMISSION,
                        is_safe=False,
                        sanitized_output="[UNAUTHORIZED_EXECUTABLE_CODE_BLOCKED]",
                        rejection_reason="Generated output contains unauthorized executable system commands.",
                    )

        # 3. Whole-Output Schema & Strict JSON Structure Check
        parsed_json: Optional[Dict[str, Any]] = None
        if expected_schema_id and expected_schema_id != "unstructured_text":
            target_str = stripped

            # Must begin and end with outer braces strictly
            if not (target_str.startswith("{") and target_str.endswith("}")):
                return OutputGuardVerdict(
                    status=OutputValidationStatus.SCHEMA_VIOLATION,
                    is_safe=False,
                    sanitized_output="[SCHEMA_VIOLATION_REJECTED]",
                    rejection_reason="Model output contains non-JSON text outside outer JSON braces.",
                )

            # Strict single JSON object decoding
            try:
                decoder = json.JSONDecoder(object_pairs_hook=_unique_object, parse_constant=_reject_constant, parse_float=_finite_float)
                parsed_json, end_idx = decoder.raw_decode(target_str)
                if end_idx != len(target_str):
                    return OutputGuardVerdict(
                        status=OutputValidationStatus.SCHEMA_VIOLATION,
                        is_safe=False,
                        sanitized_output="[SCHEMA_VIOLATION_REJECTED]",
                        rejection_reason=f"Trailing text or multiple objects detected after JSON object (idx {end_idx}/{len(target_str)}).",
                    )
            except Exception as e:
                return OutputGuardVerdict(
                    status=OutputValidationStatus.SCHEMA_VIOLATION,
                    is_safe=False,
                    sanitized_output="[SCHEMA_VIOLATION_REJECTED]",
                    rejection_reason=f"Model output failed schema validation: Not valid JSON ({e}).",
                )

            schema = {"financial_summary_v3_2": FINANCIAL_SUMMARY_SCHEMA, "financial_summary_v2": LEGACY_SUMMARY_SCHEMA, "financial_summary": FINANCIAL_SUMMARY_SCHEMA}.get(expected_schema_id)
            errors = list(Draft202012Validator(schema).iter_errors(parsed_json)) if schema else ["Unknown schema"]
            if errors:
                return OutputGuardVerdict(
                    status=OutputValidationStatus.SCHEMA_VIOLATION, is_safe=False,
                    sanitized_output="[SCHEMA_VIOLATION_REJECTED]",
                    rejection_reason="Schema violation (including unexpected fields): " + str(errors[0]),
                )
            # Scan decoded strings too: JSON escapes must not bypass command/DLP checks.
            decoded = json.dumps(parsed_json, ensure_ascii=False)
            if decoded != raw_output:
                scan = self.validate(decoded, confidential_tokens=confidential_tokens,
                                     block_executable_code=block_executable_code, strict_citations=False)
                if not scan.is_safe:
                    return scan

        # 4. Citation and Evidence Binding Check
        if strict_citations and admissible_evidence_ids is not None:
            cited_ids = set(re.findall(r"\[(?:source|ref|evidence):\s*([a-zA-Z0-9_\-:]+)\]", raw_output, re.I))
            if parsed_json and "citations" in parsed_json and isinstance(parsed_json["citations"], list):
                for c in parsed_json["citations"]:
                    if isinstance(c, str):
                        cited_ids.add(c)
                    elif isinstance(c, dict) and "source_id" in c:
                        cited_ids.add(c["source_id"])

            fabricated = cited_ids - admissible_evidence_ids
            if fabricated:
                return OutputGuardVerdict(
                    status=OutputValidationStatus.UNSUPPORTED_CLAIMS,
                    is_safe=False,
                    sanitized_output="[UNSUPPORTED_CLAIMS_FILTERED]",
                    filtered_claims=list(fabricated),
                    rejection_reason=f"Output cited unsupported or fictitious evidence sources: {fabricated}",
                )

        if parsed_json and evidence_claims is not None:
            cited = parsed_json.get("citations", [])
            matches = [evidence_claims[c] for c in cited if c in evidence_claims]
            def supports(claim):
                expected = parse_quantity(claim.get("value"), claim.get("currency", ""), claim.get("unit", ""))
                actual = parse_quantity(parsed_json.get("value"), parsed_json.get("currency", expected[1] if expected else ""), parsed_json.get("unit", ""))
                return expected is not None and actual == expected and all(
                    str(parsed_json.get(k, "")).casefold() == str(v).casefold()
                    for k, v in claim.items() if k not in {"value", "currency", "unit"})
            if not matches or not any(supports(claim) for claim in matches):
                return OutputGuardVerdict(
                    status=OutputValidationStatus.UNSUPPORTED_CLAIMS, is_safe=False,
                    sanitized_output="[UNSUPPORTED_CLAIMS_FILTERED]",
                    rejection_reason="Cited evidence does not support the claim/value.",
                )

        # 5. Canonical Egress Generation (Never return raw un-sanitized model string)
        if parsed_json is not None:
            canonical_output = json.dumps(parsed_json, indent=2, ensure_ascii=False)
        else:
            canonical_output = stripped

        return OutputGuardVerdict(
            status=OutputValidationStatus.VALID,
            is_safe=True,
            sanitized_output=canonical_output,
        )


FINANCIAL_SUMMARY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object", "additionalProperties": False,
    "required": ["entity", "metric", "value", "citations"],
    "properties": {
        "entity": {"type": "string", "minLength": 1},
        "metric": {"type": "string", "minLength": 1},
        "value": {"type": ["string", "number"]},
        "currency": {"type": "string"}, "unit": {"type": "string"},
        "fiscal_period": {"type": "string"}, "fiscal_year": {"type": ["integer", "string"]},
        "summary": {"type": "string"}, "status": {"type": "string"},
        "citations": {"type": "array", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
    },
}


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value):
    raise ValueError("Non-finite JSON number")

LEGACY_SUMMARY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
    "additionalProperties": False, "required": ["entity", "summary", "claims", "citations"],
    "properties": {"entity":{"type":"string"}, "summary":{"type":"string"},
                   "claims":{"type":"array","items":{"type":"string"}},
                   "citations":{"type":"array","items":{"type":"string"}}},
}


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite JSON number")
    return number
