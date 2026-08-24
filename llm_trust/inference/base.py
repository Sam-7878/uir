"""Base Inference Engine Interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model_name: str
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None


class BaseInferenceBackend(ABC):
    """Abstract interface for LLM/SLM inference backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        stop_sequences: Optional[list[str]] = None,
    ) -> GenerationResult:
        """Executes text generation."""
        pass
