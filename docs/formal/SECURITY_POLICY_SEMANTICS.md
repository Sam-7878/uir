# HETE Security Policy DSL Operational Semantics

**Version:** 3.0.0  
**Grammar Reference:** `docs/formal/SECURITY_POLICY_DSL.ebnf`  
**Executable Mapping:** `llm_trust/policy/security_policy_engine.py`

---

## 1. Evaluation Model

The HETE Policy Engine evaluates an incoming request $r = \langle p, a, R, E, c \rangle$ against an ordered set of rules $\mathcal{P} = \{r_1, r_2, \dots, r_n\}$ where:
- $p$: Authenticated Principal (`principal.id`, `principal.trust_level`, `principal.roles`)
- $a$: Requested Action / Intent (`action.name`, `action.type`)
- $R$: Target Resource (`resource.id`, `resource.classification`)
- $E$: Evidence Set ($\{e_1, \dots, e_k\}$ with cryptographic provenance tiers)
- $c$: Capability Set bound to session

---

## 2. Invariant Semantics and Evaluation Precedence

### 2.1 Precedence Hierarchy
1. **Rule 1: Hard Deny Invariant (POL-SEC-001):**  
   If $a \in \mathrm{ForbiddenCapabilities}(p)$, decision is `DENY`.
2. **Rule 2: Capability Monotonicity (POL-CAP-001):**  
   If $a \notin \mathrm{AllowedCapabilities}(p)$, decision is `DENY`.
3. **Rule 3: Evidence Quarantine (POL-EVD-001):**  
   If $\exists e \in E$ such that $e.\mathrm{instruction\_bearing} = \mathrm{TRUE}$ and $e.\mathrm{tier} = \mathrm{QUARANTINED}$, decision is `QUARANTINE_EVIDENCE`.
4. **Rule 4: Classification Clearance (POL-CLR-001):**  
   If $R.\mathrm{classification} > p.\mathrm{clearance}$, decision is `DENY`.
5. **Rule 5: Resource Budget (POL-RES-001):**  
   If token usage or latency budget is exceeded, decision is `DENY`.
6. **Rule 6: Explicit Permission Rule:**  
   If all conditions evaluate to `TRUE`, decision is `ALLOW`.
7. **Rule 7: Fall-Through Default:**  
   **DEFAULT DENY:** If no rule explicitly matches, the outcome is strictly `DENY`.

---

## 3. Core Theorems and Invariants

### Theorem 1 (Capability Monotonicity)
$$\forall x \in \mathrm{Inputs},\quad \mathrm{EffectiveCapabilities}(x, s) \subseteq \mathrm{TrustedCapabilities}(s)$$

*Proof Sketch:*  
$\mathrm{EffectiveCapabilities}$ is computed solely by looking up $p$ in `principals.json` through `create_trusted_security_context`. The parsing of user text $x$ produces only an unauthenticated syntactic draft (`ParsedDraft`) without write access to the session capability vector. Downstream dispatch via `CapabilityGate` checks $a \in \mathrm{TrustedCapabilities}(s)$. If $a \notin \mathrm{TrustedCapabilities}(s)$, execution is refused. Hence, natural-language input $x$ cannot expand the capability set. $\blacksquare$

### Theorem 2 (Evidence Admission Independence)
$$\forall e \in E,\quad \mathrm{Retrieved}(e) \centernot\implies \mathrm{Authoritative}(e)$$

*Proof Sketch:*  
Retrieved items from vector indices or external APIs are initially tagged with `tier = UNVERIFIED`. An evidence item transitions to `Authoritative` if and only if $\mathrm{ProvenanceVerifier}(e)$ validates that $e.\mathrm{authority} \in \mathrm{TRUSTED\_AUTHORITIES}$, $e.\mathrm{sha256} = \mathrm{SHA256}(e.\mathrm{content})$, and $e.\mathrm{instruction\_bearing} = \mathrm{FALSE}$. Search similarity score plays zero role in authority assignment. $\blacksquare$

### Theorem 3 (Post-Generation Non-Authority)
$$\mathrm{RawModelOutput} \centernot\to \mathrm{TrustedStateMutation}$$

*Proof Sketch:*  
The language model emits unconstrained UTF-8 string tokens. The string is buffered in local memory and passed directly to `OutputGuard.validate`. No operating system system-call, database write, or external HTTP request is invoked by the inference engine. Only after schema conformance and citation validation are satisfied does the system present the text to the user. $\blacksquare$
