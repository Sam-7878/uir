# OutputGuard validation

The `financial_summary_v3_2` JSON Schema requires entity, metric, value, and citations, rejects unknown properties and invalid types, and is distinct from the legacy renderer contract. The whole document is decoded; fenced JSON, prefixes, suffixes, duplicate keys, and non-finite constants fail. Raw and decoded content are checked for DLP/encoded command emission. Accepted output is canonical JSON.

Citation IDs are checked against admitted evidence; the V3.2 pipeline supplies authenticated fixture claims for claim/value consistency checks. DLP accepts exact private fixture classifications and does not depend on a canary prefix. This does not claim detection of all transformed or encoded leakage.

Regression tests include trailing text, hidden instructions, JSON concatenation, schema smuggling, unsupported citations, right-citation/wrong-value, malformed field types, Unicode-escaped command strings, non-canary protected secrets, and exact entity/currency/unit scoring. Results are recorded in `audit/regression_tests.txt`; no unexecuted test or favorable empirical utility is presumed.

A further independent regression verified that unsigned sibling claim metadata cannot override the authenticated body. Claim quantities compare exact decimal amounts across equivalent B/M/T representations; omitted scale means base currency units. JSON numeric overflow is rejected. These corrections precede HETE live execution and are documented in SOURCE_AMENDMENT_01.json.
