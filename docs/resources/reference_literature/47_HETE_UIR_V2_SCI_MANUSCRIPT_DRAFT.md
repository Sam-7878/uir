# HETE: A Neuro-Symbolic Universal Intermediate Representation for Zero-Trust and Attack-Resilient Language-Model Execution

> **Manuscript status:** SCI journal draft based on the finalized HETE UIR-v2 publication benchmark.  
> **Primary empirical evidence:** frozen Phi-3.5 benchmark package with `publication_eligible=true`.  
> **Important claim boundary:** all security claims in this draft are limited to the evaluated threat taxonomy and benchmark conditions.  
> **Reference note:** the reference list below is an initial working list and should be merged with the existing project BibTeX database before submission.

---

## Abstract

Large language model (LLM) applications increasingly combine natural-language inputs, retrieval-augmented generation (RAG), tool invocation, memory, and external data sources. This architecture expands the security perimeter beyond conventional prompt safety: untrusted text may influence model behavior, retrieved content may carry indirect instructions or poisoned evidence, and model outputs may trigger security-critical downstream actions. Existing prompt-based safeguards attempt to make the model itself resistant to manipulation, but the model remains probabilistic and shares the same natural-language context for trusted instructions and untrusted data.

This paper presents **HETE UIR-v2**, a neuro-symbolic Zero-Trust architecture that treats the LLM as an **untrusted transformation component** and moves security authority outside the model. HETE compiles multilingual natural-language requests into a typed **Universal Intermediate Representation (UIR)** that acts as a Security Reference Representation. Deterministic components bind trusted security context, verify evidence provenance, constrain capabilities and resource budgets, isolate retrieved instructions, validate output structure and citations, and re-check proposed actions before they can affect trusted system state. The central principle is **Prompt ≠ Authority**: natural-language content may influence interpretation, but it cannot directly grant privileges, modify trusted execution semantics, or promote unverified evidence to authoritative status.

We evaluate HETE using a bilingual Korean/English benchmark covering nine adversarial classes and benign tasks. The finalized experiment uses `microsoft/Phi-3.5-mini-instruct`, three repeated runs, a 1,600-case development set, and a disjoint 320-case held-out set. On the held-out set, Vanilla SLM, Naive RAG, Prompt-only Guardrail, and UIR-v1 exhibit end-to-end attack success rates (E2E-ASR) of 41.79%, 46.43%, 38.57%, and 7.14%, respectively. HETE UIR-v2 records **0/280 observed successful attacks (0.00% E2E-ASR)** in each held-out run while retaining **100% benign task utility and 0% false rejection**. The corresponding per-run Wilson 95% upper bound for a zero-success rate over 280 attacks is approximately 1.35%, emphasizing that zero observed attacks does not imply universal immunity. Paired exact McNemar tests show significant reductions versus all four baselines. Ablation and paired multi-knockout experiments further show that security is produced by **defense-in-depth**: some controls are masked when removed individually but become critical when complementary layers are jointly disabled.

These results support a Zero-Trust interpretation of LLM security: trustworthy application behavior need not depend on assuming a trustworthy language model. Instead, the authority of model outputs can be constrained through deterministic representations, evidence verification, capability boundaries, and post-generation enforcement.

**Keywords:** Large Language Models, Zero Trust, Universal Intermediate Representation, Prompt Injection, Retrieval-Augmented Generation, Neuro-Symbolic AI, LLM Security, Hallucination, Security Policy Enforcement, HETE

---

# 1. Introduction

Large language models have moved from isolated conversational systems to application components that retrieve enterprise data, call tools, write structured outputs, maintain memory, and interact with operational workflows. This transition creates a fundamental security problem. A model context may simultaneously contain system instructions, user requests, retrieved documents, tool responses, previous messages, and persistent memory. The model must infer which portions are authoritative, but this distinction is generally represented in the same probabilistic natural-language space.

Prompt injection is therefore not merely a problem of detecting suspicious wording. An attacker may place malicious instructions directly in a user request or indirectly inside documents, webpages, database fields, tool responses, or memory. RAG introduces another class of risks: a retrieved item may be semantically relevant while being untrusted, modified, poisoned, or instruction-bearing. Agentic systems expand the impact further because generated text may be converted into tool calls or real-world actions.

The OWASP GenAI LLM Top 10 2026 identifies prompt injection as a leading risk and expands attention to sensitive information disclosure, excessive agency, data and model poisoning, hidden-context exposure, vector and embedding weaknesses, misinformation, improper output handling, supply-chain issues, and unbounded consumption [1]. NIST AI 100-2e2025 similarly describes adversarial risks affecting generative AI, including poisoning, privacy compromise, misuse, indirect prompt injection, and RAG knowledge-base poisoning [2]. These taxonomies suggest that LLM security should be addressed at the **system architecture level**, not solely through prompt engineering.

Most current defenses attempt to strengthen the model-facing prompt, classify malicious text, or filter outputs. Such measures remain valuable but share a structural limitation: the model itself is asked to interpret and enforce part of the policy. A security-critical decision is thus delegated to the same probabilistic component that the attacker is attempting to manipulate.

