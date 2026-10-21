# A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents

> **SCI Manuscript Preview — Final Evidence Freeze (Phase UIR-4F)**
>
> This document is a manuscript-level preview for PI review before section-by-section LaTeX refinement.
> Numerical claims are based on the final frozen evidence package through Phase UIR-4F.
> Reference markers such as `[REF]` are intentionally left for final bibliography verification.
>
> **Evidence-source note for PI review:** direct inspection of the frozen D1 raw file gives 596/600 schema-valid generations (**99.33%**). Some auto-generated Phase-4F prose/tables still show 100.00%. This preview uses **99.33%**, the raw-evidence value. No new experiment is required; the final LaTeX table generator should be corrected before submission.

---

## Abstract

Small language models (SLMs) are attractive for private, local, and resource-constrained agents, but their probabilistic outputs are difficult to reconcile with deterministic authorization, multilingual consistency, evidence provenance, and fail-closed execution. Retrieval-augmented generation (RAG), tool calling, guardrails, and grammar-constrained generation can reduce individual failure modes, yet they typically leave the language model with substantial authority over how retrieved information is interpreted and which claims are emitted.

This paper presents a **Universal Intermediate Representation (UIR)** for policy-constrained multilingual SLM agents. UIR is a language-independent, policy-evaluable execution contract positioned between controlled-language frontends and executable agent behavior. Korean and English requests are compiled into a typed representation containing semantics, policy constraints, execution requirements, provenance bindings, and an explicit output contract. Deterministic entity verification, policy evaluation, and verified-fact binding are performed before or around SLM rendering. The accepted-output transition is therefore separated from free-form neural generation: **prompt is not authority**.

The final evaluation combines multilingual semantic tests, a 600-case authentic internal campaign, a 50-case adversarial subset, a 418-case commit-eligible utility cohort, a 600-case genuine grammar-constrained decoding baseline, two open-weight model families, and 200-case FinQA and HaluEval-QA external evaluations. On the internal campaign, the final UIR pipeline observed **0 accepted unsupported claims** (Wilson 95% CI: 0.00–0.64%) and **0% adversarial attack success**, while Naive RAG showed 49.33% accepted unsupported claims and 92% adversarial attack success. UIR achieved **53.59% complete claim-set accuracy**, statistically comparable to Naive RAG at 53.11% (exact McNemar \(p=0.50\)), but increased **supported-answer coverage to 65.07%** by retaining **11.48% safe partial answers**. A genuine token-level constrained-decoding baseline achieved 99.33% schema validity but still accepted unsupported claims in 20.83% of cases, showing that syntactic control alone does not establish evidence authority.

External evaluation exposed an important boundary. On FinQA and HaluEval-QA, UIR consistently prevented unsupported generated material from reaching accepted output under the evaluated contracts, but task accuracy varied substantially with the backbone and contract fit. For example, Qwen2.5-7B achieved 21.5% FinQA execution accuracy under UIR, whereas its HaluEval UIR outputs had 50% raw semantic accuracy but 0% contract validity and therefore 0% accepted end-to-end accuracy. These results demonstrate that **model semantic correctness, contract validity, accepted-system correctness, and system safety are distinct properties**.

The evidence supports a bounded conclusion: UIR does not universally improve the reasoning ability of the underlying model. Instead, it provides a deterministic policy-and-evidence control boundary that converts uncertain or unsupported generations into verified answers, safe partial answers, or explicit rejection rather than silently accepted fabrication.

**Keywords:** Universal Intermediate Representation, Small Language Model, Multilingual Agent, Policy Engine, Verified Generation, Grounded Generation, Neuro-Symbolic AI, Constrained Decoding, RAG, Explainable AI

---

# 1. Introduction

Language models are increasingly used as interfaces to enterprise databases, retrieval systems, analytical tools, and autonomous software agents. Their linguistic flexibility, however, creates an architectural tension. Natural-language interpretation and generation are probabilistic, while enterprise authorization, accounting rules, compliance requirements, provenance, and execution semantics are often deterministic.

A conventional LLM agent commonly approximates the following pipeline:

```text
user request
→ prompt / retrieval
→ language model
→ answer or tool action
```

This design gives the model considerable implicit authority. Even when the correct document has been retrieved, the model must still decide which evidence is relevant, how rules should be applied, whether an exception overrides a general rule, and which generated claims are safe to emit. RAG improves access to knowledge but does not, by itself, determine how that knowledge should govern execution. Grammar-constrained decoding can guarantee an output shape without guaranteeing that the values inside the structure are authorized or supported. Guardrails may block classes of outputs, but they do not necessarily create a reproducible decision trace connecting facts, rules, policy, and execution.

The problem becomes more pronounced in multilingual agents. Semantically equivalent Korean and English requests may use different surface forms while referring to the same intent, target, conditions, and policy obligations. If authorization is performed directly over surface text or free-form model reasoning, linguistic variation can leak into execution behavior.

We therefore investigate a different architectural principle:

> **Prompt is not authority.**

The language model may participate in semantic interpretation and rendering, but final execution and accepted factual output are governed by a typed, machine-verifiable intermediate contract.

We propose a **Universal Intermediate Representation (UIR)** that connects:

```text
multilingual controlled request
→ canonical semantics
→ explicit policy constraints
→ verified execution contract
→ verified fact binding
→ constrained model rendering
→ accepted-output validation
```

UIR is not intended to make an SLM universally more capable. Its purpose is to reduce the amount of authority delegated to probabilistic generation.

