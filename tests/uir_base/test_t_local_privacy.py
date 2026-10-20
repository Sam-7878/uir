"""Synthetic local guard tests, not confirmatory scientific evidence."""
import json
import subprocess
import sys

import pytest

from projects.uir_base.electronics_research import policy
from projects.uir_base.electronics_research.privacy import remote_identity


@pytest.mark.parametrize("path", ["../secret", "/secret", "a/../b", "a/./b", "a//b", "a/", "C:/secret", "a\\b", "", "a\x00b"])
def test_bad_relative_path(path):
    with pytest.raises(ValueError):
        policy.safe_relative(path)


@pytest.mark.parametrize("path", ["docs/work_reports/x.md", "docs/papers/draft.tex", "results/private_gold/a.json",
    "results/evaluator_only/a.json", "results/gold_boundary_v2/a.json", "results/raw_prompt.jsonl",
    "results/manuscript_private/a.tex", "results/work_reports/x.md", "results/benchmark_gold.csv", "release.zip", "model.gguf"])
def test_private_path_denied(path):
    assert policy.protected_path(path)


def test_canonical_source_allowed():
    assert not policy.protected_path("src/llm_trust/uir/builder.py")


@pytest.mark.parametrize("path", ["docs/work_reports/run_20261020T000000Z", str(policy.RESULTS_PREFIX), str(policy.RESULTS_PREFIX / "old")])
def test_wrong_results_dir(tmp_path, path):
    with pytest.raises(ValueError):
        policy.validate_results_dir(tmp_path / path, tmp_path)


def test_valid_results_dir(tmp_path):
    p = tmp_path / policy.RESULTS_PREFIX / "run_20261020T000000Z"
    assert policy.validate_results_dir(p, tmp_path) == p


def test_write_once(tmp_path):
    p = tmp_path / "one.json"
    policy.write_once(p, {"value": 1})
    with pytest.raises(FileExistsError):
        policy.write_once(p, {"value": 2})
    assert json.loads(p.read_text()) == {"value": 1}


def test_allowlist_requires_actual_approval(tmp_path):
    with pytest.raises(ValueError, match="NO_ACTUAL"):
        policy.check_public_allowlist(tmp_path, [])


def test_empty_allowlist_denied(tmp_path):
    with pytest.raises(ValueError, match="EMPTY"):
        policy.check_public_allowlist(tmp_path, [], approval={"owner_approved": True, "approval_evidence_sha256": "0" * 64})


@pytest.mark.parametrize("kind", ["private", "duplicate", "modified", "missing"])
def test_public_byte_guard(tmp_path, kind):
    p = tmp_path / "sample.json"
    p.write_text("{}")
    entry = {"path": "sample.json", "sha256": policy.sha(p), "rights_class": "PUBLIC_APPROVED"}
    entries = [entry]
    if kind == "private":
        entry["path"] = "docs/work_reports/x.md"
    elif kind == "duplicate":
        entries.append(dict(entry))
    elif kind == "modified":
        p.write_text("changed")
    else:
        p.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        policy.check_public_allowlist(tmp_path, entries, approval={"owner_approved": True, "approval_evidence_sha256": "0" * 64})


def test_unverified_pass_labels_cannot_open_submission():
    labels = dict.fromkeys(["ARCHIVE_INTEGRITY", "SCIENTIFIC_EVIDENCE", "GOLD_ISOLATION", "CONFIRMATORY",
        "PAPER_SCOPE", "MDPI_FORMAT", "RIGHTS", "REMOTE_PRIVACY", "AUTHOR_APPROVAL"], "PASS_SCOPED")
    assert policy.publication_gate(labels)["SUBMISSION_READY"] == "BLOCKED"


@pytest.mark.parametrize("url", ["https://token@github.com/a/b", "https://example.com/a/b", "file:///tmp/repo"])
def test_remote_credentials_never_serialized(url):
    with pytest.raises(ValueError):
        remote_identity(url)


def test_remote_identity_normalized():
    assert remote_identity("https://github.com/Sam-7878/UIR.git") == "Sam-7878/UIR"


def test_cli_requires_explicit_directory():
    result = subprocess.run([sys.executable, "-m", "projects.uir_base.electronics_research", "prepare"],
                            cwd=policy.ROOT, text=True, capture_output=True)
    assert result.returncode == 2
    assert "--results-dir required" in result.stderr


def test_boundary_oracle_python():
    from projects.uir_base.electronics_research.conformance import cases
    from projects.uir_base.representation_research.interpreter_python import interpret
    for case in cases():
        assert interpret(case["packet"])["state"] == case["oracle_state"], case["case_id"]


@pytest.mark.parametrize("mutation", ["tamper", "missing", "undeclared", "empty"])
def test_manifest_negative_cases(tmp_path, monkeypatch, mutation):
    original = policy.validate_results_dir
    monkeypatch.setattr(policy, "validate_results_dir", lambda p: original(p, tmp_path))
    directory = tmp_path / policy.RESULTS_PREFIX / "run_20261020T000000Z"
    policy.write_once(directory / "sample.json", {"test": True})
    policy.seal(directory)
    assert policy.verify_manifest(directory) == 1
    with pytest.raises(FileExistsError):
        policy.seal(directory)
    if mutation == "tamper":
        (directory / "sample.json").write_text("changed")
    elif mutation == "missing":
        (directory / "sample.json").unlink()
    elif mutation == "undeclared":
        (directory / "extra.json").write_text("{}")
    else:
        (directory / "evidence_manifest.json").write_text('{"files": {}}')
    with pytest.raises(ValueError):
        policy.verify_manifest(directory)
