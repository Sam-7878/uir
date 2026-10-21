"""R14 scoped private release, raw replay, and detached gates."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
from .common import ARCHIVE, DOC, OLD, OUT, ROOT, check_frozen, csvfile, load, read, sha, utc, write
from .manuscript import PAPER
from .qa import checked_reference, unique_cases, required_finish

REPORT_ROOT = DOC.parent
STATUS = [
    ("R00", "PASS_NEW_ENVIRONMENT_SCOPE", "N00,N13/W00,W12", "Exact wheels/new venv/31+800 replay; same physical host, not independent human replication.", "independent_replay_report.json"),
    ("R01", "PASS_LINEAGE_SCOPE", "N03,N05/W04,W06", "418 original-row joins/290 oracle-like/128 empty; generator assignments reproduced, not proof of original historical process execution.", "fixture_lineage_audit.csv"),
    ("R02", "PASS_ALIGNED_CONTRACT_SCOPE", "N02,N04,N05/W02,W07", "Seven-field schema + numeric unknown rejection + separate generic/enum-reference protocols; stronger binding explicitly labeled.", "renderer_bound_summary.json"),
    ("R03", "PASS_FINITE_SHARED_VERIFIER_CONFORMANCE", "N04,N10,N11/W07,W10", "Two candidate formats agree with common verifier; not independent provers or arbitrary backends.", "backend_conformance_results.jsonl"),
    ("R04", "PASS_FROZEN_FAIR_CONTROLS", "N05,N11/W06", "Identical parser/context/capability/checker/scorer; artifact factor separated from output binding.", "repr_ablation_protocol_v1.json"),
    ("R05", "PASS_RESTRICTED_CNL", "N03,N04,N07/W08", "12 minimum pairs +144 development requests; no human/general free-NL accuracy.", "bilingual_raw_only_conformance.jsonl"),
    ("R06", "PARTIAL_NO_VERIFIED_FAMILY_HOLDOUT", "N05/W06,W09", "816 new Phi development calls, all versions retained; available unused rows not verified template-family-disjoint.", "confirmatory_protocol.json"),
    ("R07", "PASS_FINITE_DEPENDENCY_SCOPE", "N02,N05/W02", "Bound JSON and operand-closed partial; native prose/real-world truth NOT_MEASURED.", "dependency_projection_tests.jsonl"),
    ("R08", "PARTIAL_DEVELOPMENT_DIAGNOSTICS", "N09/W01,W09", "Typed AST,11 parity,400 retrieval audits,800 frozen parse diagnostics; no new confirmatory FinQA/whole-report unit solver.", "finqa_development_summary.json"),
    ("R09", "PASS_AI_ONLY_SCOPE", "N07,N08/W08,W14", "Old reviews preserved +16 new open judgments, no truth labels; human W08 unmet/author approval absent.", "open_review_summary.json"),
    ("R10", "PASS_SYNTHETIC_FILESYSTEM_SCOPE", "N10/W10", "Real temporary read/write tools and finite snapshot/revocation scenarios; not adaptive model security.", "policy_utility_safety_table.csv"),
    ("R11", "PASS_SCOPED_PAIRED_ANALYSIS", "N06/W11", "Paired synthetic family bootstrap and5 warm guard repeats; no universal speed/equivalence claims.", "cluster_bootstrap_results.csv"),
    ("R12", "PASS_BOUNDED_REUSE_POSITIONING", "N11/W05,W13", "Equivalent baseline equal; finite shared artifact/backend composition, not measured human effort or accuracy superiority.", "repr_summary.csv"),
    ("R13", "PARTIAL_AUTHOR_CURRENT_RULES_PENDING", "N11,N12/W03,W13,W14", "Full MDPI source/PDF/figures/Bib and private QA; actual author/rights/current journal checks pending.", "science_release_manifest.json"),
    ("R14", "PASS_TECHNICAL_QA_SUBMISSION_BLOCKED", "N13/W00-W15", "Separate integrity/reproduction/claim/manuscript/submission gates; no upload/payment/submission.", "final_tests.xml"),
]


def metadata():
    check_frozen()
    extras = sorted((OUT / "official_evaluator_wheels").glob("*.whl"))
    requirements = []; manifest = []
    for p in extras:
        with zipfile.ZipFile(p) as wheel:
            info = wheel.read(next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))).decode()
        name = next(l[6:] for l in info.splitlines() if l.startswith("Name: "))
        version = next(l[9:] for l in info.splitlines() if l.startswith("Version: "))
        requirements.append(f"{name}=={version} --hash=sha256:{sha(p)}\n")
        manifest.append({"filename": p.name, "sha256": sha(p)})
    (OUT / "official_evaluator_requirements.lock").write_text("".join(requirements))
    write(OUT / "official_evaluator_wheel_manifest.json", {"files": manifest})
    csvfile(DOC / "claim_contract_matrix.csv", [{"field": f, "seven_field_generator": "required string", "reference_generator": "not generated",
          "authoritative_source": "versioned catalog", "scorer": "exact seven-field support", "approved_renderer": "authoritative bound value"} for f in
          ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance")])
    mismatches = []
    for r in read(OLD / "fresh_matched/raw_requests_responses.jsonl"):
        if not r["model_invoked"]: continue
        response = r.get("response") or {}; content = response.get("message", {}).get("content", "")
        parsed = None
        try: parsed = json.loads(content)
        except (ValueError, TypeError): pass
        claims = parsed.get("claims", []) if isinstance(parsed, dict) else []
        mismatches.append({"case_id": r["case_id"], "period_missing": any("period" not in c for c in claims),
                           "unit_missing": any("unit" not in c for c in claims), "strict_json": parsed is not None,
                           "finish_reason": response.get("done_reason", "MISSING"), "old_scores_changed": False,
                           "evidence_kind": "historical_reanalysis"})
    csvfile(OUT / "schema_support_mismatch_audit.csv", mismatches)
    with (OUT / "comparison_case_manifest.csv").open() as handle:
        new = list(csv.DictReader(handle))
    csvfile(OUT / "source_family_manifest_vNext.csv", [{"case_id": r["case_id"], "source_family_id": r["family"],
            "family_kind": "declared constructed source/entity", "template_independence": "NOT_ESTABLISHED", "split": "DEVELOPMENT"} for r in new])
    registry = load(OUT / "frozen_review_registry.json"); portable = {}
    for name, digest in registry["files"].items():
        if name.startswith("/"):
            name = "projects/" + name.split("/projects/", 1)[1]
        elif not name.startswith("projects/"):
            name = str((OLD / name).relative_to(ROOT))
        checked_reference(ROOT, name, digest); portable[name] = digest
    write(OUT / "frozen_review_registry_vNext.json", {"files": portable, "correction": "v1 absolute references retained as provenance only; no captured reviews changed"})
    report = {"created_at_utc": utc(), "pages_reviewed": list(range(1,10)), "page_count": 9,
              "layout_review": "all pages visually inspected; no table clipping; final draft banner/denominator change reviewed separately",
              "main_source_sha256": sha(PAPER / "main.tex"), "pdf_sha256": sha(PAPER / "main.pdf"),
              "abstract_wordcount": int((PAPER / "abstract_wordcount.txt").read_text()), "current_rules_verified": False,
              "author_institution_signoff": False, "technical_PDF_QA": True}
    write(PAPER / "paper_final_QA.json", report)
    write(PAPER / "source_diff_final.json", {"original_source_sha256": sha(ROOT / "projects/uir_base/paper/_47_UIR/_47_UIR.tex"),
          "original_bib_sha256": sha(ROOT / "projects/uir_base/paper/_47_UIR/references.bib"), "final_source_sha256": sha(PAPER / "main.tex"),
          "final_bib_sha256": sha(PAPER / "references.bib"), "original_replaced": False,
          "initial_source_diff_json": "generation-time pre-compile snapshot, not final source binding"})
    (PAPER / "source_diff.md").write_text("# Source changes\n\nOriginal IEEE source and bibliography preserved. Complete separate MDPI draft replaces framing with bounded IR/reuse evidence, oracle-like input disclosure, equal specialized control, all negative renderer/FinQA/AI findings and pending declarations. source_diff_final.json binds final bytes; source_diff.json is the initial generation snapshot before bibliography/layout repairs.\n")
    write(DOC / "conformance_matrix.json", {"raw_frontends": ["restricted KO CNL", "restricted EN CNL", "authenticated API slots"],
          "backends": ["reference candidate", "seven-field candidate"], "shared_verifier": True,
          "N_backend_pairs": load(OUT / "repr_execution_manifest.json")["backend_N"], "N_minimum_pairs": 12,
          "human_semantic_validation": False, "independent_backend_verifier": False})


def export(destination):
    check_frozen()
    if destination.exists(): raise FileExistsError("Refuse release replacement")
    overlay = {}
    for directory in (ROOT / "projects/uir_base/validation", OUT, DOC, PAPER):
        for path in directory.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                if path.is_symlink(): raise ValueError("SYMLINK_NOT_PERMITTED")
                overlay[str(path.relative_to(ROOT))] = path
    overlay["src/uir_common/representation.py"] = ROOT / "src/uir_common/representation.py"
    for path in (ROOT / "tests/uir_base").glob("test_*vnext.py"): overlay[str(path.relative_to(ROOT))] = path
    for name in ("test_representation_dependencies.py", "test_r_stage_negative.py"):
        overlay["tests/uir_base/" + name] = ROOT / "tests/uir_base" / name
    for name in ("uir_next_source_evidence_v3.zip", "uir_next_offline_source_evidence_v2.zip", "110_mdpi_rev.zip"):
        relative = "docs/work_reports/uir_base/110_mdpi_rev/" + name; overlay[relative] = ROOT / relative
    for name in ("_47_UIR.tex", "references.bib"):
        relative = "projects/uir_base/paper/_47_UIR/" + name; overlay[relative] = ROOT / relative
    entries = []
    with zipfile.ZipFile(ARCHIVE) as base, zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as result:
        for name in sorted(set(base.namelist()) | set(overlay)):
            if name == "archive_manifest.json": continue
            content = overlay[name].read_bytes() if name in overlay else base.read(name)
            entries.append({"path": name, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
            result.writestr(name, content)
        result.writestr("archive_manifest.json", json.dumps({"scope": "PRIVATE_REVIEW_ONLY, distribution rights pending; no weights/secrets",
                          "files": entries, "self_hash": "NOT_APPLICABLE"}, sort_keys=True, indent=2))
    print(json.dumps({"archive": str(destination), "sha256": sha(destination), "N_files": len(entries)}))


def reconstruct(root):
    """Metric replay only: no network/model/author approval."""
    import importlib
    from uir_common.representation import accept, TypedRequest
    out = root / OUT.relative_to(ROOT)
    from .renderers import evaluate
    from .renderers_bound import schema
    from jsonschema import validate
    repr_rows = read(out / "dev_matched_raw.jsonl")
    unique_cases(repr_rows, ("case_id", "condition"))
    from .frontends import compile_shared, specialized_plan
    for record in repr_rows:
        case = record["runtime_packet"]
        if record["artifact"] is None and record["specialized_plan"] is None:
            try:
                compile_shared(case["raw_request"], case["policy"], case["source_catalog"], assisted=case["assisted_slots"], action=case["action"])
            except ValueError:
                continue
            raise ValueError("FALSE_CLARIFICATION_IN_CAPTURE")
        request = TypedRequest.from_artifact(record["artifact"]) if record["artifact"] else None
        plan = request.plan() if request else record["specialized_plan"]
        expected = record["accepted_output"]
        actual = accept(plan, case["source_catalog"], case["policy"], case["condition_context"], record["candidate"],
                        identity=expected["contract_digest"])
        if actual != expected: raise ValueError("REPR_RAW_TO_OUTPUT_REPLAY_MISMATCH")
    cases = {r["case_id"]: r for r in read(out / "renderer_runtime_packets.jsonl")}
    comparisons = []
    for r in read(out / "renderer_fresh_raw.jsonl"):
        response = r["response"] or {}; required_finish(response)
        actual = evaluate(response.get("message", {}).get("content", ""), cases[r["case_id"]], r["condition"],
                          finished=response["done_reason"] == "stop")
        comparisons.append((r["case_id"], r["condition"], actual["complete"], actual["accepted_nonempty"], actual["structured_unsupported"]))
    with (out / "renderer_results.csv").open() as handle:
        recorded = {(r["case_id"], r["condition"]): r for r in csv.DictReader(handle)}
    for cid, cond, complete, nonempty, unsupported in comparisons:
        row = recorded[cid, cond]
        if [complete, nonempty, unsupported] != [row[k] == "True" for k in ("complete", "accepted_nonempty", "structured_unsupported")]:
            raise ValueError("RENDERER_RAW_METRIC_MISMATCH")
    bound = []
    for r in read(out / "renderer_bound_raw.jsonl"):
        case = cases[r["case_id"]]; response = r["response"]; required_finish(response)
        body = json.loads(response["message"]["content"]); validate(body, schema(case))
        candidate = json.dumps({"contract_digest": r["server_contract_digest"], "fact_ids": body["fact_ids"]})
        bound.append(evaluate(candidate, case, "FACT_ID_BINDING", finished=response["done_reason"] == "stop"))
    expected = load(out / "renderer_bound_summary.json")
    if sum(r["complete"] for r in bound) != expected["N_complete"] or sum(r["structured_unsupported"] for r in bound) != expected["N_unsupported"]:
        raise ValueError("BOUND_RAW_METRIC_MISMATCH")
    from .reviews import SCHEMA
    from jsonschema import validate as validate_label
    reviews = read(out / "open_review_raw.jsonl")
    unique_cases(reviews, ("case_id", "reviewer"))
    index = {}
    for record in reviews:
        response = record["response"]; required_finish(response); label = None
        try:
            if response["done_reason"] != "stop": raise ValueError("Incomplete")
            label = json.loads(response["message"]["content"]); validate_label(label, SCHEMA)
        except Exception: label = None
        if label != record["label"]: raise ValueError("AI_RAW_LABEL_MISMATCH")
        index[record["case_id"], record["reviewer"]] = label
    summary = load(out / "open_review_summary.json"); unresolved = set()
    for field in summary["comparisons"]:
        pairs = []
        for cid in {r["case_id"] for r in reviews}:
            a, b = index[cid, "AI_J1"], index[cid, "AI_J2"]
            if a is None or b is None: unresolved.add(cid); continue
            pair = a[field], b[field]; pairs.append(pair)
            if pair[0] != pair[1] or "UNCERTAIN" in pair or field == "epistemic_uncertainty" and "HIGH" in pair: unresolved.add(cid)
        if len(pairs) != summary["comparisons"][field]["N_pairs"] or sum(x == y for x,y in pairs) != summary["comparisons"][field]["N_agree"]:
            raise ValueError("OPEN_AGREEMENT_REPLAY_MISMATCH")
    if len(unresolved) != summary["N_unresolved"]: raise ValueError("OPEN_UNRESOLVED_REPLAY_MISMATCH")
    return {"status": "R_STAGE_RAW_METRIC_REPLAY_PASS", "N_representation_records": len(repr_rows), "N_v1_renderer_calls": len(comparisons),
            "N_v2_renderer_calls": len(bound), "model_calls_in_replay": 0, "human_validation": False}


def reproduce(archive):
    from projects.uir_base.scripts.next_verify import reproduce as prior
    directory = Path(tempfile.mkdtemp(prefix="uir-r-final-"))
    subprocess.run([sys.executable, "-m", "venv", "--copies", str(directory / "venv")], check=True)
    python = directory / "venv/bin/python"
    install = subprocess.run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", "--require-hashes",
        "--find-links", str(OUT / "wheelhouse"), "-r", str(OUT / "requirements.lock")], capture_output=True, text=True)
    if install.returncode: raise RuntimeError(install.stdout + install.stderr)
    destination = directory / "checkout"
    # Frozen verifier bootstrap performs the complete combined archive integrity check.
    import zipfile
    with zipfile.ZipFile(archive) as z: code = z.read("projects/uir_base/scripts/next_verify.py")
    bootstrap = directory / "verify.py"; bootstrap.write_bytes(code)
    program = ("import importlib.util,sys;from pathlib import Path;"
        f"s=importlib.util.spec_from_file_location('verifier',{str(bootstrap)!r});m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        f"m.reproduce(Path({str(archive)!r}),Path({str(destination)!r}));"
        f"sys.path[:0]=[{str(destination / 'src')!r},{str(destination)!r}];"
        "from projects.uir_base.validation.release import reconstruct; import json;"
        f"print('R_REPLAY='+json.dumps(reconstruct(Path({str(destination)!r}))));")
    run = subprocess.run([str(python), "-I", "-c", program], cwd=directory, capture_output=True, text=True,
                         env={"PATH": "/usr/bin:/bin", "HOME": str(directory), "PYTHONNOUSERSITE": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    with (REPORT_ROOT / "final_reproduce.log").open("x") as handle: handle.write(install.stdout + install.stderr + run.stdout + run.stderr)
    if run.returncode: raise RuntimeError(run.stdout + run.stderr)
    new = json.loads(next(l.removeprefix("R_REPLAY=") for l in run.stdout.splitlines() if l.startswith("R_REPLAY=")))
    write(REPORT_ROOT / "final_reproduce_report.json", {"status": "FRESH_ENV_COMBINED_ARCHIVE_REPLAY_PASS", "archive_sha256": sha(archive),
          "prior": load(destination / "clean_room_report.json"), "R_stage": new, "new_venv": str(directory / "venv"),
          "model_calls": 0, "independent_human_or_machine": False, "interpreter_provisioning_shared": True})
    print(new)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--metadata", action="store_true"); parser.add_argument("--export", type=Path); parser.add_argument("--reproduce", type=Path)
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    if args.report_dir:
        REPORT_ROOT = args.report_dir.resolve()
        if not REPORT_ROOT.is_relative_to(ROOT): parser.error("Report directory must remain inside this repository")
        REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.metadata: metadata()
    elif args.export: export(args.export.resolve())
    elif args.reproduce: reproduce(args.reproduce.resolve())
    else: parser.error("Explicit --metadata / --export / --reproduce required")
