"""Validate and quote DuckDB SQL identifiers."""

from __future__ import annotations

import re

_IDENT = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def quote_ident(name: str) -> str:
    """Return a safely quoted identifier or raise ValueError."""
    if not _IDENT.fullmatch(name):
        raise ValueError(f"invalid SQL identifier: {name!r}")
    return '"' + name.replace('"', '""') + '"'
