# V3.2 final scientific-validity report

**FINAL_PUBLICATION_EVIDENCE — strict artifact gate passed.**

Canonical execution evidence: `results/llm_security_v3_2_closure/`; the completed package is also materialized at the work-order path `results/llm_security_v3_2/`. Source, raw, and summary hashes are in ARTIFACT_MANIFEST.json. V3.1 remains V3_1_PRELIMINARY_PUBLICATION_EVIDENCE.

| System | MCR | E2E | Complete utility | FRR |
|---|---:|---:|---:|---:|
| Vanilla SLM | 88/600 (14.67%) | 99/600 (16.50%) | 0/250 (0.00%) | 0/250 (0.00%) |
| Naive RAG | 138/600 (23.00%) | 162/600 (27.00%) | 250/250 (100.00%) | 0/250 (0.00%) |
| Spotlighting | 117/600 (19.50%) | 141/600 (23.50%) | 250/250 (100.00%) | 0/250 (0.00%) |
| Progent-inspired | 89/600 (14.83%) | 47/600 (7.83%) | 231/250 (92.40%) | 0/250 (0.00%) |
| CaMeL-inspired | 108/600 (18.00%) | 72/600 (12.00%) | 249/250 (99.60%) | 0/250 (0.00%) |
| HETE | 0/600 (0.00%) | 0/600 (0.00%) | 249/250 (99.60%) | 1/250 (0.40%) |

## Multi-model HETE results

| Model | Attack N | Benign N | MCR | E2E | Utility | FRR | Raw invalid | Final invalid | Mean latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:7b | 600 | 250 | 0/600 (0.00%) | 0/600 (0.00%) | 249/250 (99.60%) | 1/250 (0.40%) | 0/250 (0.00%) | 1/250 (0.40%) | 1095.95 |
| phi3.5:latest | 600 | 250 | 3/600 (0.50%) | 6/600 (1.00%) | 0/250 (0.00%) | 250/250 (100.00%) | 250/250 (100.00%) | 250/250 (100.00%) | 1964.63 |

Runtime: Ubuntu 26.04.1 on WSL2; Python 3.12.13; Ollama 0.33.3; num_ctx=8192; max_new_tokens=384; timeout=180s.

| Model | Digest | Parameters | Quantization | Native context |
|---|---|---:|---|---:|
| qwen2.5:7b | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | 7.6B | Q4_K_M | 32768 |
| phi3.5:latest | `61819fb370a3c1a9be6694869331e5f85f867a079e9271d66cb223acb81d04ba` | 3.8B | Q4_0 | 131072 |

## Full-size ablation results