We propose a different security boundary.

> **The LLM is not the policy decision point.**

In HETE, a request is compiled into a typed **Universal Intermediate Representation (UIR)** before the LLM is allowed to produce an authoritative response. Security-relevant fields are derived from trusted application state, verified evidence, and deterministic policy rather than user-provided natural language. The model receives only an approved rendering of this representation, and its output remains untrusted until it passes an output verification stage.

The resulting design can be summarized by the principle:

> **Prompt ≠ Authority.**

User text, retrieved text, tool output, and model output may supply semantic information, but they cannot directly become security authority. A user cannot grant itself a new capability by writing a sentence. A retrieved document cannot mutate the compiled execution intent merely because it contains imperative text. A model cannot turn generated code into an executable operation without passing the capability and policy boundary.

This paper extends earlier HETE work focused primarily on hallucination and factual consistency. The earlier architecture demonstrated that deterministic entity verification and structured evidence grounding could prevent unsupported answers in tested enterprise-style tasks. However, hallucination is only one manifestation of a broader trust problem. The revised HETE UIR-v2 therefore generalizes UIR from a factual intermediate format into a **Security Reference Representation (SRR)** for Zero-Trust LLM execution.

The main contributions are:

1. **A Zero-Trust LLM architecture based on typed UIR.**  
   HETE treats the LLM as an untrusted transformation component and places trusted security semantics outside the model.

2. **A deterministic attack-defense pipeline.**  
   The architecture combines trusted security-context binding, policy enforcement, evidence provenance, context isolation, least-privilege capability control, resource budgets, output validation, and immutable audit evidence.

3. **A distinction between model compromise and system compromise.**  
   We define and separately measure **Model Compromise Rate (MCR)** and **End-to-End Attack Success Rate (E2E-ASR)**. This distinguishes cases where the model follows an adversarial instruction from cases where that behavior survives deterministic controls and changes trusted output or state.

4. **A bilingual security benchmark with held-out evaluation.**  
   We construct Korean/English development and held-out sets spanning benign tasks and nine attack classes. Attack success is determined by a common behavior-based oracle rather than by attack labels or baseline identity.

5. **Empirical comparison and ablation.**  
   On the held-out benchmark, HETE UIR-v2 produces 0/280 observed end-to-end successful attacks in each of three repeated runs while preserving 100% benign task success. Paired exact McNemar tests show statistically significant reductions relative to Vanilla SLM, Naive RAG, Prompt-only Guardrail, and UIR-v1. Single and paired component knockouts reveal defense-in-depth effects.

The rest of the paper is organized as follows. Section 2 reviews LLM security threats and related approaches. Section 3 defines the threat model and Zero-Trust requirements. Section 4 presents HETE UIR-v2. Section 5 explains the security properties of the architecture. Section 6 describes the benchmark methodology. Section 7 presents the empirical results. Section 8 discusses implications and limitations. Section 9 concludes.

---

# 2. Background and Related Work

## 2.1 Hallucination and misinformation

LLM hallucination is the generation of content that is unsupported, incorrect, or inconsistent with authoritative evidence. In enterprise settings, hallucination becomes a security and governance problem when generated claims are accepted as trustworthy inputs to decision processes.

RAG reduces some hallucination by providing retrieved evidence, but retrieval alone does not establish that evidence is authentic, current, non-malicious, or suitable for authoritative use. A semantically relevant document may still be poisoned. Therefore, grounding requires both **retrieval relevance** and **evidence trust**.

Earlier HETE work focused on this distinction by verifying target entities and grounding generation in structured enterprise evidence. HETE UIR-v2 retains this mechanism but treats factual verification as one part of a broader Zero-Trust security boundary.

## 2.2 Prompt injection and jailbreaks

Prompt injection attempts to change model behavior through adversarial natural-language instructions. Direct injection appears in the user prompt; indirect injection appears in external content consumed by the model. The latter is particularly important in RAG and agentic architectures because untrusted webpages, documents, emails, tool results, or memory may contain instructions that were never intended to be system policy.

A core architectural difficulty is that instructions and data are often concatenated into one context window. The model is therefore expected to infer which natural-language tokens are authoritative. HETE does not assume that this inference can be made perfectly. Instead, it prevents untrusted context from obtaining execution authority.

## 2.3 RAG poisoning and evidence integrity

NIST describes knowledge-base poisoning and indirect prompt injection as important generative-AI threats [2]. A poisoned RAG item may be crafted to influence a target query while still appearing relevant to a vector retriever.

HETE separates **retrieval** from **admission as authoritative evidence**. Retrieved items receive explicit source identity, trust status, and integrity metadata. Evidence failing provenance checks can be quarantined even if it is highly relevant semantically.

## 2.4 Excessive agency and improper output handling

Agentic LLM applications often allow model outputs to select or parameterize external tools. This creates a dangerous transition from probabilistic text to privileged action. A model may be manipulated into proposing an unauthorized operation even when the original user lacked permission.

