#!/usr/bin/env python3
"""Validate role-separated AntiGravity audit packets, captures, and review rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKETS = ROOT / "evaluation/uir_phase3d/audit_packets"
WORK = ROOT / "results/uir_phase3d/actual_ai_work"
OUT = ROOT / "results/uir_phase3d/role_separated_validation.json"
EXPECTED_PROMPT_HASH = "1660e3f70d9c11b0b415a7adb3c4bcc01dd1b8c9576af19c8881335336198310"
EXPECTED_FROZEN_HASH = "9bb8a5d423b53bae14b2c699cba6b1338f0115345f94c6b4a9f93af2400d4a3c"
EXPECTED_PARSER_HASH = "bee778f3e3767fdcd64d0926f27c680143d217ea1d6febcabd08aac96de321d7"
EXPECTED = {
    "AI-R1": ("AntiGravity Gemini 3.5 Flash", "gemini-3.5-flash"),
    "AI-R2": ("AntiGravity Gemini 3.6 Flash", "gemini-3.6-flash-high"),
    "AI-R3": ("AntiGravity Gemini 3.1 Pro", "gemini-3.1-pro"),
}
FIELDS = (
    "source_text_valid", "language_valid", "intent_valid", "target_valid",
    "conditions_valid", "policy_valid", "outcome_valid", "claims_valid",
)
RECONSTRUCTED_FIELDS = (
    "intent", "target", "conditions", "policy_decision", "expected_outcome",
    "required_claims",
)
ALLOWED = {"1", "0", "NA"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def parse_model_payload(outer: dict) -> dict:
    structured = outer.get("structured_output")
    if isinstance(structured, dict):
        return structured
    response = outer.get("response")
    if isinstance(response, dict):
        return response
    return json.loads(str(response).strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    for reviewer in EXPECTED:
        parser.add_argument(
            f"--{reviewer.lower().replace('-', '')}", type=Path,
            default=WORK / f"actual_ai_review_{reviewer[-2:]}.jsonl",
        )
    args = parser.parse_args()
    review_paths = {"AI-R1": args.air1, "AI-R2": args.air2, "AI-R3": args.air3}
    failures: list[dict] = []
    warnings: list[dict] = []
    capture_lookup: dict[tuple[str, str], dict] = {}

    def fail(check: str, detail: str, case_id: str | None = None) -> None:
        failures.append({"check": check, "case_id": case_id, "detail": detail})

    def warn(check: str, detail: str) -> None:
        warnings.append({"check": check, "detail": detail})

    manifest_path = PACKETS / "AUDIT_PACKET_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("case_count") != 1200:
        fail("packet_manifest", f"case_count={manifest.get('case_count')}, expected=1200")
    if manifest.get("prompt_template_sha256") != EXPECTED_PROMPT_HASH:
        fail("packet_manifest", "prompt-template hash mismatch")
    if manifest.get("candidate_sha256") != EXPECTED_FROZEN_HASH:
        fail("packet_manifest", "frozen-v2 identity mismatch")
    if not manifest.get("contexts_isolated"):
        fail("packet_manifest", "contexts_isolated is not true")

    frozen_path = ROOT / "results/uir_phase3b/frozen_test_v2.jsonl"
    frozen_manifest = json.loads(
        (ROOT / "results/uir_phase3b/FROZEN_TEST_V2_MANIFEST.json").read_text(encoding="utf-8")
    )
    actual_frozen_hash = digest_file(frozen_path)
    if actual_frozen_hash != EXPECTED_FROZEN_HASH:
        fail("frozen_v2_integrity", f"actual SHA-256={actual_frozen_hash}")
    if frozen_manifest.get("dataset_sha256") != EXPECTED_FROZEN_HASH:
        fail("frozen_v2_integrity", "manifest dataset SHA-256 mismatch")
    if frozen_manifest.get("parser_source_sha256") != EXPECTED_PARSER_HASH:
        fail("parser_integrity", "frozen manifest parser SHA-256 mismatch")

    packet_rows: dict[str, list[dict]] = {}
    packet_ids: dict[str, list[str]] = {}
    packet_hashes: dict[str, str] = {}
    packet_allowed_top = {
        "annotation_guideline", "audit_input", "case_id", "engine",
        "prompt_template_sha256", "response_schema", "reviewer_id",
    }
    audit_input_allowed = {
        "case_id", "expected_claims", "expected_conditions", "expected_outcome",
        "expected_policy_decision", "expected_semantics", "language", "source_text",
        "verified_facts",
    }
    for reviewer, (expected_engine, _) in EXPECTED.items():
        path = PACKETS / f"audit_input_{reviewer}.jsonl"
        rows = read_jsonl(path)
        packet_rows[reviewer] = rows
        packet_hashes[reviewer] = digest_file(path)
        ids = [row.get("case_id") for row in rows]
        packet_ids[reviewer] = ids
        if len(rows) != 1200:
            fail("packet_coverage", f"{reviewer}: rows={len(rows)}, expected=1200")
        duplicates = [case for case, count in Counter(ids).items() if count > 1]
        if duplicates:
            fail("packet_coverage", f"{reviewer}: duplicate IDs={duplicates[:10]}")
        for row in rows:
            case_id = row.get("case_id")
            if set(row) - packet_allowed_top:
                fail("packet_forbidden_content", f"unexpected top-level keys={sorted(set(row)-packet_allowed_top)}", case_id)
            audit_input = row.get("audit_input", {})
            if set(audit_input) - audit_input_allowed:
                fail("packet_forbidden_content", f"unexpected audit_input keys={sorted(set(audit_input)-audit_input_allowed)}", case_id)
            if row.get("reviewer_id") != reviewer:
                fail("packet_identity", f"reviewer_id={row.get('reviewer_id')}", case_id)
            if row.get("prompt_template_sha256") != EXPECTED_PROMPT_HASH:
                fail("packet_prompt_hash", "mismatch", case_id)
            if audit_input.get("case_id") != case_id:
                fail("packet_case_identity", "nested case ID mismatch", case_id)
        packet_engines = {row.get("engine") for row in rows}
        if packet_engines != {expected_engine}:
            warn(
                "legacy_packet_engine_metadata",
                f"{reviewer}: packet engine={sorted(str(x) for x in packet_engines)}, actual role={expected_engine}; "
                "the original packets are retained for hash reproducibility",
            )

    reference_ids = set(packet_ids["AI-R1"])
    for reviewer in EXPECTED:
        if set(packet_ids[reviewer]) != reference_ids:
            fail("packet_shared_case_set", f"{reviewer}: case-ID set differs from AI-R1")

    review_summary: dict[str, dict] = {}
    all_sessions: dict[str, str] = {}
    for reviewer, (engine, model_selector) in EXPECTED.items():
        path = review_paths[reviewer]
        rows = read_jsonl(path)
        indexed: dict[str, dict] = {}
        raw_dir = WORK / f"raw_{reviewer[-2:]}"
        captures = sorted(raw_dir.glob("*.json"))
        capture_cases: set[str] = set()
        verified_batches = 0
        for capture_path in captures:
            try:
                capture = json.loads(capture_path.read_text(encoding="utf-8"))
                outer = capture["stdout_object"]
                raw_response = outer.get("response", "")
                raw_hash = digest_bytes(str(raw_response).encode("utf-8"))
                if capture.get("reviewer_id") != reviewer or capture.get("engine") != engine:
                    fail("raw_capture_identity", capture_path.name)
                if capture.get("model_selector") != model_selector:
                    fail("raw_capture_model_selector", capture_path.name)
                if outer.get("status") != "SUCCESS" or capture.get("returncode") != 0:
                    fail("raw_capture_status", capture_path.name)
                if capture.get("raw_response_sha256") != raw_hash:
                    fail("raw_capture_hash", capture_path.name)
                if not isinstance(outer.get("structured_output"), dict):
                    fail("raw_structured_output", f"missing schema-validated output: {capture_path.name}")
                judgments = parse_model_payload(outer).get("judgments")
                if not isinstance(judgments, list):
                    raise ValueError("judgments is not a list")
                by_id = {row.get("case_id"): row for row in judgments}
                case_ids = capture.get("case_ids", [])
                if len(by_id) != len(judgments) or set(by_id) != set(case_ids):
                    fail("raw_capture_coverage", capture_path.name)
                for case_id in case_ids:
                    if case_id in capture_cases:
                        fail("raw_capture_duplicate_case", capture_path.name, case_id)
                    capture_cases.add(case_id)
                session_id = outer.get("conversation_id")
                if not session_id:
                    fail("raw_capture_session", capture_path.name)
                elif session_id in all_sessions:
                    fail("session_isolation", f"session reused by {all_sessions[session_id]} and {reviewer}")
                else:
                    all_sessions[session_id] = reviewer
                capture["_judgments_by_id"] = by_id
                capture["_verified_raw_hash"] = raw_hash
                capture["_session_id"] = session_id
                verified_batches += 1
                for case_id in case_ids:
                    capture_lookup[(reviewer, case_id)] = capture
            except Exception as exc:
                fail("raw_capture_parse", f"{capture_path.name}: {type(exc).__name__}: {exc}")

        ids = [row.get("case_id") for row in rows]
        if len(rows) != 1200:
            fail("review_coverage", f"{reviewer}: rows={len(rows)}, expected=1200")
        if set(ids) != reference_ids:
            missing = sorted(reference_ids - set(ids))[:10]
            unknown = sorted(set(ids) - reference_ids)[:10]
            fail("review_coverage", f"{reviewer}: missing={missing}, unknown={unknown}")
        if len(set(ids)) != len(ids):
            fail("review_coverage", f"{reviewer}: duplicate case IDs")
        if capture_cases != reference_ids:
            fail("raw_capture_coverage", f"{reviewer}: captured={len(capture_cases)}, expected=1200")

        for row in rows:
            case_id = row.get("case_id")
            if case_id in indexed:
                continue
            indexed[case_id] = row
            if row.get("reviewer_id") != reviewer or row.get("engine") != engine:
                fail("review_identity", f"got {row.get('reviewer_id')} / {row.get('engine')}", case_id)
            if row.get("prompt_template_sha256") != EXPECTED_PROMPT_HASH:
                fail("review_prompt_hash", "mismatch", case_id)
            provenance = row.get("provenance", {})
            required = (
                "session_run_id", "timestamp", "generation_interface", "raw_response_sha256",
                "temperature", "annotation_method", "model_selector",
            )
            missing = [key for key in required if provenance.get(key) in (None, "")]
            if missing:
                fail("review_provenance", f"missing={missing}", case_id)
            if provenance.get("temperature") != "not_exposed_by_antigravity_cli":
                fail("review_temperature", f"got={provenance.get('temperature')}", case_id)
            if provenance.get("annotation_method") != "actual_model_generation":
                fail("review_annotation_method", f"got={provenance.get('annotation_method')}", case_id)
            if provenance.get("model_selector") != model_selector:
                fail("review_model_selector", f"got={provenance.get('model_selector')}", case_id)
            if not SHA256_RE.fullmatch(str(provenance.get("raw_response_sha256", ""))):
                fail("review_raw_hash_format", "not a SHA-256 hex digest", case_id)
            try:
                datetime.fromisoformat(str(provenance.get("timestamp")))
            except ValueError:
                fail("review_timestamp", f"invalid={provenance.get('timestamp')}", case_id)
            if provenance.get("audit_packet_sha256") not in (None, packet_hashes[reviewer]):
                fail("review_packet_hash", f"got={provenance.get('audit_packet_sha256')}", case_id)
            judgment = row.get("judgment", {})
            if judgment.get("case_id") != case_id:
                fail("judgment_case_identity", f"nested={judgment.get('case_id')}", case_id)
            invalid = {field: judgment.get(field) for field in FIELDS if str(judgment.get(field, "")).upper() not in ALLOWED}
            if invalid:
                fail("judgment_schema", f"invalid fields={invalid}", case_id)
            reconstructed = judgment.get("reconstructed")
            if not isinstance(reconstructed, dict):
                fail("judgment_reconstruction", "not an object", case_id)
            else:
                absent = [field for field in RECONSTRUCTED_FIELDS if field not in reconstructed]
                if absent:
                    fail("judgment_reconstruction", f"missing={absent}", case_id)
            if not str(judgment.get("reasoning_summary", "")).strip():
                fail("judgment_rationale", "empty", case_id)
            capture = capture_lookup.get((reviewer, case_id))
            if capture:
                if provenance.get("session_run_id") != capture["_session_id"]:
                    fail("row_capture_session", "session mismatch", case_id)
                if provenance.get("raw_response_sha256") != capture["_verified_raw_hash"]:
                    fail("row_capture_hash", "hash mismatch", case_id)
                if judgment != capture["_judgments_by_id"].get(case_id):
                    fail("row_capture_judgment", "JSONL judgment differs from captured model output", case_id)

        review_summary[reviewer] = {
            "engine": engine,
            "model_selector": model_selector,
            "rows": len(rows),
            "unique_case_ids": len(set(ids)),
            "raw_batches": len(captures),
            "verified_raw_batches": verified_batches,
            "review_file_sha256": digest_file(path),
            "audit_packet_sha256": packet_hashes[reviewer],
        }

    result = {
        "status": "PASS" if not failures else "FAIL",
        "role_separated_actual_model_audit_valid": not failures,
        "prompt_template_sha256": EXPECTED_PROMPT_HASH,
        "frozen_v2_sha256": actual_frozen_hash,
        "parser_sha256": frozen_manifest.get("parser_source_sha256"),
        "shared_case_count": len(reference_ids),
        "reviewers": review_summary,
        "unique_session_count": len(all_sessions),
        "failures": failures,
        "warnings": warnings,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 2

if __name__ == "__main__":
    raise SystemExit(main())
