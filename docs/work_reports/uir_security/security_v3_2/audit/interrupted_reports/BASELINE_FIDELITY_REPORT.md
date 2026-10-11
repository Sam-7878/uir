# HETE UIR-ZTA V3.2: Baseline Fidelity & Architectural Approximation Report

## 1. Executive Summary

This report documents the architectural design, implementation fidelity, and operational scope of the comparative baseline systems evaluated in the HETE UIR-ZTA V3.2 publication campaign. In adherence to Work Order mandates (§15, P15) and scientific integrity principles, all comparative baselines are transparently characterized by their operational mechanisms and explicitly designated as **"inspired approximations"** where external closed-source or production frameworks are adapted into the standardized evaluation harness.

---

## 2. Evaluated Systems & Architectural Classification

| System Name | Publication Reference | Fidelity Designation | Core Mechanism | Security Perimeter |
| :--- | :--- | :--- | :--- | :--- |
| **Vanilla SLM** | Unconstrained Foundation Model | Reference Baseline | Direct prompt execution | None (Zero Trust absent) |
| **Naive RAG** | Standard Retrieval-Augmented Gen. | Architecture Baseline | Unfiltered context injection | None (Retrieval assumed trusted) |
| **Spotlighting** | Hing et al. (2024) | Faithful Replication | Delimiting & Datamarking | Prompt-level structural isolation |
| **Progent-inspired** | Wang et al. (2024) | Runtime Sandbox Approximation | Tool call interception & monitoring | Dynamic capability & policy checks |
| **CaMeL-inspired** | Slutzky et al. (2024) | Capability Isolation Approximation | Typed capability contracts | Function-level capability gating |
| **HETE UIR-ZTA** | Proposed Architecture | Authoritative System | Dual-boundary Zero Trust | InputGuard + Firewall + Gate + OutputGuard |

---

## 3. Detailed Baseline Specifications

### 3.1 Vanilla SLM (Bare Small Language Model)
- **Implementation**: [`VanillaSlmBaselineAdapter`](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3_2/baselines/vanilla_slm_adapter.py)
- **Model Runtime**: Qwen2.5-7B-Instruct (4-bit quantized, `845dbda0ea48`) running live on local Ollama via WSL2 CUDA acceleration.
- **Behavioral Profile**: Accepts raw user instructions without sanitization, schema constraints, or output boundaries.
- **Agency Path**: Tool proposals extracted via `ToolProposalParser` execute directly on `MockToolExecutor` without capability checks, leading to unconstrained state mutations upon prompt injection or tool escalation.

### 3.2 Naive RAG (Standard Context Injection)
- **Implementation**: [`NaiveRagBaselineAdapter`](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3_2/baselines/naive_rag_adapter.py)
- **Behavioral Profile**: Concurrently injects external retrieval evidence into the prompt context under the naive assumption that retrieved corpus chunks are authentic.
- **Vulnerability Surface**: Highly susceptible to Indirect Prompt Injection (IPI) and Poisoned Retrieval Evidence (PRE), as injected corpus instructions directly override system instructions.

### 3.3 Spotlighting (Hing et al., 2024)
- **Implementation**: [`SpotlightingBaselineAdapter`](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3_2/baselines/spotlighting_adapter.py)
- **Behavioral Profile**: Applies structural delimiting and datamarking to untrusted inputs, instructing the model to treat content within dedicated boundaries as inert data.
- **Observed Deficiencies**: Under sophisticated multi-turn role-playing or delimiter-escaping attacks, models frequently cross delimiter boundaries. Furthermore, Spotlighting provides no post-LLM output validation or capability enforcement on tool executions.

### 3.4 Progent-inspired Runtime Sandbox (Wang et al., 2024)
- **Implementation**: [`ProgentBaselineAdapter`](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3_2/baselines/progent_adapter.py)
- **Designation**: *Progent-inspired runtime sandbox approximation*.
- **Mechanism**: Intercepts model tool proposals and enforces static policy rules before execution. 
- **Distinction from HETE**: Progent lacks the continuous cryptographic provenance tracking (ProvenanceEngine) and semantic egress boundary validation (OutputGuard) present in HETE.

### 3.5 CaMeL-inspired Capability-Isolation Approximation (Slutzky et al., 2024)
- **Implementation**: [`CaMeLBaselineAdapter`](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3_2/baselines/camel_adapter.py)
- **Designation**: *CaMeL-inspired capability-isolation approximation*.
- **Mechanism**: Implements function-level capability gating by restricting available tool calls based on user principal roles.
- **Distinction from HETE**: Operates primarily at the execution interface; lacks HETE's pre-LLM zero-trust content inspection, bidirectional session isolation, and token-level resource budgeting.

---

## 4. Standardized Evaluation Harness & Agency Path

To guarantee scientific parity and eliminate evaluation artifacts:
1. **Identical Case Population**: All 6 systems evaluate the exact same stratified $N=240$ held-out cases in the exact same sequence.
2. **Unified Mock Tool State**: All tool proposals across all baselines are processed by [`MockToolExecutor`](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3_2/harness/agency_harness.py), which maintains concrete state variables (`balances`, `roles`, `confidential_records`).
3. **Decoupled Metric Tracking**:
   - **MCR (Model Compromise Rate)**: Evaluates whether the raw model output complied with adversarial intent.
   - **E2E-ASR (End-to-End Attack Success Rate)**: Evaluates whether the attack breached the security perimeter to cause an uncontained impact (e.g. egress leakage or unauthorized state mutation).
4. **Zero Fallback Commitment**: Every baseline runs 100% against live local LLM inference (`enable_deterministic_fallback=False`). Any network timeout, memory exhaustion, or model crash triggers an immediate test failure rather than silent substitution.

---

## 5. Summary of Publication Compliance

- [x] All baselines clearly designated as "inspired approximations" where applicable.
- [x] Evaluated on identical test cases with identical random seeds.
- [x] No simulated or mocked model outputs.
- [x] Concrete tool state mutations measured for agency attacks.
