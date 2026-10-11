# HETE Architectural Invariant Traceability Matrix

**Version:** 3.0.0  
**Specification:** SCIE Security Evidence Traceability

---

| Invariant | Implementation Component | Property / Unit Test | Targeted Attack Class | Metric | Observed Result |
|---|---|---|---|---|:---:|
| **$I_1$: Capability Monotonicity**<br>$\mathrm{EffectiveCaps}(x, s) \subseteq \mathrm{TrustedCaps}(s)$ | `CapabilityGate`, `create_trusted_security_context`, `principals.json` | `tests/security_v3/test_authority_non_escalation.py` | `excessive_agency_tool_escalation` | Tool Escalation Success Rate | **0.0%** (Contained) |
| **$I_2$: Prompt $\neq$ Authority**<br>Untrusted text cannot allocate authorization | `InputGuard`, `LanguageRouter`, `UirV2Builder` | `tests/security_v3/test_taint_propagation.py`, `test_no_label_leakage.py` | `direct_prompt_injection`, `jailbreak_policy_override` | Security Field Mutation Rate | **0.0%** (Immutable) |
| **$I_3$: Evidence Admission Independence**<br>$\mathrm{Retrieved}(e) \centernot\implies \mathrm{Authoritative}(e)$ | `ProvenanceVerifier`, `TrustedResolver` | `tests/security_v3/test_evidence_admission.py`, `test_provenance_security.py` | `poisoned_retrieval_evidence`, provenance spoofing | Poisoned Evidence Adoption Rate | **0.0%** (Quarantined) |
| **$I_4$: Post-Generation Confinement**<br>Raw model output cannot commit effects | `OutputGuard` (DLP, schema validator, citation matcher) | `tests/security_v3/test_output_non_authority.py` | `sensitive_data_exfiltration`, unauthorized code emission | Canary Exfiltration Rate | **0.0%** (Suppressed) |
| **$I_5$: Fail-Closed Routing**<br>Syntactic parser errors fail closed | `EnglishFrontend`, `KoreanFrontend` | `evaluation/llm_security_v3/parser_robustness/run_parser_robustness.py` | Adversarial syntactic noise, homoglyphs | Authority Escalation Rate | **0.0%** (Contained) |
| **$I_6$: Resource Boundedness**<br>$\mathrm{Tokens} \le B_{\mathrm{tok}} \land t \le B_{\mathrm{time}}$ | `ResourceTracker`, `ResourceBudget` | `evaluation/llm_security_v3/baselines/uir_v3_security.py` | `resource_exhaustion` | Runaway Latency / OOM | **0.0%** (Terminated) |
