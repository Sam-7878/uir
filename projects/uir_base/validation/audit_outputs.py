"""R07/R14 independent channel counts, delivery integrity and reviewer scope."""
from collections import Counter
import csv
import json
import zipfile
from .common import DOC, OLD, OUT, ROOT, csvfile, load, read, sha, write


def run():
    delivery = ROOT / "docs/work_reports/uir_base/110_mdpi_rev/110_mdpi_rev.zip"
    expected = "007ae2715abb8a996d6376d5786d529d19608c7857769a5f2d7214ffe2e5b3e8"
    if sha(delivery) != expected: raise ValueError("DELIVERY_ZIP_HASH_MISMATCH")
    with zipfile.ZipFile(delivery) as archive:
        duplicates = len(archive.namelist()) != len(set(archive.namelist()))
    if duplicates: raise ValueError("DUPLICATE_DELIVERY_ENTRY")
    write(OUT / "delivery_zip_verification.json", {"path": str(delivery.relative_to(ROOT)), "sha256": expected, "status": "PASS",
                                                 "initial_missing_input_resolved_by_user": True})
    raw = read(OUT / "dev_matched_raw.jsonl")
    rows = []
    for condition in {r["condition"] for r in raw}:
        group = [r for r in raw if r["condition"] == condition]
        assessed = 0; errors = 0
        for record in group:
            result = record["accepted_output"]; text = result["accepted_rendered_text"]
            if not text: continue
            output = json.loads(text); assessed += 1
            if output["claims"] != result["accepted_claims"]: errors += 1
        nonempty = sum(bool(r["accepted_output"]["accepted_claims"]) for r in group)
        rows.append({"condition": condition, "N_requests": len(group), "N_nonempty_accepted": nonempty,
                     "N_bound_json_output_assessed": assessed, "N_renderer_channel_mismatch": errors,
                     "native_prose_AUCR": "NOT_MEASURED", "structured_accepted_unsupported_N": 0,
                     "full_output_assessment_scope": "JSON bound claims only, no open prose; relative to synthetic trusted catalog",
                     "complete": sum(r["accepted_output"]["state"] == "FULL_VERIFIED_ANSWER" for r in group),
                     "partial": sum(r["accepted_output"]["state"] == "PARTIAL_VERIFIED_ANSWER" for r in group),
                     "none": sum(r["accepted_output"]["state"] == "NO_VERIFIED_ANSWER" for r in group),
                     "early_policy_or_clarification": sum(r["accepted_output"]["state"] not in {"FULL_VERIFIED_ANSWER", "PARTIAL_VERIFIED_ANSWER", "NO_VERIFIED_ANSWER"} for r in group)})
    csvfile(OUT / "output_channel_metrics_vNext.csv", rows)
    registry = load(OUT / "frozen_review_registry.json")
    for name, digest in registry["files"].items():
        p = ROOT / name if name.startswith("projects/") else OLD / name if not name.startswith("/") else __import__("pathlib").Path(name)
        if sha(p) != digest: raise ValueError("FROZEN_REVIEW_MUTATED")
    review = load(OUT / "open_review_summary.json")
    csvfile(DOC / "reviewer_scope_matrix.csv", [
        {"cohort": "historical 120 cases / 240 responses", "truth": "no independent human semantic labels", "accuracy": "NOT_ESTABLISHED", "allowed_claim": "agreement/uncertainty only"},
        {"cohort": "synthetic v2 16 calibration + 16 holdout / 64 responses", "truth": "executable fixture rules", "accuracy": "synthetic rule accuracy only", "allowed_claim": "not human gold"},
        {"cohort": "new v3 open judgment 8 cases / 16 responses", "truth": "NONE", "accuracy": "NOT_MEASURED", "allowed_claim": "agreement/uncertainty; no majority tie resolution"},
    ])
    write(OUT / "output_audit_summary.json", {"delivery": "PASS", "N_repr_raw_records": len(raw),
          "N_open_review_responses": review["N_responses"], "N_open_review_valid": review["N_valid"],
          "human_validation": False, "original_W08": "NOT_SATISFIED", "author_institution_signoff": False})


if __name__ == "__main__": run()
