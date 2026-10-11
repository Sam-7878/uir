# HETE UIR-ZTA Major-Revision Implementation Plan

This plan establishes the execution roadmap for addressing the Grok SCI-security review and independent audit findings in accordance with [HETE_UIR_ZTA_GROK_REVIEW_MAJOR_REVISION_WORK_ORDER.md](file:///d:/_Work/goat_bank/uir/docs/work_reports/200_zta_phase_1/HETE_UIR_ZTA_GROK_REVIEW_MAJOR_REVISION_WORK_ORDER.md) and [background.md](file:///d:/_Work/goat_bank/uir/docs/work_reports/200_zta_phase_1/background.md).

The central philosophy of this revision is:
> **Do not optimize for 0% ASR. Produce evidence that remains credible when oracle labels are hidden, held-out attacks are independent, the attacker knows the defense, stronger models are used, and contemporary defenses are compared fairly.** Non-zero HETE E2E-ASR under severe adaptive pressure directly validates the core thesis: *a compromised model does not imply a compromised system when authority is externalized*.

---

## User Review Required

> [!IMPORTANT]
> **1. Preservation of Historical v2 Artifacts**  
> As instructed, `evaluation/llm_security` and `results/llm_security_v2` will remain intact as pre-revision engineering baselines. All new work will be developed under `evaluation/llm_security_v3`, `results/llm_security_v3`, `docs/security_v3`, and `docs/formal`.
>
> **2. Title & Claim Alignment**  
> Based on Work Order §10 and Grok Review M5, we recommend adjusting the manuscript title to:  
> **"HETE: A Typed Intermediate Representation and Deterministic Enforcement Envelope for Zero-Trust Language-Model Execution"**  
> (or alternatively retaining "Neuro-Symbolic" backed by our formal Policy DSL, typed taint flow, and explicit TCB boundaries).
>
> **3. Execution Environment Confirmation**  
> We confirmed that:
> - Ubuntu 26.04.1 LTS on WSL2 is active.
> - Python 3.12.13 in `/mnt/d/_Work/goat_bank/.venv` is active and `jsonschema` has been installed.
> - `/snap/bin/ollama` is running live at `http://localhost:11434` with both required models: `phi3.5:latest` (3.8B) and `qwen2.5:7b` (7.6B).

---

## Open Questions

> [!NOTE]
> 1. **Title Preference:** Do you prefer the scoped title (*HETE: A Typed Intermediate Representation and Deterministic Enforcement Envelope for Zero-Trust Language-Model Execution*) or retaining *Neuro-Symbolic* with our formal policy DSL and symbolic taint semantics? (Default recommendation: use the scoped, highly defensible title).
> 2. **Baseline Selection for P2:** In addition to **CaMeL** and **Spotlighting**, would you like to include an implementation of **Progent** as a third comparison? (Default recommendation: Yes, implement CaMeL, Spotlighting, and Progent).

---

## Proposed Changes

```
uir/
├── evaluation/
│   └── llm_security_v3/
│       ├── __init__.py
│       ├── schema/
│       │   ├── runtime_case.py           # Strictly SUT-visible fields
│       │   └── oracle_case.py            # Evaluation oracle-only fields
│       ├── fixtures/
│       │   ├── principals.json           # Authenticated & limited principals
│       │   └── environments.json         # Deployment contexts
│       ├── attacks/
│       │   ├── generator_v3.py           # Independent template generator
│       │   └── lexical_analyzer.py       # Defense-attack lexical overlap
│       ├── datasets/
│       │   ├── custom_dev_v3.jsonl
│       │   ├── custom_validation_v3.jsonl
│       │   ├── custom_heldout_v3.jsonl
│       │   └── oracle_heldout_v3.jsonl
│       ├── baselines/
│       │   ├── uir_v3_security.py        # Leakage-free HETE SUT
│       │   ├── camel_adapter.py          # CaMeL capability-sandbox adapter
│       │   ├── spotlighting_adapter.py   # Spotlighting prompt-marking adapter
│       │   ├── progent_adapter.py        # Progent tool-sandboxing adapter
│       │   └── vanilla_slm.py / naive_rag.py
│       ├── public_benchmarks/
│       │   └── agentdojo_adapter.py      # AgentDojo benchmark runner & adapter
│       ├── adaptive_attacks/
│       │   ├── campaigns.py              # A0/A1/A2 adaptive attack campaigns
│       │   └── search_runner.py          # Budgeted adaptive search engine
│       ├── parser_robustness/
│       │   └── run_parser_robustness.py  # Homoglyphs, unicode, code-switching, typos
│       ├── human_validation/
│       │   ├── sample_cases.py           # Blinded 200+ case sampling
│       │   └── adjudication_analyzer.py  # Inter-rater agreement & Cohen's kappa
│       ├── audit_semantic_leakage.py     # N-gram and embedding similarity audit
│       ├── run_publication_campaign.py   # Unified v3 execution runner
│       └── validate_publication_results.py
├── results/
│   └── llm_security_v3/
│       ├── publication_manifest.json
│       ├── containment_funnel.json
│       ├── defense_attack_lexical_overlap.json
│       └── ... (CSVs and JSON summaries)
├── docs/
│   ├── security_v3/
│   │   ├── TCB_MANIFEST.md / .json
│   │   ├── FRONTEND_SPEC.md
│   │   ├── CONTEXT_FIREWALL_SPEC.md
│   │   └── INVARIANT_TRACEABILITY.md
│   └── formal/
│       ├── SECURITY_POLICY_DSL.ebnf
│       └── SECURITY_POLICY_SEMANTICS.md
├── tests/
│   └── security_v3/
│       ├── test_no_label_leakage.py
│       ├── test_provenance_security.py
│       ├── test_authority_non_escalation.py
│       ├── test_taint_propagation.py
│       ├── test_evidence_admission.py
│       └── test_output_non_authority.py
└── docs/papers/_47_1_UIR_for_ZTA/
    ├── _47.1_UIR_ZTA.tex                 # Revised manuscript source
    └── references.bib                    # Cleaned & augmented bibtex
```

---

### Phase 0: P0 Critical Evaluation-Integrity Repair

#### [NEW] [runtime_case.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/schema/runtime_case.py)
#### [NEW] [oracle_case.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/schema/oracle_case.py)
- Enforce complete data separation: `RuntimeCase` contains only `case_id`, `language`, `user_input`, `retrieved_context`, `principal_id`, and `environment_id`.
- `OracleCase` retains `attack_class`, `attack_goal`, `expected_answer`, `forbidden_actions`, and `canaries`.
- No SUT pipeline receives `OracleCase`.

#### [NEW] [principals.json](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/fixtures/principals.json)
#### [NEW] [environments.json](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/fixtures/environments.json)
- Define authenticated enterprise roles (`finance_analyst_authenticated`, `finance_viewer_authenticated`, `tool_user_limited`, `tool_user_privileged`, `anonymous_public_user`).
- Both benign requests and direct injection attacks are issued under the *same real principal* (e.g., `finance_analyst_authenticated`), guaranteeing that authorization decisions depend strictly on authenticated session state and policy, not benchmark labels.

#### [NEW] [uir_v3_security.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/baselines/uir_v3_security.py)
- Refactored HETE pipeline that ingests only `RuntimeCase`.
- Integrates typed evidence provenance (`SourceIdentity` with scheme, authority, resource_id, sha256 hash, and manifest validation).
- Eliminates substring domain trust matching to reject lookalikes (e.g. `sec.gov.attacker.example`).

#### [NEW] [generator_v3.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/attacks/generator_v3.py)
#### [NEW] [audit_semantic_leakage.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/audit_semantic_leakage.py)
- Generate a genuinely independent held-out set (>= 800 cases: >= 200 benign, >= 600 attacks) using disjoint templates and public benchmark attacks.
- Audit semantic leakage (n-gram overlap, exact duplicates, template overlap, entity overlap).
- Measure lexical overlap in `results/llm_security_v3/defense_attack_lexical_overlap.json`.

#### [NEW] [test_no_label_leakage.py](file:///d:/_Work/goat_bank/uir/tests/security_v3/test_no_label_leakage.py)
#### [NEW] [test_provenance_security.py](file:///d:/_Work/goat_bank/uir/tests/security_v3/test_provenance_security.py)
- Automated AST and runtime inspection asserting that no SUT component imports or accesses oracle fields.
- Provenance tests covering substring spoofing, unicode punycode lookalikes, hash tampering, and unverified source quarantine.

---

### Phase 1: P1 TCB & Formal Specification

#### [NEW] [TCB_MANIFEST.md](file:///d:/_Work/goat_bank/uir/docs/security_v3/TCB_MANIFEST.md) / [TCB_MANIFEST.json](file:///d:/_Work/goat_bank/uir/docs/security_v3/TCB_MANIFEST.json)
- Explicit component audit table: LanguageRouter, Frontends, UIR Builder, Resolver, Context Firewall, Policy Engine, Capability Gate, LLM (NOT in TCB), OutputGuard.

#### [NEW] [FRONTEND_SPEC.md](file:///d:/_Work/goat_bank/uir/docs/security_v3/FRONTEND_SPEC.md) & [run_parser_robustness.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/parser_robustness/run_parser_robustness.py)
- Full documentation of deterministic multilingual frontend.
- Robustness evaluation over homoglyphs, zero-width spaces, code-switching, typos, and formatting noise.

#### [NEW] [CONTEXT_FIREWALL_SPEC.md](file:///d:/_Work/goat_bank/uir/docs/security_v3/CONTEXT_FIREWALL_SPEC.md)
- Formal specification of instruction-bearing content detection, sanitization, and quarantine policies.

#### [NEW] [SECURITY_POLICY_DSL.ebnf](file:///d:/_Work/goat_bank/uir/docs/formal/SECURITY_POLICY_DSL.ebnf) & [SECURITY_POLICY_SEMANTICS.md](file:///d:/_Work/goat_bank/uir/docs/formal/SECURITY_POLICY_SEMANTICS.md)
- Machine-readable EBNF grammar and operational semantics for security policies.

#### [NEW] Invariant Tests & Traceability
- [test_authority_non_escalation.py](file:///d:/_Work/goat_bank/uir/tests/security_v3/test_authority_non_escalation.py): `EffectiveCapabilities(x, s) ⊆ TrustedCapabilities(s)`
- [test_taint_propagation.py](file:///d:/_Work/goat_bank/uir/tests/security_v3/test_taint_propagation.py): Untrusted text cannot synthesize authorization tokens or rules.
- [test_evidence_admission.py](file:///d:/_Work/goat_bank/uir/tests/security_v3/test_evidence_admission.py): `Retrieved(e) !=> Authoritative(e)`
- [test_output_non_authority.py](file:///d:/_Work/goat_bank/uir/tests/security_v3/test_output_non_authority.py): Raw model output cannot directly commit side effects.
- [INVARIANT_TRACEABILITY.md](file:///d:/_Work/goat_bank/uir/docs/security_v3/INVARIANT_TRACEABILITY.md): Maps formal invariants to implementation, property tests, and observed benchmark outcomes.

---

### Phase 2: P2 Baselines & Public Benchmarks

#### [NEW] [camel_adapter.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/baselines/camel_adapter.py)
- Faithful adapter for CaMeL (capability-based sandboxing, untrusted data isolation, and control flow extraction).

#### [NEW] [spotlighting_adapter.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/baselines/spotlighting_adapter.py) & [progent_adapter.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/baselines/progent_adapter.py)
- Spotlighting baseline (input marking and delimiter isolation) and Progent (fine-grained tool sandboxing).

#### [NEW] [agentdojo_adapter.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/public_benchmarks/agentdojo_adapter.py)
- Public benchmark evaluation adapter providing external attack and utility distributions.

---

### Phase 3: P3 Adaptive Attacks

#### [NEW] [campaigns.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/adaptive_attacks/campaigns.py) & [search_runner.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/adaptive_attacks/search_runner.py)
- Attacker knowledge models:
  - **A0 (Black-box):** Input/output probing only.
  - **A1 (Gray-box):** System architecture and output schema known.
  - **A2 (White-box adaptive):** Full parser rules, regexes, policy semantics, and output schema known.
- Six campaigns: Parser manipulation, Firewall bypass (lexically novel), Output-contract bypass, Provenance spoofing, Capability escalation, Multi-turn attacks.
- Budgeted search recording bypass curves (ASR vs. query budget up to 20 queries).

---

### Phase 4: P4 Multi-Model & Decoding Robustness

- Execute across two local models via Ollama:
  1. `microsoft/Phi-3.5-mini-instruct` (`phi3.5:latest`)
  2. `Qwen/Qwen2.5-7B-Instruct` (`qwen2.5:7b`)
- Decoding conditions:
  - Deterministic: `temperature=0`
  - Stochastic: `temperature=0.7`, `top_p=0.9`, 5 random seeds.

---

### Phase 5: P5 Human Oracle Validation & Utility Redesign

#### [NEW] [sample_cases.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/human_validation/sample_cases.py) & [adjudication_analyzer.py](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3/human_validation/adjudication_analyzer.py)
- Protocol for 200+ blinded adjudication cases across benign, attack, and adaptive runs.
- Compute raw agreement and Cohen's kappa ($\kappa \ge 0.80$).
- Disentangle utility metrics: System-Neutral Semantic Utility, Contract Utility, Structured Validity, Citation Accuracy, FRR.

---

### Phase 6: P6 Results, Containment Funnel & Statistics

- Generate [containment_funnel.json](file:///d:/_Work/goat_bank/uir/results/llm_security_v3/containment_funnel.json):
  `Attack Attempted -> Model Compromised (MCR) -> Pre-LLM Blocked -> Post-LLM Guard Blocked -> Reached Trusted Effect (E2E-ASR)`.
- Path-separated latency analysis (Allowed, Pre-LLM Blocked, Post-LLM Blocked).
- Statistical tests (paired McNemar, 95% Wilson score intervals, absolute risk reduction).
- Publication manifest & strict validation gate.

---

### Phase 7: P7 & P8 Manuscript LaTeX Revision

#### [MODIFY] [_47.1_UIR_ZTA.tex](file:///d:/_Work/goat_bank/uir/docs/papers/_47_1_UIR_for_ZTA/_47.1_UIR_ZTA.tex)
- Title adjustment: Scoped title without overclaiming.
- Section 1 (Intro): Distill contributions to 3 core pillars; replace slogan boxes with rigorous technical exposition.
- Section 2 (Related Work): Add CaMeL, Instruction Hierarchy, IsolateGPT, Progent, and Zhan et al. (adaptive attacks) into a structured capability/IFC taxonomy.
- Section 3 (Threat Model & TCB): Full TCB specification matching `TCB_MANIFEST.md`; explicitly model A0, A1, and A2 attackers.
- Section 4 (Architecture): Concrete specification of deterministic frontends, typed UIR, provenance tiers, and policy engine.
- Section 5 (Formal Invariants): Replace analogy math ($\partial C_t / \partial a = 0$) with formal invariant theorems and noninterference properties.
- Section 6 & 7 (Evaluation & Results):
  - Replace low-information 0% tables with full comparative results (Vanilla, Naive RAG, Prompt Guard, CaMeL, Spotlighting, HETE).
  - Containment funnel table and figure.
  - Multi-model comparison (Phi-3.5 vs Qwen2.5-7B).
  - Adaptive attack evaluation results.
  - Public benchmark (AgentDojo) results.
  - Path-separated latency table.
  - Human validation agreement metrics.
- Section 8 & 9 (Discussion & Limitations): Qualitative failure analysis of near-misses and adaptive attacks; clear articulation of residual risks.
- IEEEtran formatting cleanup:
  - Remove `\usepackage{kotex}` and Korean comments.
  - Clean up duplicated packages (`hyperref`, `tikz`).
  - Standardize journal author/affiliation blocks.
  - Remove engineering status logs (`publication_eligible=true`).

#### [MODIFY] [references.bib](file:///d:/_Work/goat_bank/uir/docs/papers/_47_1_UIR_for_ZTA/references.bib)
- Add entries for CaMeL, Instruction Hierarchy, AgentDojo, InjecAgent, Progent, Spotlighting, StruQ, SecAlign.
- Fix arXiv/@article citations to official peer-reviewed conference/journal versions where available; resolve duplicate entries (e.g. `zou2024poisonedrag` vs `zou2025poisonedrag`).

---

### Phase 8: Final Work Report Deliverables

- Create [HETE_UIR_MAJOR_REVISION_FINAL_REPORT.md](file:///d:/_Work/goat_bank/uir/docs/work_reports/200_zta_phase_1/HETE_UIR_MAJOR_REVISION_FINAL_REPORT.md) answering all 20 required questions from Work Order §16.

---

## Verification Plan

### Automated Tests
Execute in Ubuntu 26.04.1 WSL2 environment using `/mnt/d/_Work/goat_bank/.venv/bin/python`:
```bash
# 1. Label leakage & Provenance tests
PYTHONPATH=. /mnt/d/_Work/goat_bank/.venv/bin/python -m pytest tests/security_v3/test_no_label_leakage.py tests/security_v3/test_provenance_security.py

# 2. Formal Invariants & Authority flow tests
PYTHONPATH=. /mnt/d/_Work/goat_bank/.venv/bin/python -m pytest tests/security_v3/test_authority_non_escalation.py tests/security_v3/test_taint_propagation.py tests/security_v3/test_evidence_admission.py tests/security_v3/test_output_non_authority.py

# 3. Parser robustness suite
PYTHONPATH=. /mnt/d/_Work/goat_bank/.venv/bin/python -m evaluation.llm_security_v3.parser_robustness.run_parser_robustness

# 4. End-to-end publication campaign execution
PYTHONPATH=. /mnt/d/_Work/goat_bank/.venv/bin/python -m evaluation.llm_security_v3.run_publication_campaign

# 5. Strict publication gate validation
PYTHONPATH=. /mnt/d/_Work/goat_bank/.venv/bin/python -m evaluation.llm_security_v3.validate_publication_results --strict
```

### Manual Verification
- Verify LaTeX compilation of `_47.1_UIR_ZTA.tex` (no duplicate package errors, clean PDF output).
- Review all generated CSV tables and JSON artifacts for internal consistency.
- Inspect `containment_funnel.json` to verify that `MCR > E2E-ASR` is empirically observed and documented.
