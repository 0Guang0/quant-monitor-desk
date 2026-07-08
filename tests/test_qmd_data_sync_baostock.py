"""R3-DCP-01 — qmd data sync baostock incremental CLI tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.cli import data_commands, main
from backend.app.cli.errors import CliFailure
from backend.app.config import PROJECT_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations


def _sandbox_data_root(tmp_path: Path) -> Path:
    return tmp_path / ".audit-sandbox" / "wave3-accept" / "data"


def test_qmdData_syncBaostock_dryRun_includesWatermarkWindow(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：cn_equity_daily_bar sync dry-run 审计输出
    测试对象：data_commands.sync_baostock_incremental dry_run=True
    目的/目标：dry-run 须暴露 watermark 与 date_start/date_end 窗
    验证点：dry_run=True；window 含精确 date_start/date_end；watermark 字段存在
    失败含义：运维无法审计增量窗即无法安全启用真跑
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_baostock_incremental(
        dry_run=True,
        instrument_id="sh.600519",
        end="2024-06-30",
    )
    assert payload["dry_run"] is True
    assert payload["data_domain"] == "cn_equity_daily_bar"
    assert payload["watermark"] is None
    window = payload["window"]
    assert window["date_start"] == "2024-05-31"
    assert window["date_end"] == "2024-06-30"
    assert payload["clean_table"] == "security_bar_1d"
    assert payload["caught_up"] is False


def test_qmdData_syncBaostock_dryRun_noDbFileCreated(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：dry-run 无副作用（不建库、不 migration）
    测试对象：sync_baostock_incremental dry_run=True
    目的/目标：dry-run 前后隔离目录下不应出现 duckdb 文件
    验证点：duckdb 目录不存在或仍无 quant_monitor.duckdb
    失败含义：dry-run 写库会误导运维并污染 sandbox/canonical
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    data_commands.sync_baostock_incremental(dry_run=True, end="2024-06-30")
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    assert not db.exists()


def test_qmdData_syncBaostock_nonDryRun_requiresSourceRouteDbRoot(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：cn_equity 真跑须 production-equivalent 验收根（T9）
    测试对象：sync_baostock_incremental dry_run=False on generic sandbox
    目的/目标：普通 .audit-sandbox 不再执行 legacy baostock live 写入
    验证点：CliFailure error_code==ISOLATED_ROOT_REQUIRED
    失败含义：旧 sandbox live fallback 仍可写库
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_baostock_incremental(
            dry_run=False,
            instrument_id="sh.600519",
            end="1999-12-31",
            empty_table_lookback_days=30,
        )
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_qmdData_syncBaostock_failedFinal_cliExitNonZero(monkeypatch, tmp_path: Path, capsys) -> None:
    """覆盖范围：非 production-equivalent 真跑 CLI fail-closed（T9）
    测试对象：main.main data sync --no-dry-run on generic sandbox
    目的/目标：不得 silent success；须结构化错误退出
    验证点：rc != 0；stderr 含 ISOLATED_ROOT_REQUIRED
    失败含义：legacy live 路径仍可用或错误未结构化
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    rc = main.main(
        [
            "data",
            "sync",
            "--domain",
            "cn_equity_daily_bar",
            "--no-dry-run",
            "--instrument-id",
            "sh.600519",
            "--end",
            "1999-12-31",
        ]
    )
    assert rc != 0
    err = capsys.readouterr().err
    assert "ISOLATED_ROOT_REQUIRED" in err


