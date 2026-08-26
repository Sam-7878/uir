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
