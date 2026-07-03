"""Shared CN product-live replay-first helper (R3H-08 S08-02)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TypeVar

from backend.app.datasources.adapters.fetch_port import FetchPayload, FetchPort
from backend.app.datasources.fetch_result import FetchRequest

_MockPort = TypeVar("_MockPort", bound=FetchPort)


def replay_first_fetch_payload(
    mock_port_cls: type[_MockPort],
    *,
    symbols: Sequence[str],
    max_rows: int,
    replay_path: Path,
    req: FetchRequest,
    replay_caught_up_fallback: bool = False,
    **mock_port_kwargs,
) -> FetchPayload:
    """Product live CN path: replay fixture when present, else mock synthetic bars."""
    return mock_port_cls(
        symbols=symbols,
        max_rows=max_rows,
        replay_path=replay_path,
        replay_caught_up_fallback=replay_caught_up_fallback,
        **mock_port_kwargs,
    ).fetch_payload(req)
