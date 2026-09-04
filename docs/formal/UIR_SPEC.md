# Universal Intermediate Representation (UIR) Specification
## Architectural Reference for Policy-Constrained Multilingual Small Language Model Agents

**Document Version:** 4.0.0  
**Target Manuscript:** *A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents*  
**Scope:** Formal contract, data representations, invariant enforcement, and execution boundaries.

---

## 1. Introduction and Architectural Motivation

The Universal Intermediate Representation (UIR) serves as a **Security Reference Representation (SRR)** and **Semantic Canonicalization Layer** for Small Language Model (SLM) agents operating in mission-critical and enterprise domains. 

In traditional Retrieval-Augmented Generation (RAG) architectures, the language model occupies both the semantic interpretation space and the policy enforcement boundary. Consequently, adversarial manipulation of natural language inputs (such as indirect prompt injection, jailbreaking, and entity spoofing) can bypass safety constraints by exploiting the probabilistic nature of autoregressive token generation.

UIR enforces the principle:

$$\text{Prompt} \neq \text{Authority}$$

Natural language prompts provide *semantic intent* and *candidate parameters*, but they cannot grant execution privileges, alter domain policies, or inject unverifiable facts. The UIR compiler isolates the language model into an untrusted transformation component, placing policy enforcement and evidence verification in deterministic subsystems outside the model.

```
+---------------------+      +---------------------+
| Natural Language    |  --> | Multilingual        |
| Request (KO / EN)   |      | Frontend Parser     |
+---------------------+      +---------------------+
                                        |
                                        v
                             +---------------------+
                             | Canonical Typed     |
                             | UIR Abstract Syntax |
                             +---------------------+
                                        |
                                        v
                             +---------------------+
                             | Deterministic       |
                             | Policy Engine L0-L3 |
                             +---------------------+
                               /                 \
                     [Reject / Quarantine]    [Allow]
                             /                     \
                            v                       v
                   +-----------------+    +-------------------+
                   | Fail-Closed     |    | Verified Grounding|
                   | Typed Reject    |    | & Context Binding |
                   +-----------------+    +-------------------+
                                                    |
                                                    v
                                          +-------------------+
                                          | Constrained SLM   |
                                          | Inference (Phi3.5)|
                                          +-------------------+
                                                    |
                                                    v
                                          +-------------------+
                                          | Output Guard &    |
                                          | Deterministic     |
                                          | Filter/Renderer   |
                                          +-------------------+
```

---

## 2. Core Data Structures

A canonical UIR document $\mathcal{U}$ is structured as a typed JSON object comprising five primary sections:

```json
{
  "uir_version": "4.0.0",
  "metadata": {
    "request_id": "req-98b2-4f1a",
    "source_language": "ko",
    "source_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "compiler_version": "poa-uir-0.4.0",
    "domain": "enterprise_finance",
    "created_at": "2026-09-04T10:00:00Z"
  },
  "semantics": {
    "intent": "VERIFY",
    "target": {
      "entity_type": "corporation",
      "entity_id": "QV0000"
    },
    "parameters": {
      "metric": "assets",
      "period": "2022"
    }
  },
  "conditions": {
    "operator": "AND",
    "exprs": [
      {
        "operator": "EQ",
        "lhs": "entity_verified",
        "rhs": true
      },
      {
        "operator": "GE",
        "lhs": "period",
        "rhs": 2020
      }
    ]
  },
  "policy": {
    "level": "L2_ENTERPRISE",
    "enforcement": "BLOCK_EXECUTION",
    "rules": [
      "RULE_AUTH_ENTITY_MANDATORY",
      "RULE_IMMUTABLE_PROVENANCE_REQUIRED"
    ]
  },
  "execution_contract": {
    "mode": "VERIFIED_ONLY",
    "failure_behavior": "REJECT",
    "output_format": "STRUCTURED_JSON",
    "unsupported_claim_behavior": "FILTER_AND_RENDER"
  }
}
```

### 2.1 Metadata Section
- `request_id`: Globally unique identifier for correlation and audit tracing.
- `source_language`: ISO-639-1 code (`ko`, `en`, etc.) of the input surface text.
- `source_hash`: Cryptographic SHA-256 digest of the raw natural language input.
- `compiler_version`: Exact build identifier of the transpiler.
- `domain`: Registered security domain (`enterprise_finance`, `statutory_compliance`, etc.).
- `created_at`: ISO-8601 UTC timestamp.

