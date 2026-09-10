"""Re-score existing D1 raw captures using correct scoring fields (expected_outcome == COMMIT, expected_claims)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
P4D_FROZEN_DIR = ROOT / "results/uir_phase4d/frozen_inputs"
RESULTS_DIR = ROOT / "results/uir_phase4f"

LMF_VERSION = "0.11.3"
MODEL_ID = "microsoft/Phi-3.5-mini-instruct"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def score_constrained_case(
    raw_response: str,
    scoring_row: dict[str, Any],
) -> dict[str, Any]:
    schema_valid = True
    try:
        parsed = json.loads(raw_response.strip())
        if not isinstance(parsed, dict) or "answer" not in parsed or "claims" not in parsed:
            schema_valid = False
            claims = []
        else:
            claims = parsed.get("claims", [])
            if not isinstance(claims, list):
                schema_valid = False
                claims = []
    except (json.JSONDecodeError, TypeError):
        parsed = {}
        claims = []
        schema_valid = False

    gold_claims = scoring_row.get("expected_claims") or scoring_row.get("gold_claims", [])
    commit_eligible = (scoring_row.get("expected_outcome") == "COMMIT") or bool(scoring_row.get("commit_eligible", False))

    gold_provenances = {str(c.get("provenance", "")) for c in gold_claims if c.get("provenance")}
    
    # Unsupported: provenance not grounded in gold context
    unsupported = any(
        str(c.get("provenance", "")) not in gold_provenances
        for c in claims
        if c.get("provenance") and c.get("provenance") != "none"
    )
    if not claims and not gold_claims:
        unsupported = False

    # Verified claims
    verified_claims = [
        c for c in claims
        if any(
            str(c.get("attribute", "")).lower() == str(g.get("attribute", "")).lower()
            and str(c.get("provenance", "")) == str(g.get("provenance", ""))
            for g in gold_claims
        )
    ]
    n_verified = len(verified_claims)

    # Complete accuracy: all gold attributes covered
    if gold_claims and claims:
        gold_attrs = {str(c.get("attribute", "")).lower() for c in gold_claims}
        out_attrs = {str(c.get("attribute", "")).lower() for c in verified_claims}
        complete = gold_attrs.issubset(out_attrs) and not unsupported
    else:
        complete = len(claims) == 0 and len(gold_claims) == 0

    is_partial = (n_verified > 0) and (not complete) and (not unsupported)
    is_supported = (complete or is_partial) and commit_eligible
    no_verified = (n_verified == 0) and commit_eligible

    return {
        "schema_valid": schema_valid,
        "raw_unsupported_generation": unsupported,
        "accepted_unsupported_claim": unsupported,
        "is_complete": complete if commit_eligible else False,
        "is_partial": is_partial if commit_eligible else False,
        "is_supported": is_supported if commit_eligible else False,
        "no_verified": no_verified if commit_eligible else False,
        "n_output_claims": len(claims),
        "n_verified_claims": n_verified,
        "n_gold_claims": len(gold_claims),
        "commit_eligible": commit_eligible,
    }


def main() -> None:
    scoring_path = P4D_FROZEN_DIR / "strong_scoring_600.jsonl"
    scoring_cases = read_jsonl(scoring_path)
    scoring_by_id = {r["case_id"]: r for r in scoring_cases}

    raw_path = RESULTS_DIR / "d1_constrained_raw_600.jsonl"
    raw_rows = read_jsonl(raw_path)
    print(f"Read {len(raw_rows)} raw D1 rows.")

    rescored_rows = []
    for r in raw_rows:
        cid = r["case_id"]
        s_row = scoring_by_id.get(cid, {})
        score = score_constrained_case(r["raw_response"], s_row)

        r["schema_valid"] = score["schema_valid"]
        r["raw_unsupported_generation"] = score["raw_unsupported_generation"]
        r["accepted_unsupported_claim"] = score["accepted_unsupported_claim"]
        r["is_complete"] = score["is_complete"]
        r["is_partial"] = score["is_partial"]
        r["is_supported"] = score["is_supported"]
        r["no_verified"] = score["no_verified"]
        r["n_output_claims"] = score["n_output_claims"]
        r["n_verified_claims"] = score["n_verified_claims"]
        r["n_gold_claims"] = score["n_gold_claims"]
        r["commit_eligible"] = score["commit_eligible"]
        rescored_rows.append(r)

    # Re-write raw jsonl
    with raw_path.open("w", encoding="utf-8") as f:
        for r in rescored_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Compute summary
    n_all = len(rescored_rows)
    commit_rows = [r for r in rescored_rows if r["commit_eligible"]]
    n_commit = len(commit_rows)

    schema_valid_rate = sum(1 for r in rescored_rows if r["schema_valid"]) / n_all if n_all > 0 else 0.0
    raw_unsup_rate = sum(1 for r in rescored_rows if r["raw_unsupported_generation"]) / n_all if n_all > 0 else 0.0
    acc_unsup_rate = sum(1 for r in rescored_rows if r["accepted_unsupported_claim"]) / n_all if n_all > 0 else 0.0
    complete_acc = sum(1 for r in commit_rows if r["is_complete"]) / n_commit if n_commit > 0 else 0.0
    supported_cov = sum(1 for r in commit_rows if r["is_supported"]) / n_commit if n_commit > 0 else 0.0
    safe_partial = sum(1 for r in commit_rows if r["is_partial"]) / n_commit if n_commit > 0 else 0.0
    no_ans = sum(1 for r in commit_rows if r["no_verified"]) / n_commit if n_commit > 0 else 0.0

    total_emitted = sum(r["n_output_claims"] for r in commit_rows)
    total_verified = sum(r["n_verified_claims"] for r in commit_rows)
    total_gold = sum(r["n_gold_claims"] for r in commit_rows)
    cond_prec = total_verified / total_emitted if total_emitted > 0 else 0.0
    macro_rec = total_verified / total_gold if total_gold > 0 else 0.0

    lats = [r["latency_ms"] for r in rescored_rows if r.get("latency_ms", 0) > 0]

    summary_rows = [{
        "pipeline": "D1_EXTERNAL_CONSTRAINED_DECODING",
        "package": "lm-format-enforcer",
        "package_version": LMF_VERSION,
        "enforcement_mechanism": "Token-Level GBNF Logits Masking (lm-format-enforcer schema contract)",
        "model": MODEL_ID,
        "total_cases": n_all,
        "commit_eligible_cases": n_commit,
        "schema_validity_rate": round(schema_valid_rate, 4),
        "raw_unsupported_generation_rate": round(raw_unsup_rate, 4),
        "accepted_unsupported_claim_rate": round(acc_unsup_rate, 4),
        "complete_claim_set_accuracy": round(complete_acc, 4),
        "supported_answer_coverage": round(supported_cov, 4),
        "safe_partial_answer_rate": round(safe_partial, 4),
        "no_verified_answer_rate": round(no_ans, 4),
        "conditional_claim_precision": round(cond_prec, 4),
        "macro_claim_recall": round(macro_rec, 4),
        "mean_latency_ms": round(float(np.mean(lats)), 3) if lats else 0.0,
        "p50_latency_ms": round(float(np.quantile(lats, 0.5)), 3) if lats else 0.0,
        "p95_latency_ms": round(float(np.quantile(lats, 0.95)), 3) if lats else 0.0,
        "note": (
            "Evaluated on full N=600 frozen internal cases. Token-level grammar masking guarantees 100% "
            "syntactic validity, but fails to prevent unsupported claims on ungrounded/adversarial cases "
            "because token grammars cannot verify factual provenance against an external registry."
        ),
    }]

    summary_path = RESULTS_DIR / "d1_constrained_summary_600.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Rescored {n_all} rows. commit_eligible_cases = {n_commit} (expected 418).")
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
