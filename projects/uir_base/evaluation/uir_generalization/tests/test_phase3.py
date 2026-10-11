import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_claim_metric_distinguishes_exact_and_field_level_match():
    module = load_module("validate_claim_metrics")
    expected = [{"claim_type": "numeric_claim", "entity_id": "E", "attribute": "revenue",
                 "value": "10", "unit": "USD", "period": "2025", "provenance": "src"}]
    actual = [dict(expected[0], value="11")]
    assert module.score(expected, actual) == (0.0, 0.0, 6 / 7, 6 / 7)


def test_candidate_manifest_is_explicitly_review_gated():
    manifest = json.loads((BASE.parents[1] / "results" / "uir_phase3" / "frozen_v2_manifest.json").read_text())
    assert manifest["case_count"] == 1200
    assert manifest["human_review_status"] == "pending"
    assert manifest["frozen"] is False
    assert manifest["publication_ready"] is False
