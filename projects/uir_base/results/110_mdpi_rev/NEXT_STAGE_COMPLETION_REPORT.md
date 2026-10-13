# Next-stage completion report — 2026-10-12 KST

Overall: **PARTIAL_COMPLETION / BLOCKED_FOR_SUBMISSION**, not all N00–N13 PASS.
Priority: Electronics / Generative AI, Large Language Models and Their Applications.
User-approved route B: original W08 NOT_SATISFIED; no actual human labels or author/institution approvals.

## Executed evidence

- Configured Python suite: 242 passed; Rust offline workspace log: 62 passed.
- Historical archive-only replay: 31 byte-identical scientific files; old 120 cases / 240 reviews replayed, 119 unresolved.
- Output-layer development: 600 requests / 272 Phi GPU calls. 251 stop, 21 length; five-required-field schema versus seven-bound-field scoring confounds ability/IR attribution.
- Supplementary AI review: 16 calibration + 16 holdout cases × two model families = 64 schema-valid responses; all 16+16 unresolved on at least one field.
- FinQA: 800 real requests on local RTX3090, no remote inference; independent archive-only case/summary replay identical.
- In-memory policy: six prohibited/four allowed opportunities per capable condition; enforcement zero prohibited execution/false denial; refuse-only four false denials.
- 500 legacy mutations / 1,500 gate decisions reconstructed; not recovered original mutation captures.

## FinQA strict adapter-defined endpoints

| Model | Condition | Correct | Finished | Adapter MISSING state |
|---|---|---:|---:|---:|
| Phi-3.5 | C1_NATIVE_ANSWER | 4/200 | 195/200 | 108/200 |
| Phi-3.5 | C8_ARITHMETIC_CONTRACT | 0/200 | 200/200 | 0/200 |
| Qwen3-1.7B | C1_NATIVE_ANSWER | 1/200 | 199/200 | 138/200 |
| Qwen3-1.7B | C8_ARITHMETIC_CONTRACT | 0/200 | 194/200 | 6/200 |

Not isolated reasoning accuracy or hallucination rates. Post-hoc diagnostics: 64 answer-marker-present responses rejected by strict end-anchored extraction; program-string JSON often describes arithmetic in prose rather than valid DSL. Percentage/benchmark-unit interpretation remains a confound. Primary scores and frozen raw captures are unchanged.

## Corrected historical findings

C8 224/418 complete + 48 partial = 272 coverage; deterministic trusted-slot control 272/418 complete. Control-only complete cases 48; C8-only 0. D1 legacy 206 complete / 125 unsupported becomes 74 / 326 under exact seven-field support, without raw changes. Old Phi HaluEval 72% was hardcoded; old Qwen 50% used a parse-failure default label. Native whole-output factuality is NOT_MEASURED.
Eligible recorded source families: 238, not 418 independent row hashes; unknown dependence and single-repetition latency limits are explicit.

## N00–N13 / W00–W15

| Task | Status | Original work | Scope / remaining work |
|---|---|---|---|
| N00 | PASS_SCOPED | W00,W04,W12 | Preserved historical inputs/evaluator; archive-only replay, not model rerun. |
| N01 | PASS | W01,W02,W03 | Literal labels, hardcoded aggregate and exact-field D1 transition traced to raw captures. |
| N02 | PASS_SCOPED | W02,W10 | Structured support and unassessed prose separated; native whole-output safety NOT_MEASURED. |
| N03 | PASS_SCOPED | W04,W07,W08 | Raw-only/trusted-slot paths separated; CPython payload/file tests, not host/native/inherited-FD isolation. |
| N04 | PASS_RESTRICTED_CNL | W07,W08 | Recursive condition AST/canonical identity/conformance; no general free-NL accuracy. |
| N05 | PARTIAL | W06 | C5 lineage and 272 fresh calls; five/seven-field confound; input/IR causal comparison not executed. |
| N06 | PASS_SCOPED | W11 | 238 recorded eligible source families; paired bootstrap; descriptive single-repetition latency. |
| N07 | PARTIAL_UNRELIABLE_CALIBRATION | W08 | 64 valid-schema reviews, 16+16 unresolved; fixture accuracy is not human semantic calibration. |
| N08 | PASS_ROUTE_B_ONLY | W08,W14 | User-approved AI-only amendment; original W08 NOT_SATISFIED, actual human/author approvals absent. |
| N09 | PARTIAL_ADAPTER_CONFOUNDED | W01,W09 | 800 real requests replayed; strict extraction, DSL syntax and unit effects confound attribution. |
| N10 | PASS_SYNTHETIC_CONFORMANCE_ONLY | W10 | In-memory action opportunities tested; seeded mutation reconstruction, not deployed prompt-injection robustness. |
| N11 | PASS_BOUNDED_POSITIONING | W05,W13 | Primary literature and negative controls retained; causal IR benefit remains unestablished. |
| N12 | PARTIAL_PROVISIONAL_DRAFT | W03,W13,W14 | Generated tables/compiled separate research draft; not full MDPI revision or author-approved declarations. |
| N13 | PARTIAL_SUBMISSION_BLOCKED | W00-W15 | Technical replay/negative tests do not replace remaining scientific gates or human/author confirmations. |

