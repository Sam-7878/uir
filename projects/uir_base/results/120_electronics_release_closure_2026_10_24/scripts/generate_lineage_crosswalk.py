import os
import hashlib
import csv

base_dir = '/mnt/d/_Work/goat_bank/uir'
lineage_entries = [
    ('Primary Evaluation Frame', 'Stage 116', 'projects/uir_base/results/116_electronics_confirmatory_2026_10_23/raw_evaluation_records_116.jsonl', 'M=82 convenience frame definition and 240 primary records'),
    ('Exact Statistical Recompute', 'Stage 117', 'projects/uir_base/results/117_electronics_evidence_closure_2026_10_23/audit/independent_recompute_117.json', 'Hypergeometric p=0.0009651338 (K=5), upper bound K<=2'),
    ('Factorial Attribution Matrix', 'Stage 117', 'projects/uir_base/results/117_electronics_evidence_closure_2026_10_23/audit/factorial_2x2x2_117.csv', 'N=1,920 factorial outcome rows across 8 conditions C1-C8'),
    ('Claim Semantic Contract', 'Stage 118', 'projects/uir_base/results/118_electronics_submission_remediation_2026_10_23/claim_audit/claim_semantics_audit_118.csv', 'Line-by-line claim classification and negative boundary definitions'),
    ('Manuscript Remediation Tree', 'Stage 118', 'projects/uir_base/paper/mdpi_electronics_118/main.tex', 'Generic IEEE LaTeX manuscript drafting stage'),
    ('Official MDPI LaTeX Source', 'Stage 119', 'projects/uir_base/paper/mdpi_electronics_119/main.tex', 'Official Definitions/mdpi.cls 15-page manuscript source'),
    ('Official MDPI Compiled PDF', 'Stage 119', 'projects/uir_base/paper/mdpi_electronics_119/main.pdf', '15-page clean-room PDF compilation artifact'),
    ('Submission Package ZIP', 'Stage 119', 'projects/uir_base/results/119_electronics_final_submission_2026_10_23/release/local_submission_sources_119.zip', '18-file submission archive for SuSy upload'),
    ('Refined MDPI LaTeX Source', 'Stage 120', 'projects/uir_base/paper/mdpi_electronics_120/main.tex', 'Stage 120 expanded manuscript source tree'),
    ('Refined MDPI Compiled PDF', 'Stage 120', 'projects/uir_base/paper/mdpi_electronics_120/main.pdf', 'Stage 120 compiled PDF artifact')
]

out_csv = '/mnt/d/_Work/goat_bank/uir/projects/uir_base/results/120_electronics_release_closure_2026_10_24/audit/lineage_crosswalk_120.csv'
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['artifact_concept', 'origin_stage', 'relative_path', 'byte_size', 'sha256', 'lineage_function'])
    for concept, stage, path, desc in lineage_entries:
        abs_p = os.path.join(base_dir, path)
        size = os.path.getsize(abs_p) if os.path.exists(abs_p) else 'PENDING'
        digest = 'PENDING'
        if os.path.exists(abs_p):
            with open(abs_p, 'rb') as fp:
                digest = hashlib.sha256(fp.read()).hexdigest()
        writer.writerow([concept, stage, path, size, digest, desc])

print(f'Generated {out_csv}')
