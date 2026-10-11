"""Record an unscored exact-case diagnostic after a fail-closed Phi interruption."""
from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
import sys

import requests

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from evaluation.llm_security_v3_2.closure_campaign import Campaign, write
from evaluation.llm_security_v3_2.schema.oracle_case import OracleCase
from evaluation.llm_security_v3_2.schema.runtime_case import RuntimeCase


OUT = REPO / "results/llm_security_v3_2_closure"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--failure", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    failure = json.loads(args.failure.read_text())
    case_id = failure["case_id"]
    completed = int(failure["completed_rows"])

    session = requests.Session()
    session.trust_env = False
    response = session.post(
        args.endpoint + "/api/generate",
        json={"model": "phi3.5:latest", "keep_alive": 0},
        timeout=180,
    )
    unload = {
        "status_code": response.status_code,
        "response": response.json() if response.content else None,
    }

    runtime = [
        RuntimeCase.from_dict(item)
        for item in json.loads((OUT / "datasets/runtime.json").read_text())
    ]
    oracles = [
        OracleCase.from_dict(item)
        for item in json.loads((OUT / "datasets/oracle.json").read_text())
    ]
    runtime_case = next(item for item in runtime if item.case_id == case_id)
    oracle_case = next(item for item in oracles if item.case_id == case_id)

    campaign = Campaign(OUT, args.endpoint)
    campaign.load_model("phi3.5:latest")
    result = {
        "purpose": "Unscored exact-case diagnostic after fail-closed Phi response; excluded from all denominators",
        "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "failure": failure,
        "unload": unload,
        "case_id": case_id,
    }
    try:
        result["row"] = campaign.execute(runtime_case, oracle_case, "HETE")
        result["diagnostic_complete"] = True
    except Exception as error:
        result["diagnostic_complete"] = False
        result["error"] = repr(error)
        result["captured_calls"] = campaign.backend.calls if campaign.backend else []

    output = OUT / "operational_failures" / f"backend_failure_diagnostic_phi_after_{completed}_rows_recovery.json"
    write(output, result)
    calls = result.get("row", {}).get("calls", result.get("captured_calls", []))
    raw = calls[0].get("response", {}) if calls else {}
    print(json.dumps({
        "case_id": case_id,
        "completed_rows": completed,
        "unload_done": (unload["response"] or {}).get("done"),
        "diagnostic_complete": result["diagnostic_complete"],
        "response_done": raw.get("done"),
        "done_reason": raw.get("done_reason"),
        "eval_count": raw.get("eval_count"),
    }, indent=2))
    return 0 if result["diagnostic_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
