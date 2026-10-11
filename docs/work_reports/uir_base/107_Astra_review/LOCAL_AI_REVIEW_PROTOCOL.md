# Local cross-family AI reviewers — 2026-10-11

## Decision and evidence boundary

The user approved Qwen3-4B and Mistral AI's Ministral 3 14B Instruct. The earlier
Qwen3-1.7B proposal is cancelled; it is not installed by this workflow.

Use `AI_J1` and `AI_J2`, never `H1` or `H2`, for their outputs. Separate contexts
and different model families provide cross-family triangulation; they do not
establish statistically independent errors, human expertise, or human ground truth.
The original W08 human-review requirement remains unsatisfied. Changing to an
AI-only study requires explicit, appropriately limited manuscript claims rather
than recording that human review occurred. Author/ethics declarations also remain
pending; AI execution does not resolve them.

## Models and local execution

| Role | Upstream model | Ollama tag | License |
|---|---|---|---|
| Answer generator | Microsoft Phi-3.5-mini-instruct | `phi3.5:latest` | MIT |
| AI_J1 | Qwen/Qwen3-4B-Instruct-2507 | `qwen3:4b-instruct-2507-q4_K_M` | Apache-2.0 |
| AI_J2 | mistralai/Ministral-3-14B-Instruct-2512 | `ministral-3:14b` | Apache-2.0 |

The installed Ollama variants are quantized GGUF artifacts, not the upstream
BF16/FP8 checkpoints. Save actual quantization, digest, prompt-template and license
hashes in each run. Mutable tags alone are insufficient for reproduction; compare
installed digests to the manifest before interpreting a rerun.
Inspection found that Ollama's mutable `qwen3:4b` alias now points to
Qwen3-4B-Thinking-2507, not the original hybrid model. Its downloaded cache is not
the selected reviewer. Use the explicit Instruct-2507 tag above. The original
alias installation/smoke attempt is diagnostic and must not supply AI_J1 labels.

Use the requested `.venv_cuda` Python. The local server runs on `127.0.0.1:18747`
with cloud inference disabled and RTX 3090 selected by GPU UUID. The original system
service/11434 configuration is not modified. Weights are stored under ignored
`local_storage/ollama/models`; no weights or private keys belong in public Git.
Load one model at a time. Set 8,192 context tokens initially; do not infer that the
model's advertised maximum context fits on this GPU.

```bash
bash scripts/serve_local_models.sh
```

In another WSL terminal:

```bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
cd /mnt/d/_Work/goat_bank/uir
python -m projects.uir_base.scripts.setup_local_models
python -m projects.uir_base.scripts.run_local_ai_review --prepare-only
python -m projects.uir_base.scripts.run_local_ai_review
```

CLI access to this isolated server (without changing the existing system service):

```bash
OLLAMA_HOST=127.0.0.1:18747 ollama list
OLLAMA_HOST=127.0.0.1:18747 ollama run qwen3:4b-instruct-2507-q4_K_M
OLLAMA_HOST=127.0.0.1:18747 ollama run ministral-3:14b
```

Installation/smoke evidence is saved under
`projects/uir_base/results/mdpi_revision_2026_10_11/local_models/<run>/`.
An operational smoke test is NOT calibration of reviewer accuracy.

## Annotation protocol

Use the already prepared post-hoc stratified 120-case subset: 10 cases per
stratum/language group where available. It is not a new prospective holdout.
Each reviewer sees the identical raw input, candidate UIR and authoritative policy
rules, but neither evaluation gold, historical AI labels, other reviewer results,
nor human labels. A process audit hook denies opening gold/scoring/human-label
files. Fresh per-case messages contain no conversation history and no tools.
Case IDs are replaced by opaque hashes in model-visible packets, because original
IDs can expose strata such as adversarial cases. The evaluator-only mapping is
not included in prompts. This is blinding against labels/strata, not against the
meaning of the raw request itself.

The candidate is produced by the historical compiler with trusted runtime slot
metadata. Therefore this review can identify candidate/text discrepancies but
cannot establish end-to-end accuracy of an unconstrained natural-language parser.
Do not feed trusted candidate slots back as a correct reference. Explicit condition
scope must be assessed separately from the compiler's default provenance condition.
Policy decisions concern the supplied finite policy rules, not real-world legal
or regulatory correctness. This review is not factual verification of SEC sources.

Freeze rubric, response schema, sampling manifest, source/compiler/policy hashes,
token budget, seed, thinking setting and model digests before model review. The
selected Qwen checkpoint is the non-thinking Instruct-2507 model; temperature 0 is an operational repeatability setting,
not an assertion of optimal model quality. Both reviewers have the same output
budget of 512 tokens. No prompt adjustment or cherry-picked rerun on reviewed cases.

Each raw response is retained, including finish reason, token counts and failures.
Require strict JSON/schema validity and literal source quotes. An invented quote,
truncation, failed request or missing response becomes invalid, not a default label.
Record per-field uncertainty; agreement does not make a label true.

Report paired raw agreement, jointly valid N, full-packet valid-agreement rate,
missing/invalid pairs, per-field confusion counts and Cohen's kappa. Kappa is
undefined for degenerate all-one-class marginals; never force it to 1. Two invalid
responses are not agreement. Two reviewers do not supply a majority on a tie.
Report jointly uncertain agreement separately from decisive agreement.
Disagreements and uncertainty remain unresolved pending independent adjudication.

Outputs live only under `.../ai_reviews/<run>/`. Do not change `human_labels.csv`,
`adjudication.csv`, historical R1/R2/R3 reviews or old publication gates.

## Acceptable reporting

After successful capture, report: "A post-hoc stratified subset was additionally
reviewed by two locally executed AI models from different model families, using
isolated contexts and a fixed rubric. No human annotation was performed."

Do not report "two independent human evaluators", "human-validated gold",
"expert adjudication", or statistically independent model errors. AI agreement
is supplementary evidence and must not automatically certify submission readiness.

## Primary sources checked

- [Qwen3-4B-Instruct-2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [Ollama Qwen3 tags and version distinctions](https://ollama.com/library/qwen3/tags)
- [Ministral 3 14B Instruct model card](https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512)
- [Ollama Ministral 3 14B package](https://ollama.com/library/ministral-3:14b)
- [LLM-as-a-judge limitations](https://arxiv.org/abs/2306.05685)
- [Ollama chat API](https://docs.ollama.com/api/chat)
