# Installation and Environment

The three projects share this repository but have distinct scientific dependency and evaluation requirements. **Fast `verify`** requires Python 3.11 or newer and the standard library:

```bash
python scripts/reproduce_project.py uir_base verify
python scripts/reproduce_project.py uir_security verify
python scripts/reproduce_project.py uir_law verify
```

## Environment Setup

On the host system, use the shared environment specified in the parent workspace `dev_env.md`:

```bash
# Activate workspace Python environment
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate

# Install shared Python packages in editable mode
python -m pip install --no-deps --no-build-isolation -e .

# Run test suites
python -m pytest -q
cargo test --workspace
```

For evaluation dependencies (e.g., jsonschema, scipy, matplotlib):

```bash
python -m pip install -e '.[evaluation]'
```

## Project Entry Points

- [uir_base](projects/uir_base/README.md): Grounded financial question answering and utility contracts.
- [uir_security](projects/uir_security/README.md): Cybersecurity, capability enforcement, and HETE zero-trust experiments.
- [uir_law](projects/uir_law/README.md): Legal-domain knowledge retrieval and compliance benchmarks.

Historical developmental evidence is preserved under `archive/<project>/results/`.
