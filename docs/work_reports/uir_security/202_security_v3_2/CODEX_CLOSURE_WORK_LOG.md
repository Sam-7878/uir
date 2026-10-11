# Codex V3.2 continuation log

Status: COMPLETE. The full-population execution, benign-length supplement, manuscript build, artifact reconstruction, and independent strict publication-evidence gate all passed.

The current workspace is Ubuntu 26.04.1, root `.venv` Python 3.12.13. `/mnt/d/_Work/goat_bank` and the current `/mnt/d/_work/goat_bank` spelling refer to this workspace. Ollama is available through the local HTTP service; executable observed at `/usr/local/bin/ollama` (the former snap path is absent).

## Frozen execution

- Command: `python -u -m evaluation.llm_security_v3_2.closure_campaign`, from `uir/` using the root `.venv`.
- Results: `uir/results/llm_security_v3_2_closure/`.
- Log: `execution.log`; checkpoints: `raw_runs/*.jsonl`.
- Primary: all 850 original held-out IDs (250 benign, 600 attacks) × 6 systems.
- HETE Phi/Qwen: same 850 IDs. Twelve HETE ablation configurations each use 850 IDs.
- Adaptive: six campaigns × 30 seeds, B=20 or first actual E2E success. Five stochastic seeds use the same 30 frozen IDs.
- Do not edit frozen evaluation/SUT Python sources during this run. `campaign_protocol.json` contains exact source hashes, and resume rejects changes.
- The interrupted 240-case artifacts are preserved; authoritative new execution does not mix them with current evidence.

## Actual verification

- 116 regression tests passed across security_v3, security_v3_1, security_v3_2 and test_llm_trust.py. Log: `docs/security_v3_2/audit/regression_tests.txt`.
- Independent strict audit of the first complete primary system reported no raw-record replay failures. It correctly fails the overall gate while remaining systems/experiments/manuscript evidence are incomplete.
- Revised pending manuscript: `docs/papers/_47_1_UIR_for_ZTA/_47.1_UIR_ZTA.tex`, including `v3_2_evidence.tex`.
- LaTeX → BibTeX → LaTeX → LaTeX succeeded for the pending 16-page draft, with no unresolved references/citations. This is not the final evidence build.
- Dataset audit: 850 IDs, 722 unique normalized user requests, 128 reused-request rows, zero normalized request overlap with existing dev/validation. This is NOT proof of semantic independence; template reuse and conditional statistical scope are disclosed.

## Interruption and resumption

The first primary system stopped after 783 admitted rows because the backend response failed the complete/live-response check. The failed output was not admitted. The original incomplete response body was not retained, so its cause cannot be established. A separate unscored diagnostic of the same frozen input returned a complete actual Ollama response. All 783 rows were preserved and execution resumed at the next missing row; primary_0 subsequently reached 850/850.

Files: `operational_failures/EXECUTION_FAILURE_original.json`, `operational_failures/interruption_after_783_rows.json`, `backend_failure_diagnostic.json`. Do not remove this history or claim every attempted backend body was retained. No model, policy, dataset or outcome threshold was changed for resumption.

## Completion worker

`python -u docs/security_v3_2/audit/finalize_closure.py --wait-for-campaign` is started as the companion completion process. Log: `docs/security_v3_2/audit/finalization.log`.

It waits for the campaign completion message; any new EXECUTION_FAILURE.json stops it. After successful execution it reconstructs supplemental metrics, runs the raw auditor, renders final manuscript numbers only after the raw-data audit passes, compiles LaTeX/BibTeX, copies frozen source and artifact material, and reruns the strict final gate. Completion state is `results/llm_security_v3_2_closure/FINALIZATION_STATUS.json`.

A successful inference process alone is not completion. The required condition is `publication_evidence_validation.json: publication_evidence_valid=true`, followed by review of the actual generated report and manuscript. If an audit fails, retain evidence and repair the specific integrity issue; do not tune model/defense behavior against final outcomes.

## Claims and source scope

- V3.1 is V3_1_PRELIMINARY_PUBLICATION_EVIDENCE; pre-closure hashes and original manuscripts/reports are archived under `docs/security_v3_2/audit/` and preclosure directories.
- Human Option B: no human adjudication or kappa claims, human_validation=false.
- AgentDojo Option B: only a historical AgentDojo-inspired micro-suite (N=5), no actual public benchmark execution or superiority claim.
- CaMeL and Progent evaluation adapters are explicitly inspired approximations.
- Current report remains marked INCOMPLETE until the final gate actually passes.

## Source amendment 01 (before the first HETE live case)

An independent synthetic regression showed that a signed document body could be paired with altered unsigned sibling claim metadata, and that omitted B/M/T scale could be incorrectly interpreted at the expected answer scale. Both are work-order P7/P8 validity defects. The signed body now controls evidence claims; exact decimal normalization treats omitted scales as base currency units. The model prompts, inference client, dataset and five baseline adapters were unchanged.

The live process was paused with 850 Vanilla + 399 Naive RAG records and no HETE rows. Original source, protocol and original records are preserved in `source_epochs/epoch_0/`. Exactly 1,249 canonical records were rejudged with the corrected oracle, asserting that every field other than verdict remained identical. The amendment and hashes are in `SOURCE_AMENDMENT_01.json`. Current frozen source is epoch_1; resumption continues only from missing cases. A mechanical integration pass covered all 10,200 case/configuration combinations without exceptions (test doubles only, not model evidence). The new security regressions are part of the 116-pass suite.

