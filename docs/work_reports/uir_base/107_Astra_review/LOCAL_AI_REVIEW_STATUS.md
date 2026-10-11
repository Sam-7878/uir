# Local AI model installation and review status — 2026-10-11

## Installed and GPU verified

All three selected artifacts are installed in WSL. The RTX 3090 is selected for
local Ollama on port 18747; the existing port-11434 service is unchanged. Both
reviewer models passed English instruction, Korean arithmetic, and constrained
JSON operational probes at 8,192 context tokens. These probes do not establish
their semantic-review accuracy.

| Role | Actual artifact | Quantization | Artifact digest |
|---|---|---|---|
| Generator | `phi3.5:latest` | Q4_0 | `61819fb370a3c1a9be6694869331e5f85f867a079e9271d66cb223acb81d04ba` |
| AI_J1 | `qwen3:4b-instruct-2507-q4_K_M` | Q4_K_M | `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` |
| AI_J2 | `ministral-3:14b` | Q4_K_M | `4760c35aeb9d9e9c6174c2492562c0b999e80a222804fd96b1915ab72bbcdcf7` |

Selected-artifact installation evidence:
`projects/uir_base/results/mdpi_revision_2026_10_11/local_models/20261011T113904Z/installation_manifest.json`.
The manifest, API outputs, template/license hashes and GPU allocation snapshots
are retained. Weights are excluded from Git.

Phi's English strict-format probe failed because it returned READY followed by an
explanatory paragraph. Its Korean arithmetic and constrained-JSON probes passed.
The aggregate status is therefore `INSTALLED_GPU_VERIFIED_WITH_SMOKE_PROBE_WARNINGS`,
not an unqualified all-probes-pass result. No prompt was tuned to hide this warning.

The earlier mutable `qwen3:4b` download is a Thinking-2507 artifact, not the selected
reviewer. Its cached weights and diagnostic attempt are retained but excluded from
the actual reviewer run. Qwen3-1.7B was not installed. These new quantized artifacts
must not be presented as an exact rerun of historical FP16 experiments.

## Actual AI review

Status: `AI_REVIEW_CAPTURE_COMPLETE_NOT_HUMAN_VALIDATION`.

Run: `projects/uir_base/results/mdpi_revision_2026_10_11/ai_reviews/20261011T114157Z/`.
Each reviewer completed 120 cases; all 240 responses passed strict schema, literal
quote and finish-reason validation. No retry or prompt adjustment was used for
these reviewed cases. Schema validity is not semantic correctness.

| Field | Agree / 120 | Raw agreement | Cohen's kappa |
|---|---:|---:|---:|
| Intent | 86 | 71.67% | 0.413793 |
| Entity | 107 | 89.17% | 0.682862 |
| Attribute | 101 | 84.17% | 0.587330 |
| Period | 113 | 94.17% | 0.809481 |
| Conditions preservation | 83 | 69.17% | 0.172260 |
| Policy decision | 77 | 64.17% | 0.355000 |
| Ambiguity | 26 | 21.67% | -0.020814 |

Joint uncertainty accounts for 19 intent agreements and 23 ambiguity agreements.
Decisive ambiguity agreement is only 3/120. The unresolved union is **119/120**
cases with at least one disagreement or uncertain judgment across seven fields.
This is NOT 119 system errors: there is no independent truth label establishing
which reviewer is correct, and rater/rubric interpretation can differ. Do not use
these outputs as automatic ground truth or claim human-equivalent validation.
The run was not tuned/rerun to inflate agreement after observing this result.

Report these as descriptive results on a post-hoc subset, not statistical
independence of cases/model errors or demonstrated reviewer accuracy. There is no
two-rater majority for unresolved ties. Preserve all original judgments.

Artifacts include `AI_J1_raw_reviews.jsonl`, `AI_J2_raw_reviews.jsonl`,
`AI_labels.csv`, `AI_agreement.csv`, `AI_agreement.json`,
`AI_unresolved_cases.json`, `review_manifest.json` and `verification_report.json`.

The separate verifier replays paired agreement using exact rational arithmetic and
checks source/code/output hashes, reconstructed isolated prompts, case coverage,
strict response validity and raw-label correspondence. Its pass is integrity and
statistics replay, not factual/semantic validation of AI judgments.

```bash
python -m projects.uir_base.scripts.verify_local_ai_review \
  projects/uir_base/results/mdpi_revision_2026_10_11/ai_reviews/20261011T114157Z
```

The existing post-hoc stratified 120-case packet is reviewed once per AI model, in
isolated contexts with an identical frozen rubric and schema. Model-visible case
IDs are opaque; gold/scoring/human-label file access is blocked by a process audit
hook. Actual responses, finish reasons, token counts, failures and disagreements
are retained. See `LOCAL_AI_REVIEW_PROTOCOL.md` for scope and reproduction commands.

## Submission and annotation boundary

Human review completed: **false**. Original W08 human requirement satisfied:
**false**. Author/ethics confirmation: **pending**.

The additional result is cross-family AI validation, not two human evaluators,
human ground truth, expert adjudication or statistical independence of errors.
No historical review, human-label file, manuscript source or publication gate is
overwritten. The existing manuscript and bibliography hashes remain unchanged.

Python regression tests: **170 passed**. The gold-boundary diagnostic passes for
600 runtime contracts while actively rejecting access to evaluation gold.
