#!/usr/bin/env python3
"""
Stage 118 — T41 Execution Script
Establish multi-tier reproducibility packages (private full vs public safe),
record third-party rights clearance, and propose a transparent data availability statement.
"""

import json
import os
import csv
import hashlib

BASE_DIR = "/mnt/d/_Work/goat_bank/uir"
STAGE116_DIR = os.path.join(BASE_DIR, "projects/uir_base/results/116_electronics_confirmatory_2026_10_23")
STAGE117_RUN = os.path.join(BASE_DIR, "projects/uir_base/results/117_electronics_evidence_closure_2026_10_23/run_20261023T120000Z")
STAGE118_RUN = os.path.join(BASE_DIR, "projects/uir_base/results/118_electronics_submission_remediation_2026_10_23")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("--- [T41] Establishing Reproducibility Tiers and Rights Matrices ---")

    # 1. lineage_index_118.json
    lineage = {
        "timestamp": "2026-10-23T21:07:00Z",
        "description": "Cross-stage evidence linkage connecting Stage 116 raw inputs to Stage 118 publication tables",
        "stages": {
            "stage_116_raw": {
                "checkpoint_id": "run_20261023T100000Z",
                "raw_trace": "projects/uir_base/results/116_electronics_confirmatory_2026_10_23/run_20261023T100000Z/experiments/primary_raw.jsonl",
                "sha256": compute_sha256(os.path.join(STAGE116_DIR, "run_20261023T100000Z/experiments/primary_raw.jsonl")),
                "total_raw_rows": 481,
                "outcome_records": 480
            },
            "stage_116_secondary_raw": {
                "checkpoint_id": "run_20261023T095130Z",
                "raw_capture": "projects/uir_base/results/116_electronics_confirmatory_2026_10_23/run_20261023T095130Z/experiments/runtime_capture.jsonl",
                "sha256": compute_sha256(os.path.join(STAGE116_DIR, "run_20261023T095130Z/experiments/runtime_capture.jsonl")),
                "unique_model_captures": 480,
                "raw_outcomes": 1920
            },
            "stage_117_reconciled": {
                "checkpoint_id": "run_20261023T120000Z",
                "scored_primary": "projects/uir_base/results/117_electronics_evidence_closure_2026_10_23/run_20261023T120000Z/scoring/final_per_case_scored_117.jsonl",
                "scored_secondary": "projects/uir_base/results/117_electronics_evidence_closure_2026_10_23/run_20261023T120000Z/scoring/secondary_rescore_117.jsonl",
                "evidence_manifest": "projects/uir_base/results/117_electronics_evidence_closure_2026_10_23/run_20261023T120000Z/evidence_manifest.json"
            },
            "stage_118_remediated": {
                "root": "projects/uir_base/results/118_electronics_submission_remediation_2026_10_23",
                "manuscript_workspace": "projects/uir_base/paper/mdpi_electronics_118"
            }
        }
    }

    lineage_path = os.path.join(STAGE118_RUN, "release/lineage_index_118.json")
    with open(lineage_path, "w", encoding="utf-8") as f:
        json.dump(lineage, f, indent=2)
    print(f"Wrote {lineage_path}")

    # 2. private_reproduction_manifest_118.json
    priv_files = [
        os.path.join(STAGE116_DIR, "run_20261023T100000Z/experiments/primary_raw.jsonl"),
        os.path.join(STAGE116_DIR, "run_20261023T095130Z/experiments/runtime_capture.jsonl"),
        os.path.join(STAGE117_RUN, "scoring/final_per_case_scored_117.jsonl"),
        os.path.join(STAGE117_RUN, "scoring/secondary_rescore_117.jsonl"),
        os.path.join(STAGE118_RUN, "audit/raw_to_derived_lineage_118.csv"),
        os.path.join(STAGE118_RUN, "audit/independent_recompute_118.json"),
        os.path.join(STAGE118_RUN, "claim_audit/claim_semantics_audit_118.csv"),
        os.path.join(STAGE118_RUN, "claim_audit/selector_eligible_reanalysis_118.csv")
    ]
    priv_manifest = {
        "tier": "PRIVATE_FULL_REPRODUCIBILITY",
        "access": "CONFIDENTIAL_AUDIT_ONLY",
        "description": "Full end-to-end execution reproduction manifest linking physical raw bytes, model captures, and scored tables.",
        "files": {
            os.path.relpath(f, BASE_DIR).replace("\\", "/"): {
                "sha256": compute_sha256(f),
                "byte_size": os.path.getsize(f)
            }
            for f in priv_files if os.path.exists(f)
        }
    }

    priv_path = os.path.join(STAGE118_RUN, "release/private_reproduction_manifest_118.json")
    with open(priv_path, "w", encoding="utf-8") as f:
        json.dump(priv_manifest, f, indent=2)
    print(f"Wrote {priv_path}")

    # 3. public_safe_candidate_manifest_118.json
    pub_files = [
        os.path.join(STAGE118_RUN, "audit/independent_recompute_118.json"),
        os.path.join(STAGE118_RUN, "claim_audit/claim_semantics_audit_118.csv"),
        os.path.join(STAGE118_RUN, "claim_audit/metric_eligibility_contract_118.yaml"),
        os.path.join(STAGE118_RUN, "claim_audit/selector_eligible_reanalysis_118.csv"),
        os.path.join(STAGE118_RUN, "claim_audit/counterfactual_claim_limits_118.md")
    ]
    pub_manifest = {
        "tier": "PUBLIC_SAFE_CANDIDATE",
        "access": "BLOCKED_PENDING_OWNER_RIGHTS_CLEARANCE",
        "description": "Public candidate artifacts containing statistical aggregations, formal models, and code verification scripts without raw proprietary source bytes.",
        "files": {
            os.path.relpath(f, BASE_DIR).replace("\\", "/"): {
                "sha256": compute_sha256(f),
                "byte_size": os.path.getsize(f)
            }
            for f in pub_files if os.path.exists(f)
        }
    }

    pub_path = os.path.join(STAGE118_RUN, "release/public_safe_candidate_manifest_118.json")
    with open(pub_path, "w", encoding="utf-8") as f:
        json.dump(pub_manifest, f, indent=2)
    print(f"Wrote {pub_path}")

    # 4. rights_clearance_matrix_118.csv
    rights_matrix = [
        {
            "component": "Software Manifest Frame (82 repositories)",
            "source": "Public GitHub open-source repositories",
            "license": "Permissive (MIT, Apache-2.0, BSD-3-Clause)",
            "clearance_status": "LOCAL_RESEARCH_CLEARED",
            "public_release_permission": "BLOCKED (Requires individual repository license audit allowlist)",
            "notes": "Original manifest files used for byte offset validation."
        },
        {
            "component": "Phi-3.5-mini-instruct Model Weights",
            "source": "Microsoft / Hugging Face",
            "license": "MIT License",
            "clearance_status": "LOCAL_RESEARCH_CLEARED",
            "public_release_permission": "PERMITTED_UNDER_MIT",
            "notes": "Quantized GGUF Q4_K_M weights used locally."
        },
        {
            "component": "US Treasury Open Debt Data (Pilot)",
            "source": "Fiscal Data API (fiscaldata.treasury.gov)",
            "license": "US Government Work (17 U.S.C. § 105)",
            "clearance_status": "PILOT_ONLY",
            "public_release_permission": "BLOCKED (Requires explicit owner sign-off)",
            "notes": "Excluded from confirmatory primary claims."
        },
        {
            "component": "UIR & Specialized Compiler Source",
            "source": "Proprietary Research Codebase (Sam-7878/UIR)",
            "license": "Proprietary / Author Copyright",
            "clearance_status": "OWNER_CONFIDENTIAL",
            "public_release_permission": "BLOCKED (Requires human author release decision)",
            "notes": "Private local execution only."
        }
    ]

    rights_path = os.path.join(STAGE118_RUN, "release/rights_clearance_matrix_118.csv")
    with open(rights_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "component", "source", "license", "clearance_status", "public_release_permission", "notes"
        ])
        writer.writeheader()
        writer.writerows(rights_matrix)
    print(f"Wrote {rights_path}")

    # 5. data_availability_proposal_118.md
    da_path = os.path.join(STAGE118_RUN, "release/data_availability_proposal_118.md")
    with open(da_path, "w", encoding="utf-8") as f:
        f.write(r"""# Stage 118 — Data and Code Availability Statement Proposal

**Proposed Text for MDPI Electronics Manuscript:**

> **Data Availability Statement:** The mathematical models, statistical recomputation scripts, and evaluation metadata supporting the conclusions of this article are available in the local replication archive. Independent numerical recalculation of all primary hypergeometric p-values and factorial attribution tables can be fully performed using the open-source statistical routines provided in the supplementary materials. The raw third-party repository software manifests and model interaction capture logs are maintained in a secure local repository to respect repository owner licensing terms and will be made available by the corresponding author upon reasonable academic request and execution of a standard research data agreement.

---

## 2. Reviewer vs Public Separation
- **External Peer Reviewers:** Can independently recalculate all exact $p$-values, confidence intervals, Macro F1 scores, and tabular values using `independent_recompute_118.json` and verification scripts.
- **Public Domain:** Release candidate will NOT bundle unvetted external source manifest files or private Git histories without author allowlist.
""")
    print(f"Wrote {da_path}")
    print("--- [T41] Completed Successfully ---")

if __name__ == "__main__":
    main()