## Required work-order questions

1. HaluEval labels are replayed directly from historical raw text with missing/ambiguous states; D1 invokes the unchanged legacy pure scorer and independently compares seven exact fields. See metric_change_diagnostics.json, case_metric_transition.csv and halueval_extraction_audit.jsonl.
2. All 498 original C5 invocations have raw references/hashes; the 226 exclusions are common UIR pre-execution policy/entity decisions, not absent raw candidates. replay_exclusion_audit.csv gives each case and reason. All-candidate projection additionally avoids selection by C8 success; zero fresh replay calls does not make original generation free.
3. No necessity or incremental useful-answer benefit for SLM rendering is established; deterministic trusted-slot output wins completeness. The new five/seven-field mismatch prevents unbiased ability attribution. Input/IR comparison is still pending.
4. Raw-only CNL preserves typed NOT/AND/OR, Boolean/decimal comparisons, supported units and explicit conditions separately from system provenance. Unknown tokens/fields, incomplete operands and unsupported requests clarify rather than dropping predicates; conformance is not free-NL accuracy.
5. Effect sizes retain the same paired cases, but confidence intervals now resample 238 recorded families rather than 418 independent row hashes. Selected historical C8-minus-baseline complete-answer differences follow; all 18 comparisons/limits remain in paired_source_family_statistics.csv.

| Baseline | Paired difference | Family bootstrap 95% interval | Recorded families |
|---|---:|---|---:|
| C1_NAIVE_RAG | 0.004785 | [0.000000, 0.013761] | 238 |
| C5_GUARDRAIL_STYLE | 0.002392 | [0.000000, 0.008798] | 238 |
| D1_EXTERNAL_CONSTRAINED_DECODING | 0.358852 | [0.244055, 0.539799] | 238 |

6. Reviewer accuracy uses separate executable synthetic fixture labels only; model agreement is independently replayed, not treated as truth. No independent human semantic evidence exists; route B is approved and original W08 remains unmet.
7. Holdout inference and finite sandbox action traces were actually executed, not merely prepared. They are not an external deployed-agent attack benchmark or recovered original raw mutation run.
8. Extracted archive source reproduces 31 historical scientific files and new raw-to-metric scores with no development imports. This was performed by the current agent using separate replay code on the host interpreter, not by an independently appointed person/new machine and not a fresh GPU inference rerun.

## Reproducibility and files

Archive: docs/work_reports/uir_base/110_mdpi_rev/uir_next_source_evidence_v3.zip
SHA-256: aea0551d1b7e14cc98f5e8cfd32694cb9c1fcac25a700dee284c6d3c6814da76
Detached FINAL_RELEASE_RECEIPT.json binds the ZIP, result index and clean-room proof; release_gate.json separates integrity/replay/semantic/manuscript/submission gates. The archive contains scope docs, code, raw data, tests and captured result hashes; it excludes private paper bytes, model weights, secrets, Git internals and symlinks.
New source-linked research draft: docs/papers/_47_UIR_revision_next/draft_v4/. It is a provisional separate article, not full MDPI revision. Four result tables are generated; complete narrative numeric synchronization and actual PDF/source review remain pending. Original _47_UIR source is preserved.
Scope: implementation/matched_baseline_protocol.md, rubric_change_log.md, fresh_failure_analysis.md, claim_evidence_matrix.csv, journal_target_verification.md and backmatter_verification.md.

Archive-only replay with already installed CPU evaluation dependencies (no inference/network):

~~~bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
PYTHONPATH=src:. python -m projects.uir_base.scripts.next_verify \
  --archive docs/work_reports/uir_base/110_mdpi_rev/uir_next_source_evidence_v3.zip --extract-to /tmp/NEW-NONEXISTENT-UIR-CHECKOUT
python -m pytest -q
cargo test --workspace --offline
~~~

Python -I uses extracted source, not editable development imports; the installed interpreter/dependencies are shared with the host. This is archive-only code/data reproduction, not independent human or new-machine replication. GPU artifact/templates/decoding/timestamp evidence is retained, not a second inference run. Frozen protocol status labels remain their pre-execution snapshots; separate execution manifests establish completed inference.

## Remaining work

Next development must align schema/DSL/unit interpretation on declared development data and compare equivalent-input representation layers. Do not optimize or silently rerun the evaluated holdout. Any future confirmatory run requires a new protocol and unused holdout.
Actual author/institution confirmations, current Electronics instructions/template, publication rights/deposit, independent Clarivate/institution recognition and submission-day deadline/APC checks are pending. HTTP 429 limited publisher verification; search records are not a full live author-instructions check.
No commit/push, submission, public upload or payment performed; AI-only design does not guarantee publication.
