"""Fresh interpreter, runtime-only stdin; CPython audit hooks are NOT OS isolation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "Cargo.toml").is_file())
sys.path.insert(0, str(ROOT / "src"))
from uir_common.contracts import RuntimeContract, bind_references, reject_gold


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-gold", type=Path)
    args = parser.parse_args()

    def boundary(event, values):
        if event == "open" and isinstance(values[0], (str, bytes)):
            name = str(values[0]).casefold()
            if any(word in name for word in ("scoring_", "gold", "human_labels", "adjudication")):
                raise PermissionError("evaluation-only input denied")
    sys.addaudithook(boundary)
    if args.attempt_gold:
        args.attempt_gold.read_text()
        raise AssertionError("Negative boundary check failed")
    cases = json.load(sys.stdin)
    reject_gold(cases)
    outputs = []
    for row in cases:
        contract = RuntimeContract(row["requested_entity"], row["requested_attribute"],
                                   row["requested_period"], "fixture-policy", "fixture-evidence")
        facts = {str(i): fact for i, fact in enumerate(row.get("context_claims", []))}
        outputs.append({"case_id": row["case_id"], "input_route": "trusted_slot",
                        "used_fields": ["requested_entity", "requested_attribute", "requested_period", "context_claims"],
                        "output": bind_references(contract, facts, list(facts))})
    print(json.dumps(outputs, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
