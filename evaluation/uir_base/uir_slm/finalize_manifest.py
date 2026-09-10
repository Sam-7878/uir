#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--results", type=Path, default=Path("results/uir_slm")); args = parser.parse_args()
    path = args.results / "run_manifest.json"; manifest = json.loads(path.read_text(encoding="utf-8")); evidence = {}
    for item in sorted(args.results.iterdir()):
        if item.is_file() and item.name != path.name:
            evidence[item.name] = {"bytes": item.stat().st_size, "sha256": hashlib.sha256(item.read_bytes()).hexdigest()}
    manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat(); manifest["status"] = "complete"; manifest["evidence"] = evidence
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "evidence_files": len(evidence)}, sort_keys=True))


if __name__ == "__main__": main()
