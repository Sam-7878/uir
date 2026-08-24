#!/usr/bin/env python3
from __future__ import annotations

import math
import random
from collections.abc import Iterable


def mcnemar_exact(left: list[bool], right: list[bool]) -> dict[str, float | int]:
    if len(left) != len(right):
        raise ValueError("paired inputs differ in length")
    left_only = sum(a and not b for a, b in zip(left, right))
    right_only = sum(not a and b for a, b in zip(left, right))
    discordant = left_only + right_only
    p_value = 1.0 if discordant == 0 else min(
        1.0,
        2
        * sum(
            math.comb(discordant, index)
            for index in range(0, min(left_only, right_only) + 1)
        )
        / (2**discordant),
    )
    return {
        "left_only": left_only,
        "right_only": right_only,
        "discordant": discordant,
        "p_value": p_value,
    }


def paired_bootstrap_delta(
    left: list[float],
    right: list[float],
    seed: int = 20260807,
    samples: int = 5000,
) -> dict[str, float]:
    if len(left) != len(right) or not left:
        return {"mean_delta": 0.0, "ci95_low": 0.0, "ci95_high": 0.0}
    deltas = [b - a for a, b in zip(left, right)]
    rng = random.Random(seed)
    estimates = sorted(
        sum(deltas[rng.randrange(len(deltas))] for _ in deltas) / len(deltas)
        for _ in range(samples)
    )
    return {
        "mean_delta": sum(deltas) / len(deltas),
        "ci95_low": estimates[int(0.025 * samples)],
        "ci95_high": estimates[min(samples - 1, int(0.975 * samples))],
    }


def percentile(values: Iterable[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * quantile
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(ordered[low])
    return ordered[low] * (high - position) + ordered[high] * (position - low)
