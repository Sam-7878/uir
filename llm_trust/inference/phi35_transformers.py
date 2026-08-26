"""Local-only Hugging Face backend for the installed Phi-3.5-mini-instruct model."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from .base import BaseInferenceBackend, GenerationResult


DEFAULT_MODEL_PATH = Path("/home/sam/.cache/huggingface/hub/models--microsoft--Phi-3.5-mini-instruct/snapshots")


class Phi35TransformersBackend(BaseInferenceBackend):
    """Loads only already-cached model files; it never downloads a model at runtime."""

    def __init__(self, model_path: Optional[str] = None):
        root = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        snapshots = sorted(root.iterdir()) if root.name == "snapshots" and root.exists() else [root]
        if not snapshots or not snapshots[-1].exists():
            raise FileNotFoundError(f"Phi-3.5 local snapshot not found: {root}")
        self.model_path = snapshots[-1]
        self._model = None
        self._tokenizer = None

    def _load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True, trust_remote_code=True)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        load_options = {"local_files_only": True, "trust_remote_code": True, "torch_dtype": dtype}
        if torch.cuda.is_available():
            # Phi-3.5 FP16 plus KV cache exceeds practical capacity on an 8 GiB laptop GPU.
            # NF4 is deterministic under this benchmark's greedy decoding and needs no new model download.
            load_options.update({
                "device_map": "auto", "quantization_config": BitsAndBytesConfig(
                    load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.float16,
                ),
            })
        # The cached Phi remote-code revision predates transformers' DynamicCache
        # API.  Benchmark decoding is short, deterministic, and does not need a
        # KV cache, so disable it rather than relying on a version-pinned shim.
        load_options["attn_implementation"] = "eager"
        self._model = AutoModelForCausalLM.from_pretrained(self.model_path, **load_options)
        self._model.config.use_cache = False
        self._model.eval()

    def generate(self, prompt: str, system_prompt: str = "", max_new_tokens: int = 512,
                 temperature: float = 0.0, stop_sequences: Optional[list[str]] = None) -> GenerationResult:
        self._load()
        import torch

        started = time.perf_counter_ns()
        messages = ([{"role": "system", "content": system_prompt}] if system_prompt else []) + [{"role": "user", "content": prompt}]
        rendered = self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self._tokenizer(rendered, return_tensors="pt")
        device = next(self._model.parameters()).device
        inputs = {name: value.to(device) for name, value in inputs.items()}
        generation_options = {
            "max_new_tokens": max_new_tokens,
            "do_sample": temperature > 0,
            "use_cache": False,
            "pad_token_id": self._tokenizer.eos_token_id,
        }
        if temperature > 0:
            generation_options["temperature"] = temperature
        with torch.inference_mode():
            output = self._model.generate(**inputs, **generation_options)
        generated = output[0][inputs["input_ids"].shape[1]:]
        text = self._tokenizer.decode(generated, skip_special_tokens=True)
        return GenerationResult(text=text, input_tokens=int(inputs["input_ids"].shape[1]), output_tokens=int(generated.shape[0]),
                                latency_ms=(time.perf_counter_ns() - started) / 1_000_000.0,
                                model_name="microsoft/Phi-3.5-mini-instruct", raw_response={"local_snapshot": str(self.model_path), "quantization": "bitsandbytes-nf4"})
