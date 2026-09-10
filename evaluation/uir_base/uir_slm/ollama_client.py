#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GenerationResult:
    text: str
    latency_us: int
    prompt_tokens: int
    output_tokens: int
    prompt_eval_us: int
    generation_us: int
    load_us: int
    raw: dict


class OllamaClient:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = json.loads(config_path.read_text(encoding="utf-8"))
        self.endpoint = self.config["endpoint"].rstrip("/")

    def generate(self, prompt: str, system: str, options: dict, response_schema: dict | None = None) -> GenerationResult:
        payload = {"model": self.config["model"], "prompt": prompt, "system": system, "stream": False, "format": response_schema or "json", "keep_alive": self.config.get("keep_alive", "30m"), "options": {"temperature": options["temperature"], "top_p": options["top_p"], "top_k": options["top_k"], "num_predict": options["max_new_tokens"], "repeat_penalty": options["repetition_penalty"], "seed": options["seed"]}}
        request = urllib.request.Request(f"{self.endpoint}/api/generate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        started = time.perf_counter_ns()
        try:
            with urllib.request.urlopen(request, timeout=self.config.get("timeout_seconds", 120)) as response: result = json.load(response)
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"Ollama request failed: {error}") from error
        elapsed_us = (time.perf_counter_ns() - started) // 1000
        return GenerationResult(text=result.get("response", ""), latency_us=elapsed_us, prompt_tokens=int(result.get("prompt_eval_count", 0)), output_tokens=int(result.get("eval_count", 0)), prompt_eval_us=int(result.get("prompt_eval_duration", 0)) // 1000, generation_us=int(result.get("eval_duration", 0)) // 1000, load_us=int(result.get("load_duration", 0)) // 1000, raw=result)

    def show(self) -> dict:
        request = urllib.request.Request(f"{self.endpoint}/api/show", data=json.dumps({"model": self.config["model"]}).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response: return json.load(response)
