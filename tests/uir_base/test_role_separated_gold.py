import json
from pathlib import Path

import pytest

from projects.uir_base.electronics_research.stage116.gold_reference import source_values, reference_gold
from projects.uir_base.electronics_research.stage116.source_catalog import build_catalog, usd_cents
from projects.uir_base.electronics_research.stage116.role_runtime import compile_query


@pytest.mark.parametrize("raw,expected", [("1.25", "125"), ("-0.01", "-1"), ("123456789012345.01", "12345678901234501"), ("0", "0")])
def test_cents_without_float_rounding(raw, expected):
    assert usd_cents(raw) == expected


@pytest.mark.parametrize("raw", ["1.234", "NaN", "1e3", "+1", True])
def test_runtime_registry_rejects_unexplained_numeric_conversion(raw):
    with pytest.raises(ValueError): usd_cents(raw)


@pytest.fixture
def original_documents(tmp_path):
    treasury = tmp_path / "raw.json"
    treasury.write_text(json.dumps({"data": [{"record_date": "2024-01-02", "debt_held_public_amt": "1.25", "intragov_hold_amt": "2.00", "tot_pub_debt_out_amt": "3.25"}]}))
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text('[package]\nversion="0.102.0"\nrust-version="1.99"\n[workspace.package]\nrust-version="1.97"\nedition="2024"\n')
    return treasury, cargo


def test_source_reference_not_a_runtime_self_oracle(original_documents):
    originals = source_values(*original_documents)
    catalog = build_catalog(*original_documents)
    assert len(catalog) == len(originals) == 11
    for expected in originals:
        record = next(f for f in catalog if all(f[k] == expected[k] for k in ("entity", "metric", "period", "unit")))
        assert record["value"] == expected["value"]
        assert record["provenance"].endswith(expected["source_pointer"])
    # Mutating the runtime registry cannot mutate source-recomputed gold.
    catalog[0]["value"] = "999999"
    query = "At snapshot, return package_rust_minor for CARGO in COUNT."
    assert reference_gold(query, originals)["value"] == "99"


@pytest.mark.parametrize("raw", ["At snapshot, return package_rust_minor for CARGO in COUNT.", "snapshot 기준 CARGO의 package_rust_minor 항목을 COUNT 단위로 응답하세요."])
def test_two_separate_parsers_match_declared_cnl(original_documents, raw):
    reference = reference_gold(raw, source_values(*original_documents))
    actual = compile_query(raw)
    assert {k: actual[k] for k in reference["semantics"]} == reference["semantics"]
    assert actual["predicate"] is None


def test_runtime_cannot_import_scorer():
    import inspect
    from projects.uir_base.electronics_research.stage116 import role_runtime
    text = inspect.getsource(role_runtime)
    assert "from .gold_reference" not in text and "reference_gold(" not in text
    with pytest.raises(ValueError): compile_query("Please explain anything about Cargo")


@pytest.mark.parametrize("entity", ["DEMO", "CRATE_2", "BASE64"])
@pytest.mark.parametrize("metric", ["package_version_major", "package_version_minor"])
def test_fresh_primary_cnl_parsers_are_separate_and_agree(entity, metric):
    from projects.uir_base.electronics_research.stage116.confirm_runtime import parse_release_query
    from projects.uir_base.electronics_research.stage116.confirm_primary import EN, KO, independent_query_reference
    for template in (EN, KO):
        raw = template.format(entity=entity, metric=metric, unit="COUNT")
        assert parse_release_query(raw) == {**independent_query_reference(raw), "predicate": None}
        assert not raw.startswith("At ") and not raw.startswith("show ")


def test_reference_value_uses_source_not_runtime_registry(original_documents):
    from projects.uir_base.electronics_research.stage116.confirm_primary import reference_value
    _, original = original_documents
    assert reference_value(original, "package_version_major") == "0"
    assert reference_value(original, "package_version_minor") == "102"
    with pytest.raises(ValueError): reference_value(original, "invented_metric")


def test_primary_cluster_precision_is_not_240_independent_cases():
    upper_60 = 1 - .05 ** (1 / 60)
    upper_240 = 1 - .05 ** (1 / 240)
    assert .048 < upper_60 < .05
    assert upper_60 > upper_240 * 3


def test_exact_finite_frame_bound_and_null():
    from projects.uir_base.electronics_research.stage116.confirm_primary import frame_upper, hypergeom_lower_tail
    assert hypergeom_lower_tail(10, 5, 0, 0) == 1
    assert hypergeom_lower_tail(10, 5, 10, 0) == 0
    assert hypergeom_lower_tail(10, 5, 2, 0) == pytest.approx(56 / 252)
    upper = frame_upper(142, 60, 0)
    assert hypergeom_lower_tail(142, 60, upper, 0) > .05
    assert hypergeom_lower_tail(142, 60, upper + 1, 0) <= .05
    assert upper / 142 < .05
    assert frame_upper(60, 60, 0) == 0
    assert frame_upper(60, 60, 60) == 60


def test_secondary_original_line_check_does_not_trust_runtime_value(original_documents, monkeypatch):
    from projects.uir_base.electronics_research.stage116 import matched_score
    from projects.uir_base.electronics_research.policy import sha
    _, path = original_documents
    monkeypatch.setattr(matched_score, "ROOT", path.parent)
    source = {"manifest_ref": path.name, "parent_family": "github-owner:demo", "manifest_sha256": sha(path)}
    provenance = source["parent_family"] + ":" + sha(path) + "/package/version#minor"
    fact = {"entity": "DEMO", "metric": "package_version_minor", "value": "102", "provenance": provenance}
    assert " | 102 COUNT | " in matched_score.line_from_original(fact, source)
    with pytest.raises(ValueError): matched_score.line_from_original({**fact, "value": "999"}, source)
    with pytest.raises(ValueError): matched_score.line_from_original({**fact, "provenance": "invented"}, source)


def test_secondary_cluster_ci_keeps_language_pairs_together():
    from projects.uir_base.electronics_research.stage116.matched_score import clustered_completion_ci, quantile
    rows = [{"family": f, "allowed": True, "complete": complete} for f, complete in (("a", True), ("a", True), ("b", False), ("b", False))]
    assert clustered_completion_ci(rows) == [0, 1]
    assert quantile([0, 10], .95) == pytest.approx(9.5)


@pytest.mark.parametrize("entity", ["DEMO", "A_12"])
def test_v4_fixed_context_query_parsers(entity):
    from projects.uir_base.electronics_research.stage116.confirm_primary import FIXED_EN, FIXED_KO, independent_query_reference
    from projects.uir_base.electronics_research.stage116.confirm_runtime import parse_release_query
    for template in (FIXED_EN, FIXED_KO):
        text = template.format(entity=entity, metric="package_version_major", unit="COUNT")
        assert parse_release_query(text) == {**independent_query_reference(text), "predicate": None}
