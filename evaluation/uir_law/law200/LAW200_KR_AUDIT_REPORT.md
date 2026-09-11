# LAW-KR-200 Audit Report

Status: **READY_FOR_KAIC_MANUSCRIPT_KR**

## Checks

- [x] required_frozen_inputs: `PASS` — []
- [x] exactly_200_test_cases: `PASS` — {'runtime': 200, 'gold': 200}
- [x] runtime_gold_case_alignment: `PASS` — one-to-one opaque IDs
- [x] gold_labels_absent_from_runtime: `PASS` — {'leaking_rows': 0}
- [x] category_balance: `PASS` — {'D_ENTITY_MISMATCH': 50, 'A_VALID': 50, 'C_NONEXISTENT': 50, 'B_SURFACE_VARIATION': 50}
- [x] language_balance: `PASS` — {'en': 100, 'ko': 100}
- [x] unique_runtime_queries: `PASS` — 200 required
- [x] frozen_test_hash: `PASS` — e728fae81590f640e52e9174a72e238d00a550870c8cb6b0178b04e60d0efc21
- [x] frozen_registry_hash: `PASS` — 9b9094e9fa0f6d28eb13730796bdcc47d90c84b7176783bb988f08cecd2c1655
- [x] frozen_corpus_hash: `PASS` — 227cd5c6cff18b42bc838a0a6d42019c9a86674020f286d04fa0ca407e08d0f5
- [x] hardware_observation_bound_to_test: `PASS` — {'capture_timing': 'post-run', 'gpu_probe': {'devices': ['NVIDIA GeForce RTX 4070 Laptop GPU, 595.97, 8188 MiB'], 'status': 'DETECTED'}}
- [x] cross_lingual_uir_equivalence: `PASS` — {'equivalent_pairs': 100, 'pairs': 100}
- [x] source_integrity_audit: `PASS` — {'status': 'PASS', 'registry_records': 90, 'valid_200_records': 60, 'normalized_not_found_records': 30, 'not_found_http_semantics': 'HTTP 200 with no exact 사건번호 match; registry lookup_status normalized to 404', 'findings': []}
- [x] credential_absent_from_artifacts: `PASS` — {'leak_file_count': 0}
- [x] dev_test_id_separation: `PASS` — no overlap
- [x] dev_test_query_separation: `PASS` — no overlap
- [x] forbidden_pre_generation_gold_access_zero: `PASS` — /mnt/d/_Work/goat_bank/uir/evaluation/uir_law/law200/results/kr/raw/test_pre_generation_access_log.json
- [x] raw_file_C0_DIRECT: `PASS` — ['/mnt/d/_Work/goat_bank/uir/evaluation/uir_law/law200/results/kr/raw/test_C0_DIRECT_phi3-5-latest.jsonl']
- [x] raw_rows_C0_DIRECT: `PASS` — 200
- [x] same_cases_C0_DIRECT: `PASS` — must equal frozen runtime
- [x] raw_output_complete_C0_DIRECT: `PASS` — model raw response or explicit pre-model output required
- [x] raw_file_C1_NAIVE_RAG: `PASS` — ['/mnt/d/_Work/goat_bank/uir/evaluation/uir_law/law200/results/kr/raw/test_C1_NAIVE_RAG_phi3-5-latest.jsonl']
- [x] raw_rows_C1_NAIVE_RAG: `PASS` — 200
- [x] same_cases_C1_NAIVE_RAG: `PASS` — must equal frozen runtime
- [x] raw_output_complete_C1_NAIVE_RAG: `PASS` — model raw response or explicit pre-model output required
- [x] raw_file_C2_EXISTENCE_CHECK: `PASS` — ['/mnt/d/_Work/goat_bank/uir/evaluation/uir_law/law200/results/kr/raw/test_C2_EXISTENCE_CHECK_phi3-5-latest.jsonl']
- [x] raw_rows_C2_EXISTENCE_CHECK: `PASS` — 200
- [x] same_cases_C2_EXISTENCE_CHECK: `PASS` — must equal frozen runtime
- [x] raw_output_complete_C2_EXISTENCE_CHECK: `PASS` — model raw response or explicit pre-model output required
- [x] raw_file_C4_TOOL_AGENT: `PASS` — ['/mnt/d/_Work/goat_bank/uir/evaluation/uir_law/law200/results/kr/raw/test_C4_TOOL_AGENT_phi3-5-latest.jsonl']
- [x] raw_rows_C4_TOOL_AGENT: `PASS` — 200
- [x] same_cases_C4_TOOL_AGENT: `PASS` — must equal frozen runtime
- [x] raw_output_complete_C4_TOOL_AGENT: `PASS` — model raw response or explicit pre-model output required
- [x] raw_file_C5_GUARDRAIL: `PASS` — ['/mnt/d/_Work/goat_bank/uir/evaluation/uir_law/law200/results/kr/raw/test_C5_GUARDRAIL_phi3-5-latest.jsonl']
- [x] raw_rows_C5_GUARDRAIL: `PASS` — 200
- [x] same_cases_C5_GUARDRAIL: `PASS` — must equal frozen runtime
- [x] raw_output_complete_C5_GUARDRAIL: `PASS` — model raw response or explicit pre-model output required
- [x] raw_file_C8_UIR: `PASS` — ['/mnt/d/_Work/goat_bank/uir/evaluation/uir_law/law200/results/kr/raw/test_C8_UIR_phi3-5-latest.jsonl']
- [x] raw_rows_C8_UIR: `PASS` — 200
- [x] same_cases_C8_UIR: `PASS` — must equal frozen runtime
- [x] raw_output_complete_C8_UIR: `PASS` — model raw response or explicit pre-model output required
- [x] same_backbone_and_configuration: `PASS` — {'distinct_configs': 1}
- [x] aggregate_and_statistics_present: `PASS` — {'metrics': True, 'statistics': True}
- [x] aggregates_and_confidence_intervals_recomputed: `PASS` — full metric objects must reproduce exactly
- [x] statistics_recomputed_from_raw: `PASS` — McNemar, Holm, and risk differences must reproduce
- [x] paper_facing_tables_present: `PASS` — {'csv': True, 'md': True}
- [x] paper_table_recomputed_not_manual: `PASS` — CSV must equal raw recomputation
- [x] markdown_table_generation_marker: `PASS` — required
