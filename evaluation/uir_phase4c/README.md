# Phase UIR-4C reproduction

All commands run from the `uir` repository root with the root Ubuntu Python environment.

```bash
export PYTHONPATH=.
PY=/mnt/d/_Work/goat_bank/.venv/bin/python

# 1. Freeze source-bound runtime/scoring partitions before generation.
$PY evaluation/uir_phase4c/freeze_inputs.py

# 2. Authenticity smoke and gate.
$PY evaluation/uir_phase4c/run_actual_baselines.py --stage smoke --batch-size 8
$PY evaluation/uir_phase4c/score_actual_evidence.py --stage smoke
$PY evaluation/uir_phase4c/detect_placeholder_evidence.py --stage smoke

# 3. Pre-registered 600 x 9 matched campaign.
$PY evaluation/uir_phase4c/run_actual_baselines.py --stage full --batch-size 8
$PY evaluation/uir_phase4c/score_actual_evidence.py --stage full

# 4. Official FinQA and HaluEval-QA actual inference and post-generation scoring.
$PY evaluation/uir_phase4c/run_official_benchmarks.py --benchmark all --batch-size 16
$PY evaluation/uir_phase4c/score_official_benchmarks.py

# 5. Authenticity, tests, publication gate, and report.
$PY evaluation/uir_phase4c/detect_placeholder_evidence.py --stage full --include-external
$PY -m pytest -q evaluation/uir_phase4c/test_phase4c_authenticity.py
$PY evaluation/uir_phase4c/publication_gate_phase4c.py
$PY evaluation/uir_phase4c/generate_phase4c_report.py
```

Generation is resumable at pipeline granularity. A complete pipeline capture is reused unless `--force` is passed. Scoring modules are deliberately separate from generation modules; generation runners never import a scorer or open a scoring/source file containing gold values.
