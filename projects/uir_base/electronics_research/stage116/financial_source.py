"""One bounded alternative after retained WDI timeouts, without fabricating gold."""
import argparse
from decimal import Decimal
import json
from pathlib import Path

from ..policy import ROOT, sha, write_once
from .artifacts import RunStore
from .runner import DOCS
from .sources import fetch


def run(directory, prior_directory):
    prior = RunStore(prior_directory)
    prior.verify()
    store = RunStore(directory)
    store.create()
    metadata = fetch(store, "treasury_datagov_metadata.json", "https://catalog.data.gov/api/3/action/package_show?id=debt-to-the-penny",
                     family="US-Treasury:DebtToPenny", role="DATASET_RIGHTS_METADATA", license_status="DATASET_LICENSE_FIELD_PENDING")
    raw = fetch(store, "treasury_debt_2024_first5.json",
                "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?format=json&page%5Bsize%5D=5&sort=record_date&filter=record_date:gte:2024-01-01",
                family="US-Treasury:DebtToPenny", role="RAW_SOURCE", license_status="US_GOVERNMENT_DATA_CANDIDATE_OWNER_RIGHTS_SIGNOFF_PENDING")
    license_fields = {}
    if metadata["status"] == "PHYSICAL_BYTES_VERIFIED":
        value = json.loads(store.path(metadata["relative_path"]).read_text()).get("result", {})
        license_fields = {k: value.get(k) for k in ("license_id", "license_title", "license_url")}
    rows = []
    if raw["status"] == "PHYSICAL_BYTES_VERIFIED":
        body = json.loads(store.path(raw["relative_path"]).read_text())
        rows = body.get("data", [])
        if not rows or len(rows) > 5:
            raise ValueError("TREASURY_RESPONSE_NOT_A_BOUNDED_FIVE_ROW_SOURCE")
        for row in rows:
            for key in ("debt_held_public_amt", "intragov_hold_amt", "tot_pub_debt_out_amt"):
                if not Decimal(row[key]).is_finite():
                    raise ValueError("INVALID_SOURCE_DECIMAL")
    previous = json.loads(prior.path("source_registry/T17_gate.json").read_text())
    families = set(previous["physical_source_families"])
    if rows:
        families.add("US-Treasury:DebtToPenny")
    store.write("source_registry/source_registry_116.json", {"records": [metadata, raw], "explicit_license_fields": license_fields,
                "bounded_raw_rows": len(rows), "physical_source_families": sorted(families),
                "physical_sources_not_independent_gold": True, "rights_release_approval": "PENDING"})
    store.write("prior_checkpoint.json", {"path": str(prior.directory.relative_to(ROOT)), "manifest_sha256": sha(prior.path("evidence_manifest.json")),
                "old_failures_retained": True})
    store.write("code_snapshot.json", {str(p.relative_to(ROOT)): sha(p) for p in Path(__file__).parent.glob("*.py")})
    store.write("publication_gates/final_stage_gate_116.json", {"ENGINEERING_CONFORMANCE_READY": "SEE_PRIOR_REGRESSION_NOT_RERUN_HERE",
                "CONFIRMATORY_EVIDENCE_READY": "BLOCKED_INDEPENDENT_QUERY_GOLD_FAMILY_OS_ISOLATION_AND_PRECISION",
                "MANUSCRIPT_READY": "BLOCKED", "PUBLIC_RELEASE_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED", "model_calls": 0})
    report = DOCS / ("T_STAGE_116_FINANCIAL_SOURCE_" + store.directory.name + ".md")
    write_once(report, "# Financial source acquisition checkpoint\n\n"
               f"Actual raw source status: {raw['status']}; bounded rows: {len(rows)}; physical candidate families: {sorted(families)}. "
               f"Official catalog license fields: `{license_fields}`. Metadata is candidate rights evidence, not owner redistribution approval. "
               "WDI failed requests remain immutable. No source row was promoted into a query/gold case or supplied to a model. "
               "Independent curation/gold role separation, family/template overlap certification, runtime gold OS isolation and precision/method review still block T17/T18. "
               "Two available raw sources do not automatically authorize confirmatory inference. Current scientific stop rule remains in force; no manuscript or submission package was produced.\n")
    store.write("work_report_lineage.json", {str(report.relative_to(ROOT)): sha(report)})
    store.write("README.md", "# LOCAL ONLY source-candidate checkpoint\n\nRaw public source and catalog rights metadata; not a confirmatory dataset or authorized public release.\n")
    store.seal()
    print(json.dumps({"verified_files": store.verify(), "physical_source_families": sorted(families), "raw_rows": len(rows), "raw_status": raw["status"], "results_dir": str(store.directory)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--prior-run", type=Path, required=True)
    args = parser.parse_args()
    run(args.results_dir, args.prior_run)
