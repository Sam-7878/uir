#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.uir_law.law200.baselines import PIPELINES
from evaluation.uir_law.law200.common import DATA_DIR, RAW_DIR, RESULTS_DIR
from evaluation.uir_law.law200.scoring.score_supported_claims import score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--jurisdiction", choices=("us", "kr"), default="us")
    parser.add_argument("--model-slug", default="phi3-5-latest")
    parser.add_argument("--pipelines", nargs="+", choices=PIPELINES, default=list(PIPELINES))
    args = parser.parse_args()
    data_dir = DATA_DIR if args.jurisdiction == "us" else DATA_DIR / "kr"
    results_dir = RESULTS_DIR if args.jurisdiction == "us" else RESULTS_DIR / "kr"
    raw_dir = RAW_DIR if args.jurisdiction == "us" else results_dir / "raw"
    aggregate_dir = results_dir / "aggregate"
    table_dir = results_dir / "tables"
    paths = [raw_dir / f"{args.split}_{pipeline}_{args.model_slug}.jsonl" for pipeline in args.pipelines]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"raw result files missing: {missing}")
    scored, aggregates = score(
        args.split, paths, data_dir / f"law200_{args.split}_gold.jsonl",
        aggregate_dir=aggregate_dir, table_dir=table_dir,
    )
    print(json.dumps({"status": "COMPLETE", "scored_rows": len(scored), "pipelines": len(aggregates)}, indent=2))


if __name__ == "__main__":
    main()
