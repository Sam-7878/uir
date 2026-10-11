# HETE UIR-ZTA V3.2A Final Artifact & Manuscript Reconciliation Work Order

**Project:** HETE UIR-ZTA / Zero-Trust Language-Model Execution  
**Parent:** `HETE_UIR_ZTA_V3_2_FINAL_SCIENTIFIC_VALIDITY_CLOSURE_WORK_ORDER.md`  
**Scope:** Final documentation/package/manuscript reconciliation only  
**Experimental status:** **V3.2 SCIENTIFIC EVIDENCE CLOSURE PASSED**  
**New inference required:** **NO**  
**New architecture development required:** **NO**  
**Submission status:** **HOLD until the reconciliation gate below passes**

---

## 0. Executive Decision

The V3.2 experimental closure is substantially successful.

The authoritative result package shows:

- all 850 held-out cases executed for each of six primary systems;
- 250 benign + 600 attack cases;
- 12 HETE ablation configurations × 850 cases;
- identical 850-case HETE evaluation on Qwen2.5-7B and Phi-3.5;
- 180 adaptive seeds and 3,600 actual adaptive queries;
- 5 stochastic seeds;
- exact paired McNemar tests;
- raw-record validation and cryptographic artifact hashes;
- no admitted fallback/incomplete model response;
- `publication_evidence_valid=true`;
- `scientific_integrity_failures=[]`.

Therefore, **do not initiate another V3.3 experiment merely to improve numbers**.

However, the uploaded package still contains stale documentation and manuscript statements that do not match the final V3.2 evidence. The remaining task is to make **one canonical submission package** whose report, manuscript, tables, artifact ZIPs, and claims all agree with the frozen evidence.

The scientific rule for this work order is:

> **No final held-out result may be rerun, tuned, replaced, or cherry-picked. Only documentation, packaging, manuscript wording, and evidence binding may change unless a genuine integrity defect is discovered.**

---

# 1. Authoritative Source of Truth

For this reconciliation, treat the following final V3.2 evidence as authoritative:

```text
results/llm_security_v3_2_closure/
    publication_evidence_validation.json
    baseline_comparison.json
    per_class_results.json
    ablation_results.json
    adaptive_attack_results.json
    stochastic_results.json
    multi_model_results.json
    statistical_tests.json
    containment_funnel.json
    containment_funnel_cases.jsonl
    ARTIFACT_MANIFEST.json
    raw_runs/
    documentation/
```

The final closure counts are:

```text
Primary population:
  850 cases = 600 attacks + 250 benign

Primary systems:
  6 systems × 850 cases

Ablations:
  12 configurations × 850 cases

Adaptive:
  6 campaigns × 30 seeds = 180 seeds
  B = 20
  3,600 actual queries total

Stochastic:
  5 seeds
  30 frozen cases/seed
  150 rows total

Multi-model:
  Qwen2.5-7B: same 850 IDs
  Phi-3.5:     same 850 IDs
```

Do not treat older `N=120`, `N=240`, `30 adaptive seeds`, `600 adaptive queries`, or `9 ablations` as final V3.2 evidence.

---

# 2. P0 — Preserve the Frozen Experimental Evidence

Do not edit:

```text
raw publication JSONL
frozen runtime/oracle datasets
model outputs
oracle verdicts
HETE/baseline evaluated source epochs
campaign protocol
source amendment history
operational-failure history
```

Preserve all documented interrupted-backend events.

The final report/manuscript should explicitly retain the limitation:

> Incomplete Ollama responses were rejected before admission; the campaign resumed from the missing frozen case without changing the model, dataset, policy, or outcome criteria. Some rejected response bodies were not retained.

Do not rewrite this history as “zero operational failures.”

---

# 3. P1 — Replace the Stale `security_v3_2.zip`

## Current problem

The uploaded `security_v3_2.zip` is not synchronized with the authoritative final result package.

Its documents still contain examples such as:

```text
N = 240 primary
30 adaptive seeds
up to 600 adaptive queries
9 ablation configurations
older utility/result values
```

while the authoritative closure contains:

```text
N = 850 primary
180 adaptive seeds
3,600 queries
12 ablation configurations
```

## Required repair

Regenerate:

```text
security_v3_2_final.zip
```

**only from the final documentation stored with the authoritative result package.**

The canonical documentation ZIP should include:

```text
HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md
ADAPTIVE_ATTACK_PROTOCOL.md
AGENTDOJO_PROVENANCE.md
BASELINE_FIDELITY_REPORT.md
HUMAN_REVIEW_PROTOCOL.md
OUTPUT_GUARD_VALIDATION_REPORT.md
README_REPRODUCE.md
```

All of these files must be the final 850-case versions.

## Mandatory stale-string rejection

Fail packaging if any canonical final document contains obsolete claims such as:

```text
N=240
N = 240
30 adaptive seeds
600 adaptive queries
9 ablation configurations
18.3% adaptive MCR             # if from obsolete run
88.3% complete utility         # if from obsolete run
```

unless clearly labeled as archived historical evidence.

---

# 4. P2 — Keep the Scope Corrections from V3.2

The following V3.2 scope decisions are correct and must remain:

### Human validation

```text
human_validation = false
```

No human Cohen's kappa, dual-rater, expert-adjudication, or human-validation result may be claimed.

### AgentDojo

The existing local test is:

```text
AgentDojo-inspired micro-suite, N=5
```

It is **not** an actual public AgentDojo execution.

Do not state:

```text
public AgentDojo benchmark result
HETE outperforms AgentDojo baselines
```

### CaMeL / Progent

Always use:

```text
CaMeL-inspired capability-isolation approximation
Progent-inspired runtime-sandbox approximation
```

Do not shorten these to official `CaMeL` / `Progent` in empirical superiority claims.

---

# 5. P3 — Correct the Main Manuscript's Stale Ablation Statement

## Current stale statement

The full manuscript contains a statement equivalent to:

> meaningful failure appeared when `Context Firewall + OutputGuard` and `Entity Verifier + OutputGuard` were jointly removed.

Those combinations are not the final V3.2 paired ablations reported by the authoritative result package.

## Replace it with actual V3.2 evidence

Use the real findings:

### A. Model/system decoupling

```text
-no_input_guard:
  MCR = 4/600 = 0.67%
  E2E-ASR = 0/600
```

This is the cleanest empirical example of:

```text
model compromise without system compromise
```

### B. Resource-control contribution

```text
-no_resource_guard:
  E2E-ASR = 20/600 = 3.33%
```

This demonstrates that the resource layer is not redundant under the tested resource threat class.

### C. Authority-chain multi-knockout

```text
-no_capability_gate
-no_policy
-no_action_revalidation:
  MCR = 8/600 = 1.33%
  E2E-ASR = 7/600 = 1.17%
```

This is the strongest multi-control evidence that authority-chain controls jointly prevent state-changing agency attacks.

### D. Masked controls

The following individual removals should be interpreted as defense masking / redundancy under this finite distribution, not as proof that the components are unnecessary:

```text
-no_capability_gate
-no_output_guard
-no_context_firewall
-no_provenance
```

---

# 6. P4 — Reframe `MCR > E2E-ASR` as a Conditional Containment Observation

## Current problem

The manuscript labels the contribution as:

```text
Architectural Containment Thesis (MCR > E2E-ASR)
```

A strict universal inequality is too strong.

Reasons:

1. Full Qwen HETE has:
   ```text
   MCR = 0
   E2E = 0
   ```
   so strict `>` does not hold.

2. Resource exhaustion can produce a system-level resource violation without satisfying the behavioral MCR definition used for prompt/model compromise.

## Required wording

Preferred contribution label:

> **MCR–E2E Decoupling and System-Level Containment**

Define:

> For model-mediated attack paths, downstream enforcement is evidenced when observed E2E-ASR is lower than MCR. More generally, MCR and E2E-ASR are intentionally disaggregated because model behavior and trusted system effects are distinct security events.

Keep:

```text
MCR > E2E-ASR
```

only as an **observed pattern in specific configurations**, such as `-no_input_guard`, not as a universal theorem.

---

# 7. P5 — Strengthen the Abstract with the Actual Final Results

## Current issue

The abstract describes the protocol but does not state the most important final empirical outcomes.

## Required abstract content

Include the primary Qwen result:

```text
HETE/Qwen:
MCR       = 0/600
E2E-ASR   = 0/600
Complete task utility = 249/250 = 99.6%
FRR       = 1/250 = 0.4%
```

Also include the critical negative multi-model result:

```text
HETE/Phi-3.5:
MCR       = 3/600 = 0.5%
E2E-ASR   = 6/600 = 1.0%
Complete task utility = 0/250
FRR       = 250/250
```

The Phi result must not be hidden.

It supports a more nuanced conclusion:

> The enforcement placement is model-independent, but successful contract-following and benign task utility are not backbone-independent.

This substantially strengthens scientific credibility.

---

# 8. P6 — Add a Clear UIR-Version vs Evaluation-Version Statement

To avoid reviewer confusion, define near the beginning of Methodology:

```text
UIR-v2
    = architecture / typed schema / enforcement-envelope version

Security Evaluation V3.2
    = experimental protocol / benchmark / evidence package version
```

Do not imply that V3.2 is a new UIR representation format unless it actually is.

Preferred wording:

> We retain the UIR-v2 security representation and evaluate it under the V3.2 scientific-validity protocol.

---

# 9. P7 — Update the Conclusion to Reflect Completed Closure

## Current stale sentence in `v3_2_evidence.tex`

The current conclusion says, in effect:

> Final submission requires the scientific-validity gate, artifact/manuscript audit, and clean LaTeX/BibTeX build.

Those conditions have already been completed according to the final closure.

## Required replacement

Use a completed, scoped conclusion such as:

> The V3.2 evidence package passed the strict raw-evidence validity gate, artifact binding audit, full test suite, and clean LaTeX/BibTeX build. Within the frozen custom benchmark and two local model backbones, the results support the claim that deterministic authority enforcement can prevent compromised or adversarial model behavior from automatically becoming a trusted system effect. The evidence does not establish universal security, official CaMeL/Progent superiority, human-validated judge accuracy, or public AgentDojo generalization.

Do not state or imply formal proof of universal attack resistance.

---

# 10. P8 — Make the Phi-3.5 Negative Result a First-Class Limitation

The identical-case multi-model experiment is particularly valuable because it did **not** produce uniformly favorable results.

Add a Discussion/Limitations paragraph explaining:

```text
Qwen2.5:
  249/250 complete benign utility

Phi-3.5:
  0/250 complete benign utility
  250/250 structured-contract failures/rejections
  3/600 MCR
  6/600 E2E
```

Interpretation:

- the deterministic envelope is not itself enough to guarantee semantic/format competence;
- model capability and structured-output reliability still matter;
- “model-agnostic architecture” must not be conflated with “model-independent performance”;
- fail-closed enforcement can preserve safety while destroying utility on a weak/incompatible backbone.

This is a strong and publishable negative result.

---

# 11. P9 — Keep Adaptive Claims Numerically Precise

The final adaptive experiment is:

```text
6 campaigns
30 seeds/campaign
180 seeds
20-query budget
3,600 actual queries
6 collision reframes
0 duplicate candidate hashes
```

Final observed seed outcomes include:

```text
Excessive agency:
  1/30 seeds with MCR
  0/30 with E2E success

Other five campaigns:
  0 MCR seeds
  0 E2E seeds
```

Do not summarize this as merely:

```text
0/6 campaign breaches
```

because that hides the actual experiment scale and the single model-compromise seed.

Report both:

```text
campaign-level summary
seed-level counts
```

---