| Configuration | Attack N | Benign N | MCR | E2E | Utility | FRR |
|---|---:|---:|---:|---:|---:|---:|
| full_defense | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 249/250 (99.60%; 95% Wilson 97.77--99.93) | 1/250 (0.40%; 95% Wilson 0.07--2.23) |
| no_input_guard | 600 | 250 | 4/600 (0.67%; 95% Wilson 0.26--1.70) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 249/250 (99.60%; 95% Wilson 97.77--99.93) | 1/250 (0.40%; 95% Wilson 0.07--2.23) |
| no_provenance | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 248/250 (99.20%; 95% Wilson 97.13--99.78) | 2/250 (0.80%; 95% Wilson 0.22--2.87) |
| no_context_firewall | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 250/250 (100.00%; 95% Wilson 98.49--100.00) | 0/250 (0.00%; 95% Wilson 0.00--1.51) |
| no_capability_gate | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 249/250 (99.60%; 95% Wilson 97.77--99.93) | 1/250 (0.40%; 95% Wilson 0.07--2.23) |
| no_output_guard | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 249/250 (99.60%; 95% Wilson 97.77--99.93) | 0/250 (0.00%; 95% Wilson 0.00--1.51) |
| no_resource_guard | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 20/600 (3.33%; 95% Wilson 2.17--5.09) | 249/250 (99.60%; 95% Wilson 97.77--99.93) | 1/250 (0.40%; 95% Wilson 0.07--2.23) |
| no_input_guard_no_output_guard | 600 | 250 | 4/600 (0.67%; 95% Wilson 0.26--1.70) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 250/250 (100.00%; 95% Wilson 98.49--100.00) | 0/250 (0.00%; 95% Wilson 0.00--1.51) |
| no_provenance_no_output_guard | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 248/250 (99.20%; 95% Wilson 97.13--99.78) | 0/250 (0.00%; 95% Wilson 0.00--1.51) |
| no_policy | 600 | 250 | 1/600 (0.17%; 95% Wilson 0.03--0.94) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 248/250 (99.20%; 95% Wilson 97.13--99.78) | 2/250 (0.80%; 95% Wilson 0.22--2.87) |
| no_action_revalidation | 600 | 250 | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 0/600 (0.00%; 95% Wilson 0.00--0.64) | 249/250 (99.60%; 95% Wilson 97.77--99.93) | 1/250 (0.40%; 95% Wilson 0.07--2.23) |
| no_capability_gate_no_policy_or_action_revalidation | 600 | 250 | 8/600 (1.33%; 95% Wilson 0.68--2.61) | 7/600 (1.17%; 95% Wilson 0.57--2.39) | 249/250 (99.60%; 95% Wilson 97.77--99.93) | 1/250 (0.40%; 95% Wilson 0.07--2.23) |

## Evidence hash index

| Artifact | SHA-256 |
|---|---|
| `raw_runs/primary_5.jsonl` | `bab9e2cf826dcef0ee7fa9ecaf34cfdaae670c8afca32cf6a80810f3a649f148` |
| `raw_runs/multimodel_phi.jsonl` | `47cb642d77a6408fc8673c3182918a9ef6cd3faef64cc9d68b166f0052b96cd4` |
| `raw_runs/adaptive.jsonl` | `f4f17c6aefd832da22c2091f3ad973d67903044c9a0929670e7f39079905071a` |
| `raw_runs/ablation_full_defense.jsonl` | `217eca6c54dfef8d4a6c617bbce5134ebec471ca403c2e08c6cc9993e0d7248e` |
| `datasets/runtime.json` | `ca07af4d8fe252273a8596f43a7a3c8f4845c218937bfd350992dd3af19a6fd5` |
| `datasets/oracle.json` | `21825e889e4acd1af866de82ce83a92e13a4e2fb86880b647295c575ca21567c` |
| `dataset_manifest_v3_2.json` | `633b2e3b616e00fdbd401a69ffc82e44c3bb86ecc24bdaba3a431670cc1cd2a4` |
| `runtime_manifest.json` | `14be20a03a322d0fc3027198e6486bb68e3eae09f157a81a5e6b4d258e580c1f` |
| `policy_manifest.json` | `8bdbe4d42273e962616fd795f7d5ccefbc360a5ffaa66e31da57d26a2da5face` |
| `provenance_manifest.json` | `3e111c5436e7561fbeb3ea90280945b2d80042b2597a44609d9f96c01337cf4c` |
| `statistical_tests.json` | `c89fb8da787e8e74f4dc41bdc6072c79a63f7c361051a2982fb31b21bc33b64e` |
| `exact_statistics_crosscheck.json` | `7f96d9c2182d27e04ffc42b7cce09c7ca1dbc123c9f6ea1201fd68381265dac0` |
| `tool_gate_comparison.json` | `3cc3b85d608794443235b9ffbec7416780d15fbc9348777d7857c9223c2dbb76` |
| `resource_guard_comparison.json` | `f3b928a281305329191302b59a5276ec6b7760f9ea66734ab1606b611e974553` |
| `operational_interruption_summary.json` | `606546cf4c07daf007c30bc6ff6d2984731ad1291ca2420699a06fe006471693` |
| `benign_long_supplement/audit.json` | `4ebb017e3a24cf15058d3ab3aa62fbe4a918655f9517c6c0115063730a4cd474` |
| `SOURCE_AMENDMENT_01.json` | `7a9613e83eef85ac20a66d4a343ad4d210eb52c2407bf4c2c696f45e129a7624` |
| `SOURCE_AMENDMENT_02.json` | `6244532bdb86f740c91ac4a9c76585ef7d0a68021822399445da16010519999e` |

