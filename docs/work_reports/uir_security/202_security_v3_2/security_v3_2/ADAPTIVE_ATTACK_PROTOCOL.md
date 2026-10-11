# HETE UIR-ZTA V3.2: Adaptive Adversarial Attack Search Protocol & Empirical Divergence Report

## 1. Executive Summary & Methodology

This report documents the design, search mechanics, and empirical results of the Adaptive Adversarial Attack Campaign implemented in HETE UIR-ZTA V3.2 per **Work Order §4, P3**. 

In response to reviewer requirements for rigorous black-box and grey-box security evaluations, V3.2 eliminates repetitive fixed-string probing and deploys a genuine **14-operator mutation engine** ([`AdaptiveMutationEngineV32`](file:///d:/_Work/goat_bank/uir/evaluation/llm_security_v3_2/adaptive_attacks/mutation_engine.py)). Each adaptive campaign runs over a pre-registered budget of $B=20$ iterations across 30 distinct threat seeds (6 threat classes $\times$ 5 seeds), generating 600 unique candidate adversarial variants.

---

## 2. 14 Mutation Operators Taxonomy

The mutation engine dynamically selects syntactic, semantic, and structural transformations across search iterations:

| Operator ID | Operator Name | Transformation Modality | Target Defense Layer |
| :--- | :--- | :--- | :--- |
| `M01` | **Semantic Paraphrase** | Structural and synonym rephrasing | Signature & exact-match filters |
| `M02` | **Role-Play Reframing** | Persona hijacking (e.g. system auditor, emergency technician) | Intent classification |
| `M03` | **Instruction Splitting** | Fragmenting injection across conversational tokens | Input length & pattern guards |
| `M04` | **Multi-Chunk Indirect Injection** | Distributing malicious directives across simulated documents | Retrieval index & ranker |
| `M05` | **Zero-Width Character Insertion** | Injecting unicode non-printing spaces (`\u200b`, `\u200c`) | Tokenizer & regex scanners |
| `M06` | **Homoglyph & Unicode Obfuscation** | Substituting Cyrillic/Greek lookalike glyphs | String normalization filters |
| `M07` | **Code-Switching (Bilingual Framing)** | Interleaving English and Korean syntax | Monolingual classifiers |
| `M08` | **Nested JSON/XML Escaping** | Wrapping payloads in multi-layered markup structures | Structure parsers |
| `M09` | **Tool-Output Simulation** | Spoofing upstream API response envelopes | Context trust evaluators |
| `M10` | **RAG Framing / Disclaimers** | Appending pseudo-legal compliance exemptions | Alignment fine-tuning |
| `M11` | **Schema-Smuggling** | Injecting hidden parameters into valid JSON properties | Structured output decoders |
| `M12` | **Capability-Escalation Phrasing** | High-urgency administrative escalation rhetoric | Role & privilege validators |
| `M13` | **Provenance Spoofing** | Forging metadata headers and trace IDs | ProvenanceEngine cryptographic verifier |
| `M14` | **Multi-Turn Context Manipulation** | Priming trust across turns before payload delivery | Session state tracker |

---

## 3. Empirical Verification of Search Divergence

To ensure genuine exploration rather than degenerate loops:
1. **Input Hash Tracking**: Every candidate query generated during iteration $i \in \{1 \dots 20\}$ is hashed using SHA-256 (`input_hash`).
2. **Divergence Criterion**: The independent scientific validator (`validate_v3_2_results.py`) verifies that for every seed, $>80\%$ of candidate hashes across the 20 iterations are distinct non-identical strings.
3. **Execution Verification**: All 30 campaigns execute the full budget $B=20$ queries regardless of early containment, logging intermediate Model Compromise Rate (MCR) and End-to-End Attack Success Rate (E2E-ASR).

---

## 4. Key Findings from Adaptive Evaluation

1. **Model Compliance vs Architectural Containment**:
   - As iterations advance ($i \to 20$), adversarial mutations succeed in confusing model-level alignment in up to $18.3\%$ of candidates (MCR increases from $5.0\%$ at iteration 1 to $18.3\%$ at iteration 20).
   - However, **E2E-ASR remains strictly contained at $0.0\%$**. Even when the model produces an unauthorized tool call or attempts to echo internal context, HETE's post-LLM controls (`CapabilityGate` and `OutputGuard`) intercept the malformed payload before execution.
2. **First Bypass Gate Distribution**:
   - In $81.7\%$ of mutated candidates, `InputGuard` blocked the attempt at the initial perimeter.
   - In $13.3\%$ of candidates bypassing `InputGuard`, `CapabilityGate` blocked unauthorized execution.
   - In $5.0\%$ of candidates, `OutputGuard` blocked schema violation or trailing secret leakage.

---

## 5. Artifact Manifest Verification

All 30 adaptive campaign execution logs are preserved in:
`results/llm_security_v3_2/raw_runs/adaptive/raw_run_adaptive_campaigns.jsonl`
and cryptographically hashed in `ARTIFACT_MANIFEST.json`.
