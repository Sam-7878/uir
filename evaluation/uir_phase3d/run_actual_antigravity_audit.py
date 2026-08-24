#!/usr/bin/env python3
"""Collect genuine isolated AntiGravity model judgments with resumable provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKETS = ROOT / "evaluation/uir_phase3d/audit_packets"
SCHEMA = ROOT / "evaluation/uir_phase3d/actual_ai_batch_response.schema.json"
WORK = ROOT / "results/uir_phase3d/actual_ai_work"

REVIEWERS = {
    "AI-R1": ("gemini-3.5-flash", "AntiGravity Gemini 3.5 Flash", "high"),
    "AI-R2": ("gemini-3.6-flash-high", "AntiGravity Gemini 3.6 Flash", "high"),
    "AI-R3": ("gemini-3.1-pro", "AntiGravity Gemini 3.1 Pro", "high"),
}
FIELDS = [
    "source_text_valid", "language_valid", "intent_valid", "target_valid",
    "conditions_valid", "policy_valid", "outcome_valid", "claims_valid",
]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    )
    return result.stdout.strip()


def atomic_write_jsonl(path: Path, rows: list[dict]) -> None:
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def parse_response(response: object) -> dict:
    if isinstance(response, dict):
        return response
    text = str(response).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def validate_judgments(payload: dict, expected_ids: list[str]) -> list[dict]:
    rows = payload.get("judgments")
    if not isinstance(rows, list) or len(rows) != len(expected_ids):
        raise ValueError(f"judgment count mismatch: got={len(rows) if isinstance(rows, list) else 'invalid'}, expected={len(expected_ids)}")
    indexed = {row.get("case_id"): row for row in rows}
    if set(indexed) != set(expected_ids) or len(indexed) != len(rows):
        raise ValueError("case IDs are missing, duplicated, or unexpected")
    ordered = []
    for case_id in expected_ids:
        row = indexed[case_id]
        if any(str(row.get(field, "")).upper() not in {"1", "0", "NA"} for field in FIELDS):
            raise ValueError(f"invalid judgment field: {case_id}")
        if not isinstance(row.get("reconstructed"), dict) or not str(row.get("reasoning_summary", "")).strip():
            raise ValueError(f"missing reconstruction/rationale: {case_id}")
        ordered.append(row)
    return ordered


def build_prompt(reviewer: str, batch: list[dict]) -> str:
    return (
        f"You are {reviewer}, an independent benchmark auditor. Perform the reconstruction-first audit now. "
        "Do not use tools, inspect files, or ask questions. Use only the supplied packet objects. "
        "For each case, first reconstruct intent, target, conditions, policy decision, expected outcome, "
        "and required claims from source_text; then compare that reconstruction with candidate_annotation "
        "contained in audit_input expected_* fields. Return exactly one judgment per case in the supplied "
        "order. All eight validity fields must be strings: '1', '0', or 'NA'. Provide only a concise "
        "reasoning_summary of at most 240 characters, never hidden chain-of-thought. Keep reconstructed "
        "conditions compact. In reconstructed required_claims include only claim_type, entity_id, attribute, "
        "and period; do not repeat numeric values, units, provenance URIs, or hashes. The output must match "
        "the registered JSON schema.\n\n"
        "AUDIT_PACKET_BATCH:\n" + json.dumps(batch, ensure_ascii=False, separators=(",", ":"))
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer", choices=REVIEWERS, required=True)
    default_agy = Path("/home/sam/.local/bin/agy") if Path("/home/sam/.local/bin/agy").exists() else ROOT / ".tools/antigravity/agy"
    parser.add_argument("--agy", type=Path, default=default_agy)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    args = parser.parse_args()

    model, engine, effort = REVIEWERS[args.reviewer]
    packet_path = PACKETS / f"audit_input_{args.reviewer}.jsonl"
    packets = read_jsonl(packet_path)
    if args.limit:
        packets = packets[:args.limit]
    manifest = json.loads((PACKETS / "audit_packet_manifest.json").read_text(encoding="utf-8"))
    prompt_hash = manifest["prompt_template_sha256"]
    collector_commit = repository_commit()
    packet_sha256 = sha256_file(packet_path)
    schema_sha256 = sha256_file(SCHEMA)

    WORK.mkdir(parents=True, exist_ok=True)
    output = WORK / f"actual_ai_review_{args.reviewer[-2:]}.jsonl"
    raw_dir = WORK / f"raw_{args.reviewer[-2:]}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    isolated_workspace = WORK / "isolated_workspaces" / args.reviewer
    isolated_workspace.mkdir(parents=True, exist_ok=True)
    records = read_jsonl(output) if output.exists() else []
    completed = {row["case_id"] for row in records}
    pending = [packet for packet in packets if packet["case_id"] not in completed]
    print(json.dumps({"reviewer": args.reviewer, "engine": engine, "completed": len(completed), "pending": len(pending)}), flush=True)

    for offset in range(0, len(pending), args.batch_size):
        batch = pending[offset:offset + args.batch_size]
        case_ids = [packet["case_id"] for packet in batch]
        prompt = build_prompt(args.reviewer, batch)
        error = None
        for attempt in range(1, args.max_attempts + 1):
            started = time.monotonic()
            command = [
                str(args.agy), "--model", model, "--mode", "plan",
                "--disable-slash-commands", "--output-format", "json", "--json-schema", str(SCHEMA),
                "--print-timeout", f"{args.timeout_seconds}s", "--print", prompt,
            ]
            if effort:
                command[3:3] = ["--effort", effort]
            result = subprocess.run(command, cwd=isolated_workspace, text=True, capture_output=True, timeout=args.timeout_seconds + 60)
            timestamp = datetime.now(timezone.utc).isoformat()
            try:
                lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                if not lines:
                    raise ValueError("empty CLI output")
                outers = [json.loads(line) for line in lines]
                for o in outers:
                    if o.get("status") == "ERROR":
                        raise ValueError(f"CLI status=ERROR: {o.get('error')}")
                success_outers = [o for o in outers if o.get("status") == "SUCCESS"]
                outer = success_outers[-1] if success_outers else outers[-1]
                if result.returncode or outer.get("status") != "SUCCESS":
                    raise ValueError(f"CLI status={outer.get('status')} returncode={result.returncode}: {outer.get('error')}")
                raw_response = outer.get("structured_output") or outer.get("response", "")
                judgments = validate_judgments(parse_response(raw_response), case_ids)
                raw_hash = hashlib.sha256(str(outer.get("response", "")).encode("utf-8")).hexdigest()
                batch_id = f"{args.reviewer}-{case_ids[0]}--{case_ids[-1]}"
                capture = {
                    "batch_id": batch_id, "reviewer_id": args.reviewer, "engine": engine, "model_selector": model,
                    "case_ids": case_ids, "timestamp": timestamp, "duration_seconds": time.monotonic() - started,
                    "returncode": result.returncode, "stdout_object": outer, "stderr": result.stderr,
                    "raw_response_sha256": raw_hash,
                }
                (raw_dir / f"{batch_id}.json").write_text(json.dumps(capture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                for judgment in judgments:
                    records.append({
                        "reviewer_id": args.reviewer,
                        "engine": engine,
                        "case_id": judgment["case_id"],
                        "prompt_template_sha256": prompt_hash,
                        "provenance": {
                            "session_run_id": outer["conversation_id"],
                            "timestamp": timestamp,
                            "generation_interface": "Antigravity CLI 1.1.11 --print --json-schema",
                            "raw_response_sha256": raw_hash,
                            "temperature": "not_exposed_by_antigravity_cli",
                            "annotation_method": "actual_model_generation",
                            "model_selector": model,
                            "collector_commit": collector_commit,
                            "audit_packet_sha256": packet_sha256,
                            "response_schema_sha256": schema_sha256,
                            "usage": outer.get("usage", {}),
                        },
                        "judgment": judgment,
                    })
                atomic_write_jsonl(output, records)
                print(json.dumps({"reviewer": args.reviewer, "batch": batch_id, "cases": len(case_ids), "total": len(records), "conversation_id": outer["conversation_id"]}), flush=True)
                error = None
                break
            except Exception as exc:
                error = f"attempt {attempt}: {type(exc).__name__}: {exc}; stderr={result.stderr[-1000:]} stdout={result.stdout[-1000:]}"
                print(json.dumps({"reviewer": args.reviewer, "case_ids": case_ids, "error": error}), flush=True)
                time.sleep(min(5 * attempt, 15))
        if error:
            raise SystemExit(error)

    expected = {packet["case_id"] for packet in packets}
    actual = {row["case_id"] for row in records}
    if actual != expected or len(records) != len(expected):
        raise SystemExit(f"final coverage mismatch: {len(actual)}/{len(expected)}")
    print(json.dumps({"status": "complete", "reviewer": args.reviewer, "records": len(records), "output": str(output)}), flush=True)


if __name__ == "__main__":
    main()
