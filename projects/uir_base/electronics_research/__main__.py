import argparse
import json
from pathlib import Path
from .policy import validate_results_dir, verify_manifest

def main():
    parser = argparse.ArgumentParser(description="T-stage local-only research evidence; no implicit publication")
    parser.add_argument("command", choices=["prepare", "verify", "scan-staged"])
    parser.add_argument("--results-dir", type=Path)
    parser.add_argument("--network-metadata", action="store_true")
    args = parser.parse_args()
    if args.command == "scan-staged":
        from .privacy import staged_scan
        result = staged_scan()
        print(json.dumps(result))
        raise SystemExit(1 if result["violations"] else 0)
    if args.results_dir is None:
        parser.error("--results-dir required; no root/docs output fallback")
    directory = validate_results_dir(args.results_dir)
    if args.command == "prepare":
        from .prepare import run
        run(directory, network_metadata=args.network_metadata)
    else:
        print(json.dumps({"verified_files": verify_manifest(directory)}))

if __name__ == "__main__":
    main()
