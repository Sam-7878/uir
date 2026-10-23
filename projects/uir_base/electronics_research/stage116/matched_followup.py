"""Prospective secondary SLM factorial after the frozen deterministic primary.

Never relabels the already observed primary as a new unseen experiment.
"""
import argparse
import json
from pathlib import Path
import subprocess

from .artifacts import RunStore
from .curated_pilot import namespace_args
from ..policy import ROOT, sha, utc


def snapshot(directory, primary_directory):
    primary = RunStore(primary_directory)
    primary.verify()
    store = RunStore(directory)
    store.create()
    pins = json.loads(primary.path("code_snapshot.json").read_text())
    for name, digest in pins.items():
        original = ROOT / name
        if sha(original) != digest:
            raise ValueError("PRIMARY_SOURCE_NO_LONGER_MATCHES")
        store.write("frozen_primary_bytes/" + name, original.read_bytes())
    store.write("primary_lineage.json", {"path": str(primary.directory.relative_to(ROOT)),
                "manifest_sha256": sha(primary.path("evidence_manifest.json")), "source_pins": pins,
                "scope": "CURRENT_BYTES_MATCH_PRIMARY_FREEZE_NOT_AN_INDEPENDENT_BUILD"})
    store.write("README.md", "# LOCAL ONLY frozen primary code and binary bytes\n\nSource/binary pin bytes preserved before further secondary-code changes. Historical primary outputs remain unchanged.\n")
    store.seal()
    print(json.dumps({"snapshot": str(store.directory), "files": store.verify()}))


def worker(store, primary, *, hidden=True, overlay=None, mode="probe"):
    args = namespace_args(store.path("runtime"), primary.path("private_evaluator_only/gold.jsonl"), hidden=hidden, overlay=overlay, mode=mode)
    return args + ["--grammar", "release_snapshot", "--split", "SECONDARY_SLM_FIRST_EXPOSURE"]


