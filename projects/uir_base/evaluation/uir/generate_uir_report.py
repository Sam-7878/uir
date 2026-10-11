#!/usr/bin/env python3
"""Generate the research report from CSV/JSON results only."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))


def pct(value: str | float) -> str: return f"{float(value) * 100:.2f}%"
def num(value: str | float) -> str: return f"{float(value):.2f}"


def table(headers: list[str], rows: list[list[object]]) -> str:
    return "| " + " | ".join(headers) + " |\n|" + "|".join("---" for _ in headers) + "|\n" + "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--input", type=Path, default=Path("results/uir")); parser.add_argument("--dataset", type=Path, default=Path("evaluation/uir/fixtures/generated/dataset.jsonl")); parser.add_argument("--output", type=Path, default=Path("docs/work_reports/300_uir/REPORT.md")); args = parser.parse_args()
    manifest = json.loads((args.input / "run_manifest.json").read_text()); metrics = {item["metric"]: item for item in csv_rows(args.input / "metric_summary.csv")}; languages = csv_rows(args.input / "language_summary.csv"); categories = csv_rows(args.input / "category_summary.csv"); policy = csv_rows(args.input / "policy_summary.csv"); latency = csv_rows(args.input / "latency_summary.csv"); ablation = csv_rows(args.input / "ablation_summary.csv"); failures = (args.input / "failures.jsonl").read_text().splitlines()
    dataset = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]; composition = Counter((item["category"], item["language"]) for item in dataset)
    dataset_rows = [[category, composition[(category, "ko")], composition[(category, "en")], composition[(category, "ko")] + composition[(category, "en")]] for category in sorted({item["category"] for item in dataset})]
    report = f"""# UIR Evaluation Report

Generated exclusively from `results/uir` machine-readable artifacts. No result below is manually entered.

## 1. Objective

Evaluate deterministic Korean/English DSL compilation into a canonical UIR, default-deny policy and entity validation, AACO outcome mapping, verified-fact output constraints, component ablation, and runtime overhead.

## 2. Repository / Commit / Environment

- Commit: `{manifest['git_commit']}`
- Worktree dirty during run: `{manifest['worktree_dirty']}`
- OS: `{manifest['os']}`
- Rust: `{manifest['rustc_version']}`
- Python: `{manifest['python_version']}`
- Dataset seed/hash: `{manifest['dataset_seed']}` / `{manifest['dataset_hash']}`
- Cases: `{manifest['case_count']}`

## 3. UIR Architecture

Language-specific controlled DSL frontends emit one `UniversalIr` model. `poa-protocol` supplies deterministic canonicalization and policy digesting; validation and EffectivePolicy evaluation precede the AACO adapter; only Commit reaches the verified executor and mock renderer; structured claims are checked against a provenance-bearing fact set.

## 4. Dataset Composition

{table(['Category', 'KO', 'EN', 'Total'], dataset_rows)}

## 5. Evaluation Metrics

{table(['Metric', 'Value', '95% CI'], [[name, pct(row['value']), f"[{pct(row['ci95_low'])}, {pct(row['ci95_high'])}]" if row['ci95_low'] else 'n/a'] for name, row in metrics.items()])}

## 6. DSL Parsing Results

{table(['Language', 'Cases', 'Semantic match', 'Outcome accuracy'], [[row['language'], row['cases'], pct(row['semantic_match']), pct(row['outcome_accuracy'])] for row in languages])}

## 7. Cross-Lingual UIR Equivalence

Observed semantic-digest equivalence: {pct(metrics['cross_lingual_equivalence_rate']['value'])} ({metrics['cross_lingual_equivalence_rate']['successes']}/{metrics['cross_lingual_equivalence_rate']['total']}), Wilson 95% CI [{pct(metrics['cross_lingual_equivalence_rate']['ci95_low'])}, {pct(metrics['cross_lingual_equivalence_rate']['ci95_high'])}].

## 8. Policy Decision Results

{table(['Policy level', 'Cases', 'Accuracy', 'FAR', 'FRR'], [[row['policy_level'], row['cases'], pct(row['accuracy']), pct(row['far']), pct(row['frr'])] for row in policy])}

## 9. Invalid Entity Rejection

Observed prevention rate: {pct(metrics['invalid_entity_fabrication_prevention_rate']['value'])}; Wilson 95% CI [{pct(metrics['invalid_entity_fabrication_prevention_rate']['ci95_low'])}, {pct(metrics['invalid_entity_fabrication_prevention_rate']['ci95_high'])}]. This is an observed controlled-dataset result, not a population guarantee.

## 10. Output Contract Validation

Detected unsupported claim rate among generated factual claims: {pct(metrics['unsupported_claim_rate']['value'])}. Post-validation unsupported-claim acceptance rate: {pct(metrics['unsupported_claim_acceptance_rate']['value'])}, Wilson 95% CI [{pct(metrics['unsupported_claim_acceptance_rate']['ci95_low'])}, {pct(metrics['unsupported_claim_acceptance_rate']['ci95_high'])}]. Rejected policy/entity paths recorded zero renderer invocations by construction and test.

## 11. Ablation Study

{table(['Configuration', 'Outcome acc.', 'Semantic match', 'Policy acc.', 'Invalid reject', 'UCR', 'Mean us'], [[row['configuration'], pct(row['outcome_accuracy']), pct(row['semantic_match']), pct(row['policy_accuracy']), pct(row['invalid_reject_rate']), pct(row['unsupported_claim_rate']), num(row['latency_mean_us'])] for row in ablation])}

## 12. Latency and Overhead

{table(['Stage', 'Mean', 'P50', 'P95', 'P99'], [[row['stage'], num(row['mean']), num(row['p50']), num(row['p95']), num(row['p99'])] for row in latency])}

## 13. Confidence Intervals

All ratio metrics with binomial counts use two-sided Wilson 95% intervals. A zero observed failure is reported with its finite-sample upper bound.

## 14. Failure Analysis

Failure records: {len(failures)}. Details are retained in `results/uir/failures.jsonl`.

## 15. Architecture Invariant Results

ARCH-UIR-001 through ARCH-UIR-010 are enforced by `evaluation/check_architecture.py`; behavioral invariants are covered by `poa-uir` tests.

## 16. Reproducibility Commands

```bash
source /mnt/d/_Work/goat_bank/.venv/bin/activate
python evaluation/uir/run_all.py --seed {manifest['dataset_seed']}
cargo test --workspace --all-features
python evaluation/check_architecture.py
```

## 17. Limitations

The frontend is deterministic controlled language, not production NLP. Entity/fact data and rendering are fixtures, not live registries or Phi-3.5. Ablation A0-A5 is a deterministic component replay over the same cases; A6 is the measured Rust pipeline. Latency on WSL2 is environment-specific. GATv2/XBRL and claims of causal attribution are intentionally excluded.
"""
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(report, encoding="utf-8", newline="\n"); print(args.output)


if __name__ == "__main__": main()