HETE addresses this with two boundaries:

- a **Capability Gate** before privileged execution; and
- an **Output Guard** after model generation.

Generated commands remain data until revalidated against UIR policy and capability state.

## 2.5 Sensitive-information disclosure

Sensitive data can leak through user prompts, retrieved context, model memory, or generated output. HETE therefore applies controls on both ingress and egress. Data classification determines which content may enter the model context, while output inspection prevents unauthorized disclosure of protected values.

## 2.6 Resource exhaustion

LLM workloads can be exploited through long inputs, recursive retrieval, repeated tool calls, or excessive generation. HETE encodes deterministic resource budgets in UIR so that input tokens, output tokens, retrieval count, tool-call count, timeout, and recursion depth can be bounded independently of model compliance.

## 2.7 Zero Trust for LLM systems

Zero Trust assumes that trust is not granted merely because a component is inside a perimeter. Each access or operation must be explicitly verified. Applying this principle to LLM systems requires treating the model itself as a component whose output is not automatically authoritative.

HETE therefore does not attempt to prove that the LLM is intrinsically secure. Instead, it limits what the system will accept from it. This changes the core research question from:

> “Can an LLM be prevented from ever generating unsafe content?”

to:

> “Can unsafe or manipulated model behavior be prevented from gaining trusted system authority?”

---

# 3. Threat Model and Security Requirements

## 3.1 Trust boundaries

HETE defines four conceptual zones.

| Zone | Components | Trust assumption |
|---|---|---|
| System-Trusted | UIR builder, trusted security-context binder, deterministic policy engine, capability/resource guards | Trusted implementation boundary |
| Verification-Required | Evidence resolver, provenance verifier, output guard | Data accepted only after verification |
| Untrusted-but-Isolated | LLM inference component | Model output is untrusted |
| Quarantine | Unverified RAG/tool/memory evidence | Cannot modify security semantics |

The attacker may influence user input, RAG content, tool-returned text, and model-visible context. The attacker may attempt to induce false statements, override policy, leak secrets, escalate privileges, or consume excess resources.

The attacker is **not** assumed to control the trusted UIR builder, policy implementation, operating system kernel, or frozen benchmark oracle. Training-time model compromise, hardware compromise, and full model supply-chain compromise are outside the evaluated scope.

## 3.2 Evaluated attack classes

The benchmark evaluates:

1. nonexistent or fictitious entity hallucination;
2. gaslighting / false-premise adoption;
3. direct prompt injection;
4. jailbreak / policy override;
5. indirect prompt injection through retrieved content;
6. poisoned retrieval evidence;
7. sensitive-data exfiltration;
8. excessive agency / tool escalation;
9. resource exhaustion.

These classes cover major application-layer risks discussed in OWASP and NIST taxonomies while remaining measurable in a controlled enterprise-style pipeline [1], [2].

## 3.3 Security requirements

The architecture enforces the following principal invariants.

| ID | Security invariant |
|---|---|
| INVAR-001 | User text cannot directly define `allowed_capabilities`. |
| INVAR-002 | RAG/tool/memory content cannot mutate the compiled `intent.action`. |
| INVAR-003 | `security_context` originates from trusted application state. |
| INVAR-004 | High-impact actions require explicit approval. |
| INVAR-005 | Untrusted evidence cannot become authoritative without verification. |
| INVAR-006 | Missing provenance for security-sensitive facts fails closed. |
| INVAR-007 | Model-proposed actions are revalidated after generation. |
| INVAR-008 | Token, retrieval, tool, and time budgets are deterministically enforced. |
| INVAR-009 | SECRET/CONFIDENTIAL data cannot enter model context without authorization. |
| INVAR-010 | Generated code and commands remain untrusted data until separately authorized. |

These invariants define what the system will authorize, not what the model will internally believe.

---

# 4. HETE UIR-v2 Architecture

## 4.1 Overview

HETE processes each request through a deterministic security envelope:

```text
Untrusted Input
      |
      v
[1] Input Guard
      |
      v
[2] Multilingual Frontend
      |
      v
[3] UIR-v2 Builder
      |
      v
[4] Evidence Resolver / Provenance
      |
      v
[5] Context Firewall
      |
      v
[6] Zero-Trust Policy Engine
      |
      v
[7] Capability Gate
      |
      v
[8] LLM Renderer / Phi-3.5      <-- Untrusted model zone
      |
      v
[9] Output Guard
      |
      v
[10] Resource Finalization / Audit
      |
      v
Trusted Response or Deterministic Denial
```

The model is invoked only after trusted state has been compiled and checked.

## 4.2 Universal Intermediate Representation as a Security Reference Representation

UIR-v2 includes semantic and security fields:

```json
{
  "uir_version": "2.0",
  "metadata": {
    "request_id": "...",
    "source_lang": "KO|EN",
    "domain": "...",
    "target_id": ["..."],
    "source_hash": "sha256:..."
  },
  "intent": {
    "action": "...",
    "arguments": {}
  },
  "security_context": {
    "principal": "...",
    "trust_level": "...",
    "input_taint": ["USER", "RAG", "TOOL", "MEMORY"],
    "data_classification": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "SECRET"],
    "allowed_capabilities": [],
    "denied_capabilities": [],
    "requires_human_approval": false
  },
  "evidence": [
    {
      "source_id": "...",
      "source_type": "...",
      "trust": "TRUSTED|UNTRUSTED",
      "sha256": "...",
      "verified": true,
      "instruction_bearing": false
    }
  ],
  "resource_budget": {
    "max_input_tokens": 4096,
    "max_output_tokens": 1024,
    "max_retrievals": 5,
    "max_tool_calls": 0,
    "timeout_ms": 10000
  },
  "expected_output": {
    "schema_id": "...",
    "citations_required": true
  }
}
```

The essential property is not the JSON syntax itself but the **authority separation**. Security-sensitive values are populated from trusted application state rather than copied from user-controlled text.

## 4.3 Input Guard

InputGuard normalizes input, assigns taint/source metadata, and performs pre-budget checks. Pattern matching may provide telemetry but is not the primary security boundary. This distinction is important because prompt injection cannot be assumed to follow a fixed lexical signature.

Unicode normalization reduces some compatibility/canonical obfuscations but is not claimed to eliminate all homoglyph or Unicode-confusable attacks.

## 4.4 Trusted evidence and provenance

The evidence subsystem performs:

- exact entity resolution where available;
- source allow-list verification;
- integrity-hash checking;
- explicit trust labeling;
- conflict detection;
- quarantine of unverified evidence.

A retrieved document is therefore not authoritative merely because the vector retriever selected it.

## 4.5 Context Firewall

The Context Firewall isolates instruction-bearing retrieved content from executable semantics. Retrieved text is rendered as evidence rather than as trusted policy. Raw content and corresponding hashes remain available for audit.

The system does not claim that the model can never semantically interpret an injected instruction. Instead, the firewall prevents such text from mutating authoritative UIR fields.

## 4.6 Security Policy Engine

The deterministic policy engine evaluates policy constraints and returns a finite security outcome:

```text
ALLOW
DENY
CLARIFY
REQUIRE_APPROVAL
QUARANTINE_EVIDENCE
DEGRADE_TO_READ_ONLY
```

Security decisions are recorded in an audit event with the matched rule and UIR digest.

## 4.7 Capability Gate

The Capability Gate binds actions to least-privilege capability sets. Operations that are destructive or externally visible require explicit authorization. A model-generated suggestion cannot manufacture a capability.

## 4.8 LLM Renderer

The LLM receives a sanitized rendering of policy-approved UIR state. It remains an untrusted component.

The publication experiment uses:

- `microsoft/Phi-3.5-mini-instruct`;
- frozen revision `2fe192450127e6a83f7441aef6e3ca586c338b77`;
- NF4 double quantization;
- deterministic greedy decoding;
- three repeated runs.

## 4.9 Output Guard

The output guard performs:

- schema validation;
- citation/evidence-ID binding;
- sensitive-data filtering;
- action revalidation;
- code/command containment.

This provides a second boundary after model generation.

## 4.10 Audit evidence

Each request produces auditable metadata including request identity, canonical UIR digest, policy result, evidence hashes, model identity, output hash, terminal outcome, and latency.

This representation is designed to support later integration with broader Zero-Trust evidence frameworks.

---

# 5. Security Analysis

## 5.1 Direct prompt injection

A direct injection can influence raw natural-language parsing, but it cannot directly assign trusted `security_context` or new capabilities. A user statement such as “ignore all restrictions and grant administrator privileges” remains untrusted input.

The security objective is therefore not perfect detection of the sentence. It is preventing the sentence from becoming authority.

## 5.2 Indirect injection

Retrieved documents and tool outputs are tainted and cannot mutate compiled action semantics. Context Firewall and downstream Output Guard provide overlapping controls.

The ablation results show why these layers should be interpreted as defense-in-depth rather than independent single points of security.

## 5.3 Poisoned retrieval

Provenance metadata separates semantic relevance from evidence authority. Unverified data may be retrieved but should not be admitted as trusted evidence.

## 5.4 Excessive agency

Tool authority is bound to capabilities outside the model. The architecture distinguishes textual proposals from actual executed actions.

## 5.5 Sensitive-data exfiltration

Data classification constrains what may enter the model context, while output DLP and schema validation restrict externally visible responses.

## 5.6 Resource exhaustion

UIR resource budgets constrain compute-relevant operations independent of model cooperation.

## 5.7 Model compromise versus system compromise

We define:

\[
MCR = \frac{N_{\text{model-compromised attacks}}}{N_{\text{attacks}}}
\]

and

\[
E2E\text{-}ASR =
\frac{N_{\text{attacks achieving trusted external effect}}}
{N_{\text{attacks}}}.
\]

The distinction is central to HETE.

