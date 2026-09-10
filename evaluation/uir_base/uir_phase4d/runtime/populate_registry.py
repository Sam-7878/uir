"""Populate entity_registry.json with benchmark entities QV0001-QV1200."""
from __future__ import annotations

import json
from pathlib import Path

p = Path(__file__).parent / "entity_registry.json"
data = json.loads(p.read_text(encoding="utf-8"))
for i in range(1, 1201):
    qid = f"QV{i:04d}"
    data["entities"][qid] = {
        "name": f"Benchmark Enterprise {qid}",
        "jurisdiction": "BENCHMARK",
        "lei": f"549300{qid}BENCH001",
    }

p.write_text(json.dumps(data, indent=2), encoding="utf-8")
print("Total entities in registry:", len(data["entities"]))
