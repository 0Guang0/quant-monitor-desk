"""R3-DCP-02 S02-05 — fred macro incremental CLI tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from backend.app.cli.data_commands import sync_plan
from backend.app.cli.errors import CliFailure
from backend.app.core.resource_guard import Decision, ResourceGuard
from tests.contract_gate_support import PROJECT_ROOT
from tests.service_path_support import enable_source_route


def test_fredIncrementalCli_dryRun_includesSourceId(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """覆盖范围：CLI dry-run 旗标契约
    测试对象：sync_plan --domain macro_series --source-id fred
    目的/目标：dry-run 返回 route 预览且含 source_id
    验证点：dry_run==True；data_domain==macro_series；source_id==fred
    失败含义：CLI 旗标与 Plan audit F4 修复后契约不一致
    """
    from backend.app.cli import data_commands

    data_root = tmp_path / ".audit-sandbox" / "wave3-accept" / "data"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = sync_plan(
        data_domain="macro_series",
        source_id="fred",
        dry_run=True,
    )
    assert payload["dry_run"] is True
    assert payload["data_domain"] == "macro_series"
    assert payload.get("source_id") == "fred"


def test_fredIncrementalCli_execute_rejectsWithoutLiveEnv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：真跑须 env-gated product live
    测试对象：sync_plan dry_run=False macro_series/fred
    目的/目标：无 QMD_ALLOW_LIVE_FETCH 时 fail-closed
    验证点：CliFailure error_code == LIVE_FETCH_REJECTED
    失败含义：CLI 可绕过 ProductLiveGate 写库
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(CliFailure) as exc_info:
        sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert exc_info.value.error_code == "LIVE_FETCH_REJECTED"


def test_fredIncrementalCli_execute_rejectsCanonicalDb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：真跑禁止写 canonical 主库
    测试对象：sync_plan dry_run=False 无 audit-sandbox QMD_DATA_ROOT
    目的/目标：operator/sandbox 双门禁 fail-closed，不得 silent 写 data/duckdb
    验证点：CliFailure 为 USER_AUTH_REQUIRED 或 INVALID_INPUT；后者须含 production DB refused
    失败含义：CLI 可 silent 写 canonical quant_monitor.duckdb
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMD_FRED_INCREMENTAL_USE_MOCK", "1")
    monkeypatch.delenv("QMD_DATA_ROOT", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        monkeypatch, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    with pytest.raises(CliFailure) as exc_info:
        sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert exc_info.value.error_code in {"INVALID_INPUT", "USER_AUTH_REQUIRED"}
    if exc_info.value.error_code == "INVALID_INPUT":
        assert "production DB path refused" in exc_info.value.message


def test_fredIncrementalCli_execute_rejectsUserLiveAuditPath(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：fred 真跑拒绝 user-live 类生产 audit 路径
    测试对象：sync_plan dry_run=False + QMD_DATA_ROOT=.audit-sandbox/user-live
    目的/目标：与 baostock 一致；user-live 不得被增量 sync 写入
    验证点：CliFailure INVALID_INPUT 且 message 含 user-live
    失败含义：类生产路径可被 fred 增量污染
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMD_FRED_INCREMENTAL_USE_MOCK", "1")
    user_live = tmp_path / ".audit-sandbox" / "user-live"
    user_live.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(user_live))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        monkeypatch, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    with pytest.raises(CliFailure) as exc_info:
        sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert exc_info.value.error_code == "INVALID_INPUT"
    assert "user-live" in exc_info.value.message


def test_sandboxDbAllowed_permitsAuditSandboxDataRootAtImport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：QMD_DATA_ROOT 指向 .audit-sandbox 隔离库
    测试对象：assert_sandbox_db_allowed
    目的/目标：隔离验收/增量 sync 不得因 DATA_ROOT==目标库而误拒
    验证点：audit-sandbox 下 db 路径 allow；canonical data/ 仍 refuse
    失败含义：Wave3 隔离库真跑 fred/baostock 增量被错误 fail-closed
    """
    from backend.app import config as app_config
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )

    audit_data = tmp_path / ".audit-sandbox" / "wave3-accept" / "data"
    audit_db = audit_data / "duckdb" / "quant_monitor.duckdb"
    audit_db.parent.mkdir(parents=True, exist_ok=True)
    audit_db.write_bytes(b"")
    monkeypatch.setattr(app_config, "DATA_ROOT", audit_data)
    allowed = assert_sandbox_db_allowed(
        audit_db, no_production_mutation=True, allow_isolated_data_root=True
    )
    assert allowed == audit_db.resolve()

    canonical = app_config.PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
    with pytest.raises(RehearsalRunnerError, match="production DB path refused"):
        assert_sandbox_db_allowed(canonical, no_production_mutation=True)


def test_sandboxDbAllowed_rejectsUserLiveEvenWithIsolatedFlag(
    tmp_path: Path,
) -> None:
    """覆盖范围：allow_isolated_data_root 仍拒绝 user-live 类生产路径
    测试对象：assert_sandbox_db_allowed
    目的/目标：运维 user-live 树不得被 fred/baostock 增量 sync 写入
    验证点：.audit-sandbox/user-live 下 db → RehearsalRunnerError
    失败含义：类生产路径可被增量 sync 污染，与 ACC-USER-LIVE-PATH 文档矛盾
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )

    user_live_db = (
        tmp_path / ".audit-sandbox" / "user-live" / "duckdb" / "quant_monitor.duckdb"
    )
    user_live_db.parent.mkdir(parents=True, exist_ok=True)
    user_live_db.write_bytes(b"")
    with pytest.raises(RehearsalRunnerError, match="user-live"):
        assert_sandbox_db_allowed(
            user_live_db,
            no_production_mutation=True,
            allow_isolated_data_root=True,
        )


def test_fredIncrementalCli_execute_mockInTest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：测中真跑（mock）写隔离库
    测试对象：sync_plan dry_run=False + QMD_DATA_ROOT 隔离
    目的/目标：对齐 live-fetch 旗标；隔离库可完成增量
    验证点：dry_run==False；series_results 非空；total_rows_written>=1
    失败含义：CLI 无法触发 fred 增量执行路径
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMD_FRED_INCREMENTAL_USE_MOCK", "1")
    audit_data = tmp_path / ".audit-sandbox" / "wave3-accept" / "data"
    audit_data.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(audit_data))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        monkeypatch, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    payload = sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert payload["dry_run"] is False
    assert payload["source_id"] == "fred"
    assert payload["series_results"]
    assert payload["total_rows_written"] >= 1
    assert payload["overall_status"] == "COMPLETED"


def test_fredIncrementalCli_help_showsSourceIdFlag() -> None:
    """覆盖范围：qmd data sync help 快照
    测试对象：CLI argparse --help
    目的/目标：操作员可见 --domain 与 --source-id（非裸 --source）
    验证点：help 含 --source-id 与 macro_series 示例域
    失败含义：CLI 文档与实现旗标漂移
    """
    proc = subprocess.run(
        [sys.executable, "-m", "backend.app.cli.main", "data", "sync", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--source-id" in proc.stdout
    assert "macro_series" in proc.stdout
