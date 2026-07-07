"""DCP-05 S04 — BIS incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_ports.bis_port import BisLiveFetchPort, BisMockFetchPort
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.product_live_gate import ProductLiveGateError
from backend.app.ops.db_inspector import DbInspector
from backend.app.ops.bis_incremental_run import (
    build_bis_incremental_service,
    bis_staging_rows_from_bundle,
    create_bis_incremental_port,
    run_bis_incremental,
)
from backend.app.ops.bis_incremental_run import (
    DATA_DOMAIN,
    DEFAULT_COUNTRIES,
    SOURCE_ID,
    enabled_bis_source_registry,
    read_since_dates_for_instruments,
    watermark_start_year,
)
from tests.macro_incremental_support import (
    FIXED_TODAY,
    bootstrap_macro_live_e2e_ctx,
    build_macro_e2e_ctx,
    insert_axis_observation,
)


@pytest.fixture
def bis_incremental_e2e_ctx(tmp_path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    port = create_bis_incremental_port(countries=DEFAULT_COUNTRIES, max_rows=3, use_mock=True)
    return build_macro_e2e_ctx(
        tmp_path,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        fetch_port=port,
        since_reader=read_since_dates_for_instruments,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_bis_incremental_service,
        registry_factory=enabled_bis_source_registry,
    )


def test_bisIncremental_e2e_replay_writesAxisObservation(
    bis_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_bis_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert 到 macro clean
    验证点：status==COMPLETED；axis_observation 行数>=1；indicator_id==US
    失败含义：bis 增量无法走 Sync 金路径写 macro clean
    """
    ctx = bis_incremental_e2e_ctx
    report = run_bis_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = 'US'"
        ).fetchone()[0]
        assert count >= 1
        row = con.execute(
            "SELECT raw_value FROM axis_observation WHERE indicator_id = 'US' LIMIT 1"
        ).fetchone()
    assert row is not None and float(row[0]) == 5.25


def test_bisIncremental_idempotent_secondRun_rowCountStable(
    bis_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次增量跑 row count 不增
    测试对象：run_bis_incremental 幂等 upsert
    目的/目标：重复跑 observation_id PK upsert 不重复插入
    验证点：两次 COMPLETED 后 COUNT(*) 相等
    失败含义：幂等失败，生产重复跑会膨胀行数
    """
    ctx = bis_incremental_e2e_ctx
    run_bis_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_bis_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
    assert first >= 1


def test_bisStagingRows_monthlySinceFilter_usesMonthGrain() -> None:
    """覆盖范围：BIS 月频 staging 与 since 日级窗对齐
    测试对象：bis_staging_rows_from_bundle
    目的/目标：live 冷启动 since 在日月中段时仍保留当月观测（G-01 bis 根因）
    验证点：start_date=2026-03-05 时保留 2026-03-01 月频行
    失败含义：月频被日级 since 误滤光导致 EMPTY_RESPONSE
    """
    bundle = {
        "source_id": "bis",
        "content_hash": "h",
        "schema_hash": "s",
        "observations": [
            {
                "observation_date": "2026-01-01",
                "policy_rate": 1.0,
                "frequency": "monthly",
                "country_code": "US",
            },
            {
                "observation_date": "2026-03-01",
                "policy_rate": 1.2,
                "frequency": "monthly",
                "country_code": "US",
            },
        ],
    }
    rows = bis_staging_rows_from_bundle(
        bundle, instrument_id="US", start_date="2026-03-05"
    )
    assert len(rows) == 1
    pub = rows[0]["publish_timestamp"]
    if isinstance(pub, datetime):
        pub_date = pub.date()
    else:
        pub_date = date.fromisoformat(str(pub)[:10])
    assert pub_date == date(2026, 3, 1)


def test_bisIncremental_emptyResponse_whenWatermarkCurrent(
    bis_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：bis staging adapter + run_bis_incremental
    目的/目标：since 之后无新观测时不写假行
    验证点：status==EMPTY_RESPONSE；axis_observation 行数不变
    失败含义：水位追上仍拉取或写入，增量语义错误
    """
    ctx = bis_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-bis-seed",
            indicator_id="US",
            obs_date=FIXED_TODAY,
        )
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    with patch(
        "backend.app.datasources.fetch_ports.bis_port.datetime",
        wraps=datetime,
    ) as mock_dt:
        mock_dt.now.return_value = datetime.combine(FIXED_TODAY, time(0), tzinfo=UTC)
        report = run_bis_incremental(
            ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
        )
    assert report.instrument_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before


