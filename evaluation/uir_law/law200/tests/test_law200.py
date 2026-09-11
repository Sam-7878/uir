from __future__ import annotations

import json
from datetime import date

import pytest

from evaluation.uir_law.law200.baselines import PIPELINES
from evaluation.uir_law.law200.baselines.core import post_guard, render_verified_selection, run_pipeline
from evaluation.uir_law.law200.builders.freeze_dataset import build_split, make_pair
from evaluation.uir_law.law200.builders.generate_hard_negatives import candidates
from evaluation.uir_law.law200.builders.generate_mismatch_cases import mismatch_pairs
from evaluation.uir_law.law200.legal_ir import (
    case_names_match,
    compile_legal_uir,
    detect_language,
    extract_citation,
    verify_entity,
)
from evaluation.uir_law.law200.kr.build_dataset import source_date_is_eligible
from evaluation.uir_law.law200.kr.law_go_kr import redact_credential
from evaluation.uir_law.law200.retrieval import retrieve
from evaluation.uir_law.law200.scoring.score_supported_claims import aggregate, score_record
from evaluation.uir_law.law200.scoring.statistics import exact_mcnemar, holm, wilson


def record(citation: str, name: str, source_id: str = "courtlistener:cluster:1", status: int = 200) -> dict:
    return {
        "citation_canonical": citation,
        "citation_raw": citation,
        "case_name": name,
        "court": "Supreme Court of the United States",
        "date_filed": "1973-01-22",
        "courtlistener_cluster_id": 1 if status == 200 else None,
        "lookup_status": status,
        "source_uri": "https://www.courtlistener.com/opinion/1/",
        "source_id": source_id,
        "response_sha256": "a" * 64,
        "raw_batch_sha256": "b" * 64,
        "raw_response_file": "data/source_responses/fake.json",
        "mutation": {"type": "adjacent_page_plus_1", "source_valid_citation": "410 U.S. 113"} if status == 404 else None,
    }


@pytest.fixture
def registry() -> list[dict]:
    return [
        record("410 U.S. 113", "Roe v. Wade"),
        record("347 U.S. 483", "Brown v. Board of Education", "courtlistener:cluster:2"),
    ]


@pytest.fixture
def corpus(registry) -> list[dict]:
    return [{
        key: row[key] for key in ("source_id", "citation_canonical", "case_name", "court", "date_filed", "courtlistener_cluster_id")
    } | {"verified_summary": f"{row['citation_canonical']} is {row['case_name']}"} for row in registry]


class FakeModel:
    def __init__(self, responses: list[str]):
        self.responses = iter(responses)
        self.calls = 0

    def generate(self, prompt: str, system: str) -> dict:
        self.calls += 1
        return {
            "raw_response": next(self.responses), "latency_ms": 1.0,
            "input_tokens": 10, "output_tokens": 10, "load_ms": 0.0,
            "prompt_eval_ms": 0.1, "generation_ms": 0.9, "done_reason": "stop",
        }


def supported_output(citation="410 U.S. 113", name="Roe v. Wade", source="courtlistener:cluster:1") -> str:
    return json.dumps({
        "decision": "ANSWER", "citation": citation, "case_name": name,
        "answer": "Verified metadata.", "evidence_ids": [source],
    })


def gold(category="A_VALID") -> dict:
    return {
        "case_id": "x", "pair_id": "p", "language": "en", "category": category,
        "gold_citation": "410 U.S. 113", "gold_case_name": "Roe v. Wade",
        "source_id": "courtlistener:cluster:1",
    }


@pytest.mark.parametrize("text", ["410 U.S. 113", "410 US 113", "410 U. S. 113"])
def test_citation_surface_canonicalization(text):
    assert extract_citation(text) == "410 U.S. 113"


def test_language_detection():
    assert detect_language("판례를 요약해 주세요") == "ko"
    assert detect_language("Summarize the case") == "en"


