"""R3-DCP-05 S12 — incremental sync ``qmd data sync --source-id`` router tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.cli import data_commands, main
from backend.app.cli.errors import CliFailure
from backend.app.cli.incremental_sync_router import sync_incremental_by_source_id
from backend.app.config import PROJECT_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.sync.incremental_source_registry import (
    iter_incremental_gold_path_sources,
    resolve_incremental_gold_path,
)

ADR028_CLEAN = {
    "baostock": "security_bar_1d",
    "mootdx": "security_bar_1d",
    "fred": "axis_observation",
    "us_treasury": "axis_observation",
    "bis": "axis_observation",
    "world_bank": "axis_observation",
    "cftc_cot": "axis_observation",
    "cninfo": "cn_announcement_clean",
    "sec_edgar": "us_disclosure_clean",
    "alpha_vantage": "security_bar_1d",
    "deribit": "crypto_derivative_clean",
}


def _sandbox_data_root(tmp_path: Path) -> Path:
    return tmp_path / ".audit-sandbox" / "wave3-accept" / "data"


def _enable_source_registry(
    monkeypatch: pytest.MonkeyPatch, source_id: str, data_domain: str
) -> None:
    """Patch SourceRegistry.load — same enable semantics as enabled_source_registry."""
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    real_load = SourceRegistry.load

    def _load(self, path=None) -> None:
        real_load(self, path)
        rec = self.get(source_id)
        object.__setattr__(rec, "is_enabled", True)
        orig = self.get_domain_roles

        def _domain_enabled(domain: str):
            binding = orig(domain)
            if domain != data_domain:
                return binding
            return DomainRoleBinding(
                primary_source_id=source_id,
                validation_source_id=binding.validation_source_id,
                fallback_policy=binding.fallback_policy,
                domain_enabled_by_default=True,
                fallback_source_ids=binding.fallback_source_ids,
            )

        self.get_domain_roles = _domain_enabled  # type: ignore[method-assign]

    monkeypatch.setattr(SourceRegistry, "load", _load)
    monkeypatch.setattr(
        SourceRoutePlanner,
        "_platform_allows",
        lambda self, sid: (True, None),
    )


# R3-DCP-08 Repair closed mootdx validation_only registry drift; no test patch needed.


@pytest.fixture
def sandbox_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    data_root = _sandbox_data_root(tmp_path)
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    return data_root


@pytest.mark.parametrize("source_id", list(iter_incremental_gold_path_sources()))
def test_incrementalSyncRouter_dryRun_allSources_auditableJson(
    sandbox_env: Path, source_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：11 个 Tier A 源 dry-run 路由
    测试对象：sync_incremental_by_source_id dry_run=True
    目的/目标：每源可审计 JSON（source_id、canonical domain、clean 表）
    验证点：dry_run；source_id；data_domain；clean_table；message 含 dry-run
    失败含义：运维无法按 --source-id 统一审计增量计划
    """
    entry = resolve_incremental_gold_path(source_id)
    _enable_source_registry(monkeypatch, source_id, entry.canonical_domain)
    payload = sync_incremental_by_source_id(source_id=source_id, dry_run=True, end="2024-06-30")
    assert payload["command"] == "sync"
    assert payload["dry_run"] is True
    assert payload["source_id"] == source_id
    assert payload["clean_table"] == ADR028_CLEAN[source_id]
    assert payload["data_domain"]
    assert "dry-run" in payload["message"].lower()


def test_incrementalSyncRouter_dryRun_disabledRegistry_failClosed(
    sandbox_env: Path,
) -> None:
    """覆盖范围：registry 默认禁用源 dry-run fail-closed
    测试对象：sync_incremental_by_source_id dry_run=True + 生产 SourceRegistry
    目的/目标：bis 等 enabled_by_default=false 源不得 silent enable 后返回 READY
    验证点：CliFailure DISABLED_SOURCE
    失败含义：dry-run 审计误导运维认为禁用源可跑
    """
    with pytest.raises(CliFailure) as exc_info:
        sync_incremental_by_source_id(source_id="bis", dry_run=True, end="2024-06-30")
    assert exc_info.value.error_code == "DISABLED_SOURCE"


