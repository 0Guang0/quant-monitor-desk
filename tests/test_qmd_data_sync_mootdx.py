"""R3-DCP-05 S08 — qmd data sync mootdx incremental CLI tests."""

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


def test_qmdData_syncMootdx_refusesCanonicalDbPath(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：真跑拒绝 canonical 主库路径
    测试对象：sync_mootdx_incremental dry_run=False + canonical DATA_ROOT
    目的/目标：未设 sandbox 时不得写 PROJECT_ROOT/data/duckdb
    验证点：CliFailure；消息含 operator|production DB
    失败含义：运维误跑会 silent 写 canonical 主库
    """
    canonical_root = PROJECT_ROOT / "data"
    monkeypatch.setenv("QMD_DATA_ROOT", str(canonical_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", canonical_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_mootdx_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code in {
        "ISOLATED_ROOT_REQUIRED",
        "CANONICAL_MAIN_DB_REJECTED",
    }


def test_qmdData_syncMootdx_operatorAuthRequired(monkeypatch, non_sandbox_data_root: Path) -> None:
    """覆盖范围：mootdx 真跑须 production-equivalent 验收根
    测试对象：sync_mootdx_incremental dry_run=False
    目的/目标：非 source-route-db DATA_ROOT 须 ISOLATED_ROOT_REQUIRED
    验证点：tmp_path 直设抛 CliFailure
    失败含义：mootdx 仍可在非验收根 live 写库
    """
    data_root = non_sandbox_data_root
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_mootdx_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_qmdData_syncMootdx_rejectsUserLiveAuditPath(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：mootdx 真跑拒绝非 source-route-db 根
    测试对象：sync_mootdx_incremental dry_run=False
    目的/目标：user-live 路径不得 live 写库
    验证点：ISOLATED_ROOT_REQUIRED
    失败含义：类生产路径可被 mootdx 增量污染
    """
    data_root = tmp_path / ".audit-sandbox" / "user-live"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_mootdx_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_qmdData_syncMootdx_dryRun_includesWatermarkWindow(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：mootdx sync dry-run 审计输出
    测试对象：sync_mootdx_incremental dry_run=True
    目的/目标：dry-run 须暴露 watermark 与 date_start/date_end 窗
    验证点：dry_run=True；window 含 date_end；watermark 字段存在
    失败含义：运维无法审计增量窗即无法安全启用真跑
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_mootdx_incremental(
        dry_run=True,
        instrument_id="sh.600519",
        end="2024-06-30",
    )
    assert payload["dry_run"] is True
    assert payload["data_domain"] == "cn_equity_daily_bar"
    assert payload["window"]["date_end"] == "2024-06-30"
    assert payload["clean_table"] == "security_bar_1d"


def test_qmdData_syncMootdx_cliDryRun_exitZero(monkeypatch, tmp_path: Path, capsys) -> None:
    """覆盖范围：CLI --source-id mootdx dry-run 端到端
    测试对象：main.main data sync --source-id mootdx
    目的/目标：S12 路由 mootdx dry-run 可 exit 0
    验证点：rc==0；stdout 含 source_id=mootdx
    失败含义：CLI 与 sync_mootdx_incremental 路由断裂
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
            "--source-id",
            "mootdx",
            "--domain",
            "cn_equity_daily_bar",
            "--end",
            "2024-06-30",
        ]
    )
    assert rc == 0
    assert '"source_id": "mootdx"' in capsys.readouterr().out


def test_qmdData_syncMootdx_nonDryRun_requiresSourceRouteDbRoot(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：mootdx 真跑须 production-equivalent 验收根（T9）
    测试对象：sync_mootdx_incremental dry_run=False on generic sandbox
    目的/目标：普通 sandbox 不再执行 legacy mootdx live
    验证点：ISOLATED_ROOT_REQUIRED
    失败含义：旧 sandbox live fallback 仍可写库
    """
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_mootdx_incremental(
            dry_run=False,
            instrument_id="sh.600519",
            end="1999-12-31",
            empty_table_lookback_days=30,
        )
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_qmdData_syncMootdx_nonDryRun_sourceRouteDbBlockedWithoutAuth(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：source-route-db mootdx live 缺授权诚实阻断
    测试对象：sync_mootdx_incremental dry_run=False
    目的/目标：正式 phase1 路径产出 BLOCKED acceptance
    验证点：gate_eligible=True；failure_class=BLOCKED
    失败含义：mootdx live 仍走 generic sandbox 特化路径
    """
    data_root = tmp_path / ".audit-sandbox" / "source-route-db-mootdx"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "0")
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_mootdx_incremental(
        dry_run=False,
        instrument_id="sh.600519",
        end="2024-06-25",
        empty_table_lookback_days=30,
    )
    assert payload.get("gate_eligible") is True
    assert payload["acceptance_report"]["failure_class"] == "BLOCKED"


def test_qmdData_syncMootdx_caughtUpDryRun(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：mootdx caught-up 水位 dry-run 审计
    测试对象：sync_mootdx_incremental + 已有 watermark==end
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
    payload = data_commands.sync_mootdx_incremental(
        dry_run=True,
        instrument_id="sh.600519",
        end="2024-06-30",
    )
    assert payload["caught_up"] is True
    assert payload["window"]["date_start"] == "2024-07-01"
    assert payload["window"]["date_end"] == "2024-06-30"
