#!/usr/bin/env python3
"""Generate realistic reporter-preserving mutations and retain only live 404 results."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from evaluation.uir_law.law200.common import DATA_DIR, read_jsonl, write_jsonl
from evaluation.uir_law.law200.courtlistener import CourtListenerClient, entry_record, wait_for_citation_window

CITE = re.compile(r"^(\d+) U\.S\. (\d+)$")


def candidates(records: list[dict]) -> list[tuple[str, dict]]:
    output: list[tuple[str, dict]] = []
    seen: set[str] = {str(record["citation_canonical"]) for record in records}
    for record in records:
        source = str(record["citation_canonical"])
        match = CITE.match(source)
        if not match:
            continue
        volume, page = map(int, match.groups())
        variants = [
            (page + 1, "adjacent_page_plus_1"),
            (page + 7, "adjacent_page_plus_7"),
            (max(1, page - 1), "adjacent_page_minus_1"),
            (page + 11, "page_small_delta"),
        ]
        digits = str(page)
        if len(digits) > 1 and digits[-1] != digits[-2]:
            variants.append((int(digits[:-2] + digits[-1] + digits[-2]), "page_digit_transposition"))
        for mutated_page, mutation_type in variants:
            citation = f"{volume} U.S. {mutated_page}"
            if citation in seen:
                continue
            seen.add(citation)
            output.append((citation, {"type": mutation_type, "source_valid_citation": source}))
        for mutated_volume, mutation_type in ((volume + 1, "volume_plus_1"), (max(1, volume - 1), "volume_minus_1")):
            citation = f"{mutated_volume} U.S. {page}"
            if citation not in seen:
                seen.add(citation)
                output.append((citation, {"type": mutation_type, "source_valid_citation": source}))
    return output


def generate(valid_path: Path, output: Path, auth_scheme: str, minimum: int = 30) -> list[dict]:
    valid = read_jsonl(valid_path)
    pending = candidates(valid)
    client = CourtListenerClient(auth_scheme=auth_scheme)
    accepted: list[dict] = []
    for offset in range(0, len(pending), 60):
        chunk = pending[offset : offset + 60]
        batch = client.lookup([citation for citation, _ in chunk], f"negative_{offset // 60:03d}")
        by_citation = {citation: mutation for citation, mutation in chunk}
        for entry in batch.entries:
            raw = str(entry.get("citation", ""))
            mutation = by_citation.get(raw)
            if mutation is None:
                normalized = entry.get("normalized_citations") or []
                mutation = by_citation.get(str(normalized[0])) if normalized else None
            record = entry_record(entry, batch, mutation)
            if record["lookup_status"] == 404 and mutation:
                accepted.append(record)
        print(f"[negative] checked={min(offset + 60, len(pending))} accepted_404={len(accepted)}", flush=True)
        if len(accepted) >= minimum:
            break
        if offset + 60 < len(pending):
            wait_for_citation_window()
    if len(accepted) < minimum:
        raise RuntimeError(f"only {len(accepted)} verified 404 citations; need {minimum}")
    write_jsonl(output, accepted[:minimum])
    return accepted[:minimum]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--valid", type=Path, default=DATA_DIR / "source_registry_valid.jsonl")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "source_registry_invalid.jsonl")
    parser.add_argument("--auth-scheme", choices=("Token", "Bearer"), default="Token")
    parser.add_argument("--minimum", type=int, default=30)
    args = parser.parse_args()
    generate(args.valid, args.output, args.auth_scheme, args.minimum)


if __name__ == "__main__":
    main()
