import json
from pathlib import Path
import zipfile

import pytest
from jsonschema import Draft202012Validator
from projects.uir_base.scripts.next_frontend import compile_raw
from projects.uir_base.scripts.next_release import checked_path, independent_label
from projects.uir_base.scripts.revision_audit import digest
from projects.uir_base.scripts.next_verify import safe_extract
from projects.uir_base.scripts.next_matched_analysis import paired


@pytest.mark.parametrize("raw,status,label", [
    ('{"overall_hallucination":"Yes", "unfinished":', "PRESENT", "Yes"),
    ('{"claim_evaluations":[', "MISSING", None),
    ('{"overall_hallucination":"Maybe"}', "INVALID", None),
    ('{"overall_hallucination":"No", "overall_hallucination":"Yes"}', "AMBIGUOUS", None)])
def test_semantic_literal_is_separate_from_json_format(raw, status, label):
    assert independent_label(raw, "Qwen2.5-7B", "C8") == (status, label)


def test_release_dependencies_fail_closed(tmp_path):
    path = tmp_path / "fixture.json"; path.write_text("{}")
    assert checked_path(tmp_path, "fixture.json", digest(path)) == path
    with pytest.raises(FileNotFoundError):
        checked_path(tmp_path, "missing", "0" * 64)
    with pytest.raises(ValueError, match="hash mismatch"):
        checked_path(tmp_path, "fixture.json", "0" * 64)
    with pytest.raises(ValueError, match="root-relative"):
        checked_path(tmp_path, "../escape", "0" * 64)


def test_actual_frontend_matches_published_recursive_schema():
    root = next(p for p in Path(__file__).resolve().parents if (p / "Cargo.toml").is_file())
    schema = json.loads((root / "docs/work_reports/uir_base/110_mdpi_rev/implementation/uir.schema.json").read_text())
    validator = Draft202012Validator(schema)
    result = compile_raw("verify TSLA revenue 2025 in USD unless approval AND (value > 10 OR NOT entity_verified)",
                         policy_snapshot="p1", evidence_snapshot="e1")
    assert validator.is_valid(result["uir"])
    bad = result["uir"] | {"user_condition": {"field": "approval", "op": "==", "type": "DECIMAL", "value": "1"}}
    assert not validator.is_valid(bad)


def test_archive_rejects_escaping_and_duplicate_entries(tmp_path):
    for name, entries in (("escape", ["../outside"]), ("duplicate", ["file", "file"])):
        archive = tmp_path / f"{name}.zip"
        with zipfile.ZipFile(archive, "w") as output:
            for entry in entries:
                output.writestr(entry, "bad")
        with pytest.raises(ValueError):
            safe_extract(archive, tmp_path / name)
    assert not (tmp_path / "outside").exists()


def test_paired_source_family_missing_or_duplicate_is_not_a_pass():
    def row(condition):
        return {"pipeline": condition, "case_id": "a", "commit_eligible": True,
                "complete": True, "safe_claim_answered": True}
    rows = [row("DETERMINISTIC_TRUSTED_FIXTURE"), row("SLM_SCHEMA_RENDERER")]
    with pytest.raises(ValueError, match="Missing source-family"):
        paired(rows, {})
    with pytest.raises(ValueError, match="Duplicate"):
        paired(rows + [rows[-1]], {"a": "family"})
    result = paired(rows, {"a": "family"}, repetitions=50)
    assert len(result) == 2
    assert all(r["risk_difference"] == 0 and r["p_holm"] == 1 for r in result)
