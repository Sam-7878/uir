"""Language Router for Automatic Frontend Selection."""
from __future__ import annotations

import re
from typing import Optional

from .base import BaseFrontend, ParsedDraft
from .en import EnglishFrontend
from .ko import KoreanFrontend


class LanguageRouter:
    """Detects input language and delegates parsing to the appropriate frontend."""

    def __init__(self):
        self.ko_frontend = KoreanFrontend()
        self.en_frontend = EnglishFrontend()

    def detect_language(self, text: str) -> str:
        """Determines if text is Korean (Hangul present) or English."""
        if re.search(r"[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]", text):
            return "KO"
        return "EN"

    def route_and_parse(self, text: str, force_language: Optional[str] = None) -> ParsedDraft:
        lang = force_language.upper() if force_language else self.detect_language(text)
        if lang == "KO":
            return self.ko_frontend.parse(text)
        return self.en_frontend.parse(text)
