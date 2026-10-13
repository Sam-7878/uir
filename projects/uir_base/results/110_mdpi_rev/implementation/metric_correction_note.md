# Raw-level correction causes

Preserve original captures and scripts. `next_release` invokes pure scoring
functions only, never the legacy `rescore_d1_inplace.main` or aggregate writers.

The old Phi C8 HaluEval 72% is a literal `raw_semantic_accuracy: 0.7200` in
`rescore_publication_final.py`. It is not calculated from per-case raw labels.
No per-case estimator justifying that value was found. A correction must not
invent a 144-case old semantic-label assignment.

The old Qwen C8 runner initialized `pred8 = No` before parsing. Parse failures
kept this value; the current 200 raw outputs' missing overall label is not a
50%-accurate semantic response and is not 0% semantic capability. Independent
completed-literal extraction is reported separately from strict JSON parsing.

The legacy D1 pure scorer reproduces 206 complete cases (49.28% of 418) and
125 unsupported cases (20.83% of 600). It validated attribute/provenance coverage,
not all seven exact claim fields. New exact-field binding yields 74 complete
and 326 unsupported cases. All 600 transitions include record/hash references;
nonexclusive field-mismatch counts are explicitly not additive cause attribution.

D1 schema validation is performed against the actual declared JSON Schema:
596/600 valid; all four invalid raw strings and JSON/schema paths are included.
Finish reason was not recorded in that capture and must remain NOT_RECORDED.

Every C0–C8 condition and D1 uses the same new scorer. Prose-vs-structured scope,
rejection detection and support-catalog differences are retained in the 6000-row
transition ledger. This does not retrospectively certify the old aggregate code.
