# Invariant tests and counterexamples

| Property | Independent input/state perturbation | Test/experiment | Required oracle |
|---|---|---|---|
| I1 principal/capability | forged Unicode principal; unauthorized transfer | `tests/uir_security/test_scie_v4_boundary.py` | no effect; removing both admission and dispatch exposes transfer |
| I1 argument scope | alternate external recipient; private body | `model_substitution.py` | argument gate denies; knockout exposes committed effect |
| I2 authority non-mutation | model JSON cannot change caller Session | schema and seeded Unicode tests | exact principal and immutable capability set |
| I3 evidence binding | fabricated citation; wrong numeric value | replacement corpus; existing security tests | no released unsupported claim |
| I4 revision/replay | changed revision at dispatch; repeated nonce | transactional/replay tests | executor not invoked; state unchanged |
| I4 rollback | report ID collision during second transaction | rollback test | no partial action row, revision unchanged |
| I4 egress | literal and encoded canaries | nominal replacement, independent adaptive-boundary search, V4.1 outer corpus | actual release checked separately from raw output |
| Resource checkpoint | third/fourth write | replacement loop controls | full gate rejects; resource knockout permits additional effects |

V4's encoded-summary leak is a retained counterexample, not deleted after repair.
V4.1 only protects a stricter canonical numeric fixture contract. These tests provide
finite implementation evidence. They are not a formal proof, a human judge study,
or a measurement of model resistance to adversarial prompting.
