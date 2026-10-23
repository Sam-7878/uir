"""Pre-data planning and explicit gate prerequisites; no fake preregistration."""
from itertools import product
import math


def precision_plan():
    # Exact one-sided no-event upper bound under INDEPENDENT Bernoulli units.
    rows = []
    for n in (2, 24, 50, 100, 200, 300):
        rows.append({"independent_units": n, "zero_event_one_sided_95_upper": 1 - 0.05 ** (1 / n),
                     "worst_case_wald_halfwidth_planning_only": 1.96 * math.sqrt(0.25 / n)})
    return {"status": "PLANNING_NOT_PREREGISTERED", "rows": rows,
            "note": "Independent units are parent families, not copies of queries. Two families cannot justify 200 independent trials.",
            "hypothesis_test_power": "NOT_ESTIMABLE_WITHOUT_DISCORDANCE_AND_CLUSTER_MODEL",
            "source_target": "AT_LEAST_TWO_CANDIDATE_FAMILIES_NOT_SUFFICIENT_FOR_CONFIRMATORY_POWER"}


def matrix():
    return [{"representation": r, "selector": s, "renderer": d, "stratum": "NON_ORACLE_PRIMARY_PLANNED",
             "same_registry_authority_guard_budget": True, "execution_status": "NOT_EXECUTED"}
            for r, s, d in product(("UIR", "EQUIVALENT_SPECIALIZED"), ("DETERMINISTIC", "LOCAL_SLM"), ("DETERMINISTIC", "LOCAL_SLM"))]


def require_confirmation(proof):
    required = ("source_bytes_verified", "dataset_rights_recorded", "document_family_disjoint", "query_template_family_disjoint",
                "gold_role_separation", "runtime_gold_os_isolation_verified", "protocol_frozen_before_inference",
                "method_review_recorded", "precision_target_satisfied")
    missing = [key for key in required if proof.get(key) is not True]
    if missing:
        raise ValueError("CONFIRMATORY_BLOCKED:" + ",".join(missing))
    if proof.get("split") != "CONFIRMATORY_FRESH" or proof.get("previously_observed") is not False:
        raise ValueError("DEVELOPMENT_CANNOT_BECOME_CONFIRMATORY")
    return True


def preregistration_text():
    return """# T18 draft — NOT PREREGISTERED / NOT A CONFIRMATORY FREEZE

Primary claim: preservation of policy/evidence-bound execution semantics across consumers,
UIR versus equivalently capable specialized representation. Primary endpoint: semantic state
and accepted-ID mismatch per all paired cases, with parent-source-family clustering.
Eight matched cells: representation x selector x renderer. Oracle evidence is a separate
secondary stratum, never pooled into non-oracle main effects. Same raw query, catalog,
authority, guard, model digest, seed, budget and clock boundaries in both representations.

Invalid output, timeouts and abstentions remain in the all-assigned denominator. Report
accepted-nonempty and model-invoked denominators separately. Template guard effects are
shared-verifier effects, not UIR accuracy superiority. Native prose AUCR remains NOT_MEASURED
unless every displayed prose claim is actually annotated and assessed.

Planned paired exact McNemar for case discordance is descriptive if clustered; primary
uncertainty uses family bootstrap with declared multiplicity correction. No equivalence
or noninferiority claim without a prespecified justified margin. Cluster counts and
effective precision, not fabricated 200 repeated-template requests, determine adequacy.

Independent request design/gold role separation, document/template disjointness, rights,
OS gold-access isolation, model digests and review must be certified before a real freeze.
No gold packet, raw request set or source facts have been supplied to a model by this runner.
AI_ONLY_METHOD_REVIEW is not independent human validation. This draft is hash-recorded only;
hashing an incomplete protocol does not make it preregistered. Endpoint changes require a
new protocol version and previously inspected data remains DEVELOPMENT/EXPLORATORY.
"""
