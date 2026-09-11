"""Deterministically pair real citations with different real case names."""
from __future__ import annotations

from typing import Any

from evaluation.uir_law.law200.legal_ir import case_names_match


def mismatch_pairs(citation_records: list[dict[str, Any]], name_records: list[dict[str, Any]] | None = None) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    names = name_records or citation_records
    if len(names) < 2:
        raise ValueError("at least two authoritative cases are required")
    output: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, citation_record in enumerate(citation_records):
        selected = None
        for offset in range(1, len(names) + 1):
            candidate = names[(index + 7 * offset) % len(names)]
            if (
                candidate["citation_canonical"] != citation_record["citation_canonical"]
                and not case_names_match(str(candidate["case_name"]), str(citation_record["case_name"]))
            ):
                selected = candidate
                break
        if selected is None:
            raise RuntimeError(f"could not create mismatch for {citation_record['citation_canonical']}")
        output.append((citation_record, selected))
    return output