The final study addresses the following research questions.

### RQ1 — Multilingual semantic normalization
Can Korean and English controlled requests be compiled into a shared canonical semantic representation?

### RQ2 — Policy and evidence safety
Can deterministic policy and evidence binding prevent unsupported or unauthorized model output from entering accepted system output?

### RQ3 — Safety–utility trade-off
Does fail-closed verification merely cause excessive refusal, or can verified partial answers recover useful information without accepting unsupported claims?

### RQ4 — Alternative controls
How does UIR compare with RAG, existence checks, tool calling, guardrails, corrective retrieval, graph-structured RAG, JSON-schema prompting, and genuine token-level grammar-constrained decoding?

### RQ5 — External generalization
How does the architecture behave on independently authored numerical-reasoning and hallucination-detection benchmarks?

### RQ6 — Model dependence
Which observed properties belong to the deterministic UIR boundary, and which remain dependent on the underlying language model?

The contributions are:

1. **A typed multilingual UIR execution contract** that separates source-language interpretation from policy, evidence, and execution authority.
2. **A deterministic policy-and-evidence enforcement boundary** with explicit fail-closed behavior and verified-fact binding.
3. **A verified partial-answer mechanism** that distinguishes complete answers, safe partial answers, and no-verified-answer outcomes.
4. **A formal specification** including an EBNF grammar, typed condition AST, operational policy semantics, semantic digests, and conditional safety invariants.
5. **A broad empirical comparison** against nine internal pipelines plus a genuine token-level constrained-decoding baseline.
6. **An external cross-model study** on FinQA and HaluEval-QA using Phi-3.5-mini and Qwen2.5-7B.
7. **A negative-result analysis** showing that deterministic verifiability does not imply universal semantic accuracy or reasoning improvement.

---

# 2. Related Work

## 2.1 Retrieval-Augmented Generation

RAG augments model generation with retrieved external information and is now a standard method for grounding language-model responses [REF-RAG]. Its main strength is improving access to task-relevant knowledge. However, retrieval and authorization are different operations. A retrieved passage may be correct while a generated interpretation remains unsupported, unauthorized, or inconsistent with organizational policy.

Advanced variants such as corrective retrieval, self-reflective retrieval, and graph-based retrieval improve retrieval quality or relational context [REF-CRAG, REF-SELF-RAG, REF-GRAPHRAG]. In this study, mechanism-matched corrective and graph-structured retrieval pipelines are treated as comparison conditions rather than as policy engines.

## 2.2 Tool-Calling Agents

Tool and function calling can constrain an agent to authoritative APIs and reduce free-form factual generation [REF-TOOL]. Nevertheless, tool selection, argument generation, sequencing, and interpretation may remain model-controlled. UIR differs by representing policy and evidence requirements before accepted execution rather than relying solely on a tool-use protocol.

## 2.3 Guardrails

Guardrail systems provide input/output filtering, topical constraints, safety policies, and validation layers [REF-GUARDRAILS]. Guardrails can be highly effective, and our internal experiments confirm that a guardrail-style pipeline can achieve strong safety. UIR is complementary in spirit but places greater emphasis on typed semantic compilation, explicit policy evaluation, fact-reference binding, and a reproducible execution contract.

## 2.4 Structured and Grammar-Constrained Generation

JSON schemas, grammar-constrained decoding, finite-state constraints, and token-level logits masking can guarantee structural properties of generated output [REF-CONSTRAINED]. We distinguish **syntactic validity** from **semantic authorization**. A perfectly valid JSON object may still contain an unsupported entity, value, or policy-violating action.

This distinction is tested directly with `lm-format-enforcer` as a genuine token-level constrained-decoding baseline.

## 2.5 Intermediate Representations and Domain-Specific Languages

Compiler intermediate representations normalize source-language syntax into structures that support type checking, optimization, and deterministic execution. Domain-specific languages similarly constrain expressiveness to make specialized tasks analyzable and reproducible [REF-IR-DSL].

Our work extends this compiler principle to multilingual AI agents. The UIR is not merely an AST serialization. It is an execution contract that links:
- user semantics,
- policy constraints,
- verified resources,
- output admissibility,
- provenance,
- and execution outcomes.

## 2.6 Neuro-Symbolic and Explainable AI

Neuro-symbolic systems combine learned representations with symbolic constraints or logic [REF-NEUROSYMBOLIC]. Explainable AI often attempts to explain a model decision after the fact [REF-XAI]. UIR instead makes the deterministic decision path itself auditable. An explanation may be rendered from actual policy and evidence traces rather than generated as an unconstrained post-hoc narrative.

---

# 3. Problem Formulation

Let \(Q_l\) denote a request expressed in language \(l\), where the implemented normative language set is:

\[
l \in \{\mathrm{ko}, \mathrm{en}\}.
\]

A language-specific frontend \(T_l\) maps the request to a UIR object:

\[
U = T_l(Q_l).
\]

For supported parallel requests \(Q_{\mathrm{ko}}\) and \(Q_{\mathrm{en}}\), the desired semantic-normalization property is:

\[
\mathrm{Canon}(T_{\mathrm{ko}}(Q_{\mathrm{ko}}))
=
\mathrm{Canon}(T_{\mathrm{en}}(Q_{\mathrm{en}})),
\]

where `Canon` excludes source-specific provenance metadata that should not affect semantic equivalence.

