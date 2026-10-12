"""N00/N01/N02/N05/N06 offline evidence completion. Never downloads or infers.

Historical programs/captures remain unchanged. New artifacts are versioned and
scoped; completing arithmetic reproduction is not completing submission gates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
import zipfile

from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts import revision_support as support
from projects.uir_base.scripts.next_frontend import compile_raw, sandbox_action

ROOT, BASE, FROZEN = a.ROOT, a.BASE, a.FROZEN
OLD = BASE / "mdpi_revision_2026_10_11"
DEFAULT = BASE / "mdpi_next_2026_10_11_v2"
LINEAGE = {
    "frozen_v1": ROOT / "projects/uir_base/evaluation/uir_external/frozen_test_v1.jsonl",
    "frozen_v2": ROOT / "archive/uir_base/results/uir_phase3b/frozen_test_v2.jsonl",
    "real_fact": ROOT / "archive/uir_base/results/uir_phase3b/real_fact_subset.jsonl",
}
COMPARE = ("metrics_case_level.csv", "internal_utility_recomputed.csv", "d1_schema_case_audit.csv",
           "halueval_case_audit.csv", "halueval_recomputed.csv", "halueval_transition_tables.csv",
           "paired_statistics.csv", "latency_case_results.csv", "latency_summary.csv", "cohort_manifest.csv")


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def checked_path(root, relative, expected):
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Non-root-relative dependency")
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Dependency escapes root or is a symbolic link")
    if not path.is_file():
        raise FileNotFoundError(f"MISSING required dependency: {relative}")
    if a.digest(path) != expected:
        raise ValueError(f"Dependency hash mismatch: {relative}")
    return path


def independent_label(raw, model, pipeline):
    if pipeline == "C1":
        value = a.yes_no(raw)
        return ("PRESENT", value) if value else ("AMBIGUOUS" if re.search(r"\b(yes|no)\b", raw, re.I) else "MISSING", None)
    field = "judgement" if model == "Phi-3.5" else "overall_hallucination"
    # Extract a completed literal even when the enclosing JSON is truncated.
    labels = re.findall(r'"' + field + r'"\s*:\s*"(Yes|No)"', raw, re.I)
    distinct = {v.title() for v in labels}
    if len(distinct) > 1:
        return "AMBIGUOUS", None
    if distinct:
        return "PRESENT", distinct.pop()
    obj = a.extract(raw)
    return ("INVALID" if obj and field in obj else "MISSING"), None


def metric_transitions(out, runtime, gold, historical):
    from jsonschema import Draft202012Validator
    from projects.uir_base.evaluation.uir_phase4f.rescore_d1_inplace import score_constrained_case
    new_rows = {(r["pipeline"], r["case_id"]): r for r in csv_rows(out / "historical_reanalysis/metrics_case_level.csv")}
    changes = []
    for record in historical:
        cid, pipeline = record["case_id"], record["pipeline"]
        row = new_rows[pipeline, cid]; old = record["metrics"]
        changes.append({"case_id": cid, "pipeline": pipeline, "raw_output_ref": "projects/uir_base/results/uir_phase4d/per_case_evidence_actual.jsonl",
                        "raw_record_hash": hash_object(record),
                        "old_complete": old.get("complete_claim_accuracy", "NOT_MEASURED"), "new_complete": row["complete"],
                        "old_unsupported": old.get("unsupported_claim", "NOT_MEASURED"), "new_structured_claim_unsupported": row["unsupported_accepted"],
                        "old_accepted": old.get("accepted", "NOT_MEASURED"), "new_accepted": row["accepted"],
                        "reason": "historical rejection/prose/gold-support vs structured exact-fields runtime-catalog support",
                        "evidence_kind": "historical_reanalysis"})
    validator = Draft202012Validator(a.SCHEMA)
    errors = []; old_d1 = []; mismatches = Counter()
    d1_path = BASE / "uir_phase4f/d1_constrained_raw_600.jsonl"
    for index, record in enumerate(a.read(d1_path), 1):
        cid = record["case_id"]; raw = record["raw_response"]
        old = score_constrained_case(raw, gold[cid]); old_d1.append(old)
        new = new_rows["D1_EXTERNAL_CONSTRAINED_DECODING", cid]
        proposed = a.claim_set(a.extract(raw)); catalog = a.claim_set({"claims": runtime[cid].get("context_claims", [])})
        differences = {field: sum(any(candidate[i] != fact[i] and all(candidate[j] == fact[j] for j in (1, 2) if j != i)
                                          for fact in catalog) for candidate in proposed - catalog)
                       for i, field in enumerate(a.CLAIM_FIELDS)}
        mismatches.update(differences)
        changes.append({"case_id": cid, "pipeline": "D1_EXTERNAL_CONSTRAINED_DECODING", "raw_output_ref": f"{d1_path.relative_to(ROOT)}#line={index}",
                        "raw_record_hash": hash_object(record), "old_complete": old["is_complete"], "new_complete": new["complete"],
                        "old_unsupported": old["accepted_unsupported_claim"], "new_structured_claim_unsupported": new["unsupported_accepted"],
                        "old_accepted": "NOT_MEASURED", "new_accepted": new["accepted"],
                        "reason": json.dumps({"old": "attribute/provenance coverage", "new": "exact seven-field binding", "mismatches_nonexclusive": differences}),
                        "evidence_kind": "historical_reanalysis"})
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append({"case_id": cid, "raw_output_ref": str(d1_path.relative_to(ROOT)), "raw": raw,
                           "parse_error": str(exc), "schema_path": None, "finish_reason": "NOT_RECORDED"})
            continue
        for error in validator.iter_errors(obj):
            errors.append({"case_id": cid, "raw_output_ref": str(d1_path.relative_to(ROOT)), "raw": raw,
                           "parse_error": None, "schema_path": list(error.absolute_schema_path), "error": error.message,
                           "finish_reason": "NOT_RECORDED"})
    a.write_csv(out / "case_metric_transition.csv", changes)
    jsonl(out / "d1_raw_schema_errors.jsonl", errors)
    a.write_json(out / "metric_change_diagnostics.json", {
        "legacy_D1_pure_scorer_reexecuted_not_inplace_main": True,
        "legacy_D1_complete": sum(r["is_complete"] for r in old_d1),
        "legacy_D1_unsupported": sum(r["accepted_unsupported_claim"] for r in old_d1),
        "D1_field_mismatches_nonexclusive": dict(mismatches),
        "old_phi_72_percent": "hardcoded literal in rescore_publication_final.py; no per-case estimator was found",
        "old_qwen_50_percent": "run_qwen_external_full.py initialized prediction=No before JSON parse; not missing-aware semantic ability",
        "prose_safety": "NOT_MEASURED", "evidence_kind": "historical_reanalysis"})


def hash_object(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def external_audit(out):
    hrs, hgs = (a.unique(a.read(FROZEN / name)) for name in ("halueval_qa_runtime_200.jsonl", "halueval_qa_scoring_200.jsonl"))
    rows = []; taxonomy = []
    for model in ("Phi-3.5", "Qwen2.5-7B"):
        for task in ("halueval", "finqa"):
            for pipeline in ("C1", "C8"):
                path = BASE / (f"uir_phase4d/{task}_predictions_actual_{pipeline}.jsonl" if model == "Phi-3.5" else f"uir_phase4e/qwen_{task}_{pipeline}_raw.jsonl")
                for index, record in enumerate(a.read(path), 1):
                    raw = record.get("raw_response", record.get("generation", {}).get("raw_response", ""))
                    finish = record.get("generation", {}).get("finish_reason", record.get("finish_reason", "NOT_RECORDED"))
                    taxonomy.append({"case_id": record["case_id"], "model": model, "task": task, "pipeline": pipeline,
                                     "raw_output_ref": f"{path.relative_to(ROOT)}#line={index}", "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                                     "strict_json": a.parse(raw) is not None, "finish_reason": finish,
                                     "truncation_status": "CONFIRMED_TOKEN_LIMIT" if finish in {"length", "max_tokens"} else "UNASSESSABLE" if finish == "NOT_RECORDED" else "NOT_TOKEN_LIMIT",
                                     "unsupported_claim_status": "NOT_MEASURED", "evidence_kind": "historical_reanalysis"})
                    if task != "halueval":
                        continue
                    cid = record["case_id"]; parsed = a.score_halu(raw, model, pipeline, hrs[cid], hgs[cid])
                    status, label = independent_label(raw, model, pipeline)
                    old_label = record.get("prediction", "NOT_MEASURED")
                    rows.append(parsed | {"raw_output_ref": f"{path.relative_to(ROOT)}#line={index}",
                        "raw_label_status": status, "independent_semantic_label": label,
                        "independent_label_correct": label == hgs[cid]["gold_judgement"] if label else "NOT_EVALUABLE",
                        "strict_native_response": bool(re.fullmatch(r"\s*(Yes|No)\s*", raw, re.I)) if pipeline == "C1" else a.parse(raw) is not None,
                        "old_prediction": old_label, "old_prediction_correct": old_label == hgs[cid]["gold_judgement"] if old_label != "NOT_MEASURED" else "NOT_MEASURED",
                        "finish_reason": finish, "evidence_kind": "historical_reanalysis"})
    jsonl(out / "halueval_extraction_audit.jsonl", rows)
    a.write_csv(out / "external_error_taxonomy.csv", taxonomy)


def candidate_audit(out, runtime, gold, historical):
    from evaluation.uir_phase4d.pipelines import build_internal_request
    by_id = {r["case_id"]: (i, r) for i, r in enumerate(historical, 1) if r["pipeline"] == "C5_GUARDRAIL_STYLE"}
    if len(by_id) != 600:
        raise ValueError("C5 cohort mismatch")
    manifest = []; replay = []
    for cid, case in sorted(runtime.items()):
        line, record = by_id[cid]; gate = build_internal_request("C8_FINAL_UIR_B6", case)
        raw = record.get("generation", {}).get("raw_response", "")
        refs = a.claim_set(a.extract(raw)); facts = case.get("context_claims", [])
        selected = [f for f in facts if a.key(f) in refs] if record["model_invoked"] else []
        final = json.dumps({"answer": "", "claims": selected}, ensure_ascii=False) if selected else "REJECTED: no verified claim"
        row = a.score_claims(final, raw, case, gold[cid], "C5_ALL_CAPTURED_CANDIDATES_PROJECTION", False, None)
        row.update(evidence_kind="counterfactual_replay", original_candidate_model_invoked=record["model_invoked"],
                   selection_reason="all_historical_C5_cases_no_C8_success_filter")
        replay.append(row)
        manifest.append({"case_id": cid, "original_model_invoked": record["model_invoked"],
                         "raw_candidate_ref": f"projects/uir_base/results/uir_phase4d/per_case_evidence_actual.jsonl#line={line}",
                         "raw_candidate_sha256": hashlib.sha256(raw.encode()).hexdigest() if record["model_invoked"] else "NOT_APPLICABLE",
                         "raw_candidate_status": "PRESENT" if record["model_invoked"] else "NOT_INVOKED",
                         "pre_gate_decision": record["policy_decision"], "post_guard_ref": "same_record.final_output",
                         "common_UIR_preexecution_gate": bool(gate["invoke"]), "old_replay_exclusion_reason": "INCLUDED" if gate["invoke"] else gate["policy_decision"],
                         "new_projection_stage": "fresh_deterministic_projection_of_all_original_candidates",
                         "fresh_model_calls": 0, "evidence_kind": "counterfactual_replay"})
    a.write_csv(out / "candidate_stage_manifest.csv", manifest)
    a.write_csv(out / "replay_exclusion_audit.csv", [r for r in manifest if r["original_model_invoked"] and not r["common_UIR_preexecution_gate"]])
    a.write_csv(out / "matched_case_results.csv", replay)
    a.write_csv(out / "all_candidate_replay_summary.csv", a.summarize_internal(replay))


def families(out, runtime):
    sources = {}
    for dataset, path in LINEAGE.items():
        for row in a.read(path):
            sources[dataset, hash_object(row)] = (row, str(path.relative_to(ROOT)))
    parent = {cid: cid for cid in runtime}
    def find(cid):
        while parent[cid] != cid:
            parent[cid] = parent[parent[cid]]; cid = parent[cid]
        return cid
    def union(left, right):
        left, right = find(left), find(right)
        parent[max(left, right)] = min(left, right)
    keys = {}; rows = []
    for cid, case in sorted(runtime.items()):
        source = sources.get((case["source_dataset"], case["source_row_hash"]))
        if source is None:
            raise ValueError(f"Unresolved original lineage: {cid}")
        original, path = source; evidence = []
        pair = original.get("pair_id")
        if pair:
            evidence.append("pair:" + case["source_dataset"] + ":" + pair)
        elif original.get("category") in {"parallel", "numeric_provenance"} and re.search(r"-(KO|EN)$", cid):
            # ID alone is insufficient: bind the declared category AND original semantic/fact signature.
            signature = hash_object({"semantics": original.get("expected_semantics"), "facts": original.get("expected_claims")})
            evidence.append("verified-original-pair:" + re.sub(r"-(KO|EN)$", "", cid) + ":" + signature)
        for fact in original.get("context_claims", original.get("expected_claims", [])):
            provenance = str(fact.get("provenance", ""))
            if provenance:
                accession = re.search(r"\d{10}-\d{2}-\d{6}", provenance)
                document = "sec-accession:" + accession.group(0) if accession else provenance.split("#sha256=")[0]
                evidence.append("document-or-fixture:" + document)
        template = original.get("template_id")
        if template:
            evidence.append("declared-template:" + case["source_dataset"] + ":" + template)
        for item in evidence:
            if item in keys:
                union(cid, keys[item])
            else:
                keys[item] = cid
        rows.append({"case_id": cid, "source_row_hash": case["source_row_hash"], "source_ref": path,
                     "source_original_case_id": original["case_id"], "lineage_keys": json.dumps(sorted(set(evidence))),
                     "lineage_status": "HASH_MATCHED_ORIGINAL", "unmeasured_dependence": "unrecorded template/document relationships"})
    for row in rows:
        row["source_family_id"] = "F-" + hashlib.sha256(find(row["case_id"]).encode()).hexdigest()[:20]
    a.write_csv(out / "source_family_manifest.csv", rows)
    mapping = {r["case_id"]: r["source_family_id"] for r in rows}
    scored = []
    for row in csv_rows(out / "historical_reanalysis/metrics_case_level.csv"):
        for field in ("commit_eligible", "complete", "safe_claim_answered"):
            row[field] = row[field] == "True"
        row["source_cluster"] = mapping[row["case_id"]]; scored.append(row)
    a.write_csv(out / "paired_source_family_statistics.csv", a.paired(scored))
    return mapping


def annotations_and_conformance(out):
    run = OLD / "ai_reviews/20261011T114157Z"
    packets = a.read(run / "review_packets.jsonl")
    annotation_dir = out / "annotations"; annotation_dir.mkdir()
    # New packets use existing opaque IDs; do not regenerate historical labels.
    for name in ("H1", "H2"):
        jsonl(annotation_dir / f"{name}_blinded_cases.jsonl", packets)
        a.write_csv(annotation_dir / f"{name}_labels_template.csv", [
            {"opaque_case_id": r["case_id"], "annotator_id": name, "independent_decision": "",
             "expertise": "", "reviewed_at": "", "minutes": "", "uncertainty": "", "guideline_version": ""} for r in packets])
    a.write_json(out / "study_design_amendment.json", {
        "route": "B_AI_ONLY", "approved_by": "human_user_in_current_task", "approval_date_local": "2026-10-11",
        "W08_original_human_requirement": "NOT_SATISFIED", "human_annotation_performed": False,
        "allowed_claims": ["restricted bilingual CNL conformance", "typed policy/evidence contract system evaluation"],
        "excluded_claims": ["human validated", "expert gold", "unrestricted natural language semantic accuracy", "statistically independent AI errors"]})
    texts = ["verify TSLA revenue 2025", "TSLA의 2025년 매출 검증",
             "verify TSLA revenue 2025 if approval", "verify TSLA revenue 2025 unless approval",
             "verify TSLA revenue 2025 if approval AND (entity_verified OR verified_provenance)",
             "verify TSLA revenue 2025 if (approval AND entity_verified) OR verified_provenance",
             "verify TSLA revenue 2025 if unknown", "verify TSLA revenue 2025 if approval AND"]
    jsonl(out / "frontend_case_results.jsonl", [{"input": text, "evidence_kind": "deterministic_execution", "gold_kind": "synthetic_conformance_not_human",
           "result": compile_raw(text, policy_snapshot="p1", evidence_snapshot="e1")} for text in texts])
    action_configs = [{}, {"action": "write", "policy": "DENY"}, {"action": "write", "policy": "READ_ONLY"},
                      {"policy": "REQUIRE_APPROVAL"}, {"policy": "REQUIRE_APPROVAL", "approved": True}, {"current_snapshot": "p2"}]
    jsonl(out / "action_traces.jsonl", [{"case_id": f"SANDBOX-{i}", "evidence_kind": "deterministic_execution",
           "scope": "in_memory_conformance_not_attack_benchmark", **sandbox_action(**kwargs)} for i, kwargs in enumerate(action_configs)])


def output_channels(out, runtime, historical):
    from evaluation.uir_phase4d.runtime.policy_engine import PolicyEngine
    policy = PolicyEngine()
    rows = []
    for index, record in enumerate(historical, 1):
        cid = record["case_id"]; final = record["final_output"]
        parsed = a.extract(final); rejected = not final.strip() or final.lstrip().upper().startswith("REJECTED:")
        claims = a.claim_set(parsed) if not rejected else set()
        facts = {a.key(fact) for fact in runtime[cid].get("context_claims", [])}
        decision = policy.evaluate(runtime[cid]["input"], requested_attribute=runtime[cid].get("requested_attribute", ""))
        rows.append({"case_id": cid, "pipeline": record["pipeline"], "raw_text_ref": f"projects/uir_base/results/uir_phase4d/per_case_evidence_actual.jsonl#line={index}:generation.raw_response",
                     "raw_structured_claims": sorted(a.claim_set(a.extract(record.get("generation", {}).get("raw_response", "")))),
                     "accepted_structured_claims": sorted(claims), "accepted_rendered_text_ref": f"same_record.final_output",
                     "evidence_supported_claims": len(claims & facts), "unsupported_claims": len(claims - facts),
                     "task_correctness": "see separate case_metric_transition with scoring-only gold",
                     "actual_runtime_policy": decision.decision.value, "executed_actions": "NO_INDEPENDENT_ACTION_TRACE",
                     "nonempty_accepted_structured": bool(claims), "full_output_assessed": False,
                     "claims_full_output_safety": False, "prose_safety": "NOT_MEASURED",
                     "fact_registry_truth": "NOT_INDEPENDENTLY_VALIDATED", "evidence_kind": "historical_reanalysis"})
    jsonl(out / "output_channel_case_results.jsonl", rows)
    summary = []
    for pipeline in sorted({r["pipeline"] for r in rows}):
        group = [r for r in rows if r["pipeline"] == pipeline]
        summary.append({"pipeline": pipeline, "N_all": len(group), "N_nonempty_accepted_structured": sum(r["nonempty_accepted_structured"] for r in group),
                        "N_full_output_assessed": 0, "structured_claim_unsupported_cases": sum(r["unsupported_claims"] > 0 for r in group),
                        "full_output_unsupported_rate": "NOT_MEASURED", "full_output_safe": "UNASSESSABLE"})
    a.write_csv(out / "whole_output_assessment.csv", summary)


def run(out):
    if (out / "release_manifest.json").exists():
        raise FileExistsError("Refusing to overwrite a completed release; choose a fresh output path")
    out.mkdir(parents=True, exist_ok=True)
    old_manifest = json.loads((OLD / "evidence_manifest.json").read_text())
    inputs = [checked_path(ROOT, r["path"], r["sha256"]) for r in old_manifest["sources"]]
    checked_path(ROOT, old_manifest["evaluator"], old_manifest["evaluator_sha256"])
    protected = {str(p.relative_to(ROOT)): a.digest(p) for p in OLD.rglob("*") if p.is_file()}
    protected.update({str(p.relative_to(ROOT)): a.digest(p) for p in inputs})
    protected.update({str(p.relative_to(ROOT)): a.digest(p) for p in (ROOT / "docs/papers/_47_UIR").glob("*") if p.is_file()})
    a.run(out / "historical_reanalysis")
    comparisons = [{"file": name, "historical_sha256": a.digest(OLD / name),
                    "reproduced_sha256": a.digest(out / "historical_reanalysis" / name)} for name in COMPARE]
    for row in comparisons:
        row["exact_bytes_equal"] = row["historical_sha256"] == row["reproduced_sha256"]
    if not all(r["exact_bytes_equal"] for r in comparisons):
        raise ValueError("Historical reanalysis export mismatch")
    a.write_json(out / "historical_reproduction_comparison.json", comparisons)
    runtime, gold = (a.unique(a.read(FROZEN / name)) for name in ("strong_runtime_600.jsonl", "strong_scoring_600.jsonl"))
    historical = a.read(BASE / "uir_phase4d/per_case_evidence_actual.jsonl")
    metric_transitions(out, runtime, gold, historical)
    external_audit(out)
    output_channels(out, runtime, historical)
    candidate_audit(out, runtime, gold, historical)
    families(out, runtime)
    annotations_and_conformance(out)
    for relative, expected in protected.items():
        checked_path(ROOT, relative, expected)
    a.write_json(out / "protected_artifact_hashes.json", protected)
    a.write_json(out / "environment.json", {"python": sys.version, "packages": sorted(
        {f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()}),
        "evidence_kind": "environment_inventory_not_inference", "cuda_execution": "NOT_RUN"})
    scientific_outputs = {str(p.relative_to(out)): a.digest(p) for p in out.rglob("*") if p.suffix in {".csv", ".jsonl", ".tex"}}
    a.write_json(out / "release_manifest.json", {"schema_version": "uir-next-release-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "evidence_kind": "historical_reanalysis",
        "input_sources": old_manifest["sources"], "scientific_output_sha256": scientific_outputs,
        "inference_rerun": False, "human_validation": False, "study_route": "B_AI_ONLY",
        "allowed_nondeterministic_metadata": ["created_at_utc", "environment.json", "logs/test durations"],
        "source_hashes": {str(p.relative_to(ROOT)): a.digest(p) for p in (ROOT / "projects/uir_base/scripts").glob("*.py")}})
    print(f"Offline evidence completion written to {out}")


def package(out, destination):
    """Allowlisted source+capture archive; no weights, keys, links, Git internals."""
    if destination.exists():
        raise FileExistsError("Refusing to overwrite a release archive")
    manifest = json.loads((out / "release_manifest.json").read_text())
    files = {ROOT / r["path"] for r in manifest["input_sources"]}
    files.update(LINEAGE.values())
    for directory in (ROOT / "src", ROOT / "projects/uir_base/scripts", ROOT / "projects/uir_base/evaluation", ROOT / "tests/uir_base"):
        files.update(p for p in directory.rglob("*") if p.suffix in {".py", ".yaml", ".json", ".ebnf"} and "__pycache__" not in p.parts and "official_sources" not in p.parts)
    files.update(ROOT / name for name in ("Cargo.toml", "Cargo.lock", "pyproject.toml", "README.md", "AGENTS.md"))
    for directory in (ROOT / "crates", ROOT / "projects/uir_base/results/mdpi_revision_2026_10_11/ai_reviews/20261011T114157Z", out,
                      ROOT / "projects/uir_base/results/mdpi_revision_2026_10_11/annotation_packets"):
        files.update(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    files.update(OLD / name for name in COMPARE)
    files.add(OLD / "evidence_manifest.json")
    files.add(ROOT / "docs/work_reports/uir_base/107_Astra_review/layout_migration_manifest.json")
    files.update(ROOT / "projects/uir_base/evaluation/uir_phase4c/official_sources/FinQA" / name
                 for name in ("test.json", "evaluate.py", "LICENSE"))
    for task in ("finqa", "halueval"):
        for condition in ("C1", "C8"):
            files.add(BASE / f"uir_phase4e/qwen_{task}_{condition}_raw.jsonl")
            files.add(BASE / f"uir_phase4d/{task}_predictions_actual_{condition}.jsonl")
    # Scope documents are release inputs too; they cannot be substituted later.
    docs = ROOT / "docs/work_reports/uir_base/110_mdpi_rev/implementation"
    files.update(p for p in docs.rglob("*") if p.is_file())
    dependencies = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
                raise ValueError(f"Unsafe or missing release dependency: {path}")
            relative = str(path.relative_to(ROOT))
            dependencies.append({"path": relative, "sha256": a.digest(path), "bytes": path.stat().st_size})
            archive.write(path, relative)
        archive.writestr("archive_manifest.json", json.dumps({"files": dependencies, "manifest_self_hash": "NOT_APPLICABLE"}, sort_keys=True, indent=2))
    a.write_csv(out / "dependency_manifest.csv", dependencies)
    print(json.dumps({"archive": str(destination), "sha256": a.digest(destination), "files": len(dependencies)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT)
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    if args.package:
        package(args.out, args.package)
    else:
        run(args.out)


if __name__ == "__main__":
    main()
