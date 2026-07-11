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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """覆盖范围：真跑须 production-equivalent 验收根
    测试对象：sync_plan dry_run=False macro_series/fred
    目的/目标：非 source-route-db live 路径 fail-closed
    验证点：CliFailure error_code == ISOLATED_ROOT_REQUIRED
    失败含义：CLI 仍可在普通 sandbox 执行 legacy live fred 路径
    """
    root = tmp_path / ".audit-sandbox" / "wave3-accept" / "data"
    root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(CliFailure) as exc_info:
        sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_fredIncrementalCli_execute_rejectsCanonicalDb(
    tmp_path: Path,
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
        tmp_path, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    with pytest.raises(CliFailure) as exc_info:
        sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert exc_info.value.error_code in {
        "INVALID_INPUT",
        "USER_AUTH_REQUIRED",
        "CANONICAL_MAIN_DB_REJECTED",
        "ISOLATED_ROOT_REQUIRED",
    }
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
        tmp_path, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    with pytest.raises(CliFailure) as exc_info:
        sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert exc_info.value.error_code in {"INVALID_INPUT", "ISOLATED_ROOT_REQUIRED"}
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
    """覆盖范围：source-route-db live sync 缺授权诚实阻断
    测试对象：sync_plan dry_run=False + production-equivalent root
    目的/目标：正式路径经 phase1 envelope，缺 live 授权时 BLOCKED 非 legacy mock 写库
    验证点：gate_eligible=True；failure_class=BLOCKED；acceptance_report 存在
    失败含义：仍走已退役的 generic sandbox fred mock live 路径
    """
    root = tmp_path / ".audit-sandbox" / "source-route-db-fred"
    root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "0")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        tmp_path, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    payload = sync_plan(data_domain="macro_series", source_id="fred", dry_run=False)
    assert payload.get("gate_eligible") is True
    assert payload["acceptance_report"]["failure_class"] == "BLOCKED"


def test_fredIncrementalCli_syncDefinesSourceIdFlag() -> None:
    """覆盖范围：data sync 子命令 --source-id 旗标存在
    测试对象：CLI argparse sync 子解析器
    目的/目标：操作员可指定 --source-id（非裸 --source）
    验证点：sync 子命令 action 含 --source-id dest=source_id
    失败含义：CLI 旗标与实现漂移，操作员无法指定源
    """
    import argparse

    from backend.app.cli.main import _build_data_parser

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    _build_data_parser(sub)
    data_parser = next(
        action.choices["data"]
        for action in parser._actions
        if hasattr(action, "choices") and action.choices and "data" in action.choices
    )
    sync_parser = next(
        action.choices["sync"]
        for action in data_parser._actions
        if hasattr(action, "choices") and action.choices and "sync" in action.choices
    )
    option_dests = {
        opt.dest for opt in sync_parser._actions if opt.dest not in {None, argparse.SUPPRESS}
    }
    assert "source_id" in option_dests
