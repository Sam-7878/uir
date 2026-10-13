# Precedence and transitions

| Priority | Trigger | State | Action/output permission |
|---|---|---|---|
| 1 | policy/evidence snapshot stale | QUARANTINE | none |
| 2 | unsupported grammar or unavailable typed predicate value | CLARIFICATION | none |
| 3 | false explicit user predicate or trusted policy denial | DENY | none |
| 4 | approval required but absent/revoked | APPROVAL_PENDING | none |
| 5 | read-only grant with non-read action | READ_ONLY | no write |
| 6 | after permission admission: catalog conflict/invalid dependency | QUARANTINE | none |
| 7 | no supported emitted claims | NO_VERIFIED_ANSWER | no factual answer |
| 8 | all required authorized/dependency claims selected | FULL_VERIFIED_ANSWER | bound claims only |
| 9 | nonempty dependency-closed subset, partial permitted | PARTIAL_VERIFIED_ANSWER | bound subset only |
| 10 | incomplete selection with partial disabled | NO_VERIFIED_ANSWER | none |

Parsing occurs before an executable request exists; malformed raw text therefore
clarifies without a snapshot comparison. The table applies to compiled requests.
Changing policy/evidence versions before execution invalidates the contract.
Approval/nonce consumption is owner-supplied state in the finite tool host, not
a model assertion. Read-only is a denial reason for writes, not an answer grade.
No native prose bypasses the shared approved renderer.
