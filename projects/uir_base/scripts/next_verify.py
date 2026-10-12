"""Independent raw-label agreement replay and isolated archive reproduction."""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_replay(directory):
    import jsonschema
    manifest = json.loads((directory / "review_manifest.json").read_text())
    packets = {row["case_id"]: row for row in read(directory / "review_packets.jsonl")}
    fields = [key for key, spec in manifest["schema"]["properties"].items() if "enum" in spec]
    records = {}
    for reviewer in ("AI_J1", "AI_J2"):
        raw = read(directory / f"{reviewer}_raw_reviews.jsonl")
        if len(raw) != manifest["N"] or len({r["case_id"] for r in raw}) != len(raw):
            raise ValueError("Duplicate/missing reviewer case")
        records[reviewer] = {}
        for row in raw:
            response = row["response"]; content = response["message"]["content"]
            if hashlib.sha256(content.encode()).hexdigest() != row["raw_content_sha256"]:
                raise ValueError("Response hash mismatch")
            label = json.loads(content)
            jsonschema.validate(label, manifest["schema"])
            if label != row["label"] or response["done_reason"] != "stop" or response["done"] is not True:
                raise ValueError("Raw-label/finish mismatch")
            if label["request_quote"] and label["request_quote"] not in packets[row["blinded_case_id"]]["raw_input"]:
                raise ValueError("Invented source quote")
            if row["model_digest"] != manifest["models"][reviewer]["digest"]:
                raise ValueError("Reviewer artifact mismatch")
            records[reviewer][row["case_id"]] = label
    if records["AI_J1"].keys() != records["AI_J2"].keys():
        raise ValueError("Unpaired reviewer cases")
    stats = {}; unresolved = set()
    for field in fields:
        pairs = [(records["AI_J1"][cid][field], records["AI_J2"][cid][field]) for cid in records["AI_J1"]]
        n = len(pairs); equal = sum(x == y for x, y in pairs)
        marginals_a = Counter(x for x, _ in pairs); marginals_b = Counter(y for _, y in pairs)
        expected = Fraction(sum(marginals_a[v] * marginals_b[v] for v in marginals_a.keys() | marginals_b.keys()), n * n)
        observed = Fraction(equal, n)
        kappa = (observed - expected) / (1 - expected) if expected != 1 else None
        stats[field] = {"N": n, "N_agree": equal, "agreement": float(observed), "kappa": float(kappa) if kappa is not None else None,
                        "joint_uncertain": sum(x == y == "UNCERTAIN" for x, y in pairs),
                        "decisive_agreement": sum(x == y and x != "UNCERTAIN" for x, y in pairs)}
        for cid in records["AI_J1"]:
            x, y = records["AI_J1"][cid][field], records["AI_J2"][cid][field]
            if x != y or x == "UNCERTAIN" or y == "UNCERTAIN":
                unresolved.add(cid)
    if len(unresolved) != manifest["N_unresolved_cases"]:
        raise ValueError("Unresolved union mismatch")
    return {"status": "RAW_RESPONSE_TO_LABELS_AND_EXACT_AGREEMENT_PASS_NOT_SEMANTIC_VALIDATION",
            "N_cases": manifest["N"], "N_responses": sum(len(v) for v in records.values()),
            "N_unresolved": len(unresolved), "human_validation": False, "fields": stats}


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def safe_extract(archive, destination):
    if destination.exists():
        raise FileExistsError("Use a new clean-room directory")
    with zipfile.ZipFile(archive) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive entry")
        for entry in source.infolist():
            path = Path(entry.filename)
            if path.is_absolute() or ".." in path.parts or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Unsafe archive path or symbolic link")
        source.extractall(destination)
    manifest = json.loads((destination / "archive_manifest.json").read_text())
    for item in manifest["files"]:
        if sha(destination / item["path"]) != item["sha256"]:
            raise ValueError(f"Archive dependency hash mismatch: {item['path']}")


