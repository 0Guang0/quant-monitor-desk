"""R3-DCP-02 S02-03/04 — fred macro incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest

from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_ports.fred_port import FredMockFetchPort
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.fred_incremental_run import (
    macro_staging_rows_from_bundle,
    run_fred_macro_incremental,
)
from backend.app.ops.macro_incremental_common import STAGING_TABLE
from tests.fred_macro_incremental_support import (
    fred_incremental_e2e_ctx,
    insert_axis_observation,
)


@pytest.mark.parametrize("replay", [True], ids=["replay"])
def test_fredIncremental_e2e_replay_writesAxisObservation(
    fred_incremental_e2e_ctx: dict[str, Any], replay: bool
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_fred_macro_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert
    验证点：status==COMPLETED；axis_observation 行数>=1；raw_value==4.25；staging 表在 promote 后仍保留行（orchestrator 不 TRUNCATE）
    失败含义：fred 增量无法走 Sync 金路径写 macro clean
    """
    ctx = fred_incremental_e2e_ctx
    report = run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10",),
        use_mock=True,
        source_registry=ctx["registry"],
    )
    assert report.series_results[0]["status"] == "COMPLETED"
    with ctx["cm"].writer() as con:
        count = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
        assert count >= 1
        row = con.execute(
            "SELECT raw_value FROM axis_observation WHERE indicator_id = 'DGS10' LIMIT 1"
        ).fetchone()
        staging_count = con.execute(f"SELECT COUNT(*) FROM {STAGING_TABLE}").fetchone()[0]
    assert row is not None and float(row[0]) == 4.25
    # A4-P2-04: macro_incremental_common DELETE 仅在下次 fetch 入口；promote 后 staging 残留可观测
    assert staging_count >= 1


def test_fredIncremental_idempotent_secondRun_rowCountStable(
    fred_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次增量跑 row count 不增
    测试对象：run_fred_macro_incremental 幂等 upsert
    目的/目标：重复跑 observation_id PK upsert 不重复插入
    验证点：两次 COMPLETED 后 COUNT(*) 相等
    失败含义：幂等失败，生产重复跑会膨胀行数
    """
    ctx = fred_incremental_e2e_ctx
    run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10",),
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10",),
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
    assert first >= 1


@pytest.mark.skipif(
    not __import__("os").environ.get("FRED_API_KEY"),
    reason="live_smoke requires FRED_API_KEY",
)
def test_fredIncremental_live_smoke_envGated(
    tmp_path, monkeypatch: pytest.MonkeyPatch, fred_incremental_e2e_ctx: dict[str, Any]
) -> None:
    """覆盖范围：env-gated live smoke（有 key 时）
    测试对象：run_fred_macro_incremental use_mock=False
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 + FRED_API_KEY 时可 live fetch
    验证点：COMPLETED 或 EMPTY_RESPONSE（水位已最新）；非 LIVE_FETCH_REJECTED
    失败含义：产品 live 增量路径未接通
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    ctx = fred_incremental_e2e_ctx
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port

    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)
    ctx["service"]._inner._fetch_port = port  # noqa: SLF001
    report = run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10",),
        use_mock=False,
        source_registry=ctx["registry"],
    )
    assert report.series_results[0]["status"] in {"COMPLETED", "EMPTY_RESPONSE"}


def test_fredIncremental_emptyResponse_whenWatermarkCurrent(
    tmp_path, fred_incremental_e2e_ctx: dict[str, Any]
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：macro staging adapter + run_fred_macro_incremental
    目的/目标：since 之后无新观测时不写假行
    验证点：series status==EMPTY_RESPONSE；axis_observation 行数不变
    失败含义：水位追上仍拉取或写入，增量语义错误
    """
    ctx = fred_incremental_e2e_ctx
    today = datetime.now(UTC).date()
    with ctx["cm"].writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-seed",
            indicator_id="DGS10",
            obs_date=today,
        )
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    report = run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10",),
        source_registry=ctx["registry"],
    )
    assert report.series_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before


def test_fredIncremental_multiSeries_bothComplete(
    fred_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：多 series 编排 loop
    测试对象：run_fred_macro_incremental series_ids 双路
    目的/目标：L3 编排对 DGS10 + VIXCLS 均完成增量
    验证点：len(series_results)==2；两路 status==COMPLETED
    失败含义：多 series 编排串扰或只跑首项
    """
    ctx = fred_incremental_e2e_ctx
    report = run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10", "VIXCLS"),
        source_registry=ctx["registry"],
    )
    assert len(report.series_results) == 2
    assert {r["series_id"] for r in report.series_results} == {"DGS10", "VIXCLS"}
    assert all(r["status"] == "COMPLETED" for r in report.series_results)


