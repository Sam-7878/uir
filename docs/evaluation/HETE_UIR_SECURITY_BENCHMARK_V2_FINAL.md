# HETE UIR-v2 Publication Security Benchmark

## Publication gate

This report is generated from the frozen JSON evidence package. Manuscript use is allowed only when strict `results_validation.json` reports publication eligibility.

## Held-out baseline comparison

| Baseline | MCR | E2E-ASR | FRR | Benign utility | Mean latency (ms) |
|---|---:|---:|---:|---:|---:|
| Vanilla SLM | 41.79% | 41.79% | 100.00% | 0.00% | 15568.50 |
| Naive RAG | 47.50% | 46.43% | 5.00% | 95.00% | 17492.97 |
| Prompt-only Guardrail | 43.93% | 38.57% | 72.50% | 27.50% | 15953.62 |
| UIR-v1 | 7.14% | 7.14% | 27.50% | 72.50% | 6716.39 |
| HETE UIR-v2 Security | 0.00% | 0.00% | 0.00% | 100.00% | 5252.87 |

## Required final questions

1. HETE UIR-v2 MCR: **0.00%**.
2. HETE UIR-v2 E2E-ASR: **0.00%**.
3. Downstream deterministic-gate containment: **not applicable (no HETE model compromises observed)**.
4. Retained benign utility: **100.00%**.
5. FRR: **0.00%**.
6. Weakest held-out attack class by E2E-ASR: **none; every held-out attack class was 0.00%** (maximum 0.00% in run 0; all runs remain in JSON).
7. Largest measured threat-specific single-knockout effect: **-entity_verifier** (targeted ΔE2E-ASR 0.00%; targeted ΔMCR 50.00%).
8. Defense-in-depth masking is reported by the four paired knockout configurations in `heldout_multi_knockout_summary.json`.
9. KO/EN benign utility: **100.00% / 100.00%**; inferential comparisons must use the raw paired records.
10. Baseline comparisons and exact McNemar tests are shown above and in `statistical_tests.json`.
11. Valid-request mean latency and token totals are recorded per run; held-out run-0 mean is **4999.92 ms**.
12. Mean attack-class latency is **2947.67 ms** versus overall **4999.92 ms**; early-termination interpretation is limited to class-specific raw records.
13. Three-run HETE E2E-ASR spread: mean **0.00%**, population SD **0.00%**.
14. Development vs held-out HETE E2E-ASR: **0.00% / 0.00%**.
15. Residual out-of-scope risks include training-time compromise, model supply-chain compromise, hardware attacks, and threats outside the frozen taxonomy.

## Prompt-only Guardrail appendix

The exact invariant system prompt is defined by `PromptGuardBaseline.HARDENED_SYSTEM_PROMPT`; it is identical across every case and is preserved in the committed source.

## Evidence limitations

- Non-zero residual attack rates are retained and must not be hidden.
- Infrastructure failures are excluded from security verdicts and independently gate publication.
- Judge validation was `ai_assisted_manual_evidence_review` over 200 cases with 100.00% agreement. It was Codex AI-assisted evidence review; no human reviewer is claimed.
