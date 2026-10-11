# UIR-Core Typed Reasoning IR v0.1 — Architecture Specification

- **Status:** Draft for implementation (normative where MUST/SHOULD/MAY appear)
- **Version:** `uir-ir/0.1.0`
- **Date:** 2026-10-10
- **Primary language:** Rust (UIR-Core and URI Engine)
- **Primary runtime:** WSL2 / Ubuntu 26.04, GPU inference on Linux
- **OpenBSD scope:** External interface, service edge, and operations only; not the UIR inference runtime
- **Initial domain:** Code generation, verification, debugging, and repair
- **Design principle:** An LLM's reasoning output is never equivalent to authority to execute.

## 0. Purpose, boundaries, and terminology

This specification defines four foundational contracts: **(1) Typed IR v0.1**, **(2) state transitions**, **(3) trust boundaries**, and **(4) Resolver Capability Contract (RCC)**. The objective is a small, testable, language-independent reasoning representation implemented with Rust and used to coordinate Qwen3-4B, deterministic executors, compilers, retrieval, and optional Prolog, Common Lisp, and OCaml resolvers.

**UIR** is a structured, versioned *state representation*. **URI Engine** is the orchestration process that proposes, validates, commits, and audits state transitions. **Resolver** is an external or internal computational capability invoked through a typed interface. **Verifier** checks claims and artifacts against explicitly named criteria. **Policy decision point (PDP)** decides whether a proposed action is allowed; a **policy enforcement point (PEP)** enforces that decision at the tool/OS boundary. The router selects *which method to try*, not what is trustworthy.

### v0.1 in scope

- Task, domain, claim, constraint, evidence, uncertainty, candidate, artifact, and resolver invocation records.
- Immutable identifiers, explicit provenance, stable revision numbers, deterministic transition validation, and append-only audit events.
- Read-only retrieval, sandboxed code build/test, bounded model reasoning, and explicit human escalation.
- Least-privilege capability grants and tool execution boundaries.

### Explicitly out of scope

- General-purpose formal proof of arbitrary LLM output; production-grade safety certification.
- Full ontology inference, arbitrary dynamic Lisp/Prolog code execution, automated production deployment, autonomous physical control.
- Training or fine-tuning of Qwen; replacing the underlying model runtime.
- Treating a scalar confidence value as proof or calibrated probability.

## 1. Typed IR v0.1

### 1.1 Wire contract and versioning

The **canonical exchange format** for v0.1 is JSON encoded as UTF-8. Rust types are the reference implementation, not the normative wire format. All messages MUST include `schema_version`, `id`, `revision` (for state snapshots), and `created_at` (RFC 3339 UTC). Identifiers MUST be opaque and unique within a run; use UUIDv7 or UUIDv4. All cross-references MUST resolve within the run or be explicitly declared external references. Reject unknown enum variants; unknown noncritical fields MAY be preserved in a namespaced `extensions` object. Reject unknown top-level fields by default. Canonical serialization for hashing MUST be specified before using hashes for integrity; v0.1 recommends RFC 8785 JSON Canonicalization Scheme and SHA-256 with domain-separated record-type prefixes.

A state snapshot MUST NOT embed raw secrets, raw binary artifacts, or unbounded tool output. Use content-addressed references and access-controlled storage. Large or sensitive evidence is accessed through separate scoped capabilities.

### 1.2 Primitive types and invariants

| Type | Definition / invariants |
|---|---|
| `RunId`, `ItemId`, `EventId`, `ArtifactId`, `ResolverId`, `GrantId` | Distinct newtypes around opaque IDs; no accidental mixing |
| `Revision` | Monotonically increasing `u64`; transition requires expected revision |
| `Timestamp` | UTC RFC 3339 string |
| `Digest` | Algorithm + lowercase hex digest, e.g. `sha256:...` |
| `SourceRef` | `kind`, `locator`, optional `digest`, trust zone, timestamp |
| `ResourceBudget` | `timeout_ms`, `max_output_bytes`, optional `max_cpu_ms`, `max_memory_bytes`, `max_tokens`, `max_tool_calls` |
| `DomainPath` | Nonempty stable segments such as `software.codegen.rust` |
| `ReasoningMethod` | `retrieval`, `logic`, `constraint`, `symbolic`, `deterministic`, `llm`, `compiler`, `test`, `human` |
| `EvidenceStatus` | `unverified`, `supported`, `conflicted`, `refuted`, `insufficient` |
| `ItemStatus` | `proposed`, `active`, `resolved`, `blocked`, `superseded` |