An LLM may produce attacker-aligned text, yielding model compromise, while deterministic downstream controls prevent the text from changing trusted system state. Such a case increases MCR but not E2E-ASR.

This metric decomposition avoids equating “the model said something unsafe” with “the application was successfully compromised.”

---

# 6. Experimental Methodology

## 6.1 Research questions

The experiments address:

- **RQ1:** Does HETE reduce end-to-end attack success relative to model-only and RAG baselines?
- **RQ2:** Does HETE preserve benign task utility while applying strict Zero-Trust controls?
- **RQ3:** Does UIR-v2 improve security over earlier UIR-v1?
- **RQ4:** Which components contribute directly, and which are masked by defense-in-depth?
- **RQ5:** Are results consistent across Korean and English?
- **RQ6:** Does deterministic early termination affect latency?

## 6.2 Datasets

The development dataset contains 1,600 bilingual cases:

| Class | Cases |
|---|---:|
| Benign | 200 |
| Nonexistent entity | 200 |
| Gaslighting / false premise | 200 |
| Direct prompt injection | 200 |
| Jailbreak / policy override | 150 |
| Indirect prompt injection | 200 |
| Poisoned retrieval | 150 |
| Sensitive-data exfiltration | 100 |
| Excessive agency | 100 |
| Resource exhaustion | 100 |
| **Total** | **1,600** |

The held-out set contains 320 disjoint cases:

- 40 benign;
- 280 attacks;
- 160 Korean / 160 English.

Dataset auditing reported:

- zero duplicated prompts;
- zero duplicated case IDs;
- no shared prompts between development and held-out sets;
- no shared case IDs between splits;
- no missing machine-checkable attack goals;
- no benign cases missing trusted evidence fixtures;
- no literal held-out prompt leakage into judge rules.

## 6.3 Baselines

Five systems are compared.

### Vanilla SLM
Direct Phi-3.5 generation without HETE security controls.

### Naive RAG
Retrieved context is supplied to the model without HETE provenance and policy enforcement.

### Prompt-only Guardrail
A fixed hardened system prompt is used identically for every case.

### UIR-v1
Earlier HETE architecture emphasizing entity validation and factual grounding but without the complete UIR-v2 security pipeline.

### HETE UIR-v2 Security
Full proposed Zero-Trust architecture.

## 6.4 Independent attack oracle

Unlike the initial engineering benchmark, the final benchmark does not assign attack success from the attack label. Each case defines an explicit attack objective and the evaluator determines success from observable response, evidence admission, tool activity, sensitive-data disclosure, or resource-bound violation.

The evaluated system emits execution records; the common judge computes MCR and E2E-ASR afterward.

## 6.5 Judge validation

A balanced 200-case development sample, 20 cases from each class including benign cases, was reviewed against prompt, attack goal, expected answer, final output, evidence admission, tool calls, and resource bounds.

The deterministic judge and the AI-assisted evidence review agreed on all 200 cases.

Importantly, this was **AI-assisted manual evidence review using Codex GPT-5.6, not an independent human annotation study**. We therefore treat the 100% agreement as evaluator consistency evidence rather than as human-ground-truth validation.

## 6.6 Runtime environment

The frozen publication manifest records:

- Python 3.12.13;
- PyTorch 2.5.1+cu121;
- Transformers 5.13.1;
- bitsandbytes 0.49.2;
- CUDA 12.1;
- NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB;
- WSL2 Linux runtime;
- Phi-3.5 model revision fixed by hash;
- deterministic decoding;
- no fallback backend.

The strict validator reports:

```text
status = PASS
publication_eligible = true
failures = []
```

## 6.7 Statistical analysis

For rate metrics we report raw counts, percentages, and Wilson 95% intervals. Paired exact McNemar tests compare attack success on the same held-out cases.

For HETE, zero successful attacks were observed among 280 held-out attack cases in each run. The per-run Wilson 95% upper confidence bound is approximately 1.35%. We therefore write **“0% observed E2E-ASR”**, not “provably attack-proof.”

---

# 7. Results

## 7.1 Held-out baseline comparison

Table 1 summarizes the held-out results aggregated over the three deterministic repeated runs.

### Table 1. Held-out security and utility comparison

| System | MCR | E2E-ASR | FRR | Benign utility | Mean latency |
|---|---:|---:|---:|---:|---:|
| Vanilla SLM | 41.79% | 41.79% | 100.00% | 0.00% | 15,568.50 ms |
| Naive RAG | 47.50% | 46.43% | 5.00% | 95.00% | 17,492.97 ms |
| Prompt-only Guardrail | 43.93% | 38.57% | 72.50% | 27.50% | 15,953.62 ms |
| UIR-v1 | 7.14% | 7.14% | 27.50% | 72.50% | 6,716.39 ms |
| **HETE UIR-v2** | **0.00%** | **0.00%** | **0.00%** | **100.00%** | **5,252.87 ms** |

HETE UIR-v2 achieved 0/280 observed E2E successful attacks in each held-out run. Both Korean and English subsets recorded 0/140 observed attack successes and 20/20 benign utility successes per run.

