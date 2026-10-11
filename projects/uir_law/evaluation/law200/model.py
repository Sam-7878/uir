"""Measured Ollama client used identically by all primary LAW-200 pipelines."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    model: str = "phi3.5:latest"
    endpoint: str = "http://127.0.0.1:11434"
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 192
    seed: int = 20260911
    timeout_seconds: int = 180

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OllamaModel:
    def __init__(self, config: ModelConfig):
        self.config = config

    def generate(self, prompt: str, system: str) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
                "seed": self.config.seed,
            },
        }
        request = urllib.request.Request(
            f"{self.config.endpoint.rstrip('/')}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter_ns()
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Ollama generation failed: {exc}") from exc
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        return {
            "raw_response": str(body.get("response", "")),
            "latency_ms": elapsed_ms,
            "input_tokens": int(body.get("prompt_eval_count", 0)),
            "output_tokens": int(body.get("eval_count", 0)),
            "load_ms": int(body.get("load_duration", 0)) / 1_000_000,
            "prompt_eval_ms": int(body.get("prompt_eval_duration", 0)) / 1_000_000,
            "generation_ms": int(body.get("eval_duration", 0)) / 1_000_000,
            "done_reason": body.get("done_reason"),
        }

    def show(self) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.config.endpoint.rstrip('/')}/api/show",
            data=json.dumps({"model": self.config.model}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Ollama model metadata lookup failed: {exc}") from exc
        details = body.get("details") if isinstance(body.get("details"), dict) else {}
        return {
            "model": self.config.model,
            "family": details.get("family"),
            "parameter_size": details.get("parameter_size"),
            "quantization_level": details.get("quantization_level"),
            "modified_at": body.get("modified_at"),
            "digest": body.get("digest"),
        }
