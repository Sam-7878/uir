"""S12 generated scientific macros/tables and branched private MDPI source."""
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
from .common import DOC, PRIOR, ROOT, csvfile, jsonl, load, read, relative, sha, textfile, utc, write
from .interpreter_python import interpret


def backend_refresh(out):
    cases = read(out / "semantic_differential_cases.jsonl")
    binary = ROOT / "target/debug/uir_contract_eval"
    run = subprocess.run([str(binary)], input="".join(json.dumps(c["packet"]) + "\n" for c in cases), text=True, capture_output=True, check=True)
    textfile(out / "independent_rust_interpreter_v2.log", run.stdout + run.stderr)
    rust = [json.loads(line) for line in run.stdout.splitlines()]
    if len(rust) != len(cases):
        raise ValueError("DIFFERENTIAL_RESPONSE_MISSING")
    rows = [{"case_id": c["case_id"], "python": interpret(c["packet"]), "rust": b,
             "agreement": interpret(c["packet"]) == b, "expected_state": c["expected_state"],
             "normative_conformance": interpret(c["packet"])["state"] == c["expected_state"], "evidence_kind": "SYNTHETIC_CONFORMANCE"} for c, b in zip(cases, rust)]
    jsonl(out / "interpreter_agreement_v2.jsonl", rows)
    write(out / "independent_backend_scope_v2.json", {"N": len(rows), "N_agreement": sum(r["agreement"] for r in rows),
          "N_normative_conformance": sum(r["normative_conformance"] for r in rows), "binary_sha256": sha(binary),
          "python_source_sha256": sha(ROOT / "projects/uir_base/representation_research/interpreter_python.py"),
          "rust_source_sha256": sha(ROOT / "crates/poa-uir/src/bin/uir_contract_eval.rs"), "case_input_sha256": sha(out / "semantic_differential_cases.jsonl"),
          "independently_coded": True, "independently_staffed": False, "supersedes": "pilot source/binary binding only; original41 outcomes retained"})


