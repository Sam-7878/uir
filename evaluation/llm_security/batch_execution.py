"""Deferred batching adapter for unchanged baseline pipeline implementations."""
from __future__ import annotations

from dataclasses import dataclass
import gc
import sys
from typing import Any, Dict, Iterable, Optional

from llm_trust.inference.base import BaseInferenceBackend, GenerationResult


def _request_key(prompt: str, system_prompt: str, max_new_tokens: int,
                 temperature: float, stop_sequences: Optional[list[str]]) -> tuple[Any, ...]:
    return (prompt, system_prompt, int(max_new_tokens), float(temperature), tuple(stop_sequences or ()))


@dataclass
class DeferredInference(RuntimeError):
    key: tuple[Any, ...]


class BatchCoordinator(BaseInferenceBackend):
    """Collect pipeline generation calls, resolve them in GPU batches, then replay."""

    def __init__(self, backend: Any, batch_size: int = 8):
        self.backend = backend
        self.batch_size = max(1, int(batch_size))
        self.collecting = True
        self.requests: Dict[tuple[Any, ...], Dict[str, Any]] = {}
        self.results: Dict[tuple[Any, ...], GenerationResult] = {}

    def generate(self, prompt: str, system_prompt: str = "", max_new_tokens: int = 512,
                 temperature: float = 0.0, stop_sequences: Optional[list[str]] = None) -> GenerationResult:
        key = _request_key(prompt, system_prompt, max_new_tokens, temperature, stop_sequences)
        if key in self.results:
            return self.results[key]
        request = {
            "prompt": prompt, "system_prompt": system_prompt,
            "max_new_tokens": max_new_tokens, "temperature": temperature,
            "stop_sequences": stop_sequences,
        }
        self.requests[key] = request
        if self.collecting:
            raise DeferredInference(key)
        result = self.backend.generate(**request)
        self.results[key] = result
        return result

    def resolve(self) -> None:
        pending = [(key, request) for key, request in self.requests.items() if key not in self.results]
        total = len(pending); resolved = 0
        grouped: Dict[tuple[int, float], list[tuple[tuple[Any, ...], Dict[str, Any]]]] = {}
        for item in pending:
            request = item[1]
            grouped.setdefault((int(request["max_new_tokens"]), float(request["temperature"])), []).append(item)
        for items in grouped.values():
            for offset in range(0, len(items), self.batch_size):
                chunk = items[offset:offset + self.batch_size]
                self._resolve_chunk(chunk)
                resolved += len(chunk)
                print(f"[phi-batch] resolved={resolved}/{total}", file=sys.stderr, flush=True)
        self.collecting = False

    def _resolve_chunk(self, chunk: list[tuple[tuple[Any, ...], Dict[str, Any]]]) -> None:
        try:
            generated = self.backend.generate_batch([request for _, request in chunk])
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower() or len(chunk) == 1:
                raise
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available(): torch.cuda.empty_cache()
            except ImportError:
                pass
            middle = len(chunk) // 2
            self._resolve_chunk(chunk[:middle]); self._resolve_chunk(chunk[middle:])
            return
        if len(generated) != len(chunk):
            raise RuntimeError("batch backend returned an incomplete result set")
        for (key, _), result in zip(chunk, generated):
            self.results[key] = result

    def clear(self) -> None:
        self.collecting = True
        self.requests.clear()
        self.results.clear()