Both the live campaign and completion worker were restarted after this amendment. No empirical outcome or success-rate threshold motivated these repairs.

## Source amendment 02 (adaptive candidate uniqueness)

After all six 850-case primary groups, all twelve 850-case ablations, and the first 30 adaptive seeds completed, the runner stopped fail-closed before admitting the next seed. The first `indirect_prompt_injection` seed produced a duplicate full input/context hash at query 20 because a homoglyph transform converged on a feedback-selected parent. The failure was reproduced without inference.

Epoch-1 source, protocol, execution log, and the 30 completed adaptive records are preserved under `source_epochs/epoch_1/` and `operational_failures/`. `SOURCE_AMENDMENT_02.json` binds the failure and before/after hashes. Epoch 2 deterministically wraps a colliding candidate in a newly indexed red-team authorization scenario until its full request/context hash is unique, with a bound of 20 and explicit `collision_reframes` evidence. An offline pass over the remaining 150 seeds × 20 mutation positions found six collisions, each resolved by one reframe. No dataset, oracle, judge, model, inference option, HETE/baseline adapter, completed primary/ablation record, or success threshold changed.

The epoch-2 security regression suite remains 116/116 passing. The resumed campaign continues from the first missing adaptive seed, followed by the preregistered stochastic groups and identical-850-case Phi group.

## Full-repository test limitation and bibliography audit

The broader `python -m pytest tests -q` attempt failed during collection in the pre-existing `tests/uir_phase4d/test_runtime_run.py`: `build_internal_request` is referenced without an import. No tests ran in that invocation. The independent security-focused 116-pass result remains the applicable validation; no claim of a passing full repository suite is made. The complete collection log is archived in `audit/full_python_tests.txt`.

This broader-suite limitation was subsequently repaired. The Phase 4D diagnostic now imports its existing `build_internal_request` function. A second failure exposed that the V2 resume loader checked fallback model metadata before checking a changed dataset fingerprint; its validation order now rejects the fingerprint mismatch first. Neither change is inside the frozen V3.2 evaluated-source hash scope. The full repository suite then passed 130/130 tests; the earlier failed logs and final passing log remain in `audit/`.

Primary-source bibliography checks found incorrect CaMeL and Progent author/title/venue entries. Corrected these against arXiv:2503.18813v2 and arXiv:2504.11703v3, retaining the previous bibliography. Removed unsupported absence-of-feature crosses in the related-work taxonomy and distinguished published designs from local adapters. These are document-only changes, with no evaluated execution source or protocol changes.

## Second operational interruption (Phi after 53 rows)

After all 180 adaptive seeds and all 150 stochastic rows completed, the identical-case Phi campaign stopped fail-closed before admitting case `c_4f81ad8aebf880f0`. The response failed the same complete/live-response admission check after 53 admitted Phi rows. The active failure marker and execution log were preserved under `results/llm_security_v3_2_closure/operational_failures/`; the incomplete response body was not retained, so its exact failure mode cannot be established.

An unscored retry of the exact frozen case, model, prompt path, and deterministic options returned one complete actual Ollama call. Its full row and raw response are stored in `backend_failure_diagnostic_phi_after_53_rows.json` and are excluded from every publication denominator. The campaign then resumed from row 54 without source, model, dataset, oracle, policy, or threshold changes.

The Phi process stopped a second time after 240 admitted rows on case `c_bfb96b5196175e21`. An immediate exact-case diagnostic reproduced `done=false` with no token counters or termination reason. After a normal Ollama `keep_alive=0` unload and reload of the unchanged `phi3.5:latest` model, the same request completed with `done=true`, `done_reason=length`, and `eval_count=384`. Both diagnostics and the failure marker are retained under `operational_failures/`; neither diagnostic is scored. Execution resumed from row 241 with the frozen protocol unchanged.

The same runner state recurred after 412 admitted Phi rows on case `c_8e6026ea95115b45`. The failure marker and log were preserved, a normal unload returned HTTP 200 with `done=true`, and the campaign resumed from row 413. The recovery response is stored in `phi_model_unload_after_412_rows.json`. No retry policy was inserted into the evaluated source and no incomplete response entered the raw publication records.

The Phi runner later stopped after 496, 624, 646, and 768 admitted rows. The 646-row case also reproduced immediately after a diagnostic consumed the first complete post-reload response. Each marker and execution log was preserved. Normal model unloads returned `done=true`; campaign execution resumed only from the missing frozen case. Eight unique operational interruptions occurred across the complete campaign, including the original Vanilla interruption. The final raw records contain no fallback or admitted incomplete response.

## Final closure

- Primary comparison: 850 cases for each of six systems.
- Ablations: 850 cases for each of 12 configurations.
- Adaptive: 180 seeds and 3,600 actual queries; six collision reframes; no duplicate candidate hashes.
- Stochastic: five seeds and 150 rows at temperature 0.7 and top-p 0.9.
- Multi-model: identical 850 case IDs for Qwen2.5-7B and Phi-3.5.
- Benign-length supplement: 30/30 rows, retained outside primary denominators.
- Validation: 130/130 full repository tests, 116/116 security tests, exact-statistics cross-check, supplemental reconstruction, manuscript binding, and LaTeX/BibTeX build all pass.
- Final status: `publication_evidence_valid=true`, `scientific_integrity_failures=[]`.
