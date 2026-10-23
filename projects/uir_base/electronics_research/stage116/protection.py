"""Conservative index-byte scanner; no sensitive content in returned findings.

This is a bounded accidental-inclusion guard, not a complete DLP detector.
Unknown binary formats and resource-exhausting/nested archives fail closed.
"""
from io import BytesIO
import json
import re
import subprocess
import zipfile

from ..policy import protected_path, sha, utc

MAX_BYTES = 2 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 100
SENSITIVE_KEYS = {"expected_ids", "expected_claims", "gold_program", "exe_ans", "gold_version", "raw_prompt", "api_key", "access_token", "private_key"}


def sensitive_structure(value):
    if isinstance(value, dict):
        return any(str(k).lower() in SENSITIVE_KEYS or sensitive_structure(v) for k, v in value.items())
    if isinstance(value, list):
        return any(sensitive_structure(v) for v in value)
    return False


def inspect_bytes(data, *, depth=0):
    if len(data) > MAX_BYTES:
        return ["OVERSIZE_NOT_INSPECTED"]
    if zipfile.is_zipfile(BytesIO(data)):
        if depth >= 3:
            return ["ARCHIVE_NESTING_LIMIT"]
        findings = []
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                members = archive.infolist()
                if len(members) > MAX_ARCHIVE_MEMBERS or sum(m.file_size for m in members) > MAX_BYTES:
                    return ["ARCHIVE_RESOURCE_LIMIT"]
                seen = set()
                for member in members:
                    if member.is_dir():
                        continue
                    if member.filename in seen:
                        findings.append("DUPLICATE_ARCHIVE_MEMBER")
                    seen.add(member.filename)
                    try:
                        if protected_path(member.filename): findings.append("PRIVATE_ARCHIVE_PATH")
                    except ValueError:
                        findings.append("UNSAFE_ARCHIVE_MEMBER")
                    if member.flag_bits & 1:
                        findings.append("ENCRYPTED_ARCHIVE_UNINSPECTED")
                    elif member.file_size <= MAX_BYTES:
                        findings.extend(inspect_bytes(archive.read(member), depth=depth + 1))
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
            findings.append("UNREADABLE_ARCHIVE")
        return sorted(set(findings))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return ["UNKNOWN_BINARY_NOT_INSPECTED"]
    if "-----BEGIN " in text and "PRIVATE KEY-----" in text:
        return ["PRIVATE_KEY_MATERIAL"]
    # Full JSON and each JSONL record, even when the filename claims to be text.
    candidates = [text] + text.splitlines()
    for candidate in candidates:
        try:
            if sensitive_structure(json.loads(candidate)):
                return ["SCORING_OR_SECRET_JSON_FIELDS"]
        except (ValueError, RecursionError):
            continue
    if "PRIVATE_REVIEW_ONLY" in text or "SCORING_ONLY_GOLD" in text:
        return ["PRIVATE_CONTENT_MARKER"]
    if re.search(r"(?im)^\s*(?:api_key|access_token|private_key)\s*[:=]\s*\S+", text):
        return ["SECRET_ASSIGNMENT_PATTERN"]
    return []


def scan_index(repository):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repository, timeout=60)
    names = [p for p in git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").decode().split("\0") if p]
    findings = []
    for name in names:
        reasons = []
        mode = git("ls-files", "-s", "--", name).decode().split()[0]
        if mode not in {"100644", "100755"}:
            reasons.append("NONREGULAR_INDEX_ENTRY")
        try:
            if protected_path(name): reasons.append("PROTECTED_INDEX_PATH")
        except ValueError:
            reasons.append("UNSAFE_INDEX_PATH")
        spec = ":" + name
        size = int(git("cat-file", "-s", spec))
        if size > MAX_BYTES:
            reasons.append("OVERSIZE_NOT_INSPECTED")
        else:
            reasons.extend(inspect_bytes(git("show", spec)))
        if reasons:
            findings.append({"path": name, "reasons": sorted(set(reasons))})
    return {"checked_index_files": len(names), "status": "NO_STAGED_FILES_NOT_A_PROTECTION_TEST" if not names else "BLOCKED" if findings else "PASS_BOUNDED",
            "findings": findings, "scope": "STAGED_BLOB_BYTES_NOT_WORKTREE_NOT_HISTORICAL_PURGE", "timestamp_utc": utc()}
