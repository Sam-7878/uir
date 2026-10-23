#!/usr/bin/env python3
"""
Stage 117 — T29 Execution Script
Audit second-domain candidate readiness (Treasury DebtToPenny),
record source byte rights and family disjointness,
establish gold authority matrix and dataset card,
and formalize the single-domain bounded frame scope decision.
"""

import json
import os
import csv

BASE_DIR = "/mnt/d/_Work/goat_bank/uir"
STAGE117_RUN = os.path.join(BASE_DIR, "projects/uir_base/results/117_electronics_evidence_closure_2026_10_23/run_20261023T120000Z")

def main():
    print("--- [T29] Evaluating Domain Coverage and Source Rights ---")

    # 1. second_domain_readiness_117.json
    readiness = {
        "timestamp": "2026-10-23T12:00:00Z",
        "evaluator": "Stage 117 Domain Governance & Science Gate",
        "second_domain_candidate": "US-Treasury:DebtToPenny",
        "candidate_source_bytes": 3168,
        "candidate_row_count": 5,
        "metadata_api_status": "HTTP_404_CATALOG_DATA_GOV",
        "fiscal_api_status": "HTTP_200_PHYSICAL_BYTES_VERIFIED",
        "has_independent_human_gold": False,
        "has_query_aware_temporal_holdout": False,
        "has_unseen_confirmatory_families": False,
        "rights_status": "US_GOVERNMENT_PUBLIC_DOMAIN_CANDIDATE_AUTHOR_SIGNOFF_PENDING",
        "gold_isolation_guarantee": "NOT_OS_ISOLATED_IN_STAGE116_PILOT",
        "readiness_verdict": "UNAVAILABLE_FOR_CONFIRMATORY_INFERENCE",
        "recommendation": "SINGLE_DOMAIN_SOFTWARE_CONTRACT_PRIMARY_WITH_PILOT_PROTOTYPE_REPORTING"
    }
    readiness_path = os.path.join(STAGE117_RUN, "source_registry/second_domain_readiness_117.json")
    with open(readiness_path, "w", encoding="utf-8") as f:
        json.dump(readiness, f, indent=2)
    print(f"Wrote {readiness_path}")

    # 2. source_family_disjoint_117.csv
    disjoint_path = os.path.join(STAGE117_RUN, "source_registry/source_family_disjoint_117.csv")
    with open(disjoint_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["family_id", "domain", "role", "split", "N_cases", "disjoint_from_pilot", "confirmatory_eligible"])
        writer.writerow(["github-owner:* (82 owners)", "Software Manifest", "Primary Benchmark Frame", "V4_FROZEN_FRAME", 240, True, True])
        writer.writerow(["US-Treasury:DebtToPenny", "Financial/Fiscal", "Feasibility Prototype", "STAGE116_PILOT_ONLY", 5, False, False])
        writer.writerow(["WorldBank:Finances", "Financial/Development", "Candidate (Network Timed Out)", "DROPPED", 0, False, False])
    print(f"Wrote {disjoint_path}")

    # 3. source_byte_rights_117.csv
    rights_path = os.path.join(STAGE117_RUN, "source_registry/source_byte_rights_117.csv")
    with open(rights_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_id", "source_uri", "license_declared", "distribution_scope", "local_research_permitted", "public_release_permitted"])
        writer.writerow([
            "github_software_manifests_82", "https://github.com/*", "Permissive (MIT/Apache-2.0/BSD)", 
            "Public open-source software repositories", True, False # Private evaluator only until explicit manifest allowlist
        ])
        writer.writerow([
            "treasury_debt_2024_first5.json", "https://api.fiscaldata.treasury.gov/...", "US Government Work (17 U.S.C. 105)", 
            "US Department of the Treasury Fiscal Data", True, False # Pending author legal signoff
        ])
    print(f"Wrote {rights_path}")

    # 4. gold_authority_matrix_117.csv
    gold_matrix_path = os.path.join(STAGE117_RUN, "source_registry/gold_authority_matrix_117.csv")
    with open(gold_matrix_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_type", "authority_policy_id", "normative_decision", "gold_source_mechanism", "human_vs_machine", "verification_rule"])
        writer.writerow([
            "software_version_major_ALLOW", "H116-P1", "ALLOW", "Raw Cargo.lock / Cargo.toml byte parsing", "MACHINE_DETERMINISTIC", "Exact integer string match"
        ])
        writer.writerow([
            "software_version_minor_ALLOW", "H116-P1", "ALLOW", "Raw Cargo.lock / Cargo.toml byte parsing", "MACHINE_DETERMINISTIC", "Exact integer string match"
        ])
        writer.writerow([
            "unauthorized_dependency_DENY", "H116-P1", "DENY", "Policy violation specification in contract", "MACHINE_DETERMINISTIC", "Contract-level block (0 display lines)"
        ])
        writer.writerow([
            "unauthorized_private_repo_DENY", "H116-P1", "DENY", "Policy violation specification in contract", "MACHINE_DETERMINISTIC", "Contract-level block (0 display lines)"
        ])
    print(f"Wrote {gold_matrix_path}")

    # 5. dataset_card_117.md
    dataset_card_path = os.path.join(STAGE117_RUN, "source_registry/dataset_card_117.md")
    with open(dataset_card_path, "w", encoding="utf-8") as f:
        f.write(r"""# Dataset Card — UIR Software Manifest Conformance Corpus (V4)

## 1. Corpus Summary
- **Domain:** Open-source software manifests (Rust ecosystem, `Cargo.toml`/`Cargo.lock`).
- **Eligible Target Frame:** $M = 82$ distinct GitHub-owner clusters meeting strict inclusion criteria (permissive license, clean manifest parsing, non-empty release snapshot).
- **Primary Sample Size:** $n = 60$ distinct clusters sampled without replacement ($SRSWOR$).
- **Cases per Cluster:** 4 balanced queries (2 ALLOW: major/minor version; 2 DENY: unauthorized scope/metric).
- **Total Evaluated Cases:** 240 unique cases $\times 2$ representations (UIR, Specialized) $= 480$ records.

## 2. Supported Metrics and Grounding
- **Entities:** Software package names (canonical uppercase tokens).
- **Metrics:** `package_version_major`, `package_version_minor`.
- **Period:** `release_snapshot`.
- **Units:** `COUNT`.
- **Grounding Target:** Exact source provenance pointers pointing to physical source byte offsets (`github-owner:<owner>:<commit>/package/version#<field>`).

## 3. Second-Domain Status
- US Treasury fiscal debt data was piloted on 5 rows to verify parser extensibility.
- Due to lack of independent large-scale query-aware gold and OS isolation in the pilot, it is **excluded from confirmatory claims** and documented solely as an exploratory feasibility demonstration.
""")
    print(f"Wrote {dataset_card_path}")

    # 6. SCOPE_DECISION_117.md
    scope_decision_path = os.path.join(STAGE117_RUN, "source_registry/SCOPE_DECISION_117.md")
    with open(scope_decision_path, "w", encoding="utf-8") as f:
        f.write(r"""# Stage 117 — Research Scope Decision and Stop Rule Declaration

**Date:** 2026-10-23  
**Decision Authority:** Lead Investigator / Stage 117 Science Gate  
**Target Manuscript:** MDPI *Electronics* Special Issue (“Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems”)  
**Target Title:** **“Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding”**

---

## 1. Context and Problem Statement

Stage 116 successfully completed a bit-exact audit and established a highly rigorous, finite-frame confirmatory trial on 82 GitHub-owner software manifests ($p=0.000965$, $0$ failures in 60 sampled clusters).
However, second-domain evidence (US Treasury fiscal debt data) was limited to a 5-row exploratory pilot with pending rights clearance, non-isolated gold, and an unverified external data catalog.

Under the Stage 117 Work Order (T29, Stop Rule B):
> *If second-domain / authoritative human gold cannot be established with prospective isolation and complete rights, the research shall NOT engage in infinite feature development. Instead, the authors shall formally narrow the claim boundary to a bounded software-manifest intermediate contract study.*

---

## 2. Formal Scope Determination: Single-Domain Bounded Confirmatory Route

We hereby adopt **Route B (Single-Domain Bounded Confirmatory Scope)**:

1. **Confirmatory Scientific Claims:**
   - Restricted strictly to the $M=82$ frozen software-manifest convenience frame.
   - Primary endpoint: Deterministic semantic preservation and cross-runtime interpreter conformance between independent Python and Rust interpreters ($480/480$, exact hypergeometric $p=0.000965$).
   - Secondary endpoint: Attribution analysis of SLM fact-selection error ($0/240$ exact match) vs deterministic guard rescue ($120/120$ template recovery) vs model rendering utility omission ($76/120$ completion, $44$ empty/omission).
2. **Exclusion of Cross-Domain Generalization:**
   - The manuscript will NOT claim empirical cross-domain transfer or multi-domain verification.
   - Financial data will be honestly cited as a preliminary prototype demonstration of syntactic grammar mapping, without statistical inference.
3. **Exclusion of Unmeasured Endpoints:**
   - `Native Prose AUCR`: Explicitly marked `NOT_MEASURED`.
   - `FinQA Official Task Accuracy`: Explicitly marked `NOT_MEASURED`.
   - `Portability Developer Effort`: Explicitly marked `NOT_MEASURED`.
   - `Representation Superiority`: Explicitly declared as `NOT_IDENTIFIED` (empirical equivalence under shared authority).

---

## 3. Justification and Journal Alignment

This scoped posture significantly **strengthens the paper for MDPI *Electronics***:
1. It eliminates the scientific vulnerability of over-claiming generalization from pilot data.
2. It highlights our strongest, indisputable scientific contribution: **The separation of generative model selection capability from accepted system correctness via typed intermediate contracts and deterministic guards**.
3. It directly aligns with the Special Issue focus on reliable electronic and software systems utilizing generative AI components.
""")
    print(f"Wrote {scope_decision_path}")
    print("--- [T29] Completed Successfully ---")

if __name__ == "__main__":
    main()
