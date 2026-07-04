"""Shared RED stub helpers for M-G1-03 planned tests (skip until slice Execute)."""

from __future__ import annotations

import pytest


def red_skip(slice_id: str, plan_task: str) -> None:
    pytest.skip(f"M-G1-03 RED: {slice_id} {plan_task} — implement in Execute")
