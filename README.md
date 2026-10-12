# UIR research repository

Typed execution contracts, policy enforcement and evidence-bound output validation
for language-model workflows. Three projects share one core and are integrated
on `main`:

- [uir_base](projects/uir_base): grounded financial answers and utility.
- [uir_security](projects/uir_security): security and zero-trust experiments.
- [uir_law](projects/uir_law): legal-domain evaluation.

## Canonical source layout

Shared Python sources have one physical location: `src/llm_trust` and
`src/uir_common`. Rust sources remain in the self-contained `crates` workspace.
Project evaluation, scripts and current results live under `projects/<project>`;
historical base results are under `archive/uir_base/results`.
Do not create root package copies or symbolic-link compatibility directories.
See [current layout](docs/architecture/PROJECT_LAYOUT.md) and
[Rust provenance](docs/architecture/RUST_PROVENANCE.md).

The shared import names remain `llm_trust` and `uir_common`. New project code
should import `projects.<project>.evaluation.<module>`. The small
`src/evaluation` namespace supports historical `evaluation.<module>` imports
from the same project source files without copying files or creating links.
It is a checkout compatibility adapter, not part of the domain-neutral core.

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

The next-stage audit, AI-only scope amendment, and explicitly local RTX3090 runs
are recorded in
[the N00–N13 implementation record](docs/work_reports/uir_base/110_mdpi_rev/implementation/README.md).
Its results are separately versioned as `mdpi_next_2026_10_11_v2`; historical
evidence is not replaced. Qwen3-1.7B is a newly selected generator comparison,
not a relabeling of Qwen2.5-7B or an independent human evaluator.

## Local verification

Use the environment specified in the parent workspace's `dev_env.md`.
On the current Ubuntu host, from this repository:

```bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest -q
cargo test --workspace
bash projects/uir_base/reproduce.sh verify
bash projects/uir_security/reproduce.sh verify
bash projects/uir_law/reproduce.sh verify
```

The installation command above assumes the shared environment already contains
dependencies. For a new environment use `python -m pip install -e '.[evaluation]'`.
After relocating the repository, reinstall from its new path; do not retain
the old location with a link.

`verify` checks recorded integrity, not scientific validity. The base
`tables` command regenerates revision rescoring/replay tables; it is not a
fresh model-inference campaign.

For the isolated RTX 3090 Ollama server, model installation and cross-family AI
review, see [local reviewer protocol](docs/work_reports/uir_base/107_Astra_review/LOCAL_AI_REVIEW_PROTOCOL.md)
and [execution status](docs/work_reports/uir_base/107_Astra_review/LOCAL_AI_REVIEW_STATUS.md).

## Release boundary

Code, tests, schemas, provenance and permitted raw evidence are public-release
candidates. Manuscripts, credentials, environments, model weights and unapproved
legal corpora are excluded. Check the staged file list and release permissions
before publishing. No remote publication is performed by these local commands.