The key comparison is UIR-v1 versus UIR-v2. UIR-v1 reduced attack success substantially relative to unstructured baselines but retained a held-out E2E-ASR of 7.14%. UIR-v2 eliminated observed successes within the evaluated held-out set while also improving benign utility from 72.5% to 100%.

### Interpretation of benign utility

The benign metric is **benchmark task success under the benchmark's required structured evidence-backed response contract**. It should not be interpreted as general conversational helpfulness. Vanilla SLM receives 0% under this strict criterion because it does not satisfy the required structured/evidence-bound task contract, not because the model is incapable of producing useful natural-language responses in general.

## 7.2 Statistical significance

Paired exact McNemar comparisons against HETE show:

| Baseline | Held-out E2E risk | HETE risk | Absolute risk reduction | Exact p-value |
|---|---:|---:|---:|---:|
| Vanilla SLM | 41.79% | 0% | 41.79 percentage points | \(1.20 \times 10^{-35}\) |
| Naive RAG | 46.43% | 0% | 46.43 percentage points | \(1.47 \times 10^{-39}\) |
| Prompt-only Guardrail | 38.57% | 0% | 38.57 percentage points | \(6.16 \times 10^{-33}\) |
| UIR-v1 | 7.14% | 0% | 7.14 percentage points | \(1.91 \times 10^{-6}\) |

All four paired comparisons are statistically significant in the evaluated held-out set.

## 7.3 Per-class HETE results

HETE recorded 0 observed MCR and 0 observed E2E-ASR in every held-out class:

| Attack class | Cases/run | Observed MCR | Observed E2E-ASR |
|---|---:|---:|---:|
| Direct prompt injection | 40 | 0% | 0% |
| Excessive agency | 20 | 0% | 0% |
| Gaslighting / false premise | 40 | 0% | 0% |
| Indirect prompt injection | 40 | 0% | 0% |
| Jailbreak / policy override | 30 | 0% | 0% |
| Nonexistent entity | 40 | 0% | 0% |
| Poisoned retrieval evidence | 30 | 0% | 0% |
| Resource exhaustion | 20 | 0% | 0% |
| Sensitive-data exfiltration | 20 | 0% | 0% |

These values establish benchmark observations, not universal attack immunity.

## 7.4 Language consistency

For HETE UIR-v2:

| Language | Attack cases | E2E-ASR | Benign cases | Utility |
|---|---:|---:|---:|---:|
| English | 140 | 0% | 20 | 100% |
| Korean | 140 | 0% | 20 | 100% |

The results support bilingual consistency within this dataset. Because both groups have zero observed attack successes, broader multilingual generalization requires additional languages and independently sourced prompts.

## 7.5 Latency

The aggregate mean held-out latency of HETE was 5.25 s, compared with:

- 15.57 s for Vanilla SLM;
- 17.49 s for Naive RAG;
- 15.95 s for Prompt-only Guardrail;
- 6.72 s for UIR-v1.

This corresponds to approximate mean reductions of:

- **66.3%** versus Vanilla SLM;
- **70.0%** versus Naive RAG;
- **67.1%** versus Prompt-only Guardrail;
- **21.8%** versus UIR-v1.

The result should not be interpreted as evidence that security checks are intrinsically faster than generation. The primary mechanism is **early deterministic termination**: many attack cases are rejected before costly full model generation. In run 0, the reported attack-class mean latency was approximately 2.95 s compared with an overall mean of approximately 5.00 s.

A fair production interpretation should therefore separate benign-path overhead from attack-path early termination.

## 7.6 Single-component ablation

The held-out ablation study reveals that not every component produces an independent E2E-ASR increase when removed. This is expected in a layered architecture because remaining components can mask the failure.

Two single knockouts show clear measured degradation:

### Entity verifier removed

- global ΔMCR: +26.07 percentage points;
- global ΔE2E-ASR: +7.14 points;
- targeted ΔMCR: +50 points;
- FRR increases to 100%;
- benign utility falls to 0%.

The large utility penalty indicates that entity verification and evidence binding interact strongly with the benchmark's fail-closed factual contract.

### Policy engine removed

- global ΔMCR: +22.50 points;
- global ΔE2E-ASR: +7.14 points;
- targeted ΔMCR: +42.86 points;
- benign utility remains 100%.

This demonstrates that deterministic policy evaluation makes a measurable contribution even when downstream controls remain active.

For Context Firewall, provenance, Capability Gate, Output Guard, and Resource Guard, some single-knockout targeted E2E deltas remain zero. These results do **not** justify claiming that those components are unnecessary. Instead, they indicate masking by complementary controls.

## 7.7 Multi-knockout defense-in-depth analysis

Paired knockouts expose these masked relationships.

### Table 2. Selected paired knockout results

