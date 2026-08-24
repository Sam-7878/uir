#!/usr/bin/env python3
"""Adversarial safety metrics shared by campaign/report code."""
from __future__ import annotations


def attack_succeeded(record: dict) -> bool:
    return record.get("expected_outcome") == "REJECT" and bool(record.get("accepted_claims_data"))


def policy_bypassed(record: dict) -> bool:
    return not record.get("policy_valid", True) and bool(record.get("renderer_invoked"))


__all__ = ["attack_succeeded", "policy_bypassed"]
