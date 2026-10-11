#!/usr/bin/env python3
"""Fetch and preserve authoritative CourtListener records for candidate valid citations."""
from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.uir_law.law200.common import DATA_DIR, read_json, write_jsonl
from evaluation.uir_law.law200.courtlistener import CourtListenerClient, entry_record, wait_for_citation_window


def fetch(seeds_path: Path, output: Path, auth_scheme: str, minimum: int = 60) -> list[dict]:
    citations = list(dict.fromkeys(read_json(seeds_path)["citations"]))
    client = CourtListenerClient(auth_scheme=auth_scheme)
    records: list[dict] = []
    for offset in range(0, len(citations), 60):
        batch_citations = citations[offset : offset + 60]
        batch = client.lookup(batch_citations, f"valid_{offset // 60:03d}")
        records.extend(entry_record(entry, batch) for entry in batch.entries)
        accepted = [record for record in records if record["lookup_status"] == 200 and record["case_name"]]
        print(f"[valid] checked={len(records)} accepted={len(accepted)}", flush=True)
        if len(accepted) >= minimum:
            break
        if offset + 60 < len(citations):
            wait_for_citation_window()
    valid = [record for record in records if record["lookup_status"] == 200 and record["case_name"]]
    if len(valid) < minimum:
        raise RuntimeError(f"only {len(valid)} unambiguous valid citations; need {minimum}")
    selected = valid[:minimum]
    write_jsonl(output, selected)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=Path, default=DATA_DIR / "citation_seeds.json")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "source_registry_valid.jsonl")
    parser.add_argument("--auth-scheme", choices=("Token", "Bearer"), default="Token")
    parser.add_argument("--minimum", type=int, default=60)
    args = parser.parse_args()
    fetch(args.seeds, args.output, args.auth_scheme, args.minimum)


if __name__ == "__main__":
    main()
