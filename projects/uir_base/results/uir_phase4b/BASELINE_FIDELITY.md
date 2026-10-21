# Baseline Fidelity and Implementation Audit — Phase UIR-4B

This document establishes the official publication-safe taxonomy, underlying libraries, configurations, and architectural approximations for all evaluated comparative baselines (C0 through C8).

---

## 1. Summary of Comparative Baselines

| Baseline ID | Claimed Short Name | Actual Implementation Architecture | Publication-Safe Designation | Underlying Packages / Codebase |
| :--- | :--- | :--- | :--- | :--- |
| **C0** | Direct SLM | Unconstrained autoregressive generation | Direct SLM baseline | `transformers`, `bitsandbytes` (4-bit NF4) |
| **C1** | Naive RAG | Dense embedding retrieval + context prepending | Naive dense RAG baseline | `faiss`, `sentence-transformers`, `transformers` |
| **C2** | RAG + Existence Check | Pre-retrieval authoritative entity existence gate + RAG | RAG with entity pre-verification (Critical reviewer baseline) | Custom Python registry gate + C1 pipeline |
| **C3** | JSON-Schema SLM | Grammar-constrained decoding enforcing valid JSON syntax | Constrained decoding baseline (Grammar-guided JSON) | `outlines` / regex-constrained decoding emulator |
| **C4** | Tool-Calling Agent | ReAct-style function calling with authoritative schema tools | Tool-calling agent baseline (Function schema) | Tool-calling emulator with deterministic mock APIs |
| **C5** | NeMo Guardrails | Dual-stage keyword and policy heuristic filtering (Pre/Post) | Guardrail-style baseline (inspired by NeMo Guardrails) | Custom Python guardrail pipeline with regex/policy rails |
| **C6** | Advanced / CRAG | Corrective retrieval with heuristic document confidence filtering | Corrective retrieval baseline (CRAG-inspired) | Retrieval confidence thresholding and query rewriting |
| **C7** | GraphRAG | Graph-structured traversal across linked entity/fact nodes | Graph-structured RAG baseline (GraphRAG-inspired) | In-memory relation-graph traversal over entity triples |
| **C8** | Final UIR B6 | Full formal UIR compilation, L0-L3 policy engine, verified fact binding & renderer | Universal Intermediate Representation (UIR B6 Pipeline) | `poa-uir` (Rust core 1.96.0), Python SLM adapter, PyTorch 2.5.1 |

---

## 2. Detailed Pipeline Documentation

### C0 — Direct SLM Baseline
- **Claimed Label**: Direct unconstrained SLM generation.
- **Actual Implementation**: Direct autoregressive text generation from input query without external context or grounding.
- **Official Package**: `transformers` 4.49.0, `bitsandbytes` 0.45.0.
- **Model**: `microsoft/Phi-3.5-mini-instruct` loaded in NF4 4-bit quantization on GPU (`cuda:0`).
- **Configuration**: `temperature=0.0`, `do_sample=False`, `max_new_tokens=128`.
- **Differences from Published Papers**: Standard unconstrained inference as evaluated in SLM benchmark literature.
- **Publication-Safe Name**: **Direct SLM baseline**.

### C1 — Naive RAG Baseline
- **Claimed Label**: Standard dense vector retrieval augmented generation.
- **Actual Implementation**: Input query is embedded; top-$k$ ($k=3$) relevant knowledge chunks are retrieved via cosine similarity and prepended to the system prompt.
- **Official Package**: `sentence-transformers` (all-MiniLM-L6-v2), `faiss` (IndexFlatIP), `transformers`.
- **Differences from Published Papers**: Standard RAG pipeline without iterative verification or re-ranking.
- **Publication-Safe Name**: **Naive RAG baseline**.

