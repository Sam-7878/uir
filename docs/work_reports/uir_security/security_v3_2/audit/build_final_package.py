#!/usr/bin/env python3
"""Build the no-new-inference V3.2A documentation and submission packages."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from check_final_claims import scan_file


REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "results/llm_security_v3_2_closure"
PAPER = REPO / "docs/papers/_47_1_UIR_for_ZTA"
AUDIT_SOURCE = REPO / "docs/security_v3_2/audit"
PACKAGE_NAME = "HETE_UIR_ZTA_V3_2_FINAL_PACKAGE"
PACKAGE = REPO / "results" / PACKAGE_NAME

DOCUMENTATION = (
    "HETE_UIR_V3_2_FINAL_SCIENTIFIC_VALIDITY_REPORT.md",
    "ADAPTIVE_ATTACK_PROTOCOL.md",
    "AGENTDOJO_PROVENANCE.md",
    "BASELINE_FIDELITY_REPORT.md",
    "HUMAN_REVIEW_PROTOCOL.md",
    "OUTPUT_GUARD_VALIDATION_REPORT.md",
    "README_REPRODUCE.md",
)
MANUSCRIPT = ("_47.1_UIR_ZTA.tex", "v3_2_evidence.tex", "references.bib", "_47.1_UIR_ZTA.pdf")
EVIDENCE = (
    "publication_evidence_validation.json",
    "ARTIFACT_MANIFEST.json",
    "baseline_comparison.json",
    "per_class_results.json",
    "ablation_results.json",
    "multi_model_results.json",
    "adaptive_attack_results.json",
    "stochastic_results.json",
    "statistical_tests.json",
    "containment_funnel.json",
    "containment_funnel_cases.jsonl",
    "operational_interruption_summary.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def deterministic_zip(output: Path, entries: list[tuple[Path, str]]) -> None:
    output.unlink(missing_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, arcname in sorted(entries, key=lambda item: item[1]):
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def copy_named(source: Path, target: Path, names: tuple[str, ...]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        path = source / name
        if not path.is_file():
            raise FileNotFoundError(path)
        shutil.copy2(path, target / name)


def write_report(path: Path, audit: dict, build: dict, package_files: int) -> None:
    rows = [
        ("Primary population", f"{audit['primary_n']} = {audit['attack_n']} attacks + {audit['benign_n']} benign"),
        ("Primary systems", str(audit["systems_n"])),
        ("Ablation configurations", str(audit["ablation_configs"])),
        ("Adaptive", f"{audit['adaptive_seeds']} seeds / {audit['adaptive_queries']} actual queries / B=20"),
        ("Adaptive collision reframes", str(audit["adaptive_collision_reframes"])),
        ("Adaptive within-seed duplicate hashes", str(audit["adaptive_duplicate_candidate_hashes"])),
        ("Stochastic seeds", str(audit["stochastic_seeds"])),
        ("Qwen/Phi case IDs", f"{audit['qwen_case_ids']} / {audit['phi_case_ids']}"),
        ("Human validation", str(audit["human_validation"]).lower()),
        ("Public AgentDojo", str(audit["public_agentdojo"]).lower()),
        ("Frozen manifest", f"{audit['manifest_artifacts_checked']} checked / {audit['raw_manifest_hash_failures']} failures"),
        ("Stale claims", str(len(audit["stale_claim_findings"]))),
        ("Number/manuscript mismatches", str(audit["manuscript_mismatches"])),
        ("Final-package artifacts", str(package_files)),
    ]
    table = "\n".join(f"| {name} | {value} |" for name, value in rows)
    text = f"""# HETE UIR-ZTA V3.2A Final Reconciliation Report

Generated at {datetime.now(timezone.utc).isoformat()} from `results/llm_security_v3_2_closure/`.

## Decision

**PASS — V3.2A final artifact/manuscript reconciliation is complete.** No model inference, held-out replay, tuning, oracle change, dataset change, or evaluated source-epoch change was performed.

| Check | Result |
|---|---:|
{table}

## Claim reconciliation

- The abstract reports the final Qwen outcome (MCR 0/600, E2E-ASR 0/600, complete utility 249/250, FRR 1/250) and the Phi-3.5 negative outcome (MCR 3/600, E2E-ASR 6/600, complete utility 0/250, FRR 250/250).
- UIR-v2 identifies the architecture/schema/enforcement-envelope version; Security Evaluation V3.2 identifies the experimental protocol and evidence package.
- `MCR > E2E-ASR` is retained only as a conditional observed pattern. The `-no_input_guard`, `-no_resource_guard`, and authority-chain triple-knockout results replace the stale paired-ablation statement.
- Adaptive reporting includes six campaigns, 30 seeds per campaign, 180 seeds, 3,600 actual queries, and the one excessive-agency MCR seed with zero E2E seeds.
- The containment funnel is described as overlapping case-level indicators; 176 OutputGuard rejections are not called model compromises.
- Human validation remains false. AgentDojo remains an inspired local N=5 micro-suite. CaMeL and Progent remain inspired approximations.

