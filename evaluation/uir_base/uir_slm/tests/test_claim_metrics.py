import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claim_metrics import evaluate_claims, parse_output, validate_against_facts
from paired_statistics import mcnemar_exact


CLAIM = {"claim_type": "numeric_claim", "entity_id": "AAPL", "attribute": "assets", "value": "10", "unit": "USD", "period": "2025", "provenance": "sec:x"}


def test_exact_claim_acceptance_and_unsupported_rejection():
    supported, rejected = validate_against_facts([CLAIM, {**CLAIM, "value": "11"}], [CLAIM])
    assert supported == [CLAIM]
    assert len(rejected) == 1
    metrics = evaluate_claims([CLAIM], [CLAIM, {**CLAIM, "value": "11"}], supported)
    assert metrics["claim_precision"] == 0.5
    assert metrics["unsupported_claim_acceptance_rate"] == 0.0


def test_json_contract_parser_and_mcnemar():
    answer, claims, error = parse_output('{"answer":"ok","claims":[]}')
    assert (answer, claims, error) == ("ok", [], None)
    assert mcnemar_exact([True, False], [True, True])["right_only"] == 1
