import json
from pathlib import Path
import pytest
from uir_common.representation import FULL_SCHEMA, FIELDS, TypedRequest
from projects.uir_base.validation.qa import checked_reference, unique_cases, required_finish, actual_signoff


def test_schema_and_guard_align_all_required_fields():
    assert FULL_SCHEMA["properties"]["claims"]["items"]["required"] == list(FIELDS)


def test_missing_and_corrupt_source_reference_fail(tmp_path):
    with pytest.raises(ValueError, match="MISSING_REFERENCE"):
        checked_reference(tmp_path, "missing.schema.json", "a" * 64)
    source = tmp_path / "schema.json"; source.write_text("{}")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        checked_reference(tmp_path, source.name, "a" * 64)
    with pytest.raises(ValueError, match="UNSAFE_REFERENCE"):
        checked_reference(tmp_path, "../escape", "a" * 64)


def test_duplicate_broken_family_and_missing_finish_fail(tmp_path):
    with pytest.raises(ValueError, match="DUPLICATE_CASE"):
        unique_cases([{"case_id": "C"}, {"case_id": "C"}])
    with pytest.raises(ValueError): required_finish({"done": True})
    with pytest.raises(ValueError): required_finish({"done": True, "done_reason": "invented"})
    required_finish({"done": True, "done_reason": "length"})
    family = tmp_path / "family.csv"; family.write_text("case_id,family\nC,WRONG\n")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        checked_reference(tmp_path, family.name, "0" * 64)


def test_no_human_or_author_approval_can_be_inferred_from_ai_record(tmp_path):
    with pytest.raises(ValueError, match="MISSING_AUTHOR"):
        actual_signoff(tmp_path / "none.json")
    source = tmp_path / "ai.json"; source.write_text(json.dumps({"source": "model output", "approved": True}))
    with pytest.raises(ValueError, match="INVALID_AUTHOR"):
        actual_signoff(source)


def test_artifact_digest_metadata_and_semantic_tampering():
    r = TypedRequest("D001", "revenue", "2025", "USD", None, "read", "P1", "E1")
    artifact = r.artifact({"language": "ko"})
    artifact["metadata"]["language"] = "en"
    assert TypedRequest.from_artifact(artifact).digest == r.digest
    artifact["semantics"]["entity"] = "OTHER"
    with pytest.raises(ValueError, match="DIGEST_MISMATCH"):
        TypedRequest.from_artifact(artifact)
