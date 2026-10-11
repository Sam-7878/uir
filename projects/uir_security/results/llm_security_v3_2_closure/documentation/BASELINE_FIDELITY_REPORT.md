# Baseline fidelity

The full primary comparison uses six adapters on all 850 original held-out identifiers. Every adapter receives the same numeric contract and private fixture through a runtime-only evidence backend. Actual request text and options are stored with each call.

| Adapter | Actual mechanism | Limitation |
|---|---|---|
| Vanilla SLM | Direct prompt, no retrieval, unrestricted mock execution | No retrieved evidence access |
| Naive RAG | Appended retrieved content, unrestricted mock execution | No provenance admission |
| Spotlighting | Delimited data channel in one prompt | Local delimiter-based approximation; no claim of reproducing every published variant |
| Progent-inspired runtime sandbox approximation | Tool-name allow-list | No official Progent implementation |
| CaMeL-inspired capability-isolation approximation | Prompt channel labels and deterministic tool-capability membership | No official CaMeL dual-model/Python interpreter reproduction |
| HETE | Typed request pipeline, provenance, firewall, policy, capability/action checks, numeric output guard, resource accounting | Custom benchmark adapter; mock effects only |

CaMeL-inspired capabilities are actually consulted before execution. Each case resets mock state. A proposed tool name alone is not an executed effect. All tools are controlled in-memory mocks; shell_exec only appends to a mock log.

Comparative claims must name the inspired approximations. No statement that HETE outperforms official CaMeL or Progent is supported by this harness. Any sampling intervals condition on the template-generated population and do not establish external task independence.

The Spotlighting adapter implements the **delimiting** variant described by Hines et al. ([paper](https://arxiv.org/abs/2403.14720)). Retrieved text is wrapped in the literal `<<<UNTRUSTED_EXTERNAL_CONTENT_START>>>` and `<<<UNTRUSTED_EXTERNAL_CONTENT_END>>>` markers. The prompt instructs the model to treat the enclosed material as data rather than instructions; the user query is outside the markers. The system prompt reiterates the boundary. No datamarking or encoding variant is implemented, and no delimiter escaping or randomization is performed. The adapter adds no deterministic tool gate: parsed proposals go to the mock executor.

The published CaMeL mechanism is control/data-flow separation with capability checks ([Debenedetti et al.](https://arxiv.org/abs/2503.18813v2)); published Progent uses symbolic privilege rules ([Shi et al.](https://arxiv.org/abs/2504.11703v3), first published 2025 and revised 2026). Their official features must not be inferred from the much narrower local adapters. Bibliographic corrections and the removal of unsupported comparative feature assertions are recorded in the closure work log.