def test_fredIncremental_partialFailure_surfacesFailedSeries(
    fred_incremental_e2e_ctx: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：单 series fetch 失败时整体 PARTIAL_FAILURE
    测试对象：run_fred_macro_incremental 错误聚合
    目的/目标：部分 series 失败可观测，非无条件 completed
    验证点：overall_status==PARTIAL_FAILURE；失败 series 在 results 中
    失败含义：部分失败静默成功，操作员误判同步完成
    """
    ctx = fred_incremental_e2e_ctx
    port = ctx["port"]
    original = port.fetch_payload

    def _fail_vix(self, req: FetchRequest):
        if req.instrument_id == "VIXCLS":
            raise PortError("NETWORK_ERROR", "simulated VIXCLS outage")
        return original(req)

    monkeypatch.setattr(FredMockFetchPort, "fetch_payload", _fail_vix)
    report = run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10", "VIXCLS"),
        source_registry=ctx["registry"],
    )
    assert report.overall_status == "PARTIAL_FAILURE"
    by_id = {r["series_id"]: r["status"] for r in report.series_results}
    assert by_id["DGS10"] == "COMPLETED"
    assert by_id["VIXCLS"] == "FAILED_FINAL"


def test_fredStaging_skipsObservationsWithoutValue() -> None:
    """覆盖范围：bundle 缺省 value 不写入 0.0
    测试对象：macro_staging_rows_from_bundle
    目的/目标：对齐 fred_port 跳过 '.' / 空 value
    验证点：空 value 观测被 skip；有效行 raw_value 非假零
    失败含义：缺省 value 污染 macro clean 为假 0.0
    """
    bundle = {
        "source_id": "fred",
        "content_hash": "h1",
        "observations": [
            {"series_id": "DGS10", "observation_date": "2026-06-01", "value": "."},
            {"series_id": "DGS10", "observation_date": "2026-06-02", "value": "4.1"},
        ],
    }
    rows = macro_staging_rows_from_bundle(bundle, series_id="DGS10")
    assert len(rows) == 1
    assert rows[0]["raw_value"] == 4.1


def test_fredStagingAdapter_invalidJson_returnsFailed(
    tmp_path, fred_incremental_e2e_ctx: dict[str, Any]
) -> None:
    """覆盖范围：非 JSON evidence payload
    测试对象：FredMacroStagingAdapter.fetch
    目的/目标：JSONDecodeError 包装为 FAILED FetchResult
    验证点：series status 非 COMPLETED；overall_status==FAILED
    失败含义：坏 payload 以未分类异常失败，不可观测
    """
    ctx = fred_incremental_e2e_ctx

    class BadJsonPort(FredMockFetchPort):
        def fetch_payload(self, req: FetchRequest):
            from backend.app.datasources.adapters.fetch_port import FetchPayload

            return FetchPayload(content=b"not-json", file_type="json", row_count=0)

    ctx["service"]._inner._fetch_port = BadJsonPort(series_ids=("DGS10",), max_rows=3)  # noqa: SLF001
    report = run_fred_macro_incremental(
        ctx["orch"],
        service=ctx["service"],
        series_ids=("DGS10",),
        source_registry=ctx["registry"],
    )
    assert report.overall_status == "FAILED"
    assert report.series_results[0]["status"] == "FAILED_FINAL"