def test_law_go_kr_credential_is_redacted_recursively():
    value = {"link": "https://example.test/?OC=secret", "rows": ["secret", 1]}
    assert redact_credential(value, "secret") == {
        "link": "https://example.test/?OC=[REDACTED_OC]", "rows": ["[REDACTED_OC]", 1]
    }


def test_korean_source_rejects_future_decision_date():
    assert source_date_is_eligible({"선고일자": "2026.09.11"}, date(2026, 9, 11))
    assert not source_date_is_eligible({"선고일자": "2026.12.11"}, date(2026, 9, 11))


def test_cross_language_uir_equivalence():
    en = compile_legal_uir("Summarize 410 U.S. 113.")
    ko = compile_legal_uir("410 U.S. 113 판례를 요약해 주세요.")
    assert (en.domain, en.intent, en.citation) == (ko.domain, ko.intent, ko.citation)


def test_case_name_normalization():
    assert case_names_match("Roe v. Wade", "Roe v. Wade")
    assert case_names_match("성년후견개시", "성년후견개시")
    assert not case_names_match("Brown v. Board of Education", "Roe v. Wade")


def test_korean_case_number_and_parenthesized_claimed_name():
    uir = compile_legal_uir("(심리 불속행) 잘못된 사건명 (2026두30553) 판결을 요약해 주세요.")
    assert uir.citation == "2026두30553"
    assert uir.claimed_case_name == "(심리 불속행) 잘못된 사건명"


def test_entity_verification_valid(registry):
    decision = verify_entity(compile_legal_uir("Summarize 410 U.S. 113."), registry)
    assert decision.status == "VERIFIED"


def test_entity_verification_not_found(registry):
    decision = verify_entity(compile_legal_uir("Summarize 410 U.S. 114."), registry)
    assert decision.reason == "CITATION_NOT_FOUND"


def test_entity_verification_mismatch(registry):
    decision = verify_entity(compile_legal_uir("Summarize Brown v. Board of Education (410 U.S. 113)."), registry)
    assert decision.reason == "ENTITY_BINDING_MISMATCH"


def test_hard_negative_candidates_are_reporter_preserving(registry):
    values = candidates(registry)
    assert values
    assert all(" U.S. " in citation for citation, _ in values)
    assert all(meta["source_valid_citation"] in {r["citation_canonical"] for r in registry} for _, meta in values)


def test_mismatch_pairing(registry):
    pairs = mismatch_pairs(registry)
    assert len(pairs) == 2
    assert all(left["citation_canonical"] != right["citation_canonical"] for left, right in pairs)


def test_runtime_pair_has_no_oracle_fields(registry):
    runtime, scoring = make_pair("dev", "A_VALID", 0, registry[0])
    assert len(runtime) == len(scoring) == 2
    assert set(runtime[0]) == {"case_id", "query"}


def test_split_balance(registry):
    valids = [record(f"{index + 1} U.S. {index + 10}", f"Alpha{index} v. Omega{index}", f"source:{index}") for index in range(50)]
    invalid = [record(f"{index + 1} U.S. {index + 100}", "", f"invalid:{index}", 404) for index in range(25)]
    runtime, scoring = build_split("test", valids[:25], valids[25:], invalid, valids[:25], valids[25:])
    assert len(runtime) == len(scoring) == 200
    assert len({row["query"] for row in runtime}) == 200


def test_retrieval_prefers_exact_citation(corpus):
    assert retrieve("Please summarize 347 U.S. 483", corpus, 1)[0]["citation_canonical"] == "347 U.S. 483"


def test_guard_accepts_bound_output(corpus):
    output, transition = post_guard(supported_output(), corpus[:1])
    assert transition == "OUTPUT_CONTRACT_PASS"
    assert output["decision"] == "ANSWER"


def test_guard_rejects_wrong_entity(corpus):
    output, transition = post_guard(supported_output("410 U.S. 113", "Brown v. Board of Education"), corpus[:1])
    assert transition == "OUTPUT_CONTRACT_REJECT"
    assert output["decision"] == "REJECT"