`SourceRef.trust_zone` MUST NOT itself imply truth. `supported` means supported *under the recorded verifier, scope, and evidence*, not universally true. Do not equate a compiler success with functional correctness.

### 1.3 State structure

```rust
// Illustrative Rust model, not a complete compiling crate.
struct UirState {
    schema_version: String, // "uir-ir/0.1.0"
    id: RunId,
    revision: u64,
    created_at: Timestamp,
    updated_at: Timestamp,
    objective: Objective,
    items: Vec<ReasoningItem>,
    edges: Vec<Relation>,
    pending: Vec<InvocationId>,
    artifacts: Vec<ArtifactRef>,
    policy_set: Vec<PolicyRef>,
    last_event_hash: Option<Digest>,
}

enum ReasoningItem {
    Requirement(Requirement),
    Claim(Claim),
    Constraint(Constraint),
    Evidence(Evidence),
    Uncertainty(Uncertainty),
    Candidate(Candidate),
    Verification(Verification),
    Decision(Decision),
}

enum RelationKind {
    Supports, Refutes, DependsOn, Constrains,
    DerivedFrom, Resolves, Supersedes, RelatedTo,
}
```

Every `ReasoningItem` MUST carry an `id`, `status`, `created_at`, `provenance`, and `scope`. Item payloads MUST be tagged with a discriminator (`kind`) on the wire. `Relation` contains `from`, `to`, `kind`, and optional `justification_ref`. An edge MUST NOT silently change the status of its target. Cycles MAY exist for `related_to`; dependency cycles MUST be reported to a validation resolver rather than silently accepted.

### 1.4 Minimum item payloads

| Item | Required payload |
|---|---|
| `Requirement` | `statement`, `acceptance_criteria[]`, `priority`, `source_ref` |
| `Claim` | `proposition`, `evidence_status`, `evidence_refs[]`, `source_ref` |
| `Constraint` | `predicate`, `severity` (`must`, `should`, `prefer`), `scope`, `source_ref` |
| `Evidence` | `source_ref`, `observation`, `method`, `observed_at`, optional `artifact_ref` |
| `Uncertainty` | `question`, `candidate_refs[]`, `missing_evidence[]`, `resolution_policy`, `status` |
| `Candidate` | `proposal`, `assumption_refs[]`, `constraint_refs[]`, `artifact_refs[]` |
| `Verification` | `target_ref`, `verifier_id`, `criteria_refs[]`, `outcome`, `evidence_refs[]` |
| `Decision` | `selected_refs[]`, `rejected_refs[]`, `rationale_refs[]`, `policy_decision_ref`, `decision_kind` |

`Verification.outcome` is one of `pass`, `fail`, `inconclusive`, `error`; `error` denotes a verifier failure, not proof that a candidate is wrong. Constraints with severity `must` are non-overridable by ordinary resolver output. An uncertainty may be marked `resolved` only with a recorded resolution event and linked evidence or an explicitly labeled human decision.

### 1.5 Example minimal JSON snapshot

