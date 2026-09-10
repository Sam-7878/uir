#!/usr/bin/env python3
"""Validate independent human reviews; fail closed until genuinely complete."""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "evaluation" / "uir_generalization" / "candidate"
MANIFEST = ROOT / "results" / "uir_phase3" / "frozen_v2_manifest.json"
FIELDS = ["source_text_valid", "language_valid", "intent_valid", "target_valid", "conditions_valid",
          "policy_valid", "outcome_valid", "claims_valid"]

def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))

def main() -> int:
    reviews = [read(CANDIDATE / f"review_R{i}.csv") for i in (1, 2)]
    complete = all(row[field].strip().lower() in {"true", "false"} for rows in reviews for row in rows for field in FIELDS)
    adjudication = read(CANDIDATE / "adjudication.csv")
    if not complete:
        print("BLOCKED: two independent human review sheets are incomplete", file=sys.stderr); return 2
    labels = [[all(row[f].lower() == "true" for f in FIELDS) for row in rows] for rows in reviews]
    observed = sum(a == b for a, b in zip(*labels)) / len(labels[0])
    pa = sum(labels[0]) / len(labels[0]); pb = sum(labels[1]) / len(labels[1])
    expected = pa * pb + (1 - pa) * (1 - pb)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    disagreements = [reviews[0][i]["case_id"] for i, (a, b) in enumerate(zip(*labels)) if a != b]
    adjudicated_ids = {row["case_id"] for row in adjudication if row.get("adjudicated_valid", "").lower() in {"true", "false"}}
    if not set(disagreements) <= adjudicated_ids:
        print("BLOCKED: review disagreements require adjudication", file=sys.stderr); return 3
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest.update(human_review_status="completed", reviewer_count=2, agreement={"cohens_kappa": kappa},
                    adjudicated=True, frozen=True, artifact_state="frozen_after_human_review", publication_ready=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__": raise SystemExit(main())