# 12. P10 — Preserve the Exact Statistical Method

The final statistics use:

```text
exact two-sided binomial McNemar
family-wise alpha = 0.05
Holm correction
Wilson intervals
```

Keep scientific notation for small p-values.

Examples from the final package include:

```text
Vanilla vs HETE:      p ≈ 3.16e-30
Naive RAG vs HETE:    p ≈ 3.42e-49
Spotlighting vs HETE: p ≈ 7.17e-43
```

Do not reintroduce:

```text
continuity-corrected chi-square labeled as exact
p = 0.0
alpha = 0.01 without explanation
```

---

# 13. P11 — Preserve the Correct Containment-Funnel Semantics

The final funnel is an **overlapping-indicator view**, not a sequential subtraction pipeline.

Authoritative counts:

```text
attack_attempted             = 600
llm_invoked                  = 363
suspicious_output            = 0
behavioral_mcr_satisfied     = 0
output_guard_rejected        = 176
action_gate_rejected         = 68
trusted_effect_committed     = 0
```

Do not call all 176 OutputGuard rejections “model compromises.”

Use the case-level funnel artifact to support each stage.

---

# 14. P12 — Reconcile the Final Report, Evidence Include, and Main `.tex`

Create one canonical number source:

```text
results/llm_security_v3_2_closure/
```

Then verify the following three manuscript/report surfaces against it:

```text
HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md
v3_2_evidence.tex
_47.1_UIR_ZTA.tex
```

No manually copied number is accepted without a trace to a frozen JSON/CSV field.

Recommended approach:

```text
render_v3_2_evidence.py
render_v3_2_report.py
```

to generate tables/paragraph constants from JSON.

---

# 15. P13 — Canonical Final Package Layout

Produce a single final submission-support package:

```text
HETE_UIR_ZTA_V3_2_FINAL_PACKAGE/
    manuscript/
        _47.1_UIR_ZTA.tex
        v3_2_evidence.tex
        references.bib
        _47.1_UIR_ZTA.pdf

    documentation/
        HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md
        BASELINE_FIDELITY_REPORT.md
        ADAPTIVE_ATTACK_PROTOCOL.md
        HUMAN_REVIEW_PROTOCOL.md
        AGENTDOJO_PROVENANCE.md
        OUTPUT_GUARD_VALIDATION_REPORT.md
        README_REPRODUCE.md

    evidence/
        publication_evidence_validation.json
        ARTIFACT_MANIFEST.json
        baseline_comparison.json
        per_class_results.json
        ablation_results.json
        multi_model_results.json
        adaptive_attack_results.json
        stochastic_results.json
        statistical_tests.json
        containment_funnel.json
        containment_funnel_cases.jsonl
        operational_interruption_summary.json

    audit/
        FINAL_RECONCILIATION_REPORT.md
        stale_claim_scan.txt
        manuscript_build.log
```

The full raw-run archive may be a separate supplementary ZIP if size requires it.

---

# 16. P14 — Automated Stale-Claim Scanner

Create:

```text
docs/security_v3_2/audit/check_final_claims.py
```

It should fail if current submission files contain obsolete publication claims.

At minimum scan for:

```text
N=120
N = 120
N=240
N = 240
90 attacks
30 benign            # when referring to primary final population
30 adaptive seeds
600 adaptive queries
9 ablation
18.3%                # obsolete adaptive result
88.3%                # obsolete utility result
dual-blinded human
Cohen's kappa        # as an observed V3.2 human result
public AgentDojo benchmark
HETE outperforms CaMeL
HETE outperforms Progent
Context Firewall + OutputGuard    # as observed final paired ablation
Entity Verifier + OutputGuard     # as observed final paired ablation
Final submission requires the scientific-validity gate
```

Allow occurrences only if explicitly labeled:

```text
historical / archived / prior V3.1
```

---

# 17. P15 — Final Build and Cross-Reference Audit

Run:

```bash
pdflatex
bibtex
pdflatex
pdflatex
```

