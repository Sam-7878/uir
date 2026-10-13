"""Gold-blind runtime process; no grader/dataset/evaluation imports."""
import argparse
import json
from pathlib import Path
from uir_common.contracts import canonical_digest
from uir_common.query_contract import make_artifact, parse_raw
from .interpreter_python import interpret


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--probe-gold", type=Path, required=True)
    args = parser.parse_args()
    try:
        args.probe_gold.read_bytes()
    except (PermissionError, FileNotFoundError):
        print(json.dumps({"probe": "GOLD_READ_BLOCKED"}))
    else:
        raise RuntimeError("GOLD_READ_SUCCEEDED_RUNTIME_MUST_ABORT")
    for line in args.runtime.read_text().splitlines():
        row = json.loads(line)
        source = row["source"]
        packet = {"artifact": make_artifact(parse_raw(row["raw_user_request"]), row["authority"], source, action=row["action"]),
                  "authority": row["authority"], "current_evidence_version": source["version"],
                  "current_evidence_sha256": canonical_digest(source), "context": row["context"]}
        print(json.dumps({"case_id": row["case_id"], "result": interpret(packet)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
