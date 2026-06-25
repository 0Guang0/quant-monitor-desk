"""Batch6 source_health_snapshot writer — non-DH2 persist path (ADR-024)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ponytail: DDL mirrors docs/modules/data_sources.md §5.8; prod migration owned by B3F-MIG
_SOURCE_HEALTH_SNAPSHOT_DDL = """
CREATE TABLE IF NOT EXISTS source_health_snapshot (
    snapshot_id         VARCHAR PRIMARY KEY,
    source_id           VARCHAR,
    as_of_timestamp     TIMESTAMP,
    health_status       VARCHAR,
    success_rate_7d     DOUBLE,
    last_success_time   TIMESTAMP,
    last_error_time     TIMESTAMP,
    last_error_type     VARCHAR,
    avg_latency_ms_7d   DOUBLE,
    schema_drift_count  INTEGER,
    rate_limit_count    INTEGER,
    notes               TEXT
);
"""


@dataclass(frozen=True)
class SourceHealthSnapshotRow:
    snapshot_id: str
    source_id: str
    as_of_timestamp: datetime
    health_status: str
    success_rate_7d: float | None = None
    last_success_time: datetime | None = None
    last_error_time: datetime | None = None
    last_error_type: str | None = None
    avg_latency_ms_7d: float | None = None
    schema_drift_count: int | None = None
    rate_limit_count: int | None = None
    notes: str | None = None


def _now_utc() -> datetime:
    return datetime.now(UTC)


class SourceHealthSnapshotWriter:
    """Isolated / Batch6 writer — not wired into DH2 read-only profiles."""

    def __init__(self, con) -> None:
        self._con = con

    def ensure_schema(self) -> None:
        self._con.execute(_SOURCE_HEALTH_SNAPSHOT_DDL)

    def insert(self, row: SourceHealthSnapshotRow) -> None:
        self._con.execute(
            """
            INSERT INTO source_health_snapshot (
                snapshot_id, source_id, as_of_timestamp, health_status,
                success_rate_7d, last_success_time, last_error_time,
                last_error_type, avg_latency_ms_7d, schema_drift_count,
                rate_limit_count, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row.snapshot_id,
                row.source_id,
                row.as_of_timestamp,
                row.health_status,
                row.success_rate_7d,
                row.last_success_time,
                row.last_error_time,
                row.last_error_type,
                row.avg_latency_ms_7d,
                row.schema_drift_count,
                row.rate_limit_count,
                row.notes,
            ],
        )

    def fetch_by_snapshot_id(self, snapshot_id: str) -> dict[str, Any] | None:
        row = self._con.execute(
            "SELECT * FROM source_health_snapshot WHERE snapshot_id = ?",
            [snapshot_id],
        ).fetchone()
        if row is None:
            return None
        cols = [
            "snapshot_id",
            "source_id",
            "as_of_timestamp",
            "health_status",
            "success_rate_7d",
            "last_success_time",
            "last_error_time",
            "last_error_type",
            "avg_latency_ms_7d",
            "schema_drift_count",
            "rate_limit_count",
            "notes",
        ]
        return dict(zip(cols, row, strict=True))


def persist_readiness_rollup(
    con,
    *,
    evidence_dir: Path,
    overall_status: str,
    gate_ready: bool,
    gate_rationale: str,
) -> str:
    """Persist DH2 rollup summary into source_health_snapshot (SH-04, non-DH2 path)."""
    manifest_path = evidence_dir / "rollup_manifest.json"
    rollup = json.loads(manifest_path.read_text(encoding="utf-8"))
    writer = SourceHealthSnapshotWriter(con)
    writer.ensure_schema()
    snapshot_id = f"rollup-{rollup.get('rollup_id', uuid.uuid4().hex[:12])}"
    notes = json.dumps(
        {
            "rollup_id": rollup.get("rollup_id"),
            "profiles": rollup.get("profiles"),
            "gate_ready": gate_ready,
            "gate_rationale": gate_rationale,
            "staged_only": rollup.get("staged_only"),
        },
        ensure_ascii=False,
    )
    writer.insert(
        SourceHealthSnapshotRow(
            snapshot_id=snapshot_id,
            source_id="source_readiness_rollup",
            as_of_timestamp=_now_utc(),
            health_status=overall_status,
            notes=notes,
        )
    )
    return snapshot_id
