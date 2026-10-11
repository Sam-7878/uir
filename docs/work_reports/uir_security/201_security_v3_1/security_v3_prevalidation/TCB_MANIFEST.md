# HETE UIR-ZTA Trusted Computing Base (TCB) Manifest

**Version:** 3.0.0  
**Specification Level:** SCIE Systems & Security Protocol  
**Repository Reference:** `Sam-7878/uir` / `llm_trust`

---

## 1. Executive Definition of the TCB

The Trusted Computing Base (TCB) of HETE consists exclusively of the deterministic, auditable software components, policy engines, cryptographic validators, and memory boundaries whose correct operation is required to enforce the security policy.

> [!CRITICAL]
> **The Large Language Model (LLM) is EXPLICITLY EXCLUDED from the TCB.**  
> The model is treated as an untrusted, probabilistic natural-language transformation component. It never holds security authority, cannot allocate or alter execution capabilities, and cannot directly commit side effects or state mutations to the operating system or enterprise databases.

---

## 2. Component TCB Audit Matrix

| Component | In TCB? | Neural? | Primary Input | Primary Output | Writes Authority? | Failure Mode |
|---|:---:|:---:|---|---|:---:|---|
| **InputGuard** | **Yes** | No | Raw user text | Sanitized Unicode text, taint tags | No | Fail-closed on buffer bounds |
| **LanguageRouter** | **Yes** | No | Raw text | Script routing decision | No (routes to parser) | Fallback to English parser |
| **EnglishFrontend** | **Yes** | No | English text | Syntactic draft (intent, entities) | **No** (untrusted intent only) | Fail-closed / UNKNOWN intent |
| **KoreanFrontend** | **Yes** | No | Korean text | Syntactic draft (intent, entities) | **No** (untrusted intent only) | Fail-closed / UNKNOWN intent |
| **UIR Builder** | **Yes** | No | Parsed draft + immutable session state | Typed UIR Document | **Yes** (binds trusted context) | Strict schema validation failure |
| **TrustedResolver** | **Yes** | No | Entity identifiers | Cryptographic evidence records | **Yes** (evidence authority) | Quarantine / Rejection |
| **ProvenanceVerifier** | **Yes** | No | Source URIs, hashes, signers | Typed Evidence Records with Tiers | **Yes** (admission tiering) | Reject / Quarantine unverified |
| **ContextFirewall** | **Yes** | No | Retrieved evidence content | Sanitized text / Quarantine flag | **No** (isolates instructions) | Quarantine on active payloads |
| **PolicyEngine (PDP/PEP)** | **Yes** | No | UIR Document, Principal, Evidence | Policy Decision (ALLOW/DENY/QUARANTINE) | **Yes** (governs gate passage) | Default DENY |
| **CapabilityGate** | **Yes** | No | Requested tool call, Session state | Execution verdict | **Yes** (authorizes tool dispatch) | Deny unauthorized calls |
| **ResourceTracker** | **Yes** | No | Token / query execution metrics | Budget enforcement signal | **Yes** (terminates runaway tasks) | Hard termination on budget limit |
| **OutputGuard** | **Yes** | No | Raw model generation | Egress payload / Suppression | **Yes** (authorizes egress) | Suppress & redact output |
| **Language Model (LLM)** | **NO** | **Yes** | Rendered prompt text | Candidate generation text | **NO** (Zero Authority) | Untrusted generation; quarantined |

---

## 3. Core Architectural Invariants Enforced by the TCB

1. **Non-Escalation ($I_1$):**  
   $$\mathrm{EffectiveCapabilities}(x, s) \subseteq \mathrm{TrustedCapabilities}(s)$$  
   No text submitted by a user or ingested via external retrieval can grant capabilities beyond those statically bound to the authenticated principal.

2. **Prompt $\neq$ Authority ($I_2$):**  
   Natural-language requests contribute semantic intent but possess zero intrinsic authority. System security decisions depend exclusively on verified credentials, cryptographic evidence, and deterministic policy rules.

3. **Evidence Admission ($I_3$):**  
   $$\mathrm{Retrieved}(e) \centernot\implies \mathrm{Authoritative}(e)$$  
   Relevance in RAG search does not confer evidence validity. Evidence must satisfy exact authority allow-listing, hash integrity, and absence of instruction-bearing payloads.

4. **Post-Generation Confinement ($I_4$):**  
   Raw model output is untrusted data until revalidated by OutputGuard against schema constraints, DLP rules, and citation claims.
