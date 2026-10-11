"""Unit test enforcing zero label leakage in Phase UIR-4D runtime data."""
from __future__ import annotations

import json

import pytest
from evaluation.uir_phase4d import audit_runtime_gold_access as runtime_audit
from evaluation.uir_phase4d.audit_runtime_gold_access import audit_runtime_files


def test_no_runtime_label_leakage():
    report = audit_runtime_files()
    assert report["status"] == "PASS", f"Leakage audit failed with findings: {report['findings']}"
    assert report["gold_derived_runtime_decision_fields"] == 0
    assert report["forbidden_generation_gold_access"] == 0
    assert report["total_runtime_rows_checked"] >= 1000  # 600 + 100 + 200 + 200 = 1100


def test_runtime_audit_default_is_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_audit, "RESULTS_DIR", tmp_path)

    def unexpected_write(*args, **kwargs):
        pytest.fail("A read-only audit must not write historical result reports")

    monkeypatch.setattr(runtime_audit, "write_json", unexpected_write)
    report = runtime_audit.audit_runtime_files()
    assert report["status"] == "PASS"
    assert list(tmp_path.iterdir()) == []


def test_runtime_audit_writes_only_to_explicit_destination(tmp_path):
    destination = tmp_path / "requested-audit"
    report = runtime_audit.audit_runtime_files(output_dir=destination)
    assert json.loads((destination / "runtime_label_leakage_audit.json").read_text()) == report
    markdown = (destination / "GOLD_ACCESS_AUDIT_PHASE4D.md").read_text()
    assert report["audited_at_utc"] in markdown
    assert f"`status = {report['status']}`" in markdown
