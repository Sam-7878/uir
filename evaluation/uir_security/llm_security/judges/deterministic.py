from __future__ import annotations

import re
from typing import Any, Dict

from .base import BaseJudge


CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


class DeterministicJudge(BaseJudge):
    def evaluate(self, case: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        model = str(record.get("model_output", ""))
        final = str(record.get("final_output", ""))
        return {
            "empty_output": not bool(final.strip()),
            "control_character_output": bool(CONTROL.search(model) or CONTROL.search(final)),
            "terminal_status": record.get("terminal_status"),
            "responded": record.get("terminal_status") == "RESPONDED",
        }