def test_incrementalSyncRouter_dryRun_defaultEnabledSource_noPatch(
    sandbox_env: Path,
) -> None:
    """覆盖范围：生产默认启用源 dry-run 无需 patch registry
    测试对象：sync_incremental_by_source_id source_id=baostock dry_run=True
    目的/目标：与 bis/fred 禁用对照 — baostock enabled_by_default=true 应可直接 dry-run 审计
    验证点：dry_run=True；source_id=baostock；message 含 dry-run
    失败含义：默认启用源 dry-run 仍须 monkeypatch，掩盖生产 posture
    """
    payload = sync_incremental_by_source_id(source_id="baostock", dry_run=True, end="2024-06-30")
    assert payload["dry_run"] is True
    assert payload["source_id"] == "baostock"
    assert "dry-run" in payload["message"].lower()


def test_incrementalSyncRouter_unknownSource_failClosed(sandbox_env: Path) -> None:
    """覆盖范围：非 Tier A source_id 负向
    测试对象：sync_incremental_by_source_id
    目的/目标：未知源 fail-closed
    验证点：CliFailure INVALID_INPUT
    失败含义：任意 source_id 被静默路由会写错 clean 表
    """
    with pytest.raises(CliFailure) as exc_info:
        sync_incremental_by_source_id(source_id="akshare", dry_run=True)
    assert exc_info.value.error_code == "INVALID_INPUT"


@pytest.mark.parametrize("source_id", ["bis", "deribit"])
def test_incrementalSyncRouter_nonDryRun_disabledSources_userAuthRequired(
    sandbox_env: Path, source_id: str
) -> None:
    """覆盖范围：S12 非 production-equivalent 真跑 fail-closed（T9）
    测试对象：sync_incremental_by_source_id dry_run=False
    目的/目标：bis/deribit 等源在非 source-route-db 根上须 ISOLATED_ROOT_REQUIRED
    验证点：CliFailure error_code==ISOLATED_ROOT_REQUIRED
    失败含义：未授权源仍可在普通 sandbox 真跑
    """
    with pytest.raises(CliFailure) as exc_info:
        sync_incremental_by_source_id(source_id=source_id, dry_run=False, end="2024-06-30")
    assert exc_info.value.error_code == "ISOLATED_ROOT_REQUIRED"


