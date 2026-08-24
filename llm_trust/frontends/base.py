"""Base Language Frontend Interface for UIR."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ParsedDraft:
    language: str
    intent: str
    action: str
    target_entities: List[str]
    arguments: Dict[str, Any]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    temporal_scope: Optional[str] = None
    domain: str = "FINANCE"
    raw_prompt: str = ""


class BaseFrontend(ABC):
    """Abstract base class for language-specific UIR frontends."""

    @abstractmethod
    def parse(self, text: str) -> ParsedDraft:
        """Parses natural language request into typed UIR draft."""
        pass
