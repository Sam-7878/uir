# TCB and operational assumptions

The TCB includes session authentication, policy configuration, parser/schema,
capability and argument checks, current revision storage, evidence endorsement,
egress serialization, SQLite/runtime and the OS. The LLM is outside this set.

The research harness receives a trusted Session from the test runner; it does not
authenticate users against an identity provider. Authorization claims condition on
that trusted session. No attacker-controlled principal string grants a capability.
The local AgentDojo adapter receives a preregistered read-only capability set for
read-only legitimate tasks, and never reads the task ground-truth plan or answer.

Production threats not resolved by these experiments include a compromised
application/session issuer, stolen grants, malicious trusted evidence, signer-key
exposure, distributed TOCTOU, external tool side effects with no rollback protocol,
backend/OS/hypervisor compromise, and covert channels outside the narrow fixture
contract. Python freezing is not process isolation or memory safety.

Official CaMeL interpreter conformance tests are distinct from a full official
CaMeL model-agent benchmark. Local adapters must remain labeled approximations;
neither module tests nor read-only AgentDojo trials justify official-system superiority.