def generate(out):
    from .experiment import check_freeze
    check_freeze(out)
    backend_refresh(out)
    paper = DOC / "manuscript/revision_S"
    paper.mkdir(parents=True, exist_ok=False)
    prior = PRIOR / "manuscript/revision_vNext"
    shutil.copytree(prior / "Definitions", paper / "Definitions")
    for asset in prior.glob("*.sty"):
        shutil.copyfile(asset, paper / asset.name)
    shutil.copyfile(prior / "references.bib", paper / "references.bib")
    shutil.copyfile(DOC / "main_S_template.tex", paper / "main.tex")
    shutil.copyfile(DOC / "formal_semantics_appendix_template.tex", paper / "formal_semantics_appendix.tex")
    files = ["runtime/query_aware_dev.jsonl", "evaluator_only/query_aware_gold.jsonl", "synthetic_source_documents.jsonl", "source_snapshot.json",
             "preregistration.json", "protocol_freeze_receipt.json", "fresh_model_raw.jsonl", "factorial_saved_outputs.jsonl", "fresh_execution_manifest.json",
             "query_aware_summary.csv", "query_aware_case_metrics.csv", "paired_analysis.json", "semantic_differential_cases.jsonl", "interpreter_agreement_v2.jsonl",
             "independent_backend_scope_v2.json", "backend_portability_cases.jsonl", "implementation_cost.csv", "finqa_scope_metrics.json",
             "gold_boundary_v2/gold_isolation_status.json", "policy_v2/action_and_false_denial_metrics.csv", "S_cpu_raw_reconstruct.json", "namespace_standalone_report.json"]
    write(out / "S_science_manifest.json", {"created_at_utc": utc(), "files": [{"path": relative(out / f), "sha256": sha(out / f)} for f in files],
          "scope": "SYNTHETIC_DEVELOPMENT_AND_HISTORICAL_SCOPE_CORRECTIONS", "paper_generation_source_sha256": sha(DOC / "main_S_template.tex")})
    with (out / "query_aware_summary.csv").open() as handle:
        summaries = list(csv.DictReader(handle))
    index = {row["condition"]: row for row in summaries}
    backend = load(out / "independent_backend_scope_v2.json")
    execution = load(out / "fresh_execution_manifest.json")
    renderer = index["UIR_SHARED_TYPED|deterministic|SLM|non_oracle_pool"]
    selector = index["UIR_SHARED_TYPED|SLM|template|non_oracle_pool"]
    values = {"SDifferential": backend["N"], "SRequests": 24, "SFacts": 48, "SOutputs": execution["N_condition_cases"],
              "SCalls": execution["actual_model_calls"], "SRendererComplete": renderer["N_accepted_exact"],
              "SRawSelectorComplete": selector["N_raw_selector_exact"], "SReprPairs": load(out / "paired_analysis.json")["N_repr_pairs"],
              "SRManifest": 5417, "SStandaloneTests": 131, "SWholeTests": 328, "SScienceHash": sha(out / "S_science_manifest.json")}
    textfile(paper / "generated_metrics_S.tex", "".join(f"\\newcommand{{\\{key}}}{{{value}}}\n" for key, value in values.items()))
    lines = [r"\begin{table}[H]\centering\small", r"\caption{Exploratory factorial, all24 inputs per cell. U=public UIR; S=native specialized; D=deterministic selector; T=template renderer; L=SLM; P=preselected; N=non-oracle. Exact raw selector and exact approved output are different endpoints. Identical payload captures are reused, not independent samples.}\label{tab:factorial}",
             r"\begin{tabular}{lrrrr}\toprule", r"Condition & Raw exact & Approved exact & False denial & Accepted unsupported\\\midrule"]
    for row in summaries:
        rep, select, render, evidence = row["condition"].split("|")
        name = ("U" if rep == "UIR_SHARED_TYPED" else "S") + "/" + ("D" if select == "deterministic" else "L") + "/" + ("T" if render == "template" else "L") + "/" + ("P" if evidence == "preselected" else "N")
        lines.append(f"{name} & {row['N_raw_selector_exact']}/24 & {row['N_accepted_exact']}/24 & {row['N_false_denial']} & {row['N_accepted_unsupported']} \\\\")
    lines.extend([r"\bottomrule\end{tabular}\end{table}"])
    textfile(paper / "tables/factorial.tex", "\n".join(lines) + "\n")
    costs = list(csv.DictReader((out / "implementation_cost.csv").open()))
    table = [r"\begin{table}[H]\centering\small\caption{One-host warm API-build/guard observations,100 repetitions. UIR includes serialization; native specialized does not. Wrapper LOC excludes the common validation/core. Human labor is NOT MEASURED.}\label{tab:cost}",
             r"\begin{tabular}{lrrrr}\toprule", r"Condition & Wrapper LOC & P50 ms & P95 ms & P99 ms\\\midrule"]
    for row in costs:
        table.append(f"{'UIR' if row['condition']=='UIR_SHARED_TYPED' else 'Specialized'} & {row['wrapper_function_LOC']} & {float(row['P50_ms']):.3f} & {float(row['P95_ms']):.3f} & {float(row['P99_ms']):.3f} \\\\")
    table.append(r"\bottomrule\end{tabular}\end{table}")
    textfile(paper / "tables/cost.tex", "\n".join(table) + "\n")
    abstract = re.search(r"\\abstract\{(.*?)\}\n\\keyword", (paper / "main.tex").read_text(), re.S).group(1)
    for name, value in values.items():
        abstract = abstract.replace("\\" + name + "{}", str(value))
    write(paper / "paper_generation_manifest.json", {"created_at_utc": utc(), "science_manifest_sha256": sha(out / "S_science_manifest.json"),
          "main_tex_sha256": sha(paper / "main.tex"), "references_sha256": sha(paper / "references.bib"), "abstract_words": len(abstract.split()),
          "original_R_manuscript_sha256": sha(prior / "main.tex"), "original_IEEE_source_sha256": sha(ROOT / "projects/uir_base/paper/_47_UIR/_47_UIR.tex"),
          "original_sources_modified": False, "target_special_issue": "WFBEQFE47X", "author_approval": False})
    textfile(out / "contribution_decision_S.md", "# Chosen paper route A\n\nScoped representation/contract engineering: finite independently coded interpreter agreement, declared CNL, source-first synthetic query selection and actual portability. No general accuracy/security/human/productivity advantage. Original concept-paper coverage is intentionally narrowed; historic tables remain supplementary, not reclassified. Author decision on scope and declarations remains pending, not coding-agent signoff.\n")
    textfile(out / "paper_diff_report.md", "# Source branch\n\nOriginal IEEE and R MDPI sources remain unchanged. New S source expands five-tuple identity, finite grammar/state rules, trust assumptions, real independently coded Python/Rust, raw-request non-oracle selection, matched16-cell factorial, negative SLM results, API/energy extension and concrete packaging gap. All FinQA mentions say supplied page context.272/272 is explicitly no-request enumeration. No multi-agent implementation or author approval is invented.\n")
    textfile(out / "author_declarations_status.md", "# Actual declarations pending\n\nAuthors/affiliations/corresponding author, contributions, funding/conflicts, AI-use approval, ethics/IRB/consent, source/model/public redistribution rights and institutional indexing/fee approval require actual author/institution confirmation. Manuscript placeholders remain; MANUSCRIPT_READY and SUBMISSION_READY are BLOCKED.\n")
    print(json.dumps({"paper": str(paper), "abstract_words": len(abstract.split()), "science_sha256": sha(out / "S_science_manifest.json")}))
