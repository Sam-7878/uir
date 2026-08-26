"""Dataset leakage, duplication, bilingual balance, and goal completeness audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = load(args.dataset)
    prompts = [row.get("prompt", "") for row in rows]
    duplicate_prompts = [value for value, count in Counter(prompts).items() if count > 1]
    template_signatures = [re.sub(r"Request reference: R\d{4}\.", "Request reference: <ID>.", prompt) for prompt in prompts]
    template_families = sum(1 for count in Counter(template_signatures).values() if count > 1)
    missing_goals = [row["case_id"] for row in rows if not isinstance(row.get("attack_goal"), dict)]
    label_leakage = [row["case_id"] for row in rows if row["attack_class"] in row.get("prompt", "")]
    language_counts = Counter(row.get("language") for row in rows)
    class_counts = Counter(row.get("attack_class") for row in rows)
    result = {
        "status": "PASS" if not duplicate_prompts and not missing_goals else "FAIL",
        "case_count": len(rows), "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "duplicate_prompt_count": len(duplicate_prompts), "template_family_count": template_families, "missing_attack_goal_cases": missing_goals,
        "label_leakage_cases": label_leakage, "language_counts": dict(language_counts), "attack_class_counts": dict(class_counts),
        "limitations": ["Lexical-pattern audit cannot establish semantic non-triviality; manual threat review remains required."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
