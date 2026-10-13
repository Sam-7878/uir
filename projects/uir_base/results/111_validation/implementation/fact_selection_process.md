# Fixture construction and independent selection

All 418 eligible rows were hash-joined to original source rows. 224 frozen-v2
cases come through review_and_freeze.campaign_record, which assigns required_claims
to both expected_claims and context_claims. 66 real-fact cases are selected SEC
registry facts transformed into the same claim set twice. 128 frozen-v1 cases
have expected claims but no context_claims field; freeze_inputs_phase4d turns this
into an empty runtime catalog. The same freeze script constructs requested slots
from expected_semantics. These are assisted/oracle-like fixtures, not raw-only
independent fact selection. Direct gold-file access is a separate question.

Source row/generator/file hashes and field transformations are retained in
fixture_lineage_audit.csv and fixture_lineage_scoring_only.jsonl. Original physical
SEC document bytes have not been freshly verified. A larger candidate universe
was not saved for every constructed frozen-v2 question.

The new development packets build a catalog with wrong entities, attributes,
periods and units BEFORE selecting by the typed request. Runtime sees that catalog
and authenticated policy only; normative scoring labels are written separately.
This is B non-oracle fixed-catalog selection and D incomplete evidence, not C
free-language source discovery. A is retained for the separate output-layer
renderer experiment. Source-number lexical/full-document diagnostics are distinct
from semantic financial operand/unit sufficiency.
