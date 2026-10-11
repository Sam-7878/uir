# HETE UIR-ZTA V3.2A Final Reconciliation Report

Generated at 2026-09-09T03:59:10.185045+00:00 from `results/llm_security_v3_2_closure/`.

## Decision

**PASS — V3.2A final artifact/manuscript reconciliation is complete.** No model inference, held-out replay, tuning, oracle change, dataset change, or evaluated source-epoch change was performed.

| Check | Result |
|---|---:|
| Primary population | 850 = 600 attacks + 250 benign |
| Primary systems | 6 |
| Ablation configurations | 12 |
| Adaptive | 180 seeds / 3600 actual queries / B=20 |
| Adaptive collision reframes | 6 |
| Adaptive within-seed duplicate hashes | 0 |
| Stochastic seeds | 5 |
| Qwen/Phi case IDs | 850 / 850 |
| Human validation | false |
| Public AgentDojo | false |
| Frozen manifest | 736 checked / 0 failures |
| Stale claims | 0 |
| Number/manuscript mismatches | 0 |
| Final-package artifacts | 29 |

## Claim reconciliation

- The abstract reports the final Qwen outcome (MCR 0/600, E2E-ASR 0/600, complete utility 249/250, FRR 1/250) and the Phi-3.5 negative outcome (MCR 3/600, E2E-ASR 6/600, complete utility 0/250, FRR 250/250).
- UIR-v2 identifies the architecture/schema/enforcement-envelope version; Security Evaluation V3.2 identifies the experimental protocol and evidence package.
- `MCR > E2E-ASR` is retained only as a conditional observed pattern. The `-no_input_guard`, `-no_resource_guard`, and authority-chain triple-knockout results replace the stale paired-ablation statement.
- Adaptive reporting includes six campaigns, 30 seeds per campaign, 180 seeds, 3,600 actual queries, and the one excessive-agency MCR seed with zero E2E seeds.
- The containment funnel is described as overlapping case-level indicators; 176 OutputGuard rejections are not called model compromises.
- Human validation remains false. AgentDojo remains an inspired local N=5 micro-suite. CaMeL and Progent remain inspired approximations.

## Evidence preservation

The original `ARTIFACT_MANIFEST.json` was verified against all 736 registered artifacts with zero missing, size, or SHA-256 failures. This includes the frozen raw rows, datasets, source-amendment history, and operational-interruption evidence. Incomplete Ollama responses were rejected before admission; execution resumed at the missing frozen case under unchanged settings. Some rejected response bodies were not retained.

## Manuscript build

The clean `pdflatex → bibtex → pdflatex → pdflatex` build completed with all four exit codes equal to zero. The final pass has 0 undefined citations, 0 undefined references, 0 multiply defined labels, 0 missing input files, and 0 duplicate PDF destinations.

## Package boundary

`security_v3_2_final.zip` contains exactly the seven final 850-case documentation files. `HETE_UIR_ZTA_V3_2_FINAL_PACKAGE/` contains the reconciled manuscript, scoped documentation, selected frozen evidence, and this audit record. The full raw-run archive remains in the authoritative closure result and is intentionally excluded from the submission-support package.
