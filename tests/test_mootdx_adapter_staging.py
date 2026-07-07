"""R3-DCP-01 — MootdxAdapter staging path tests."""

from __future__ import annotations

from pathlib import Path

from tests.service_path_support import build_test_adapter
from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port
from backend.app.datasources.fetch_ports.tdx_fetch_guards import EQUITY_INDEX_MAX_ROWS
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.macro_incremental_common import enabled_source_registry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations

SYMBOL = "sh.600519"
FIXTURE_DATE = "2024-06-25"


def test_mootdxAdapter_fetchPortPath_populatesStaging(tmp_path: Path) -> None:
    """覆盖范围：MootdxAdapter + fetch_port 金路径 staging
    测试对象：MootdxAdapter.fetch
    目的/目标：replay bars 应写入 stg_foundation_smoke 并返回 staging_table
    验证点：status SUCCESS；staging_table 非空；source_used=mootdx
    失败含义：adapter 不填 staging 则 run_incremental 无法落 security_bar_1d
    """
    db = tmp_path / "adapter.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    port = create_mootdx_fetch_port(
        symbols=(SYMBOL,), max_rows=EQUITY_INDEX_MAX_ROWS, use_mock=True
    )
    registry = enabled_source_registry(
        source_id="mootdx", data_domain="cn_equity_daily_bar"
    )
    adapter = build_test_adapter(
        "mootdx",
        registry,
        tmp_path / "raw",
        fetch_port=port,
    )
    req = FetchRequest(
        run_id="adapter-test",
        source_id="mootdx",
        data_domain="cn_equity_daily_bar",
        instrument_id=SYMBOL,
        start_time=FIXTURE_DATE,
        end_time=FIXTURE_DATE,
    )
    with cm.writer() as con:
        result = adapter.fetch(req, con=con, job_id="adapter-job", record_fetch_log=False)
    assert result.status == "SUCCESS"
    assert result.staging_table == "stg_foundation_smoke"
    assert result.row_count == 1
    with cm.reader() as con:
        row = con.execute(
            "SELECT trade_date, source_used FROM stg_foundation_smoke WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()
    assert row is not None and str(row[0]) == FIXTURE_DATE
    assert row[1] == "mootdx"