```json
{
  "schema_version": "uir-ir/0.1.0",
  "id": "0199a000-0000-7000-8000-000000000001",
  "revision": 0,
  "created_at": "2026-10-10T00:00:00Z",
  "updated_at": "2026-10-10T00:00:00Z",
  "objective": {"domain": "software.codegen.rust", "task": "repair", "summary": "Handle zero divisor"},
  "items": [
    {"kind": "requirement", "id": "req-1", "status": "active", "created_at": "2026-10-10T00:00:00Z", "scope": "src/math.rs", "provenance": {"source_kind": "user", "source_ref": "prompt:1"}, "statement": "Zero divisor returns None", "acceptance_criteria": ["test_divide_zero"], "priority": "must", "source_ref": "prompt:1"},
    {"kind": "uncertainty", "id": "unc-1", "status": "active", "created_at": "2026-10-10T00:00:00Z", "scope": "src/math.rs", "provenance": {"source_kind": "engine", "source_ref": "parse:1"}, "question": "Does current implementation satisfy req-1?", "candidate_refs": [], "missing_evidence": ["test output"], "resolution_policy": "run sandboxed test"}
  ],
  "edges": [], "pending": [], "artifacts": [], "policy_set": [], "last_event_hash": null
}
```

The sample uses compact string IDs for readability; a strict production schema MUST enforce the selected ID format consistently. A JSON Schema and a Rust/Serde conformance suite are required before declaring v0.1 frozen.

## 2. State transition rules

### 2.1 State machine

The run lifecycle is `created → active → {completed | blocked | failed | cancelled}`. `blocked` MAY return to `active` only through a new authorized `resume` event; terminal states `completed`, `failed`, and `cancelled` are immutable. A completed run can be superseded by a **new** run, never reopened in place.

Item lifecycle is `proposed → active → {resolved | blocked | superseded}`; `blocked → active` requires new evidence, a policy change, or human input. `resolved` and `superseded` are immutable; corrections are new items linked by `supersedes`. Evidence is append-only. A new conflicting observation MUST NOT erase an older one.

### 2.2 Event-sourced transitions

The engine MUST append an event before publishing a new committed snapshot. The event includes `event_id`, `run_id`, `expected_revision`, `actor`, `operation`, `input_refs`, `proposed_changes`, `policy_decision_ref`, `timestamp`, and `previous_event_hash`. A transaction commits only if validation and authorization succeed and the expected revision matches. Increment revision exactly once per committed event. Failed proposals are recorded as rejected audit events but MUST NOT mutate the committed state.

| Operation | Preconditions | Postconditions |
|---|---|---|
| `create_run` | Valid objective, schema and principal | Revision 0, `created` |
| `activate_run` | Run `created`, policy permits | Run `active` |
| `add_item` | Active run, valid type, scoped actor | New `proposed` or `active` item |
| `propose_invocation` | Active run, selected resolver, budget | Invocation request recorded; no execution yet |
| `authorize_invocation` | Capability check, PDP approval, budget | Time-bound invocation grant issued |
| `commit_result` | Invocation ID matches, schema valid, verifier result recorded | Append evidence/items; release invocation |
| `resolve_uncertainty` | Supporting evidence or explicit human decision | Mark uncertainty `resolved`, preserve provenance |
| `block_item` | Missing evidence, denial, or unsafe condition | Item `blocked`, reason recorded |
| `complete_run` | Acceptance criteria satisfied or explicit qualified completion | Run `completed`, residuals disclosed |
| `fail_or_cancel` | Authorized actor and reason | Terminal status; revoke grants |

### 2.3 Non-negotiable invariants

1. **No direct resolver mutation:** resolvers only return proposals and evidence.
2. **No privilege from inference:** a model-generated recommendation cannot mint or widen a capability grant.
3. **No silent uncertainty deletion:** unresolved, contradicted, and unverified claims remain traceable.
4. **No self-verification shortcut:** a resolver's own success claim is not independent verification; separate tests/verifiers are needed when required by policy.
5. **No policy downgrade:** a lower-trust source cannot override a `must` or `forbid` rule.
6. **No execution on stale state:** verify `expected_revision`, resource scope, grant expiry, and replay protection before execution.
7. **No infinite repair loops:** bounded retries, tool calls, wall time, and tokens; exhaustion leads to `blocked`/`failed`/human escalation.
8. **No claim of proof from a test pass:** verification scope is always explicit.

### 2.4 Code generation / repair example

