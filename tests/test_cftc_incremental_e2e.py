"""DCP-05 S06 — CFTC incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest

from backend.app.ops.cftc_incremental_run import (
    build_cftc_incremental_service,
    create_cftc_incremental_port,
    run_cftc_incremental,
)
from backend.app.ops.cftc_incremental_watermark import (
    DATA_DOMAIN,
    DEFAULT_MARKETS,
    SOURCE_ID,
    WEEKLY_ADVANCE_DAYS,
    enabled_cftc_source_registry,
    read_since_dates_for_markets,
)
from tests.macro_incremental_support import build_macro_e2e_ctx, insert_axis_observation


@pytest.fixture
def cftc_incremental_e2e_ctx(tmp_path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    port = create_cftc_incremental_port(markets=DEFAULT_MARKETS, max_rows=3, use_mock=True)
    return build_macro_e2e_ctx(
        tmp_path,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        fetch_port=port,
        since_reader=read_since_dates_for_markets,
        instrument_ids=DEFAULT_MARKETS,
        service_builder=build_cftc_incremental_service,
        registry_factory=enabled_cftc_source_registry,
    )


def test_cftcIncremental_e2e_replay_writesAxisObservation(
    cftc_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_cftc_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert 到 macro clean
    验证点：status==COMPLETED；axis_observation 行数>=1；indicator_id==088691
    失败含义：cftc 增量无法走 Sync 金路径写 macro clean
    """
    ctx = cftc_incremental_e2e_ctx
    report = run_cftc_incremental(
        ctx["orch"],
        service=ctx["service"],
        markets=DEFAULT_MARKETS,
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = '088691'"
        ).fetchone()[0]
    assert count >= 1


def test_cftcIncremental_weeklyWatermark_advancesSevenDays() -> None:
    """覆盖范围：CFTC 周频水位 advance_days=7
    测试对象：read_since_dates_for_markets + compute_since_date
    目的/目标：周频 COT 水位后 since = watermark + 7 天
    验证点：watermark=2026-06-01 → since=2026-06-08
    失败含义：日频水位导致周频源重复拉取或漏拉
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.macro_incremental_common import compute_since_date, read_observation_date_watermark

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    insert_axis_observation(
        con,
        observation_id="obs-cftc",
        indicator_id="088691",
        obs_date=date(2026, 6, 1),
    )
    wm = read_observation_date_watermark(con, "088691")
    since = compute_since_date(wm, today=date(2026, 6, 30), advance_days=WEEKLY_ADVANCE_DAYS)
    assert since == date(2026, 6, 8)


def test_cftcIncremental_emptyResponse_whenWatermarkCurrent(
    cftc_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：cftc staging adapter + run_cftc_incremental
    目的/目标：since 之后无新观测时不写假行
    验证点：status==EMPTY_RESPONSE；axis_observation 行数不变
    失败含义：水位追上仍拉取或写入，增量语义错误
    """
    ctx = cftc_incremental_e2e_ctx
    today = datetime.now(UTC).date()
    with ctx["cm"].writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-cftc-seed",
            indicator_id="088691",
            obs_date=today,
        )
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    report = run_cftc_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    assert report.instrument_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before
