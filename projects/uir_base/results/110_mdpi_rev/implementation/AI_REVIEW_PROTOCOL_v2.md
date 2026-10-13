# AI review v2 (prepared protocol; not completed annotation)

The 20261011T114157Z 120-case /240-response run is frozen. Do not tune v2 on
that run then replace its labels. AI-only route B is explicitly approved; original
W08 remains NOT_SATISFIED. Agreement is supplementary, not reviewer accuracy.

Separate request_ambiguity (CLEAR/AMBIGUOUS), reviewer_epistemic_state
(DECISIVE/UNCERTAIN), candidate_status (PRESENT/ABSENT), evaluability
(EVALUABLE/NOT_EVALUABLE), and policy/entity/evidence availability. If candidate
is absent, slot-match and condition-preservation are NOT_EVALUABLE, not false.
User condition presence and preservation differ from a default provenance rule.

Finite policy rules and authenticated role/action context constrain policy labels;
reviewers must not invent policy from source availability or subjective risk.
Development calibration uses novel explicit CNL/policy fixtures, separately
identified as synthetic conformance gold. It is NOT human semantic gold.

Actual calibration and heldout model judgments require a frozen new packet,
rubric/schema/options/digests, complete raw responses and failures, no access to
other judgments, and no favorable rerun selection. Until executed, calibration
accuracy is NOT_MEASURED and new AI holdout is NOT_EXECUTED. No two-reviewer
majority can adjudicate ties. Independent truth labels absent -> unresolved.

Report schema validity, evaluable fraction, uncertainty/abstention, confusion
matrix on explicit synthetic truth, agreement and decisive agreement separately.
Do not optimize kappa as a gate. Old reviewer outputs and original templates
must not be overwritten by this protocol.