def run(directory, primary_directory):
    primary = RunStore(primary_directory)
    primary.verify()
    store = RunStore(directory)
    store.create()
    for name in ("runtime", "preregistration", "isolation", "experiments"):
        store.path(name).mkdir()
    data = primary.path("runtime/runtime.jsonl").read_bytes()
    rows = [json.loads(x) for x in data.splitlines()]
    if len(rows) != 240 or len({r["family"] for r in rows}) != 60:
        raise ValueError("EXPECTED_FIXED_PRIMARY_CORPUS")
    store.write("runtime/runtime.jsonl", data)
    store.write("preregistration/secondary_protocol.json", {
        "created_at_utc": utc(), "status": "PROSPECTIVE_SECONDARY_SLM_FIRST_EXPOSURE_NOT_NEW_PRIMARY",
        "N_cases": 240, "clusters": 60, "conditions": 8, "expected_rows": 1920,
        "primary_already_observed": True, "primary_changed_or_repeated_for_tuning": False,
        "prior_primary_run": str(primary.directory.relative_to(ROOT)), "prior_primary_sha256": sha(primary.path("evidence_manifest.json")),
        "runtime_sha256": sha(store.path("runtime/runtime.jsonl")),
        "gold_access": "SCORER_ONLY_MOUNT_MASKED_RUNTIME", "model": "phi3.5:latest",
        "model_digest": "61819fb370a3c1a9be6694869331e5f85f867a079e9271d66cb223acb81d04ba",
        "dimensions": {"representation": ["UIR", "SPECIALIZED"], "selector": ["DETERMINISTIC", "SLM"], "renderer": ["TEMPLATE", "SLM"]},
        "parity": "Identical source, query, authority, shared guard and model payload. Identical request hashes reuse actual outputs; not independent repetitions.",
        "endpoints": ["ALLOW_complete", "DENY_nonempty_display", "raw_requested_selection_exact", "accepted_irrelevant", "original_source_unsupported_display"],
        "policy_labels": "protocol-assigned permissions, not inferred natural-language intent", "DENY_selection_gold": "empty",
        "statistics": "descriptive per condition plus family-cluster bootstrap95 CI of ALLOW completion, seed116; no new significance test or superiority claim",
        "invalid_or_timeout": "retain denominator, invalid typed output empty; request exception preserves partial raw and blocks completion; no retry or tuning",
        "native_prose_AUCR": "NOT_MEASURED", "runtime_LLM_calls_before_freeze": 0,
        "annotation_truth": "DECLARED_CNL_SOURCE_MACHINE_GOLD_AI_ONLY_NOT_HUMAN",
    })
    critical = list(Path(__file__).parent.glob("*.py")) + list((ROOT / "src/uir_common").glob("*.py")) + list((ROOT / "projects/uir_base/representation_research").glob("*.py"))
    pins = {str(p.relative_to(ROOT)): sha(p) for p in critical}
    store.write("preregistration/code_snapshot.json", pins)
    store.write("preregistration/freeze_receipt.json", {"created_at_utc": utc(),
                "protocol_sha256": sha(store.path("preregistration/secondary_protocol.json")), "model_calls_before_freeze": 0,
                "signature": "UNSIGNED_LOCAL_MACHINE_RECORD_NOT_AUTHOR_APPROVAL"})
    probes = {}
    for name, args in (("positive", worker(store, primary, hidden=False)), ("masked", worker(store, primary)),
                       ("mutated", worker(store, primary, overlay=primary.path("private_evaluator_only/mutated_gold.jsonl")))):
        result = subprocess.run(args, text=True, capture_output=True, close_fds=True, timeout=60)
        probes[name] = {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        store.write("isolation/" + name + ".json", probes[name])
    passed = (probes["positive"]["returncode"] != 0 and "GOLD_VISIBLE_TO_RUNTIME" in probes["positive"]["stderr"]
              and probes["masked"]["returncode"] == probes["mutated"]["returncode"] == 0 and probes["masked"]["stdout"] == probes["mutated"]["stdout"])
    store.write("isolation/gate.json", {"passed": passed, "network": "SHARED_HOST_LOOPBACK", "model_calls_during_probe": 0})
    if not passed:
        store.write("gate.json", {"status": "BLOCKED_OS_BOUNDARY", "model_calls": 0})
        store.seal()
        print("BLOCKED_OS_BOUNDARY")
        return
    print(json.dumps({"phase": "secondary_slm_frozen_and_started", "cases": 240, "conditions": 8}), flush=True)
    with store.path("experiments/runtime_capture.jsonl").open("x") as out, store.path("experiments/runtime_stderr.log").open("x") as err:
        execution = subprocess.run(worker(store, primary, mode="infer"), text=True, stdout=out, stderr=err, close_fds=True, timeout=3600)
    captures = [json.loads(x) for x in store.path("experiments/runtime_capture.jsonl").read_text().splitlines()]
    ends = [r for r in captures if r["type"] == "end"]
    store.write("execution_receipt.json", {"returncode": execution.returncode, "outcomes": sum(r["type"] == "outcome" for r in captures),
                "end_present": len(ends) == 1, "actual_calls": ends[0]["actual_model_calls"] if len(ends) == 1 else None,
                "code_unchanged": all(sha(ROOT / p) == digest for p, digest in pins.items()), "scoring": "PENDING_SCORER_ONLY_AUDIT"})
    store.write("primary_lineage.json", {"path": str(primary.directory.relative_to(ROOT)), "manifest_sha256": sha(primary.path("evidence_manifest.json"))})
    store.write("README.md", "# LOCAL ONLY prospective secondary SLM factorial\n\n240 existing primary cases, first runtime SLM exposure; original primary remains unchanged. All8 matched conditions share policy/evidence/guard. Raw captures are private. Scoring separately.\n")
    store.seal()
    print(json.dumps({"run": str(store.directory), "files": store.verify(), "execution": json.loads(store.path("execution_receipt.json").read_text())}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", type=Path, required=True)
    p.add_argument("--primary-run", type=Path, required=True)
    p.add_argument("--snapshot-primary", action="store_true")
    a = p.parse_args()
    (snapshot if a.snapshot_primary else run)(a.results_dir, a.primary_run)
