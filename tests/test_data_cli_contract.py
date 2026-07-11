"""data_cli_contract — 仅保留正式 CLI 运行时行为测。

YAML/文档/phase1_gate 静态登记与 legacy sandbox-clean-write 移除检查已迁至
phase-scripts/check_data_cli_contract_phase.py（artifact-guard / phase-guard）。
"""

from __future__ import annotations


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
