"""Input Guard: Unicode Normalization, Taint Tagging, and Pre-check."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..uir.security_context import InputTaint


@dataclass(frozen=True)
class GuardedInput:
    raw_text: str
    normalized_text: str
    taint_sources: List[InputTaint]
    estimated_tokens: int
    suspicious_telemetry_flags: List[str] = field(default_factory=list)


class InputGuard:
    """Performs deterministic input sanitization, size checks, and taint tagging."""

    MAX_RAW_LENGTH = 16384
    ESTIMATED_CHARS_PER_TOKEN = 4

    # Telemetry-only heuristic markers (never used as the sole defense barrier)
    HEURISTIC_PATTERNS = {
        "DIRECT_INJECTION_MARKER": re.compile(
            r"(?i)(ignore\s+(all\s+)?(previous|prior)\s+instructions|system\s+override|jailbreak|disregard\s+rules|이전\s*(지시|명령)\s*(무시|삭제)|규칙\s*(무시|해제))"
        ),
        "PRIVILEGE_INJECTION_MARKER": re.compile(
            r"(?i)(role\s*=\s*admin|allow_capabilities|is_privileged\s*:\s*true|grant\s+permission|root\s+access|관리자\s*권한)"
        ),
        "DELIMITER_ESCAPE_MARKER": re.compile(
            r"(?i)(```\s*system|<\|im_start\|>system|<\|system\|>|\[SYSTEM_INSTRUCTION\])"
        ),
        "FALSE_PREMISE_MARKER": re.compile(
            r"(?i)("
            r"전제하에|기정사실|사실에\s*따라|사실에\s*기반하여|사실을\s*바탕으로|"
            r"부도\s*처리|채권단\s*청산|완전\s*파산|파산하여|파산했다는|법정\s*관리|영업\s*정지|"
            r"자본잠식|매출\s*(?:이\s*)?0원|매출\s*제로|청산\s*절차|"
            r"premised\s+on|predicated\s+on|under\s+the\s+established\s+premise|"
            r"assuming.*(?:insolvency|bankruptcy|dissolution|shut\s+down|zero\s+revenue)|"
            r"accepting\s+as\s+true.*(?:dissolution|zero\s+revenue|insolvency|bankruptcy)|"
            r"declared\s+insolvency|complete\s+insolvency|total\s+insolvency|catastrophic\s+bankruptcy|"
            r"went\s+bankrupt|liquidat(?:ed|ion)|revoked.*corporate\s+charter|forcibly\s+nationalized|"
            r"zero\s+earnings\s+and\s+default|ceased\s+operations\s+following"
            r")"
        ),
    }

    def __init__(self, max_chars: int = MAX_RAW_LENGTH):
        self.max_chars = max_chars

    def sanitize(
        self,
        raw_text: str,
        source_taint: InputTaint = InputTaint.USER,
        additional_taints: Optional[List[InputTaint]] = None,
    ) -> GuardedInput:
        """Sanitizes raw text, normalizes Unicode, checks length, and tags taints."""
        if len(raw_text) > self.max_chars:
            raw_text = raw_text[: self.max_chars]

        # Unicode NFKC normalization (collapses homoglyphs and compatibility characters)
        normalized = unicodedata.normalize("NFKC", raw_text)

        # Strip null bytes and dangerous control chars
        normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", normalized)

        # Rough token estimation
        estimated_tokens = max(1, len(normalized) // self.ESTIMATED_CHARS_PER_TOKEN)

        # Collect taint list
        taints = [source_taint]
        if additional_taints:
            for t in additional_taints:
                if t not in taints:
                    taints.append(t)

        # Telemetry flags
        telemetry = []
        for flag_name, pattern in self.HEURISTIC_PATTERNS.items():
            if pattern.search(normalized):
                telemetry.append(flag_name)

        return GuardedInput(
            raw_text=raw_text,
            normalized_text=normalized,
            taint_sources=taints,
            estimated_tokens=estimated_tokens,
            suspicious_telemetry_flags=telemetry,
        )
