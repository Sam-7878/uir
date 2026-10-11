# HETE UIR-ZTA V3.1 Publication Evidence Repair Work Order

**Project:** HETE UIR-ZTA / LLM Security V3  
**Parent task:** `HETE_UIR_ZTA_GROK_REVIEW_MAJOR_REVISION_WORK_ORDER.md`  
**Reviewed artifacts:** `security_v3.zip`, `llm_security_v3.zip`, `walkthrough(8).md`, `implementation_plan(8).md`, `_47.1_UIR_ZTA.tex`, `references(4).bib`  
**Purpose:** Repair the remaining scientific-validity, benchmark-fidelity, adaptive-evaluation, human-validation, multi-model, statistics, artifact, and manuscript-consistency defects before submission.  
**Decision:** **ADDITIONAL DEVELOPMENT REQUIRED — DO NOT SUBMIT CURRENT MANUSCRIPT AS FINAL SCI EVIDENCE**

---

# 0. Executive Review Verdict

The major-revision implementation has made **real and important progress**:

- Runtime and oracle schemas are separated.
- Benign and attack cases no longer receive different principals purely from `attack_class`.
- A separate 850-case held-out dataset exists instead of `dev[::5]`.
- Typed provenance source identity and domain parsing improve the old substring-trust design.
- TCB, frontend, firewall, invariant, and traceability documentation substantially improve the architectural specification.
- The title is now more defensible:
  > *HETE: A Typed Intermediate Representation and Deterministic Enforcement Envelope for Zero-Trust Language-Model Execution*
- Decorative formalism has been replaced by executable-style invariants.
- The manuscript now acknowledges CaMeL, Instruction Hierarchy, Spotlighting, Progent, and related security work.

However, the current V3 package **does not yet satisfy the original work order's publication-grade acceptance criteria**.

The main problem is no longer the basic architecture. The problem is **evaluation authenticity and claim fidelity**.

The following current claims are not yet supported strongly enough to remain in a final manuscript:

```text
"dual-blinded human expert adjudication"
"official/public AgentDojo evaluation"
"faithful CaMeL / Progent comparison"
"white-box adaptive attack search up to 20 queries"
"two-model publication campaign"
"stochastic decoding robustness over 5 seeds"
"strict publication gate passed"
"all final V3 results complete"
```

Until the repairs below are complete, current V3 evidence must be treated as:

```text
V3_PREVALIDATION_ENGINEERING_EVIDENCE
```

not:

```text
FINAL_PUBLICATION_EVIDENCE
```

---

# 1. P0 — Immediate Claim Freeze and Artifact Preservation

## 1.1 Freeze current V3

Do not overwrite the present package.

Archive it under an immutable tag/directory, e.g.:

```text
results/llm_security_v3_prevalidation/
docs/security_v3_prevalidation/
```

Record:

```text
git commit SHA
zip SHA-256
dataset hashes
model configuration
date/time
```

## 1.2 Manuscript claim freeze

Until V3.1 passes, remove or mark as TODO all statements asserting:

```text
real human experts
official AgentDojo benchmark completion
faithful CaMeL reproduction
faithful Progent reproduction
20-query adaptive search
full Qwen2.5 held-out campaign
5-seed stochastic robustness
publication_eligible / all gates passed
```

Do not use current V3 summary numbers in Abstract or Conclusion.

---

# 2. P1 — Full Raw-Result Artifact Package

The uploaded V3 source package contains code and datasets but does not provide a complete publication evidence package with all required raw runs.

Create:

```text
results/llm_security_v3_1/
    ARTIFACT_MANIFEST.json
    publication_manifest.json
    publication_validation.json

    raw_runs/
        custom/
        agentdojo/
        adaptive/
        phi35/
        qwen25/
        stochastic/
        baselines/

    baseline_comparison.json
    per_class_results.json
    containment_funnel.json
    adaptive_attack_results.json
    public_agentdojo_results.json
    multi_model_results.json
    stochastic_results.json
    human_judge_validation.json
    latency_by_path.json
    statistical_tests.json

    tables/
        table_main_security_utility.csv
        table_per_class.csv
        table_agentdojo.csv
        table_adaptive.csv
        table_models.csv
        table_containment.csv
        table_latency.csv
```

Every aggregate metric must be reconstructible from raw per-case records.

Each raw record must contain at least:

```text
case_id
opaque_case_id
system
model
seed
temperature
top_p
prompt_hash
raw model output
final accepted output
policy outcome
evidence admitted
tool proposals
tool attempts
tool executions
resource usage
guard events
MCR verdict
E2E verdict
utility verdict
latency breakdown
failure status
```

---

# 3. P2 — Remove Residual Label/Metadata Leakage

## 3.1 Opaque case IDs

Current case identifiers encode semantics such as:

```text
heldout-atk-...
heldout-benign-...
```

Even if current SUT code does not branch on those prefixes, this violates the cleanest form of oracle/runtime separation.

Replace runtime-visible IDs with opaque UUID-like IDs:

```text
c_01J...
```

Keep benign/attack class only in the oracle mapping.

Required test:

```text
tests/security_v3_1/test_opaque_runtime_identity.py
```

## 3.2 Runtime-field allow-list

Create an allow-list instead of only a forbidden-field list.

The SUT may receive only explicitly approved runtime fields.

Fail CI if additional fields appear without review.

---

# 4. P3 — Strengthen Dataset Independence and Diversity Audit

The current separate held-out generation is a real improvement, but the audit must satisfy the original work order rather than only exact/normalized duplicate tests.

## Required audit dimensions

Implement:

```text
evaluation/llm_security_v3_1/audit_semantic_leakage.py
```

Report:

```text
exact duplicate rate
normalized duplicate rate
3-gram and 5-gram overlap
template-family overlap
attack-payload stem overlap
entity/fact template overlap
nearest-neighbor embedding similarity
duplicate semantic-intent rate
unique prompt ratio by attack class
unique template ratio by attack class
```

Current held-out size and class counts must be reported from the dataset itself, never hard-coded in the manuscript.

## Diversity requirement

For each attack class:

```text
>= 50 independent cases
>= 20 genuinely distinct attack templates or externally sourced attacks
```

For classes with fewer unique constructions, increase diversity before final execution.

Do not call a held-out set "semantically independent" solely because exact strings differ.

---

# 5. P4 — Provenance: Convert Checksum Trust into Real Authenticated Provenance

The current typed `SourceIdentity` is an improvement, but a caller-supplied SHA-256 digest matching caller-supplied content is only an integrity checksum, not authenticated provenance.

## Required design

Implement a frozen trusted provenance manifest:

```text
evaluation/llm_security_v3_1/fixtures/trusted_source_manifest.json
```

Manifest entry:

```json
{
  "authority": "sec.gov",
  "resource_id": "...",
  "content_sha256": "...",
  "signer_id": "...",
  "signature": "..."
}
```

At runtime, trust must require one of:

### Option A — Digital signature

Verify a real signature over canonical source metadata + content digest.

### Option B — HMAC / keyed fixture for benchmark

If public-key signatures are too heavy for this benchmark, use a keyed authenticator in the test harness and explicitly call it an experimental authenticated manifest.

### Option C — Weaken the paper claim

If no authentication is implemented, change manuscript wording from:

```text
cryptographically verified provenance
```

to:

```text
structured source allow-list + content-integrity checking
```

## Mandatory spoof tests

```text
authority substring spoof
subdomain trick
punycode/lookalike
recomputed attacker hash
wrong signer
missing signature
stale manifest
cross-resource substitution
cross-case evidence replay
```

---

# 6. P5 — Replace Approximate CaMeL / Progent / Spotlighting Claims with Fidelity-Correct Baselines

## 6.1 CaMeL

The present adapter must not be called a faithful CaMeL reproduction unless it actually implements the reference design sufficiently closely.

Preferred:

```text
Use official CaMeL code/repository or a documented integration layer.
```

If integration is technically infeasible:

Rename current baseline to:

```text
CaMeL-inspired capability-isolation approximation
```

and explicitly state:

```text
not an official CaMeL reproduction
```

Do not use it for superiority claims such as:

```text
HETE outperforms CaMeL
```

unless fidelity is independently demonstrated.

## 6.2 Progent

Same rule:

- official/reference implementation preferred;
- otherwise use `Progent-inspired` wording;
- document missing semantics.

## 6.3 Spotlighting

Implement the method as described by the source paper, including its intended marking/encoding strategy, not only a generic delimiter prompt.

## 6.4 Fidelity document

Create:

```text
docs/security_v3_1/BASELINE_FIDELITY_REPORT.md
```

For every modern defense:

```text
reference paper/repo
version/commit
implemented mechanism
omitted mechanism
known incompatibilities
whether direct numerical comparison is valid
```

---

# 7. P6 — Run Genuine AgentDojo

