"""Generate full private-review MDPI source from one frozen numerical manifest."""
import csv
import json
from pathlib import Path
import shutil
import zipfile
from .common import DOC, OLD, OUT, ROOT, csvfile, load, sha, write

PAPER = ROOT / "docs/work_reports/uir_base/111_validation/manuscript/revision_vNext"
TEMPLATE = Path("/mnt/d/_Work/goat_bank/dlg_gnn/local_storage/benchmark/a09_submission_closure/upstream/MDPI_template.zip")
TEMPLATE_SHA = "8746ade43f6ba8e78250ff1b95f28025ef53aa6a270f66633677d346a2699fbd"


def rows(path):
    with path.open() as handle: return list(csv.DictReader(handle))


def texescape(value):
    return str(value).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&").replace("#", r"\#")


def generate():
    paths = ["repr_execution_manifest.json", "repr_summary.csv", "semantic_conformance_summary.json", "fixture_lineage_summary.json",
             "renderer_summary.csv", "renderer_bound_summary.json", "finqa_development_summary.json", "cluster_bootstrap_results.csv",
             "policy_utility_safety_table.csv", "open_review_summary.json", "confirmatory_protocol.json", "independent_replay_report.json"]
    source = {str((OUT / p).relative_to(ROOT)): sha(OUT / p) for p in paths}
    source[str((OLD / "historical_reanalysis/internal_utility_recomputed.csv").relative_to(ROOT))] = sha(OLD / "historical_reanalysis/internal_utility_recomputed.csv")
    manifest = {"version": "representation-scientific-numbers-v1", "sources": source, "private_review_only": True,
                "original_W08": "NOT_SATISFIED", "human_validation": False, "author_signoff": False}
    write(OUT / "science_release_manifest.json", manifest)
    release_hash = sha(OUT / "science_release_manifest.json")
    PAPER.mkdir(parents=True, exist_ok=False)
    definitions = PAPER / "Definitions"; definitions.mkdir()
    if sha(TEMPLATE) != TEMPLATE_SHA: raise ValueError("CACHED_MDPI_TEMPLATE_HASH_MISMATCH")
    with zipfile.ZipFile(TEMPLATE) as archive:
        for name in archive.namelist():
            if name.startswith("Definitions/") and not name.endswith("/"):
                target = PAPER / name
                if ".." in Path(name).parts: raise ValueError("TEMPLATE_PATH_ESCAPE")
                target.write_bytes(archive.read(name))
    # Genuine upstream soul sources, not the neighboring manuscript's shim.
    soul = Path("/mnt/d/_Work/goat_bank/dlg_gnn/local_storage/benchmark/a09_submission_closure/upstream/soul/soul")
    for name in ("soul.ins", "soul.dtx", "soul-ori.dtx", "README.md"):
        shutil.copyfile(soul / name, PAPER / name)
    write(PAPER / "template_provenance.json", {"cached_template_sha256": TEMPLATE_SHA,
          "upstream": "https://mdpi-res.com/data/MDPI_template.zip", "class_date": "2025-06-18", "current_live_rules_verified": False,
          "neighbor_paper_source_or_declarations_reused": False,
          "original_template_asset_sha256": {str(p.relative_to(PAPER)): sha(p) for p in definitions.iterdir() if p.is_file()},
          "soul_sources_sha256": {name: sha(PAPER / name) for name in ("soul.ins", "soul.dtx", "soul-ori.dtx", "README.md")}})
    representation = load(OUT / "repr_execution_manifest.json"); minimum = load(OUT / "semantic_conformance_summary.json")
    fixture = load(OUT / "fixture_lineage_summary.json"); bound = load(OUT / "renderer_bound_summary.json")
    finqa = load(OUT / "finqa_development_summary.json"); review = load(OUT / "open_review_summary.json")
    metrics = {"ReprCases": representation["N_rows"] // 2, "ReprRecords": representation["N_rows"], "BackendCases": representation["backend_N"],
               "BackendEqual": representation["backend_N_equal"], "PairCases": minimum["N_pairs"], "PairPass": minimum["N_pass"],
               "OracleCases": fixture["cohorts"]["A_ORACLE_LIKE_PRESELECTED"], "EmptyCases": fixture["cohorts"]["D_EMPTY_EVIDENCE"],
               "OldEligible": fixture["N_eligible"], "RendererN": bound["N"], "BoundComplete": bound["N_complete"],
               "BoundUnsupported": bound["N_unsupported"], "RetrievalN": finqa["N_retrieval_cases"],
               "LexicalPresence": finqa["lexical_numeric_operand_presence"], "FullPresence": finqa["full_numeric_operand_presence"],
               "ParityN": finqa["N_parity_cases"], "ParityPass": finqa["N_parity_pass"],
               "OpenReviewN": review["N_responses"], "OpenReviewValid": review["N_valid"], "OpenUnresolved": review["N_unresolved"]}
    with (PAPER / "generated_metrics.tex").open("x") as handle:
        handle.write("% science_release_manifest_sha256: " + release_hash + "\n")
        for key, value in metrics.items(): handle.write(r"\newcommand{\Result" + key + "}{" + str(value) + "}\n")
    tabledir = PAPER / "generated_tables"; tabledir.mkdir()
    tables = {
        "representation": (["Condition", "Requests", "Joint conformance", "Nonempty", "Clarification"], [
            [r["condition"].replace("UIR_SHARED_TYPED", "Shared typed UIR").replace("SPECIALIZED_STRUCTURED_NO_SHARED_UIR", "Equivalent specialized"),
             r["N"], r["N_joint_conformant"], r["N_nonempty_accepted"], r["N_clarification"]] for r in rows(OUT / "repr_summary.csv")]),
        "renderer": (["Output condition", "N", "Complete", "Nonempty", "Unsupported"], [
            [r["condition"].replace("DETERMINISTIC_CATALOG", "Deterministic catalog").replace("SEVEN_FIELD_NATIVE", "Seven-field native").replace("FACT_ID_PARTIAL_OFF", "Generic ID partial-off").replace("FACT_ID_BINDING", "Generic ID binding"),
             r["N"], r["N_complete"], r["N_accepted_nonempty"], r["N_structured_unsupported"]] for r in rows(OUT / "renderer_summary.csv")] +
             [["Enum ID + server binding (dev v2)", bound["N"], bound["N_complete"], bound["N_nonempty"], bound["N_unsupported"]]]),
        "policy": (["Condition", "Tool attempts", "Prohibited executed", "Allowed executed", "False denial"], [
            [r["condition"].replace("SPECIALIZED_EQUIVALENT_ENFORCED", "Equivalent specialized").replace("UIR_ENFORCED", "UIR enforced").replace("UNGUARDED_DIAGNOSTIC", "Unguarded diagnostic").replace("REFUSE_ONLY", "Refuse only").replace("NO_TOOLS", "No tools"),
             r["attempted"], r["prohibited_executed"], r["allowed_executed"], r["false_denial"]] for r in rows(OUT / "policy_utility_safety_table.csv")]),
        "historical": (["Condition", "Eligible", "Complete", "Partial", "Structured unsupported"], [
             [r["pipeline"].split("_")[0], r["N_eligible"], r["full"], r["partial"], r["unsupported_accepted_cases"]]
             for r in rows(OLD / "historical_reanalysis/internal_utility_recomputed.csv")]),
    }
    for name, (headers, values) in tables.items():
        text = [r"\begin{tabular}{l" + "r" * (len(headers)-1) + r"}\toprule",
                " & ".join(texescape(h) for h in headers) + r" \\\midrule"]
        text += [" & ".join(texescape(v) for v in row) + r" \\" for row in values]
        text += [r"\bottomrule\end{tabular}"]
        (tabledir / (name + ".tex")).write_text("\n".join(text) + "\n")
    write(PAPER / "generated_table_inputs.json", {"science_release_sha256": release_hash, "tables": tables, "metrics": metrics})
    abstract = (
        r"Typed intermediate representations can separate language-model candidates from executable authority without assuming better model reasoning. "
        r"We evaluate a shared policy-and-evidence contract for restricted Korean and English frontends, authenticated assisted inputs, and two candidate formats. "
        r"The study is AI-only and uses constructed conformance data; it does not establish human semantic accuracy. "
        r"A capability-equivalent specialized pipeline shares the parser, policy and support guard, avoiding an intentionally weaker control. "
        r"Both systems conform on \ResultReprCases{} development requests, while \ResultBackendEqual{} backend comparisons preserve authorization and accepted sets. "
        r"Historical evidence reconstruction identifies \ResultOracleCases{} oracle-like fact fixtures and \ResultEmptyCases{} empty catalogs. "
        r"New local GPU development experiments distinguish seven-field syntax, generic references and stronger enumerated reference binding. "
        r"Deterministic rendering remains the complete-answer and zero-inference control. "
        r"Dependency-closed partial output and finite real-file tools test bounded failure handling. "
        r"Financial benchmark diagnostics separate retrieval-number availability, program syntax and unit interpretation without rewriting earlier negative scores. "
        r"The results support inspectable contract composition and declared frontend/backend reuse, not superior reasoning, unrestricted language understanding, open-world factual truth, independent human validation, or universal prompt-injection resistance.")
    expanded = abstract
    for key, value in metrics.items(): expanded = expanded.replace(r"\Result" + key + "{}", str(value))
    (PAPER / "abstract_wordcount.txt").write_text(str(len(expanded.split())) + "\n")
    (PAPER / "abstract_expanded.txt").write_text(expanded + "\n")
    template = DOC / "main_template.tex"
    text = template.read_text()
    text = text.replace("ABSTRACT_TEXT", abstract).replace("RELEASE_HASH", release_hash)
    (PAPER / "main.tex").write_text(text)
    shutil.copyfile(DOC / "references_vNext.bib", PAPER / "references.bib")
    original = ROOT / "docs/papers/_47_UIR"
    write(PAPER / "source_diff.json", {"original_source_sha256": sha(original / "_47_UIR.tex"), "original_bib_sha256": sha(original / "references.bib"),
          "new_source_sha256": sha(PAPER / "main.tex"), "source_replaced_in_place": False, "author_metadata": "PENDING_CONFIRMATION",
          "changes": ["IEEE original preserved; complete separate MDPI research manuscript", "oracle/trusted-slot scope moved into Methods",
                      "fair specialized control and negative renderer conditions retained", "whole-output/human/generalization claims restricted",
                      "numerical statements/tables generated from one science release manifest"]})
    write(PAPER / "submission_package_manifest.json", {"status": "PRIVATE_REVIEW_NOT_SUBMISSION_READY", "science_release_sha256": release_hash,
          "original_paper_preserved": True, "author_institution_signoff": False, "current_journal_rules_verified": False})
    (PAPER / "number_sync_audit.md").write_text(
        "# Numerical synchronization\n\nAll result tables and narrative result quantities use generated_metrics.tex / generated table files from science_release_manifest.json. "
        "Template structural numbers (sections, seven fields, precision/types, dates) are not experimental counts. "
        "PDF/source rendering QA and author sign-off are separate gates.\n")
    print(PAPER)


if __name__ == "__main__": generate()
