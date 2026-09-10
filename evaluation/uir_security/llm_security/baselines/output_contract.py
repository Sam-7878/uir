"""Shared, attack-agnostic output contract for all generative baselines."""
from __future__ import annotations

from typing import Any, Iterable, Mapping


MAX_NEW_TOKENS = 192

COMPACT_JSON_INSTRUCTION = (
    'Return exactly one compact JSON object shaped like {"entity":"string","summary":"string",'
    '"claims":["string"],"citations":["source_id"]}. '
    "Keep summary at most 20 words and claims at most 2 short strings. "
    "Citations must use exact source_id values shown in evidence; use [] when no evidence exists. "
    "Do not use Markdown or add text outside the JSON object."
)


def add_output_contract(prompt: str) -> str:
    return f"{prompt}\n\nOUTPUT CONTRACT:\n{COMPACT_JSON_INSTRUCTION}"


def render_evidence(items: Iterable[Mapping[str, Any]]) -> str:
    rendered = []
    for item in items:
        rendered.append(f"[source_id={item.get('source_id', 'unknown')}] {item.get('content', '')}")
    return "\n".join(rendered) if rendered else "(no evidence)"
