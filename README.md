HETE employs a two-tier compilation pipeline: language-specific frontends for agglutinative (e.g., Korean particle/ending-based) and analytic/inflected (e.g., English imperative/prepositional) natural language inputs transpile queries into a standardized, machineexecutable
Universal Intermediate Representation (UIR) formatted as a JSON Abstract Syntax Tree (AST). Prior to inference, a deterministic policy engine evaluates multi-layered enterprise constraints (L0–L3) directly on the UIR to enforce hard-stop or graceful degradation rules. Furthermore, HETE integrates
a Graph Attention Network (GATv2) operating over financial (XBRL calculation linkbases) and legal knowledge Directed Acyclic Graphs (DAGs) to extract mathematically verifiable rootcause causality via attention weights (α). Injected as immutable
ground truth, this mathematical context binds the local SLM to zero-trust compliance. Comprehensive benchmark evaluations across 1,000 real-world and adversarial test cases demonstrate that HETE achieves a 0.0% hallucination rate and 100.0% factconsistency,
while reducing average inference latency to 5.38 s on a single 8GB VRAM GPU via 4-bit quantization, outperforming Naive RAG by a factor of three.

## Python source layout

The shared `llm_trust` package has one canonical source directory:
`src/llm_trust`. Do not create root-level copies or symbolic-link aliases.
The import name remains `llm_trust`.

From the repository root, using the existing Ubuntu virtual environment:

```bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest tests/test_package_layout.py tests/uir_security/test_llm_trust.py
```

For a new environment, install dependencies with `python -m pip install -e '.[test]'`.
After relocating this repository, reinstall from its new path; do not retain
the old location with a link. See [the architecture guide](docs/architecture/REPOSITORY_PROJECT_STRUCTURE.md)
for evaluation imports and data-dependent test requirements.
