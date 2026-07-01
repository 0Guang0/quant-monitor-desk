"""DCP-05 S05 — World Bank incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from backend.app.ops.macro_incremental_common import (
    compute_since_date,
    read_observation_date_watermark,
)
from backend.app.ops.world_bank_incremental_run import (
    build_world_bank_incremental_service,
    create_world_bank_incremental_port,
    run_world_bank_incremental,
)
from backend.app.ops.world_bank_incremental_watermark import (
    DATA_DOMAIN,
    DEFAULT_COUNTRIES,
    SOURCE_ID,
    clean_indicator_id,
    enabled_world_bank_source_registry,
)
from tests.macro_incremental_support import build_macro_e2e_ctx, insert_axis_observation


def _read_wb_since(con, countries):
    return {
        country: compute_since_date(
            read_observation_date_watermark(con, clean_indicator_id(country))
        ).isoformat()
        for country in countries
    }


@pytest.fixture
def world_bank_incremental_e2e_ctx(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    port = create_world_bank_incremental_port(
        countries=DEFAULT_COUNTRIES, max_rows=3, use_mock=True
    )
    return build_macro_e2e_ctx(
        tmp_path,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        fetch_port=port,
        since_reader=_read_wb_since,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_world_bank_incremental_service,
        registry_factory=enabled_world_bank_source_registry,
    )


def test_worldBankIncremental_e2e_replay_writesAxisObservation(
    world_bank_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_world_bank_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert 到 macro clean
    验证点：status==COMPLETED；composite indicator_id 行数>=1
    失败含义：world_bank 增量无法走 Sync 金路径写 macro clean
    """
    ctx = world_bank_incremental_e2e_ctx
    report = run_world_bank_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    indicator = clean_indicator_id("US")
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = ?",
            [indicator],
        ).fetchone()[0]
    assert count >= 1


def test_worldBankIncremental_idempotent_secondRun_rowCountStable(
    world_bank_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次增量跑 row count 不增
    测试对象：run_world_bank_incremental 幂等 upsert
    目的/目标：重复跑 observation_id PK upsert 不重复插入
    验证点：两次 COMPLETED 后 COUNT(*) 相等
    失败含义：幂等失败，生产重复跑会膨胀行数
    """
    ctx = world_bank_incremental_e2e_ctx
    run_world_bank_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_world_bank_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
    assert first >= 1
