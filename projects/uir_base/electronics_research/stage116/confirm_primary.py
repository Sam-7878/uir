"""Preregistered bounded primary trial on60 reserved publisher clusters.

Not a powered natural-language/financial-generalization or full SLM factorial claim.
AI-only method review, two separately coded scorer/runtime paths, real kernel boundary.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import random
import re
import secrets
import subprocess
import sys
import tomllib

from uir_common.ollama_client import OllamaClient
from .artifacts import RunStore
from .curated_pilot import DESIGNER, REVIEWER, namespace_args, role_call
from ..policy import ROOT, sha, utc, write_once
from .runner import DOCS, csv_text

EN = "Read {metric} from {entity}'s release_snapshot manifest in {unit}."
KO = "{entity} 릴리스 manifest에서 {metric}을 {unit} 단위로 읽으세요."
FIXED_EN = "For release_snapshot, fetch {entity}.{metric} as {unit}."
FIXED_KO = "release_snapshot에서 {entity}.{metric} 값을 {unit}(으)로 조회하세요."


def independent_query_reference(raw):
    if raw.startswith("For release_snapshot, fetch "):
        coordinate, unit = raw.removeprefix("For release_snapshot, fetch ").split(" as ")
        entity, metric = coordinate.split(".")
        unit = unit.removesuffix(".")
    elif raw.startswith("release_snapshot에서 "):
        coordinate, unit = raw.removeprefix("release_snapshot에서 ").split(" 값을 ")
        entity, metric = coordinate.split(".")
        unit = unit.removesuffix("(으)로 조회하세요.")
    elif raw.startswith("Read "):
        metric, tail = raw.removeprefix("Read ").split(" from ")
        entity, unit = tail.split("'s release_snapshot manifest in ")
        unit = unit.removesuffix(".")
    else:
        entity, tail = raw.split(" 릴리스 manifest에서 ")
        metric, unit = tail.split("을 ")
        unit = unit.removesuffix(" 단위로 읽으세요.")
    return dict(entity=entity, metric=metric, unit=unit, period="release_snapshot")


def reference_value(original_path, metric):
    original = tomllib.loads(original_path.read_text())["package"]["version"]
    matched = re.match(r"^([0-9]+)\.([0-9]+)(?:\.|$)", original)
    if not matched or metric not in {"package_version_major", "package_version_minor"}:
        raise ValueError("REFERENCE_SOURCE_UNSUPPORTED")
    return str(int(matched[1 if metric.endswith("major") else 2]))


def bind_worker(runtime_dir, gold_path, *, hidden=True, overlay=None, mode="probe"):
    args = namespace_args(runtime_dir, gold_path, hidden=hidden, overlay=overlay, mode=mode)
    idx = args.index("--chdir")
    args[idx:idx] = ["--ro-bind", str(ROOT / "target/debug/uir_contract_eval"), "/consumer/uir_contract_eval"]
    args[args.index("projects.uir_base.electronics_research.stage116.role_runtime")] = "projects.uir_base.electronics_research.stage116.confirm_runtime"
    return args


def hypergeom_lower_tail(N, n, failures_in_frame, observed):
    denominator = math.comb(N, n)
    return sum(math.comb(failures_in_frame, k) * math.comb(N - failures_in_frame, n - k)
               for k in range(max(0, n - (N - failures_in_frame)), min(observed, n, failures_in_frame) + 1)) / denominator


def frame_upper(N, n, observed, alpha=.05):
    return max(F for F in range(observed, N + 1) if hypergeom_lower_tail(N, n, F, observed) > alpha)


def run(directory, reserve_dir, design_srswor=False, exclude_observed_primary=None):
    reserve = RunStore(reserve_dir)
    reserve.verify()
    reserve_manifest = json.loads(reserve.path("source_registry/reserve_manifest.json").read_text())
    records = reserve_manifest["records"]
    if design_srswor:
        if reserve_manifest["target"] != "ALL_ELIGIBLE_FIRST500_FRAME" or any("catalog_page" in f for f in reserve_manifest["failures"]):
            raise ValueError("COMPLETE_FROZEN_FRAME_REQUIRED")
        for page in range(1, 6):
            if len(json.loads(reserve.path(f"source_registry/catalog_page_{page}.json").read_text())["crates"]) != 100:
                raise ValueError("INCOMPLETE_CATALOG_PAGE")
    if len(records) < 60 or len({r["parent_family"] for r in records}) != len(records) or any(r["parent_family"] == "github-owner:rust-lang" for r in records):
        raise ValueError("REQUIRED_60_DISJOINT_PUBLISHERS_NOT_READY")
    if not exclude_observed_primary:
        raise ValueError("V3_CONTEXT_DEPENDENT_CI_WITHDRAWN_USE_FRESH_FIXED_CONTEXT_FRAME")
    observed = RunStore(exclude_observed_primary)
    observed.verify()
    seen_rows = [json.loads(x) for x in observed.path("runtime/runtime.jsonl").read_text().splitlines()]
    seen_parents = {r["family"] for r in seen_rows}
    seen_fact_entities = {f["entity"] for r in seen_rows for f in r["source"]["facts"]}
    records = sorted([r for r in records if r["parent_family"] not in seen_parents and r["source_id"].upper().replace("-", "_") not in seen_fact_entities], key=lambda r: r["parent_family"])
    if len(records) < 60:
        raise ValueError("INSUFFICIENT_TRULY_UNOBSERVED_FIXED_FRAME")
    frame_records = records[:]
    store = RunStore(directory)
    store.create()
    store.write("statistical_correction_of_prior_V3.json", {"prior_run": str(observed.directory.relative_to(ROOT)),
                "prior_manifest_sha256": sha(observed.path("evidence_manifest.json")),
                "prior_p_and_CI_status": "WITHDRAWN_INVALID_SAMPLE_DEPENDENT_DISTRACTOR_CONTEXT",
                "prior_observed_rows_status": "PRESERVE_DESCRIPTIVE_ONLY", "prior_secondary_factorial_status": "DESCRIPTIVE_ONLY_NOT_NEW_PRIMARY",
                "new_trial": "FRESH_UNOBSERVED_SOURCE_REMAINDER_FIXED_CONTEXTS_BEFORE_SAMPLING",
                "fresh_frame_outcomes_before_amendment": 0, "exclude_rule": "all prior observed sources, not based on success/failure"})
    frame_N = len(records)
    assignment = [{"family": r["parent_family"], "manifest_sha256": r["manifest_sha256"],
                   "distractor_parents": [frame_records[(i+1) % frame_N]["parent_family"], frame_records[(i+2) % frame_N]["parent_family"]]}
                  for i, r in enumerate(frame_records)]
    store.write("frame_contexts_before_random_seed.json", {"assignment": assignment, "selection_dependent": False,
                "excluded_observed_run": str(observed.directory.relative_to(ROOT)), "excluded_parents": sorted(seen_parents),
                "source_values_used_for_exclusion": False, "exclusion_rule": "ALL previously runtime-observed families and supplied fact entities, regardless of outcome"})
    if design_srswor:
        seed = secrets.randbits(256)  # drawn once before trial; no seed search/outcome peeking
        records = random.Random(seed).sample(sorted(records, key=lambda r: r["parent_family"]), 60)
        store.write("random_sample_before_outcomes.json", {"frame_N": frame_N, "n": 60, "seed": str(seed),
                    "selected_source_ids": [r["source_id"] for r in records], "trial_outcomes_seen": 0,
                    "method": "SIMPLE_RANDOM_SAMPLE_WITHOUT_REPLACEMENT"})
    elif len(records) != 60:
        raise ValueError("EXPLICIT_RANDOM_DESIGN_REQUIRED_FOR_COMPLETED_FRAME")
    for name in ("runtime", "private_evaluator_only", "curation", "isolation", "experiments", "scoring", "statistics", "preregistration"):
        store.path(name).mkdir()
    store.write("reserve_lineage.json", {"path": str(reserve.directory.relative_to(ROOT)), "manifest_sha256": sha(reserve.path("evidence_manifest.json"))})
    critical = list(Path(__file__).parent.glob("*.py")) + list((ROOT / "src/uir_common").glob("*.py"))
    critical += list((ROOT / "projects/uir_base/representation_research").glob("*.py"))
    critical += list((ROOT / "crates/poa-uir/src").rglob("*.rs"))
    critical += [ROOT / p for p in ("Cargo.toml", "Cargo.lock", "crates/poa-uir/Cargo.toml", "target/debug/uir_contract_eval")]
    code_snapshot = {str(p.relative_to(ROOT)): sha(p) for p in critical}
    store.write("code_snapshot.json", code_snapshot)
    store.write("runtime_environment.json", {"python": sys.version, "executable": sys.executable,
                "worker_python": subprocess.check_output(["/usr/bin/python3.14", "--version"], text=True).strip(),
                "bwrap_version": subprocess.check_output(["bwrap", "--version"], text=True).strip()})
    plan = {"stage": "T18_PRIMARY_116_V2", "primary_endpoint": "publisher cluster has any interpreter/state/value/authority discrepancy in its4 cases",
            "N_parent_clusters": 60, "N_cases": 240, "cases_per_cluster": "major EN/KO ALLOW; minor EN/KO DENY", "N_representation_cases": 480,
            "primary_conditions": ["UIR+deterministic+template", "equivalent_native+deterministic+template"],
            "other_six_SLM_cells": "SECONDARY_PLANNED_NOT_EXECUTED_IN_THIS_PRIMARY_TRIAL", "model_calls_in_runtime": 0,
            "scoring": "all240 cases, all60 clusters retained; error or missing row=cluster failure; no retries/outcome exclusions",
            "hypothesis": "conditional Bernoulli cluster failure rate>=.05; reject only if exact one-sided95 upper<.05",
            "zero_failure_upper": 1 - 0.05 ** (1 / 60), "multiple_testing": "ONE_PRIMARY_NO_OTHER_CONFIRMATORY_TESTS",
            "sampling_limits": "deterministic convenience frame; owner clusters not proven statistically independent; CI is conditional, not population sampling guarantee",
            "scope": "FINITE_S1_TYPED_INTERCHANGE_ON_SOFTWARE_MANIFESTS_NOT_GENERAL_NL_OR_FINANCIAL_TRANSFER",
            "template_disjointness": "new literal grammar families versus pilot At/기준 and historical show/보여주세요; same single-fact intent NOT claimed novel",
            "source_disjointness": "all60 owners distinct; excludes pilot rust-lang and Treasury; old S/R financial/synthetic query datasets not reused",
            "annotation_truth": "DECLARED_CNL_AND_ORIGINAL_SOURCE_MACHINE_GOLD_AI_ONLY_METHOD_REVIEW_NOT_HUMAN_GOLD",
            "human_effort": "NOT_MEASURED", "native_prose_AUCR": "NOT_MEASURED", "author_signature": "PENDING_NOT_REQUIRED_FOR_LOCAL_TRIAL"}
    if design_srswor:
        plan.update(stage="T18_PRIMARY_116_V4_FIXED_CONTEXT_SRSWOR", frame_N=frame_N, sampling_design="SRSWOR_60_FROM_FROZEN_UNOBSERVED_ELIGIBLE_REMAINDER",
                    hypothesis="finite eligible owner-frame failure fraction>=.05; exact hypergeometric one-sided test",
                    zero_failure_upper=frame_upper(frame_N, 60, 0) / frame_N,
                    sampling_limits="Design-based inference ONLY to the frozen finite eligible frame. No independent-owner/Bernoulli assumption, no population outside this convenience frame.",
                    actual_execution="480 actual Python decisions AND480 actual Rust decisions after freeze in kernel-masked process. Zero runtime LLM calls is not zero executions.",
                    gold_definition="Exact major/minor integer projection of original normalized published package.version; independent string-regex reference versus runtime split parser, no interpreter self-labels or AI value labels.",
                    prior_rejected_method="run_20261023T093051Z; zero trial outcomes generated; preserve rejection unchanged",
                    prior_V3_statistics="WITHDRAWN_CONTEXT_DEPENDED_ON_SELECTED_SAMPLE; preserve480/480 descriptive results and original bytes",
                    fixed_contexts_sha256=sha(store.path("frame_contexts_before_random_seed.json")),
                    context_assignment="Each frame parent has two deterministic neighbors in the full sorted unobserved frame BEFORE seed; NOT sample neighbors. Its4case outcome is fixed regardless of sampled companions.",
                    fresh_frame_prior_runtime_observations=0,
                    template_disjointness="For/fetch and release_snapshot에서 new literal grammar versus prior Read/manifest and pilot At/기준; NOT a novel semantic task")
    store.write("preregistration/protocol_before_curation.json", plan)
    client = OllamaClient("http://127.0.0.1:18747")
    installed = {m["name"]: m for m in client.get("/api/tags")["models"]}
    intended_templates = {"EN": FIXED_EN, "KO": FIXED_KO}
    templates = role_call(store, client, installed, "heldout_question_template_designer", DESIGNER,
                          [{"role": "system", "content": 'As a question designer, emit these exact two controlled-language templates with unchanged placeholders. JSON {"EN":"...","KO":"..."}. No answers, source values, IDs or labels.'},
                           {"role": "user", "content": json.dumps(intended_templates, ensure_ascii=False)}],
                          {"type": "object", "required": ["EN", "KO"], "properties": {"EN": {"type": "string"}, "KO": {"type": "string"}}}, budget=512)
    if templates != intended_templates:
        raise ValueError("QUESTION_TEMPLATE_CONFORMANCE_FAILED_NO_POSTHOC_REPAIR")
    catalogs, originals, entity_seen = [], {}, set()
    # Runtime catalog is separately built from source; no reference value function used here.
    for source in frame_records:
        path = ROOT / source["manifest_ref"] if "manifest_ref" in source else reserve.path(source["manifest_path"])
        if sha(path) != source["manifest_sha256"]: raise ValueError("RESERVE_SOURCE_CHANGED")
        package = tomllib.loads(path.read_text())["package"]
        if package.get("name") != source["source_id"]:
            raise ValueError("PUBLISHED_SOURCE_NAME_MISMATCH")
        entity = source["source_id"].upper().replace("-", "_")
        if entity in entity_seen: raise ValueError("ENTITY_NORMALIZATION_COLLISION")
        entity_seen.add(entity)
        components = str(package["version"]).split(".")
        facts = []
        for i, component in enumerate(("major", "minor")):
            if not components[i].isascii() or not components[i].isdigit(): raise ValueError("RUNTIME_VERSION_CONVERSION_UNSUPPORTED")
            facts.append({"id": entity + "_" + component, "entity": entity, "metric": "package_version_" + component,
                          "period": "release_snapshot", "unit": "COUNT", "value": str(int(components[i])),
                          "provenance": source["parent_family"] + ":" + source["manifest_sha256"] + "/package/version#" + component,
                          "status": "current", "visibility": "public"})
        catalogs.append(facts)
        originals[entity] = (path, source)
    runtime, gold = [], []
    frame_positions = {s["parent_family"]: i for i, s in enumerate(frame_records)}
    for selected_index, source in enumerate(records):
        index = frame_positions[source["parent_family"]]
        facts = catalogs[index] + catalogs[(index + 1) % frame_N] + catalogs[(index + 2) % frame_N]
        entity = catalogs[index][0]["entity"]
        for part, action in (("major", "ALLOW"), ("minor", "DENY")):
            for language in ("EN", "KO"):
                cid = f"F116-{selected_index:02}-{part}-{language}"
                raw = templates[language].format(entity=entity, metric="package_version_" + part, unit="COUNT")
                semantics = independent_query_reference(raw)
                value = reference_value(originals[semantics["entity"]][0], semantics["metric"])
                gold.append({"case_id": cid, "family": source["parent_family"], "semantics": semantics, "value": value,
                             "expected_state": "FULL_VERIFIED_ANSWER" if action == "ALLOW" else "DENY",
                             "source_manifest_sha256": source["manifest_sha256"]})
                runtime.append({"case_id": cid, "family": source["parent_family"], "raw_user_request": raw,
                                "authority": {"version": "H116-P1", "decision": action, "approved": False},
                                "source": {"version": "H116-FROZEN-SOURCE-1", "facts": facts, "trusted_provenance": sorted({f["provenance"] for f in facts})},
                                "split": "CONFIRMATORY_FRESH_FIXED_CORPUS"})
    store.jsonl("runtime/runtime.jsonl", runtime)
    store.jsonl("private_evaluator_only/gold.jsonl", gold)
    from .role_runtime import compile_query as pilot_parser
    from uir_common.query_contract import parse_raw as historical_parser
    def rejects(parser, text):
        try: parser(text)
        except ValueError: return True
        return False
    pilot_runtime = ROOT / "projects/uir_base/results/116_electronics_confirmatory_2026_10_23/run_20261023T091259Z/runtime/runtime.jsonl"
    pilot_rows = [json.loads(x) for x in pilot_runtime.read_text().splitlines()]
    old_query_set = {r["raw_user_request"] for r in pilot_rows}
    pilot_parents = {"github-owner:rust-lang", "US-Treasury"}
    pilot_hashes = set(json.loads(pilot_runtime.parent.parent.joinpath("source_lineage.json").read_text()).values())
    proof = {"source_parent_overlap_with_pilot": len({s["parent_family"] for s in records} & pilot_parents),
             "source_parent_overlap_with_observed_V3": len({s["parent_family"] for s in frame_records} & seen_parents),
             "fixed_context_assignment_before_random_seed_sha256": sha(store.path("frame_contexts_before_random_seed.json")),
             "source_byte_hash_overlap_with_pilot": sum(s["manifest_sha256"] in pilot_hashes for s in records),
             "license_text_sha256s": {p: sha(ROOT / p) for s in records for p in s.get("license_refs", [])},
             "exact_raw_request_overlap": sum(r["raw_user_request"] in old_query_set for r in runtime),
             "pilot_grammar_rejects_new_requests": sum(rejects(pilot_parser, r["raw_user_request"]) for r in runtime),
             "historical_show_grammar_rejects_new_requests": sum(rejects(historical_parser, r["raw_user_request"]) for r in runtime),
             "N_new_requests": len(runtime), "gold_values_are_exact_source_scalars_not_model_judgments": True,
             "gold_authority_DENY_labels_are_protocol_assignments": True, "gold_runtime_access_before_test": "OS_BOUNDARY_TEST_PENDING",
             "curator_scope": "AI_REALIZATION_OF_FIXED_CNL_TEMPLATES_NOT_INDEPENDENT_HUMAN_NL_DESIGN",
             "license_evidence": "accepted permissive expressions plus bundled license texts in source reserve; no public distribution approval",
             "runtime_decisions_observed": 0}
    store.write("preregistration/prospective_eligibility_evidence.json", proof)
    if proof["source_parent_overlap_with_pilot"] or proof["source_byte_hash_overlap_with_pilot"] or proof["exact_raw_request_overlap"] or proof["pilot_grammar_rejects_new_requests"] != 240 or proof["historical_show_grammar_rejects_new_requests"] != 240:
        raise ValueError("QUERY_GRAMMAR_DISJOINTNESS_FAILED")
    review = role_call(store, client, installed, "primary_method_review", REVIEWER,
                       [{"role": "system", "content": 'Independently review this prospective, bounded, deterministic software-contract trial BEFORE any test outcomes. Output JSON {"approved_bounded_trial":true/false,"limitations":[...],"reason":"..."}. Evaluate the protocol actually stated. Actual CPU Python/Rust executions occur even though runtime LLM calls=0. Source version integer projections and a declared controlled-language grammar have exact machine gold, not AI-generated value labels; no human NLP truth claim is made. In SRSWOR design, exact hypergeometric finite-frame inference does NOT assume statistical independence of owners. It does NOT generalize beyond that frozen frame. Retain limitations and reject genuine defects; do not invent author approval or broad NLP validation.'},
                        {"role": "user", "content": json.dumps({"protocol": plan, "templates": templates, "prospective_tests": {k: v for k, v in proof.items() if k != "license_text_sha256s"}}, ensure_ascii=False)}],
                       {"type": "object", "required": ["approved_bounded_trial", "limitations", "reason"], "properties": {"approved_bounded_trial": {"type": "boolean"}, "limitations": {"type": "array", "items": {"type": "string"}}, "reason": {"type": "string"}}}, budget=3072)
    store.write("preregistration/AI_ONLY_METHOD_REVIEW.json", review)
    if review["approved_bounded_trial"] is not True:
        store.write("gate.json", {"status": "BLOCKED_METHOD_REVIEW", "trial_outcomes": 0})
        store.seal()
        print(json.dumps({"status": "BLOCKED_METHOD_REVIEW", "run": str(store.directory)}))
        return
    store.write("preregistration/freeze_receipt.json", {"created_at_utc": utc(), "protocol_sha256": sha(store.path("preregistration/protocol_before_curation.json")),
                "runtime_sha256": sha(store.path("runtime/runtime.jsonl")), "gold_sha256_scorer_only": sha(store.path("private_evaluator_only/gold.jsonl")),
                "code_sha256s": json.loads(store.path("code_snapshot.json").read_text()), "method_review_sha256": sha(store.path("preregistration/AI_ONLY_METHOD_REVIEW.json")),
                "heldout_decisions_before_freeze": 0, "signature": "UNSIGNED_MACHINE_FREEZE_NOT_AUTHOR_SIGNOFF"})
    gold_path = store.path("private_evaluator_only/gold.jsonl")
    store.jsonl("private_evaluator_only/mutated_gold.jsonl", [{**g, "value": "WRONG", "expected_state": "WRONG"} for g in gold])
    probes = {}
    for name, args in (("positive", bind_worker(store.path("runtime"), gold_path, hidden=False)),
                       ("masked", bind_worker(store.path("runtime"), gold_path)),
                       ("mutated", bind_worker(store.path("runtime"), gold_path, overlay=store.path("private_evaluator_only/mutated_gold.jsonl")))):
        result = subprocess.run(args, text=True, capture_output=True, close_fds=True, timeout=60)
        probes[name] = {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        store.write("isolation/" + name + ".json", probes[name])
    boundary = ("GOLD_VISIBLE_TO_RUNTIME" in probes["positive"]["stderr"] and probes["positive"]["returncode"] != 0
                and probes["masked"]["returncode"] == probes["mutated"]["returncode"] == 0 and probes["masked"]["stdout"] == probes["mutated"]["stdout"])
    store.write("isolation/gold_boundary_receipt.json", {"passed": boundary, "canonical_mutation_invariance": boundary,
                "mount_isolation": True, "network": "SHARED_HOST_LOOPBACK", "heldout_decisions_during_probe": 0})
    if not boundary:
        store.write("gate.json", {"status": "BLOCKED_OS_ISOLATION", "trial_outcomes": 0})
        store.seal()
        print(json.dumps({"status": "BLOCKED_OS_ISOLATION", "run": str(store.directory)}))
        return
    print(json.dumps({"phase": "primary_freeze_and_gold_boundary_passed", "cases": 240, "clusters": 60}), flush=True)
    if any(sha(ROOT / p) != digest for p, digest in code_snapshot.items()):
        raise ValueError("CODE_CHANGED_AFTER_FREEZE")
    with store.path("experiments/primary_raw.jsonl").open("x") as output, store.path("experiments/primary_stderr.log").open("x") as error:
        execution = subprocess.run(bind_worker(store.path("runtime"), gold_path, mode="infer"), stdout=output, stderr=error, close_fds=True, text=True, timeout=180)
    answers = [json.loads(x) for x in store.path("experiments/primary_raw.jsonl").read_text().splitlines() if x]
    code_unchanged = all(sha(ROOT / p) == digest for p, digest in code_snapshot.items())
    outcomes = [r for r in answers if r["type"] == "outcome"]
    lookup = {(r["case_id"], r["representation"]): r for r in outcomes}
    duplicate_rows = len(outcomes) - len(lookup)
    scored, clusters = [], {}
    for g in gold:
        for representation in ("UIR", "SPECIALIZED"):
            row = lookup.get((g["case_id"], representation))
            passed = bool(code_unchanged and row and row["consumer_agreement"] and row["python"]["state"] == row["rust"]["state"] == g["expected_state"])
            if row:
                passed = passed and row["compiled_semantics"] == {**g["semantics"], "predicate": None}
            if row and g["expected_state"] == "FULL_VERIFIED_ANSWER":
                component = g["semantics"]["metric"].removeprefix("package_version_")
                expected_provenance = g["family"] + ":" + g["source_manifest_sha256"] + "/package/version#" + component
                passed = (passed and len(row["accepted_values"]) == 1 and row["accepted_values"][0]["value"] == g["value"]
                          and row["accepted_values"][0]["provenance"] == expected_provenance)
            if row and g["expected_state"] == "DENY":
                passed = passed and not row["accepted_values"] and not row["python"]["fact_ids"] and not row["rust"]["fact_ids"]
            clusters[g["family"]] = clusters.get(g["family"], False) or not passed
            scored.append({"case_id": g["case_id"], "family": g["family"], "representation": representation, "passed": passed, "row_present": row is not None})
    failures = sum(clusters.values())
    summary = {"status": "PRIMARY_CONFIRMATORY_TRIAL_EXECUTED_SCOPED", "N_parent_clusters": 60, "N_cases": 240,
               "representation_rows_expected": 480, "representation_rows_observed": len(outcomes), "duplicate_rows": duplicate_rows,
               "execution_returncode": execution.returncode, "code_unchanged": code_unchanged, "passed_representation_rows": sum(r["passed"] for r in scored),
               "failed_clusters": failures, "conditional_exact_one_sided95_upper_if_zero_failures": 1 - .05 ** (1 / 60) if failures == 0 else None,
               "conditional_threshold_test": "REJECT_FAILURE_RATE_GE_5_PERCENT_UNDER_BERNOULLI_ASSUMPTION" if failures == duplicate_rows == execution.returncode == 0 and len(outcomes) == 480 else "NOT_PASSED",
               "population_guarantee": False, "UIR_superiority": "NOT_ESTABLISHED_EQUAL_CAPABILITY_CONTROL", "other_SLM_factorial_cells": "NOT_EXECUTED",
               "human_ground_truth": False, "independent_implementation_teams": False, "no_posthoc_tuning_or_retries": True}
    if design_srswor:
        upper = frame_upper(frame_N, 60, failures)
        p = hypergeom_lower_tail(frame_N, 60, math.ceil(.05 * frame_N), failures)
        summary.update(statistical_design="EXACT_FINITE_FRAME_SRSWOR", frame_N=frame_N, failed_frame_groups_one_sided95_upper=upper,
                       failure_fraction_frame_upper=upper / frame_N, exact_primary_p=p,
                       conditional_exact_one_sided95_upper_if_zero_failures=None,
                       conditional_threshold_test="DESIGN_BASED_FRAME_NULL_REJECTED" if p < .05 and duplicate_rows == execution.returncode == 0 and len(outcomes) == 480 else "FRAME_NULL_NOT_REJECTED",
                       inference_scope="ONLY_FROZEN_ELIGIBLE_FRAME_NO_BERNOULLI_INDEPENDENCE_ASSUMPTION")
    store.jsonl("scoring/primary_per_case.jsonl", scored)
    store.write("statistics/primary_summary.json", summary)
    store.write("gate.json", {"PRIMARY_FIXED_CORPUS_EVIDENCE": "EXECUTED_SCOPED", "FULL_CONFIRMATORY_SLM_FACTORIAL": "INCOMPLETE",
                "MANUSCRIPT_READY": "BLOCKED", "PUBLIC_RELEASE_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED"})
    report = DOCS / ("CONFIRMATORY_PRIMARY_" + store.directory.name + ".md")
    write_once(report, "# Prospective fixed-corpus primary trial (AI-only methods review)\n\n" + json.dumps(summary, indent=2) + "\n\n"
               "Protocol, source/code/query/gold hashes and isolated model-method review froze before any240-case runtime decision. "
               "Positive visibility control, kernel gold masking and canonical-label mutation invariance were tested without case decisions. "
               "The trial is deterministic S1 interoperability/authority binding on normalized software-package manifests, not broad NL/financial generalization or SLM task accuracy. "
               + ("Inference is design-based only to the frozen finite eligible convenience frame, using SRSWOR and exact hypergeometric inversion; no independent-owner/Bernoulli assumption or outside-frame guarantee. " if design_srswor else "Owner independence and the Bernoulli CI model remain unverified assumptions. ") +
               "New syntactic template families do not imply a new semantic task. Original source version components are machine gold, not human annotations. "
               "Six secondary SLM factorial cells, native-prose safety, FinQA and human effort remain unexecuted/unmeasured. No source/outcome was tuned after trial.\n")
    store.write("work_report_lineage.json", {str(report.relative_to(ROOT)): sha(report)})
    store.write("README.md", "# LOCAL ONLY prospective fixed-corpus primary evidence\n\nBounded deterministic S1 trial, with explicit AI-only/convenience-sample/conditional-CI limitations. Not full T15–T26 or submission completion.\n")
    store.seal()
    print(json.dumps({"run": str(store.directory), "verified_files": store.verify(), "summary": summary}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--source-reserve", type=Path, required=True)
    parser.add_argument("--design-srswor", action="store_true")
    parser.add_argument("--exclude-observed-primary", type=Path)
    args = parser.parse_args()
    run(args.results_dir, args.source_reserve, args.design_srswor, args.exclude_observed_primary)