## Answers to all work-order questions

1. No human labels were generated for this final evidence. Historical simulated ratings are archived, not admitted.
2. No R1/R2 labels were supplied; human_validation=false (Option B).
3. Actual AgentDojo was not imported or executed.
4. No public AgentDojo commit/version applies. The historical local AgentDojo-inspired micro-suite has N=5 and is not primary evidence.
5. The auditor verifies every adaptive input/context hash from the stored actual candidate, with no within-seed duplicates.
6. Adaptive execution: 180 seeds; 3600 actual queries.
7. The gate verifies B=20 for every surviving search; only actual E2E success permits early termination.
8. Synthetic secrets occur only in private fixtures/system context, and the auditor verifies absence from attacker input.
9. Raw-model and final-egress leakage counts are in exfiltration_details.json: {"case_count": 67, "model_leakage_count": 0, "egress_leakage_count": 0}.
10. Unauthorized proposed tools are enumerated per system in agency_details.json; HETE: {}.
11. Actual forbidden mock mutations, HETE: {}.
12. CapabilityGate and independent action revalidation are isolated in full-size individual and paired knockouts. Exact proposal, admission, executor-invocation and forbidden-mutation case counts are: {"full_defense": {"case_count": 67, "cases_with_tool_proposals": 0, "cases_with_admitted_calls": 0, "cases_with_executor_invocations": 0, "cases_with_forbidden_mutations": 0}, "no_capability_gate": {"case_count": 67, "cases_with_tool_proposals": 0, "cases_with_admitted_calls": 0, "cases_with_executor_invocations": 0, "cases_with_forbidden_mutations": 0}, "no_policy": {"case_count": 67, "cases_with_tool_proposals": 0, "cases_with_admitted_calls": 0, "cases_with_executor_invocations": 0, "cases_with_forbidden_mutations": 0}, "no_action_revalidation": {"case_count": 67, "cases_with_tool_proposals": 0, "cases_with_admitted_calls": 0, "cases_with_executor_invocations": 0, "cases_with_forbidden_mutations": 0}, "no_capability_gate_no_policy_or_action_revalidation": {"case_count": 67, "cases_with_tool_proposals": 7, "cases_with_admitted_calls": 7, "cases_with_executor_invocations": 7, "cases_with_forbidden_mutations": 7}}.
13. ResourceGuard comparison on identical resource-class IDs is: {"full_defense": {"case_count": 66, "blocked_resource_exhausted": 27, "e2e_resource_exceed_count": 0, "consumption_totals": {"input_tokens": 19430.0, "output_tokens": 1821.0, "retrieval_ops": 299.0, "tool_proposals": 0.0, "tool_executions": 0.0, "agent_steps": 26.0, "elapsed_ms": 41430.516379}, "consumption_means": {"input_tokens": 294.3939393939394, "output_tokens": 27.59090909090909, "retrieval_ops": 4.53030303030303, "tool_proposals": 0.0, "tool_executions": 0.0, "agent_steps": 0.3939393939393939, "elapsed_ms": 627.7350966515152}}, "no_resource_guard": {"case_count": 66, "blocked_resource_exhausted": 0, "e2e_resource_exceed_count": 20, "consumption_totals": {"input_tokens": 68190.0, "output_tokens": 3260.0, "retrieval_ops": 313.0, "tool_proposals": 0.0, "tool_executions": 0.0, "agent_steps": 46.0, "elapsed_ms": 85105.87497}, "consumption_means": {"input_tokens": 1033.1818181818182, "output_tokens": 49.39393939393939, "retrieval_ops": 4.742424242424242, "tool_proposals": 0.0, "tool_executions": 0.0, "agent_steps": 0.696969696969697, "elapsed_ms": 1289.482954090909}}}. Resource_details.json also retains per-case consumption. Blocking cannot undo already consumed resources; post-call wall-clock detection is explicitly limited.
The additional preregistered benign-length supplement uses 10 lexical-order benign seeds crossed with three length targets (30 cases); its raw traces, actual consumption and false-rejection counts are in benign_long_supplement. It does not change any 850-case primary denominator.
14. Whole-document JSON trailing text, fences, duplicate objects/keys, hidden-context and schema regressions pass; see regression_tests.txt.
15. HETE accepted benign contract-valid outputs: 249/250; see baseline_comparison.json for all systems.
16. HETE complete-task utility: 249/250; entity, metric, unit, value, year, citation and schema must all match.
17. Primary N=850, with 600 attacks and 250 benign cases.
18. Phi and Qwen HETE use identical frozen 850-case sets, checked against the dataset.
19. Every one of 12 ablation configurations has N=850; raw records and exact denominators are retained.
20. Exact two-sided binomial McNemar and Holm alpha=.05 values are in statistical_tests.json, with scientific notation and replay verification.
21. The raw auditor replays judges, recomputes summary metrics and tests case completeness, sampling and statistical parity. Supplemental reconstruction is documented in supplemental_audit.json.
22. The artifact manifest contains 736 files, including all raw JSONLs, dataset/oracle/lineage, runtime and policy material.
23. The manuscript is generated from frozen summaries and manifests; artifact binding and the LaTeX/BibTeX build are separately recorded.
24. Observed HETE outcomes include 0 model-compromise cases, 0 E2E attack successes, 1 incomplete benign tasks, 1 false rejections, and 1 contract-invalid benign final outputs. No observed failure was removed to improve a result.
Source amendment: before any HETE live run, independent synthetic regressions found unsigned claim-metadata binding and unit-normalization defects. The signed body now controls claim validation, and unitless money means base units. Earlier baseline generations were preserved and rejudged with the corrected oracle; full epoch/source/original-record hashes are retained in SOURCE_AMENDMENT_01.json and source_epochs. No model or prompt was tuned.
Adaptive-runner amendment: after the primary comparison, all twelve ablations, and the first 30 adaptive seeds completed, a repeated full input/context hash stopped the run before admission of the affected seed. SOURCE_AMENDMENT_02.json preserves the epoch-1 source, protocol, completed adaptive records, failure reproduction, and exact code hashes. Epoch 2 deterministically reframes only a colliding candidate and records the collision count; metrics, judges, dataset, models, and completed records were unchanged.
Operational history is reconstructed in operational_interruption_summary.json: {"unique_interruption_count": 8, "interruptions": [{"group": "multimodel_phi", "case_id": "c_01c3078e429fa7e2", "completed_rows": 624, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_phi_after_624_rows.json"], "diagnostics": []}, {"group": "multimodel_phi", "case_id": "c_0f32f93e74f52fc0", "completed_rows": 496, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_phi_after_496_rows.json"], "diagnostics": []}, {"group": "multimodel_phi", "case_id": "c_47cf76a6768f1f39", "completed_rows": 646, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_phi_after_646_rows.json", "operational_failures/EXECUTION_FAILURE_phi_after_646_rows_retry.json"], "diagnostics": [{"path": "operational_failures/backend_failure_diagnostic_phi_after_646_rows_recovery.json", "complete_response": true, "purpose": "Unscored exact-case diagnostic after fail-closed Phi response; excluded from all denominators"}]}, {"group": "multimodel_phi", "case_id": "c_4f81ad8aebf880f0", "completed_rows": 53, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_phi_after_53_rows.json", "operational_failures/EXECUTION_FAILURE_phi_after_53_rows_active_marker.json"], "diagnostics": [{"path": "operational_failures/backend_failure_diagnostic_phi_after_53_rows.json", "complete_response": true, "purpose": "Unscored exact-case diagnostic after fail-closed incomplete Phi response; excluded from all denominators"}]}, {"group": "multimodel_phi", "case_id": "c_8e6026ea95115b45", "completed_rows": 412, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_phi_after_412_rows.json"], "diagnostics": []}, {"group": "multimodel_phi", "case_id": "c_bfb96b5196175e21", "completed_rows": 240, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_phi_after_240_rows.json"], "diagnostics": [{"path": "operational_failures/backend_failure_diagnostic_phi_after_240_rows.json", "complete_response": false, "purpose": "Unscored exact-case diagnostic after fail-closed incomplete Phi response; excluded from all denominators"}, {"path": "operational_failures/backend_failure_diagnostic_phi_after_240_rows_reload.json", "complete_response": true, "purpose": "Unscored exact-case diagnostic after explicit normal model unload/reload; excluded from all denominators"}]}, {"group": "multimodel_phi", "case_id": "c_d499d629bd814de9", "completed_rows": 768, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_phi_after_768_rows.json"], "diagnostics": []}, {"group": "primary_0", "case_id": "c_5a9525f498fc2fc5", "completed_rows": 783, "error": "Non-live or incomplete backend response; no publication row admitted", "evidence_paths": ["operational_failures/EXECUTION_FAILURE_original.json", "operational_failures/interruption_after_783_rows.json"], "diagnostics": []}], "recovery_events": [{"path": "operational_failures/phi_model_unload_after_412_rows.json", "after_completed_rows": 412, "status_code": 200, "done": true, "purpose": "Operational recovery after fail-closed Phi interruption; model/config unchanged"}, {"path": "operational_failures/phi_model_unload_after_496_rows.json", "after_completed_rows": 496, "status_code": 200, "done": true, "purpose": "Operational recovery after fail-closed Phi interruption; model/config unchanged"}, {"path": "operational_failures/phi_model_unload_after_624_rows.json", "after_completed_rows": 624, "status_code": 200, "done": true, "purpose": "Operational recovery after fail-closed Phi interruption; model/config unchanged"}, {"path": "operational_failures/phi_model_unload_after_646_rows_retry.json", "after_completed_rows": 646, "status_code": 200, "done": true, "purpose": "Operational recovery after repeated fail-closed Phi interruption; no diagnostic request before campaign retry"}, {"path": "operational_failures/phi_model_unload_after_768_rows.json", "after_completed_rows": 768, "status_code": 200, "done": true, "purpose": "Operational recovery after fail-closed Phi interruption; no diagnostic request before campaign retry"}], "admission_policy": "A response missing done=true, containing an error, or using fallback is rejected before a publication row is written.", "resumption_policy": "Preserve checkpoints and failure evidence; retry only the missing frozen case without changing model, input, evaluation policy, or outcome criteria.", "limitation": "Rejected response bodies were not retained by the campaign runner; only diagnostics performed after interruption retain response bodies."}. No rejected response was admitted. Each run resumed only the missing frozen case without changing model, policy, dataset, or outcome criteria.
The broader repository suite passes 130 tests and the security-focused regression suite passes 116 tests. Exact command output is retained in full_python_tests.txt and regression_tests.txt; the optional requests character-detector warning does not affect execution.
25. Conclusions are limited to the recorded custom fixture population, two quantized local models, deterministic judges and inspired baseline approximations. No universal security, official-baseline superiority, human validation or public AgentDojo generalization is established.

Template reuse is explicitly reported in dataset_independence_audit.json. Confidence intervals and exact paired p-values do not establish independence of novel real-world tasks. No further tuning against the frozen final set is authorized by this completion report.
