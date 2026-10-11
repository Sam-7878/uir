# LAW-KR-200 Category-wise Decision Quality

Frozen test runtime SHA-256: `e728fae81590f640e52e9174a72e238d00a550870c8cb6b0178b04e60d0efc21`

| Category / correct outcome | Existence Check | Guardrail | UIR |
|---|---:|---:|---:|
| A Valid / verified answer | 8/50 (16%) | 0/50 (0%) | 50/50 (100%) |
| B Surface / verified answer | 25/50 (50%) | 8/50 (16%) | 50/50 (100%) |
| C Hard negative / safe rejection | 50/50 (100%) | 33/50 (66%) | 50/50 (100%) |
| D Mismatch / safe outcome | 19/50 (38%) | 44/50 (88%) | 50/50 (100%) |

A/B: source-bound verified answers are the correct outcome; FRR applies only here.
C: invalid FAR is accepted/50 and safe rejection is REJECT or CLARIFY/50.
D: safe outcome is REJECT, CLARIFY, or source-bound correction; this is not FRR.
Counts are recomputed from frozen raw outputs and matched exactly to the frozen scored rows.
