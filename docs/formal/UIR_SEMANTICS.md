# Formal Operational Semantics and Invariant Theory of UIR
## Specification Version: 4.0.0

**Target Manuscript:** *A Universal Intermediate Representation for Policy-Constrained Multilingual Small Language Model Agents*  
**Scope:** Operational semantics, formal condition typing system, transition relations, and inductive safety invariant proofs.

---

## 1. Mathematical Foundations & Operational Judgment

We formalize the execution of an agent pipeline over a compiled Universal Intermediate Representation (UIR) document $\mathcal{U}$, an enterprise policy database $\mathcal{P}$, and an environmental context $\mathcal{C}$.

### 1.1 Domains and State Signatures

Let the system domains be defined as follows:
- $\mathcal{U} \in \mathbf{UIR}$: The set of well-formed, typed UIR documents.
- $\mathcal{P} \in \mathbf{Policy}$: The hierarchical lattice of policy constraints $\mathcal{P} = \langle L_0, L_1, L_2, L_3 \rangle$.
- $\mathcal{C} \in \mathbf{Context}$: The trusted runtime context comprising authoritative fact registry $\mathcal{V}_{\text{facts}}$, session state, and permissions $\langle \mathcal{V}_{\text{facts}}, \sigma, \tau \rangle$.
- $\mathcal{D} \in \mathbf{Decision}$: The set of policy outcomes:
  $$\mathbf{Decision} \triangleq \{ \text{Allow}, \text{Reject}(r), \text{Quarantine}(r), \text{NeedsClarification}(q) \}$$
  where $r \in \mathbf{ReasonCode}$ and $q \in \mathbf{ClarificationPrompt}$.

### 1.2 Big-Step Policy Evaluation Judgment

The deterministic policy evaluation is denoted by the judgment relation:

$$\langle \mathcal{U}, \mathcal{P}, \mathcal{C} \rangle \Downarrow \mathcal{D}$$

The evaluation rules proceed through strict lexicographical hierarchy from $L_0$ to $L_3$:

#### Rule 1: System-Level Hard Stop (L0 Violation)
$$\frac{\exists r \in L_0 \quad \text{s.t.} \quad \neg \text{Sat}(r, \mathcal{U}, \mathcal{C})}{\langle \mathcal{U}, \mathcal{P}, \mathcal{C} \rangle \Downarrow \text{Reject}(\text{"L0\_SYSTEM\_FAULT"})}$$

#### Rule 2: Entity Unverified (L1 Domain Gate)
$$\frac{\mathcal{U}.\text{target}.\text{entity\_id} \notin \text{Dom}(\mathcal{V}_{\text{facts}})}{\langle \mathcal{U}, \mathcal{P}, \mathcal{C} \rangle \Downarrow \text{Reject}(\text{"ENTITY\_UNVERIFIED"})}$$

#### Rule 3: Condition Evaluation Failure
$$\frac{\mathcal{C} \not\models \mathcal{U}.\text{conditions}}{\langle \mathcal{U}, \mathcal{P}, \mathcal{C} \rangle \Downarrow \text{Reject}(\text{"CONDITION\_UNSATISFIED"})}$$

#### Rule 4: Enterprise Policy Rejection (L2 Violation)
$$\frac{\exists r \in L_2 \quad \text{s.t.} \quad \neg \text{Sat}(r, \mathcal{U}, \mathcal{C}) \quad \wedge \quad \text{Action}(r) = \text{Block}}{\langle \mathcal{U}, \mathcal{P}, \mathcal{C} \rangle \Downarrow \text{Reject}(\text{"ENTERPRISE\_POLICY\_VIOLATION"})}$$

#### Rule 5: Permitted Execution (Allow)
$$\frac{\forall i \in \{0,1,2\}, \ \forall r \in L_i, \ \text{Sat}(r, \mathcal{U}, \mathcal{C}) \quad \wedge \quad \mathcal{C} \models \mathcal{U}.\text{conditions} \quad \wedge \quad \text{EntityVerified}(\mathcal{U}.\text{target})}{\langle \mathcal{U}, \mathcal{P}, \mathcal{C} \rangle \Downarrow \text{Allow}}$$

---

## 2. Typed Condition Abstract Syntax Tree (AST)

Conditions in UIR are typed propositions evaluated over context attributes.

### 2.1 Types and Values

$$\tau ::= \mathbf{Bool} \mid \mathbf{Num} \mid \mathbf{Str} \mid \mathbf{EntityId}$$

Evaluation environment $\Gamma: \mathbf{Identifier} \to \tau$ maps bound parameters and context variables to static types.

### 2.2 Typing Rules ($\Gamma \vdash e : \tau$)

