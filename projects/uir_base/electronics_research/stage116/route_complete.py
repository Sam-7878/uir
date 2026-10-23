"""Final byte and arithmetic audit; does not invoke generation or interpreters."""
import argparse
import json
import math
from pathlib import Path
import random
import tomllib
from xml.etree import ElementTree

from .artifacts import RunStore, PREFIX
from ..policy import ROOT, sha, utc, write_once
from .runner import DOCS


def run(directory, primary_dir, secondary_score_dir):
    primary, secondary = RunStore(primary_dir), RunStore(secondary_score_dir)
    primary.verify()
    secondary.verify()
    reserve = RunStore(ROOT / json.loads(primary.path("reserve_lineage.json").read_text())["path"])
    reserve.verify()
    frame = json.loads(reserve.path("source_registry/reserve_manifest.json").read_text())["records"]
    fixed_context = json.loads(primary.path("frame_contexts_before_random_seed.json").read_text())
    fixed_parents = {r["family"] for r in fixed_context["assignment"]}
    frame = [r for r in frame if r["parent_family"] in fixed_parents]
    assert len(frame) == len(fixed_parents) and not fixed_context["selection_dependent"]
    sample = json.loads(primary.path("random_sample_before_outcomes.json").read_text())
    expected = random.Random(int(sample["seed"])).sample(sorted(frame, key=lambda r: r["parent_family"]), 60)
    assert [s["source_id"] for s in expected] == sample["selected_source_ids"]
    by_entity = {s["source_id"].upper().replace("-", "_"): s for s in expected}
    all_entities = {s["source_id"].upper().replace("-", "_"): s for s in frame}
    prior = RunStore(ROOT / fixed_context["excluded_observed_run"])
    prior.verify()
    prior_rows = [json.loads(x) for x in prior.path("runtime/runtime.jsonl").read_text().splitlines()]
    old_entities = {f["entity"] for r in prior_rows for f in r["source"]["facts"]}
    assert not old_entities.intersection(all_entities)
    assignment = {r["family"]: r for r in fixed_context["assignment"]}
    runtime_rows = [json.loads(x) for x in primary.path("runtime/runtime.jsonl").read_text().splitlines()]
    for r in runtime_rows:
        contexts = {all_entities[f["entity"]]["parent_family"] for f in r["source"]["facts"]}
        assert contexts == {r["family"], *assignment[r["family"]]["distractor_parents"]}
        assert len(r["source"]["facts"]) == 6
    gold = [json.loads(x) for x in primary.path("private_evaluator_only/gold.jsonl").read_text().splitlines()]
    raw = [json.loads(x) for x in primary.path("experiments/primary_raw.jsonl").read_text().splitlines()]
    outputs = {(r["case_id"], r["representation"]): r for r in raw if r["type"] == "outcome"}
    audited, failures = [], set()
    for g in gold:
        s = by_entity[g["semantics"]["entity"]]
        path = ROOT / s["manifest_ref"]
        assert sha(path) == s["manifest_sha256"] == g["source_manifest_sha256"]
        version = tomllib.loads(path.read_text())["package"]["version"]
        component = g["semantics"]["metric"].removeprefix("package_version_")
        actual_value = str(int(version.split(".")[0 if component == "major" else 1]))
        assert g["value"] == actual_value
        expected_state = "FULL_VERIFIED_ANSWER" if component == "major" else "DENY"
        assert g["expected_state"] == expected_state
        for rep in ("UIR", "SPECIALIZED"):
            out = outputs[(g["case_id"], rep)]
            passed = (out["python"] == out["rust"] and out["python"]["state"] == expected_state
                      and out["compiled_semantics"] == {**g["semantics"], "predicate": None})
            if component == "major":
                values = out["accepted_values"]
                passed = passed and len(values) == 1 and values[0]["value"] == actual_value and values[0]["provenance"] == s["parent_family"] + ":" + s["manifest_sha256"] + "/package/version#major"
            else:
                passed = passed and not out["accepted_values"] and not out["python"]["fact_ids"]
            if not passed: failures.add(g["family"])
            audited.append({"case_id": g["case_id"], "representation": rep, "original_source_checked": True, "passed": passed})
    assert len(audited) == len(outputs) == sum(r["type"] == "outcome" for r in raw) == 480
    # Independent arithmetic check of this zero-failure finite-frame result.
    assert not failures
    N, n = len(frame), len(expected)
    denominator = math.comb(N, n)
    upper = max(F for F in range(N - n + 1) if math.comb(N - F, n) / denominator > .05)
    p = math.comb(N - math.ceil(.05*N), n) / denominator
    reported = json.loads(primary.path("statistics/primary_summary.json").read_text())
    assert reported["failed_frame_groups_one_sided95_upper"] == upper and abs(reported["exact_primary_p"] - p) < 1e-14
    store = RunStore(directory)
    store.create()
    checks = {}
    for run_dir in sorted((ROOT / PREFIX).glob("run_*")):
        if run_dir == store.directory: continue
        if (run_dir / "evidence_manifest.json").is_file():
            other = RunStore(run_dir)
            checks[run_dir.name] = {"verified_files": other.verify(), "manifest_sha256": sha(other.path("evidence_manifest.json"))}
    for path in Path(__file__).parent.glob("*.py"):
        store.write("current_source_bytes/" + path.name, path.read_bytes())
    xml = ROOT / PREFIX / "independent_route_full_tests.xml"
    suites = ElementTree.fromstring(xml.read_bytes())
    tests = sum(int(s.get("tests", 0)) for s in suites.iter("testsuite"))
    assert tests > 0 and all(int(s.get("failures", 0)) == int(s.get("errors", 0)) == 0 for s in suites.iter("testsuite"))
    store.write("tests/independent_route_full_tests.xml", xml.read_bytes())
    store.write("integrity/all_sealed_checkpoints.json", checks)
    store.jsonl("audit/primary_original_source_recheck.jsonl", audited)
    stats = {"sample_reproduced_from_recorded_seed": True, "frame_N": N, "sample_n": n, "audited_primary_rows": len(audited),
             "primary_failed_clusters": len(failures), "finite_frame_upper95_failed_groups": upper, "finite_frame_upper95_fraction": upper/N,
             "exact_hypergeometric_p": p, "runtime_contexts_match_preseed_assignments": True, "prior_runtime_fact_entity_overlap": 0,
             "python_tests_passed": tests, "audit_identity": "SAME_CODING_AGENT_SEPARATE_SCORER_PATH_NOT_THIRD_PARTY_OR_HUMAN"}
    store.write("audit/arithmetic_and_sampling.json", stats)
    counts = json.loads(secondary.path("statistics/execution_counts.json").read_text())
    summaries = json.loads(secondary.path("statistics/summary.json").read_text())
    gates = {"owner_route": "CONTINUE_INDEPENDENT_QUERY_GOLD_RESEARCH_AI_ONLY", "T00_T14_COMPLETE": False,
             "SOURCE_AND_GOLD_ROUTE": "EXECUTED_SCOPED_CNL_MACHINE_TRUTH", "PRIMARY_FINITE_FRAME": "EXECUTED",
             "SECONDARY_SLM_FACTORIAL": "EXECUTED", "T17_FULL_TWO_DOMAIN_CONFIRMATION": "INCOMPLETE_SOFTWARE_ONLY_HOLDOUT",
             "BROAD_NL_GENERALIZATION": "NOT_ESTABLISHED", "T19_NEW_INDEPENDENT_IMPLEMENTATION_TEAM": "NOT_AVAILABLE",
             "NATIVE_PROSE_AUCR": "NOT_MEASURED", "FinQA_OFFICIAL_TASK_ACCURACY": "NOT_MEASURED",
             "PORTABILITY_INTEGRATION_EFFORT": "NOT_MEASURED", "HUMAN_GROUND_TRUTH": "NOT_SATISFIED_AI_ONLY_DESIGN",
             "HISTORICAL_PRIVACY": "UNRESOLVED_OWNER_ACKNOWLEDGED", "MANUSCRIPT_READY": "BLOCKED", "PUBLIC_RELEASE_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED"}
    store.write("publication_gates/current_gate.json", gates)
    store.write("statistics/withdrawn_V3_inference.json", {"prior_run": str(prior.directory.relative_to(ROOT)),
                "status": "V3_P_AND_CI_WITHDRAWN_SAMPLE_DEPENDENT_CONTEXT", "descriptive_counts": "PRESERVED_NOT_ERASED",
                "superseding_primary": str(primary.directory.relative_to(ROOT)), "secondary_corpus": "V3_DESCRIPTIVE_NOT_V4"})
    store.write("task_status.csv", "task,status,reason\nT15,PARTIAL_HISTORY_UNRESOLVED,owner_acknowledged_no_remote_write\nT16,DONE_SCOPED,local_tests_not_CI_install\nT17,PARTIAL,two_domain_pilot_but_software_only_confirmation\nT18,DONE_SCOPED,V4_fixed_context_prospective_finite_frame_AI_only\nT19,PARTIAL,existing_Python_Rust_not_new_team_consumer\nT20,PARTIAL,primary_two_deterministic_and_V3_secondary_eight_cells\nT21,PARTIAL,closed_lines_not_native_prose_or_protected_tool\nT22,NOT_EXECUTED,no_new_FinQA_official_accuracy\nT23,NOT_MEASURED,no_new_backend_effort_trial\nT24,DONE_SCOPED,original_byte_scoring_and_explicit_V3_stats_withdrawal\nT25,NOT_EXECUTED,no_new_manuscript_claim_integration\nT26,BLOCKED,rights_authors_history_and_remaining_science\n")
    report = DOCS / ("INDEPENDENT_QUERY_GOLD_COMPLETION_" + store.directory.name + ".md")
    text = "# 독립 질의·gold 경로 및 확인 실험 후속 결과\n\n" + f"검사 시각: {utc()}\n\n"
    text += "## 수행 결과\n\n"
    text += f"전체 Python 회귀 검사: {tests} passed. 기대된 duplicate-ZIP 경고2건은 negative test에서 발생했습니다.\n\n"
    text += "- 새 Treasury/Cargo 원문 기반 개발 파일럿: KO/EN24질의,8조건192행; Qwen 질의 실현과 Ministral blind annotation24/24, Phi50실호출. 파일럿을 확인셋으로 승격하지 않았습니다.\n"
    text += "- 기존 방법론의 반려(run_20261023T093051Z)는 결과 관측0건 상태로 보존했습니다. 개선한 유한 모집단 무작위 설계는 AI-only scoped 방법 검토 후 동결했습니다.\n"
    text += "- V3(run_20261023T094720Z)의480/480 관측은 유지하지만 표본에 따라 distractor 문맥이 달라지는 설계 결함 때문에 hypergeometric p/CI 해석은 철회했습니다. 그 표본과 제공 facts에 한 번이라도 노출된 출처는 모두 V4에서 제외했습니다.\n"
    text += f"- V4 새 확인 실험: 사례별 문맥을 추출 전 고정한 미관측 {N}개 소프트웨어 출처 그룹에서60개 SRSWOR;240질의,480표현별 행에서 Python/Rust와 원문 gold 일치480/480, 실패 그룹0. 단측95% 상한{upper}/{N}={upper/N:.4%}, 정확 p={p:.8f}. 이 추론은 해당 고정 잔여 모집단만 대상으로 합니다.\n"
    text += f"- 별도 V3 코퍼스 첫 SLM 노출 후속 실험:240질의×8조건, 실제 Phi 호출{counts['unique_phi_calls']}회, 보존 결과{counts['observed_rows']}행; 표현 쌍{counts['identical_pairs']}/{counts['paired_cases']} 동일. V4와 다른 corpus이며 새 primary 검정은 아닙니다. 동일 payload 응답 재사용은 독립 반복으로 세지 않았습니다.\n\n"
    text += "|선택|렌더링|ALLOW 완전 응답 /120|DENY 정확 /120|원시 ALLOW 정확 선택 /120|승인 출력의 원문 미지원 case /240|\n|---|---|---:|---:|---:|---:|\n"
    for s in summaries:
        if s["representation"] == "UIR":
            text += f"|{s['selector']}|{s['renderer']}|{s['ALLOW_complete']}|{s['DENY_correct']}|{s['ALLOW_raw_selection_exact']}|{s['unsupported_display_cases']}|\n"
    text += "\n양 표현이 같은 결과라면 UIR 우월성을 주장할 수 없습니다. 안전성은 공유 verifier/guard를 포함한 시스템 효과입니다. 단일 사실 질의이므로 다중 사실 safe-partial 이점은 검증하지 않았습니다.\n\n"
    text += "특히 SLM 원시 exact requested-subset 선택과 shared guard 이후의 성공을 분리해야 합니다. SLM이 과다 선택한 catalog를 guard가 걸러서 정답을 표시한 경우 모델의 질의 이해 성공으로 해석하지 않습니다. SLM renderer의 빈 응답도 실패/utility 저하로 보존했습니다.\n\n"
    text += "## 증거 경계와 미완료 항목\n\n"
    text += "질의는 고정된 controlled-language 문법이며 Qwen은 템플릿 실현 역할입니다. Gold는 원문 숫자 투영+명시적 정책 배정으로 계산했고, 별도 채점 경로가 원문을 다시 읽었습니다. 일반 자연어 의미 정확성·독립 인간 gold·독립 연구팀 검증은 아닙니다.\n\n"
    text += "실제 canonical gold의 positive visibility 실패, masked 접근 차단, mutated-gold 불변성을 검사했습니다. 네트워크는 host loopback 공유이며 trusted host/kernel/Ollama를 가정합니다. 전체 workspace를 runtime에 마운트하지 않았습니다.\n\n"
    text += "Ministral 방법 검토 원문은 보존했으나 일부 해석 오류가 있습니다: 관측 전 runtime_decisions=0을 로그 부재로 읽었고, AUCR을 잘못 풀어 썼으며 single-primary/no-other-tests를 확인 검정 부재로 읽었습니다. AI 승인 자체를 과학적 진실/인간 승인으로 사용하지 않습니다. 실제 동결 시각·실행 로그·산술 검산이 근거입니다.\n\n"
    text += "V4 AI 검토는 JSON상 approved=true와 stop 종료였지만 자유서술 설명이 문장 중간에서 끝났습니다. 상세한 독립 방법 감사 완료로 해석하지 않으며 원문 그대로 보존했습니다.\n\n"
    text += "소프트웨어 confirmatory corpus와 재무 파일럿을 합쳐 두 도메인 확인 실험으로 부르지 않습니다. 새 금융 도메인 확인셋, native-prose whole-output 평가, FinQA 공식 실행 정확도, 별도 신규 consumer/실측 통합 비용, 저자/권리 승인 및 원고 통합은 남아 있습니다. 기존 부정 결과와 공개 이력 unresolved도 유지합니다. 모든 신규 결과/보고서는 LOCAL ONLY, 외부 업로드·push·투고는 수행하지 않았습니다.\n\n"
    text += "## 현재 게이트\n\n```json\n" + json.dumps(gates, indent=2, ensure_ascii=False) + "\n```\n"
    write_once(report, text)
    store.write("work_report_lineage.json", {str(report.relative_to(ROOT)): sha(report)})
    store.write("README.md", "# LOCAL ONLY independent-query/gold route completion checkpoint\n\nScoped primary and secondary results, raw-byte/scorer/sampling arithmetic verification. Full T-stage and publication remain blocked; see gate matrix.\n")
    store.seal()
    print(json.dumps({"run": str(store.directory), "verified_files": store.verify(), "report": str(report), "primary": stats, "secondary": counts}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", type=Path, required=True)
    p.add_argument("--primary-run", type=Path, required=True)
    p.add_argument("--secondary-score-run", type=Path, required=True)
    a = p.parse_args()
    run(a.results_dir, a.primary_run, a.secondary_score_run)
