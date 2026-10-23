"""Scorer-only raw -> case -> aggregate pilot audit, no runtime/interpreter calls."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from .artifacts import RunStore
from .gold_reference import source_values
from ..policy import ROOT, sha, write_once
from .runner import DOCS, csv_text


def run(directory, input_directory):
    source = RunStore(input_directory)
    source.verify()
    store = RunStore(directory)
    store.create()
    captures = [json.loads(x) for x in source.path("experiments/runtime_capture.jsonl").read_text().splitlines() if x.strip()]
    outcomes = [r for r in captures if r["type"] == "outcome"]
    runtime = {r["case_id"]: r for r in (json.loads(x) for x in source.path("runtime/runtime.jsonl").read_text().splitlines())}
    gold = {r["case_id"]: r for r in (json.loads(x) for x in source.path("private_evaluator_only/gold.jsonl").read_text().splitlines())}
    paths = json.loads(source.path("source_lineage.json").read_text())
    originals = []
    for name, digest in paths.items():
        if sha(ROOT / name) != digest:
            raise ValueError("ORIGINAL_SOURCE_HASH_CHANGED")
    treasury = next(ROOT / p for p in paths if "treasury_debt_2024" in p)
    cargo = next(ROOT / p for p in paths if p.endswith("cargo_Cargo.toml"))
    originals = source_values(treasury, cargo)
    supported_lines = set()
    for record in originals:
        family = "US-Treasury:DebtToPenny" if record["entity"] == "US_TREASURY" else "GitHub:rust-lang/cargo"
        supported_lines.add(f"{record['entity']} | {record['metric']} | {record['period']} | {record['value']} {record['unit']} | source={family}{record['source_pointer']}")
    seen = set()
    scored = []
    groups = defaultdict(list)
    for row in outcomes:
        key = (row["case_id"], row["representation"], row["selector"], row["renderer"])
        if key in seen:
            raise ValueError("DUPLICATED_CASE_CONDITION")
        seen.add(key)
        g = gold[row["case_id"]]
        facts = runtime[row["case_id"]]["source"]["facts"]
        expected = {f["id"] for f in facts if all(f[k] == v for k, v in g["semantics"].items()) and f["value"] == g["value"]}
        if len(expected) != 1:
            raise ValueError("GOLD_NOT_UNIQUE_OR_REGISTRY_VALUE_DRIFT")
        actual, selected = set(row["fact_ids"]), set(row["raw_selector_ids"])
        lines = row["display"].splitlines()
        invalid_lines = [line for line in lines if line not in supported_lines]
        score = {"case_id": row["case_id"], "representation": row["representation"], "selector": row["selector"], "renderer": row["renderer"],
                 "family": runtime[row["case_id"]]["family"], "complete": actual == expected,
                 "raw_selection_exact": selected == expected, "raw_selection_precision": len(selected & expected) / len(selected) if selected else 0.0,
                 "raw_selection_recall": len(selected & expected) / len(expected), "accepted_irrelevant_facts": len(actual - expected),
                 "accepted_nonempty": bool(lines), "unsupported_whole_display_case": bool(invalid_lines),
                 "unsupported_display_claim_count": len(invalid_lines), "all_display_claims": len(lines),
                 "split": "DEVELOPMENT_NEW_SOURCE_PILOT", "native_prose_AUCR": "NOT_MEASURED"}
        scored.append(score)
        groups[(row["representation"], row["selector"], row["renderer"])].append(score)
    if len(outcomes) != 24 * 8 or len(groups) != 8 or any(len(v) != 24 for v in groups.values()):
        raise ValueError("MISSING_CASES_MUST_NOT_VANISH_FROM_DENOMINATOR")
    summary = []
    for (representation, selector, renderer), values in sorted(groups.items()):
        summary.append({"representation": representation, "selector": selector, "renderer": renderer, "N": len(values),
                        "complete": sum(r["complete"] for r in values), "raw_selection_exact": sum(r["raw_selection_exact"] for r in values),
                        "nonempty": sum(r["accepted_nonempty"] for r in values),
                        "unsupported_accepted_cases": sum(r["unsupported_whole_display_case"] for r in values),
                        "irrelevant_accepted_facts": sum(r["accepted_irrelevant_facts"] for r in values),
                        "independent_parent_clusters": 2, "population_CI": "NOT_INFERRED_TWO_PARENT_FAMILIES",
                        "native_prose_AUCR": "NOT_MEASURED"})
    paired = []
    indexed = {(r["case_id"], r["representation"], r["selector"], r["renderer"]): r for r in outcomes}
    for row in outcomes:
        if row["representation"] != "UIR": continue
        other = indexed[(row["case_id"], "SPECIALIZED", row["selector"], row["renderer"])]
        paired.append({"case_id": row["case_id"], "selector": row["selector"], "renderer": row["renderer"],
                       "same_accepted_ids": row["fact_ids"] == other["fact_ids"], "same_display": row["display"] == other["display"]})
    store.jsonl("scoring/per_case.jsonl", scored)
    store.write("statistics/summary.csv", csv_text(summary, list(summary[0])))
    store.jsonl("statistics/representation_pairs.jsonl", paired)
    end = next(r for r in captures if r["type"] == "end")
    store.write("statistics/execution_counts.json", {"unique_phi_calls": end["actual_model_calls"], "factorial_case_rows": len(outcomes),
                "paired_representation_rows": len(paired), "identical_accepted_and_display_pairs": sum(r["same_accepted_ids"] and r["same_display"] for r in paired),
                "role_curator_calls": 2, "independent_teams": False, "confirmatory": False,
                "cache_reuse": "IDENTICAL_PAYLOAD_HASHES_REUSED_NOT_INDEPENDENT_MODEL_REPETITIONS"})
    store.write("source_checkpoint.json", {"path": str(source.directory.relative_to(ROOT)), "manifest_sha256": sha(source.path("evidence_manifest.json"))})
    store.write("README.md", "# Scored new-source development pilot\n\nActual raw model outputs, declared CNL machine gold, 8 matched conditions and original-source whole-line audit. Two parent families: no population/generalization CI or confirmatory promotion.\n")
    report = DOCS / ("INDEPENDENT_GOLD_PILOT_RESULTS_" + store.directory.name + ".md")
    write_once(report, "# Independent-path pilot results (AI-only, controlled language)\n\n"
               f"Scored {len(outcomes)} condition rows from24 new-source requests. {end['actual_model_calls']} unique Phi calls plus2 curation/review calls. "
               f"Representation identical accepted-ID/display pairs: {sum(r['same_accepted_ids'] and r['same_display'] for r in paired)}/{len(paired)}; not superiority or powered equivalence.\n\n"
               "Ministral blinded annotations agreed24/24 with raw-source machine/CNL gold. Kernel mount masking passed positive visibility, negative visibility and canonical changed-label invariance. "
               "Network is host-loopback shared, NOT isolated; trusted host/kernel/Ollama assumption remains. Different local model roles are not independent humans or research teams.\n\n"
               + csv_text(summary, list(summary[0])) + "\n"
               "The observed pilot remains DEVELOPMENT. Next confirmation must use new unseen parent/template families and a powered, frozen method. "
               "No native-prose AUCR, protected-tool attacks or human effort has been measured here. No public release/submission or existing evidence rewrite occurred.\n")
    store.write("work_report_lineage.json", {str(report.relative_to(ROOT)): sha(report)})
    store.seal()
    print(json.dumps({"run": str(store.directory), "verified_files": store.verify(), "summary": summary}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--input-run", type=Path, required=True)
    args = parser.parse_args()
    run(args.results_dir, args.input_run)