#### Relational Operator Typing (Numeric)
$$\frac{\Gamma \vdash e_1 : \mathbf{Num} \quad \Gamma \vdash e_2 : \mathbf{Num} \quad \text{op} \in \{\text{GT}, \text{GE}, \text{LT}, \text{LE}\}}{\Gamma \vdash \text{op}(e_1, e_2) : \mathbf{Bool}}$$

#### Equality Typing
$$\frac{\Gamma \vdash e_1 : \tau \quad \Gamma \vdash e_2 : \tau \quad \text{op} \in \{\text{EQ}, \text{NE}\}}{\Gamma \vdash \text{op}(e_1, e_2) : \mathbf{Bool}}$$

#### Logical Conjunction and Disjunction
$$\frac{\forall i \in \{1, \dots, n\}, \quad \Gamma \vdash e_i : \mathbf{Bool} \quad n \ge 2 \quad \text{op} \in \{\text{AND}, \text{OR}\}}{\Gamma \vdash \text{op}(e_1, \dots, e_n) : \mathbf{Bool}}$$

#### Negation
$$\frac{\Gamma \vdash e : \mathbf{Bool}}{\Gamma \vdash \text{NOT}(e) : \mathbf{Bool}}$$

#### Exceptional Override (Modal Exception)
$$\frac{\Gamma \vdash e_{\text{rule}} : \mathbf{Bool} \quad \Gamma \vdash e_{\text{except}} : \mathbf{Bool}}{\Gamma \vdash \text{EXCEPT}(e_{\text{rule}}, e_{\text{except}}) : \mathbf{Bool}}$$

Semantics of `EXCEPT`:
$$\llbracket \text{EXCEPT}(e_{\text{rule}}, e_{\text{except}}) \rrbracket_\mathcal{C} \triangleq \llbracket e_{\text{rule}} \rrbracket_\mathcal{C} \land \neg \llbracket e_{\text{except}} \rrbracket_\mathcal{C}$$

**Static Type Soundness:** Any expression failing static type checking (e.g., $\text{GT}(\text{"apple"}, 42)$) raises a `TYPE_CHECK_FAILURE` before compilation or policy execution.

---

## 3. Post-Generation Output Guard Semantics

Let $M$ denote the local small language model and $\mathcal{R}_{\text{raw}} = M(\mathcal{U}_{\text{prompt}})$ be the raw generation output. The deterministic filter and renderer $\Pi$ executes as follows:

$$\Pi(\mathcal{R}_{\text{raw}}, \mathcal{V}_{\text{facts}}) \to \mathcal{R}_{\text{final}}$$

Let $\text{Claims}(\mathcal{R}_{\text{raw}}) = \{c_1, \dots, c_m\}$. Each candidate claim $c_i$ undergoes projection against the verified fact catalog $\mathcal{V}_{\text{facts}}$:

$$\text{ProjectClaim}(c_i, \mathcal{V}_{\text{facts}}) = \begin{cases}
c_i^* & \text{if } \exists v \in \mathcal{V}_{\text{facts}} \text{ s.t. } \text{Match}(c_i, v) \\
\bot & \text{otherwise}
\end{cases}$$

where $c_i^*$ binds exact numeric, unit, and provenance attributes directly from $v$.

The final output is rendered via deterministic template:
$$\mathcal{R}_{\text{final}} \triangleq \text{Render}(\{c_i^* \mid \text{ProjectClaim}(c_i, \mathcal{V}_{\text{facts}}) \neq \bot\})$$

If all claims are ungrounded and no verified claims can be emitted, the pipeline emits a graceful safe fallback rather than unverified text:
$$\mathcal{R}_{\text{final}} \gets \text{"NO\_VERIFIED\_FACT\_AVAILABLE"}$$

---

---

## 4. Conditional Safety Properties and Proof Sketches

All formal safety properties are conditional upon explicit architectural assumptions:
- **A1:** Authoritative registry integrity.
- **A2:** Trusted policy store integrity.
- **A3:** Correct fact-ID binding.
- **A4:** Output guard cannot be bypassed.
- **A5:** Deterministic renderer uses only accepted claims.

### Invariant 1 (INV-1: Fail-Closed Execution)
**Proposition 1 (Conditional Fail-Closed Invariant).** *Under assumptions A1–A2, if $\langle \mathcal{U}, \mathcal{P}, \mathcal{C} \rangle \Downarrow \mathcal{D}$ with $\mathcal{D} \in \{\text{Reject}, \text{Quarantine}\}$, downstream SLM inference $M$ and natural language generation are strictly unreachable in the execution transition system.*

