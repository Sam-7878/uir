# LAW-200

LAW-200 is a law-only benchmark for measuring whether typed UIR legal-entity verification reduces accepted unsupported citation claims without obtaining safety by rejecting all valid requests. It has two independent jurisdiction strata; their results must never be pooled as one N=200 experiment.

- **LAW-KR-200** — 대한민국 대법원 사건번호, 국가법령정보 공동활용 판례 API. Frozen test and all required pipelines are complete; the publication gate passes.
- **LAW-US-200** — U.S. case citations, CourtListener Citation Lookup v4. The implementation is ready, but source freeze and execution require `COURTLISTENER_API_TOKEN`.

The package implements the registered path:

`natural-language query → typed legal UIR → authoritative entity binding → retrieval/model → verified answer or safe rejection`

It is independent of the frozen Phase-4E/4F evidence. Those directories are never modified.

## Environment

- Ubuntu 26.04.1 under WSL2
- `/mnt/d/_Work/goat_bank/.venv/bin/python` (Python 3.12.13)
- Local Ollama primary model: `phi3.5:latest`
- Optional replication model: `qwen2.5:7b`
- Korean authoritative construction source: 국가법령정보 공동활용 판례 API
- U.S. authoritative construction source: CourtListener REST v4 citation lookup

The CourtListener token must exist only in the process environment:

```bash
export COURTLISTENER_API_TOKEN='...'
```

Never place the CourtListener token in a repository file, shell history, manifest, or result artifact. The Korean client reads `LAW_GO_KR_OC` or the ignored local credential file, redacts that value from official response links before persistence, and the validator scans the package for leakage.

## Korean reproduction (complete primary stratum)

The dataset is already frozen. Rebuilding performs live official API access and requires an explicit bug note when overwriting a freeze. Normal reproduction starts from execution/scoring:

```bash
PY=/mnt/d/_work/goat_bank/.venv/bin/python

$PY -m evaluation.uir_law.law200.run_law200 --jurisdiction kr --split dev
$PY -m evaluation.uir_law.law200.score_law200 --jurisdiction kr --split dev

$PY -m evaluation.uir_law.law200.run_law200 --jurisdiction kr --split test
$PY -m evaluation.uir_law.law200.score_law200 --jurisdiction kr --split test
$PY -m evaluation.uir_law.law200.kr.validate_publication_results
$PY -m evaluation.uir_law.law200.kr.generate_report
$PY -m evaluation.uir_law.law200.kr.update_kaic_docx
```

The Korean validator emits `READY_FOR_KAIC_MANUSCRIPT_KR` only when all source, leakage, split, raw-evidence, matched-configuration, recomputation, confidence-interval, and generated-table checks pass.

## U.S. reproduction (pending CourtListener token)

Run from the repository root (`/mnt/d/_Work/goat_bank/uir`) with the root virtual environment:

```bash
PY=/mnt/d/_Work/goat_bank/.venv/bin/python

$PY -m evaluation.uir_law.law200.builders.fetch_valid_citations
$PY -m evaluation.uir_law.law200.builders.generate_hard_negatives
$PY -m evaluation.uir_law.law200.builders.freeze_dataset

$PY -m evaluation.uir_law.law200.audits.audit_source_integrity
$PY -m evaluation.uir_law.law200.audits.audit_gold_access
$PY -m evaluation.uir_law.law200.audits.audit_dataset_duplicates

$PY -m evaluation.uir_law.law200.run_law200 --split dev
$PY -m evaluation.uir_law.law200.score_law200 --split dev
```

Only the development split may be used to diagnose parser/verifier behavior. After that review, run the frozen test once:

```bash
$PY -m evaluation.uir_law.law200.run_law200 --split test
$PY -m evaluation.uir_law.law200.score_law200 --split test
$PY -m evaluation.uir_law.law200.generate_report
$PY -m evaluation.uir_law.law200.validate_publication_results
```

The U.S. validator emits `READY_FOR_KAIC_MANUSCRIPT` only when all dataset, source, leakage, raw-evidence, matched-configuration, recomputation, confidence-interval, and auto-generated-table checks pass.

Long runs can be resumed with `--resume`. A frozen dataset cannot be overwritten unless `--force --bug-note "..."` records a software-defect reason; prior test evidence must be preserved separately before doing so.

## Outputs

Korean artifacts are namespaced under `data/kr/` and `results/kr/`:

- `data/kr/law200_test_runtime.jsonl` / `law200_test_gold.jsonl`
- `data/kr/source_registry.jsonl` and credential-redacted official responses
- `results/kr/raw/`, `results/kr/aggregate/`, `results/kr/tables/`
- `LAW200_KR_AUDIT_REPORT.md`, `LAW200_KR_REPORT.md`, and `KAIC_MANUSCRIPT_UPDATE_KR.md`

U.S. artifacts use the original un-namespaced paths once that stratum is built:

- `data/law200_test_runtime.jsonl` — model-visible opaque IDs and queries only
- `data/law200_test_gold.jsonl` — post-generation evaluation oracle
- `data/source_registry.jsonl` — hashed CourtListener records (60 status-200, 30 status-404)
- `data/corpus/legal_cases.jsonl` — one shared authoritative metadata corpus
- `results/raw/` — per-case prompts, raw outputs, timing, tokens, transitions
- `results/tables/law200_main_table.{csv,md}` — generated only from scored raw rows
- `results/aggregate/test_statistics.json` — exact McNemar, Holm, and risk differences
- `LAW200_AUDIT_REPORT.md` and `LAW200_REPORT.md`

See [LAW200_PROTOCOL.md](LAW200_PROTOCOL.md) and [DATASET_CARD.md](DATASET_CARD.md) for the frozen scientific contract and limitations.
