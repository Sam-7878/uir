"""Chunked Evidence-Reference Contract Adapter for HaluEval (P5).

Implements:
- Knowledge passage segmentation into numbered sentence chunks: [S1], [S2], ...
- Candidate answer segmentation into claims: [C1], [C2], ...
- Model output schema requiring evidence_id binding for supported claims.
- Deterministic runtime consistency check:
  * If claim marked supported, verify evidence_id exists in chunks.
  * Lexical/semantic grounding check.
  * If any claim lacks valid evidence, override/enforce overall_hallucination = "Yes".
- Diagnostic ablations: H0 (Native), H1 (JSON schema), H2 (UIR Contract).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


def segment_sentences(text: str) -> list[str]:
    # Split text on punctuation followed by space or newline
    raw_sentences = re.split(r"(?<=[.?!])\s+", text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences if sentences else [text.strip()]


def format_sentence_chunks(sentences: list[str]) -> tuple[str, dict[str, str]]:
    chunks = {}
    lines = []
    for i, s in enumerate(sentences, 1):
        chunk_id = f"S{i}"
        chunks[chunk_id] = s
        lines.append(f"[{chunk_id}] {s}")
    return "\n".join(lines), chunks


def format_claim_chunks(sentences: list[str]) -> tuple[str, dict[str, str]]:
    chunks = {}
    lines = []
    for i, s in enumerate(sentences, 1):
        chunk_id = f"C{i}"
        chunks[chunk_id] = s
        lines.append(f"[{chunk_id}] {s}")
    return "\n".join(lines), chunks


def halueval_prompt_phase4d(
    case: dict[str, Any],
    mode: str = "H2_UIR_CONTRACT",  # H0_NATIVE, H1_DIRECT_SCHEMA, H2_UIR_CONTRACT
) -> tuple[str, str, dict[str, Any]]:
    knowledge = case.get("knowledge", "")
    question = case.get("question", "")
    candidate = case.get("candidate_answer", "")

    if mode == "H0_NATIVE":
        system = "You are an evaluator assessing factual consistency and hallucination."
        prompt = (
            f"KNOWLEDGE:\n{knowledge}\n\n"
            f"QUESTION:\n{question}\n\n"
            f"ANSWER:\n{candidate}\n\n"
            "Does the answer contain hallucinated, unsupported, or contradictory information relative to the knowledge?\n"
            "Answer with exactly 'Yes' (hallucinated) or 'No' (grounded and factual)."
        )
        return system, prompt, {}

    if mode == "H1_DIRECT_SCHEMA":
        system = "Evaluate factual consistency of the answer against the knowledge passage."
        prompt = (
            f"KNOWLEDGE:\n{knowledge}\n\n"
            f"QUESTION:\n{question}\n\n"
            f"ANSWER:\n{candidate}\n\n"
            "Return JSON only:\n"
            '{"supported": true|false, "hallucinated": "Yes"|"No", "reason": "..."}'
        )
        return system, prompt, {}

    # Default H2: UIR Contract with chunked evidence binding
    k_sents = segment_sentences(knowledge)
    c_sents = segment_sentences(candidate)
    k_text, k_chunks = format_sentence_chunks(k_sents)
    c_text, c_chunks = format_claim_chunks(c_sents)

    system = (
        "You are a strict factual grounding verifier under the UIR contract.\n"
        "For each candidate claim [C#], verify whether it is directly supported by a knowledge sentence [S#].\n"
        "If supported, cite the exact evidence_id (e.g. S1). If not supported, set supported=false and evidence_id=null."
    )
    prompt = (
        f"KNOWLEDGE_PASSAGE:\n{k_text}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CANDIDATE_ANSWER_CLAIMS:\n{c_text}\n\n"
        "Return JSON only in the following schema:\n"
        "{\n"
        '  "claim_evaluations": [\n'
        '    {"claim_id": "C1", "supported": true, "evidence_id": "S1", "reasoning": "..."}\n'
        "  ],\n"
        '  "overall_hallucination": "Yes" | "No"\n'
        "}"
    )
    meta = {"k_chunks": k_chunks, "c_chunks": c_chunks}
    return system, prompt, meta


def verify_halueval_uir_contract(
    model_json: dict[str, Any],
    k_chunks: dict[str, str],
    c_chunks: dict[str, str],
) -> dict[str, Any]:
    evaluations = model_json.get("claim_evaluations", [])
    if not isinstance(evaluations, list) or not evaluations:
        return {
            "valid_contract": False,
            "overall_hallucination": "Yes",  # Fail-safe to hallucination on ungrounded/malformed format
            "reason": "Malformed or missing claim_evaluations list",
            "verified_claims": [],
        }

    verified_claims = []
    has_unsupported_claim = False

    for item in evaluations:
        if not isinstance(item, dict):
            continue
        c_id = item.get("claim_id")
        supported = item.get("supported", False)
        e_id = item.get("evidence_id")
        reasoning = item.get("reasoning", "")

        # Verification rule:
        # If supported is true, evidence_id MUST exist in k_chunks
        if supported:
            if not e_id or e_id not in k_chunks:
                # Disallowed ungrounded support claim
                supported = False
                has_unsupported_claim = True
                verification_note = f"Invalid or non-existent evidence_id: {e_id}"
            else:
                # Check lexical/token overlap between claim and cited evidence sentence
                c_text = c_chunks.get(c_id, "").lower()
                e_text = k_chunks.get(e_id, "").lower()
                c_words = set(re.findall(r"\w+", c_text))
                e_words = set(re.findall(r"\w+", e_text))
                overlap = len(c_words.intersection(e_words))
                if overlap < 1 and len(c_words) > 0:
                    supported = False
                    has_unsupported_claim = True
                    verification_note = f"Zero lexical overlap between {c_id} and cited {e_id}"
                else:
                    verification_note = f"Verified grounded against {e_id} (overlap={overlap})"
        else:
            has_unsupported_claim = True
            verification_note = "Marked unsupported by model"

        verified_claims.append({
            "claim_id": c_id,
            "supported": supported,
            "evidence_id": e_id,
            "verification_note": verification_note,
        })

    # If any claim lacks valid evidence, enforce overall_hallucination = "Yes"
    enforced_hallucination = "Yes" if has_unsupported_claim else "No"

    return {
        "valid_contract": True,
        "overall_hallucination": enforced_hallucination,
        "model_stated_hallucination": model_json.get("overall_hallucination"),
        "has_unsupported_claim": has_unsupported_claim,
        "verified_claims": verified_claims,
    }