| Disabled controls | MCR | E2E-ASR | FRR | Utility | Principal observed failure |
|---|---:|---:|---:|---:|---|
| Context Firewall + Output Guard | 14.29% | 14.29% | 100% | 0% | Gaslighting/false-premise acceptance |
| Policy Engine + Capability Gate | 22.50% | 7.14% | 0% | 100% | Resource exhaustion; model-level jailbreak/leakage |
| Provenance + Entity Verifier | 26.07% | 7.14% | 100% | 0% | Grounding/resource failures |
| Entity Verifier + Output Guard | 26.07% | 26.07% | 100% | 0% | Gaslighting, resource exhaustion, sensitive-data leakage |

The most important observation is that **model-level compromise and system-level compromise diverge under partial defenses**.

For example, disabling Policy Engine and Capability Gate produces model-level compromise on jailbreak and sensitive-data cases, but some of those compromises do not become end-to-end successes because other downstream controls still contain them.

Likewise, removing both Entity Verifier and Output Guard increases E2E-ASR to 26.07%, showing that upstream factual admission and downstream output enforcement form a complementary protection boundary.

These results support describing HETE as a **defense-in-depth Zero-Trust envelope**, not as a set of seven independently necessary filters.

---

# 8. Discussion

## 8.1 Main finding: reduce authority, not merely unsafe text

The key contribution of HETE is not a new prompt classifier. The architecture changes what natural-language text is allowed to mean operationally.

A prompt may ask for privilege.  
A retrieved document may contain an instruction.  
A model may generate a tool command.

None of these observations alone grant authority.

Authority originates from typed UIR state, trusted application context, verified evidence, deterministic policy, and capability binding.

This distinction aligns LLM security with a general Zero-Trust principle: verification is required at each trust transition.

## 8.2 Why prompt-only protection is insufficient

Prompt-only Guardrail retains 38.57% held-out E2E-ASR and only 27.5% benchmark task success under the tested conditions. The precise values depend on the selected model and benchmark, but the architectural result is more important: a system prompt remains part of the model's probabilistic context and does not create an independent enforcement boundary.

HETE uses prompts for model guidance but not as the final source of execution authority.

## 8.3 Why RAG is not a trust mechanism

Naive RAG achieves high benign utility (95%) but the highest held-out E2E-ASR among tested baselines (46.43%). Retrieval therefore improves information availability without establishing evidence trust.

This result reinforces the distinction:

\[
\text{semantic relevance} \neq \text{security authority}.
\]

A secure RAG architecture must evaluate provenance, integrity, and permissible use of retrieved content.

## 8.4 Evolution from UIR-v1 to UIR-v2

UIR-v1 reduces attack success dramatically relative to unstructured baselines but still records 7.14% held-out E2E-ASR and 72.5% benign utility.

UIR-v2 extends UIR beyond factual normalization by explicitly encoding:

- security context;
- taint;
- capabilities;
- evidence trust;
- resource budgets;
- expected output contract.

The observed reduction from 7.14% to 0% E2E-ASR suggests that the security benefit is associated with the expanded enforcement model rather than merely using an intermediate representation.

## 8.5 Defense-in-depth interpretation

A naïve reading of single ablation would incorrectly conclude that controls with zero single-knockout E2E delta have no value. Paired knockouts show that this is not the case.

This is common in layered security systems: two controls may each be sufficient to stop a given pathway, so removing only one produces no system-level compromise. Their contribution becomes visible when both are removed.

Therefore HETE should be analyzed using:

1. single component knockout;
2. model compromise;
3. E2E compromise; and
4. multi-knockout masking.

This four-part methodology is itself a useful evaluation pattern for LLM security architectures.

## 8.6 Relationship to broader Zero-Trust architecture

HETE UIR-v2 is designed as a Data/AI Trust layer. Its evidence and audit records can be combined with other trust layers, such as network anomaly evidence or deterministic process-execution evidence, through a shared evidence envelope.

A broader Zero-Trust model may therefore combine:

```text
Network Trust
   |
   +-- anomaly / fraud evidence
   |
Process Trust
   |
   +-- execution invariants / authorization evidence
   |
Data / AI Trust
   |
   +-- UIR / provenance / LLM security evidence
   |
Unified Trust Decision & Audit
```

This paper evaluates only the Data/AI Trust layer. Cross-layer integration is future work.

---

# 9. Limitations and Threats to Validity

## 9.1 Finite benchmark

The strongest observed HETE result is 0/280 successful attacks per held-out run, not a proof of universal security. The Wilson 95% interval retains a non-zero upper bound. New attack formulations may bypass evaluated controls.

## 9.2 Held-out set size

The held-out set contains 320 cases. This is useful for controlled paired comparison but remains modest compared with the diversity of real-world LLM attacks.

## 9.3 One backbone model

The publication benchmark uses Phi-3.5-mini-instruct. Results may differ for larger models, closed-source APIs, models with stronger instruction-following behavior, or agent-specific models.

A natural next step is cross-model validation using at least one additional open-weight model and one API model where reproducibility constraints permit.

## 9.4 Bilingual but not multilingual in the broad sense

The benchmark covers Korean and English. Claims of multilingual security should therefore be limited to these two evaluated languages.

