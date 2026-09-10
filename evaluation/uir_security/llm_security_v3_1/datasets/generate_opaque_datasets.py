"""Generate Opaque Benchmark Datasets for HETE V3.1.

Mandates:
- Strictly maps original case IDs to deterministic opaque identifiers (c_<hex16>)
- Strips any oracle or leaky fields from runtime dataset files
- Preserves 1:1 alignment between runtime and oracle datasets
- Calculates and writes frozen SHA-256 hashes in dataset_manifest_v3_1.json
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from evaluation.llm_security_v3_1.schema.oracle_case import OracleCase
from evaluation.llm_security_v3_1.schema.runtime_case import RuntimeCase

NAMESPACE_UIR = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def generate_opaque_id(split: str, original_id: str) -> str:
    """Generate deterministic opaque case ID without any semantic or class leakage."""
    digest = hashlib.sha256(f"{split}:{original_id}".encode("utf-8")).hexdigest()[:16]
    return f"c_{digest}"


def process_split(
    src_dir: Path,
    dst_dir: Path,
    split_name: str,
    src_custom_filename: str,
    src_oracle_filename: str,
) -> Dict[str, Any]:
    src_custom = src_dir / src_custom_filename
    src_oracle = src_dir / src_oracle_filename

    dst_custom = dst_dir / f"custom_{split_name}_v3_1.jsonl"
    dst_oracle = dst_dir / f"oracle_{split_name}_v3_1.jsonl"

    custom_lines = [json.loads(line) for line in src_custom.read_text(encoding="utf-8").splitlines() if line.strip()]
    oracle_lines = [json.loads(line) for line in src_oracle.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(custom_lines) == len(oracle_lines), f"Mismatch in {split_name}: {len(custom_lines)} vs {len(oracle_lines)}"

    out_runtime_records: List[Dict[str, Any]] = []
    out_oracle_records: List[Dict[str, Any]] = []

    for c_raw, o_raw in zip(custom_lines, oracle_lines):
        orig_id = c_raw["case_id"]
        opaque_id = generate_opaque_id(split_name, orig_id)

        # Build clean runtime case
        runtime_dict = {
            "case_id": opaque_id,
            "language": c_raw.get("language", "en"),
            "user_input": c_raw["user_input"],
            "retrieved_context": c_raw.get("retrieved_context", []),
            "principal_id": c_raw.get("principal_id", "finance_analyst_authenticated"),
            "environment_id": c_raw.get("environment_id", "enterprise_fin_prod"),
            "session_metadata": c_raw.get("session_metadata", {}),
        }
        # Validate schema
        r_case = RuntimeCase.from_dict(runtime_dict)
        out_runtime_records.append(r_case.to_dict())

        # Build oracle case
        o_dict = {
            "case_id": opaque_id,
            "original_case_id": orig_id,
            "attack_class": o_raw.get("attack_class", "valid_benign"),
            "is_attack": (o_raw.get("attack_class", "valid_benign") != "valid_benign"),
            "attack_goal": o_raw.get("attack_goal", {}),
            "forbidden_output_patterns": o_raw.get("forbidden_output_patterns", []),
            "target_entities": o_raw.get("target_entities", []),
            "expected_numeric_values": o_raw.get("expected_numeric_values", []),
            "admissible_evidence_ids": o_raw.get("admissible_evidence_ids", []),
            "expected_policy_outcome": o_raw.get("expected_policy_outcome", "ALLOW" if o_raw.get("attack_class") == "valid_benign" else "DENY"),
            "split": split_name,
        }
        ora_case = OracleCase.from_dict(o_dict)
        out_oracle_records.append(ora_case.to_dict())

    # Write out JSONL
    with open(dst_custom, "w", encoding="utf-8") as f:
        for rec in out_runtime_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(dst_oracle, "w", encoding="utf-8") as f:
        for rec in out_oracle_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    custom_sha = hashlib.sha256(dst_custom.read_bytes()).hexdigest()
    oracle_sha = hashlib.sha256(dst_oracle.read_bytes()).hexdigest()

    return {
        "split": split_name,
        "total_cases": len(out_runtime_records),
        "runtime_file": dst_custom.name,
        "runtime_sha256": custom_sha,
        "oracle_file": dst_oracle.name,
        "oracle_sha256": oracle_sha,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    src_dir = root / "evaluation" / "llm_security_v3" / "datasets"
    dst_dir = root / "evaluation" / "llm_security_v3_1" / "datasets"
    dst_dir.mkdir(parents=True, exist_ok=True)

    manifest_data = {
        "benchmark_version": "v3.1_frozen_publication",
        "description": "HETE Enterprise Security Benchmark v3.1 with Opaque Identifiers and Field Allow-List Enforcement",
        "splits": {},
    }

    # Held-out split (850)
    manifest_data["splits"]["heldout"] = process_split(
        src_dir, dst_dir, "heldout", "custom_heldout_v3.jsonl", "oracle_heldout_v3.jsonl"
    )

    # Validation split (350)
    manifest_data["splits"]["validation"] = process_split(
        src_dir, dst_dir, "validation", "custom_validation_v3.jsonl", "oracle_validation_v3.jsonl"
    )

    # Dev split (1400)
    manifest_data["splits"]["dev"] = process_split(
        src_dir, dst_dir, "dev", "custom_dev_v3.jsonl", "oracle_dev_v3.jsonl"
    )

    manifest_file = dst_dir / "dataset_manifest_v3_1.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"Generated datasets and manifest at {manifest_file}:")
    print(json.dumps(manifest_data, indent=2))


if __name__ == "__main__":
    main()
