"""Bounded read-only retrieval of source/rights candidates, never automatic gold.

Downloaded content is untrusted data and is not executed or used as instructions.
Neither a fetched license page nor two families certify a confirmatory dataset.
"""
import hashlib
import json
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

from ..policy import utc

ALLOWED_HOSTS = {"api.worldbank.org", "datacatalog.worldbank.org", "api.github.com", "raw.githubusercontent.com", "www.mdpi.com",
                 "api.fiscaldata.treasury.gov", "catalog.data.gov"}


def fetch(store, name, url, *, family, role, license_status):
    if urlsplit(url).scheme != "https" or urlsplit(url).hostname not in ALLOWED_HOSTS:
        raise ValueError("UNAPPROVED_PUBLIC_SOURCE_HOST")
    record = {"source_id": name, "source_uri": url, "retrieved_at_utc": utc(), "parent_source_family": family,
              "role": role, "license_status": license_status, "rights_class": "PRIVATE", "split": "SOURCE_CANDIDATE_NOT_CONFIRMATORY"}
    try:
        request = Request(url, headers={"User-Agent": "UIR-Research-SourceAudit/116", "Accept": "application/json,text/plain,text/html"})
        with urlopen(request, timeout=40) as response:
            if urlsplit(response.url).hostname not in ALLOWED_HOSTS:
                raise ValueError("UNAPPROVED_REDIRECT")
            data = response.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("SOURCE_TOO_LARGE")
            record.update(http_status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"))
        path = "source_registry/bytes/" + name
        store.write(path, data)
        record.update(status="PHYSICAL_BYTES_VERIFIED", byte_count=len(data), sha256=hashlib.sha256(data).hexdigest(), relative_path=path)
    except Exception as exc:
        record.update(status="RETRIEVAL_FAILED", error_type=type(exc).__name__, http_status=getattr(exc, "code", None))
    return record


def acquire(store):
    records = []
    def get(name, url, family, role="RAW_SOURCE", license_status="RIGHTS_PENDING"):
        record = fetch(store, name, url, family=family, role=role, license_status=license_status)
        records.append(record)
        return record
    get("worldbank_licensing.html", "https://datacatalog.worldbank.org/public-licenses", "WorldBank:licensing", "LICENSE_PAGE", "DEFAULT_CC_BY_4_WITH_ADDITIONAL_TERMS_DATASET_SPECIFIC_REVIEW_PENDING")
    get("wdi_indicator_metadata.json", "https://api.worldbank.org/v2/indicator/NY.GDP.MKTP.CD?format=json", "WorldBank:WDI", "INDICATOR_METADATA")
    get("wdi_gdp_KOR_USA_DEU_2020_2023.json", "https://api.worldbank.org/v2/country/KOR;USA;DEU/indicator/NY.GDP.MKTP.CD?date=2020:2023&format=json&per_page=100", "WorldBank:WDI")
    commit = get("cargo_commit.json", "https://api.github.com/repos/rust-lang/cargo/commits/master", "GitHub:rust-lang/cargo", "REVISION_METADATA")
    if commit["status"] == "PHYSICAL_BYTES_VERIFIED":
        revision = json.loads(store.path(commit["relative_path"]).read_text())["sha"]
        if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
            raise ValueError("INVALID_SOURCE_REVISION")
        base = "https://raw.githubusercontent.com/rust-lang/cargo/" + revision
        for name, role in (("Cargo.toml", "RAW_SOURCE"), ("LICENSE-MIT", "LICENSE_TEXT"), ("LICENSE-APACHE", "LICENSE_TEXT")):
            item = get("cargo_" + name, base + "/" + name, "GitHub:rust-lang/cargo", role, "MIT_OR_APACHE_2_CANDIDATE_ATTRIBUTION_REVIEW_PENDING")
            item["source_revision"] = revision
    get("electronics_special_issue.html", "https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X", "MDPI:WFBEQFE47X", "JOURNAL_LIVE_CHECK", "NOT_FOR_REDISTRIBUTION")
    store.write("source_registry/source_bytes_manifest_116.json", {"records": records, "all_files_default": "PRIVATE",
        "automatically_confirmatory": False, "source_selection_by": "IMPLEMENTING_AGENT", "not_independent_gold": True})
    source_records = [r for r in records if r["role"] == "RAW_SOURCE"]
    return {"physical_source_families": sorted({r["parent_source_family"] for r in source_records if r["status"] == "PHYSICAL_BYTES_VERIFIED"}),
            "status": "SOURCE_CANDIDATES_ONLY", "records": records, "confirmatory_gate": "BLOCKED_NO_BLIND_GOLD_OR_RAW_QUERY_FAMILY_SIGNOFF"}
