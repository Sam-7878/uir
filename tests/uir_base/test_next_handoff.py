import json
import pytest
from projects.uir_base.scripts import next_handoff as handoff


def test_detached_seal_rejects_wrong_archive_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(handoff, "validate", lambda: None)
    archive = tmp_path / "archive.zip"
    archive.write_bytes(b"test")
    proof = tmp_path / "proof.json"
    proof.write_text(json.dumps({"status": "ARCHIVE_ONLY_OFFLINE_REPRODUCTION_PASS", "archive_sha256": "WRONG"}))
    with pytest.raises(ValueError, match="Archive/proof mismatch"):
        handoff.seal(archive, proof)


def test_detached_seal_requires_fresh_capture_replay(tmp_path, monkeypatch):
    monkeypatch.setattr(handoff, "validate", lambda: None)
    archive = tmp_path / "archive.zip"
    archive.write_bytes(b"test")
    proof = tmp_path / "proof.json"
    proof.write_text(json.dumps({"status": "ARCHIVE_ONLY_OFFLINE_REPRODUCTION_PASS", "archive_sha256": handoff.a.digest(archive),
                                "no_development_checkout_imports": True, "scientific_files_equal": 31,
                                "fresh_capture_replay": None}))
    with pytest.raises(ValueError, match="Fresh archive capture replay incomplete"):
        handoff.seal(archive, proof)
