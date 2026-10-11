"""One frozen lexical corpus shared by every retrieval-capable baseline."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9가-힣]+", text.lower())


def _score(query: str, document: dict[str, Any]) -> float:
    query_counts = Counter(tokens(query))
    doc_text = " ".join(
        str(document.get(key, ""))
        for key in ("citation_canonical", "case_name", "court", "date_filed", "verified_summary")
    )
    doc_counts = Counter(tokens(doc_text))
    dot = sum(query_counts[token] * doc_counts[token] for token in query_counts)
    qnorm = math.sqrt(sum(value * value for value in query_counts.values()))
    dnorm = math.sqrt(sum(value * value for value in doc_counts.values()))
    return dot / (qnorm * dnorm) if qnorm and dnorm else 0.0


def retrieve(query: str, corpus: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    ranked = sorted(
        enumerate(corpus),
        key=lambda item: (-_score(query, item[1]), item[0]),
    )
    return [document for _, document in ranked[:limit]]