def reproduce(archive, destination):
    safe_extract(archive, destination)
    captured = destination / "projects/uir_base/results/mdpi_next_2026_10_11_v2"
    expected = json.loads((captured / "release_manifest.json").read_text())
    output = destination / "reproduced-offline"
    code = (
        "import sys; from pathlib import Path; "
        f"root=Path({str(destination)!r}); sys.path[:0]=[str(root/'src'),str(root)]; "
        "from projects.uir_base.scripts.next_release import run; "
        f"run(Path({str(output)!r})); "
        "leaked=[(name,getattr(mod,'__file__',None)) for name,mod in sys.modules.items() "
        "if name.split('.')[0] in {'projects','evaluation','uir_common','llm_trust'} "
        "and getattr(mod,'__file__',None) and not Path(mod.__file__).resolve().is_relative_to(root)]; "
        "assert not leaked, leaked"
    )
    result = subprocess.run([sys.executable, "-I", "-c", code], cwd=destination, capture_output=True, text=True)
    (destination / "clean_room_reproduction.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    differences = []
    for relative, digest in expected["scientific_output_sha256"].items():
        if not (output / relative).is_file() or sha(output / relative) != digest:
            differences.append(relative)
    if differences:
        raise ValueError(f"Scientific result mismatch: {differences}")
    replay = review_replay(destination / "projects/uir_base/results/mdpi_revision_2026_10_11/ai_reviews/20261011T114157Z")
    fresh_report = None
    if (captured / "fresh_matched/fresh_run_manifest.json").is_file():
        code = (
            "import sys; from pathlib import Path; "
            f"root=Path({str(destination)!r}); sys.path[:0]=[str(root/'src'),str(root)]; "
            "from projects.uir_base.scripts.next_verify import replay_fresh; "
            f"replay_fresh(Path({str(captured)!r}),Path({str(destination / 'reproduced-fresh')!r}))"
        )
        fresh = subprocess.run([sys.executable, "-I", "-c", code], cwd=destination, capture_output=True, text=True)
        (destination / "clean_room_fresh_replay.log").write_text(fresh.stdout + fresh.stderr)
        if fresh.returncode:
            raise RuntimeError(fresh.stdout + fresh.stderr)
        fresh_report = json.loads((destination / "reproduced-fresh/verification.json").read_text())
    report = {"status": "ARCHIVE_ONLY_OFFLINE_REPRODUCTION_PASS", "scientific_files_equal": len(expected["scientific_output_sha256"]),
              "no_development_checkout_imports": True, "ai_raw_response_replay": replay,
              "archive_sha256": sha(archive), "fresh_inference_rerun": False, "semantic_validation": False}
    report["fresh_capture_replay"] = fresh_report
    (destination / "clean_room_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))


def review_v2_replay(directory, split):
    import csv
    import jsonschema
    protocol = json.loads((directory / "protocol.json").read_text())
    captures = read(directory / f"{split}_raw_reviews.jsonl")
    truth = {r["case_id"]: r for r in read(directory / "synthetic_scoring_only.jsonl") if r["split"] == split}
    packets = {r["case_id"]: r for r in read(directory / "packets.jsonl") if r["split"] == split}
    if len(captures) != 2 * len(truth) or len({(r["reviewer"], r["case_id"]) for r in captures}) != len(captures):
        raise ValueError("Missing/duplicate new review")
    index = {}
    for row in captures:
        response = row["response"] or {}; parsed = None
        try:
            if response.get("done") is not True or response.get("done_reason") != "stop":
                raise ValueError("Incomplete response")
            parsed = json.loads(response["message"]["content"])
            jsonschema.validate(parsed, protocol["schema"])
            if parsed["request_quote"] not in packets[row["case_id"]]["raw_input"]:
                raise ValueError("Invented quote")
            if parsed["candidate_status"] == "ABSENT" and any(parsed[f] != "NOT_EVALUABLE" for f in ("slot_match", "condition_preservation")):
                raise ValueError("Absent candidate rated evaluable")
        except (ValueError, KeyError, TypeError, jsonschema.ValidationError):
            parsed = None
        if parsed != row["label"] or row["valid"] != (parsed is not None):
            raise ValueError("Reviewer raw-label mismatch")
        if row["model_digest"] != protocol["models"][row["reviewer"]][1]:
            raise ValueError("Reviewer artifact mismatch")
        index[row["reviewer"], row["case_id"]] = row
    with (directory / f"{split}_accuracy.csv").open() as source:
        for metric in csv.DictReader(source):
            rs = [r for r in captures if r["reviewer"] == metric["reviewer"] and r["valid"]]
            correct = sum(r["label"][metric["field"]] == truth[r["case_id"]][metric["field"]] for r in rs)
            if correct != int(metric["N_correct"]) or len(rs) != int(metric["N_valid"]):
                raise ValueError("Synthetic accuracy mismatch")
    unresolved = set()
    fields = [f for f, spec in protocol["schema"]["properties"].items() if "enum" in spec]
    with (directory / f"{split}_agreement.csv").open() as source:
        for metric in csv.DictReader(source):
            field = metric["field"]; pairs = []
            for cid in truth:
                x, y = index["AI_J1", cid], index["AI_J2", cid]
                if not x["valid"] or not y["valid"]:
                    unresolved.add(cid); continue
                x, y = x["label"][field], y["label"][field]; pairs.append((x, y))
                if x != y or "UNCERTAIN" in {x, y}:
                    unresolved.add(cid)
            if len(pairs) != int(metric["N_jointly_valid"]) or sum(x == y for x, y in pairs) != int(metric["N_agree"]):
                raise ValueError("New agreement mismatch")
            n = len(pairs); ma = Counter(x for x, y in pairs); mb = Counter(y for x, y in pairs)
            expected = Fraction(sum(ma[v] * mb[v] for v in protocol["schema"]["properties"][field]["enum"]), n * n) if n else None
            observed = Fraction(sum(x == y for x, y in pairs), n) if n else None
            kappa = float((observed - expected) / (1 - expected)) if n and expected != 1 else None
            recorded = float(metric["kappa"]) if metric["kappa"] else None
            if (kappa is None) != (recorded is None) or kappa is not None and abs(kappa - recorded) > 1e-12:
                raise ValueError("New kappa mismatch")
    report = json.loads((directory / f"{split}_summary.json").read_text())
    if len(unresolved) != report["N_unresolved_cases"] or sha(directory / f"{split}_raw_reviews.jsonl") != report["raw_sha256"]:
        raise ValueError("New unresolved/hash mismatch")
    return {"status": "RAW_TO_SYNTHETIC_ACCURACY_AGREEMENT_PASS_NOT_HUMAN_VALIDATION", "N_responses": len(captures), "N_unresolved": len(unresolved)}


def replay_fresh(captured, output):
    import shutil
    from projects.uir_base.scripts.next_fresh_replay import replay as matched
    from projects.uir_base.scripts import next_holdout
    output.mkdir(exist_ok=False)
    matched(captured, output / "matched")
    reports = {split: review_v2_replay(captured / "ai_review_v2", split) for split in ("calibration", "holdout")}
    manifest = json.loads((captured / "finqa_holdout_v2/execution_manifest.json").read_text())
    if manifest["status"] != "RAW_CAPTURE_COMPLETE_NOT_SUBMISSION_READY":
        raise ValueError("External inference incomplete")
    if sha(captured / "finqa_holdout_v2/raw_requests_responses.jsonl") != manifest["raw_sha256"]:
        raise ValueError("External raw hash mismatch")
    replay_dir = output / "finqa_holdout_v2"; replay_dir.mkdir()
    for name in ("protocol.json", "runtime_packets.jsonl", "raw_requests_responses.jsonl"):
        shutil.copyfile(captured / "finqa_holdout_v2" / name, replay_dir / name)
    # Redirect only generated outputs; authoritative corpus remains in extracted root.
    next_holdout.DEFAULT = output
    next_holdout.score()
    for name in ("case_results.jsonl", "summary.csv"):
        if sha(replay_dir / name) != sha(captured / "finqa_holdout_v2" / name):
            raise ValueError("External raw-to-metric mismatch")
    result = {"status": "MATCHED_AI_AND_FINQA_CAPTURE_REPLAY_PASS", "N_finqa_requests": 800,
              "model_calls_in_replay": 0, "reviews": reports, "human_validation": False}
    (output / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--extract-to", type=Path)
    parser.add_argument("--review-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.review_dir:
        result = review_replay(args.review_dir)
        if args.report:
            args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2))
    elif args.archive and args.extract_to:
        reproduce(args.archive.resolve(), args.extract_to.resolve())
    else:
        parser.error("Explicit review directory or archive/extract destination required")


if __name__ == "__main__":
    main()