`Requirement → Candidate patch → Unverified artifact → Sandboxed compile/test → Evidence → Verification → (Accept | Diagnose | Retry | Escalate)`. A compiler failure is evidence of a particular failure mode, not a blanket reason to rerun the LLM. The router MAY select a deterministic patch, logic resolver, or Qwen according to residual uncertainty, risk, and budget. A passing unit test does not authorize production deployment.

## 3. Trust boundaries and threat model

### 3.1 Deployment and zones

```text
[Zone E: External users / repositories / web / documents]
       | untrusted data, authenticated transport
       v
[Zone G: Edge API / service gateway (optional OpenBSD + Rust)]
       | authenticated principal + bounded request
       v
[Zone C: UIR-Core / URI Engine (WSL2 Ubuntu 26.04, Rust)]
       | typed IPC/RPC + per-invocation capability
       +----> [Zone R: Resolver processes (Qwen/Linux GPU, Prolog, Lisp, OCaml, Zig)]
       +----> [Zone S: Code build/test sandbox, no ambient credentials]
       +----> [Zone D: Evidence/artifact store, scoped access]
       |
       v
[Zone X: External side effects (filesystem writes, Git, network, deploy)]
       ^ must pass independent PEP / explicit authorization
```

OpenBSD is confined to external interfaces, edge services, and operations. The UIR core and LLM runtime remain on WSL2/Ubuntu 26.04. WSL2 is a development environment, **not by itself a hardened hostile-code sandbox**. Untrusted generated code MUST run in an independently constrained environment (e.g. dedicated VM/microVM or equivalent OS-enforced isolation), with restricted filesystem, networking, credentials, and resources. For high-risk tests, do not rely on containers alone without a threat-model-specific isolation assessment.

### 3.2 Trust and data-flow rules

| Boundary | Threat | Required control |
|---|---|---|
| External → Gateway | injection, oversized payloads, forged identity | authentication, rate limits, size limits, structured validation |
| Gateway → Core | identity/tenant confusion | principal binding, scoped authorization, mTLS where networked |
| Retrieval → IR | prompt injection, source poisoning | treat content as data, provenance, no authority escalation |
| Core → Resolver | excessive privileges, prompt exfiltration | least-privilege grants, input minimization, timeout and quotas |
| Resolver → Core | forged success, malformed output | strict schema, invocation correlation, evidence verification |
| Core → Sandbox | arbitrary code execution, escape | isolated runtime, deny network by default, no host secrets |
| Core → External action | destructive writes/deploy | separate authorization and enforcement, human approval when required |
| Logs → Observability | leakage of secrets/PII | redaction, access controls, retention policy |

### 3.3 Threat assumptions and limitations

Threats include prompt injection in repositories, malicious dependencies, poisoned retrieved documents, tool-result forgery, path traversal, command injection, denial of service, confused-deputy behavior, stale grants, and supply-chain compromise. Rust memory safety reduces certain classes of memory errors but does not establish semantic correctness, eliminate `unsafe`/FFI risks, or guarantee zero trust. OpenBSD `pledge`/`unveil` controls apply only where those processes actually run. A GPU inference server MUST NOT receive blanket filesystem or network permissions merely because it is local.

## 4. Resolver Capability Contract (RCC) v0.1

### 4.1 Design

The RCC separates **resolver identity**, **capabilities declared**, **capabilities granted for one invocation**, **resource budgets**, and **evidence returned**. A declaration is not authorization. Grants are created by the trusted policy service and checked again by the enforcement point. The router can request a resolver but cannot self-authorize it.

### 4.2 Resolver manifest

```json
{
  "contract_version": "uir-rcc/0.1.0",
  "resolver_id": "qwen3-4b-local",
  "implementation": {"kind": "rpc", "endpoint_ref": "service:qwen-local"},
  "methods": ["llm"],
  "domains": ["software.codegen", "software.debugging"],
  "input_schema_ref": "schema:uir-reasoning-request/0.1.0",
  "output_schema_ref": "schema:uir-resolver-result/0.1.0",
  "requested_capabilities": ["model.infer"],
  "side_effect_class": "none",
  "limits": {"timeout_ms": 30000, "max_output_bytes": 131072, "max_tokens": 4096},
  "integrity": {"artifact_digest": "sha256:REPLACE_WITH_REAL_DIGEST"}
}
```

