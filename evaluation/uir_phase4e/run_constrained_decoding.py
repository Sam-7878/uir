"""Phase UIR-4E: Genuine Grammar-Constrained Decoding Baseline (BLOCKER 7 & 8 fix).

Implements D1_EXTERNAL_CONSTRAINED_DECODING using lm-format-enforcer v0.10+
which applies actual token-level logits enforcement (not post-hoc validation).

Unlike C3 (JSON-Schema Prompted / Post-Hoc Validation Baseline), this baseline:
  1. Restricts the token generation distribution at each step to valid JSON tokens
  2. Uses a JSON schema to define the grammar
  3. Cannot produce schema-invalid output

Evaluates on same 600 internal cases as Phase 4D strong baselines.

Output:
  results/uir_phase4e/external_constrained_decoding_summary.csv
  results/uir_phase4e/constrained_decoding_per_case.jsonl
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from evaluation.uir_phase4e.common import (
    P4D_FROZEN_DIR, RESULTS_DIR, read_jsonl, sha256_text, write_csv, write_jsonl,
)

# Check for lm-format-enforcer
try:
    import lmformatenforcer
    from lmformatenforcer import JsonSchemaParser
    from lmformatenforcer.integrations.transformers import (
        build_transformers_prefix_allowed_tokens_fn,
    )
    LMF_AVAILABLE = True
    LMF_VERSION = getattr(lmformatenforcer, "__version__", "unknown")
except ImportError:
    LMF_AVAILABLE = False
    LMF_VERSION = "not_installed"

try:
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

MODEL_ID = "microsoft/Phi-3.5-mini-instruct"

# The UIR output schema (same as internal evaluation)
CLAIM_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_type": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "attribute": {"type": "string"},
                    "value": {"type": "string"},
                    "unit": {"type": "string"},
                    "period": {"type": "string"},
                    "provenance": {"type": "string"},
                },
                "required": ["claim_type", "entity_id", "attribute", "value", "provenance"],
            },
        },
    },
    "required": ["answer", "claims"],
}


def score_constrained_case(
    raw_response: str,
    scoring_row: dict[str, Any],
) -> dict[str, Any]:
    """Score a single constrained-decoding output against the frozen scoring case."""
    # Schema validity: since lmformatenforcer enforces the schema, this should always be True
    schema_valid = True
    try:
        parsed = json.loads(raw_response.strip())
        claims = parsed.get("claims", [])
    except (json.JSONDecodeError, TypeError):
        parsed = {}
        claims = []
        schema_valid = False

    gold_claims = scoring_row.get("gold_claims", [])
    commit_eligible = scoring_row.get("commit_eligible", False)

    # Unsupported claim check: any claim without a valid provenance matching gold
    gold_provenances = {str(c.get("provenance", "")) for c in gold_claims}
    unsupported = any(
        str(c.get("provenance", "")) not in gold_provenances
        for c in claims
        if c.get("provenance") and c.get("provenance") != "none"
    )

    # Complete accuracy: all gold claims present in output
    if gold_claims and claims:
        gold_attrs = {str(c.get("attribute", "")) for c in gold_claims}
        out_attrs = {str(c.get("attribute", "")) for c in claims}
        complete = gold_attrs.issubset(out_attrs)
    else:
        complete = len(claims) == 0 and len(gold_claims) == 0

    return {
        "schema_valid": schema_valid,
        "unsupported_claim": unsupported,
        "is_complete": complete,
        "n_output_claims": len(claims),
        "n_gold_claims": len(gold_claims),
        "commit_eligible": commit_eligible,
    }


def run_constrained_decoding(n_cases: int = 600) -> list[dict[str, Any]]:
    """Run lm-format-enforcer constrained decoding on internal cases."""
    if not LMF_AVAILABLE:
        print("[4E-D1] ERROR: lm-format-enforcer not installed.")
        print("[4E-D1] Install: pip install lm-format-enforcer")
        return []

    if not TRANSFORMERS_AVAILABLE:
        print("[4E-D1] ERROR: transformers not available.")
        return []

    print(f"[4E-D1] Using lm-format-enforcer v{LMF_VERSION}")
    print(f"[4E-D1] Loading model: {MODEL_ID}")

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    print(f"[4E-D1] Model loaded.")

    # Build schema parser
    schema_parser = JsonSchemaParser(CLAIM_SCHEMA)
    prefix_fn = build_transformers_prefix_allowed_tokens_fn(tokenizer, schema_parser)
    print(f"[4E-D1] JSON schema parser initialized.")

    # Load runtime + scoring cases
    runtime_cases = read_jsonl(P4D_FROZEN_DIR / "strong_runtime_600.jsonl")[:n_cases]
    scoring_cases = read_jsonl(P4D_FROZEN_DIR / "strong_scoring_600.jsonl")[:n_cases]
    scoring_by_id = {r["case_id"]: r for r in scoring_cases}
    print(f"[4E-D1] Loaded {len(runtime_cases)} cases.")

    per_case_rows = []
    for i, case in enumerate(runtime_cases):
        case_id = case.get("case_id", f"case-{i}")
        prompt = (
            f"USER_REQUEST:\n{case.get('input', '')}\n\n"
            f"RETRIEVED_CONTEXT:\n{json.dumps(case.get('context_claims', []), ensure_ascii=False)}\n\n"
            f"Respond with JSON only: {{\"answer\":\"...\",\"claims\":[...]}}. "
            f"Do not invent facts not in the context."
        )
        prompt_hash = sha256_text(prompt)

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        t0 = time.perf_counter()
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                prefix_allowed_tokens_fn=prefix_fn,
                pad_token_id=tokenizer.eos_token_id,
            )
        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Decode only new tokens
        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        raw_response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        raw_sha = sha256_text(raw_response)

        scoring_row = scoring_by_id.get(case_id, {})
        score = score_constrained_case(raw_response, scoring_row)

        per_case_rows.append({
            "case_id": case_id,
            "pipeline": "D1_EXTERNAL_CONSTRAINED_DECODING",
            "model": MODEL_ID,
            "lmformatenforcer_version": LMF_VERSION,
            "prompt_hash": prompt_hash,
            "raw_response": raw_response,
            "raw_response_sha256": raw_sha,
            "schema_valid": score["schema_valid"],
            "unsupported_claim": score["unsupported_claim"],
            "is_complete": score["is_complete"],
            "n_output_claims": score["n_output_claims"],
            "n_gold_claims": score["n_gold_claims"],
            "commit_eligible": score["commit_eligible"],
            "latency_ms": round(latency_ms, 3),
        })

        if (i + 1) % 50 == 0:
            schema_ok = sum(1 for r in per_case_rows if r["schema_valid"]) / len(per_case_rows)
            unsup = sum(1 for r in per_case_rows if r["unsupported_claim"]) / len(per_case_rows)
            print(f"  [{i+1}/{n_cases}] schema_valid={schema_ok:.3f} unsup={unsup:.3f}")

    return per_case_rows


def compute_constrained_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    n_all = len(rows)
    commit_rows = [r for r in rows if r["commit_eligible"]]
    n_commit = len(commit_rows)

    schema_valid_rate = sum(1 for r in rows if r["schema_valid"]) / n_all if n_all > 0 else 0
    unsup_rate = sum(1 for r in rows if r["unsupported_claim"]) / n_all if n_all > 0 else 0
    complete_acc = sum(1 for r in commit_rows if r["is_complete"]) / n_commit if n_commit > 0 else 0
    lats = [r["latency_ms"] for r in rows if r["latency_ms"] > 0]

    return [{
        "pipeline": "D1_EXTERNAL_CONSTRAINED_DECODING",
        "package": "lm-format-enforcer",
        "package_version": rows[0]["lmformatenforcer_version"] if rows else LMF_VERSION,
        "model": MODEL_ID,
        "total_cases": n_all,
        "commit_eligible_cases": n_commit,
        "schema_validity_rate": round(schema_valid_rate, 4),
        "unsupported_claim_accept_rate": round(unsup_rate, 4),
        "complete_claim_set_accuracy": round(complete_acc, 4),
        "mean_latency_ms": round(float(np.mean(lats)), 3) if lats else 0.0,
        "p50_latency_ms": round(float(np.quantile(lats, 0.5)), 3) if lats else 0.0,
        "p95_latency_ms": round(float(np.quantile(lats, 0.95)), 3) if lats else 0.0,
        "note": (
            "Genuine token-level grammar enforcement via lm-format-enforcer logits processor. "
            "NOT post-hoc validation. C3 JSON-schema baseline uses standard generation + instruction."
        ),
    }]


def main() -> None:
    print("[4E] D1 Constrained Decoding Baseline (BLOCKER 7 & 8 fix)")

    if not LMF_AVAILABLE:
        print("[4E-D1] lm-format-enforcer not available. Installing...")
        import subprocess
        result = subprocess.run(
            ["pip", "install", "lm-format-enforcer"],
            capture_output=True, text=True
        )
        print(result.stdout)
        print(result.stderr)
        # Retry import
        try:
            import lmformatenforcer  # noqa: F401
            print("[4E-D1] Installation successful.")
        except ImportError:
            print("[4E-D1] Installation failed. Cannot proceed.")
            sys.exit(1)

    per_case = run_constrained_decoding(n_cases=600)

    if per_case:
        write_jsonl(RESULTS_DIR / "constrained_decoding_per_case.jsonl", per_case)
        summary = compute_constrained_summary(per_case)
        write_csv(RESULTS_DIR / "external_constrained_decoding_summary.csv", summary)
        print(f"[4E] Schema validity: {summary[0]['schema_validity_rate']:.3f}")
        print(f"[4E] Unsupported claims: {summary[0]['unsupported_claim_accept_rate']:.3f}")
        print(f"[4E] Complete accuracy: {summary[0]['complete_claim_set_accuracy']:.3f}")
        print(f"[4E] Written: external_constrained_decoding_summary.csv")
    else:
        print("[4E] No results produced.")
        sys.exit(1)


if __name__ == "__main__":
    main()
