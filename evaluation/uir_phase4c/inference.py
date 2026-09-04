"""Measured, local-only Phi-3.5 batch inference for authentic Phase-4C traces."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from llm_trust.inference.phi35_transformers import Phi35TransformersBackend
from evaluation.uir_phase4c.common import MAX_NEW_TOKENS, MODEL_ID, MODEL_REVISION, SEED, sha256_text


@dataclass(frozen=True)
class Invocation:
    case_id: str
    prompt: str
    system_prompt: str


class ActualPhiGenerator:
    """Execute every supplied prompt and bind response and timing to one batch call."""

    def __init__(self, model_path: str | None = None, batch_size: int = 4):
        self.backend = Phi35TransformersBackend(model_path=model_path, max_input_tokens=2048, max_batch_token_volume=8192)
        self.batch_size = max(1, batch_size)
        random.seed(SEED)
        np.random.seed(SEED)

    def load(self) -> dict[str, Any]:
        import torch

        torch.manual_seed(SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED)
        started = time.perf_counter_ns()
        self.backend._load()
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        return {
            "model_load_ms": (time.perf_counter_ns() - started) / 1_000_000.0,
            "snapshot_path": str(self.backend.model_path),
            "hf_revision": MODEL_REVISION,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
        }

    def run(self, invocations: list[Invocation]) -> list[dict[str, Any]]:
        import torch

        outputs: list[dict[str, Any]] = []
        for offset in range(0, len(invocations), self.batch_size):
            chunk = invocations[offset : offset + self.batch_size]
            outputs.extend(self._run_chunk(chunk, offset))
            print(f"[phi35] generated {min(offset + len(chunk), len(invocations))}/{len(invocations)}", flush=True)
        return outputs

    def _run_chunk(self, chunk: list[Invocation], offset: int) -> list[dict[str, Any]]:
        import gc
        import torch

        requests = [{"prompt": item.prompt, "system_prompt": item.system_prompt, "max_new_tokens": MAX_NEW_TOKENS, "temperature": 0.0, "stop_sequences": None} for item in chunk]
        try:
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
            start_ns = time.perf_counter_ns()
            generated = self.backend.generate_batch(requests)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            end_ns = time.perf_counter_ns()
            elapsed_ms = (end_ns - start_ns) / 1_000_000.0
            peak_mb = float(torch.cuda.max_memory_allocated() / (1024 * 1024)) if torch.cuda.is_available() else 0.0
            batch_id = f"batch-{offset // self.batch_size:06d}"
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower() or len(chunk) == 1:
                raise
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
            middle = len(chunk) // 2
            return self._run_chunk(chunk[:middle], offset) + self._run_chunk(chunk[middle:], offset + middle)
        outputs = []
        for item, result in zip(chunk, generated, strict=True):
            finish_reason = "length" if result.output_tokens >= MAX_NEW_TOKENS else "stop"
            outputs.append({
                "case_id": item.case_id,
                "prompt_sha256": sha256_text(item.prompt),
                "prompt_text_or_content_ref": item.prompt,
                "system_prompt_sha256": sha256_text(item.system_prompt),
                "generation": {
                    "model": MODEL_ID,
                    "hf_revision": MODEL_REVISION,
                    "seed": SEED,
                    "do_sample": False,
                    "max_new_tokens": MAX_NEW_TOKENS,
                    "raw_response": result.text,
                    "raw_response_sha256": sha256_text(result.text),
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "finish_reason": finish_reason,
                },
                "model_timing": {"start_ns": start_ns, "end_ns": end_ns, "model_ms": elapsed_ms, "batch_id": batch_id, "batch_size": len(chunk)},
                "resource": {"peak_vram_mb": round(peak_mb, 3)},
            })
        return outputs