The system then evaluates the UIR under an effective policy \(P\) and runtime context \(C\):

\[
\langle U, P, C\rangle \Downarrow D,
\]

with decision:

\[
D \in
\{\mathrm{ALLOW},
\mathrm{DENY},
\mathrm{REQUIRE\_APPROVAL},
\mathrm{READ\_ONLY},
\mathrm{CLARIFY}\}.
\]

If execution is allowed, the verified executor produces a fact set:

\[
F = E(U,P,C).
\]

The SLM renderer produces a candidate output:

\[
Y = R_{\theta}(U,F),
\]

where \(\theta\) denotes the frozen model parameters.

The final accepted output is:

\[
Y^{*}=V_{\mathrm{out}}(Y,F,U).
\]

The critical architectural distinction is:

\[
Y \neq Y^{*}.
\]

A model generation is not automatically an accepted system answer.

---

## 3.1 Four Distinct Correctness Layers

The final experiments require four correctness concepts to be separated:

\[
\boxed{
\text{Model Semantic Correctness}
\neq
\text{Contract Validity}
\neq
\text{Accepted-System Correctness}
\neq
\text{System Safety}
}
\]

A model can:
- reason correctly but violate the output contract;
- produce valid JSON containing unsupported values;
- generate unsupported text that is rejected before acceptance;
- or produce a fully verified accepted answer.

Conflating these cases produces misleading “hallucination” and accuracy metrics.

---

## 3.2 Threat Model

We consider failures including:

- unsupported factual generation,
- invalid entity use,
- policy bypass attempts,
- instruction override,
- adversarial coercion,
- malformed structured output,
- stale or cross-case fact identifiers,
- wrong metric or reporting period binding,
- numeric tampering,
- Unicode/homoglyph identifier confusion,
- and ambiguous or incomplete requests.

The architecture does **not** assume the SLM is trusted.

---

## 3.3 Conditional Safety Assumptions

The strongest UIR safety property is conditional on the following assumptions:

- **A1:** authoritative registry integrity;
- **A2:** trusted policy-store integrity;
- **A3:** correct fact-ID binding;
- **A4:** the output guard cannot be bypassed;
- **A5:** the deterministic renderer emits only accepted claims.

Under A1–A5:

> unsupported claims are unreachable in the accepted-output transition system.

This is an architectural property of the accepted-output transition system, not a claim that the language model never generates unsupported material.

---

# 4. UIR Architecture

## 4.1 Overall Processing Flow

```text
Korean / English Request
          │
          ▼
Controlled-Language Frontend
          │
          ▼
     Canonical UIR
          │
 ┌────────┼───────────┐
 ▼        ▼           ▼
Type   Entity       Policy
Check  Resolution    Engine
 └────────┼───────────┘
          ▼
   Validated Contract
          │
          ▼
  Verified Execution
          │
          ▼
   VerifiedFactSet
          │
          ▼
       SLM Renderer
          │
          ▼
   Candidate Claims
          │
          ▼
 Output Contract / Guard
          │
  ┌───────┼────────┐
  ▼       ▼        ▼
FULL    PARTIAL   REJECT
```

---

## 4.2 UIR Contract Layers

The UIR contains five conceptual layers:

```text
metadata
semantics
policy_constraints
execution_contract
output_contract
```

### Metadata
Includes:
- request identifier,
- UIR version,
- source language,
- source hash,
- compiler version,
- domain,
- provenance metadata.

### Semantics
Includes:
- intent,
- target entity,
- requested attribute/action,
- parameters,
- temporal scope,
- typed conditions.

### Policy Constraints
Policy expressions contain:
- policy layer,
- condition expression,
- decision,
- priority/precedence,
- exception rules where supported.

### Execution Contract
Defines:
- required capabilities,
- authoritative resources,
- permitted operations,
- failure behavior,
- provenance requirements.

### Output Contract
Defines:
- allowed output structure,
- accepted claim types,
- verified reference requirements,
- numeric binding behavior,
- unsupported-claim handling.

---

## 4.3 Typed Condition AST

The condition system supports typed Boolean and comparison operators such as:

```text
EQ
NE
GT
GE
LT
LE
AND
OR
NOT
EXCEPT
```

A representative type judgment is:

\[
\Gamma \vdash \mathrm{GT}(x,y):\mathrm{Bool}
\quad
\text{if}
\quad
\Gamma \vdash x:\mathrm{Number}
\land
\Gamma \vdash y:\mathrm{Number}.
\]

Ill-typed conditions fail before execution.

This design emerged as an important result of the multilingual experiments: surface-language conditions are substantially more ambiguous than explicit typed/parenthesized condition representations.

---

## 4.4 Semantic Digest

The implementation distinguishes:
- a full object digest for provenance;
- a semantic digest that excludes non-semantic fields such as request ID, source-language metadata, source hash, and creation timestamp.

This permits cross-language equivalence checks without discarding audit metadata.

---

# 5. Policy and Verified Execution

## 5.1 Prompt Is Not Authority

The policy engine evaluates the UIR rather than asking the model to decide whether its own request is permissible.

Conceptually:

```text
Natural-language request
        ↓
UIR
        ↓
Policy Engine
        ↓
ALLOW / DENY / APPROVAL / READ-ONLY / CLARIFY
```

This makes policy outcome reproducible and inspectable.

## 5.2 Authoritative Entity Resolution

Entity validity is determined by an authoritative registry rather than by model belief. Invalid or ambiguous entities can therefore fail before model inference.

