"""Scorer-only original-byte audit of the prospective secondary factorial.

No interpreter/guard is imported or called by this scorer.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics
import tomllib

from .artifacts import RunStore
from ..policy import ROOT, sha, write_once
from .runner import DOCS, csv_text


def line_from_original(fact, source):
    original = tomllib.loads((ROOT / source["manifest_ref"]).read_text())["package"]["version"]
    parts = original.split(".")
    index = {"package_version_major": 0, "package_version_minor": 1}[fact["metric"]]
    value = str(int(parts[index]))
    component = "major" if index == 0 else "minor"
    provenance = source["parent_family"] + ":" + source["manifest_sha256"] + "/package/version#" + component
    if fact["value"] != value or fact["provenance"] != provenance:
        raise ValueError("RUNTIME_SOURCE_FACT_DIFFERS_FROM_ORIGINAL")
    return f"{fact['entity']} | {fact['metric']} | release_snapshot | {value} COUNT | source={provenance}"


def quantile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    low = int(index)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (index - low)


def clustered_completion_ci(values):
    grouped = defaultdict(list)
    for v in values:
        if v["allowed"]: grouped[v["family"]].append(int(v["complete"]))
    parents = sorted(grouped)
    rng = random.Random(116)
    estimates = []
    for _ in range(2000):
        sample = [v for p in rng.choices(parents, k=len(parents)) for v in grouped[p]]
        estimates.append(statistics.mean(sample))
    return [quantile(estimates, .025), quantile(estimates, .975)]


def run(directory, input_directory):
    inputs = RunStore(input_directory)
    inputs.verify()
    receipt = json.loads(inputs.path("execution_receipt.json").read_text())
    if receipt["returncode"] != 0 or not receipt["end_present"] or not receipt["code_unchanged"]:
        raise ValueError("SECONDARY_EXECUTION_INCOMPLETE_RETAIN_RAW_NO_SILENT_EXCLUSIONS")
    primary = RunStore(ROOT / json.loads(inputs.path("primary_lineage.json").read_text())["path"])
    primary.verify()
    reserve = RunStore(ROOT / json.loads(primary.path("reserve_lineage.json").read_text())["path"])
    reserve.verify()
    sources = json.loads(reserve.path("source_registry/reserve_manifest.json").read_text())["records"]
    source_by_entity = {r["source_id"].upper().replace("-", "_"): r for r in sources}
    for source in sources:
        if sha(ROOT / source["manifest_ref"]) != source["manifest_sha256"]:
            raise ValueError("ORIGINAL_SOURCE_MODIFIED")
    runtime = {r["case_id"]: r for r in map(json.loads, inputs.path("runtime/runtime.jsonl").read_text().splitlines())}
    gold = {r["case_id"]: r for r in map(json.loads, primary.path("private_evaluator_only/gold.jsonl").read_text().splitlines())}
    captures = [json.loads(x) for x in inputs.path("experiments/runtime_capture.jsonl").read_text().splitlines()]
    observed = [r for r in captures if r["type"] == "outcome"]
    models = [r for r in captures if r["type"] == "model_capture"]
    keyed = {(r["case_id"], r["representation"], r["selector"], r["renderer"]): r for r in observed}
    if len(keyed) != len(observed) or any(k[0] not in gold for k in keyed):
        raise ValueError("DUPLICATE_OR_UNKNOWN_CASE_CONDITION")
    groups, scores = defaultdict(list), []
    for cid, g in gold.items():
        row = runtime[cid]
        facts = row["source"]["facts"]
        original_lines = {f["id"]: line_from_original(f, source_by_entity[f["entity"]]) for f in facts}
        requested = {f["id"] for f in facts if all(f[k] == v for k, v in g["semantics"].items())}
        if len(requested) != 1:
            raise ValueError("AMBIGUOUS_REQUESTED_FACT")
        # Independently recheck reference value against the original source string.
        target = next(f for f in facts if f["id"] in requested)
        if target["value"] != g["value"]:
            raise ValueError("SCORING_GOLD_DISAGREES_WITH_ORIGINAL")
        allowed = g["expected_state"] == "FULL_VERIFIED_ANSWER"
        expected = requested if allowed else set()
        for rep in ("UIR", "SPECIALIZED"):
            for selector in ("DETERMINISTIC", "SLM"):
                for renderer in ("TEMPLATE", "SLM"):
                    output = keyed.get((cid, rep, selector, renderer))
                    selected = set(output.get("raw_selector_ids", [])) if output else set()
                    accepted = set(output.get("fact_ids", [])) if output else set()
                    display = output.get("display", "") if output else ""
                    lines = display.splitlines()
                    unsupported = [line for line in lines if line not in set(original_lines.values())]
                    expected_lines = {original_lines[fid] for fid in expected}
                    complete = bool(output and accepted == expected and set(lines) == expected_lines and len(lines) == len(expected_lines)
                                    and output.get("state") == g["expected_state"])
                    p = len(selected & expected) / len(selected) if selected else float(not expected)
                    r = len(selected & expected) / len(expected) if expected else float(not selected)
                    score = {"case_id": cid, "family": g["family"], "representation": rep, "selector": selector, "renderer": renderer,
                             "row_present": output is not None, "allowed": allowed, "complete": complete,
                             "false_denial": bool(allowed and output and output.get("state") == "DENY"),
                             "allow_empty": bool(allowed and not lines), "deny_nonempty": bool(not allowed and lines),
                             "raw_selection_exact": selected == expected, "raw_selection_precision": p, "raw_selection_recall": r,
                             "raw_selection_F1": 2*p*r/(p+r) if p+r else 0,
                             "accepted_irrelevant": len(accepted - expected), "unsupported_display_case": bool(unsupported),
                             "unsupported_display_claims": len(unsupported), "display_claims": len(lines),
                             "split": "SECONDARY_SLM_FIRST_EXPOSURE", "native_prose_AUCR": "NOT_MEASURED"}
                    scores.append(score)
                    groups[(rep, selector, renderer)].append(score)
    summaries = []
    for key, values in sorted(groups.items()):
        allows = [r for r in values if r["allowed"]]
        denies = [r for r in values if not r["allowed"]]
        summaries.append({"representation": key[0], "selector": key[1], "renderer": key[2], "N": len(values),
                          "ALLOW_N": len(allows), "DENY_N": len(denies), "ALLOW_complete": sum(r["complete"] for r in allows),
                          "DENY_correct": sum(r["complete"] for r in denies), "raw_selection_exact": sum(r["raw_selection_exact"] for r in values),
                          "ALLOW_raw_selection_exact": sum(r["raw_selection_exact"] for r in allows),
                          "ALLOW_selection_macro_F1": statistics.mean(r["raw_selection_F1"] for r in allows),
                          "ALLOW_completion_cluster_bootstrap95": clustered_completion_ci(values),
                          "ALLOW_empty": sum(r["allow_empty"] for r in values), "false_denial": sum(r["false_denial"] for r in values),
                          "DENY_nonempty": sum(r["deny_nonempty"] for r in values), "accepted_irrelevant": sum(r["accepted_irrelevant"] for r in values),
                          "unsupported_display_cases": sum(r["unsupported_display_case"] for r in values),
                          "unsupported_display_claims": sum(r["unsupported_display_claims"] for r in values), "display_claims": sum(r["display_claims"] for r in values)})
    pairs = []
    for cid in gold:
        for selector in ("DETERMINISTIC", "SLM"):
            for renderer in ("TEMPLATE", "SLM"):
                a = keyed.get((cid, "UIR", selector, renderer))
                b = keyed.get((cid, "SPECIALIZED", selector, renderer))
                pairs.append({"case_id": cid, "selector": selector, "renderer": renderer,
                              "identical": bool(a and b and all(a.get(k) == b.get(k) for k in ("fact_ids", "display", "state")))})
    store = RunStore(directory)
    store.create()
    store.jsonl("scoring/per_case.jsonl", scores)
    store.write("statistics/summary.csv", csv_text(summaries, list(summaries[0])))
    store.write("statistics/summary.json", summaries)
    store.jsonl("statistics/representation_pairs.jsonl", pairs)
    counts = {"expected_rows": 1920, "observed_rows": len(observed), "missing_rows": sum(not r["row_present"] for r in scores),
              "unique_phi_calls": len(models), "paired_cases": len(pairs), "identical_pairs": sum(p["identical"] for p in pairs),
              "model_call_latency_ms": {"p50": quantile([m["latency_ms"] for m in models], .5), "p95": quantile([m["latency_ms"] for m in models], .95),
                                        "p99": quantile([m["latency_ms"] for m in models], .99)},
              "latency_scope": "actual_unique_Phi_HTTP_calls_including_loading_NOT_stagewise_or_per_representation_end_to_end",
              "raw_output_reuse": "identical_payload_hash_only_not_independent_repetitions", "confirmatory_primary_retested": False,
              "native_prose_AUCR": "NOT_MEASURED", "human_ground_truth": False, "independent_teams": False}
    store.write("statistics/execution_counts.json", counts)
    store.write("input_lineage.json", {"path": str(inputs.directory.relative_to(ROOT)), "manifest_sha256": sha(inputs.path("evidence_manifest.json"))})
    store.write("publication_gate.json", {"SLM_FACTORIAL": "SECONDARY_EXECUTED", "T17_TWO_DOMAIN_CONFIRMATION": "INCOMPLETE_SOFTWARE_ONLY_HOLDOUT",
                "T00_T14_COMPLETE": False, "MANUSCRIPT_READY": "BLOCKED", "PUBLIC_RELEASE_READY": "BLOCKED", "SUBMISSION_READY": "BLOCKED"})
    report = DOCS / ("SECONDARY_SLM_FACTORIAL_" + store.directory.name + ".md")
    write_once(report, "# Prospective secondary first-SLM-exposure factorial\n\n" + json.dumps(counts, indent=2) + "\n\n" +
               csv_text(summaries, list(summaries[0])) + "\n\nNo new primary test: the deterministic trial was already observed. "
               "Same240 declared-CNL cases,60 software source groups,8 equal-guard conditions; all outputs retained. "
               "Whole-display claims are exact closed lines independently checked against original manifest bytes, NOT native prose. "
               "Family bootstrap intervals are descriptive sample stability, not outside-frame generalization. Guard effects and cached model outputs must not be credited as representation superiority.\n")
    store.write("work_report_lineage.json", {str(report.relative_to(ROOT)): sha(report)})
    store.write("README.md", "# LOCAL ONLY independently scored secondary SLM factorial\n\nMachine/CNL gold, original-byte display checks. All milestones/publication remain separately gated.\n")
    store.seal()
    print(json.dumps({"run": str(store.directory), "files": store.verify(), "counts": counts, "summary": summaries}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", type=Path, required=True)
    p.add_argument("--input-run", type=Path, required=True)
    a = p.parse_args()
    run(a.results_dir, a.input_run)
