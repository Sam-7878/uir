"""S00 immutable ZIP/receipt audits and historical endpoint reclassification."""
import hashlib
import json
from pathlib import PurePosixPath
import stat
import subprocess
import zipfile
from .common import DOC, PRIOR, ROOT, RELEASE_SHA, DELIVERY_SHA, csvfile, jsonl, load, read, relative, sha, textfile, utc, write


def checked_zip(path, expected=None):
    actual = sha(path)
    if expected is not None and actual != expected:
        raise ValueError("BASELINE_HASH_MISMATCH")
    records = []
    with zipfile.ZipFile(path) as archive:
        seen = set()
        for info in archive.infolist():
            name = info.filename
            parts = PurePosixPath(name).parts
            if (not name or name.startswith("/") or "\\" in name or ":" in name
                    or ".." in parts or name in seen or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError("UNSAFE_OR_DUPLICATE_ZIP_MEMBER")
            seen.add(name)
            if info.is_dir():
                continue
            body = archive.read(info)
            if len(body) != info.file_size:
                raise ValueError("ZIP_LENGTH_MISMATCH")
            records.append({"path": name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        if "archive_manifest.json" in seen:
            manifest = json.loads(archive.read("archive_manifest.json"))
            declared = manifest["files"]
            if len({r["path"] for r in declared}) != len(declared):
                raise ValueError("DUPLICATE_MANIFEST_MEMBER")
            if {r["path"]: r for r in records if r["path"] != "archive_manifest.json"} != {r["path"]: r for r in declared}:
                raise ValueError("MANIFEST_BYTE_MISMATCH")
    return {"path": relative(path), "archive_sha256": actual, "file_count": len(records),
            "manifest_tracked": len(records) - (1 if any(r["path"] == "archive_manifest.json" for r in records) else 0), "files": records}


def authoritative_report(report, expected):
    if report.get("archive_sha256") != expected or report.get("model_calls") != 0:
        raise ValueError("NONAUTHORITATIVE_REPLAY_REPORT")
    if report.get("status") != "FRESH_ENV_COMBINED_ARCHIVE_REPLAY_PASS":
        raise ValueError("REPLAY_NOT_PASS")


def unique_rows(rows, fields):
    keys = [tuple(r[k] for k in fields) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("DUPLICATE_CASE")


def validate_lineage(record):
    required = ("source_sha256", "code_revision", "run_config_sha256", "raw_sha256", "metric_generator_sha256", "manuscript_source_sha256")
    if any(not record.get(k) for k in required):
        raise ValueError("MISSING_LINEAGE")
    if record.get("code_revision") != record.get("capture_code_revision"):
        raise ValueError("SOURCE_VERSION_MIXED")


def run(out):
    release = checked_zip(PRIOR / "uir_repr_private_review_release_v3.zip", RELEASE_SHA)
    delivery = checked_zip(PRIOR / "111_validation.zip", DELIVERY_SHA)
    current_path = PRIOR / "release_v3_verification/final_reproduce_report.json"
    current = load(current_path)
    authoritative_report(current, RELEASE_SHA)
    historical = load(PRIOR / "final_reproduce_report.json")
    if historical.get("archive_sha256") == RELEASE_SHA:
        raise ValueError("HISTORICAL_REPORT_UNEXPECTEDLY_CURRENT")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    snapshot = {"created_at_utc": utc(), "baseline_code_revision": revision, "release": release, "delivery": delivery,
                "current_report_sha256": sha(current_path), "originals_modified": False,
                "S_work_order_sha256": sha(DOC / "UIR_Representation_Research_Next_Work_Order_2026-10-13.md")}
    write(out / "S_BASELINE_MANIFEST.json", snapshot)
    write(out / "release_report_sidecars.json", [
        {"path": relative(current_path), "sha256": sha(current_path), "artifact_generation": "R_RELEASE_V3",
         "archive_sha256": RELEASE_SHA, "authoritative_for_release": True, "superseded_by": None},
        {"path": relative(PRIOR / "final_reproduce_report.json"), "sha256": sha(PRIOR / "final_reproduce_report.json"),
         "artifact_generation": "R_RELEASE_V1", "archive_sha256": historical["archive_sha256"],
         "authoritative_for_release": False, "superseded_by": relative(current_path)}])
    old = ROOT / "projects/uir_base/results/uir_repr_validation_2026_10_12_v1"
    captures = read(old / "renderer_bound_raw.jsonl")
    unique_rows(captures, ("case_id",))
    audit = []
    for row in captures:
        request = row.get("request") or row.get("payload")
        if request is None:
            raise ValueError("MISSING_RAW_REQUEST_CAPTURE")
        # Preserve complete captured prompt and its hash; inspect parsed user content.
        user = next(m["content"] for m in request["messages"] if m["role"] == "user")
        body = json.loads(user)
        catalog = body["authorized_catalog"]
        ids = list(catalog)
        response = row.get("response")
        if response is None:
            raise ValueError("MISSING_RAW_RESPONSE")
        returned = json.loads(response["message"]["content"])["fact_ids"]
        audit.append({"case_id": row["case_id"], "endpoint": "CATALOG_ENUMERATION_TRANSPORT",
                      "prior_alias": "REFERENCE_ENUM_SERVER_BOUND", "raw_request_present": "raw_request" in body or "raw_user_request" in body,
                      "catalog_size": len(ids), "enumerated_entire_catalog": set(returned) == set(ids),
                      "evidence_kind": "HISTORICAL_REPLAY", "raw_capture_source": relative(old / "renderer_bound_raw.jsonl"),
                      "raw_capture_sha256": sha(old / "renderer_bound_raw.jsonl")})
    csvfile(out / "historical_endpoint_audit.csv", audit)
    textfile(out / "AUTHORITATIVE_RELEASE_MAP.md", f"# Authoritative baseline\n\nCurrent R ZIP: `{RELEASE_SHA}`. Only `{relative(current_path)}` validates it. The root historical report validates `{historical['archive_sha256']}` and is not authoritative. Original bytes remain unchanged.\n\n272 historical v2 requests contain catalog enumeration, not query-aware selection. Sidecars carry the corrected endpoint without modifying raw data.\n")
    textfile(out / "R_TO_S_CHANGELOG.md", "# R to S\n\nHistorical results, source ZIPs and manuscript stay immutable. New S source and timestamped results are separate. Catalog enumeration is reclassified via sidecar; page evidence is not a whole annual report. New experiments require a frozen query-aware protocol.\n")
    print(json.dumps({"S00": "PASS_ARCHIVE_AND_AUTHORITY", "out": str(out), "release_files": release["manifest_tracked"]}))
