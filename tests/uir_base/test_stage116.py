"""Synthetic engineering tests. No external-source or scientific confirmation claim."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import subprocess
import zipfile

import pytest

from projects.uir_base.electronics_research.stage116.artifacts import PREFIX, RunStore
from projects.uir_base.electronics_research.stage116.protection import inspect_bytes, scan_index
from projects.uir_base.electronics_research.stage116.protocol import matrix, precision_plan, require_confirmation


def git(repo, *args):
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args], text=True, capture_output=True, check=True)


@pytest.fixture
def indexed_repo(tmp_path):
    git(tmp_path, "init", "-q")
    return tmp_path


def zip_bytes(name, data):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, data)
    return buffer.getvalue()


@pytest.mark.parametrize("kind", ["private_path_force_added", "gold_disguised", "nested_gold", "private_key", "jsonl_gold", "archive_path"])
def test_actual_index_rejects_private_payload(indexed_repo, kind):
    repo = indexed_repo
    name, body = "innocent.txt", b"public text\n"
    if kind == "private_path_force_added":
        (repo / ".gitignore").write_text("docs/work_reports/\n")
        name = "docs/work_reports/x.md"
    elif kind == "gold_disguised":
        body = b'{"expected_ids":["synthetic-secret"]}'
    elif kind == "jsonl_gold":
        body = b'{"public":1}\n{"gold_program":"synthetic-only"}\n'
    elif kind == "nested_gold":
        body = zip_bytes("inner.dat", zip_bytes("labels.txt", b'{"exe_ans":42}'))
    elif kind == "private_key":
        body = b"-----BEGIN PRIVATE KEY-----\nSYNTHETIC-NONFUNCTIONAL\n-----END PRIVATE KEY-----"
    else:
        body = zip_bytes("docs/work_reports/hidden.md", b"synthetic private report")
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    git(repo, "add", "-f", "--", name)
    # Scanner must read INDEXED bytes, not a subsequently sanitized worktree file.
    path.write_bytes(b"now benign but not staged")
    result = scan_index(repo)
    assert result["checked_index_files"] == 1 and result["status"] == "BLOCKED"
    assert result["findings"] and "synthetic-secret" not in json.dumps(result)


def test_actual_positive_index_not_empty(indexed_repo):
    (indexed_repo / "safe.py").write_text("def answer():\n    return 42\n")
    git(indexed_repo, "add", "safe.py")
    result = scan_index(indexed_repo)
    assert result["checked_index_files"] == 1 and result["status"] == "PASS_BOUNDED"


def test_empty_index_is_not_a_protection_test(indexed_repo):
    assert scan_index(indexed_repo)["status"] == "NO_STAGED_FILES_NOT_A_PROTECTION_TEST"


def test_index_symlink_denied(indexed_repo):
    # Attack fixture exists only in pytest's temporary repository, never real UIR.
    (indexed_repo / "link.txt").symlink_to("/etc/passwd")
    git(indexed_repo, "add", "link.txt")
    assert "NONREGULAR_INDEX_ENTRY" in scan_index(indexed_repo)["findings"][0]["reasons"]


@pytest.mark.parametrize("body", [b'\x00\xffbinary', b'x' * (2 * 1024 * 1024 + 1), zip_bytes("../escape", b"safe")])
def test_uninspectable_or_unsafe_binary_fail_closed(body):
    assert inspect_bytes(body)


@pytest.fixture
def store(tmp_path):
    result = RunStore(tmp_path / PREFIX / "run_20261023T000000Z", root=tmp_path)
    result.create()
    return result


@pytest.mark.parametrize("path", ["../outside.json", "/tmp/outside.json", "a/../../outside", "a\\b", "a//b"])
def test_writes_cannot_escape_stage(store, path):
    with pytest.raises(ValueError):
        store.write(path, {})


def test_sealed_run_cannot_append_or_reseal(store):
    store.write("one.json", {"case": "synthetic"})
    store.seal()
    assert store.verify() == 1
    with pytest.raises(FileExistsError): store.write("later.json", {})
    with pytest.raises(FileExistsError): store.seal()
    with pytest.raises(FileExistsError): store.create()


@pytest.mark.parametrize("mutation", ["tamper", "undeclared", "missing"])
def test_manifest_tampering_rejected(store, mutation):
    store.write("one.json", {})
    store.seal()
    if mutation == "tamper": (store.directory / "one.json").write_text("wrong")
    elif mutation == "missing": (store.directory / "one.json").unlink()
    else: (store.directory / "extra.json").write_text("{}")
    with pytest.raises(ValueError): store.verify()


def test_symlink_escape_denied(store, tmp_path):
    (store.directory / "escape").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError): store.write("escape/new.json", {})


def proof():
    keys = ("source_bytes_verified", "dataset_rights_recorded", "document_family_disjoint", "query_template_family_disjoint",
            "gold_role_separation", "runtime_gold_os_isolation_verified", "protocol_frozen_before_inference",
            "method_review_recorded", "precision_target_satisfied")
    return {**dict.fromkeys(keys, True), "split": "CONFIRMATORY_FRESH", "previously_observed": False}


@pytest.mark.parametrize("missing", list(proof()))
def test_missing_prerequisite_blocks_confirmation(missing):
    candidate = proof()
    candidate.pop(missing)
    with pytest.raises(ValueError): require_confirmation(candidate)


def test_development_cannot_be_promoted():
    with pytest.raises(ValueError): require_confirmation({**proof(), "previously_observed": True})
    with pytest.raises(ValueError): require_confirmation({**proof(), "split": "DEVELOPMENT"})


def test_planning_does_not_claim_power_or_preregistration():
    assert len(matrix()) == 8
    plan = precision_plan()
    assert plan["status"] == "PLANNING_NOT_PREREGISTERED"
    assert plan["rows"][0]["zero_event_one_sided_95_upper"] > 0.7


def test_interchange_retains_metadata_and_semantics():
    from projects.uir_base.electronics_research.conformance import cases
    from projects.uir_base.electronics_research.stage116.interchange import to_native, to_uir
    from projects.uir_base.representation_research.interpreter_python import interpret
    packet = cases()[0]["packet"]
    packet["artifact"]["metadata"] = {"id": "MUST_REMAIN"}
    native = to_native(packet)
    assert to_uir(native) == packet
    assert interpret(packet) == interpret(native)


@pytest.mark.parametrize("mutation", ["unknown_section", "stale", "bad_digest", "unknown_native", "gold", "unsupported_predicate"])
def test_interchange_typed_failures(mutation):
    from projects.uir_base.electronics_research.conformance import cases
    from projects.uir_base.electronics_research.stage116.interchange import InterchangeFailure, to_native, to_uir
    from uir_common.contracts import canonical_digest
    packet = cases()[0]["packet"]
    if mutation == "unknown_native":
        native = to_native(packet)
        native["private_plan"]["hidden_override"] = "NO"
        with pytest.raises(InterchangeFailure): to_uir(native)
        return
    if mutation == "unknown_section": packet["artifact"]["unknown"] = 1
    elif mutation == "stale": packet["current_evidence_version"] = "old"
    elif mutation == "bad_digest": packet["artifact"]["semantic_digest"] = "0" * 64
    elif mutation == "gold": packet["gold_program"] = "SYNTHETIC_ONLY"
    else:
        packet["artifact"]["semantics"]["predicate"] = {"op": "AND", "args": []}
        packet["artifact"]["semantic_digest"] = canonical_digest({k: packet["artifact"][k] for k in
            ("semantics", "policy_constraints", "execution_contract", "output_contract")})
    with pytest.raises(InterchangeFailure): to_native(packet)
