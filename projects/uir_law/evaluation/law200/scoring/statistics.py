"""Exact paired tests, Wilson intervals, risk differences, and Holm correction."""
from __future__ import annotations

import math
from typing import Any


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, float | int | None]:
    if total <= 0:
        return {"successes": successes, "total": total, "rate": None, "low": None, "high": None}
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {"successes": successes, "total": total, "rate": p, "low": max(0.0, centre - margin), "high": min(1.0, centre + margin)}


def exact_mcnemar(left: list[bool], right: list[bool]) -> dict[str, float | int]:
    if len(left) != len(right):
        raise ValueError("paired endpoints differ in length")
    left_only = sum(a and not b for a, b in zip(left, right, strict=True))
    right_only = sum(b and not a for a, b in zip(left, right, strict=True))
    discordant = left_only + right_only
    if discordant == 0:
        p_value = 1.0
    else:
        smaller = min(left_only, right_only)
        tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (2**discordant)
        p_value = min(1.0, 2 * tail)
    return {"left_only": left_only, "right_only": right_only, "discordant": discordant, "p_value": p_value}


def holm(items: list[dict[str, Any]], alpha: float = 0.05) -> list[dict[str, Any]]:
    ordered = sorted(enumerate(items), key=lambda item: float(item[1]["p_value"]))
    adjusted = [0.0] * len(items)
    running = 0.0
    count = len(items)
    for rank, (original, item) in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * float(item["p_value"])))
        adjusted[original] = running
    return [item | {"holm_adjusted_p": adjusted[index], "reject_at_alpha_0_05": adjusted[index] <= alpha} for index, item in enumerate(items)]


def risk_difference(left_events: list[bool], right_events: list[bool]) -> float:
    if len(left_events) != len(right_events) or not left_events:
        raise ValueError("non-empty paired endpoints required")
    return sum(right_events) / len(right_events) - sum(left_events) / len(left_events)
