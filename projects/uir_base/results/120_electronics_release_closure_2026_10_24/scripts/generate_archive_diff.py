import csv

rows = [
    {
        "artifact_path": "paper/mdpi_electronics_120/main.tex",
        "change_type": "MODIFIED_AND_EXPANDED",
        "stage119_reference": "paper/mdpi_electronics_119/main.tex (498 lines)",
        "stage120_status": "PRODUCED_676_LINES",
        "defect_addressed": "B120-01, B120-02, B120-08",
        "rational_justification": "Neutralized premature metadata to submit placeholders; fixed hypergeometric semantics to K<=2/82 and H_0: K>=5; expanded substantive architectural, trace, and threats sections to 16 pages"
    },
    {
        "artifact_path": "paper/mdpi_electronics_120/main.pdf",
        "change_type": "RECOMPILED",
        "stage119_reference": "paper/mdpi_electronics_119/main.pdf (12 pages, 228 KB)",
        "stage120_status": "COMPILED_16_PAGES (282,139 bytes)",
        "defect_addressed": "B120-01, B120-02, B120-08",
        "rational_justification": "Full 16-page clean-room compilation with 0 errors, 0 undefined citations, 0 overfull hboxes, using vector Palatino typefaces"
    },
    {
        "artifact_path": "paper/mdpi_electronics_120/figures/execution_trace_120.tex",
        "change_type": "ADDED",
        "stage119_reference": "NONE (implicit narrative only)",
        "stage120_status": "CREATED_TIKZ_DIAGRAM",
        "defect_addressed": "B120-08, T66",
        "rational_justification": "TikZ vector flowchart demonstrating the 2x2x2 factorial response reuse topology and 480 unique model invocations"
    },
    {
        "artifact_path": "results/120_.../statistics/hypergeom_source_of_truth_120.json",
        "change_type": "ADDED",
        "stage119_reference": "NONE (conflated in markdown)",
        "stage120_status": "VERIFIED_SOURCE_OF_TRUTH",
        "defect_addressed": "B120-01",
        "rational_justification": "Canonical ground-truth combinatorial values for K=2, 3, 5 under M=82, n=60"
    },
    {
        "artifact_path": "results/120_.../audit/stage119_errata_120.md",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "PUBLISHED_ERRATA",
        "defect_addressed": "B120-01",
        "rational_justification": "Formal errata documenting the exact mathematical cause and text remediation of the hypergeometric conflation"
    },
    {
        "artifact_path": "results/120_.../scripts/check_hypergeom_semantics_120.py",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "EXECUTABLE_ASSERTION_PASS",
        "defect_addressed": "B120-01",
        "rational_justification": "Automated regression verification script asserting exact hypergeometric values and thresholds"
    },
    {
        "artifact_path": "results/120_.../editorial/mdpi_submitted_metadata_audit_120.md",
        "change_type": "ADDED",
        "stage119_reference": "audit/mdpi_metadata_check_119.md",
        "stage120_status": "AUDITED_AND_NEUTRALIZED",
        "defect_addressed": "B120-02",
        "rational_justification": "Audited and confirmed purging of volume 15, issue 18, article 4335 in favor of official MDPI submit placeholders"
    },
    {
        "artifact_path": "results/120_.../release/REPRODUCTION_LEVELS_120.md",
        "change_type": "ADDED",
        "stage119_reference": "release/REPRODUCTION_MANUAL_119.md",
        "stage120_status": "TIERED_CLASSIFICATION",
        "defect_addressed": "B120-03",
        "rational_justification": "Demarcated Level 1 runnable reproduction (< 1s CPU) from Level 2/3 protocol-documented reproduction"
    },
    {
        "artifact_path": "results/120_.../release/reviewer_safe_replication_120.zip",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "GENERATED_ZIP (8,109 bytes)",
        "defect_addressed": "B120-03",
        "rational_justification": "Self-contained zip archive containing Level 1 python scripts and ground-truth tables for instant reviewer evaluation"
    },
    {
        "artifact_path": "results/120_.../editorial/COVER_LETTER_DRAFT_NOT_SENT.md",
        "change_type": "ADDED",
        "stage119_reference": "NONE (missing)",
        "stage120_status": "DRAFTED_OFFICIAL_LETTER",
        "defect_addressed": "B120-04",
        "rational_justification": "Complete MDPI cover letter draft including required non-duplication warranty and author consent placeholders"
    },
    {
        "artifact_path": "results/120_.../publication_gates/HUMAN_APPROVAL_EVIDENCE_120_PRIVATE.md",
        "change_type": "ADDED",
        "stage119_reference": "Stage 119 unverified APPROVED text",
        "stage120_status": "LEDGER_PENDING_HUMAN_ACTION",
        "defect_addressed": "B120-05",
        "rational_justification": "Private ledger documenting author provenance from a10 and establishing gate hold for physical human PI sign-off"
    },
    {
        "artifact_path": "results/120_.../publication_gates/author_declarations_120.md",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "PUBLIC_DECLARATIONS",
        "defect_addressed": "B120-05",
        "rational_justification": "Complete public-safe CRediT contribution taxonomy, ethical declarations, and AI assistance disclosure"
    },
    {
        "artifact_path": "results/120_.../scientific/identifiability_narrative_120.md",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "FORMAL_NARRATIVE",
        "defect_addressed": "T66",
        "rational_justification": "Rigorous explanation of causal attribution, response reuse graph, and representation neutrality (Delta = 0.0%)"
    },
    {
        "artifact_path": "results/120_.../claim_audit/case_study_evidence_120.csv",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "TRACE_EVIDENCE_CSV",
        "defect_addressed": "T66",
        "rational_justification": "Trace evidence table anchoring all three case studies to physical manifest offsets and SHA-256 byte hashes"
    },
    {
        "artifact_path": "results/120_.../release/owner_level_rights_120.csv",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "RIGHTS_MATRIX_82_ROWS",
        "defect_addressed": "T69",
        "rational_justification": "Detailed license and rights audit across all 82 software manifest owner organizations"
    },
    {
        "artifact_path": "results/120_.../release/PI_rights_decision_120_PRIVATE.md",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "GOVERNANCE_DECISION",
        "defect_addressed": "T69",
        "rational_justification": "PI determination governing three-tier release partition to ensure open science without copyright risk"
    },
    {
        "artifact_path": "results/120_.../release/contents_inventory_120.json",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "THREE_TIER_INVENTORY",
        "defect_addressed": "T69",
        "rational_justification": "Structured catalog mapping public, submission, and restricted assets to access permissions and hashes"
    },
    {
        "artifact_path": "results/120_.../audit/independent_science_review_120.md",
        "change_type": "ADDED",
        "stage119_reference": "T119_INDEPENDENT_REVIEW.md",
        "stage120_status": "INTERNAL_AUDIT_REPORT",
        "defect_addressed": "T70",
        "rational_justification": "Internal pre-submission scientific audit with dual reviewer perspectives, disclaiming external journal verdict"
    },
    {
        "artifact_path": "results/120_.../audit/semantic_consistency_120.json",
        "change_type": "ADDED",
        "stage119_reference": "publication_consistency_119.json",
        "stage120_status": "JOINT_SEMANTIC_VALIDATOR",
        "defect_addressed": "T70",
        "rational_justification": "Joint parameter, symbol, and hypothesis validator preventing semantic conflation across documents"
    },
    {
        "artifact_path": "results/120_.../release/local_submission_sources_120.zip",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "TESTED_SUBMISSION_ZIP (1,313,485 bytes)",
        "defect_addressed": "T71",
        "rational_justification": "Pristine LaTeX source bundle verified via isolated clean-room compilation in temporary directory"
    },
    {
        "artifact_path": "results/120_.../publication_gates/FINAL_STAGE_GATE_120.json",
        "change_type": "ADDED",
        "stage119_reference": "FINAL_STAGE_GATE_119.json",
        "stage120_status": "SEVEN_GATE_LEDGER",
        "defect_addressed": "T71",
        "rational_justification": "Separated seven stage gates with explicit BLOCKED_PENDING_HUMAN_ACTION for external submission"
    },
    {
        "artifact_path": "results/120_.../publication_gates/PI_HANDOFF_CHECKLIST_120.md",
        "change_type": "ADDED",
        "stage119_reference": "NONE",
        "stage120_status": "ONE_PAGE_CHECKLIST",
        "defect_addressed": "T72",
        "rational_justification": "One-page actionable checklist enabling PI to review and sign off before manual SuSy portal submission"
    }
]

out_csv = r'd:\_Work\goat_bank\uir\projects\uir_base\results\120_electronics_release_closure_2026_10_24\audit\final_archive_diff_120.csv'
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print(f'Wrote {len(rows)} diff rows to {out_csv}')