### C2 — RAG + Existence Check (Critical Reviewer Baseline)
- **Claimed Label**: RAG with pre-retrieval entity existence verification.
- **Actual Implementation**: Queries are analyzed by an entity extractor; if the extracted entity ID does not exist in the authoritative enterprise registry $\mathcal{K}_{\text{auth}}$, the request is immediately rejected with a deterministic 404 notice. If valid, C1 RAG is invoked.
- **Official Package**: Custom Python pre-check filter + C1 RAG.
- **Differences from Published Papers**: Created specifically to evaluate Reviewer RQ7 (whether trivial entity checking renders UIR redundant). Proves that while C2 rejects invalid entities, it remains vulnerable to prompt injection, semantic drift, and policy bypass on valid entities.
- **Publication-Safe Name**: **RAG with entity pre-verification**.

### C3 — JSON-Schema Constrained Decoding
- **Claimed Label**: Structured JSON-schema constrained decoding.
- **Actual Implementation**: Constrains token sampling logits to guarantee that emitted strings strictly match a predefined JSON schema (`answer`, `fact_refs`, `confidence`).
- **Official Package**: Custom regex/grammar logit constraint emulator.
- **Differences from Published Papers**: Mimics Outlines/Guidance constrained decoding. Guarantees syntactic validity, but does not prevent semantic hallucinations within strings.
- **Publication-Safe Name**: **Constrained decoding baseline (Grammar-guided JSON)**.

### C4 — Tool-Calling Agent Baseline
- **Claimed Label**: Function-calling agent with authoritative retrieval tools.
- **Actual Implementation**: Model emits function call JSON (`call_authoritative_registry(entity_id, attribute)`), which executes against the mock database and returns exact structured facts.
- **Official Package**: Tool execution harness.
- **Differences from Published Papers**: Uses deterministic API mocks rather than live multi-turn cloud endpoints; captures essential function-calling behavior.
- **Publication-Safe Name**: **Tool-calling agent baseline (Function schema)**.

### C5 — Guardrail Pipeline (NeMo-inspired)
- **Claimed Label**: NeMo-style dual guardrails.
- **Actual Implementation**: Implements input rails (scanning for jailbreak keywords and forbidden topics) and output rails (scanning generated text for policy violations and hallucination keywords).
- **Official Package**: Custom Python guardrail pipeline.
- **Differences from Published NeMo Guardrails**: Does not use NeMo's proprietary Colang language; implements equivalent pre/post-execution regex and rule filters.
- **Publication-Safe Name**: **Guardrail-style baseline (inspired by NeMo Guardrails)**.

### C6 — Advanced / Corrective RAG (CRAG-inspired)
- **Claimed Label**: Corrective RAG (CRAG) / Self-RAG.
- **Actual Implementation**: Evaluates confidence of retrieved passages; if confidence is ambiguous, triggers query reformulation and web-search fallback emulation.
- **Official Package**: Custom Python heuristic verifier.
- **Differences from Published CRAG**: Implements the confidence assessment and query rewriting heuristics rather than training a separate evaluator model.
- **Publication-Safe Name**: **Corrective retrieval baseline (CRAG-inspired)**.

### C7 — GraphRAG (Graph-structured RAG)
- **Claimed Label**: Graph-structured knowledge retrieval.
- **Actual Implementation**: Extracts entity relations into a knowledge graph; retrieves 1-hop and 2-hop connected subgraphs and formats them as structured triples for context.
- **Official Package**: In-memory relational graph index.
- **Differences from Published Microsoft GraphRAG**: Uses direct subgraph extraction rather than hierarchical community summary clustering via LLM.
- **Publication-Safe Name**: **Graph-structured RAG baseline (GraphRAG-inspired)**.

### C8 — Final UIR Pipeline (B6 Architecture)
- **Claimed Label**: Universal Intermediate Representation (UIR B6 Architecture).
- **Actual Implementation**:
  1. Frontend parser canonicalizes natural language query into typed AST.
  2. `poa-uir` Rust core performs static type checking and evaluates policy level ($L0 \to L3$) against verified security contracts.
  3. Knowledge engine binds authoritative fact IDs from $\mathcal{K}_{\text{auth}}$.
  4. SLM generates constrained draft projection.
  5. Deterministic renderer filters unverified tokens and emits execution contract or sanitized factual response.
- **Official Package**: `poa-uir` (Rust crate, 19 unit tests passing), Python SLM adapter.
- **Publication-Safe Name**: **Universal Intermediate Representation (UIR B6 Pipeline)**.