def test_bisLivePort_startPeriod_fromFetchRequestStartTime() -> None:
    """覆盖范围：BIS live port startPeriod 来自 FetchRequest.start_time
    测试对象：BisLiveFetchPort.fetch_payload HTTP URL
    目的/目标：水位年 → API startPeriod query param（仿 fred port 测法）
    验证点：start_time=2023-06-15 → URL 含 startPeriod=2023
    失败含义：live BIS 忽略 start_time，增量窗错误
    """
    port = BisLiveFetchPort(countries=("US",), max_rows=3, data_domain="central_bank_policy")
    captured: dict[str, str] = {}

    def _fake_urlopen(url, timeout=30):
        captured["url"] = url

        class _Resp:
            def read(self):
                return b"REF_AREA,TIME_PERIOD,OBS_VALUE\nUS,2023-01,5.25\n"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return _Resp()

    req = FetchRequest(
        run_id="bis-start-year",
        source_id="bis",
        data_domain="central_bank_policy",
        instrument_id="US",
        start_time="2023-06-15",
    )
    with patch("backend.app.datasources.fetch_ports.bis_port.urllib.request.urlopen", _fake_urlopen):
        port.fetch_payload(req)
    assert "startPeriod=2023" in captured["url"]
    assert watermark_start_year("2023-06-15") == 2023


def test_bisIncremental_resourceGuardPause_doesNotWriteClean(
    bis_incremental_e2e_ctx: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：ResourceGuard PAUSE 时增量 fail-closed
    测试对象：run_bis_incremental + ResourceGuard.check
    目的/目标：PAUSE 时不写入 axis_observation clean 表
    验证点：overall_status!=COMPLETED；axis_observation 行数不变
    失败含义：资源守卫暂停仍写入 clean，增量链未 fail-closed
    """
    ctx = bis_incremental_e2e_ctx
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.PAUSE, "disk pressure"))
    with ctx["cm"].writer() as con:
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    report = run_bis_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    assert report.overall_status != "COMPLETED"
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before


def test_bisIncremental_partialFailure_surfacesFailedInstrument(
    bis_incremental_e2e_ctx: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：单 country fetch 失败时整体 PARTIAL_FAILURE
    测试对象：run_bis_incremental 错误聚合
    目的/目标：部分 instrument 失败可观测，非无条件 COMPLETED
    验证点：overall_status==PARTIAL_FAILURE；US COMPLETED、GB FAILED_FINAL
    失败含义：部分失败静默成功，操作员误判同步完成
    """
    ctx = bis_incremental_e2e_ctx
    port = create_bis_incremental_port(countries=("US", "GB"), max_rows=3, use_mock=True)
    ctx["service"]._inner._fetch_port = port  # noqa: SLF001
    original = port.fetch_payload

    def _fail_gb(self, req: FetchRequest):
        if req.instrument_id == "GB":
            raise PortError("NETWORK_ERROR", "simulated GB outage")
        return original(req)

    monkeypatch.setattr(BisMockFetchPort, "fetch_payload", _fail_gb)
    report = run_bis_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=("US", "GB"),
        source_registry=ctx["registry"],
    )
    assert report.overall_status == "PARTIAL_FAILURE"
    by_id = {r["instrument_id"]: r["status"] for r in report.instrument_results}
    assert by_id["US"] == "COMPLETED"
    assert by_id["GB"] == "FAILED_FINAL"


def test_bisLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 bis live port 阻断
    测试对象：create_bis_incremental_port(use_mock=False)
    目的/目标：EasyXT forbidden — live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：bis live 路径渗入 silent fallback
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_bis_incremental_port(countries=DEFAULT_COUNTRIES, max_rows=3, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_bisIncremental_liveNetwork_writesAxisObservation(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + BIS live API 写 axis_observation
    测试对象：run_bis_incremental(use_mock=False) + BisLiveFetchPort startPeriod 窗
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时真网增量写 macro clean（L2 窗参数）
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 axis_observation≥1；DbInspector 表存在
    失败含义：Tier A bis live 金路径未接通或误写主库
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_bis_incremental_port(
            countries=DEFAULT_COUNTRIES, max_rows=120, **kw
        ),
        since_reader=read_since_dates_for_instruments,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_bis_incremental_service,
        registry_factory=enabled_bis_source_registry,
    )
    report = run_bis_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
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
            count = con.execute(
                "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = 'US'"
            ).fetchone()[0]
        assert count >= 1
        assert axis_table["row_count"] is not None and axis_table["row_count"] >= 1


@pytest.mark.network
def test_bisIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续 BIS live 增量
    测试对象：run_bis_incremental live 幂等 upsert
    目的/目标：重复 live 跑 observation_id PK 不膨胀行数
    验证点：first≥1；两次 COUNT(*) 相等
    失败含义：live upsert 重复膨胀行数
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_bis_incremental_port(
            countries=DEFAULT_COUNTRIES, max_rows=120, **kw
        ),
        since_reader=read_since_dates_for_instruments,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_bis_incremental_service,
        registry_factory=enabled_bis_source_registry,
    )
    run_bis_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    _ = run_bis_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first >= 1
    assert first == second
