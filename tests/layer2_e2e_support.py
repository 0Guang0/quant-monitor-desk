"""Shared Layer2 e2e DB helpers (DCP-07 / aligned with layer1_clean_e2e_support)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer2_sensors.schema_ddl import ensure_layer2_staging_tables


def layer2_cm(tmp_path: Path, name: str) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / name)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_layer2_staging_tables(con)
    return cm


def insert_layer2_validation_report(
    cm: ConnectionManager,
    report_id: str,
    *,
    fetch_ids: list[str] | None = None,
    content_hashes: list[str] | None = None,
    source_id: str = "staged_fixture",
    rule_version: str = "layer2_sensor_staged_v1",
) -> None:
    resolved_fetch_ids = fetch_ids if fetch_ids is not None else ["fetch-l2-wm"]
    resolved_content_hashes = (
        content_hashes if content_hashes is not None else ["hash-l2-wm"]
    )
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review,
                rule_set_id, rule_version,
                source_fetch_ids_json, source_content_hashes_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                report_id,
                "run-layer2",
                "layer2_cross_asset_daily",
                source_id,
                "PASSED",
                1,
                0,
                0,
                True,
                False,
                "layer2_v1",
                rule_version,
                json.dumps(resolved_fetch_ids),
                json.dumps(resolved_content_hashes),
            ],
        )
