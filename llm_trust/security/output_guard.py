"""Output Guard: Schema Validation, Evidence Citation Check, and Data Loss Prevention (DLP)."""
from __future__ import annotations

import json
import re
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
        "SYSTEM_PROMPT_LEAK": re.compile(r"(?i)(you are an ai assistant designed by|system instruction: you must|system prompt dump)"),
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
    ) -> OutputGuardVerdict:
        """Enforces schema, DLP, and factual citation constraints on raw model outputs."""
        dlp_findings: List[str] = []

        # 1. DLP Scan
        for leak_type, pattern in self.DLP_PATTERNS.items():
            if pattern.search(raw_output):
                dlp_findings.append(leak_type)

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

        # 3. Schema & JSON Structure Check (if schema specified)
        parsed_json: Optional[Dict[str, Any]] = None
        if expected_schema_id:
            try:
                # Extract JSON block if enclosed in markdown fences
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
                json_str = match.group(1) if match else raw_output.strip()
                parsed_json = json.loads(json_str)
            except Exception as e:
                # If expecting structured output but received non-JSON
                if expected_schema_id != "unstructured_text":
                    return OutputGuardVerdict(
                        status=OutputValidationStatus.SCHEMA_VIOLATION,
                        is_safe=False,
                        sanitized_output=raw_output,
                        rejection_reason=f"Model output failed schema validation: Not valid JSON ({e}).",
                    )

        # 4. Citation and Evidence Binding Check
        if strict_citations and admissible_evidence_ids is not None:
            # Check for fabricated evidence IDs
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
                    sanitized_output=raw_output,
                    filtered_claims=list(fabricated),
                    rejection_reason=f"Output cited unsupported or fictitious evidence sources: {fabricated}",
                )

        return OutputGuardVerdict(
            status=OutputValidationStatus.VALID,
            is_safe=True,
            sanitized_output=raw_output,
        )
