"""data_cli_contract.yaml enforcement for Phase 1 acceptance gate."""

from __future__ import annotations

from pathlib import Path

import yaml
import pytest

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
    assert "sandbox-clean-write" in gate["non_gate_evidence"]


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


def test_dataCliContract_legacyInventoryListed() -> None:
    """覆盖范围：legacy CLI 入口清点（T9 退役后）
    测试对象：scripts/check_acceptance_helper_consumers.py legacy/retired 分类
    目的/目标：可调用旧验收入口已清零；退役命令单独登记
    验证点：legacy_compat_count==0；retired_legacy_cli_count>0；strict_status PASS
    失败含义：旧 sandbox/limited production 仍可作为 Phase 1 验收入口
    """
    from scripts.check_acceptance_helper_consumers import build_report

    report = build_report(PROJECT_ROOT)
    assert report["strict_status"] == "PASS"
    assert report["legacy_compat_count"] == 0
    assert report["retired_legacy_cli_count"] >= 0


def test_dataCliContract_sandboxCleanWriteRetired() -> None:
    """覆盖范围：sandbox-clean-write 公开 CLI 退役
    测试对象：raise_retired_legacy_command / main CLI handler
    目的/目标：旧验收入口稳定失败并指向 official source-route-db 命令
    验证点：LEGACY_COMMAND_RETIRED；message 含 source-route-db
    失败含义：用户仍可误用 sandbox-clean-write 作为 Phase 1 验收
    """
    from backend.app.cli.errors import CliFailure
    from backend.app.cli.phase1_acceptance import raise_retired_legacy_command

    with pytest.raises(CliFailure) as exc:
        raise_retired_legacy_command("qmd data sandbox-clean-write", subcommand="promote")
    assert exc.value.error_code == "LEGACY_COMMAND_RETIRED"
    assert "source-route-db" in exc.value.message


def test_dataCliContract_retiredCommandsDocumented() -> None:
    """覆盖范围：T10 retired_commands 契约冻结
    测试对象：data_cli_contract.yaml retired_commands / failure_class_values
    目的/目标：退役命令与统一 failure_class 语义写入契约
    验证点：sandbox-clean-write 在 retired_commands；failure_class 在 must_expose
    失败含义：契约仍列 legacy_commands 或未冻结错误语义
    """
    gate = _contract()["phase1_gate"]
    retired = {item["command"] for item in gate["retired_commands"]}
    assert "qmd data sandbox-clean-write" in retired
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


def test_dataCliContract_limitedProductionEntryRetired() -> None:
    """覆盖范围：limited production 内部入口退役
    测试对象：run_limited_production_entry
    目的/目标：promote 内部模块不可绕过 CLI 退役
    验证点：LEGACY_COMMAND_RETIRED
    失败含义：ops 模块仍可执行 limited production promote
    """
    from backend.app.cli.errors import CliFailure
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        PromoteRequest,
        run_limited_production_entry,
    )

    with pytest.raises(CliFailure) as exc:
        run_limited_production_entry(
            PromoteRequest(
                approval_file=Path("x"),
                audit_decision=Path("y"),
                before_proof=Path("z"),
                after_proof=Path("w"),
                rollback_plan=Path("r"),
            )
        )
    assert exc.value.error_code == "LEGACY_COMMAND_RETIRED"


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
