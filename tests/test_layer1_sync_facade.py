"""M-G1-03 P1-13 — layer1 sync_indicator facade seam."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.indicator_binding import load_binding
from backend.app.sync.layer1_sync_facade import sync_indicator
from tests.fred_macro_incremental_support import insert_axis_observation


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(db_path=tmp_path / "facade.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def test_layer1SyncFacade_syncIndicator_thinWrapperOnly(tmp_path: Path) -> None:
    """覆盖范围：Layer 对外 sync 接缝
    测试对象：backend.app.sync.layer1_sync_facade.sync_indicator
    目的/目标：sync_indicator 应通过绑定 ID 执行 dry-run 增量同步
    验证点：返回 SKIPPED SyncJobResult 且消息含已有观测日期
    失败含义：Layer 须直接懂 SyncJobSpec（违反 AD-MG103-10）
    """
    binding = load_binding("ENV-E1-DGS10")
    assert binding.indicator_id == "ENV-E1-DGS10"

    cm = _cm(tmp_path)
    with cm.writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-facade-dgs10",
            indicator_id="ENV-E1-DGS10",
            obs_date=date(2026, 6, 10),
        )

    result = sync_indicator(
        "ENV-E1-DGS10",
        "incremental",
        dry_run=True,
        connection_manager=cm,
    )
    assert result.status == "SKIPPED"
    assert result.job_id
    assert "2026-06-10" in (result.message or "")

    with pytest.raises(LookupError, match="unknown indicator_id"):
        sync_indicator("NOT-A-REAL-INDICATOR", "incremental", dry_run=True)
