# Implementation Plan — HETE UIR Zero-Trust Security Extension & Repository Migration

## 1. Executive Summary & Theoretical Grounding

This project implements the **HETE UIR (Universal Intermediate Representation) Zero-Trust Security Extension** as specified in `HETE_UIR_SECURITY_EXTENSION_WORK_ORDER.md`.

### Core Theoretical Pivot
Rather than treating the LLM/SLM as a trusted component or relying on brittle prompt engineering / heuristic filters, **HETE treats the LLM as an untrusted semantic transformation component**. 
**UIR serves as the authoritative Security Reference Representation (SRR)**, surrounded by deterministic policy enforcement, capability binding, cryptographic evidence provenance, context firewalls, and output verification gates.

This directly aligns with the overarching PhD dissertation architecture:
$$\text{Network Trust (DLG-GNN)} \longrightarrow \text{Process Trust (POA/PBEA)} \longrightarrow \text{Data/AI Trust (HETE-UIR)} \Longrightarrow \text{Unified Zero-Trust Decision Model}$$

---

## 2. Proposed Work Breakdown & Milestones

### Phase 1: Repository Migration & Initial Workspace Setup
1. **Migrate UIR Components from `hete_sandbox` to `uir`**:
   - Copy `crates/poa-uir/` $\to$ `uir/crates/poa-uir/`
   - Copy `protocol/schemas/uir.schema.json` $\to$ `uir/protocol/schemas/uir.schema.json`
   - Copy `spec/poa-uir.md` $\to$ `uir/spec/poa-uir.md`
   - Copy `evaluation/uir*/` $\to$ `uir/evaluation/uir*/`
   - Copy `results/uir*/` $\to$ `uir/results/uir*/`
2. **Configure `uir` Workspace & Environment**:
   - Create root `Cargo.toml` in `uir` for standalone/linked Rust compilation.
   - Validate `.venv` Python environment (Python 3.12.13 in Ubuntu 24.04 WSL2) with all necessary packages.

---

### Phase 2: UIR Schema v2 & Core Zero-Trust Security Architecture (`uir/llm_trust/`)
Implement the full modular Python pipeline under `uir/llm_trust/`:

```text
Untrusted Input (User / RAG / Tool / Memory)
       │
       ▼
[1] Input Guard (`security/input_guard.py`)
       ├── Unicode normalization & length bounds
       └── Source & Taint tagging (USER, RAG, TOOL, MEMORY)
       │
       ▼
[2] Multilingual Frontends (`frontends/ko.py`, `frontends/en.py`, `frontends/router.py`)
       │
       ▼
[3] UIR Builder & Schema v2 (`uir/builder.py`, `uir/schema_v2.json`)
       ├── Strict JSON Schema v2 validation
       ├── Intent/Action typed constraints
       └── Immutable Security Context Binding (`uir/security_context.py`)
       │
       ▼
[4] Zero-Trust Policy Enforcement Point (PEP) (`policy/security_policy_engine.py`)
       ├── Privilege escalation & capability checks
       ├── Data classification & flow rules
       └── Deterministic decisions: ALLOW, DENY, CLARIFY, REQUIRE_APPROVAL, QUARANTINE_EVIDENCE, DEGRADE_TO_READ_ONLY
       │
       ▼
[5] Trusted Evidence Resolver & Context Firewall (`evidence/`, `security/context_firewall.py`)
       ├── Source allow-listing & SHA-256 integrity check (`evidence/provenance.py`, `evidence/trusted_resolver.py`)
       └── Strict Instruction/Data separation (untrusted context cannot alter executable intent)
       │
       ▼
[6] Capability & Resource Guards (`security/capability_gate.py`, `security/resource_guard.py`)
       ├── Least privilege tool allow-lists & human-in-the-loop approval token gate
       └── Deterministic token, retrieval, tool-call, timeout budgets
       │
       ▼
[7] LLM Renderer / Inference Engine (`inference/renderer.py`, `inference/ollama_client.py`)
       ├── Structured output prompt formulation
       └── Phi-3.5-mini-instruct (3.8B) local SLM inference + mock deterministic fallbacks
       │
       ▼
[8] Output Guard & DLP (`security/output_guard.py`)
       ├── Schema validation & verified fact-set ground check
       ├── Sensitive data leakage prevention (DLP)
       └── Action re-validation prior to downstream dispatch
       │
       ▼
[9] Audit & Common Evidence Envelope (`audit/security_event.py`)
       ├── Immutable RFC 8785 canonical hash chain
       └── Cross-layer Zero-Trust hook (Network / Process / AI Trust)
```

---

### Phase 3: 1,600-Case Bilingual Attack Benchmark Dataset (`uir/evaluation/llm_security/`)
Generate and freeze a **1,600-case dataset** (800 KO / 800 EN) across all 10 threat classes:

