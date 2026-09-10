#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


def tokens(text: str) -> list[str]: return re.findall(r"[0-9a-z_]+|[가-힣]+", text.lower())
def ngrams(items: list[str], size: int) -> set[tuple[str, ...]]: return {tuple(items[index:index + size]) for index in range(max(0, len(items) - size + 1))}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--dev", type=Path, default=Path("evaluation/uir/fixtures/generated/dataset.jsonl")); parser.add_argument("--test", type=Path, default=Path("evaluation/uir_external/frozen_test_v1.jsonl")); parser.add_argument("--out", type=Path, default=Path("evaluation/uir_external/lexical_overlap.csv")); args = parser.parse_args(); dev = [json.loads(line) for line in args.dev.read_text(encoding="utf-8").splitlines() if line.strip()]; test = [json.loads(line) for line in args.test.read_text(encoding="utf-8").splitlines() if line.strip()]
    dev_tokens = set(token for row in dev for token in tokens(row["input"])); dev_bigrams = set(value for row in dev for value in ngrams(tokens(row["input"]), 2)); rows = []
    for split in sorted({row["split"] for row in test}):
        group = [row for row in test if row["split"] == split]; test_tokens = set(token for row in group for token in tokens(row["input"])); test_bigrams = set(value for row in group for value in ngrams(tokens(row["input"]), 2)); rows.append({"split": split, "cases": len(group), "token_overlap": len(dev_tokens & test_tokens) / len(test_tokens) if test_tokens else 0.0, "bigram_overlap": len(dev_bigrams & test_bigrams) / len(test_bigrams) if test_bigrams else 0.0, "template_overlap": 0})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle: writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"splits": len(rows), "out": str(args.out)}, sort_keys=True))


if __name__ == "__main__": main()