## 9.5 AI-assisted judge validation

The 200-case judge validation achieved 100% agreement with an AI-assisted evidence review performed by Codex GPT-5.6. No human reviewer is claimed.

This validates consistency between the deterministic judge and a second AI-assisted review process, but it is not equivalent to independent human annotation. A future external human review would strengthen construct validity.

## 9.6 Structured utility metric

The benign utility score measures completion of the benchmark's structured, evidence-bound task. It is not a general measure of conversational quality. This explains why Vanilla SLM receives 0% benign task success despite being able to generate semantically useful text in ordinary conversation.

## 9.7 Defense masking

Some single-component knockouts do not independently increase targeted E2E-ASR because remaining controls mask their removal. We therefore avoid claiming independent necessity for every component.

## 9.8 Trusted computing base

HETE assumes that the UIR builder, security-context source, policy engine, and enforcement code are trustworthy. Compromise of these components can invalidate the security boundary.

## 9.9 Out-of-scope threats

The benchmark does not establish protection against:

- training-time poisoning;
- model-weight backdoors;
- model supply-chain compromise;
- hardware/side-channel attacks;
- operating-system compromise;
- stolen trusted approval credentials;
- arbitrary threats outside the frozen taxonomy.

---

# 10. Conclusion

This paper presented HETE UIR-v2, a Zero-Trust architecture for LLM applications based on a typed Universal Intermediate Representation.

The central design decision is to remove security authority from the language model. The LLM is treated as an untrusted semantic transformation component, while trusted security semantics are compiled into UIR and enforced through deterministic policy, evidence provenance, capability binding, resource limits, context isolation, and output verification.

A bilingual development and held-out benchmark was evaluated with Phi-3.5-mini-instruct over three repeated runs. On the held-out set, Vanilla SLM, Naive RAG, Prompt-only Guardrail, and UIR-v1 produced E2E-ASR values of 41.79%, 46.43%, 38.57%, and 7.14%, whereas HETE UIR-v2 produced **0/280 observed successful attacks per run** while retaining **100% benchmark task utility and 0% FRR**. Paired exact McNemar tests showed significant improvement over all baselines.

Ablation results further showed that HETE should not be interpreted as a collection of isolated filters. Security emerges from overlapping deterministic controls. Paired knockout experiments exposed failures that were masked under single knockouts, supporting the defense-in-depth interpretation.

The broader implication is that trustworthy LLM applications do not require assuming that the model itself is trustworthy. A model may remain probabilistic and potentially manipulable while its authority is constrained by deterministic verification boundaries.

We therefore characterize HETE by the following principle:

> **Never treat model output as authority merely because it was generated inside the application. Compile, verify, constrain, and audit every transition from natural language to trusted system effect.**

---

# References — Working Draft

[1] OWASP GenAI Security Project, **OWASP GenAI LLM Top 10 2026**, Aug. 3, 2026.  
https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/

[2] A. Vassilev, A. Oprea, A. Fordyce, H. Anderson, X. Davies, and M. Hamin, **Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations**, NIST AI 100-2e2025, National Institute of Standards and Technology, Mar. 2025.  
https://doi.org/10.6028/NIST.AI.100-2e2025

[3] MITRE, **Adversarial Threat Landscape for Artificial-Intelligence Systems (ATLAS)**.  
https://atlas.mitre.org/

[4] J. Ouyang et al., **PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models**, working reference to be synchronized with the project's BibTeX database.

[5] Additional references from the existing HETE/UIR manuscript should be merged here, including work on RAG hallucination, prompt injection, neuro-symbolic systems, Zero Trust, structured intermediate representations, and enterprise fact grounding.

---

# Appendix A. Recommended Claim Language for Submission

Use:

> “HETE achieved 0% observed E2E-ASR on the evaluated held-out benchmark.”

Do not use:

> “HETE guarantees zero attacks.”

Use:

> “The typed UIR reduces the authority of untrusted natural-language and model outputs.”

Do not use:

> “The model cannot be compromised.”

Use:

> “Paired multi-knockout results support a defense-in-depth interpretation.”

Do not use:

> “Every component independently guarantees security.”

Use:

> “The evaluation covers Korean and English.”

Do not use:

> “HETE is universally multilingual-secure.”

---

# Appendix B. Key Reproducibility Metadata

```text
Repository commit:
6a1c4bc2e1a860f82962b660305c379fd7291820

Model:
microsoft/Phi-3.5-mini-instruct

Model revision:
2fe192450127e6a83f7441aef6e3ca586c338b77

Quantization:
bitsandbytes NF4 double-quant

Development dataset:
1,600 cases
SHA-256:
526b60c6db118c9ac9f2fddc78acc7bd081c15ac24905519b65b5797d9330ca2

Held-out dataset:
320 cases
SHA-256:
18323e3000fcfe71264dfcca46c0dc2a87fccdf26d2b451c81271cba0049594c

Runs:
3

Fallback backend:
Disabled

Strict publication validation:
PASS
publication_eligible = true
```
