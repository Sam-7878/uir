"""A new immutable checkpoint: bounded retrieval retry and current-source QA.

Never modifies/reseals the original checkpoint or recasts its failed retrieval.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

from ..policy import ROOT, sha, utc, write_once
from .artifacts import RunStore
from .runner import DOCS, command, semantic_regression
from .sources import fetch


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def run(directory, prior_directory, network=False):
    prior = RunStore(prior_directory)
    verified = prior.verify()
    store = RunStore(directory)
    store.create()
    store.write("prior_checkpoint.json", {"path": str(prior.directory.relative_to(ROOT)), "verified_files": verified,
                "manifest_sha256": sha(prior.path("evidence_manifest.json")), "frozen_prior_unchanged": True})
    paths = sorted(Path(__file__).parent.glob("*.py")) + [ROOT / "tests/uir_base/test_stage116.py"]
    store.write("code_snapshot.json", {str(p.relative_to(ROOT)): sha(p) for p in paths})
    record = fetch(store, "wdi_gdp_KOR_2020_2023.json",
                   "https://api.worldbank.org/v2/country/KOR/indicator/NY.GDP.MKTP.CD?date=2020:2023&format=json&per_page=10",
                   family="WorldBank:WDI", role="RAW_SOURCE", license_status="CC_BY_4_DEFAULT_DATASET_SPECIFIC_REVIEW_PENDING") if network else {"status": "NOT_EXECUTED"}
    store.write("source_registry/retrieval_retry_receipt.json", record)
    families = set(json.loads(prior.path("source_registry/T17_gate.json").read_text())["physical_source_families"])
    observations = 0
    if record["status"] == "PHYSICAL_BYTES_VERIFIED":
        body = json.loads(store.path(record["relative_path"]).read_text())
        if (not isinstance(body, list) or len(body) != 2 or not isinstance(body[1], list)
                or any(r.get("indicator", {}).get("id") != "NY.GDP.MKTP.CD" or r.get("countryiso3code") != "KOR" for r in body[1])):
            raise ValueError("SOURCE_RESPONSE_SCHEMA_MISMATCH")
        families.add("WorldBank:WDI")
        observations = sum(r.get("value") is not None for r in body[1])
    store.write("source_registry/T17_gate.json", {"physical_source_families": sorted(families), "WDI_nonnull_observations": observations,
                "status": "PARTIAL_PHYSICAL_SOURCES_NOT_INDEPENDENT_QUERY_GOLD_DATASET", "source_only_not_confirmatory": True,
                "source_family_overlap": "NOT_CERTIFIED", "query_template_disjoint": "NOT_CERTIFIED", "independent_gold": "NOT_CREATED",
                "gold_runtime_OS_isolation": "NOT_EXECUTED", "confirmation_allowed": False})
    page = prior.path("source_registry/bytes/electronics_special_issue.html")
    if page.is_file():
        parser = VisibleText()
        parser.feed(page.read_text(errors="replace"))
        text = " ".join(" ".join(parser.parts).split())
        checks = {"target_title_present": "Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems" in text,
                  "deadline_15_February_2027_present": "15 February 2027" in text,
                  "editor_Geunseok_Yang_present": "Geunseok Yang" in text,
                  "APC_2400_CHF_text_present": bool(re.search(r"(?:2400\s*CHF|CHF\s*2400|2,400\s*CHF)", text))}
        store.write("publication_gates/electronics_SI_live_check_116.json", {"source_uri": "https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X",
                    "retrieved_in_prior_checkpoint": True, "source_sha256": sha(page), "actual_html_text_checks": checks,
                    "portal_login_open_submission_or_discount_verified": False, "submission_authorized": False,
                    "note": "Primary page bytes were fetched HTTP200 by the local client, despite the separate browsing service returning429. Text presence is not portal eligibility certification."})
    sem = semantic_regression(store)
    rc = command(store, "full_python_tests", [sys.executable, "-m", "pytest", "-q",
                 "--junitxml=" + str(store.path("publication_gates/full_python_tests.xml"))], timeout=180)
    store.write("publication_gates/final_stage_gate_116.json", {"ENGINEERING_CONFORMANCE_READY": "PASS_SCOPED_REGRESSION_ONLY" if rc == 0 and sem["status"] == "PASS_SCOPED_REGRESSION" else "BLOCKED_TEST_FAILURES",
                "CONFIRMATORY_EVIDENCE_READY": "BLOCKED", "MANUSCRIPT_READY": "BLOCKED", "PUBLIC_RELEASE_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED",
                "inference_calls": 0, "source_families": sorted(families), "history_remediation": "UNRESOLVED_OWNER_ACCEPTED_LIMITATION"})
    report_path = DOCS / ("T_STAGE_116_FOLLOWUP_" + store.directory.name + ".md")
    report = ("# Stage 116 follow-up — PARTIAL / scientific stop rule\n\n"
              f"New immutable run: `{store.directory.relative_to(ROOT)}`. Prior checkpoint verified {verified} files and remains unchanged.\n\n"
              f"Physical candidate source families: {sorted(families)}; WDI non-null observations acquired in this retry: {observations}. "
              "The first multi-country timeout is retained. These source bytes are not a blind question/gold dataset. Rights, family/template disjointness, independent gold role separation, runtime gold OS isolation and precision signoff remain incomplete. "
              "No confirmatory or other model calls. Pilot24/confirmation200 not fabricated. T18–T23 confirmatory evaluation is blocked by T17; finite historical/adapter regression is separate.\n\n"
              f"Current-source full Python returncode={rc}. See the XML/log for actual passed/failed/skipped counts, and semantics receipt for 41/22 regression/5 transport checks. "
              "New interchange validation and tests were added after the first run's source snapshot; this fresh run records their current hashes and reruns checks. "
              "Rustfmt failure remains recorded in the prior checkpoint; no broad format rewrite or source/layout move was performed.\n\n"
              "The official Special Issue page was obtained as HTTP200 via the local read-only client. Parsed text-presence checks are retained; no logged-in portal, APC waiver, author/rights or submission approval is inferred. "
              "No article/PDF, independent final review, public or submission archive was manufactured while science prerequisites are blocked.\n\n"
              "## Direction required\n\nProvide an isolated request/gold curation/review source and certify family/template disjointness and gold access isolation, "
              "or explicitly authorize a finite typed-contract conformance and bounded acceptance-control engineering-study scope. "
              "AI-only Route B and LOCAL ONLY remain in force; they are not human gold or automatic confirmation.\n")
    write_once(report_path, report)
    store.write("work_report_lineage.json", {str(report_path.relative_to(ROOT)): sha(report_path)})
    store.write("README.md", "# LOCAL ONLY Stage116 follow-up\n\nSource candidates and current-source QA only. Confirmatory, manuscript, public release and submission remain BLOCKED.\n")
    manifest = store.seal()
    print(json.dumps({"results_dir": str(store.directory), "manifest_sha256": manifest, "verified_files": store.verify(),
                      "source_families": sorted(families), "full_python_returncode": rc, "report": str(report_path)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--prior-run", type=Path, required=True)
    parser.add_argument("--network", action="store_true")
    args = parser.parse_args()
    run(args.results_dir, args.prior_run, args.network)
