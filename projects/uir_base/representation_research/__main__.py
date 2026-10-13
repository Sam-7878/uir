import argparse
from datetime import datetime, timezone
from pathlib import Path
from .common import RESULTS


def main():
    parser = argparse.ArgumentParser(description="S-stage immutable-input representation research")
    parser.add_argument("stage", choices=["baseline", "standalone", "dataset", "evaluate", "freeze", "infer", "score"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or RESULTS / datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True, exist_ok=True)
    if args.stage == "baseline":
        from .baseline import run
        run(out)
    elif args.stage == "standalone":
        from .standalone import run
        run(out)
    elif args.stage == "dataset":
        from .dataset import prepare
        prepare(out)
    elif args.stage == "evaluate":
        from .evaluation import run
        run(out)
    elif args.stage in {"freeze", "infer"}:
        from . import experiment
        getattr(experiment, args.stage)(out)
    elif args.stage == "score":
        from .analysis import score
        score(out)


if __name__ == "__main__":
    main()
