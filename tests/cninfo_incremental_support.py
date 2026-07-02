"""Shared CNINFO incremental test bootstrap (R3-DCP-05 S07)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_ports.cninfo_port import create_cninfo_fetch_port
from backend.app.ops.cninfo_incremental_run import (
    CninfoIncrementalFetchProxy,
    build_cninfo_incremental_service,
)
from backend.app.ops.cninfo_incremental_watermark import (
    enabled_cninfo_source_registry,
    read_since_date_for_instrument,
)
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.live_incremental_support import bootstrap_acceptance_cm

SYMBOL = "sh.600519"
FIXTURE_DATE = date(2024, 6, 25)
ANNOUNCEMENT_ID = "cninfo-001"


def bootstrap_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "cninfo_incr.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def seed_watermark_row(con, publish_date: str) -> None:
    con.execute("DELETE FROM cn_announcement_clean WHERE instrument_id = ?", [SYMBOL])
    publish_ts = datetime.combine(date.fromisoformat(publish_date), datetime.min.time(), tzinfo=UTC)
    con.execute(
        """
        INSERT INTO cn_announcement_clean (
            announcement_id, instrument_id, title, publish_timestamp, data_domain,
            source_used, content_status, batch_id, created_at
        ) VALUES (?, ?, 'seed', ?, 'cn_announcements', 'seed', 'metadata_only', 'b0', CURRENT_TIMESTAMP)
        """,
        [f"seed-{publish_date}", SYMBOL, publish_ts],
    )


def bootstrap_cninfo_live_e2e_ctx(
    sandbox_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """Bootstrap CNINFO product-live e2e under isolated M-DATA-03 sandbox (ADR-034)."""
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_acceptance_cm(sandbox_root)
    raw_root = sandbox_root / "raw" / "cninfo"
    raw_root.mkdir(parents=True, exist_ok=True)
    port = create_cninfo_fetch_port(symbols=(SYMBOL,), max_rows=20, use_mock=False)
    orch = DataSyncOrchestrator(cm)
    registry = enabled_cninfo_source_registry()
    with cm.writer() as con:
        since = read_since_date_for_instrument(con, SYMBOL)
    service = build_cninfo_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={SYMBOL: since},
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {
        "cm": cm,
        "orch": orch,
        "service": service,
        "registry": registry,
        "raw_root": raw_root,
        "sandbox_root": sandbox_root,
    }


@pytest.fixture
def cninfo_incremental_e2e_ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = create_cninfo_fetch_port(symbols=(SYMBOL,), max_rows=20, use_mock=True)
    orch = DataSyncOrchestrator(cm)
    registry = enabled_cninfo_source_registry()
    with cm.writer() as con:
        since = read_since_date_for_instrument(con, SYMBOL)
    service = build_cninfo_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={SYMBOL: since},
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {"cm": cm, "orch": orch, "service": service, "registry": registry}
