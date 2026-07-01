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


def test_qmdData_syncBaostock_nonDryRun_failedFinalRaisesCliFailure(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：cn_equity replay 真跑无 bar 时 CLI fail-closed
    测试对象：sync_baostock_incremental dry_run=False + 空窗 replay
    目的/目标：orchestrator 返回 FAILED_FINAL 时须抛 CliFailure(SYNC_FAILED)，不得 exit 0
    验证点：end=1999-12-31（fixture 仅 2024-06-25）pytest.raises(CliFailure) 且 error_code==SYNC_FAILED
    失败含义：sync 失败仍 exit 0，运维误判增量成功
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
    err = exc_info.value
    assert err.error_code == "SYNC_FAILED"
    assert err.retryable is True
    assert "FAILED_FINAL" in err.message


def test_qmdData_syncBaostock_failedFinal_cliExitNonZero(monkeypatch, tmp_path: Path, capsys) -> None:
    """覆盖范围：sync 失败时 CLI main 退出码非 0
    测试对象：main.main data sync 路径在 orchestrator FAILED_FINAL 时
    目的/目标：运维通过 exit code 识别 sync 失败，不得 silent success
    验证点：rc != 0；stderr 含 SYNC_FAILED
    失败含义：函数层抛错但 CLI 仍 exit 0，违背 LIVE-BAOSTOCK-SYNC-SILENT-001
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
    assert "SYNC_FAILED" in err


def test_qmdData_syncBaostock_nonDryRun_replaySmoke(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：cn_equity_daily_bar sync replay 真跑 smoke
    测试对象：sync_baostock_incremental dry_run=False（.audit-sandbox 隔离库）
    目的/目标：replay mock 下真跑应 COMPLETED 且写 security_bar_1d
    验证点：job_status==COMPLETED；DB 有 sh.600519 fixture 行
    失败含义：CLI 真跑断链则产品 sync 不可用
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_baostock_incremental(
        dry_run=False,
        instrument_id="sh.600519",
        end="2024-06-25",
        empty_table_lookback_days=30,
    )
    assert payload["dry_run"] is False
    assert payload["job_status"] == "COMPLETED"
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db)
    with cm.reader() as con:
        row = con.execute(
            """
            SELECT COUNT(*) FROM security_bar_1d
            WHERE instrument_id = 'sh.600519' AND trade_date = '2024-06-25'
            """
        ).fetchone()
    assert row is not None and row[0] >= 1


def test_qmdData_syncBaostock_refusesCanonicalDbPath(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：真跑拒绝 canonical 主库路径
    测试对象：sync_baostock_incremental dry_run=False + canonical DATA_ROOT
    目的/目标：未设 sandbox 时不得写 PROJECT_ROOT/data/duckdb
    验证点：CliFailure；消息含 production DB path refused
    失败含义：运维误跑会 silent 写 canonical 主库
    """
    canonical_root = PROJECT_ROOT / "data"
    monkeypatch.setenv("QMD_DATA_ROOT", str(canonical_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", canonical_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure, match="operator|production DB"):
        data_commands.sync_baostock_incremental(dry_run=False, end="2024-06-25")


def test_qmdData_syncBaostock_operatorAuthRequired(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：cn_equity 真跑 operator / sandbox 双门禁
    测试对象：sync_baostock_incremental dry_run=False
    目的/目标：非 .audit-sandbox 的 DATA_ROOT 须 USER_AUTH_REQUIRED
    验证点：tmp_path 直设（无 .audit-sandbox）抛 CliFailure
    失败含义：cn_equity 绕过 operator 确认会破坏 R3F-CLI-01 契约
    """
    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure, match="operator"):
        data_commands.sync_baostock_incremental(dry_run=False, end="2024-06-25")


def test_qmdData_syncBaostock_rejectsUserLiveAuditPath(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：baostock 真跑拒绝 user-live 类生产 audit 路径
    测试对象：sync_baostock_incremental dry_run=False
    目的/目标：与 fred/sandbox guard 一致；user-live 不得被增量 sync 写入
    验证点：QMD_DATA_ROOT=.audit-sandbox/user-live → CliFailure INVALID_INPUT
    失败含义：类生产路径可被 baostock 增量污染
    """
    data_root = tmp_path / ".audit-sandbox" / "user-live"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_baostock_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code == "INVALID_INPUT"
    assert "user-live" in exc_info.value.message


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
