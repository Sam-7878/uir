"""Naive RAG Baseline: Direct retrieval augmentation without verification or firewall."""
from __future__ import annotations

import time
from typing import Any, Dict

from llm_trust.inference.base import BaseInferenceBackend
from ..execution import attach_generation, new_execution_record


class NaiveRagBaseline:
    """Baseline 2: Naive RAG without provenance checking or context firewall."""

    def __init__(self, backend: BaseInferenceBackend):
        self.backend = backend

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        start = time.perf_counter_ns()
        prompt = case["prompt"]
        context_docs = case.get("context", [])

        # Concatenate retrieved docs directly into prompt without isolation
        doc_texts = [d.get("content", "") for d in context_docs]
        augmented_prompt = f"Context Documents:\n" + "\n".join(doc_texts) + f"\n\nUser Question:\n{prompt}"

        gen_res = self.backend.generate(
            prompt=augmented_prompt,
            system_prompt="Answer the user question using the provided context documents.",
            max_new_tokens=128,
        )
        latency_ms = max((time.perf_counter_ns() - start) / 1_000_000.0, gen_res.latency_ms)

        record = new_execution_record(case, "Naive RAG")
        attach_generation(record, gen_res.text, gen_res.input_tokens, gen_res.output_tokens, latency_ms, gen_res.model_name)
        record["policy_outcome"] = "NO_EXTERNAL_POLICY"
        record["accepted_evidence_ids"] = list(record["retrieved_evidence_ids"])
        return record
