"""Local-only, write-once results and explicit publication gates (T01/T12/T14)."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[3]
RESULTS_PREFIX = Path("projects/uir_base/results/uir_electronics_T_2026_10_13_v1")
RUN_PATTERN = re.compile(r"run_\d{8}T\d{6}Z(?:_[a-f0-9]{8})?")
SI = {"journal": "Electronics", "special_issue_code": "WFBEQFE47X",
      "special_issue": "Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems",
      "url": "https://www.mdpi.com/journal/electronics/special_issues/WFBEQFE47X",
      "announced_deadline": "2027-02-15", "live_portal_certified": False}

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("UNSAFE_RELATIVE_PATH")
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("UNSAFE_RELATIVE_PATH")
    return p

def protected_path(value):
    path = str(safe_relative(value)).lower()
    parts = PurePosixPath(path).parts
    if path.startswith(str(RESULTS_PREFIX).lower() + "/"):
        return True  # Entire new evidence tree defaults PRIVATE, even candidates.
    if "work_reports" in parts or "manuscript_private" in parts or path.startswith("docs/papers/"):
        return True
    if any(p.startswith("private_") or p in {"evaluator_only", "gold_boundary_v2"} for p in parts):
        return True
    if "results" in parts and any(word in parts[-1] for word in
            ("gold", "fresh_model_raw", "raw_prompt", "review_package", "renderer_bound_raw")):
        return True
    return path.endswith((".zip", ".pem", ".key", ".gguf", ".safetensors"))

def validate_results_dir(path, root=ROOT):
    path, root = Path(path).absolute(), Path(root).absolute()
    try:
        rel = path.relative_to(root / RESULTS_PREFIX)
    except ValueError as exc:
        raise ValueError("RESULTS_OUTSIDE_T_PREFIX") from exc
    if len(rel.parts) != 1 or not RUN_PATTERN.fullmatch(rel.name):
        raise ValueError("FRESH_RUN_DIRECTORY_REQUIRED")
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("SYMLINK_RESULTS_FORBIDDEN")
        if part == root:
            break
    if path.resolve() != path:
        raise ValueError("NONCANONICAL_RESULTS_PATH")
    return path

def write_once(path, value):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("SYMLINK_OUTPUT_FORBIDDEN")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

def seal(directory):
    directory = validate_results_dir(directory)
    records = {}
    for p in sorted(directory.rglob("*")):
        if p.is_symlink():
            raise ValueError("SYMLINK_EVIDENCE_FORBIDDEN")
        if p.is_file():
            if p.name == "evidence_manifest.json":
                raise FileExistsError("SEALED_RUN_CANNOT_BE_RESEALED")
            records[str(p.relative_to(directory))] = {"sha256": sha(p), "rights_class": "PRIVATE",
                                                      "public_approved": False}
    if not records:
        raise ValueError("EMPTY_EVIDENCE_SCAN")
    write_once(directory / "evidence_manifest.json", {"files": records, "created_at_utc": utc(),
               "self_hash": "EXCLUDED_DETACHED_MANIFEST", "storage": "LOCAL_ONLY_NOT_GIT_PUBLIC"})

def verify_manifest(directory):
    directory = validate_results_dir(directory)
    manifest = json.loads((directory / "evidence_manifest.json").read_text())
    if not manifest.get("files"):
        raise ValueError("EMPTY_EVIDENCE_SCAN")
    for name, record in manifest["files"].items():
        safe_relative(name)
        p = directory / name
        if p.is_symlink() or not p.is_file() or sha(p) != record["sha256"]:
            raise ValueError("EVIDENCE_MISSING_OR_MODIFIED")
    if any(p.is_symlink() for p in directory.rglob("*")):
        raise ValueError("SYMLINK_EVIDENCE_FORBIDDEN")
    actual = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file() and p.name != "evidence_manifest.json"}
    if actual != set(manifest["files"]):
        raise ValueError("UNDECLARED_EVIDENCE")
    return len(actual)

def publication_gate(record):
    """Conservative status summary, not an approval or submission authorization.

    Only the evidence-backed final reviewer can certify readiness; caller-supplied
    PASS labels cannot open the submission gate.
    """
    required = ("ARCHIVE_INTEGRITY", "SCIENTIFIC_EVIDENCE", "GOLD_ISOLATION", "CONFIRMATORY",
                "PAPER_SCOPE", "MDPI_FORMAT", "RIGHTS", "REMOTE_PRIVACY", "AUTHOR_APPROVAL")
    return {**{k: record.get(k, "NOT_EXECUTED") for k in required},
            "SUBMISSION_READY": "BLOCKED"}

def check_public_allowlist(root, entries, *, approval=None):
    if (not approval or approval.get("owner_approved") is not True
            or not re.fullmatch(r"[a-f0-9]{64}", approval.get("approval_evidence_sha256", ""))):
        raise ValueError("NO_ACTUAL_PUBLICATION_APPROVAL")
    if not entries:
        raise ValueError("EMPTY_PUBLIC_ALLOWLIST")
    seen = set()
    for entry in entries:
        relative = str(safe_relative(entry["path"]))
        if relative in seen or protected_path(relative) or entry.get("rights_class") != "PUBLIC_APPROVED":
            raise ValueError("PROTECTED_OR_DUPLICATE_PUBLIC_FILE")
        seen.add(relative)
        path = Path(root) / relative
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError("PUBLIC_SYMLINK_FORBIDDEN")
        if path.is_symlink() or not path.resolve().is_relative_to(Path(root).resolve()) or sha(path) != entry["sha256"]:
            raise ValueError("PUBLIC_BYTE_BINDING_FAILED")
    return True
