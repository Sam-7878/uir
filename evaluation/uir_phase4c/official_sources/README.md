# Frozen official sources

Phase UIR-4C vendors only the public evaluation files and licenses needed for exact case-level reproduction.

| Dataset | Upstream | Commit | Frozen file |
|---|---|---|---|
| FinQA | `https://github.com/czyssrs/FinQA` | `0f16e2867befa6840783e58be38c9efb9229d742` | `FinQA/test.json` |
| HaluEval | `https://github.com/RUCAIBox/HaluEval` | `b7253db3cdaa0ab2c382f92b26b390109174f77e` | `HaluEval/qa_data.json` |

The corresponding upstream licenses are stored beside the data. `FinQA/evaluate.py` is the unmodified official evaluator from the same FinQA commit. File SHA-256 values are recorded in `results/uir_phase4c/OFFICIAL_BENCHMARK_PROVENANCE.json`.

