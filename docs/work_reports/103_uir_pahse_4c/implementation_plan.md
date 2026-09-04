# Phase UIR-4C implementation plan

## Goal

Replace Phase-4B template/simulated empirical artifacts with source-mapped, actual local Phi-3.5 inference while freezing the UIR architecture.

## Execution design

1. Vendor the official FinQA test split and HaluEval QA release at exact upstream commits, including licenses and the FinQA evaluator.
2. Freeze a 600-case internal stratified subset and 100-case smoke subset before inference. Keep runtime and scoring fields in separate files.
3. Execute C0–C8 with the same local Phi-3.5 snapshot, greedy seed-42 decoding, immutable raw responses, response hashes, token counts, and same-invocation timing.
4. Implement C4 as genuine model-selected tool name/arguments followed by authoritative local tool execution and a second model response.
5. Run 200 official FinQA and 200 official HaluEval-QA cases for C1/C2/C4/C8. Preserve original IDs and source-row hashes.
6. Score only after generation; calculate matched safety, utility, and latency statistics from actual records.
7. Fail closed on placeholders, missing provenance, token/timing omissions, source mismatches, pre-generation gold access, and non-model-driven C4 traces.
8. Stop development when `READY_FOR_FINAL_MANUSCRIPT_AUTHENTIC` is reached.

## Frozen scope

- No UIR grammar, AST, policy semantics, invariant, GAT, language, domain, or second-backbone feature work.
- Preserve `results/uir_phase3d`, `results/uir_phase4`, and `results/uir_phase4b` unchanged.
- Treat Phase 4B as `phase4b_evidence_audit_prototype`.
