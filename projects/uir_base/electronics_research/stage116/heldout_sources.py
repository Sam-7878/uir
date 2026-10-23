"""Blind source reserve from published crate archives; never executes package code.

Rate-limited public reads, bounded gzip/tar parsing, permissive-license metadata,
one source per GitHub owner (conservative parent cluster), no pilot publishers.
This prepares source bytes only; it does not itself certify confirmation.
"""
import argparse
import gzip
from io import BytesIO
import json
import re
import tarfile
import time
import tomllib
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .artifacts import RunStore
from ..policy import sha, utc, write_once, ROOT
from .runner import DOCS

HEADERS = {"User-Agent": "UIR116-SourceReserve/1 (https://github.com/Sam-7878/uir)", "Accept": "application/json,application/octet-stream"}


def reserve(directory, target=60, complete_frame_from=None):
    store = RunStore(directory)
    store.create()
    cached_store = RunStore(complete_frame_from) if complete_frame_from else None
    if cached_store:
        cached_store.verify()
    cached = {r["source_id"]: r for r in json.loads(cached_store.path("source_registry/reserve_manifest.json").read_text())["records"]} if cached_store else {}
    store.write("preregistration/source_acquisition_plan.json", {"created_at_utc": utc(), "status": "FROZEN_SOURCE_ACQUISITION_ONLY_NOT_INFERENCE_PREREGISTRATION",
                "target_parent_clusters": target, "planned_cases_per_parent": 4, "planned_total_cases": target * 4,
                "parent_cluster": "github_repository_owner_conservative_NOT_package_or_version_count",
                "selection_frame": "crates.io downloads-ranked first500, first eligible owner wins; deterministic convenience sample",
                "excluded_pilot_publishers": ["rust-lang", "US-Treasury"], "accepted_license_expressions": ["MIT", "Apache-2.0", "MIT OR Apache-2.0", "MIT/Apache-2.0", "Apache-2.0 OR MIT"],
                "max_api_requests_per_second": 1, "execute_or_install_downloaded_packages": False,
                "source_values_viewed_by_runtime_model": False, "package_training_contamination": "NOT_ASSESSED",
                "precision_rationale": "At60 independent cluster units and zero cluster failures, one-sided exact95 upper=1-.05**(1/60)=.0487; conditional Bernoulli assumption, not random-sample population guarantee.",
                "confirmation_gate": "INFERENCE_PROTOCOL_METHOD_REVIEW_QUERY_GOLD_ISOLATION_RIGHTS_AND_TEMPLATE_DISJOINTNESS_STILL_REQUIRED"})
    if cached_store:
        store.write("preregistration/frame_completion_amendment_before_outcomes.json", {"version": "FRAME_V2", "prior_source_checkpoint": str(cached_store.directory),
                    "full_frame": "ALL_ELIGIBLE_OWNERS_FIRST500_RANKED_ENTRIES_NOT_FIRST60", "runtime_outcomes_observed": 0,
                    "reason": "Method review rejected independence assumption. Complete fixed finite frame before a seeded SRSWOR design-based primary trial.",
                    "source_values_used_for_sampling": False, "prior_failed_method_preserved": "run_20261023T093051Z"})
    records, failures, owners = [], [], {"rust-lang"}
    last = [0.0]
    def get(url, limit):
        host = urlsplit(url).hostname
        if host not in {"crates.io", "static.crates.io"}:
            raise ValueError("UNAPPROVED_PACKAGE_SOURCE_HOST")
        pause = 1.05 - (time.monotonic() - last[0])
        if pause > 0: time.sleep(pause)
        last[0] = time.monotonic()
        with urlopen(Request(url, headers=HEADERS), timeout=30) as response:
            if urlsplit(response.url).hostname not in {"crates.io", "static.crates.io"}:
                raise ValueError("UNAPPROVED_PACKAGE_REDIRECT")
            data = response.read(limit + 1)
        if len(data) > limit: raise ValueError("SOURCE_RESOURCE_LIMIT")
        return data
    for page in range(1, 6):
        try:
            cached_page = cached_store.path(f"source_registry/catalog_page_{page}.json") if cached_store else None
            raw = cached_page.read_bytes() if cached_page and cached_page.is_file() else get(f"https://crates.io/api/v1/crates?page={page}&per_page=100&sort=downloads", 2 * 1024 * 1024)
            store.write(f"source_registry/catalog_page_{page}.json", raw)
            entries = json.loads(raw)["crates"]
        except Exception as exc:
            failures.append({"catalog_page": page, "error": type(exc).__name__, "http_status": getattr(exc, "code", None)})
            break
        for item in entries:
            repository = item.get("repository") or ""
            match = re.match(r"https?://github\.com/([^/]+)/", repository, re.I)
            if not match or match[1].lower() in owners:
                continue
            owner = match[1].lower()
            name, version = item["id"], item.get("max_stable_version") or item.get("max_version")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", name) or not version or not re.fullmatch(r"[0-9A-Za-z.+_-]+", version):
                continue
            url = f"https://static.crates.io/crates/{name}/{name}-{version}.crate"
            previous = cached.get(name)
            if previous and previous["version"] == version and previous["parent_family"] == "github-owner:" + owner:
                previous = dict(previous)
                previous["manifest_ref"] = str(cached_store.path(previous["manifest_path"]).relative_to(ROOT))
                previous["license_refs"] = [str(cached_store.path(p).relative_to(ROOT)) for p in previous["license_texts"]]
                if sha(ROOT / previous["manifest_ref"]) != previous["manifest_sha256"]:
                    raise ValueError("CACHED_SOURCE_HASH_CHANGED")
                records.append(previous)
                owners.add(owner)
                continue
            try:
                package_bytes = get(url, 8 * 1024 * 1024)
                with gzip.GzipFile(fileobj=BytesIO(package_bytes)) as stream:
                    unpacked = stream.read(16 * 1024 * 1024 + 1)
                if len(unpacked) > 16 * 1024 * 1024: raise ValueError("DECOMPRESSED_SIZE_LIMIT")
                with tarfile.open(fileobj=BytesIO(unpacked), mode="r:") as archive:
                    members = archive.getmembers()
                    if len(members) > 5000: raise ValueError("ARCHIVE_MEMBER_LIMIT")
                    member = next(m for m in members if m.name == f"{name}-{version}/Cargo.toml")
                    if not member.isfile() or member.size > 128 * 1024: raise ValueError("UNSAFE_MANIFEST_MEMBER")
                    manifest_bytes = archive.extractfile(member).read()
                    manifest = tomllib.loads(manifest_bytes.decode())
                    package = manifest["package"]
                    license_expression = package.get("license", "")
                    if license_expression not in {"MIT", "Apache-2.0", "MIT OR Apache-2.0", "MIT/Apache-2.0", "Apache-2.0 OR MIT"}:
                        raise ValueError("LICENSE_EXPRESSION_NOT_IN_ACCEPTED_SET")
                    license_members = [m for m in members if m.isfile() and "/" not in m.name.split("/", 1)[1] and
                                       m.name.split("/", 1)[1].upper().startswith(("LICENSE", "COPYING")) and m.size <= 128 * 1024]
                    if not license_members: raise ValueError("NO_BUNDLED_LICENSE_TEXT")
                    prefix = "source_registry/parents/" + owner + "__" + name + "/"
                    store.write(prefix + "Cargo.toml", manifest_bytes)
                    for i, member in enumerate(license_members):
                        store.write(prefix + f"license_{i}.txt", archive.extractfile(member).read())
                # No archive extraction to filesystem and no downloaded program execution.
                records.append({"source_id": name, "version": version, "parent_family": "github-owner:" + owner,
                                "repository": repository, "source_uri": url, "retrieved_at_utc": utc(), "license": license_expression,
                                "manifest_path": prefix + "Cargo.toml", "manifest_sha256": sha(store.path(prefix + "Cargo.toml")),
                                "manifest_ref": str(store.path(prefix + "Cargo.toml").relative_to(ROOT)),
                                "license_refs": [str(store.path(prefix + f"license_{i}.txt").relative_to(ROOT)) for i in range(len(license_members))],
                                "license_texts": [prefix + f"license_{i}.txt" for i in range(len(license_members))],
                                "rights_class": "PRIVATE", "split": "BLIND_SOURCE_RESERVE_NOT_ASSIGNED_CONFIRMATORY", "model_observations": 0})
                owners.add(owner)
                print(json.dumps({"phase": "heldout_source_reserve", "parent_clusters": len(records), "target": target}), flush=True)
            except Exception as exc:
                failures.append({"source_id": name, "parent_family": "github-owner:" + owner, "error": type(exc).__name__, "http_status": getattr(exc, "code", None)})
            if not cached_store and len(records) >= target: break
        if not cached_store and len(records) >= target: break
    store.write("source_registry/reserve_manifest.json", {"records": records, "failures": failures, "actual_parent_clusters": len(records),
                "target": "ALL_ELIGIBLE_FIRST500_FRAME" if cached_store else target, "pilot_owner_overlap": False, "semantic_gold_exists": False, "queries_exist": False,
                "confirmatory_eligibility": "PENDING_ROLE_CURATORS_TEMPLATE_DISJOINTNESS_OS_AND_FULL_METHOD_FREEZE"})
    report = DOCS / ("HELDOUT_SOURCE_RESERVE_" + store.directory.name + ".md")
    write_once(report, "# New held-out source reserve\n\n"
               f"Acquired {len(records)} distinct GitHub-owner source clusters from published crate manifests, with bundled license texts. "
               "No package program was installed/executed. Raw source values are not model observations. Source ranking/eligibility is frozen before collection. "
               "All candidates are software manifests, NOT new financial-domain validation or a random population sample. "
               "No query/gold cases or confirmatory outcomes exist yet. This reserve must go through role-separated curation, template disjointness, isolation and a new method freeze before inference. "
               "Pilot publishers are excluded and observed pilot requests will not be promoted. Rights apply per source, public redistribution still needs owner review.\n")
    store.write("work_report_lineage.json", {str(report.relative_to(ROOT)): sha(report)})
    store.write("README.md", "# LOCAL ONLY blind source reserve\n\nNever equate source bytes with a validated confirmatory dataset. No model observations or queries yet.\n")
    store.seal()
    print(json.dumps({"run": str(store.directory), "parent_clusters": len(records), "verified_files": store.verify(), "confirmation": "PENDING"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=__import__("pathlib").Path, required=True)
    parser.add_argument("--complete-frame-from", type=__import__("pathlib").Path)
    args = parser.parse_args()
    reserve(args.results_dir, complete_frame_from=args.complete_frame_from)