## 5.3 VerifiedFactSet

Permitted execution produces typed facts with stable identifiers and provenance.

Example:

```text
Fact ID: F-2026-0017
Entity: MSFT
Metric: revenue
Period: FY2025
Value: ...
Source: SEC Companyfacts snapshot
Digest: ...
```

The model may reference these facts, but it does not create their authority.

## 5.4 FULL, PARTIAL, and NO-VERIFIED-ANSWER States

The final pipeline distinguishes:

```text
FULL_VERIFIED_ANSWER
PARTIAL_VERIFIED_ANSWER
NO_VERIFIED_ANSWER
```

Suppose the model generates:

```text
supported A
unsupported B
supported C
```

The final B6 policy may retain:

```text
A + C
```

while removing B.

This mechanism is central to the final safety–utility result.

---

# 6. Formal Safety Properties

The final specification contains mechanically tested invariants including:

### INV-1 — Fail-Closed Execution

\[
D \in \{\mathrm{DENY},\mathrm{QUARANTINE}\}
\Rightarrow
N_{\mathrm{executor}} =
N_{\mathrm{renderer}} = 0.
\]

### INV-2 — Verified-Claim Acceptance

Every accepted factual claim must resolve to a verified fact or an explicitly permitted deterministic transformation.

### INV-3 — Numeric Binding

Authoritative numeric values bound through verified references cannot be replaced by arbitrary model-generated numeric values.

### INV-4 — Semantic-Digest Invariance

Changes to excluded provenance metadata do not change semantic identity.

### INV-5 — Controlled Cross-Language Canonicalization

Within the supported Korean/English controlled grammar, declared parallel semantic requests map to equivalent canonical semantics.

These properties are presented as definitions, propositions, proof sketches, and mechanically tested invariants—not as universal guarantees about arbitrary real-world inputs.

---

# 7. Implementation

The system is implemented primarily in Rust for the core execution path, with Python evaluation tooling.

Representative workspace components include:

```text
poa-core
poa-protocol
poa-uir
poa-sandbox
evaluation/
```

The UIR layer remains separated from the domain-neutral execution kernel.

Two local open-weight model families were evaluated:

### Phi-3.5-mini-instruct
- approximately 3.8B parameters;
- frozen local revision;
- local GPU execution.

### Qwen2.5-7B-Instruct
- approximately 7B-class parameters;
- Q4_K_M local Ollama execution;
- immutable blob SHA-256 recorded in the final evidence package.

No hosted API result is used as the primary model-generation evidence.

---

# 8. Evaluation Methodology

## 8.1 Evaluation Stages

The project was evaluated progressively:

1. deterministic UIR-core tests;
2. multilingual semantic and canonicalization evaluation;
3. authentic local-SLM execution;
4. strong baseline expansion;
5. external official benchmark reproduction;
6. metric and provenance reconciliation;
7. final constrained-decoding and cross-model closure.

Earlier development artifacts are retained for traceability, while the final empirical claims use the frozen Phase-4F evidence contract.

---

## 8.2 Internal Dataset

The final internal campaign contains:

\[
N=600
\]

frozen cases, balanced:

\[
300\ \mathrm{Korean}
+
300\ \mathrm{English}.
\]

The set includes:
- valid benign requests,
- condition-heavy requests,
- policy violations,
- adversarial prompts,
- numeric/provenance tasks,
- invalid entities.

A commit-eligible utility cohort contains:

\[
N_{\mathrm{commit}}=418.
\]

The adversarial security subset contains:

\[
N_{\mathrm{attack}}=50.
\]

---

## 8.3 Multilingual Frontend Evaluation

Earlier frozen multilingual evaluation produced:
- semantic UIR match: **87.5%**;
- structural match: **87.5%**;
- evaluated cross-lingual equivalence: **100%**.

A separate robustness suite of 1,000 cases included Korean, English, and Korean–English code-mixed inputs. Representative results were:
- intent accuracy: **85.0%**;
- target exact match: **100%**;
- slot F1: **100%**;
- condition AST match: **90.0%**;
- clarification precision/recall: **100% / 100%**.

These results define the scope as controlled multilingual processing, not unrestricted natural-language understanding.

---

## 8.4 Condition Representation Diagnostic

A 300-case condition-heavy diagnostic compared representations ranging from surface text to explicit parenthesized typed DSL.

Observed consistency increased as representation became more explicit:
- surface natural language: approximately **36.7–63.3%**;
- raw AST: **73.3–93.3%**;
- normalized AST: **86.7–96.7%**;
- explicit parenthesized DSL: **93.3–100%**.

This is interpreted as a representation-level consistency diagnostic, not human ground-truth agreement.

---

## 8.5 Baselines

The final internal comparison includes:

| ID | Pipeline |
|---|---|
| C0 | Direct SLM |
| C1 | Naive RAG |
| C2 | RAG + entity existence check |
| C3 | JSON-schema prompted + post-hoc validation |
| C4 | Tool-calling agent |
| C5 | Guardrail-style pipeline |
| C6 | Corrective retrieval |
| C7 | Graph-structured RAG |
| C8 | Final UIR B6 |
| D1 | Token-level grammar-constrained decoding |

C5–C7 are described according to their actual implemented mechanisms and are not claimed to be exact reproductions of every external framework with a similar name.

---

## 8.6 External Benchmarks

### FinQA
A frozen set of 200 official FinQA examples is used to evaluate financial numerical reasoning [REF-FINQA].

