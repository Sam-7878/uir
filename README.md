# UIR research repository

Typed execution contracts, policy enforcement and evidence-bound output validation
for language-model workflows. This is a shared research repository with three
project-specific evaluation portals:

- [uir_base](projects/uir_base): grounded financial answers and utility.
- [uir_security](projects/uir_security): security and zero-trust experiments.
- [uir_law](projects/uir_law): legal-domain evaluation.

Shared Python sources live in `src/llm_trust` and `src/uir_common`; Rust sources
remain in the self-contained `crates` workspace. Project-specific evaluation,
scripts and results live under `projects/<project>`. Historical paths remain
symlink aliases. See [current layout](docs/architecture/PROJECT_LAYOUT.md) and
[Rust provenance](docs/architecture/RUST_PROVENANCE.md).

## Evidence and claim boundaries

Historical results are preserved, not automatically certified. The current base
revision independently rescores raw case-level evidence and distinguishes complete
answers, macro/micro recall, unsupported structured claims, unassessed prose,
contract validity and end-to-end correctness. A finite zero-event observation is
not a general guarantee of hallucination elimination. GAT attention weights do
not establish root-cause causality, and the current base revision does not train
or rely on GNN/hybrid-graph tensors.

New base revision evidence is under
`projects/uir_base/results/mdpi_revision_2026_10_11/`; its work order and reports
are under `docs/work_reports/uir_base/107_Astra_review/`. Refer to case-level source
hashes and evaluator definitions before citing a number. AI review is not human
annotation or automatic submission approval.

## Local verification

Use the environment specified in the parent workspace's `dev_env.md`. On the
current host:

```bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
cd /mnt/d/_Work/goat_bank/uir
python -m pytest -q
cargo test --workspace
bash projects/uir_base/reproduce.sh verify
bash projects/uir_base/reproduce.sh tables
```

`verify` checks recorded integrity, not scientific validity. `tables` regenerates
revision rescoring/replay tables; it is not a fresh model-inference campaign.

For the isolated RTX 3090 Ollama server, model installation and cross-family AI
review, see [local reviewer protocol](docs/work_reports/uir_base/107_Astra_review/LOCAL_AI_REVIEW_PROTOCOL.md)
and [execution status](docs/work_reports/uir_base/107_Astra_review/LOCAL_AI_REVIEW_STATUS.md).

## Release boundary

Code, tests, schemas, provenance and permitted raw evidence are public-release
candidates. Manuscripts, credentials, environments, model weights and unapproved
legal corpora are excluded. Check the staged file list and release permissions
before publishing. No remote publication is performed by these local commands.
