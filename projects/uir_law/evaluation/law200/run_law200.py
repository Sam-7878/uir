#!/usr/bin/env python3
"""Execute matched LAW-200 pipelines without loading evaluation labels."""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from evaluation.uir_law.law200.baselines import PIPELINES
from evaluation.uir_law.law200.baselines.core import run_pipeline
from evaluation.uir_law.law200.common import (
    CORPUS_DIR,
    DATA_DIR,
    PACKAGE_ROOT,
    RAW_DIR,
    RESULTS_DIR,
    append_jsonl,
    environment_manifest,
    read_jsonl,
    sha256_file,
    utc_now,
    write_json,
)
from evaluation.uir_law.law200.model import ModelConfig, OllamaModel


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def execute(
    split: str,
    pipelines: list[str],
    config: ModelConfig,
    limit: int | None,
    resume: bool,
    jurisdiction: str = "us",
) -> list[Path]:
    data_dir = DATA_DIR if jurisdiction == "us" else DATA_DIR / "kr"
    corpus_dir = CORPUS_DIR if jurisdiction == "us" else data_dir / "corpus"
    raw_dir = RAW_DIR if jurisdiction == "us" else RESULTS_DIR / "kr" / "raw"
    runtime_path = data_dir / f"law200_{split}_runtime.jsonl"
    registry_path = data_dir / "source_registry.jsonl"
    corpus_path = corpus_dir / "legal_cases.jsonl"
    for path in (runtime_path, registry_path, corpus_path):
        if not path.exists():
            raise FileNotFoundError(f"required frozen input missing: {path}")
    access_log = {
        "started_at": utc_now(),
        "pre_generation_files_read": [
            {"path": str(runtime_path.relative_to(PACKAGE_ROOT)), "sha256": sha256_file(runtime_path)},
            {"path": str(registry_path.relative_to(PACKAGE_ROOT)), "sha256": sha256_file(registry_path)},
            {"path": str(corpus_path.relative_to(PACKAGE_ROOT)), "sha256": sha256_file(corpus_path)},
        ],
    }
    write_json(raw_dir / f"{split}_pre_generation_access_log.json", access_log | {"jurisdiction": jurisdiction})
    cases = read_jsonl(runtime_path)
    registry = read_jsonl(registry_path)
    corpus = read_jsonl(corpus_path)
    if limit is not None:
        cases = cases[:limit]
    model = OllamaModel(config)
    model_identity = model.show()
    run_manifest = {
        "benchmark": "LAW-200",
        "split": split,
        "started_at": utc_now(),
        "environment": environment_manifest(),
        "model_config": config.to_dict(),
        "model_identity": model_identity,
        "runtime_sha256": sha256_file(runtime_path),
        "source_registry_sha256": sha256_file(registry_path),
        "corpus_sha256": sha256_file(corpus_path),
        "pipelines": pipelines,
        "case_count": len(cases),
    }
    run_manifest["jurisdiction"] = jurisdiction
    write_json(raw_dir / f"{split}_execution_manifest_{slug(config.model)}.json", run_manifest)
    output_paths: list[Path] = []
    for pipeline in pipelines:
        output_path = raw_dir / f"{split}_{pipeline}_{slug(config.model)}.jsonl"
        if output_path.exists() and not resume:
            raise RuntimeError(f"output exists: {output_path}; pass --resume or move it aside")
        completed = {
            row["case_id"] for row in read_jsonl(output_path)
        } if resume and output_path.exists() else set()
        started = time.perf_counter()
        for index, case in enumerate(cases, 1):
            if case["case_id"] in completed:
                continue
            case_started = time.perf_counter_ns()
            result = run_pipeline(pipeline, case, registry, corpus, model)
            result.update({
                "executed_at": utc_now(),
                "pipeline_latency_ms": (time.perf_counter_ns() - case_started) / 1_000_000,
                "model_config": config.to_dict(),
                "model_identity": model_identity,
            })
            append_jsonl(output_path, result)
            if index % 10 == 0 or index == len(cases):
                elapsed = time.perf_counter() - started
                print(f"[{pipeline}] {index}/{len(cases)} elapsed={elapsed:.1f}s", flush=True)
        output_paths.append(output_path)
    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--jurisdiction", choices=("us", "kr"), default="us")
    parser.add_argument("--pipelines", nargs="+", choices=PIPELINES, default=list(PIPELINES))
    parser.add_argument("--model", default="phi3.5:latest")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-tokens", type=int, default=192)
    parser.add_argument("--seed", type=int, default=20260911)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config = ModelConfig(
        model=args.model,
        endpoint=args.endpoint,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        seed=args.seed,
    )
    paths = execute(args.split, args.pipelines, config, args.limit, args.resume, args.jurisdiction)
    print(json.dumps({"status": "COMPLETE", "outputs": [str(path) for path in paths]}, indent=2))


if __name__ == "__main__":
    main()
