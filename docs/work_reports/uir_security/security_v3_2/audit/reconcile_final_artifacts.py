#!/usr/bin/env python3
"""Independently reconcile frozen V3.2 raw rows, summaries, and publication text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from check_final_claims import DEFAULT_FILES, scan_file


REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "results/llm_security_v3_2_closure"
PAPER = REPO / "docs/papers/_47_1_UIR_for_ZTA"
REPORT = RESULTS / "documentation/HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md"
DEFAULT_OUTPUT = REPO / "docs/security_v3_2/audit/final_number_reconciliation.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_jsonl(path: Path) -> dict[str, Any]:
    ids: set[str] = set()
    attack = benign = mcr = e2e = utility = frr = contract = 0
    systems: set[str] = set()
    models: set[str] = set()
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            case_id = row["case_id"]
            if case_id in ids:
                raise ValueError(f"duplicate case ID in {path}:{line_number}: {case_id}")
            ids.add(case_id)
            systems.add(row["system"])
            models.add(row["model"])
            verdict = row["verdict"]
            if row["is_attack"]:
                attack += 1
                mcr += bool(verdict["model_compromised"])
                e2e += bool(verdict["e2e_attack_succeeded"])
            else:
                benign += 1
                utility += bool(verdict["complete_task_success"])
                frr += bool(verdict["false_rejection"])
                contract += bool(verdict["contract_validity"])
    return {
        "total": attack + benign,
        "attack": attack,
        "benign": benign,
        "mcr": mcr,
        "e2e": e2e,
        "utility": utility,
        "frr": frr,
        "contract": contract,
        "ids": ids,
        "systems": sorted(systems),
        "models": sorted(models),
    }


def compare_summary(label: str, raw: dict[str, Any], summary: dict[str, Any], mismatches: list[str]) -> None:
    expected = {
        "total_cases": raw["total"],
        "attack_cases": raw["attack"],
        "benign_cases": raw["benign"],
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            mismatches.append(f"{label}.{key}: raw={value}, summary={summary.get(key)!r}")
    for key in ("mcr", "e2e", "utility", "frr", "contract"):
        denominator = raw["attack"] if key in {"mcr", "e2e"} else raw["benign"]
        entry = summary.get(key, {})
        if entry.get("count") != raw[key] or entry.get("denominator") != denominator:
            mismatches.append(
                f"{label}.{key}: raw={raw[key]}/{denominator}, "
                f"summary={entry.get('count')!r}/{entry.get('denominator')!r}"
            )


def verify_manifest() -> tuple[int, int, list[str]]:
    manifest = load(RESULTS / "ARTIFACT_MANIFEST.json")
    failures: list[str] = []
    for row in manifest["artifacts"]:
        path = RESULTS / row["path"]
        if not path.is_file():
            failures.append(f"missing:{row['path']}")
        elif path.stat().st_size != row["size"]:
            failures.append(f"size:{row['path']}")
        elif sha256(path) != row["sha256"]:
            failures.append(f"sha256:{row['path']}")
    return len(manifest["artifacts"]), len(failures), failures


def verify_primary(mismatches: list[str]) -> tuple[set[str], dict[str, dict[str, Any]]]:
    summaries = load(RESULTS / "baseline_comparison.json")
    aggregates: dict[str, dict[str, Any]] = {}
    canonical_ids: set[str] | None = None
    for path in sorted((RESULTS / "raw_runs").glob("primary_*.jsonl")):
        raw = aggregate_jsonl(path)
        if len(raw["systems"]) != 1:
            mismatches.append(f"{path.name}: expected one system, got {raw['systems']}")
            continue
        system = raw["systems"][0]
        aggregates[system] = raw
        compare_summary(f"baseline_comparison.{system}", raw, summaries.get(system, {}), mismatches)
        if canonical_ids is None:
            canonical_ids = raw["ids"]
        elif raw["ids"] != canonical_ids:
            mismatches.append(f"{path.name}: case IDs differ from the primary population")
    if set(aggregates) != set(summaries):
        mismatches.append(f"primary systems differ: raw={sorted(aggregates)}, summary={sorted(summaries)}")
    return canonical_ids or set(), aggregates


def verify_ablations(canonical_ids: set[str], mismatches: list[str]) -> int:
    summaries = load(RESULTS / "ablation_results.json")
    paths = sorted((RESULTS / "raw_runs").glob("ablation_*.jsonl"))
    names: set[str] = set()
    for path in paths:
        name = path.stem.removeprefix("ablation_")
        names.add(name)
        raw = aggregate_jsonl(path)
        if raw["ids"] != canonical_ids:
            mismatches.append(f"{path.name}: case IDs differ from primary population")
        compare_summary(f"ablation_results.{name}", raw, summaries.get(name, {}), mismatches)
    if names != set(summaries):
        mismatches.append(f"ablation names differ: raw={sorted(names)}, summary={sorted(summaries)}")
    return len(paths)


def verify_models(
    canonical_ids: set[str], primary: dict[str, dict[str, Any]], mismatches: list[str]
) -> tuple[int, int]:
    summaries = load(RESULTS / "multi_model_results.json")
    qwen = primary.get("HETE", {})
    if qwen:
        compare_summary("multi_model_results.qwen2.5:7b", qwen, summaries.get("qwen2.5:7b", {}), mismatches)
    phi = aggregate_jsonl(RESULTS / "raw_runs/multimodel_phi.jsonl")
    if phi["ids"] != canonical_ids:
        mismatches.append("multimodel_phi.jsonl: case IDs differ from Qwen HETE")
    compare_summary("multi_model_results.phi3.5:latest", phi, summaries.get("phi3.5:latest", {}), mismatches)
    return len(qwen.get("ids", set())), len(phi["ids"])


def verify_adaptive(mismatches: list[str]) -> tuple[int, int, int, int]:
    rows = []
    with (RESULTS / "raw_runs/adaptive.jsonl").open(encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    campaigns = Counter(row["campaign"] for row in rows)
    queries = sum(len(row["queries"]) for row in rows)
    collision_reframes = sum(
        int(query.get("collision_reframes", 0)) for row in rows for query in row["queries"]
    )
    # The preregistered uniqueness constraint is within each adaptive seed. The
    # same frozen candidate may validly occur in different seed trajectories.
    duplicate_hashes = sum(
        len(hashes) - len(set(hashes))
        for row in rows
        for hashes in [[query["input_hash"] for query in row["queries"]]]
    )
    if len(rows) != 180 or set(campaigns.values()) != {30} or len(campaigns) != 6:
        mismatches.append(f"adaptive population: campaigns={dict(campaigns)}, seeds={len(rows)}")
    if queries != 3600 or any(row["budget"] != 20 or len(row["queries"]) != 20 for row in rows):
        mismatches.append(f"adaptive budget/query mismatch: queries={queries}")
    if collision_reframes != 6:
        mismatches.append(f"adaptive collision reframes: expected 6, got {collision_reframes}")
    if duplicate_hashes:
        mismatches.append(f"adaptive duplicate candidate hashes: {duplicate_hashes}")

    summaries = load(RESULTS / "adaptive_attack_results.json")
    for campaign, count in campaigns.items():
        group = [row for row in rows if row["campaign"] == campaign]
        raw_mcr = sum(row["first_mcr_query"] is not None for row in group)
        raw_e2e = sum(row["first_e2e_query"] is not None for row in group)
        summary = summaries.get(campaign, {})
        expected = {
            "seeds": count,
            "queries": sum(len(row["queries"]) for row in group),
            "mcr_seeds": raw_mcr,
            "e2e_seeds": raw_e2e,
        }
        for key, value in expected.items():
            if summary.get(key) != value:
                mismatches.append(f"adaptive.{campaign}.{key}: raw={value}, summary={summary.get(key)!r}")
    return len(rows), queries, collision_reframes, duplicate_hashes


def verify_stochastic(mismatches: list[str]) -> int:
    summaries = load(RESULTS / "stochastic_results.json")
    paths = sorted((RESULTS / "raw_runs").glob("stochastic_*.jsonl"))
    for path in paths:
        seed = path.stem.removeprefix("stochastic_")
        raw = aggregate_jsonl(path)
        if raw["total"] != 30:
            mismatches.append(f"{path.name}: expected 30 rows, got {raw['total']}")
        compare_summary(f"stochastic_results.{seed}", raw, summaries.get(seed, {}), mismatches)
    if {path.stem.removeprefix('stochastic_') for path in paths} != set(summaries):
        mismatches.append("stochastic seed set differs between raw rows and summary")
    return len(paths)


def require_text(label: str, text: str, patterns: dict[str, str], mismatches: list[str]) -> None:
    for claim, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL) is None:
            mismatches.append(f"{label}: missing or inconsistent claim: {claim}")


def verify_surfaces(mismatches: list[str]) -> list[dict[str, Any]]:
    main = (PAPER / "_47.1_UIR_ZTA.tex").read_text(encoding="utf-8")
    evidence = (PAPER / "v3_2_evidence.tex").read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    require_text(
        "main manuscript",
        main,
        {
            "Qwen primary result": r"Qwen2\.5-7B.*?MCR\s*\$?=0/600.*?E2E-ASR\s*\$?=0/600.*?249/250.*?1/250",
            "Phi negative result": r"Phi-3\.5.*?MCR\s*\$?=3/600.*?E2E-ASR\s*\$?=6/600.*?utility\s*\$?=0/250.*?FRR\s*\$?=250/250",
            "conditional containment": r"conditional empirical pattern rather than a universal theorem",
            "actual ablations": r"Removing InputGuard.*?four model compromises.*?Removing ResourceGuard.*?20 E2E.*?CapabilityGate, Policy, and Action Revalidation.*?eight model compromises and seven E2E",
        },
        mismatches,
    )
    require_text(
        "evidence include",
        evidence,
        {
            "version distinction": r"UIR-v2 names the architecture.*?V3\.2 names the experimental protocol",
            "Phi first-class limitation": r"Phi-3\.5 completed 0/250.*?MCR \$=3/600\$.*?E2E-ASR \$=6/600\$",
            "adaptive scale": r"six campaigns, 30 seeds per campaign, and 3,600 actual queries",
            "overlapping funnel": r"containment funnel is an overlapping-indicator view",
            "completed closure": r"passed the strict raw-evidence validity gate, artifact binding audit, full test suite, and clean LaTeX/BibTeX build",
            "operational limitation": r"Incomplete Ollama responses were rejected before admission.*?Some rejected response bodies were not retained",
        },
        mismatches,
    )
    require_text(
        "final report",
        report,
        {
            "primary scale": r"Primary N=850, with 600 attacks and 250 benign cases",
            "adaptive scale": r"Adaptive execution: 180 seeds; 3600 actual queries",
            "ablation scale": r"12 ablation configurations has N=850",
            "scope flags": r"human_validation=false.*?Actual AgentDojo was not imported or executed",
        },
        mismatches,
    )
    return [finding.__dict__ for path in DEFAULT_FILES for finding in scan_file(path)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    mismatches: list[str] = []
    manifest_count, manifest_failures, manifest_details = verify_manifest()
    primary_ids, primary = verify_primary(mismatches)
    ablation_count = verify_ablations(primary_ids, mismatches)
    qwen_ids, phi_ids = verify_models(primary_ids, primary, mismatches)
    adaptive_seeds, adaptive_queries, collision_reframes, duplicate_hashes = verify_adaptive(mismatches)
    stochastic_seeds = verify_stochastic(mismatches)
    stale_findings = verify_surfaces(mismatches)
    if stale_findings:
        mismatches.extend(
            f"stale claim {item['rule_id']} at {item['path']}:{item['line']}" for item in stale_findings
        )

    publication = load(RESULTS / "publication_evidence_validation.json")
    result = {
        "primary_n": len(primary_ids),
        "attack_n": primary.get("HETE", {}).get("attack", 0),
        "benign_n": primary.get("HETE", {}).get("benign", 0),
        "systems_n": len(primary),
        "ablation_configs": ablation_count,
        "adaptive_seeds": adaptive_seeds,
        "adaptive_queries": adaptive_queries,
        "qwen_case_ids": qwen_ids,
        "phi_case_ids": phi_ids,
        "human_validation": publication.get("human_validation"),
        "public_agentdojo": publication.get("public_agentdojo"),
        "raw_manifest_hash_failures": manifest_failures,
        "manuscript_mismatches": len(mismatches),
        "publication_evidence_valid": publication.get("publication_evidence_valid"),
        "scientific_integrity_failures": publication.get("scientific_integrity_failures"),
        "manifest_artifacts_checked": manifest_count,
        "manifest_failure_details": manifest_details,
        "adaptive_campaigns": 6,
        "adaptive_budget_per_seed": 20,
        "adaptive_collision_reframes": collision_reframes,
        "adaptive_duplicate_candidate_hashes": duplicate_hashes,
        "stochastic_seeds": stochastic_seeds,
        "stale_claim_findings": stale_findings,
        "mismatches": mismatches,
        "passed": (
            not mismatches
            and manifest_failures == 0
            and publication.get("publication_evidence_valid") is True
            and publication.get("scientific_integrity_failures") == []
        ),
    }
    output = args.output
    if not output.is_absolute():
        output = REPO / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
