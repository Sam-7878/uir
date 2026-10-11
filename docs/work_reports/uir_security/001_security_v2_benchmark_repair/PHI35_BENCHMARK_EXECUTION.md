# Phi-3.5 Security Benchmark v2 Execution Record

## Runtime verification

On Ubuntu 24.04 with the repository-root virtual environment, the locally cached
`microsoft/Phi-3.5-mini-instruct` snapshot successfully loaded with CUDA NF4
quantization and returned `READY` for a deterministic four-token probe.

The cached Phi remote-code revision is incompatible with the current
`transformers` `DynamicCache` API. The publication runner therefore uses the
current Transformers native Phi3 implementation with PyTorch SDPA and KV
cache against the exact same local checkpoint. A uniform 2,048-token model
input ceiling prevents infrastructure OOM on resource-exhaustion prompts; the
actual tokens sent and latency remain observable benchmark metrics. These are
runtime compatibility/resource settings, not a fallback model or checkpoint
change.

## Required publication run

Run these commands from Ubuntu 24.04.  They use the local Hugging Face snapshot;
they do not call Ollama and do not download a model.

```bash
cd /mnt/d/_Work/goat_bank/uir
source /mnt/d/_Work/goat_bank/.venv/bin/activate

python -m evaluation.llm_security.audit_dataset \
  evaluation/llm_security/datasets/security_benchmark_v2_development.jsonl \
  --output results/llm_security_v2/dataset_audit.json
python -m evaluation.llm_security.run_security_benchmark_v2 \
  --backend phi35-transformers --runs 3
python -m evaluation.llm_security.run_ablation_study_v2 \
  --backend phi35-transformers --runs 3
python -m evaluation.llm_security.run_multi_knockout \
  --backend phi35-transformers --runs 3
python -m evaluation.llm_security.validate_results \
  --results results/llm_security_v2 --require-publication-eligible
python -m evaluation.llm_security.generate_security_report_v2
```

`results/llm_security_v2/benchmark_metrics_summary.json` is the source of truth
for `publication_eligible`.  Do not cite results in an SCI manuscript unless the
three production runners and the strict validator all succeed.

## Current evidence boundary

Only an actual one-prompt runtime probe and a separate deterministic-fallback
pipeline smoke test have been completed during this repair task.  The fallback
smoke artifacts are intentionally marked `publication_eligible: false`; they are
implementation-validation artifacts, not Phi-3.5 benchmark evidence.