| Threat Class | Total Cases | KO | EN | Threat Description & Expected Behavior |
|---|---|---|---|---|
| **1. Benign Queries** | 200 | 100 | 100 | Valid requests $\to$ `ALLOW`, high utility |
| **2. Nonexistent Entity** | 200 | 100 | 100 | Fictitious entities $\to$ `REJECT` / `NO_VERIFIED_EVIDENCE` |
| **3. Gaslighting / False Premise** | 200 | 100 | 100 | Contradicted facts $\to$ `REJECT` / `FACT_MISMATCH` |
| **4. Direct Prompt Injection** | 200 | 100 | 100 | System rule override $\to$ `DENY` (intent unchanged) |
| **5. Jailbreak / Policy Override** | 150 | 75 | 75 | Privilege escalation $\to$ `DENY` (`POLICY_VIOLATION`) |
| **6. Indirect Prompt Injection** | 200 | 100 | 100 | RAG/tool instruction payload $\to$ `QUARANTINE_EVIDENCE` |
| **7. Poisoned Knowledge Retrieval** | 150 | 75 | 75 | Unsigned/corrupted evidence $\to$ `PROVENANCE_FAILURE` |
| **8. Sensitive Data Exfiltration** | 100 | 50 | 50 | Secrets / credential probes $\to$ `DENY` / `DLP_BLOCKED` |
| **9. Excessive Agency / Tool Escalation** | 100 | 50 | 50 | Prohibited tool invocation $\to$ `CAPABILITY_DENIED` |
| **10. Unbounded Consumption** | 100 | 50 | 50 | Resource exhaustion $\to$ `RESOURCE_BUDGET_EXCEEDED` |

Each record contains: `case_id`, `language`, `attack_class`, `prompt`, `context`, `expected_policy_outcome`, `expected_action`, `allowed_evidence_ids`, `forbidden_capabilities`, and `metadata`.

---

### Phase 4: Baselines & Benchmark Harness
Implement 5 comparative baselines:
1. **Vanilla SLM**: Direct natural language generation with no guardrails.
2. **Naive RAG**: Retrieval-augmented generation without evidence verification or context firewall.
3. **Prompt-only Guardrail**: Hardened system prompt instructions without deterministic policy engine.
4. **UIR-v1**: Entity/policy/hallucination baseline.
5. **HETE UIR-v2 Security**: Full proposed Zero-Trust architecture.

Run complete evaluation and calculate comprehensive metrics:
- **ASR (Attack Success Rate)** per class and macro-average
- **PVR (Policy Violation Rate)**, **UAR (Unauthorized Action Rate)**
- **SILR (Sensitive Information Leakage Rate)**, **PEAR (Poisoned Evidence Acceptance Rate)**
- **UCR (Unsupported Claim Rate)**
- **FAR (False Accept Rate)** & **FRR (False Reject Rate)**
- **Latency & Resource overhead** with 95% Confidence Intervals & paired statistical tests.

---

### Phase 5: Ablation Studies (7 Components)
Run security benchmark with individual components disabled:
1. `-entity_verifier`
2. `-policy_engine`
3. `-context_firewall`
4. `-provenance`
5. `-capability_gate`
6. `-output_guard`
7. `-resource_guard`

Demonstrate that security improvements are strictly attributable to specific architectural mechanisms.

---

### Phase 6: Publication Reports, Documentation & Dissertation Hooks
1. `uir/docs/architecture/HETE_UIR_SECURITY_ARCHITECTURE.md`: Complete architecture specification, threat model, invariant proofs, and dissertation integration.
2. `uir/docs/evaluation/HETE_UIR_SECURITY_BENCHMARK.md`: Full experimental results, baseline comparisons, ablation tables, latency profiles, and error analysis.
3. `uir/docs/work_reports/000_uir_v2/`: All run logs, manifests, and progress milestones recorded.
4. Define common Zero-Trust Evidence Envelope connecting Network Trust $\leftrightarrow$ Process Trust $\leftrightarrow$ Data/AI Trust.

---

## 3. Verification Plan

### Automated Tests
1. **Unit & Invariant Tests (`pytest` under Ubuntu 24.04)**:
   ```bash
   wsl.exe -d Ubuntu --cd /mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/pytest uir/tests/ -v
   ```
2. **Schema & Policy Validation**:
   - Verify strict rejection of unauthorized privilege mutations in JSON schema v2.
   - Verify context firewall blocks indirect prompt injection tokens.
   - Verify output guard filters unverified claims and DLP triggers.
3. **Benchmark Execution**:
   ```bash
   wsl.exe -d Ubuntu --cd /mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/python evaluation/llm_security/run_security_benchmark.py
   wsl.exe -d Ubuntu --cd /mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/python evaluation/llm_security/run_ablation_study.py
   wsl.exe -d Ubuntu --cd /mnt/d/_Work/goat_bank/uir /mnt/d/_Work/goat_bank/.venv/bin/python evaluation/llm_security/generate_security_report.py
   ```
4. **Reproducibility & Manifest Check**:
   - Verify SHA-256 frozen test manifests, zero data leakage, and clean evaluation pipeline.
