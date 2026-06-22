"""Connection scope helpers for db layer (DB-05)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import duckdb

from backend.app.db.connection import ConnectionManager

_T = TypeVar("_T")


def with_connection(
    con: duckdb.DuckDBPyConnection | None,
    conn_manager: ConnectionManager,
    fn: Callable[[duckdb.DuckDBPyConnection], _T],
) -> _T:
    """Run fn on con or a short-lived writer connection."""
    if con is not None:
        return fn(con)
    with conn_manager.writer() as writer_con:
        return fn(writer_con)