Manifest integrity MUST be checked against a trusted allowlist or signature before registration. Example digests are placeholders and MUST NOT be accepted in deployment.

### 4.3 Capability vocabulary

Use stable strings with scoped resources and explicit effect class:

| Capability | Meaning | Default |
|---|---|---|
| `model.infer` | Call named local model | Deny |
| `knowledge.read` | Read allowed knowledge subset | Deny |
| `artifact.read` | Read specific artifact refs | Deny |
| `artifact.propose_write` | Return a patch proposal, not write host files | Deny |
| `logic.query` | Query an approved rule base | Deny |
| `compiler.run` | Compile in sandbox | Deny |
| `test.run` | Run bounded tests in sandbox | Deny |
| `network.fetch` | Fetch allowlisted endpoint | Deny |
| `workspace.write` | Write scoped workspace files through PEP | Deny |
| `repo.commit` | Commit to named repository/ref | Deny |
| `deploy.execute` | Deployment side effect | Deny + human approval |

`policy.modify`, `grant.mint`, and unrestricted `host.shell` are **not** grantable to ordinary resolvers in v0.1. Capabilities MUST be scoped by resource, principal, run, invocation, expiry, and budget; wildcard resource scopes are disallowed by default.

### 4.4 Invocation request and grant

```json
{
  "contract_version": "uir-rcc/0.1.0",
  "invocation_id": "inv-42",
  "run_id": "0199a000-0000-7000-8000-000000000001",
  "expected_revision": 4,
  "resolver_id": "rust-test-runner",
  "method": "test",
  "input_refs": ["artifact:patch-7", "requirement:req-1"],
  "requested_capabilities": [{"name": "test.run", "resource": "sandbox:run-1"}],
  "budget": {"timeout_ms": 10000, "max_output_bytes": 65536, "max_cpu_ms": 5000, "max_memory_bytes": 536870912},
  "idempotency_key": "run-1-rev4-test-7"
}
```

The authorization service returns a short-lived grant containing `grant_id`, `invocation_id`, `principal_id`, `approved_capabilities`, `expires_at`, `policy_decision_ref`, and an integrity-protected token or equivalent server-side binding. The grant MUST be bound to the exact invocation and cannot be reused to expand scope. The PEP checks it immediately before execution; revocation MUST be possible for long-running invocations.

### 4.5 Resolver result

```json
{
  "contract_version": "uir-rcc/0.1.0",
  "invocation_id": "inv-42",
  "resolver_id": "rust-test-runner",
  "status": "succeeded",
  "proposed_items": [],
  "evidence": [{"kind": "test_report", "artifact_ref": "artifact:test-report-8", "digest": "sha256:REPLACE_WITH_REAL_DIGEST"}],
  "artifact_refs": ["artifact:test-report-8"],
  "resource_usage": {"elapsed_ms": 127, "peak_memory_bytes": 104857600},
  "diagnostics": [],
  "claims": ["test command exited with code 0"]
}
```

Result status is `succeeded`, `failed`, `timeout`, `denied`, or `error`. `succeeded` means the invocation completed as specified, **not** that the produced code is correct. Results MUST be schema-validated, matched to invocation/grant, checked against budgets, and independently verified where policy requires. Raw stdout/stderr MUST be truncated and stored as artifacts, never blindly injected into prompts or logs.

### 4.6 Resolver routing and failure behavior

Routing considers domain relevance, reasoning method, estimated uncertainty reduction, reliability, resource costs, latency, and risk. It MUST filter unauthorized or unavailable resolvers before ranking. Selection decisions MUST record considered candidates and why one was chosen. Timeouts, denial, and verifier failures return structured results and preserve residual uncertainty. Retries require explicit retry policy and new budget accounting. Never silently fall back to a more privileged resolver.

