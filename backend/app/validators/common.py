"""Shared validator helpers for DataQuality and SourceConflict layers."""

from __future__ import annotations

from backend.app.db.sql_identifiers import quote_ident


def is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def as_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def as_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_rows(
    con, table_name: str, *, limit: int | None = None
) -> list[dict[str, object]]:
    quoted_table = quote_ident(table_name)
    limit_sql = f" LIMIT {int(limit)}" if limit is not None else ""
    cursor = con.execute(f"SELECT * FROM {quoted_table}{limit_sql}")
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