Required:

```text
0 undefined citations
0 undefined references
0 multiply-defined labels affecting final output
0 missing input files
0 stale V3.1 result references
```

Also inspect:

```text
Appendix ordering
table captions
figure captions
dataset denominators
baseline approximation labels
```

Follow the target journal's appendix/bibliography ordering when known.

---

# 18. P16 — Independent Number Reconciliation

Create a final machine-readable audit:

```json
{
  "primary_n": 850,
  "attack_n": 600,
  "benign_n": 250,
  "systems_n": 6,
  "ablation_configs": 12,
  "adaptive_seeds": 180,
  "adaptive_queries": 3600,
  "qwen_case_ids": 850,
  "phi_case_ids": 850,
  "human_validation": false,
  "public_agentdojo": false,
  "raw_manifest_hash_failures": 0,
  "manuscript_mismatches": 0
}
```

The reconciliation must compare:

```text
raw JSONL
summary JSON
report markdown
LaTeX tables/text
```

and fail on any disagreement.

---

# 19. Final Acceptance Criteria

This V3.2A reconciliation is complete only when:

- [ ] No new inference was performed.
- [ ] Frozen raw V3.2 evidence is unchanged.
- [ ] `security_v3_2_final.zip` contains only final 850-case documentation.
- [ ] No stale `N=240` primary claims remain.
- [ ] No stale `30-seed / 600-query` adaptive claims remain.
- [ ] No stale `9-ablation` claim remains.
- [ ] Human validation remains explicitly false.
- [ ] AgentDojo remains explicitly an inspired N=5 micro-suite.
- [ ] CaMeL/Progent remain labeled inspired approximations.
- [ ] The stale ContextFirewall+OutputGuard / EntityVerifier+OutputGuard ablation sentence is removed.
- [ ] Actual `-no_input_guard`, `-no_resource_guard`, and authority-chain multi-knockout results are used.
- [ ] `MCR > E2E-ASR` is not presented as a universal theorem.
- [ ] Abstract reports the key Qwen result.
- [ ] Abstract/Discussion disclose the Phi negative result.
- [ ] UIR-v2 architecture vs V3.2 evaluation version is defined.
- [ ] Conclusion says the closure gate already passed.
- [ ] Exact statistics remain exact and use scientific notation.
- [ ] Adaptive results use 180 seeds / 3,600 queries.
- [ ] Containment funnel is described as overlapping indicators.
- [ ] All final report/manuscript numbers are generated or checked against frozen JSON.
- [ ] Artifact hashes all pass.
- [ ] LaTeX/BibTeX build is clean.
- [ ] `FINAL_RECONCILIATION_REPORT.md` reports zero stale-claim and number mismatches.

---

# 20. Stop Rule

Once the V3.2A reconciliation gate passes:

```text
DO NOT create V3.3 just to improve results.
DO NOT rerun the final held-out set.
DO NOT tune HETE against final failures.
```

The next step is:

```text
independent manuscript review
→ journal formatting
→ submission
```

Additional experiments should be started only if:

1. an external reviewer specifically requires an official public benchmark or real human annotation;
2. a genuine integrity defect is found in the frozen evidence;
3. the target venue requires an additional baseline.

Otherwise, the V3.2 scientific evidence should remain frozen.

---

## Final Publication Positioning

The final paper should make the following scoped claim:

> HETE's typed UIR and deterministic enforcement envelope separate language-model behavior from trusted execution authority. On the frozen 850-case custom benchmark, the Qwen2.5-backed HETE configuration observed no model- or end-to-end attack successes while completing 249/250 benign tasks; full-population ablations show both defense masking and cases in which removing resource or authority-chain controls reintroduces system-level failures. The identical-case Phi-3.5 result demonstrates that the enforcement architecture does not guarantee backbone-independent utility, reinforcing the distinction between security containment and semantic/contract competence.

This is a stronger and more defensible paper than a universal “0% attack / 100% utility” claim.
