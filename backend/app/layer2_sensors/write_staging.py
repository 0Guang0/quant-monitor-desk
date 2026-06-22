"""Unified staging-table write helper for Layer 2 writers (L2-06)."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence

import duckdb

from backend.app.db.write_manager import WriteManager, WriteRequest


def write_staging_table(
    wm: WriteManager,
    con: duckdb.DuckDBPyConnection,
    *,
    target_table: str,
    staging_prefix: str,
    template_table: str,
    rows: Sequence[tuple],
    insert_sql: str,
    row_inserter: Callable[[duckdb.DuckDBPyConnection, str, tuple], None],
    validation_report_id: str,
    run_id: str,
    job_id: str,
    source_used: str,
    data_domain: str,
    primary_keys: tuple[str, ...],
    own_transaction: bool = True,
):
    """Create staging from template, insert rows, and WriteManager.clean."""
    staging = f"{staging_prefix}_{uuid.uuid4().hex[:8]}"
    con.execute(f"CREATE TABLE {staging} AS SELECT * FROM {template_table} WHERE 1=0")
    for row in rows:
        row_inserter(con, staging, row)
    req = WriteRequest(
        run_id=run_id,
        job_id=job_id,
        target_table=target_table,
        staging_table=staging,
        write_mode="append_only",
        primary_keys=primary_keys,
        validation_report_id=validation_report_id,
        source_used=source_used,
        data_domain=data_domain,
    )
    return wm.write(req, con=con, own_transaction=own_transaction)
