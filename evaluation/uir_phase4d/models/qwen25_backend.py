"""Qwen2.5-7B-Instruct Backend supporting local Ollama or HuggingFace Transformers (P6).

Enables cross-model validation to prove UIR mechanisms generalize across model families.
"""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

from evaluation.uir_phase4d.common import MAX_NEW_TOKENS, SECOND_MODEL_ID, SEED, sha256_text


@dataclass(frozen=True)
class QwenInvocation:
    case_id: str
    prompt: str
    system_prompt: str


@dataclass(frozen=True)
class QwenResult:
    case_id: str
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model_id: str


class Qwen25OllamaBackend:
    """Fast, local REST client for local Ollama daemon hosting qwen2.5:7b."""

    def __init__(self, endpoint: str = "http://localhost:11434/api/generate", model_tag: str = "qwen2.5:7b") -> None:
        self.endpoint = endpoint
        self.model_tag = model_tag

    def generate(self, prompt: str, system: str = "", max_tokens: int = MAX_NEW_TOKENS) -> QwenResult:
        payload = {
            "model": self.model_tag,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "seed": SEED,
                "num_predict": max_tokens,
            },
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        t1 = time.perf_counter()
        
        latency_ms = (t1 - t0) * 1000.0
        response_text = body.get("response", "").strip()
        eval_count = body.get("eval_count", len(response_text.split()))
        prompt_eval_count = body.get("prompt_eval_count", len(prompt.split()))

        return QwenResult(
            case_id="",
            text=response_text,
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            latency_ms=latency_ms,
            model_id=f"ollama:{self.model_tag}",
        )