Metrics include:
- expression parse rate,
- contract validity,
- safe execution,
- official execution accuracy,
- raw unsupported generation,
- accepted unsupported claims.

### HaluEval-QA
A frozen set of 200 official HaluEval-QA examples is used [REF-HALUEVAL].

Metrics include:
- raw semantic accuracy,
- contract validity,
- accepted end-to-end accuracy,
- raw unsupported generation,
- accepted unsupported claims,
- safe rejection.

---

## 8.7 Primary Metrics

### Safety
\[
\mathrm{AcceptedUnsupportedRate}
=
\frac{\#\ \mathrm{unsupported\ claims\ surviving\ validation}}
{\#\ \mathrm{evaluated\ cases}}.
\]

### Adversarial attack success
\[
\mathrm{ASR}
=
\frac{\#\ \mathrm{successful\ behavioral\ attacks}}
{50}.
\]

### Complete utility
\[
\mathrm{CompleteAccuracy}
=
\frac{\#\ \mathrm{cases\ satisfying\ full\ required\ claim\ set}}
{418}.
\]

### Supported-answer coverage
\[
\mathrm{Coverage}
=
\frac{\#\ \mathrm{cases\ with\ at\ least\ one\ relevant\ verified\ claim}}
{418}.
\]

### Safe partial rate
\[
\mathrm{PartialRate}
=
\frac{\#\ \mathrm{supported\ but\ incomplete\ answers}}
{418}.
\]

Raw generation metrics and accepted-system metrics are always reported separately.

---

# 9. Results

## 9.1 Internal Safety

| Pipeline | Accepted Unsupported (%) ↓ | Adversarial ASR (%) ↓ |
|---|---:|---:|
| C0 Direct SLM | 35.83 | 66 |
| C1 Naive RAG | 49.33 | 92 |
| C2 RAG + Entity Check | 33.17 | 84 |
| C3 JSON-schema Prompt/Post-Hoc | 27.33 | 50 |
| C4 Tool-Calling Agent | 23.83 | 0 |
| C5 Guardrail Pipeline | 0.00 | 0 |
| C6 Corrective RAG | 11.00 | 0 |
| C7 Graph-Structured RAG | 78.00 | 90 |
| **C8 UIR** | **0.00** | **0** |
| D1 Grammar-Constrained | 20.83 | 0 |

For C8, no unsupported claim was accepted in 600 evaluated internal cases:

\[
0/600,
\]

with Wilson 95% interval approximately:

\[
[0.00\%, 0.64\%].
\]

The important comparison is not that UIR is the only configuration that can block attacks—C5 also performed strongly on these internal safety endpoints—but that UIR combines the safety boundary with explicit policy/evidence semantics, partial-answer recovery, and deterministic provenance.

---

## 9.2 Internal Utility

| Pipeline | Complete Accuracy (%) | Supported Coverage (%) | Safe Partial (%) | No Answer (%) |
|---|---:|---:|---:|---:|
| C1 Naive RAG | 53.11 | 53.11 | 0.00 | 46.89 |
| C2 RAG + Entity Check | 53.59 | 53.59 | 0.00 | 46.41 |
| C4 Tool Agent | 26.32 | 26.32 | 0.00 | 73.68 |
| C5 Guardrail | 53.35 | 53.35 | 0.00 | 46.65 |
| C6 Corrective RAG | 53.59 | 53.59 | 0.00 | 46.41 |
| **C8 UIR** | **53.59** | **65.07** | **11.48** | **34.93** |
| D1 Grammar-Constrained | 49.28 | 64.59 | 15.31 | 35.41 |

The primary complete-accuracy comparison between C1 and C8 is:

\[
53.11\%
\quad \mathrm{vs.}\quad
53.59\%.
\]

The exact McNemar test gives:

\[
p=0.50.
\]

Therefore the study **does not establish superior complete-task accuracy for UIR**.

This negative result is central to the paper.

UIR's utility difference appears instead in supported-answer coverage:

\[
53.11\%
\rightarrow
65.07\%,
\]

a gain of:

\[
+11.96\ \mathrm{percentage\ points}.
\]

The gain consists of **11.48% safe partial answers** that preserve verified information instead of collapsing all non-complete cases into either free-form generation or total rejection.

---

## 9.3 Claim Precision and Recall

For C8:

- conditional claim precision: **100%** among emitted accepted claims;
- macro claim recall: **23.78%** over all commit-eligible cases.

This difference is important.

High conditional precision means that emitted claims are verified under the final contract. It does not mean that the system answers every required claim. The relatively low macro recall exposes the cost of fail-closed verification.

---

## 9.4 Grammar-Constrained Decoding

The genuine D1 baseline uses token-level grammar enforcement through `lm-format-enforcer`.

Direct recomputation of its frozen 600 raw outputs gives:

\[
596/600 = 99.33\%
\]

schema validity.

The four invalid outputs are truncation/incomplete-generation cases. Thus token constraints dramatically improve structural validity but do not make the whole generation process infallible under a finite token budget.

| Baseline | Schema Validity | Accepted Unsupported | Complete Accuracy | Coverage |
|---|---:|---:|---:|---:|
| C3 Prompt/Post-Hoc | 16.03% | 27.33% | 0.00% | 0.00% |
| **D1 Grammar-Constrained** | **99.33%** | 20.83% | 49.28% | 64.59% |
| **C8 UIR** | 100% | **0.00%** | **53.59%** | **65.07%** |

This is one of the paper's clearest comparisons.

A grammar can constrain **how a claim is serialized**.

It cannot, by itself, determine:

> whether the claim is authorized and grounded in an authoritative external fact registry.

---

## 9.5 Internal Latency

Representative mean workload latencies are:

| Pipeline | Mean latency |
|---|---:|
| C1 Naive RAG | 14.29 s |
| C5 Guardrail | 6.76 s |
| C6 Corrective RAG | 5.57 s |
| D1 Constrained Decoding | 7.52 s |
| **C8 UIR** | **2.08 s** |

For C8, the deterministic pre-model rejection path is approximately sub-millisecond, whereas full-path inference remains model-bound.

The latency result therefore should not be interpreted as faster transformer computation.

It reflects:

\[
\text{less unnecessary model invocation}
+
\text{early deterministic rejection}.
\]

---

# 10. External Evaluation

## 10.1 FinQA

### Phi-3.5-mini

| Pipeline | Contract Valid | Official Accuracy | Raw Unsupported | Accepted Unsupported |
|---|---:|---:|---:|---:|
| C1 RAG | 100% | 3.5% | 45% | 45% |
| **C8 UIR** | 96% | **1.0%** | 0% | **0%** |

UIR is safer but less accurate than Naive RAG in this setting.

### Qwen2.5-7B

| Pipeline | Contract Valid | Official Accuracy | Raw Unsupported | Accepted Unsupported |
|---|---:|---:|---:|---:|
| C1 RAG | 100% | 0% | 0% | 0% |
| **C8 UIR** | 95.5% | **21.5%** | 4.5% | **0%** |

The 4.5% raw unsupported generation demonstrates why model-level and system-level metrics must be separated. These generations were rejected before acceptance.

FinQA therefore produces mixed evidence:
- UIR does not solve numerical reasoning by itself;
- a stronger/different model can interact more effectively with the typed arithmetic contract;
- strict execution prevents unsupported values from being silently accepted.

---

## 10.2 HaluEval-QA

### Phi-3.5-mini

| Pipeline | Raw Semantic Acc. | Contract Valid | Accepted E2E Acc. | Safe Rejection |
|---|---:|---:|---:|---:|
| C1 RAG | 80% | 100% | 80% | 0% |
| **C8 UIR** | 72% | 36.5% | **6%** | 63.5% |

The model frequently reaches a plausible semantic decision but fails the strict evidence contract.

### Qwen2.5-7B

| Pipeline | Raw Semantic Acc. | Contract Valid | Accepted E2E Acc. | Safe Rejection |
|---|---:|---:|---:|---:|
| C1 RAG | 61.5% | 100% | 61.5% | 0% |
| **C8 UIR** | 50% | **0%** | **0%** | **100%** |

This is a strong negative result.

The Qwen model produces recoverable semantic decisions in some cases, but none satisfies the instantiated strict UIR HaluEval output contract. Consequently, end-to-end accepted accuracy is zero.

The result demonstrates that:

\[
\text{semantic correctness}
\not\Rightarrow
\text{contract-valid executable output}.
\]

It also shows that overly strict or poorly task-aligned contracts can destroy utility even when they improve safety.

---

# 11. Mutation Robustness

A 10-class mutation campaign evaluated failures including:
- invalid identifiers,
- duplicate identifiers,
- stale references,
- cross-case references,
- tampered catalogs,
- wrong entities,
- wrong periods,
- wrong metrics,
- malformed syntax,
- and Unicode confusion.

The UIR path was designed to fail closed on these classes.

The interpretation is architectural:

> typed identifiers and explicit validation make classes of silent corruption observable and rejectable.

The result should not be generalized to all possible attacks.

---

# 12. Discussion

## 12.1 UIR Is a Control Boundary, Not a Better Language Model

The most important result is what UIR **does not** do.

It does not significantly improve complete internal task accuracy over Naive RAG:

\[
53.59\%
\quad \mathrm{vs.}\quad
53.11\%,
\quad p=0.50.
\]

It also performs poorly on some external tasks.

Therefore UIR should not be described as a general reasoning enhancement.

Its contribution is the separation:

\[
\boxed{
\text{Probabilistic Reasoning}
\quad\text{from}\quad
\text{Deterministic Authority}
}
\]

This separation changes the failure mode.

---

## 12.2 From Fabrication to Bounded Failure

Without a deterministic acceptance boundary, a model failure may appear as fluent but unsupported prose.

With UIR, the same uncertainty can become:

```text
FULL VERIFIED ANSWER
PARTIAL VERIFIED ANSWER
NO VERIFIED ANSWER
```

This is a different system property from raw model accuracy.

The internal results illustrate this reallocation:
- complete accuracy remains approximately unchanged;
- supported coverage increases;
- accepted unsupported claims are eliminated in the evaluated C8 set;
- some failures become explicit abstentions.

---

## 12.3 RAG Answers “What Is Relevant”; Policy Answers “What Is Permitted”

A broader architectural implication is the separation of declarative knowledge from policy knowledge.

RAG primarily addresses:

> What information is relevant to this query?

A policy engine addresses:

> Given these facts, what decision or action is permitted under explicit rules, priorities, exceptions, and context?

The current paper does not implement automated policy synthesis, but the UIR provides a machine-verifiable contract through which verified knowledge and explicit policy can be evaluated separately before execution.

---

## 12.4 Why Syntax Is Not Grounding

D1 provides the cleanest demonstration.

Token-level constraints nearly guarantee structural conformance:

\[
99.33\%\ \mathrm{schema\ validity}.
\]

Yet accepted unsupported claims remain:

\[
20.83\%.
\]

Therefore:

\[
\text{Valid JSON}
\not\Rightarrow
\text{Valid Evidence}.
\]

UIR's additional value comes from fact-registry binding, policy evaluation, and accepted-output validation.

---

## 12.5 Explainability as Decision Trace

A policy-constrained system can record:

```text
Input facts
→ matched policies
→ conditions
→ exceptions
→ decision
→ verified evidence
→ accepted claims
```

Natural-language explanation can then be rendered from this actual trace.

This is qualitatively different from asking a language model to invent a plausible explanation after making a decision.

We refer to this direction as **decision-trace explainability**.

---

## 12.6 Condition Semantics Remain Difficult

The multilingual experiments show that complex natural-language conditions remain challenging.

Nested Boolean structure, negation, exception scope, and underspecification are particularly sensitive.

The strong improvement observed when conditions are converted from surface language to normalized typed ASTs supports the UIR design, but it also exposes the frontend compiler as a critical limitation.

A wrong compiler output can deterministically enforce the wrong semantics.

---

# 13. Threats to Validity and Limitations

## 13.1 Controlled-Language Scope

The implemented language scope is Korean and English controlled requests. The results do not establish unrestricted multilingual natural-language understanding.

## 13.2 Frontend Error

A deterministic downstream system cannot recover correctness if the frontend compiles the user's intent incorrectly.

## 13.3 Closed-World Assumptions

The strongest safety propositions require A1–A5. If:
- the fact registry is compromised,
- the policy store is wrong,
- fact binding is incorrect,
- or the output guard is bypassed,

the guarantees no longer apply.

## 13.4 External Contract Fit

HaluEval demonstrates that an overly strict output contract may reject semantically useful answers.

Contract engineering is therefore part of system design, not a free safety improvement.

## 13.5 Model Dependence

Only two local model families are evaluated, and they use different inference stacks and quantization configurations.

The results do not establish monotonic improvement with model size.

## 13.6 FinQA Generalization

FinQA performance remains low in several conditions. UIR should not be claimed as a numerical-reasoning solution.

## 13.7 Guardrail Baseline

The guardrail-style internal baseline performs strongly on safety. This limits claims that UIR is uniquely capable of blocking unsupported output. UIR's differentiated contribution is the combination of explicit semantic compilation, policy authority, verified evidence, partial-answer semantics, and auditable execution.

## 13.8 Grammar-Constrained Baseline

The D1 raw evidence produced 596/600 fully schema-valid generations rather than a literal 100%. The remaining failures were incomplete/truncated outputs. Thus even token-level grammar enforcement remains subject to generation-budget and runtime behavior.

## 13.9 Benchmark and Domain Coverage

The internal domain is structured enterprise/financial querying. FinQA and HaluEval provide external stress tests but do not represent all agent domains.

---

# 14. Reproducibility

The final evidence package records:
- frozen benchmark inputs,
- raw model outputs,
- response hashes,
- model revisions/digests,
- generation parameters,
- per-case scoring,
- aggregate metrics,
- paired statistical tests,
- baseline implementation labels,
- artifact SHA-256 manifests.

The Qwen run records an immutable local model identity including its Ollama tag/blob digest and generation configuration.

The final publication pipeline is intended to follow:

```text
raw capture
→ per-case scorer
→ aggregate CSV
→ statistical CSV
→ generated Markdown/LaTeX table
→ manuscript
```

to prevent hand-edited metric drift.

---

# 15. Research Questions Revisited

## RQ1 — Can multilingual requests share a canonical representation?

**Yes, within the controlled-language scope.**

Frozen evaluations show strong Korean/English semantic normalization and complete evaluated cross-language equivalence on declared parallel cases, while the robustness tests expose remaining frontend limits.

---

## RQ2 — Does UIR provide a deterministic policy/evidence boundary?

**Yes, under explicit trust assumptions.**

The architecture separates model generation from accepted output and supports fail-closed decisions, verified fact binding, and auditable policy evaluation.

---

## RQ3 — Does the safety boundary destroy utility?

**Not entirely, but it changes utility.**

Complete accuracy is statistically comparable to Naive RAG. UIR's advantage appears in supported-answer coverage through safe partial verified answers, while some other requests are explicitly rejected.

---

## RQ4 — Is UIR equivalent to grammar-constrained generation?

**No.**

D1 achieves approximately 99.33% schema validity but still accepts unsupported claims. Structural correctness is not equivalent to evidence authorization.

---

## RQ5 — Does UIR generalize to external benchmarks?

**The safety boundary transfers more reliably than semantic utility.**

FinQA and HaluEval show mixed or negative task-accuracy results, while accepted-output grounding remains more controllable.

---

## RQ6 — Does a stronger model automatically solve the problem?

**No.**

Model and task interaction is non-monotonic. Qwen performs substantially better than Phi under the FinQA UIR condition, but the strict HaluEval contract yields 0% accepted E2E accuracy despite non-zero raw semantic accuracy.

---

# 16. Broader Implications

The results motivate a distinction between:

\[
\text{Model Intelligence}
\]

and:

\[
\text{System Intelligence}.
\]

A system can improve reliability without changing model weights by making:
- knowledge authority explicit,
- policy executable,
- evidence typed,
- decisions reproducible,
- failures observable,
- and accepted outputs verifiable.

This suggests a broader direction for future **policy-augmented AI agents**, where declarative knowledge and normative/decision knowledge are represented separately.

A future system may evolve from:

```text
RAG:
Question → Relevant Knowledge → Generated Answer
```

toward:

```text
Question
→ UIR
→ Verified Knowledge
+ Executable Policy
+ Runtime Context
→ Decision Trace
→ Verified / Partial / Abstained Output
```

Automated policy synthesis, weighted policy structures, code-generation agents, and scientific-domain UIRs are promising extensions but are outside the scope of the present paper.

---

# 17. Conclusion

This paper presented a Universal Intermediate Representation for policy-constrained multilingual small language model agents.

The central design principle is:

\[
\boxed{\text{Prompt} \neq \text{Authority}}
\]

UIR moves semantic intent, policy constraints, evidence requirements, execution permissions, and output admissibility into an explicit machine-verifiable contract.

The final experiments do not show that UIR universally increases model reasoning accuracy. Complete internal answer accuracy is statistically comparable to Naive RAG, and external tasks reveal substantial contract and reasoning failures.

Instead, the results support a different and more defensible contribution.

UIR changes **where authority resides** and **how failure is handled**.

Unsupported or uncertain generations need not become accepted fluent prose. They can become:
- verified answers,
- safe partial answers,
- or explicit fail-closed outcomes.

A genuine grammar-constrained baseline further shows that syntactic validity alone is insufficient: almost all outputs can satisfy the grammar while unsupported factual content remains possible.

The external experiments reinforce the separation:

\[
\text{Model Semantic Correctness}
\neq
\text{Contract Validity}
\neq
\text{Accepted System Correctness}
\neq
\text{System Safety}.
\]

The paper therefore argues not for a universally smarter language model, but for a more verifiable agent architecture in which probabilistic generation operates inside deterministic policy and evidence boundaries.

---

# 18. Planned Figures for the Final LaTeX Manuscript

## Figure 1 — UIR-Centered Architecture

```text
KO/EN Request
→ Controlled Frontend
→ Typed UIR
→ Entity + Policy + Type Validation
→ Verified Executor
→ VerifiedFactSet
→ SLM Renderer
→ Output Guard
→ FULL / PARTIAL / REJECT
```

## Figure 2 — Four Correctness Layers

```text
Raw Model Output
      ↓
Semantic Correctness
      ↓
Contract Validity
      ↓
Accepted-System Correctness
      ↓
System Safety
```

Emphasize that these are not interchangeable metrics.

## Figure 3 — UIR Contract Schema

```text
Metadata
Semantics
Policy Constraints
Execution Contract
Output Contract
```

## Figure 4 — Safety–Utility Reallocation

Compare C1 and C8:

```text
Complete
Safe Partial
No Verified Answer
Accepted Unsupported
```

## Figure 5 — Grammar-Constrained Decoding vs UIR

Show:

```text
Syntax control
vs.
Evidence/policy authority
```

## Figure 6 — External Generalization

Separate:
- semantic accuracy,
- contract validity,
- accepted E2E accuracy,
- accepted unsupported claims.

---

# 19. Planned Final Tables

1. **UIR schema and formal field definitions**
2. **Internal dataset composition**
3. **Baseline definitions**
4. **Internal safety — accepted unsupported claims and adversarial ASR**
5. **Internal utility — complete accuracy, supported coverage, partial/no-answer**
6. **C3 vs D1 vs C8 constrained-generation comparison**
7. **Multilingual semantic and robustness evaluation**
8. **FinQA cross-model results**
9. **HaluEval cross-model results**
10. **Path-separated latency**
11. **Mutation robustness**
12. **Threats/assumptions mapping**

---

# 20. Final Claim Boundary for the LaTeX Version

### Claims supported by the final evidence

- UIR provides an explicit language-independent policy/evidence execution contract.
- Korean and English controlled requests can be canonicalized into shared semantics within the evaluated grammar.
- UIR separates model generation from accepted-system authority.
- No unsupported claim was observed to survive the final C8 acceptance boundary in the evaluated internal and external cases under the instantiated assumptions.
- UIR preserves complete internal accuracy comparable to Naive RAG while increasing supported-answer coverage through safe partial answers.
- Grammar-constrained decoding provides strong syntactic validity but does not by itself guarantee evidence grounding.
- External semantic task performance remains model- and contract-dependent.

### Claims that must not appear

- “UIR eliminates hallucination universally.”
- “UIR always improves LLM reasoning accuracy.”
- “UIR guarantees safety in arbitrary domains.”
- “The model never generates unsupported content.”
- “A larger model always improves UIR performance.”
- “100% schema validity for D1” unless the D1 experiment is rerun or the four truncation cases are otherwise resolved.

---

# 21. Recommended LaTeX Drafting Order

The final section-by-section LaTeX drafting order should be:

```text
1. Section 3 — Problem Formulation and Threat Model
2. Section 4 — UIR Architecture
3. Section 6 — Formal Safety Properties
4. Section 8 — Evaluation Methodology
5. Section 9–10 — Internal and External Results
6. Section 12–13 — Discussion and Threats to Validity
7. Section 2 — Related Work
8. Section 1 — Introduction
9. Abstract
10. Conclusion
11. Final references and journal formatting
```

The technical and empirical sections should be frozen before polishing the Introduction and Abstract.
