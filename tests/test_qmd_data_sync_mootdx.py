"""R3-DCP-05 S08 — qmd data sync mootdx incremental CLI tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.cli import data_commands, main
from backend.app.cli.errors import CliFailure
from backend.app.config import PROJECT_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard


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
    with pytest.raises(CliFailure, match="operator|production DB"):
        data_commands.sync_mootdx_incremental(dry_run=False, end="2024-06-25")


def test_qmdData_syncMootdx_operatorAuthRequired(monkeypatch, non_sandbox_data_root: Path) -> None:
    """覆盖范围：mootdx 真跑 operator / sandbox 双门禁
    测试对象：sync_mootdx_incremental dry_run=False
    目的/目标：非 .audit-sandbox 的 DATA_ROOT 须 USER_AUTH_REQUIRED
    验证点：tmp_path 直设（无 .audit-sandbox）抛 CliFailure
    失败含义：mootdx 绕过 operator 确认会破坏 R3F-CLI-01 契约
    """
    data_root = non_sandbox_data_root
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure, match="operator"):
        data_commands.sync_mootdx_incremental(dry_run=False, end="2024-06-25")


def test_qmdData_syncMootdx_rejectsUserLiveAuditPath(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：mootdx 真跑拒绝 user-live 类生产 audit 路径
    测试对象：sync_mootdx_incremental dry_run=False
    目的/目标：与 baostock/fred sandbox guard 一致；user-live 不得被增量 sync 写入
    验证点：QMD_DATA_ROOT=.audit-sandbox/user-live → CliFailure INVALID_INPUT
    失败含义：类生产路径可被 mootdx 增量污染
    """
    data_root = tmp_path / ".audit-sandbox" / "user-live"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc_info:
        data_commands.sync_mootdx_incremental(dry_run=False, end="2024-06-25")
    assert exc_info.value.error_code == "INVALID_INPUT"
    assert "user-live" in exc_info.value.message


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
