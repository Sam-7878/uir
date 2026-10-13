# Next revision implementation

Task date: 2026-10-11; execution began 2026-10-11 and continued 2026-10-12 (Asia/Seoul).

The user explicitly approved route B (AI-only) in this task. Original W08 is
NOT_SATISFIED; no human validation, expert gold, general natural-language
accuracy, or statistically independent AI errors are claimed. The old 240
review responses remain frozen. This is not submission approval.

Current entrypoints use Ubuntu and the parent `.venv_cuda`. No symbolic links,
weights, private keys, or automatic model downloads belong in the release.

```bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
python -m projects.uir_base.scripts.next_release --out /path/to/fresh/output
python -m projects.uir_base.scripts.next_release --out /path/to/output --package /path/to/new/archive.zip
python -m projects.uir_base.scripts.next_gpu_matched --prepare
python -m projects.uir_base.scripts.next_gpu_matched --execute
```

The first command is OFFLINE: source-byte checks, raw capture reanalysis, case
transitions, candidate provenance, actual source-family clustering and synthetic
conformance. Scientific outputs must reproduce exactly. Creation timestamps,
environment inventory and test durations are the only declared nondeterministic
metadata, not permission to ignore metric changes.

The two GPU commands are explicit local inference. Local Ollama is an on-device
runtime for existing GGUF files, not a separate remote inference server.
`scripts/serve_local_models.sh` selects the RTX3090 UUID, disables cloud inference,
and leaves the existing 11434 system service unchanged. Port 18747 is only local
IPC. Same tags with different digest/template/quantization are different runs.
The new Q4_0 run is NOT an equivalent rerun of historical FP16/NF4 inference.

New results live in `projects/uir_base/results/mdpi_next_2026_10_11_v2`.
The initial offline prototype remains separately in `mdpi_next_2026_10_11`.
Never rerun a completed release into the same output folder. Original evaluator,
reviewer, raw captures, templates and paper/BibTeX bytes remain untouched.

Publication, source-family completeness, semantic scope, fresh inference,
annotation accuracy, manuscript compilation, and author declarations have
separate gates. A file's existence is not a completed scientific gate.
