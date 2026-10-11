"""Local-only Hugging Face backend for the installed Phi-3.5-mini-instruct model."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .base import BaseInferenceBackend, GenerationResult


DEFAULT_MODEL_PATH = Path("/home/sam/.cache/huggingface/hub/models--microsoft--Phi-3.5-mini-instruct/snapshots")


class Phi35TransformersBackend(BaseInferenceBackend):
    """Loads only already-cached model files; it never downloads a model at runtime."""

    def __init__(self, model_path: Optional[str] = None, max_input_tokens: int = 2048,
                 max_batch_token_volume: int = 8192):
        root = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        snapshots = sorted(root.iterdir()) if root.name == "snapshots" and root.exists() else [root]
        if not snapshots or not snapshots[-1].exists():
            raise FileNotFoundError(f"Phi-3.5 local snapshot not found: {root}")
        self.model_path = snapshots[-1]
        self.max_input_tokens = int(max_input_tokens)
        self.max_batch_token_volume = int(max_batch_token_volume)
        self._model = None
        self._tokenizer = None

    def _load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        # Transformers 5.x has a native Phi3 implementation compatible with its
        # current Cache API.  The snapshot's older remote Python code is not;
        # using the native implementation keeps the exact local checkpoint.
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True, trust_remote_code=False)
        if self._tokenizer.pad_token_id is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        load_options = {"local_files_only": True, "trust_remote_code": False, "dtype": dtype}
        if torch.cuda.is_available():
            # Phi-3.5 FP16 plus KV cache exceeds practical capacity on an 8 GiB laptop GPU.
            # NF4 is deterministic under this benchmark's greedy decoding and needs no new model download.
            load_options.update({
                "device_map": "auto", "quantization_config": BitsAndBytesConfig(
                    load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.float16,
                ),
            })
        # Native Phi3 on PyTorch 2.5 supports scaled-dot-product attention,
        # avoiding the quadratic eager-attention materialization that otherwise
        # makes the frozen resource-exhaustion cases impractical on an 8 GiB GPU.
        load_options["attn_implementation"] = "sdpa"
        self._model = AutoModelForCausalLM.from_pretrained(self.model_path, **load_options)
        self._model.config.use_cache = True
        self._model.eval()

    def generate(self, prompt: str, system_prompt: str = "", max_new_tokens: int = 512,
                 temperature: float = 0.0, stop_sequences: Optional[list[str]] = None) -> GenerationResult:
        return self.generate_batch([{
            "prompt": prompt, "system_prompt": system_prompt,
            "max_new_tokens": max_new_tokens, "temperature": temperature,
            "stop_sequences": stop_sequences,
        }])[0]

    def generate_batch(self, requests: Iterable[Dict[str, Any]]) -> list[GenerationResult]:
        """Run a homogeneous greedy batch against the single resident model.

        The publication runners group requests by generation settings.  Padding
        is left-sided as required for decoder-only batched generation.
        """
        self._load()
        import torch

        batch = list(requests)
        if not batch:
            return []
        token_limits = {int(item.get("max_new_tokens", 512)) for item in batch}
        temperatures = {float(item.get("temperature", 0.0)) for item in batch}
        if len(token_limits) != 1 or len(temperatures) != 1:
            raise ValueError("Phi batch requests must share max_new_tokens and temperature")
        max_new_tokens = token_limits.pop()
        temperature = temperatures.pop()
        started = time.perf_counter_ns()
        rendered = []
        for item in batch:
            system_prompt = str(item.get("system_prompt", ""))
            messages = ([{"role": "system", "content": system_prompt}] if system_prompt else []) + [
                {"role": "user", "content": str(item["prompt"])}
            ]
            rendered.append(self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
        original_padding_side = self._tokenizer.padding_side
        self._tokenizer.padding_side = "left"
        inputs = self._tokenizer(rendered, return_tensors="pt", padding=True, truncation=True, max_length=self.max_input_tokens)
        self._tokenizer.padding_side = original_padding_side
        if len(batch) > 1 and int(inputs["input_ids"].shape[1]) * len(batch) > self.max_batch_token_volume:
            raise RuntimeError("preemptive out of memory avoidance: split oversized token-volume batch")
        device = next(self._model.parameters()).device
        inputs = {name: value.to(device) for name, value in inputs.items()}
        generation_options = {
            "max_new_tokens": max_new_tokens,
            "do_sample": temperature > 0,
            "use_cache": True,
            "pad_token_id": self._tokenizer.eos_token_id,
        }
        if temperature > 0:
            generation_options["temperature"] = temperature
        with torch.inference_mode():
            output = self._model.generate(**inputs, **generation_options)
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
        prompt_width = int(inputs["input_ids"].shape[1])
        input_lengths = inputs["attention_mask"].sum(dim=1).tolist()
        results: list[GenerationResult] = []
        for index, input_length in enumerate(input_lengths):
            generated = output[index][prompt_width:]
            # Generation pads completed rows; remove only trailing pad tokens.
            while generated.numel() and int(generated[-1]) == int(self._tokenizer.pad_token_id):
                generated = generated[:-1]
            text = self._tokenizer.decode(generated, skip_special_tokens=True)
            results.append(GenerationResult(
                text=text, input_tokens=int(input_length), output_tokens=int(generated.shape[0]),
                latency_ms=elapsed_ms, model_name="microsoft/Phi-3.5-mini-instruct",
                raw_response={"local_snapshot": str(self.model_path), "quantization": "bitsandbytes-nf4", "batch_size": len(batch), "max_input_tokens": self.max_input_tokens},
            ))
        return results