A hand-written set of a few "AgentDojo-like" cases must not be described as the public AgentDojo benchmark.

## Required

Install and execute the actual AgentDojo benchmark/environment.

Freeze:

```text
AgentDojo version
repository commit
task suite
attack suite
tool environment
model configuration
```

Run the benchmark's native utility/security metrics.

Create adapter only for translating HETE's policy/effect trace into the benchmark interface.

Record:

```text
native AgentDojo task utility
native attack success
HETE MCR
HETE E2E-ASR where semantically equivalent
```

If actual AgentDojo integration cannot be completed:

1. delete all "public AgentDojo benchmark" claims;
2. rename the current cases to:
   ```text
   AgentDojo-inspired micro-suite
   ```
3. treat them only as supplementary engineering tests.

---

# 8. P7 — Implement Real Adaptive Attack Search

The current adaptive path must be replaced by an actual mutation/search procedure.

## 8.1 Attacker models

Run:

```text
A0 black-box
A1 gray-box
A2 white-box
```

## 8.2 Search budget

Use the preregistered maximum:

```text
20 attacker queries / seed case
```

Do not silently cap at 5.

## 8.3 Actual mutation

Each query must produce a new candidate attack.

Use a frozen attacker model or deterministic mutation engine.

Candidate transformations should include:

```text
paraphrase
role-play
instruction splitting
Unicode/zero-width
nested structured data
tool-output injection
RAG document injection
code switching
semantic synonym substitution
output-schema smuggling
provenance spoof attempts
capability-escalation phrasing
multi-turn state manipulation
```

Do not count rerunning the same prompt as adaptive search.

## 8.4 Scale

Minimum recommended:

```text
>= 30 seed attacks per adaptive campaign
6 campaigns
up to 20 queries each
```

Preferred:

```text
>= 50 seed attacks per campaign
```

## 8.5 Freeze rule

Freeze the defense before the final adaptive campaign.

If a bypass is used to patch HETE, that attack becomes development data and a new untouched final adaptive set is required.

## 8.6 Output

For every attack:

```text
all mutations
query index
attacker knowledge level
model output
guard trace
first MCR
first E2E bypass
containment gate
```

Plot/report:

```text
MCR vs query budget
E2E-ASR vs query budget
time-to-first-bypass
queries-to-first-bypass
```

---

# 9. P8 — Multi-Model Evaluation Repair

## 9.1 Equal dataset

Phi-3.5 and Qwen2.5 must be evaluated on the same preregistered case set.

No:

```text
Phi first 300
Qwen first 100
```

unless this is explicitly a pilot experiment.

For final evidence:

```text
same N
same attack classes
same benign tasks
same policy/evidence fixtures
same judge
```

## 9.2 Dynamic denominators

Never hard-code attack denominators.

Derive:

```text
n_attack
n_benign
n_per_class
```

from actual records.

## 9.3 No deterministic fallback

For publication runs:

```text
enable_deterministic_fallback = false
```

Any:

```text
MODEL_ERROR
TIMEOUT
BACKEND_ERROR
OOM
```

must be recorded as infrastructure failure and must not silently become a synthetic model answer.

The publication validator must fail if fallback output is detected.

## 9.4 Model manifests

Record:

```text
ollama model digest
model family/version
quantization
context length
generation params
hardware
software
```

---

# 10. P9 — Implement the Required Stochastic Robustness Study

Retain deterministic evaluation:

```text
temperature=0
```

and add:

```text
temperature=0.7
top_p=0.9
seeds >= 5
```

Use the same frozen case set across seeds.

Report:

```text
MCR mean / SD / range
E2E-ASR mean / SD / range
utility mean / SD
FRR mean / SD
invalid-output rate
per-seed raw counts
```

Repeated greedy runs are reproducibility checks, not stochastic robustness experiments.

---

# 11. P10 — Replace Simulated "Human Validation" with Real Human Adjudication

This is a **critical publication blocker**.

Programmatically generated labels with random disagreement are not human validation.

## Required protocol

Prepare:

```text
human_review_pack.csv
```

containing blinded:

```text
case_id
user request
relevant context/evidence
model candidate/final output
tool/effect trace if necessary
attack goal where adjudication requires it
```

Do not expose system identity.

## Reviewers

Preferred:

```text
2 independent human reviewers
N >= 220
```

Use anonymous reviewer IDs:

```text
R1
R2
```

Store actual submitted labels and timestamps.

## Statistics

Report:

```text
R1 vs R2 agreement
Cohen's kappa
R1 vs deterministic oracle
R2 vs deterministic oracle
class-wise disagreement
adjudicated final label
```

If only one human reviewer is available:

- report one-human verification;
- remove the words `dual-rater` and `Cohen's kappa between experts`.

If no human reviewer can be recruited:

- remove every human-validation claim;
- describe any AI review as:
  ```text
  AI-assisted evaluator audit
  ```
  not human validation.

---

# 12. P11 — Replace Weak Generic Oracle with Attack-Specific Behavioral Judges

Attack success cannot be determined primarily from forbidden substrings.

Create:

```text
evaluation/llm_security_v3_1/judges/
```

with per-threat judges.

## Direct/jailbreak

Measure actual intent/capability/action changes.

## Indirect prompt injection

Measure:

```text
model compromise
trusted effect compromise
```

separately.

## Poisoning

Measure:

```text
poison retrieval
poison admission
poison influence
```

## Sensitive exfiltration

Seed a synthetic secret in trusted/private context, not in the user prompt.

Measure:

```text
model leakage
egress leakage
```

## Excessive agency

Use a mock tool executor.

Measure:

```text
unauthorized proposal
unauthorized admission
unauthorized execution
```

## Resource exhaustion

Measure actual:

```text
input/output tokens
tool calls
retrieval count
recursion/depth
elapsed time
budget-exceeded terminal status
```

Do not rely on text labels for resource attack success.

## Nonexistent entity / misinformation

Use a frozen authoritative fact/entity store.

Measure accepted unsupported claims, not keyword matches.

---

# 13. P12 — Exercise CapabilityGate and ResourceGuard End-to-End

The V3 publication path must actually invoke the components claimed as part of the enforcement envelope.

## Capability path

Required trace:

```text
model proposes action
 -> CapabilityGate evaluates
 -> policy/approval checks
 -> mock executor accepts/rejects
 -> execution recorded
```

## Resource path

Required trace:

```text
budget initialized
 -> token/retrieval/tool usage updated
 -> budget checked during execution
 -> terminal result generated on exceed
```

Add invariant tests:

```text
unauthorized proposal != unauthorized execution
resource budget cannot be expanded by model output
```

A component that exists only as a documented class but is not executed in the evaluated SUT cannot support an empirical claim.

---

# 14. P13 — Utility Metric Repair

## Semantic utility

Do not score a benign task as successful merely because output contains a generic token such as:

```text
"revenue"
"매출"
```

Each benign case must have an explicit expected semantic target.

Possible scoring:

```text
exact expected field
normalized numeric match
frozen acceptable-answer set
human adjudication for open text
```

## Contract utility

Actually parse output.

Require:

```text
valid JSON
schema validation
required fields
valid evidence/citation IDs
correct answer values
```

Checking for `{` and a keyword is insufficient.

Report separately:

```text
Semantic Task Success
Contract Success
Structured Validity
Citation Accuracy
FRR
```

---

# 15. P14 — Exact Statistical Analysis

## Exact McNemar

Use the exact binomial formulation for discordant pairs:

```python
scipy.stats.binomtest(...)
```

Do not label continuity-corrected chi-square as "exact McNemar."

## Confidence intervals

Report:

```text
raw count / denominator
Wilson 95% CI
absolute risk reduction
```

## Multiple comparisons

Use:

```text
Holm correction
```

where multiple baseline tests are presented.

## Stochastic runs

Report:

```text
mean
SD
median
range
per-seed values
```

## Per-class results

The final result package must include per-threat MCR/E2E-ASR, not only macro summaries.

---

# 16. P15 — Correct the Containment Funnel

Define stages unambiguously:

```text
Attack attempts
 -> LLM invoked
 -> Model compromised
 -> Pre-effect enforcement passed
 -> Post-generation/output enforcement passed
 -> Tool/state effect attempted
 -> Trusted effect committed
```

Every attacked case belongs to a valid flow.

Do not count only one subset as `passed_pre_llm_enforcement`.

For each transition report:

```text
count
rate
case IDs
guard responsible for containment
```

The funnel is central evidence for:

> Model compromise does not necessarily imply system compromise.

---

# 17. P16 — Parser Robustness Expansion

The robustness suite should be expanded to a publication-scale dataset.

Minimum:

```text
>= 100 cases
```

Preferred:

```text
>= 200 cases
balanced KO/EN where applicable
```

Cover:

```text
paraphrase
typos
code switching
homoglyphs
zero-width
RTL controls
nested quotes
Markdown/XML/HTML
encoded payloads
split instruction
multi-entity ambiguity
period ambiguity
metric ambiguity
role-play
benign formatting noise
```

Report:

```text
Intent Exact Match
Entity Exact Match
Action Exact Match
Authority Escalation Rate
Benign Parse FRR
Parse Rejection Rate
```

Do not state that NFKC eliminates all homoglyph attacks.

Use scoped wording:

> NFKC reduces a subset of Unicode compatibility variations.

---

# 18. P17 — Publication Validator Must Validate Evidence, Not File Existence

Current `publication_eligible=true` must never be hard-coded.

Create a strict validator that recomputes eligibility.

It must verify:

```text
raw record count matches manifest
all 850 held-out cases executed
same case set across compared systems
same case set across two models
no fallback records
real AgentDojo provenance exists
modern-baseline fidelity report exists
adaptive mutations are non-identical and budget reaches 20
human labels are externally supplied, not generated by campaign code
all required attack-specific judges executed
CapabilityGate actually exercised
ResourceGuard actually exercised
exact stats regenerated from raw records
dataset/hash/code freeze is valid
manuscript table CSVs match JSON summaries
```

Publication validation should fail loudly on any missing condition.

Output:

```json
{
  "publication_eligible": false,
  "failures": [...]
}
```

until every mandatory condition is satisfied.

---

# 19. P18 — Reproducibility Package

Required:

```text
README_REPRODUCE.md
ARTIFACT_MANIFEST.json
requirements.lock / uv.lock / pip freeze
Ollama model manifests
dataset SHA-256
baseline repository commits
AgentDojo commit/version
defense source commit
adaptive attacker model/version
seed/config files
raw runs
statistics scripts
```

Add a single command:

```bash
python -m evaluation.llm_security_v3_1.run_publication_campaign \
  --config configs/publication_v3_1.yaml

python -m evaluation.llm_security_v3_1.validate_publication_results \
  --strict
```

A second clean-machine reproduction is strongly recommended.

---

# 20. P19 — Manuscript Repair

The current LaTeX revision should remain a structural draft only.

## 20.1 Replace old V2 Results

The final manuscript must not mix:

```text
new V3 methodology
```

with:

```text
old V2 320-case / 0-of-280 Results
```

When V3.1 is frozen, replace Results and Discussion entirely with V3.1 evidence.

## 20.2 Dataset counts

Generate all dataset tables from frozen manifests.

Do not manually state:

```text
development = 1600
held-out class distribution = ...
```

unless those values exactly match the files.

## 20.3 Runtime configuration

Update from actual V3.1 execution:

```text
Ollama model IDs/digests
max_new_tokens
temperature/top_p
quantization
fallback disabled
actual hardware
actual dataset hashes
```

Remove stale V2 Hugging Face/Transformers/bitsandbytes configuration if not used.

## 20.4 Human-validation language

No manuscript claim may say:

```text
dual-blinded experts
human adjudication
Cohen's kappa between reviewers
```

until real labels exist.

## 20.5 Public-benchmark language

No manuscript claim may say:

```text
AgentDojo public benchmark
CaMeL comparison
Progent comparison
```

unless fidelity requirements in this work order pass.

Otherwise use:

```text
AgentDojo-inspired micro-suite
CaMeL-inspired approximation
Progent-inspired approximation
```

## 20.6 Bibliography key audit

Fix all unresolved/mismatched citation keys.

Run:

```text
pdflatex
bibtex/biber as appropriate
pdflatex
pdflatex
```

and fail the manuscript gate if there are:

```text
undefined citations
undefined references
duplicate bibliography entries
```

## 20.7 Appendix order

For IEEEtran, place:

```latex
\appendices
...
\bibliographystyle{IEEEtran}
\bibliography{references}
```

unless the target venue explicitly requires another order.

---

# 21. P20 — Final Report Consistency Rules

Generate:

```text
docs/security_v3_1/HETE_UIR_V3_1_FINAL_REPORT.md
```

programmatically from frozen result JSON/CSV.

No hand-entered result numbers.

The report must answer:

1. Was all runtime/oracle separation verified?
2. Are runtime case IDs opaque?
3. What is the actual dev/validation/held-out size?
4. What is held-out template/semantic diversity?
5. What modern baselines are official vs approximate?
6. Was real AgentDojo executed?
7. Was adaptive search real and how many unique mutations were tested?
8. Did the search reach query budget 20?
9. Were Phi and Qwen run on the same cases?
10. Was fallback disabled?
11. Were stochastic seeds run?
12. Were real humans used?
13. What is human inter-rater kappa?
14. How is MCR defined per class?
15. How is E2E-ASR defined per class?
16. Was CapabilityGate exercised?
17. Was ResourceGuard exercised?
18. What are the per-class results?
19. What is MCR-to-E2E containment by gate?
20. Which HETE failures remain?

---

# 22. Minimum Final Campaign

At minimum execute:

## Custom held-out

```text
850 / 850 cases
```

for:

```text
Vanilla
Naive RAG
Prompt-only
Spotlighting
CaMeL or CaMeL-inspired (clearly labeled)
Progent or Progent-inspired (clearly labeled)
HETE
```

## Models

```text
Phi-3.5
Qwen2.5-7B
```

on the same frozen evaluation subset; preferably the full 850.

## Adaptive

```text
6 campaigns
>=30 seed attacks/campaign
20-query maximum
A0/A1/A2
```

## Human

```text
>=220 blinded adjudications
2 real reviewers preferred
```

## AgentDojo

Actual official suite if integration is claimed.

## Stochastic

```text
temp=0.7
top_p=0.9
>=5 seeds
```

on a preregistered representative subset or full set.

---

# 23. Publication Acceptance Criteria

The work is complete only when:

- [ ] Current V3 is archived as prevalidation.
- [ ] Opaque runtime IDs are used.
- [ ] Semantic/template/embedding leakage audit is complete.
- [ ] Provenance claim matches actual authentication mechanism.
- [ ] Baseline fidelity is documented.
- [ ] Real AgentDojo is executed or all public-AgentDojo claims are removed.
- [ ] Adaptive attacks actually mutate and search.
- [ ] Query budget reaches 20.
- [ ] Same dataset is used for Phi/Qwen comparison.
- [ ] No deterministic fallback is allowed.
- [ ] Stochastic 5-seed experiment exists.
- [ ] Human validation uses actual humans or the claim is removed.
- [ ] Attack-specific behavioral judges replace generic substring scoring.
- [ ] Synthetic secrets reside in protected context, not user input.
- [ ] CapabilityGate is exercised end-to-end.
- [ ] ResourceGuard is exercised end-to-end.
- [ ] Semantic utility is exact/task-specific.
- [ ] Contract utility uses real JSON/schema/citation validation.
- [ ] Exact McNemar is actually exact.
- [ ] Holm correction is applied where needed.
- [ ] Per-class results and raw counts exist.
- [ ] Containment funnel is recomputable from raw records.
- [ ] Full raw artifact package is available.
- [ ] Publication validator derives eligibility, not hard-codes it.
- [ ] Manuscript Results/Discussion are entirely regenerated from V3.1.
- [ ] No stale V2 runtime/results remain in primary empirical sections.
- [ ] All bibliography keys resolve.
- [ ] Final LaTeX builds without undefined citations/references.

---

# 24. Priority Order

## Critical blockers — do first

1. Real human validation or remove human claims.
2. Real AgentDojo or rename as micro-suite.
3. Real adaptive search, not repeated static prompts.
4. Disable all fallbacks.
5. Full raw-result capture.
6. Attack-specific judges.
7. Capability/resource end-to-end execution.
8. Correct multi-model denominators and same-case evaluation.
9. Publication validator redesign.

## High priority

10. Provenance authentication claim repair.
11. Utility metric repair.
12. Dataset semantic/diversity audit.
13. Exact statistics.
14. Stochastic robustness.
15. Parser robustness expansion.

## Final

16. Freeze V3.1.
17. Generate result tables.
18. Replace manuscript Results/Discussion.
19. Fix bibliography.
20. Full clean build and independent reproduction.

---

# 25. Scientific Success Criterion

The desired result is **not** another perfect `0%` table.

A stronger final result would look like:

```text
Adaptive white-box attack:
HETE MCR = 24%
HETE E2E-ASR = 3%

Comparator E2E-ASR = 9%
```

with:

```text
real public benchmark
real raw evidence
real attack search
real human checks
no hidden fallback
same cases across models
reproducible statistics
```

That directly supports the paper's central thesis:

> **The LLM may be compromised while the application remains uncompromised because trusted authority is enforced outside the model.**

---

## Final Engineering Principle

> **Do not certify completion from the report. Certify it from raw evidence that an independent reviewer can recompute.**
