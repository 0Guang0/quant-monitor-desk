"""Phase 1 official CLI DataSourceService wiring (Findings.txt slice)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.cli import data_commands
from backend.app.cli.phase1_acceptance import _build_datasource_service
from backend.app.core.resource_guard import Decision, ResourceGuard
from tests.incremental_baostock_support import SYMBOL

START = "2024-06-01"
END = "2024-06-03"


def _write_backfill_replay(path: Path) -> None:
    payload = {
        "schema_version": "cn_market_evidence_v1",
        "source_id": "baostock",
        "data_domain": "cn_equity_daily_bar",
        "bars": [
            {
                "instrument_id": SYMBOL,
                "trade_date": "2024-06-02",
                "open": 1400.0,
                "high": 1410.0,
                "low": 1395.0,
                "close": 1405.0,
                "volume": 1000000,
                "source_used": "baostock",
            }
        ],
        "source_fetch_id": "baostock-replay-wiring",
        "content_hash": "baostock-replay-hash-wiring",
        "as_of_timestamp": "2024-06-02T15:00:00Z",
        "retrieved_at": "2024-06-02T15:00:00Z",
        "trade_date": "2024-06-02",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _patch_baostock_port_only(monkeypatch, replay_path: Path) -> None:
    from backend.app.datasources.fetch_ports.baostock_port import BaostockMockFetchPort
    from backend.app.ops import baostock_incremental_run

    def _build(*, data_root, symbol, job_events, use_mock=None):
        from backend.app.datasources.service import DataSourceService

        port = BaostockMockFetchPort(symbols=(symbol,), max_rows=500, replay_path=replay_path)
        return DataSourceService(data_root=data_root, fetch_port=port, job_events=job_events)

    monkeypatch.setattr(baostock_incremental_run, "build_baostock_incremental_service", _build)


def test_buildDatasourceService_baostockBar_injectsFetchPort(tmp_path: Path) -> None:
    """覆盖范围：phase1 正式 backfill/full-load service 工厂
    测试对象：_build_datasource_service(baostock, cn_equity_daily_bar)
    目的/目标：无 monkeypatch 时 production service 必须带 fetch_port，避免 AdapterConfigurationError
    验证点：staged_fixture_mode=True（fetch_port 已注入、走 incremental 金路径）
    失败含义：正式 CLI backfill/full-load/scheduler 在真网入口崩溃
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-wiring"
    service = _build_datasource_service(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        data_root=data_root,
        operation="fetch_daily_bar",
        instrument_id="sh.600519",
    )
    assert service.staged_fixture_mode is True


def test_buildDatasourceService_fredMacro_usesProductLivePort(tmp_path: Path) -> None:
    """覆盖范围：binding/scheduler 路径 macro service 工厂
    测试对象：_build_datasource_service(fred, macro_series)
    目的/目标：非 baostock 源复用 product live port 工厂而非空 service
    验证点：product_live_mode=True 且 staged_fixture_mode=False
    失败含义：fred binding live backfill/incremental 仍因缺 fetch_port 崩溃
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-wiring-fred"
    service = _build_datasource_service(
        source_id="fred",
        data_domain="macro_series",
        data_root=data_root,
        operation="fetch_macro_series",
    )
    assert service.product_live_mode is True
    assert service.staged_fixture_mode is False


def test_backfillOfficialPath_usesWiredDatasourceServiceWithoutPhase1Patch(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official backfill 不经 patch _build_datasource_service 可完成
    测试对象：backfill_plan --no-dry-run on source-route-db
    目的/目标：仅 mock fetch port 工厂时正式路径仍注入 fetch_port 并产出验收信封
    验证点：无 AdapterConfigurationError；acceptance_report.status=PASS；fetch_log_ids 非空
    失败含义：正式 backfill 仍依赖 monkeypatch _build_datasource_service 才能跑通
    """
    root = tmp_path / ".audit-sandbox" / "source-route-db-bf-official-wiring"
    root.mkdir(parents=True)
    replay = root / "bf_replay.json"
    _write_backfill_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_baostock_port_only(monkeypatch, replay)
    payload = data_commands.backfill_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start=START,
        end=END,
        dry_run=False,
    )
    report = payload["acceptance_report"]
    assert report["status"] == "PASS"
    obs = payload.get("observability_evidence") or {}
    assert obs.get("fetch_log_ids")