*Proof Sketch.* In the execution dispatcher, invocation of $M$ is wrapped in a deterministic pattern match:
$$\text{Dispatch}(\mathcal{U}) = \mathbf{match} \ \text{EvalPolicy}(\mathcal{U}) \ \mathbf{with} \ \{ \text{Allow} \implies \text{RunInference}(\mathcal{U}), \ \text{Reject}(r) \implies \text{EmitReject}(r), \ \text{Quarantine}(r) \implies \text{EmitQuarantine}(r) \}$$
Because $\text{Dispatch}$ is executed as a compiled deterministic branch in the trusted host environment (Rust core / Python runner) and does not depend on model generation, control flow strictly diverts to `EmitReject` or `EmitQuarantine` when $\mathcal{D} \neq \text{Allow}$. (Mechanically tested invariant in test suite). $\blacksquare$

### Invariant 2 (INV-2: Conditional Grounding Soundness)
**Proposition 2 (Unreachability of Unsupported Claims).** *Under assumptions A1–A5, unsupported factual claims are unreachable in the accepted-output transition system: all accepted claims in $\mathcal{R}_{\text{final}}$ are admitted by the verified fact projection $\Pi(\cdot, \mathcal{V}_{\text{facts}})$.*

*Proof Sketch.* By construction of the verified projection $\Pi$, the output guard filters all candidate claims $C = \{c_1, \dots, c_m\}$ against $\mathcal{V}_{\text{facts}}$:
$$\text{AcceptedClaims}(\mathcal{R}_{\text{final}}) = \{ c_i^* \mid \text{ProjectClaim}(c_i, \mathcal{V}_{\text{facts}}) \neq \bot \}$$
Under assumption A4 (the output guard cannot be bypassed) and assumption A5 (the renderer is deterministic and prints only elements of $\text{AcceptedClaims}$), no unverified token sequence generated by the SLM can become an accepted output. Consequently, unsupported claims cannot transition to the accepted output state within the formal abstract machine. $\blacksquare$

### Invariant 3 (INV-3: Numeric Binding Invariance)
**Proposition 3 (Exact Numeric Value Preservation).** *Under assumptions A1, A3, and A5, for every accepted numeric claim $c \in \mathcal{R}_{\text{final}}$, $\text{Value}(c) = \text{Value}(v)$ and $\text{Unit}(c) = \text{Unit}(v)$ where $v = \text{SourceFact}(c) \in \mathcal{V}_{\text{facts}}$.*

*Proof Sketch.* In the UIR rendering pipeline, the SLM emits symbolic references to verified slot IDs ($\text{fact\_id} \in \{\text{fact\_001}, \dots, \text{fact\_k}\}$). The deterministic renderer dereferences $\text{fact\_id}$ directly against $\mathcal{V}_{\text{facts}}$ and prints the verbatim string representation of the numeric value and unit. Because authoritative numbers are not generated autoregressively by the SLM, model numeric drift is prevented by construction. $\blacksquare$

### Invariant 4 (INV-4: Semantic Digest Invariance)
**Proposition 4 (Metadata Invariance of Semantic Digest).** *Let $\mathcal{U}_1$ and $\mathcal{U}_2$ differ only in non-semantic transient metadata fields $\mathcal{M}_{\text{transient}}$ (e.g. timestamps, request correlation IDs). Then $\text{Digest}(\mathcal{U}_1) = \text{Digest}(\mathcal{U}_2)$.*

*Proof Sketch.* The canonical digest function $\mathcal{H}_{\text{sem}}(\mathcal{U})$ strips all keys matching $\mathcal{M}_{\text{transient}}$ before performing lexicographically sorted JSON canonicalization:
$$\mathcal{H}_{\text{sem}}(\mathcal{U}) = \text{SHA256}(\text{Canonicalize}(\mathcal{U} \setminus \mathcal{M}_{\text{transient}}))$$
Since $\mathcal{U}_1 \setminus \mathcal{M}_{\text{transient}} \equiv \mathcal{U}_2 \setminus \mathcal{M}_{\text{transient}}$, their canonical byte streams are identical, guaranteeing matching SHA-256 digests. (Mechanically tested invariant in test suite). $\blacksquare$

### Invariant 5 (INV-5: Controlled Cross-Language Canonicalization)
**Proposition 5 (Cross-Language Canonical Equivalence).** *For queries $Q_{\text{ko}}$ and $Q_{\text{en}}$ within the supported Korean and English controlled-language grammar sharing declared parallel semantics:*
$$\mathcal{H}_{\text{sem}}(\text{Transpile}_{\text{ko}}(Q_{\text{ko}})) = \mathcal{H}_{\text{sem}}(\text{Transpile}_{\text{en}}(Q_{\text{en}}))$$

*Proof Sketch.* The frontends $T_{\text{ko}}$ and $T_{\text{en}}$ map language-specific morphological tokens, postpositions, and prepositions into unified domain enums (`Intent`, `EntityId`, `Metric`, `Period`). The synthesized ASTs share identical schema node hierarchies and canonical serializations, producing identical digests. This property holds strictly within the evaluated controlled grammar and does not extend to unconstrained natural language. $\blacksquare$
