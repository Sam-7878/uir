#!/usr/bin/env python3
"""100-case golden validation for exact claim and field-level metrics."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "uir_phase3" / "claim_metric_validation.csv"
FIXTURES = ROOT / "evaluation" / "uir_generalization" / "fixtures" / "claim_metric_golden.jsonl"
FIELDS = ("claim_type", "entity_id", "attribute", "value", "unit", "period", "provenance")
TYPES = ("entity_claim", "attribute_claim", "numeric_claim", "relation_claim", "temporal_claim", "provenance_claim")

def normalized(claim: dict) -> tuple[str, ...]: return tuple(str(claim.get(k, "")).strip().casefold() for k in FIELDS)

def score(expected: list[dict], actual: list[dict]) -> tuple[float, float, float, float]:
    exp, act = {normalized(x) for x in expected}, {normalized(x) for x in actual}
    exact = len(exp & act)
    ep = exact / len(act) if act else float(not exp); er = exact / len(exp) if exp else float(not act)
    exp_fields = {(i, k, str(c.get(k, "")).strip().casefold()) for i, c in enumerate(expected) for k in FIELDS}
    act_fields = {(i, k, str(c.get(k, "")).strip().casefold()) for i, c in enumerate(actual) for k in FIELDS}
    matched = len(exp_fields & act_fields)
    fp = matched / len(act_fields) if act_fields else float(not exp_fields)
    fr = matched / len(exp_fields) if exp_fields else float(not act_fields)
    return ep, er, fp, fr

def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []; fixtures = []
    for i in range(100):
        expected = [{"claim_type": TYPES[i % 6], "entity_id": f"E{i}", "attribute": "revenue",
                     "value": str(i), "unit": "USD", "period": "2025", "provenance": f"src:{i}"}]
        actual = [dict(expected[0])]
        mutation = i % 5
        if mutation: actual[0][FIELDS[mutation + 1]] = f"wrong-{i}"
        observed = score(expected, actual)
        golden = (1.0, 1.0, 1.0, 1.0) if mutation == 0 else (0.0, 0.0, 6 / 7, 6 / 7)
        rows.append({"case_id": f"CM-{i:03d}", "claim_type": TYPES[i % 6], "mutation": mutation,
                     "claim_exact_precision": observed[0], "claim_exact_recall": observed[1],
                     "field_level_precision": observed[2], "field_level_recall": observed[3],
                     "golden_pass": all(abs(a-b) < 1e-12 for a,b in zip(observed, golden))})
        fixtures.append({"case_id": f"CM-{i:03d}", "expected": expected, "actual": actual,
                         "golden": {"claim_exact_precision": golden[0], "claim_exact_recall": golden[1],
                                    "field_level_precision": golden[2], "field_level_recall": golden[3]}})
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    FIXTURES.parent.mkdir(parents=True, exist_ok=True)
    FIXTURES.write_text("".join(__import__("json").dumps(x, sort_keys=True) + "\n" for x in fixtures), encoding="utf-8")
    if not all(row["golden_pass"] for row in rows): raise SystemExit("claim metric golden validation failed")

if __name__ == "__main__": main()
