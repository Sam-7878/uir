"""Fail-closed artifact references and author gates used by release QA."""
from pathlib import Path
from .common import ROOT, load, sha


def checked_reference(root, relative, digest):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts: raise ValueError("UNSAFE_REFERENCE")
    actual = root / path
    if actual.is_symlink() or not actual.is_file() or not actual.resolve().is_relative_to(root.resolve()):
        raise ValueError("MISSING_REFERENCE")
    if sha(actual) != digest: raise ValueError("REFERENCE_HASH_MISMATCH")
    return actual


def unique_cases(rows, fields=("case_id",)):
    keys = [tuple(r[f] for f in fields) for r in rows]
    if len(keys) != len(set(keys)): raise ValueError("DUPLICATE_CASE")


def required_finish(row):
    if row.get("done") is not True or row.get("done_reason") not in {"stop", "length"}:
        raise ValueError("MISSING_OR_INVALID_FINISH")


def actual_signoff(path):
    if not path.is_file(): raise ValueError("MISSING_AUTHOR_INSTITUTION_SIGNOFF")
    data = load(path)
    if data.get("source") != "actual_signed_author_institution_record" or not data.get("verified_human_signatory"):
        raise ValueError("INVALID_AUTHOR_SIGNOFF")
    return data