def test_uir_reference_selection_is_deterministically_rendered(corpus):
    raw = json.dumps({"selected_evidence_ids": ["courtlistener:cluster:1"]})
    output, transition = render_verified_selection(raw, corpus[:1], "en")
    assert transition == "REFERENCE_SELECTION_PASS"
    assert output["citation"] == "410 U.S. 113"
    assert output["case_name"] == "Roe v. Wade"
    assert output["evidence_ids"] == ["courtlistener:cluster:1"]


def test_uir_reference_selection_rejects_untrusted_id(corpus):
    raw = json.dumps({"selected_evidence_ids": ["attacker:source:9"]})
    output, transition = render_verified_selection(raw, corpus[:1], "en")
    assert transition == "MODEL_SELECTION_OUT_OF_SCOPE"
    assert output["decision"] == "REJECT"


def test_uir_rejects_invalid_before_model(registry, corpus):
    model = FakeModel([])
    result = run_pipeline("C8_UIR", {"case_id": "x", "query": "Summarize 410 U.S. 114."}, registry, corpus, model)
    assert not result["model_invoked"]
    assert model.calls == 0


def test_uir_answers_from_selected_verified_reference(registry, corpus):
    model = FakeModel([json.dumps({"selected_evidence_ids": ["courtlistener:cluster:1"]})])
    result = run_pipeline("C8_UIR", {"case_id": "x", "query": "Summarize 410 U.S. 113."}, registry, corpus, model)
    output = json.loads(result["final_output"])
    assert result["transition"] == "UIR_REFERENCE_SELECTION_PASS"
    assert output["decision"] == "ANSWER"
    assert output["citation"] == "410 U.S. 113"


def test_existence_check_does_not_bind_name(registry, corpus):
    model = FakeModel([supported_output()])
    result = run_pipeline("C2_EXISTENCE_CHECK", {"case_id": "x", "query": "Summarize Brown v. Board of Education (410 U.S. 113)."}, registry, corpus, model)
    assert result["model_invoked"]
    assert result["transition"] == "EXISTENCE_PERMIT"


def test_scoring_supported_answer():
    row = score_record({"pipeline": "C8_UIR", "final_output": supported_output(), "model_calls": [], "model_invoked": True}, gold())
    assert row["supported"]
    assert not row["accepted_unsupported"]


def test_scoring_nonexistent_false_acceptance():
    row = score_record({"pipeline": "C1_NAIVE_RAG", "final_output": supported_output(), "model_calls": [], "model_invoked": True}, gold("C_NONEXISTENT"))
    assert row["invalid_false_acceptance"]


def test_scoring_nonexistent_rejection():
    output = json.dumps({"decision": "REJECT", "citation": "410 U.S. 113", "case_name": None, "answer": "not found", "evidence_ids": []})
    row = score_record({"pipeline": "C8_UIR", "final_output": output, "model_calls": [], "model_invoked": False}, gold("C_NONEXISTENT"))
    assert row["nonexistent_safe"]


def test_wilson_zero_bound_is_nonzero():
    interval = wilson(0, 50)
    assert interval["rate"] == 0
    assert 0 < interval["high"] < 0.1


def test_exact_mcnemar():
    result = exact_mcnemar([True, True, False, False], [False, False, False, False])
    assert result["left_only"] == 2
    assert result["p_value"] == 0.5


def test_holm_monotonic_adjustment():
    result = holm([{"p_value": 0.01}, {"p_value": 0.03}, {"p_value": 0.2}])
    assert result[0]["holm_adjusted_p"] <= result[1]["holm_adjusted_p"]


def test_all_required_pipelines_present():
    assert PIPELINES == ("C0_DIRECT", "C1_NAIVE_RAG", "C2_EXISTENCE_CHECK", "C4_TOOL_AGENT", "C5_GUARDRAIL", "C8_UIR")
