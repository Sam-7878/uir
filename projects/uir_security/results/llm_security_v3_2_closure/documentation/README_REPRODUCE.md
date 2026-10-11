# Reproduce the V3.2 closure

Use the Ubuntu distribution (verified Ubuntu 26.04.1), with the workspace-root Python 3.12.13 virtual environment. The installed Ollama executable observed in this session is `/usr/local/bin/ollama`; the user's former `/snap/bin/ollama` path is absent. Existing local models are `qwen2.5:7b` and `phi3.5:latest`. No reinstall is needed.

```bash
cd /mnt/d/_work/goat_bank/uir
source /mnt/d/_work/goat_bank/.venv/bin/activate
python -m pytest tests/security_v3_2 tests/security_v3 tests/security_v3_1 tests/test_llm_trust.py -q
python -m pytest tests -q
python -m evaluation.llm_security_v3_2.closure_campaign --prepare-only
python docs/security_v3_2/audit/benign_long_supplement.py --prepare-only
python -u -m evaluation.llm_security_v3_2.closure_campaign
python -u docs/security_v3_2/audit/benign_long_supplement.py
python -u docs/security_v3_2/audit/finalize_closure.py
python -m evaluation.llm_security_v3_2.validate_publication_results --strict
```

Output: `results/llm_security_v3_2_closure/`. The interrupted 240-case artifacts remain in their original location and in `results/llm_security_v3_2_interrupted_20260908/`. They must not be combined with new evidence.

The runner checkpoints each complete case, rejects changed code/config/input on resume, has no deterministic fallback, and records execution failure rather than substituting an answer. Primary: 850 × 6. HETE secondary model: same 850. Ablations: 12 × 850. Adaptive: six × 30 seeds, B=20. Stochastic: five seeds on the same preregistered 30 cases. Runtime values must be read from actual manifests and request records.

`SOURCE_AMENDMENT_01.json` and `SOURCE_AMENDMENT_02.json` are mandatory parts of the evidence history. They bind the two validity repairs, source epochs, preserved records, and before/after hashes. A reproduction from the current source uses epoch 2 directly; it must not delete or relabel the preserved execution history of this run.

A finished inference process is not publication approval. Complete raw checks, specialized-report reconstruction, source/artifact hashing, manuscript generation, and a clean LaTeX/BibTeX build are required. Strict validation intentionally fails for an incomplete package.

```bash
cd docs/papers/_47_1_UIR_for_ZTA
pdflatex -interaction=nonstopmode -halt-on-error _47.1_UIR_ZTA.tex
bibtex _47.1_UIR_ZTA
pdflatex -interaction=nonstopmode -halt-on-error _47.1_UIR_ZTA.tex
pdflatex -interaction=nonstopmode -halt-on-error _47.1_UIR_ZTA.tex
```
