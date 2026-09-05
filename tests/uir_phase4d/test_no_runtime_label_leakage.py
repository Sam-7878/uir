"""Unit test enforcing zero label leakage in Phase UIR-4D runtime data."""
from __future__ import annotations

import pytest
from evaluation.uir_phase4d.audit_runtime_gold_access import audit_runtime_files


def test_no_runtime_label_leakage():
    report = audit_runtime_files()
    assert report["status"] == "PASS", f"Leakage audit failed with findings: {report['findings']}"
    assert report["gold_derived_runtime_decision_fields"] == 0
    assert report["forbidden_generation_gold_access"] == 0
    assert report["total_runtime_rows_checked"] >= 1000  # 600 + 100 + 200 + 200 = 1100
