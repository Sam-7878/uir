#!/usr/bin/env python3
"""Frozen World Bank registry adapter used by the Phase-2 evaluation."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RegistryFact:
    fact_id: str
    entity_id: str
    entity_name: str
    claim_type: str
    attribute: str
    value: str
    unit: str
    period: str
    provenance: dict

    def claim(self) -> dict:
        return {
            "claim_type": self.claim_type,
            "entity_id": self.entity_id,
            "attribute": self.attribute,
            "value": self.value,
            "unit": self.unit,
            "period": self.period,
            "provenance": self.provenance["source_id"],
        }

    def claims(self) -> list[dict]:
        source = self.provenance["source_id"]
        return [
            {"claim_type": "entity_claim", "entity_id": self.entity_id, "attribute": "entity_name", "value": self.entity_name, "unit": "", "period": "", "provenance": source},
            {"claim_type": "attribute_claim", "entity_id": self.entity_id, "attribute": "available_attribute", "value": self.attribute, "unit": "", "period": "", "provenance": source},
            self.claim(),
            {"claim_type": "relation_claim", "entity_id": self.entity_id, "attribute": "has_attribute", "value": self.attribute, "unit": "", "period": "", "provenance": source},
            {"claim_type": "temporal_claim", "entity_id": self.entity_id, "attribute": self.attribute, "value": self.period, "unit": "", "period": self.period, "provenance": source},
            {"claim_type": "provenance_claim", "entity_id": self.entity_id, "attribute": self.attribute, "value": source, "unit": "", "period": self.period, "provenance": source},
        ]


class FrozenRegistry:
    def __init__(self, path: Path):
        self.path = path
        self.facts = [RegistryFact(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.entities = {fact.entity_id for fact in self.facts}
        self._index = {(fact.entity_id, fact.attribute, fact.period): fact for fact in self.facts}

    def entity_exists(self, entity_id: str) -> bool:
        return entity_id.upper() in self.entities

    def lookup(self, entity_id: str, attribute: str, period: str) -> RegistryFact | None:
        return self._index.get((entity_id.upper(), attribute, str(period)))

    def facts_for_entity(self, entity_id: str, limit: int = 8) -> list[RegistryFact]:
        return [fact for fact in self.facts if fact.entity_id == entity_id.upper()][:limit]

    def naive_retrieve(self, query: str, limit: int = 3) -> list[RegistryFact]:
        tokens = set(re.findall(r"[a-z0-9_]+", query.lower()))
        scored = []
        for fact in self.facts:
            text = f"{fact.entity_id} {fact.entity_name} {fact.attribute} {fact.period} {fact.unit}".lower()
            score = len(tokens & set(re.findall(r"[a-z0-9_]+", text)))
            scored.append((score, fact.fact_id, fact))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in scored[:limit]]


def fact_context(facts: list[RegistryFact]) -> str:
    return "\n".join(
        f"FACT entity={f.entity_id}; attribute={f.attribute}; value={f.value}; unit={f.unit}; period={f.period}; provenance={f.provenance['source_id']}"
        for f in facts
    )
