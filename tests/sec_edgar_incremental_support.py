"""Shared SEC EDGAR incremental test bootstrap (R3-DCP-05 S09)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port
from backend.app.ops.sec_edgar_incremental_run import build_sec_edgar_incremental_service
from backend.app.ops.sec_edgar_incremental_watermark import (
    enabled_sec_edgar_source_registry,
    read_since_date_for_cik,
)
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.live_incremental_support import bootstrap_acceptance_cm, bootstrap_port_live_e2e_ctx
from tests.network_reachability import sec_edgar_reachable

CIK = "0000320193"
ACCESSION = "0000320193-25-000079"
FILING_DATE = date(2025, 11, 1)


def bootstrap_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "sec_edgar_incr.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def seed_watermark_row(con, filing_date: str) -> None:
    con.execute("DELETE FROM us_disclosure_clean WHERE cik = ?", [CIK])
    con.execute(
        """
        INSERT INTO us_disclosure_clean (
            accession_number, cik, form_type, filing_date, report_date,
            data_domain, source_used, batch_id, created_at
        ) VALUES (?, ?, '10-K', ?, ?, 'us_filings', 'seed', 'b0', CURRENT_TIMESTAMP)
        """,
        [f"seed-{filing_date}", CIK, filing_date, filing_date],
    )


def bootstrap_sec_edgar_live_e2e_ctx(
    sandbox_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """Bootstrap SEC EDGAR live e2e under isolated M-DATA-03 sandbox (ADR-034)."""
    import os

    ua = os.environ.get("SEC_EDGAR_USER_AGENT", "")
    if not sec_edgar_reachable(user_agent=ua or "reachability-probe@example.com"):
        pytest.skip("SEC EDGAR API unreachable from this network (TLS/connectivity)")
    return bootstrap_port_live_e2e_ctx(
        sandbox_root,
        monkeypatch,
        source_id="sec_edgar",
        data_domain="us_filings",
        port_factory=lambda **kw: create_sec_edgar_fetch_port(
            ciks=(CIK,), max_filings=5, data_domain="us_filings", **kw
        ),
        service_builder=build_sec_edgar_incremental_service,
        registry_factory=enabled_sec_edgar_source_registry,
        since_reader=lambda con, _ids: {CIK: read_since_date_for_cik(con, CIK)},
        instrument_ids=(CIK,),
        env_key="SEC_EDGAR_USER_AGENT",
    )


@pytest.fixture
def sec_edgar_incremental_e2e_ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = create_sec_edgar_fetch_port(
        ciks=(CIK,), max_filings=5, data_domain="us_filings", use_mock=True
    )
    orch = DataSyncOrchestrator(cm)
    registry = enabled_sec_edgar_source_registry()
    with cm.writer() as con:
        since = read_since_date_for_cik(con, CIK)
    service = build_sec_edgar_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_cik={CIK: since},
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {"cm": cm, "orch": orch, "service": service, "registry": registry}
