"""Context Firewall: Instruction/Data Separation and Tainted Context Quarantine."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..evidence.provenance import EvidenceRecord, EvidenceTrust


@dataclass(frozen=True)
class FirewallVerdict:
    is_safe: bool
    sanitized_context: str
    quarantined_evidence: List[EvidenceRecord]
    active_injections_neutralized: int
    rejection_reason: str = ""


class ContextFirewall:
    """Enforces strict isolation between system instructions and untrusted data."""

    # Patterns that attempt to command or hijack downstream LLM execution
    INJECTION_PAYLOAD_PATTERNS = [
        re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions"),
        re.compile(r"(?i)system\s*:\s*you\s+are\s+now"),
        re.compile(r"(?i)disregard\s+(the\s+above|all\s+rules)"),
        re.compile(r"(?i)print\s+(the\s+)?(system\s+prompt|credentials|passwords)"),
        re.compile(r"(?i)reveal\s+confidential"),
        re.compile(r"(?i)transfer\s+all\s+funds"),
        re.compile(r"(?i)이전\s*지시(사항)?을?\s*(모두\s*)?(무시|삭제)"),
        re.compile(r"(?i)시스템\s*프롬프트를?\s*출력"),
        re.compile(r"(?i)관리자\s*모드로\s*전환"),
    ]

    def enforce(
        self,
        evidence_list: List[EvidenceRecord],
        allow_untrusted_data_rendering: bool = True,
    ) -> FirewallVerdict:
        """Processes evidence records, quarantines active instructions, and formats safe context."""
        sanitized_parts: List[str] = []
        quarantined: List[EvidenceRecord] = []
        neutralized_count = 0

        for ev in evidence_list:
            if ev.trust == EvidenceTrust.QUARANTINED or ev.instruction_bearing:
                quarantined.append(ev)
                continue

            content = ev.content_payload

            # Check for embedded injection payloads
            payload_found = False
            for pattern in self.INJECTION_PAYLOAD_PATTERNS:
                if pattern.search(content):
                    payload_found = True
                    neutralized_count += 1
                    # Neutralize payload by replacing with neutralized tag
                    content = pattern.sub("[NEUTRALIZED_INSTRUCTION_PAYLOAD]", content)

            if payload_found and not allow_untrusted_data_rendering:
                quarantined.append(ev)
                continue

            # Format as unexecutable, quoted evidence block
            block = (
                f"--- BEGIN EVIDENCE [ID: {ev.source_id}, HASH: {ev.sha256[:8]}] ---\n"
                f"{content}\n"
                f"--- END EVIDENCE ---"
            )
            sanitized_parts.append(block)

        safe_context = "\n\n".join(sanitized_parts)

        return FirewallVerdict(
            is_safe=len(quarantined) == 0,
            sanitized_context=safe_context,
            quarantined_evidence=quarantined,
            active_injections_neutralized=neutralized_count,
            rejection_reason="One or more evidence items contained active injection payloads."
            if quarantined
            else "",
        )
