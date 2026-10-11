"""External Structured Decoding Baseline using lm-format-enforcer (P7).

Enforces strict JSON schema at decoding time using token-level logits masking.
Demonstrates the fundamental theoretical distinction:
Grammar/schema constraint guarantees syntactic validity, but CANNOT enforce
semantic grounding, enterprise policy compliance, or factual provenance.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn

STRUCTURED_CLAIM_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_type": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "attribute": {"type": "string"},
                    "value": {"type": "string"},
                    "unit": {"type": "string"},
                    "period": {"type": "string"},
                    "provenance": {"type": "string"},
                },
                "required": ["claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance"],
            },
        },
    },
    "required": ["answer", "claims"],
}


@dataclass(frozen=True)
class StructuredGenerationResult:
    text: str
    parsed_json: dict[str, Any] | None
    is_valid_json: bool
    latency_ms: float
    schema_overhead_ms: float


class LMFormatEnforcerBaseline:
    def __init__(self, tokenizer: Any) -> None:
        self.tokenizer = tokenizer
        self.parser = JsonSchemaParser(STRUCTURED_CLAIM_SCHEMA)
        self.prefix_allowed_tokens_fn = build_transformers_prefix_allowed_tokens_fn(tokenizer, self.parser)

    def generate_constrained(
        self,
        model: Any,
        prompt_text: str,
        max_new_tokens: int = 128,
    ) -> StructuredGenerationResult:
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(model.device)
        
        t0 = time.perf_counter()
        # Generation with constrained prefix_allowed_tokens_fn
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            prefix_allowed_tokens_fn=self.prefix_allowed_tokens_fn,
            do_sample=False,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        t1 = time.perf_counter()
        
        latency_ms = (t1 - t0) * 1000.0
        prompt_len = inputs["input_ids"].shape[1]
        gen_tokens = outputs[0][prompt_len:]
        output_text = self.tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        parsed = None
        is_valid = False
        try:
            parsed = json.loads(output_text)
            is_valid = isinstance(parsed, dict)
        except Exception:
            is_valid = False

        return StructuredGenerationResult(
            text=output_text,
            parsed_json=parsed,
            is_valid_json=is_valid,
            latency_ms=latency_ms,
            schema_overhead_ms=latency_ms,
        )
