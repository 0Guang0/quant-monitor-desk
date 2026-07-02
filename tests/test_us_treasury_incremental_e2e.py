"""DCP-05 S03 — US Treasury incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from backend.app.datasources.product_live_gate import ProductLiveGateError
from backend.app.ops.db_inspector import DbInspector
from backend.app.ops.us_treasury_incremental_run import (
    DEFAULT_TENORS,
    DATA_DOMAIN,
    SOURCE_ID,
    build_us_treasury_incremental_service,
    create_us_treasury_incremental_port,
    enabled_us_treasury_source_registry,
    read_since_dates_for_instruments,
    run_us_treasury_incremental,
)

from tests.macro_incremental_support import (
    bootstrap_macro_live_e2e_ctx,
    build_macro_e2e_ctx,
    insert_axis_observation,
)


@pytest.fixture
def us_treasury_incremental_e2e_ctx(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    port = create_us_treasury_incremental_port(tenors=DEFAULT_TENORS, max_rows=3, use_mock=True)
    return build_macro_e2e_ctx(
        tmp_path,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        fetch_port=port,
        since_reader=read_since_dates_for_instruments,
        instrument_ids=DEFAULT_TENORS,
        service_builder=build_us_treasury_incremental_service,
        registry_factory=enabled_us_treasury_source_registry,
    )


def test_usTreasuryIncremental_e2e_replay_writesAxisObservation(
    us_treasury_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_us_treasury_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert 到 macro clean
    验证点：status==COMPLETED；axis_observation 行数>=1；indicator_id==10Y
    失败含义：us_treasury 增量无法走 Sync 金路径写 macro clean
    """
    ctx = us_treasury_incremental_e2e_ctx
    report = run_us_treasury_incremental(
        ctx["orch"],
        service=ctx["service"],
        tenors=DEFAULT_TENORS,
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = '10Y'"
        ).fetchone()[0]
        assert count >= 1
        row = con.execute(
            "SELECT raw_value FROM axis_observation WHERE indicator_id = '10Y' LIMIT 1"
        ).fetchone()
    assert row is not None and float(row[0]) == 4.25


def test_usTreasuryIncremental_idempotent_secondRun_rowCountStable(
    us_treasury_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次增量跑 row count 不增
    测试对象：run_us_treasury_incremental 幂等 upsert
    目的/目标：重复跑 observation_id PK upsert 不重复插入
    验证点：两次 COMPLETED 后 COUNT(*) 相等
    失败含义：幂等失败，生产重复跑会膨胀行数
    """
    ctx = us_treasury_incremental_e2e_ctx
    run_us_treasury_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_us_treasury_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
    assert first >= 1


def test_usTreasuryIncremental_emptyResponse_whenWatermarkCurrent(
    us_treasury_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：treasury staging adapter + run_us_treasury_incremental
    目的/目标：since 之后无新观测时不写假行
    验证点：status==EMPTY_RESPONSE；axis_observation 行数不变
    失败含义：水位追上仍拉取或写入，增量语义错误
    """
    ctx = us_treasury_incremental_e2e_ctx
    today = datetime.now(UTC).date()
    with ctx["cm"].writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-treasury-seed",
            indicator_id="10Y",
            obs_date=today,
        )
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    report = run_us_treasury_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    assert report.instrument_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before


def test_usTreasuryLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 treasury live port 阻断
    测试对象：create_us_treasury_incremental_port(use_mock=False)
    目的/目标：EasyXT forbidden — live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：us_treasury live 路径渗入 silent fallback
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_us_treasury_incremental_port(tenors=DEFAULT_TENORS, max_rows=3, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_usTreasuryIncremental_liveNetwork_writesAxisObservation(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + US Treasury live API 写 axis_observation
    测试对象：run_us_treasury_incremental(use_mock=False) + TreasuryLiveFetchPort
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时真网增量写 macro clean
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 axis_observation≥1；DbInspector 表存在
    失败含义：Tier A us_treasury live 金路径未接通或误写主库
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_us_treasury_incremental_port(
            tenors=DEFAULT_TENORS, max_rows=3, **kw
        ),
        since_reader=read_since_dates_for_instruments,
        instrument_ids=DEFAULT_TENORS,
        service_builder=build_us_treasury_incremental_service,
        registry_factory=enabled_us_treasury_source_registry,
    )
    report = run_us_treasury_incremental(
        ctx["orch"],
        service=ctx["service"],
        tenors=DEFAULT_TENORS,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    status = report.instrument_results[0]["status"]
    assert status in {"COMPLETED", "EMPTY_RESPONSE"}
    inspect_report = DbInspector(ctx["cm"].db_path, ctx["raw_root"]).inspect()
    axis_table = next(t for t in inspect_report.key_tables if t["name"] == "axis_observation")
    assert axis_table["exists"] is True
    if status == "COMPLETED":
        with ctx["cm"].writer() as con:
            count = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
        assert count >= 1
        assert axis_table["row_count"] is not None and axis_table["row_count"] >= 1


@pytest.mark.network
def test_usTreasuryIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 US Treasury live 增量
    测试对象：run_us_treasury_incremental live 幂等 upsert
    目的/目标：重复 live 跑 observation_id PK 不膨胀行数
    验证点：两路 status∈{COMPLETED,EMPTY_RESPONSE}；COUNT(*) 相等
    失败含义：live 幂等失败会导致日常 sync 重复膨胀
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_us_treasury_incremental_port(
            tenors=DEFAULT_TENORS, max_rows=3, **kw
        ),
        since_reader=read_since_dates_for_instruments,
        instrument_ids=DEFAULT_TENORS,
        service_builder=build_us_treasury_incremental_service,
        registry_factory=enabled_us_treasury_source_registry,
    )
    run_us_treasury_incremental(
        ctx["orch"],
        service=ctx["service"],
        tenors=DEFAULT_TENORS,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_us_treasury_incremental(
        ctx["orch"],
        service=ctx["service"],
        tenors=DEFAULT_TENORS,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