## Evidence preservation

The original `ARTIFACT_MANIFEST.json` was verified against all {audit['manifest_artifacts_checked']} registered artifacts with zero missing, size, or SHA-256 failures. This includes the frozen raw rows, datasets, source-amendment history, and operational-interruption evidence. Incomplete Ollama responses were rejected before admission; execution resumed at the missing frozen case under unchanged settings. Some rejected response bodies were not retained.

## Manuscript build

The clean `pdflatex → bibtex → pdflatex → pdflatex` build completed with all four exit codes equal to zero. The final pass has {build['undefined_citations']} undefined citations, {build['undefined_references']} undefined references, {build['multiply_defined_labels']} multiply defined labels, {build['missing_input_files']} missing input files, and {build['duplicate_destinations']} duplicate PDF destinations.

## Package boundary

`security_v3_2_final.zip` contains exactly the seven final 850-case documentation files. `{PACKAGE_NAME}/` contains the reconciled manuscript, scoped documentation, selected frozen evidence, and this audit record. The full raw-run archive remains in the authoritative closure result and is intentionally excluded from the submission-support package.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    audit = json.loads((AUDIT_SOURCE / "final_number_reconciliation.json").read_text())
    build = json.loads((AUDIT_SOURCE / "manuscript_build_audit.json").read_text())
    if not audit.get("passed") or not build.get("passed"):
        raise RuntimeError("reconciliation and clean-build gates must pass before packaging")

    temp = PACKAGE.with_name(f".{PACKAGE_NAME}.tmp")
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir(parents=True)
    copy_named(PAPER, temp / "manuscript", MANUSCRIPT)
    copy_named(RESULTS / "documentation", temp / "documentation", DOCUMENTATION)
    copy_named(RESULTS, temp / "evidence", EVIDENCE)
    audit_dir = temp / "audit"
    audit_dir.mkdir()
    shutil.copy2(AUDIT_SOURCE / "manuscript_build.log", audit_dir / "manuscript_build.log")
    shutil.copy2(AUDIT_SOURCE / "manuscript_build_audit.json", audit_dir / "manuscript_build_audit.json")
    shutil.copy2(AUDIT_SOURCE / "final_number_reconciliation.json", audit_dir / "final_number_reconciliation.json")

    scan_targets = list((temp / "manuscript").glob("*.tex")) + list((temp / "documentation").glob("*.md"))
    findings = [finding for target in scan_targets for finding in scan_file(target)]
    scan_text = (
        f"PASS: scanned {len(scan_targets)} packaged manuscript/documentation files; 0 stale claims\n"
        if not findings
        else "\n".join(f"{f.path}:{f.line}: {f.rule_id}: {f.text}" for f in findings) + "\n"
    )
    (audit_dir / "stale_claim_scan.txt").write_text(scan_text, encoding="utf-8")
    if findings:
        raise RuntimeError(f"packaged stale-claim scan failed with {len(findings)} findings")

    pre_report_files = sum(path.is_file() for path in temp.rglob("*")) + 2
    write_report(audit_dir / "FINAL_RECONCILIATION_REPORT.md", audit, build, pre_report_files)
    manifest_rows = [
        {
            "path": path.relative_to(temp).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(temp.rglob("*"))
        if path.is_file() and path.name != "FINAL_PACKAGE_MANIFEST.json"
    ]
    (temp / "FINAL_PACKAGE_MANIFEST.json").write_text(
        json.dumps({"artifacts": manifest_rows}, indent=2) + "\n", encoding="utf-8"
    )

    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    temp.rename(PACKAGE)

    docs_zip = REPO / "results/security_v3_2_final.zip"
    deterministic_zip(
        docs_zip,
        [(RESULTS / "documentation" / name, name) for name in DOCUMENTATION],
    )
    package_zip = REPO / "results" / f"{PACKAGE_NAME}.zip"
    deterministic_zip(
        package_zip,
        [(path, f"{PACKAGE_NAME}/{path.relative_to(PACKAGE).as_posix()}") for path in PACKAGE.rglob("*") if path.is_file()],
    )
    for archive in (docs_zip, package_zip):
        archive.with_suffix(archive.suffix + ".sha256").write_text(
            f"{sha256(archive)}  {archive.name}\n", encoding="ascii"
        )

    print(f"built {PACKAGE.relative_to(REPO)}")
    print(f"built {docs_zip.relative_to(REPO)} ({len(DOCUMENTATION)} documents)")
    print(f"built {package_zip.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
