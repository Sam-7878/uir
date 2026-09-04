# Phase UIR-4C baseline fidelity

All model-backed conditions use the same local `microsoft/Phi-3.5-mini-instruct` snapshot, greedy decoding, seed 42, and a maximum of 128 generated tokens. The names below deliberately describe the implemented mechanisms rather than claiming reproduction of a third-party framework.

| ID | Publication-safe name | Actual mechanism |
|---|---|---|
| C0 | Direct SLM | Prompt-only Phi-3.5 generation without retrieved evidence. |
| C1 | Naive RAG | Deterministic lexical retrieval followed by Phi-3.5 generation. |
| C2 | RAG + existence check | An authoritative entity/report existence transition precedes retrieval and generation. |
| C3 | JSON-schema validated structured output | Actual model output is parsed and schema-shaped; invalid output is rejected. This is not Outlines. |
| C4 | Tool-calling agent with authoritative local tools | Phi-3.5 generates the tool name and arguments; a local deterministic tool executes them; Phi-3.5 generates the final response. |
| C5 | Guardrail-style baseline | A deterministic input rail precedes generation and an unsupported-claim output rail follows it. This is not NeMo Guardrails. |
| C6 | Corrective-retrieval baseline | Retrieval results are filtered against requested entity/attribute/period before generation. This is not a faithful CRAG implementation. |
| C7 | Graph-structured RAG baseline | Source-bound facts are represented as subject-predicate-object edges before generation. This is not Microsoft GraphRAG. |
| C8 | UIR B6 | Runtime entity/policy/UIR checks gate generation; the model selects fact references; deterministic output validation renders only immutable verified facts. |

FinQA uses official test rows. C8 asks the model for a source-bound arithmetic program and rejects a program if its operands cannot be bound to report evidence. HaluEval uses the official QA recognition task: the model judges whether a presented candidate answer contains hallucinated information.

The architecture is model-agnostic by interface design, but Phase UIR-4C empirical generation results are limited to Phi-3.5-mini-instruct.