def test_incrementalSyncRouter_syncPlan_delegatesWhenSourceIdSet(
    sandbox_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：sync_plan 与 --source-id 集成
    测试对象：data_commands.sync_plan(source_id=...)
    目的/目标：CLI 主路径经 incremental sync 路由器
    验证点：mootdx dry-run 返回 source_id=mootdx
    失败含义：main 仍只认 --domain 旧路径，S12 路由未接通
    """
    _enable_source_registry(monkeypatch, "mootdx", "cn_equity_daily_bar")
    payload = data_commands.sync_plan(
        data_domain="cn_equity_daily_bar",
        source_id="mootdx",
        dry_run=True,
        end="2024-06-30",
    )
    assert payload["source_id"] == "mootdx"
    assert payload["dry_run"] is True


def test_incrementalSyncRouter_cliMain_sourceIdDryRunJson(sandbox_env: Path, capsys) -> None:
    """覆盖范围：qmd data sync CLI 端到端 dry-run
    测试对象：main.main data sync --source-id
    目的/目标：CLI 输出可解析 JSON
    验证点：exit 0；stdout JSON 含 source_id=fred
    失败含义：打包 CLI 与 data_commands 路由分叉
    """
    rc = main.main(
        [
            "data",
            "sync",
            "--source-id",
            "fred",
            "--domain",
            "macro_series",
            "--end",
            "2024-06-30",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source_id"] == "fred"
    assert payload["dry_run"] is True


def test_incrementalSyncRouter_cliMain_unknownSource_exitNonZero(
    sandbox_env: Path, capsys
) -> None:
    """覆盖范围：CLI main 未知 --source-id 退出码非 0
    测试对象：main.main data sync --source-id akshare
    目的/目标：未知 Tier A 源须 INVALID_INPUT 且 rc!=0
    验证点：rc != 0；stderr 含 INVALID_INPUT
    失败含义：CLI 静默成功会误导运维路由状态
    """
    rc = main.main(
        [
            "data",
            "sync",
            "--source-id",
            "akshare",
            "--domain",
            "macro_series",
            "--end",
            "2024-06-30",
        ]
    )
    assert rc != 0
    err = capsys.readouterr().err
    assert "INVALID_INPUT" in err


def test_incrementalSyncRouter_dryRun_nonSandboxDataRoot_failClosed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """覆盖范围：dry-run 拒绝非 .audit-sandbox 的 QMD_DATA_ROOT
    测试对象：sync_incremental_by_source_id dry_run=True
    目的/目标：dry-run 不得读 canonical data/ 水位
    验证点：CliFailure error_code==INVALID_INPUT
    失败含义：运维在 canonical 路径 dry-run 会泄露生产 watermark
    """
    canonical_root = PROJECT_ROOT / "data"
    monkeypatch.setenv("QMD_DATA_ROOT", str(canonical_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", canonical_root)
    with pytest.raises(CliFailure) as exc_info:
        sync_incremental_by_source_id(source_id="fred", dry_run=True, end="2024-06-30")
    assert exc_info.value.error_code == "INVALID_INPUT"


def test_incrementalSyncRouter_dryRun_userLivePath_failClosed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """覆盖范围：dry-run 拒绝 user-live 审计路径
    测试对象：sync_incremental_by_source_id dry_run=True
    目的/目标：与真跑门禁一致，user-live 不得用于 sync 审计
    验证点：CliFailure error_code==INVALID_INPUT；消息含 user-live
    失败含义：user-live dry-run 可读 rehearsal 库误导运维
    """
    data_root = tmp_path / ".audit-sandbox" / "user-live" / "data"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(data_commands, "DATA_ROOT", data_root)
    with pytest.raises(CliFailure) as exc_info:
        sync_incremental_by_source_id(source_id="fred", dry_run=True, end="2024-06-30")
    assert exc_info.value.error_code == "INVALID_INPUT"
    assert "user-live" in exc_info.value.message


def test_incrementalSyncRouter_dryRun_mootdx_selectedSourceId_aligned(
    sandbox_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：mootdx dry-run JSON selected_source_id 对齐 CLI --source-id
    测试对象：sync_incremental_by_source_id source_id=mootdx dry_run=True
    目的/目标：关 ACC-MOOTDX-DRYRUN-ROUTE-001 — dry-run 审计 JSON 须 selected_source_id=mootdx
    验证点：selected_source_id==mootdx；source_id==mootdx；dry_run is True
    失败含义：运维 dry-run 仍显示 baostock primary，explicit mootdx 路由不可审计
    """
    _enable_source_registry(monkeypatch, "mootdx", "cn_equity_daily_bar")
    payload = sync_incremental_by_source_id(source_id="mootdx", dry_run=True, end="2024-06-30")
    assert payload["source_id"] == "mootdx"
    assert payload["selected_source_id"] == "mootdx"
    assert payload["dry_run"] is True


def test_incrementalSyncRouter_dryRun_baostock_resourceGuardPaused_failClosed(
    sandbox_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：baostock dry-run resource guard PAUSE fail-closed
    测试对象：sync_incremental_by_source_id source_id=baostock dry_run=True
    目的/目标：与 macro _dry_run_shell 一致，PAUSE 不得 exit 0
    验证点：CliFailure error_code==RESOURCE_GUARD_PAUSED
    失败含义：guard 暂停时 dry-run 仍成功会误导运维真跑
    """
    monkeypatch.setattr(
        ResourceGuard,
        "check",
        lambda self: (Decision.PAUSE, "disk pressure"),
    )
    with pytest.raises(CliFailure) as exc_info:
        sync_incremental_by_source_id(source_id="baostock", dry_run=True, end="2024-06-30")
    assert exc_info.value.error_code == "RESOURCE_GUARD_PAUSED"
