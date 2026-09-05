"""Authoritative Entity Registry and Runtime Lookup Service (Assumption A1).

Provides canonical verification of corporate/domain entities at runtime.
Runtime verification strictly performs database/registry lookup; it NEVER
reads or references dataset annotation flags (e.g. entity_valid).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from evaluation.uir_phase4d.common import ROOT

REGISTRY_PATH = ROOT / "evaluation/uir_phase4d/runtime/entity_registry.json"


class EntityStatus(str, Enum):
    EXISTS = "EXISTS"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class EntityLookupResult:
    status: EntityStatus
    canonical_id: str | None
    name: str | None
    jurisdiction: str | None


class EntityRegistry:
    def __init__(self, registry_file: Path | None = None) -> None:
        path = registry_file or REGISTRY_PATH
        if not path.exists():
            raise FileNotFoundError(f"Authoritative entity registry not found at {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        self._entities: dict[str, dict[str, Any]] = {k.upper(): v for k, v in data.get("entities", {}).items()}
        self._aliases: dict[str, str] = {k.upper(): v.upper() for k, v in data.get("aliases", {}).items()}

    def __len__(self) -> int:
        return len(self._entities)

    def count(self) -> int:
        return len(self._entities)

    def lookup(self, query: str | None) -> EntityLookupResult:
        if not query or not query.strip():
            return EntityLookupResult(EntityStatus.NOT_FOUND, None, None, None)
        
        q = query.strip().upper()
        # Direct ticker/ID lookup
        if q in self._entities:
            meta = self._entities[q]
            return EntityLookupResult(EntityStatus.EXISTS, q, meta.get("name"), meta.get("jurisdiction"))
        
        # Alias lookup
        if q in self._aliases:
            canon = self._aliases[q]
            if canon in self._entities:
                meta = self._entities[canon]
                return EntityLookupResult(EntityStatus.EXISTS, canon, meta.get("name"), meta.get("jurisdiction"))
            
        # Check partial/ambiguous
        matches = [k for k, meta in self._entities.items() if q in meta.get("name", "").upper()]
        if len(matches) == 1:
            m = matches[0]
            meta = self._entities[m]
            return EntityLookupResult(EntityStatus.EXISTS, m, meta.get("name"), meta.get("jurisdiction"))
        elif len(matches) > 1:
            return EntityLookupResult(EntityStatus.AMBIGUOUS, None, None, None)

        return EntityLookupResult(EntityStatus.NOT_FOUND, None, None, None)
