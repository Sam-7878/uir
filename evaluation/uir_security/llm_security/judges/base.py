"""Judge protocol. Judges never invoke or mutate a tested baseline."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseJudge(ABC):
    @abstractmethod
    def evaluate(self, case: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        """Return observations derived only from case data and execution record."""