### 2.2 Semantics Section
- `intent`: Canonical action enum (`SUMMARIZE`, `EXTRACT`, `ANALYZE`, `COMPARE`, `CAUSE_TRACE`, `VERIFY`).
- `target`: Subject entity comprising `entity_type` and authoritative `entity_id`.
- `parameters`: Key-value dictionary of domain-specific attributes (e.g., metric names, accounting periods).

### 2.3 Conditions Section
A recursive abstract syntax tree (AST) defining typed boolean predicates over environment state, input attributes, and verification gates. Operators include:
- Relational: `EQ`, `NE`, `GT`, `GE`, `LT`, `LE`
- Logical: `AND`, `OR`, `NOT`
- Modal/Exceptional: `EXCEPT`

### 2.4 Policy Section
- `level`: Hierarchical precedence layer:
  - `L0_SYSTEM`: Host system invariants, execution timeouts, memory bounds.
  - `L1_DOMAIN`: Regulatory constraints, privacy firewalls (e.g., GDPR, SEC rules).
  - `L2_ENTERPRISE`: Organization-specific access controls and disclosure restrictions.
  - `L3_PREFERENCE`: User formatting preferences.
- `enforcement`: Action taken upon violation: `BLOCK_EXECUTION`, `REJECT`, `GRACEFUL_DEGRADATION`, `QUARANTINE`.
- `rules`: List of referenced rule identifiers evaluated deterministically.

### 2.5 Execution Contract
Governs downstream execution behavior:
- `mode`: `VERIFIED_ONLY`, `DRY_RUN`, `STANDARD`.
- `failure_behavior`: Protocol on invariant failure (`REJECT`, `DEGRADE`, `QUARANTINE`, `ABORT`).
- `output_format`: Expected response shape (`STRUCTURED_JSON`, `GROUNDED_NATURAL_LANGUAGE`).
- `unsupported_claim_behavior`: Post-generation enforcement action (`REJECT`, `REMOVE`, `FLAG`, `FILTER_AND_RENDER`).

---

## 3. Formal System Invariants

The UIR execution environment guarantees the following invariants:

### INV-1: Fail-Closed Execution
$$\forall \mathcal{U}, \quad \text{EvalPolicy}(\mathcal{U}) \in \{\text{Reject}, \text{Quarantine}\} \implies \text{InvokeExecutor}(\mathcal{U}) = \bot \land \text{InvokeRenderer}(\mathcal{U}) = \bot$$
If a request violates any policy rule at levels L0–L2 or fails entity verification, the language model executor and natural language renderer are strictly unreachable. The system emits a structured, typed rejection without invoking the probabilistic model.

### INV-2: Verified-Claim Acceptance
$$\forall c \in \text{AcceptedClaims}(\mathcal{R}), \quad \exists v \in \mathcal{V}_{\text{facts}} \quad \text{s.t.} \quad \text{ResolvesTo}(c, v) \lor \text{PermittedTransformation}(c, v)$$
No factual claim $c$ within the final output $\mathcal{R}$ is accepted unless it directly binds to an immutable, authoritative verified fact $v$ retrieved from the ground-truth registry or produced via an approved deterministic calculation.

### INV-3: Numeric Binding Invariance
$$\forall c \in \text{AcceptedNumericClaims}(\mathcal{R}), \quad \text{Value}(c) = \text{Value}(\text{SourceFact}(c)) \land \text{Unit}(c) = \text{Unit}(\text{SourceFact}(c))$$
Authoritative numeric values, algebraic signs, scaling units, and temporal periods cannot be mutated, approximated, or rounded by the language model. The output filter strictly binds numbers from the verified fact table.

### INV-4: Semantic Digest Invariance
$$\text{Digest}(\mathcal{U}) = \text{SHA256}(\text{Canonicalize}(\mathcal{U} \setminus \text{ExcludedMetadata}))$$
The cryptographic digest of a UIR document depends solely on its canonical semantic fields, parameters, conditions, and policies. Transient metadata (e.g., timestamps, non-semantic tracing tags) do not alter the semantic digest.

### INV-5: Cross-Language Canonicalization Equivalence
$$\forall Q_{\text{ko}}, Q_{\text{en}} \in \text{ParallelRequests}, \quad \text{Digest}(\text{Transpile}_{\text{ko}}(Q_{\text{ko}})) = \text{Digest}(\text{Transpile}_{\text{en}}(Q_{\text{en}}))$$
Semantically identical queries in Korean and English map to identical canonical UIR ASTs under defined controlled-language templates, ensuring cross-lingual policy consistency.