def test_qmdData_syncBaostock_nonDryRun_sourceRouteDbBlockedWithoutAuth(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：source-route-db baostock live 缺授权诚实阻断
    测试对象：sync_baostock_incremental dry_run=False on source-route-db root
    目的/目标：正式 phase1 路径产出 BLOCKED acceptance，非 legacy replay 写库
    验证点：gate_eligible=True；failure_class=BLOCKED
    失败含义：baostock live 仍走已退役的 generic sandbox 特化路径
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-baostock"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "0")
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_baostock_incremental(
        dry_run=False,
        instrument_id="sh.600519",
        end="2024-06-25",
        empty_table_lookback_days=30,
    )
    assert payload.get("gate_eligible") is True
    assert payload["acceptance_report"]["failure_class"] == "BLOCKED"


def test_qmdData_syncBaostock_refusesCanonicalDbPath(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：真跑拒绝 canonical 主库路径
    测试对象：sync_baostock_incremental dry_run=False + canonical DATA_ROOT
    目的/目标：未设 source-route-db 时 fail-closed
    验证点：CliFailure ISOLATED_ROOT_REQUIRED
    失败含义：运维误跑会写非隔离验收库
    """
    canonical_root = PROJECT_ROOT / "data"
    monkeypatch.setenv("QMD_DATA_ROOT", str(canonical_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", canonical_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_baostock_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code in {
        "ISOLATED_ROOT_REQUIRED",
        "CANONICAL_MAIN_DB_REJECTED",
    }


def test_qmdData_syncBaostock_operatorAuthRequired(monkeypatch, non_sandbox_data_root: Path) -> None:
    """覆盖范围：cn_equity 真跑须 production-equivalent 验收根
    测试对象：sync_baostock_incremental dry_run=False
    目的/目标：非 source-route-db DATA_ROOT 须 ISOLATED_ROOT_REQUIRED
    验证点：tmp_path 直设抛 CliFailure
    失败含义：cn_equity 仍可在非验收根 live 写库
    """
    data_root = non_sandbox_data_root
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_baostock_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_qmdData_syncBaostock_rejectsUserLiveAuditPath(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：baostock 真跑拒绝 user-live 类生产 audit 路径
    测试对象：sync_baostock_incremental dry_run=False
    目的/目标：require_phase1_data_root 拒绝非 source-route-db 根
    验证点：QMD_DATA_ROOT=.audit-sandbox/user-live → ISOLATED_ROOT_REQUIRED
    失败含义：类生产路径可被 baostock 增量污染
    """
    data_root = tmp_path / ".audit-sandbox" / "user-live"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_baostock_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_qmdData_syncBaostock_invalidInputDates(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：非法 CLI 日期输入
    测试对象：sync_baostock_incremental 日期解析
    目的/目标：坏日期应包装为 CliFailure(INVALID_INPUT) 而非 ValueError
    验证点：end='not-a-date' 与 empty_table_lookback_days=0 均 CliFailure
    失败含义：未包装异常会导致 CLI 非零退出码不可审计
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure, match="invalid end date"):
        data_commands.sync_baostock_incremental(dry_run=True, end="not-a-date")
    with pytest.raises(CliFailure, match="empty_table_lookback_days"):
        data_commands.sync_baostock_incremental(
            dry_run=True,
            end="2024-06-30",
            empty_table_lookback_days=0,
        )


def test_qmdData_syncBaostock_sinceOverridesDateStart(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：since 语义为窗下界覆盖
    测试对象：sync_baostock_incremental since + end
    目的/目标：since 应覆盖 watermark 计算的 date_start，而非充当 end
    验证点：window.date_start == since；date_end 仍由 end 驱动
    失败含义：since/end 语义混乱会导致运维拉错区间
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_baostock_incremental(
        dry_run=True,
        since="2024-06-01",
        end="2024-06-30",
    )
    assert payload["window"]["date_start"] == "2024-06-01"
    assert payload["window"]["date_end"] == "2024-06-30"


def test_qmdData_syncBaostock_caughtUpDryRun(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：caught-up 水位 dry-run 审计
    测试对象：sync_baostock_incremental + 已有 watermark==end
    目的/目标：已追平时 dry-run 应标 caught_up 且倒置窗可审计
    验证点：caught_up=True；date_start > date_end
    失败含义：追平态不可审计会导致重复拉取或误触发 fetch
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        con.execute(
            """
            INSERT INTO security_bar_1d (
                instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
                adjustment_type, source_used, batch_id, quality_flags, created_at
            ) VALUES ('sh.600519', '2024-06-30', 1, 1, 1, 1, NULL, NULL, NULL,
                      'none', 'seed', 'b0', NULL, CURRENT_TIMESTAMP)
            """
        )
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_baostock_incremental(
        dry_run=True,
        instrument_id="sh.600519",
        end="2024-06-30",
    )
    assert payload["caught_up"] is True
    assert payload["window"]["date_start"] == "2024-07-01"
    assert payload["window"]["date_end"] == "2024-06-30"


def test_qmdData_syncPlan_cnEquity_routesToBaostockIncremental(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：sync_plan 对 cn_equity_daily_bar 路由
    测试对象：data_commands.sync_plan
    目的/目标：该 domain 应走 baostock watermark 子路径而非 USER_AUTH_REQUIRED
    验证点：dry-run 返回 baostock 窗字段；非 cn domain 仍挡真跑
    失败含义：路由错误会导致错误域走增量或误放行
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_plan(data_domain="cn_equity_daily_bar", dry_run=True, end="2024-06-30")
    assert payload["window"]["date_end"] == "2024-06-30"
    with pytest.raises(CliFailure, match="explicit operator"):
        data_commands.sync_plan(data_domain="market_bar_1d", dry_run=False)


def test_qmdData_syncCli_instrumentIdPassedToSyncPlan(monkeypatch, tmp_path: Path, capsys) -> None:
    """覆盖范围：main.py sync 子命令 --instrument-id 接线
    测试对象：backend.app.cli.main main() sync 路径
    目的/目标：CLI 应把 --instrument-id 传入 sync_plan/sync_baostock_incremental
    验证点：stdout JSON 含 instrument_id=sz.000001
    失败含义：CLI 缺参则运维只能依赖默认 sh.600519
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    rc = main.main(
        [
            "data",
            "sync",
            "--domain",
            "cn_equity_daily_bar",
            "--instrument-id",
            "sz.000001",
            "--end",
            "2024-06-30",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert '"instrument_id": "sz.000001"' in out


def test_qmdData_syncBaostock_dryRun_productLiveFalseByDefault(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：默认 dry-run 未 opt-in live
    测试对象：sync_baostock_incremental dry_run=True 无 QMD_ALLOW_LIVE_FETCH
    目的/目标：fail-closed 默认 product_live=false（ACC-BAOSTOCK-NO-LIVE 关账前提）
    验证点：payload product_live is False
    失败含义：未 opt-in 即标 live 会误导运维
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_baostock_incremental(dry_run=True, end="2024-06-30")
    assert payload["product_live"] is False


def test_qmdData_syncBaostock_liveOptIn_setsProductLive(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：QMD_ALLOW_LIVE_FETCH=1 时 baostock sync 标 product_live
    测试对象：sync_baostock_incremental dry_run=True + env opt-in
    目的/目标：关 ACC-BAOSTOCK-NO-LIVE — live gate 接线后 payload 应 product_live=true
    验证点：product_live is True；仍 dry-run 不写库
    失败含义：env opt-in 未反映到 sync 审计字段则 live 路径不可运维
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_baostock_incremental(dry_run=True, end="2024-06-30")
    assert payload["product_live"] is True


def test_baostockIncremental_resolveUseMock_liveOptIn(monkeypatch) -> None:
    """覆盖范围：baostock incremental use_mock 解析
    测试对象：resolve_baostock_incremental_use_mock
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 → use_mock=False
    验证点：resolve 返回 False；未设 env 返回 True
    失败含义：live port 永不启用则 ACC-BAOSTOCK-NO-LIVE 未关
    """
    from backend.app.ops.baostock_incremental_run import resolve_baostock_incremental_use_mock

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    assert resolve_baostock_incremental_use_mock() is True
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    assert resolve_baostock_incremental_use_mock() is False
