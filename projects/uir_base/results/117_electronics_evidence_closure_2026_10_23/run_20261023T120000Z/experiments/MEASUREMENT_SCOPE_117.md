# Stage 117 — System Measurement Scope and Output Boundaries

**Date:** 2026-10-23  
**Status:** Canonical Measurement Scope Sealed

---

## 1. Verified Output Boundary: `CLOSED_FACT_LINES_S1`

All empirical claims regarding zero-unsupported fact displays ($0$ unsupported cases, $0$ unauthorized leaks) apply **exclusively** to the structured `CLOSED_FACT_LINES_S1` display channel:
- Output lines adhere to strict grammar: `ENTITY | METRIC | PERIOD | VALUE UNIT | source=PROVENANCE_URI`.
- The evaluation engine verified every single character and byte against the physical source file at the recorded offset.
- **Zero Hallucination:** Under this channel, $0$ unsupported claims were emitted across all 1,920 factorial outcomes and 480 primary outcomes.

---

## 2. Explicitly Unmeasured Boundary: Free-Form Native Prose

- **Status:** `NOT_MEASURED`.
- **Publication Rule:** The manuscript MUST NOT claim that UIR or generative language models generate hallucination-free free-form prose.
- Generating unconstrained conversational text introduces linguistic ambiguity and unverified stylistic flourishes that fall outside the deterministic evidence contract.

---

## 3. The Utility-Safety Trade-off

The empirical evidence demonstrates a sharp trade-off:
1. **Safety is independent of the renderer:** Both template and SLM renderers achieved $100\%$ safety ($0$ unsupported display lines) because both were subject to the same deterministic guard.
2. **Utility depends heavily on the renderer:** Delegating rendering to the SLM caused $44$ of $120$ valid, authorized answers to be lost ($36.67\%$ utility penalty).
3. **Engineering Recommendation:** For mission-critical software systems, intermediate evidence should be formatted by deterministic templating components rather than generative language models.