## 5. Suggested Rust workspace and portability

```text
uir/
  Cargo.toml
  crates/
    uir-types/       # newtypes, tagged IR, schema_version
    uir-state/       # transition validation, event log
    uir-policy/      # PDP, capability grants, policy evaluation
    uir-router/      # domain + method routing
    uir-resolver/    # RCC types, client/server interfaces
    uir-evidence/    # provenance and artifact digests
    uir-runtime/     # URI Engine orchestration
    uir-security/    # PEP adapters, sandbox policy
  resolvers/
    qwen/            # local Linux GPU inference adapter
    compiler-test/   # isolated build/test runner
    prolog/          # optional
    common-lisp/     # optional
    ocaml/           # optional
    zig/             # optional
  schemas/
  examples/
  tests/
  docs/
```

Recommended implementation order: `uir-types` → `uir-state` → `uir-resolver` → `uir-policy`/PEP → `compiler-test` → Qwen adapter → router. Keep the core protocol independent of implementation language. Prefer process isolation and typed IPC/RPC over embedding multiple runtimes via FFI at v0.1. OCI/container and GPU runtime specifics are adapters, not part of the IR schema.

## 6. Acceptance tests for v0.1

**Type/schema:** reject invalid enum tags, duplicate IDs, unresolved references, missing provenance, oversize fields, and unsupported major schema versions.

**Transitions:** reject stale revisions; verify monotonic revisions, append-only evidence, no terminal-state mutation, and correct handling of concurrent results.

**Trust boundary:** prompt-injection text in a retrieved file MUST NOT become a tool instruction; forged resolver results and mismatched invocation IDs MUST be rejected; generated code MUST NOT read host secrets or access network without grants.

**Capabilities:** deny all undeclared actions; deny expired, replayed, widened, or wrong-run grants; enforce timeout/output/memory limits; require explicit human approval for deploy.

**Code generation end-to-end:** requirement → Qwen proposal → sandboxed compile/test → structured evidence → verified/blocked state; failing test leads to bounded repair or escalation; record tokens, latency, total memory, peak VRAM, test success, and security denials.

### Minimal exit criteria

1. All four contracts are represented by checked-in Rust types and JSON Schemas.
2. Golden JSON fixtures round-trip through Rust serialization/deserialization.
3. A test resolver cannot mutate committed UIR state or mint grants.
4. An untrusted code artifact cannot execute outside a sandboxed, authorized path.
5. An end-to-end repair run records a reproducible decision/evidence trace.
6. No unbounded loops, network calls, or production writes are available by default.

## 7. Open design decisions (must be resolved before v0.1 freeze)

- Exact canonical JSON Schema and Rust `serde` representation, including strict UUID/newtype validation.
- Policy language and precedence (`must`, `forbid`, `prefer`), conflict resolution, and human approval semantics.
- Event store transaction and hash-chain implementation; whether to sign checkpoints.
- Isolation backend for hostile code under WSL2 (prefer dedicated Linux VM/microVM rather than assuming WSL2 itself is sufficient).
- Artifact store ACLs, secret management, and tenant separation.
- Resolver transport (local Unix sockets vs authenticated RPC), request size and cancellation protocol.
- Version negotiation, migration rules, and compatibility test matrix.
- Evidence verifier taxonomy and confidence calibration policy.

## 8. Immediate first milestone

Build a **single-user, local-only, non-deploying** code repair prototype on WSL2/Ubuntu 26.04. Implement Rust UIR types/state, one deterministic sandboxed compiler/test resolver, one Qwen3-4B adapter, a deny-by-default capability policy, and a trace viewer. Do not introduce Prolog/Lisp/OCaml until the protocol and test fixtures are stable. Then add each as a separately measured resolver without changing the IR contract.

---

**Core rule:** *Represent uncertainty explicitly; choose the cheapest authorized resolver capable of reducing it; verify the result; commit only a validated state transition. Never turn model output into execution authority by implication.*
