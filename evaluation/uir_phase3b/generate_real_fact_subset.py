#!/usr/bin/env python3
"""Create a 200-case KO/EN factual subset from the frozen SEC registry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def claims(fact: dict, provenance: str) -> list[dict]:
    common = {"entity_id": fact["entity_id"], "unit": "", "period": "", "provenance": provenance}
    return [
        {**common, "claim_type": "entity_claim", "attribute": "entity_name", "value": fact["entity_name"]},
        {**common, "claim_type": "attribute_claim", "attribute": "available_attribute", "value": fact["attribute"]},
        {"claim_type": "numeric_claim", "entity_id": fact["entity_id"], "attribute": fact["attribute"],
         "value": fact["value"], "unit": fact["unit"], "period": fact["period"], "provenance": provenance},
        {**common, "claim_type": "relation_claim", "attribute": "has_attribute", "value": fact["attribute"]},
        {"claim_type": "temporal_claim", "entity_id": fact["entity_id"], "attribute": fact["attribute"],
         "value": fact["period"], "unit": "", "period": fact["period"], "provenance": provenance},
        {"claim_type": "provenance_claim", "entity_id": fact["entity_id"], "attribute": fact["attribute"],
         "value": provenance, "unit": "", "period": fact["period"], "provenance": provenance},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=ROOT / "evaluation/uir_external/registry_v1.jsonl")
    parser.add_argument("--registry-manifest", type=Path, default=ROOT / "evaluation/uir_external/REGISTRY_MANIFEST.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results/uir_phase3b")
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    facts = [json.loads(x) for x in args.registry.read_text(encoding="utf-8").splitlines() if x][:100]
    if len(facts) < 100: raise SystemExit("at least 100 frozen SEC facts are required")
    rows = []
    for index, fact in enumerate(facts):
        source = fact["provenance"]
        provenance = f"sec-companyfacts://{fact['entity_id']}/{fact['attribute']}/{fact['period']}/{source['record_id']}#sha256={source['source_hash']}"
        expected = claims(fact, provenance)
        for language in ("ko", "en"):
            text = (f"SEC 출처에 근거해 {fact['entity_id']}의 {fact['period']}년 {fact['attribute']} 수치를 검증해 주세요"
                    if language == "ko" else
                    f"Verify the {fact['period']} {fact['attribute']} value for {fact['entity_id']} using the SEC source")
            rows.append({"case_id": f"SEC3B-{index:03d}-{language.upper()}", "suite": "real_fact", "language": language,
                         "category": "numeric_provenance", "split": "real_world_sec", "input": text,
                         "expected_semantics": {"intent": "VERIFY", "target": fact["entity_id"], "action": "verify_fact",
                                                "metric": fact["attribute"], "period": fact["period"]},
                         "expected_claims": expected, "context_claims": expected, "verified_facts": [fact],
                         "expected_outcome": "COMMIT", "expected_policy_decision": "PERMIT",
                         "entity_valid": True, "policy_valid": True, "uir_ready": True,
                         "source_record_id": source["record_id"], "source_snapshot_hash": source["source_hash"],
                         "registry_snapshot_hash": json.loads(args.registry_manifest.read_text())["sha256"]})
    content = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in rows).encode()
    (args.out / "real_fact_subset.jsonl").write_bytes(content)
    registry_manifest = json.loads(args.registry_manifest.read_text(encoding="utf-8"))
    manifest = {"status": "complete", "source": "U.S. SEC XBRL Companyfacts API frozen Phase-2 snapshot",
                "case_count": 200, "language_counts": {"ko": 100, "en": 100}, "unique_source_facts": 100,
                "dataset_sha256": hashlib.sha256(content).hexdigest(), "registry_sha256": registry_manifest["sha256"],
                "registry_snapshot_date": registry_manifest["snapshot_date"], "provenance_scheme": "sec-companyfacts://...#sha256=...",
                "semantic_primary_dataset": False, "purpose": ["factual_grounding", "numeric_fidelity", "provenance_correctness"]}
    (args.out / "real_fact_subset_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
