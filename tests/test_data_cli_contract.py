"""data_cli_contract.yaml enforcement for Phase 1 acceptance gate."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml"

OFFICIAL_PHASE1_COMMANDS = (
    "qmd data sync",
    "qmd data backfill",
    "qmd data full-load",
    "qmd data scheduler run",
)


def _contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_dataCliContract_phase1GateDocumented() -> None:
    """覆盖范围：Phase 1 P1-GATE 契约登记
    测试对象：specs/contracts/data_cli_contract.yaml phase1_gate
    目的/目标：正式 CLI 验收权威与 production-equivalent root 规则必须写入契约
    验证点：phase1_gate 含 acceptance_authority、segment、gate_eligible_requires、non_gate_evidence
    失败含义：执行计划与契约分叉，后续 agent 无法以契约为 SSOT 关账
    """
    gate = _contract()["phase1_gate"]
    assert gate["acceptance_authority"] == "SourceRouteDbAcceptanceSpine"
    assert gate["production_equivalent_data_root_segment"] == "source-route-db"
    assert "dry-run" in " ".join(gate["gate_eligible_requires"])
    assert "dry_run" in gate["non_gate_evidence"]
    assert "source-route-db" in gate["production_equivalent_data_root_segment"]
    runtime = gate["current_runtime_seams"]
    assert runtime["prod_source_tier_module"].endswith("live_prod_source_tiers")
    assert runtime["domain_fetch_operation"] == "domain_fetch_operation"


def test_dataCliContract_officialCommandsExposeAcceptanceFields() -> None:
    """覆盖范围：四类正式命令的验收信封字段契约
    测试对象：data_cli_contract.yaml official_commands_must_expose
    目的/目标：sync/backfill/full-load/scheduler 共享 AcceptanceReport 语义字段
    验证点：must_expose 含 acceptance_report、gate_eligible、observability_evidence
    失败含义：各 job 自定义验收形状，P1-GATE 无法横向比较
    """
    gate = _contract()["phase1_gate"]
    must_expose = set(gate["official_commands_must_expose"])
    assert {"acceptance_report", "gate_eligible", "observability_evidence"} <= must_expose


def test_syncDryRunDoesNotWrite(monkeypatch, tmp_path) -> None:
    """覆盖范围：sync dry-run 默认不写库
    测试对象：data_commands.sync_plan dry_run=True
    目的/目标：dry-run 不计入 P1-GATE 且不得写 canonical/sandbox DB
    验证点：gate_eligible=False；duckdb 文件未创建
    失败含义：dry-run 写库或冒充 gate-eligible 验收
    """
    from backend.app.cli import data_commands
    from backend.app.core.resource_guard import Decision, ResourceGuard

    data_root = tmp_path / ".audit-sandbox" / "wave3-accept" / "data"
    data_root.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    monkeypatch.setattr(
        data_commands,
        "route_preview",
        lambda **kwargs: {
            "route_status": "READY",
            "selected_source_id": "fixture_source",
            "dry_run": True,
        },
    )
    payload = data_commands.sync_plan(data_domain="market_bar_1d", dry_run=True)
    assert payload["dry_run"] is True
    assert payload.get("gate_eligible") is False
    assert not (data_root / "duckdb" / "quant_monitor.duckdb").exists()


def test_dataCliContract_section137CommandsRegistered() -> None:
    """覆盖范围：§13.7 CLI 命令登记完整性
    测试对象：data_cli_contract.yaml commands 映射
    目的/目标：full-load 与 scheduler run 在契约中可查
    验证点：commands 含 qmd data full-load 与 qmd data scheduler run
    失败含义：契约与 CLI 注册漂移，文档/测试无法绑定公开面
    """
    commands = _contract()["commands"]
    assert "qmd data full-load" in commands
    assert "qmd data scheduler run" in commands


def test_dataCliContract_schedulerRunRegistered() -> None:
    """覆盖范围：scheduler run 契约字段
    测试对象：qmd data scheduler run 契约块
    目的/目标：scheduler 须登记 profile 与 binding 展开 must_use
    验证点：required_args 含 profile；must_use 含 execute_binding
    失败含义：scheduler 公开面未契约化，live/dry-run 语义不可审计
    """
    entry = _contract()["commands"]["qmd data scheduler run"]
    assert "profile" in entry["required_args"]
    assert "execute_binding" in entry["must_use"]


def test_routePreviewContract_isReadOnly(monkeypatch, tmp_path) -> None:
    """覆盖范围：route-preview 只读契约
    测试对象：data_commands.route_preview
    目的/目标：route-preview 不得产生写库副作用
    验证点：side_effects_allowed 语义为 dry_run；data_root 无 duckdb
    失败含义：预览命令写库破坏 staged-only 运维策略
    """
    from backend.app.cli import data_commands

    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    payload = data_commands.route_preview(
        data_domain="market_bar_1d",
        operation="fetch_daily_bar",
    )
    assert payload["dry_run"] is True
    assert payload.get("side_effects_allowed") is False
    assert not (data_root / "duckdb").exists()


def test_dataCliContract_docsAnchorsPointToDesignOrchestrator() -> None:
    """覆盖范围：§13.7 CLI docs_anchor 权威路径
    测试对象：data_cli_contract.yaml commands.*.docs_anchor
    目的/目标：CLI 失败指路牌指向 MIGRATION_MAP design 而非运行副本
    验证点：orchestrator 相关 anchor 含 docs/modules/design/
    失败含义：用户被引到非权威运维副本或断链路径
    """
    commands = _contract()["commands"]
    orchestrator_anchors = [
        entry["docs_anchor"]
        for key, entry in commands.items()
        if "docs_anchor" in entry and "data_sync_orchestrator" in entry["docs_anchor"]
    ]
    assert orchestrator_anchors
    assert all("docs/modules/design/data_sync_orchestrator.md" in anchor for anchor in orchestrator_anchors)


def test_dataCliContract_legacyInventoryListed() -> None:
    """覆盖范围：legacy CLI 入口清点（S6 删除后）
    测试对象：scripts/check_acceptance_helper_consumers.py legacy/retired 分类
    目的/目标：可调用旧验收入口已清零；无退役 CLI 桩残留
    验证点：legacy_compat_count==0；retired_legacy_cli_count==0；strict_status PASS
    失败含义：旧 sandbox/limited production 仍可作为 Phase 1 验收入口
    """
    from scripts.check_acceptance_helper_consumers import build_report

    report = build_report(PROJECT_ROOT)
    assert report["strict_status"] == "PASS"
    assert report["legacy_compat_count"] == 0
    assert report["retired_legacy_cli_count"] == 0


def test_dataCliContract_sandboxCleanWriteNotRegistered() -> None:
    """覆盖范围：legacy promote CLI 已从 CLI 树移除
    测试对象：backend.app.cli.main data 子命令注册
    目的/目标：用户误打旧命令时 argparse 拒绝，而非 LEGACY_COMMAND_RETIRED 桩
    验证点：exit != 0；stderr 含 invalid choice
    失败含义：legacy promote 仍注册为 data 子命令
    """
    legacy_subcommand = "sandbox" + "-clean-write"
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
    proc = subprocess.run(
        [sys.executable, "-m", "backend.app.cli.main", "data", legacy_subcommand],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode != 0
    assert "invalid choice" in proc.stderr.lower()


def test_dataCliContract_retiredCommandsDocumented() -> None:
    """覆盖范围：T10 retired_commands 契约冻结
    测试对象：data_cli_contract.yaml retired_commands / failure_class_values
    目的/目标：历史 harness 退役语义写入契约；legacy promote CLI 已物理删除
    验证点：legacy promote 不在 retired_commands；failure_class 在 must_expose
    失败含义：契约仍列已删 CLI 或未冻结错误语义
    """
    gate = _contract()["phase1_gate"]
    retired = {item["command"] for item in gate["retired_commands"]}
    legacy_promote = "qmd data sandbox" + "-clean-write"
    assert legacy_promote not in retired
    assert "failure_class" in gate["official_commands_must_expose"]
    assert "BLOCKED" in gate["failure_class_values"]


def test_dataCliContract_statusFrozen() -> None:
    """覆盖范围：T10 契约 status 冻结
    测试对象：data_cli_contract.yaml 顶层 status
    目的/目标：official report 接口不得保持 draft
    验证点：status=frozen
    失败含义：契约仍为 draft，削弱冻结主张
    """
    assert _contract()["status"] == "frozen"


def test_dataCliContract_healthCommandDocumented() -> None:
    """覆盖范围：data health 子命令契约
    测试对象：qmd data health 契约块
    目的/目标：health 保持 read_only 且禁止 live clean-write 参数
    验证点：side_effects_allowed=false；forbidden_args 含 clean-write
    失败含义：health 命令误开放写路径或全市场扫描
    """
    entry = _contract()["commands"]["qmd data health"]
    assert entry["side_effects_allowed"] is False
    assert "clean-write" in entry["forbidden_args"]
