# Annotation protocol and independence boundary

Date: 2026-10-11. Project: `uir_base` MDPI revision.

## Current evidence

Historical annotation contains AI-session and deterministic-script evidence, not
independent human gold. This must be stated in Methods, not only Limitations.
The additional local reviewers approved by the user are Qwen3-4B-Instruct-2507
and Ministral 3 14B Instruct. Their isolated, cross-family judgments are separately
labelled AI_J1/AI_J2. They do not become H1/H2 and cannot certify human review.

The executable AI rubric, settings, limitations and output definitions are in
[LOCAL_AI_REVIEW_PROTOCOL.md](LOCAL_AI_REVIEW_PROTOCOL.md). For status and evidence
paths see [LOCAL_AI_REVIEW_STATUS.md](LOCAL_AI_REVIEW_STATUS.md). Actual AI outputs
must be separated from original annotations and from any eventual human labels.

## Sample and blinding

Use the existing post-hoc stratified sample: 120 cases selected with seed 20261011,
10 per stratum/language group where available. Preserve the sampling manifest and
the frozen runtime source hash. This was not sampled prospectively before all
historical results existed, so it must not be described as a prospective holdout
or whole-benchmark human ground truth.

Reviewers receive raw text, a clearly identified system-candidate representation
and authoritative finite policy rules. The candidate is not a correct reference.
It originates from the historical compiler with trusted slot metadata, which
limits interpretation of parser correctness. Independent text-based judgments
must not simply adopt that metadata as truth.

The preliminary H1/H2 templates retain original case IDs for joining. Those IDs
can reveal strata such as ADVERSARIAL and must be replaced by opaque IDs before
they are used for actual human review. The final AI `review_packets.jsonl` already
uses opaque IDs; the evaluator-only mapping must not be included in reviewer
prompts/packets. Do not distribute gold, earlier labels, model identity, aggregate
scores, or another reviewer's decisions. In the actual local AI run, gold/scoring/
human-label file access is additionally denied by a process audit hook.

## Future independent human review — not yet performed

Recruit at least two reviewers with Korean/English and financial-domain competence.
Record reviewer expertise and anonymized identifiers, review dates, time spent,
instructions, consent/compensation where applicable, and institutional ethics
requirements. Obtain author/institution confirmation before filling ethics or
IRB declarations; do not automatically assert "Not applicable".

H1 and H2 review independently without seeing each other's labels or AI verdicts.
Assess intent, entity, attribute, period, explicit conditions, ambiguity and policy
decision from the raw input and the supplied authoritative rules. Cover negation,
omission, code mixing, numerical units, AND/OR parentheses, conditional scope,
permission expressions and ambiguous requests. Mark uncertainty or insufficient
information rather than assuming the compiler is correct. A default system
provenance constraint is not evidence that all user conditions were preserved.

Keep original judgments immutable. Report per-field agreement, category confusion,
valid-pair denominators, missing data and uncertainty. Obtain separate adjudication
for disagreement, preserving both original labels, adjudicator identity, decision
and reasoning. The script, a third AI model, or a two-model tie is not a human
adjudicator. Do not silently overwrite contradictory original decisions.

Report human-audited subset results separately from AI-audited data. Correlated
language variants/templates are not automatically independent random cases.
Compile-successful digest-equivalence pairs are not a denominator for all-input
end-to-end semantic correctness.

## Current completion flags

- Human reviewers completed: 0.
- `human_labels.csv`: intentionally contains no completed human judgments.
- `adjudication.csv`: intentionally contains no completed human adjudication.
- Original W08 independent-human requirement: not satisfied.
- Author/ethics/backmatter confirmation: pending.
- Local AI review: additional evidence only; consult its actual run manifest.

An AI-only manuscript is a different evidence design and must explicitly disclose
that no human annotation was performed. Cross-model agreement measures agreement,
not accuracy, and cannot establish statistical independence of errors.
