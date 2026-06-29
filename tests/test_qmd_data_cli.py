"""B3F-CLI — qmd data CLI, packaging, init_db --sync-registry (R3F-CLI-01..05)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from backend.app.cli import data_commands
from backend.app.cli.errors import CliFailure
from backend.app.core.resource_guard import Decision, ResourceGuard

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = PROJECT_ROOT / "docs/ops/staging_data_e2e_runbook.md"


def _run_qmd_data(*args: str) -> subprocess.CompletedProcess[str]:
    import os

    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "backend.app.cli.main", "data", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_qmdData_routePreview_isReadOnly_json(registry_yaml_fixture: Path, monkeypatch, tmp_path) -> None:
    """覆盖范围：qmd data route-preview 只读输出
    测试对象：backend.app.cli.main route-preview 子命令
    目的/目标：运维可预览 SourceRoutePlan 且不写库
    验证点：exit 0；JSON 含 route_status、side_effects_allowed=false 语义（dry_run）
    失败含义：预览路径若写库会破坏 staged-only 运维策略
    """
    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    proc = _run_qmd_data(
        "route-preview",
        "--domain",
        "market_bar_1d",
        "--operation",
        "fetch_daily_bar",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["dry_run"] is True
    assert payload.get("side_effects_allowed") is False
    assert "route_status" in payload
    assert payload["route_plan"]["data_domain"] == "market_bar_1d"


def test_qmdData_sync_defaultDryRun_printsPlan(monkeypatch) -> None:
    """覆盖范围：qmd data sync 默认 dry-run
    测试对象：backend.app.cli.data_commands.sync_plan
    目的/目标：同步命令默认只规划、不抓取不写库
    验证点：dry_run=true；无 live fetch
    失败含义：默认实写会导致未授权生产同步
    """
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
    assert payload.get("product_live") is False


def test_qmdData_syncWithoutDryRun_failsClosed() -> None:
    """覆盖范围：sync 无 dry-run 时 fail-closed
    测试对象：sync_plan dry_run=False 分支
    目的/目标：禁止默认 live/实写同步
    验证点：抛出 USER_AUTH_REQUIRED
    失败含义：静默允许实写会绕过 R3F-CLI-05 无默认 live 约束
    """
    with pytest.raises(CliFailure) as exc:
        data_commands.sync_plan(data_domain="market_bar_1d", dry_run=False)
    assert exc.value.error_code == "USER_AUTH_REQUIRED"
    assert exc.value.manual_confirmation_required is True


def test_qmdData_cliFailure_exposesErrorCodeAndDocsAnchor(monkeypatch) -> None:
    """覆盖范围：CLI 失败错误码与文档锚点
    测试对象：CliFailure 输出信封
    目的/目标：失败可机械映射到 ERROR_CODE_GUIDE
    验证点：未知 domain 时抛出含 error_code 与 docs_anchor 的 CliFailure
    失败含义：运维无法从 CLI 输出定位修复文档
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc:
        data_commands.sync_plan(data_domain="nonexistent_domain_xyz", dry_run=True)
    assert exc.value.error_code
    assert exc.value.docs_anchor.startswith("docs/")


def test_initDb_syncRegistry_oneLiner(
    tmp_path, monkeypatch, registry_yaml_fixture: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """覆盖范围：init_db --sync-registry 一键初始化
    测试对象：scripts.init_db.main --sync-registry
    目的/目标：闭合 R2-GAP-1 的 CI one-liner
    验证点：stdout 含 sync_registry rows=；source_registry 表有行
    失败含义：新环境仍需手工两步 init+sync，运维易漏 registry
    """
    import scripts.init_db as init_db_mod
    from backend.app.db.connection import ConnectionManager

    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setattr(init_db_mod, "DATA_ROOT", data_root)
    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    init_db_mod.main(["--db", str(db_path), "--sync-registry"])
    out = capsys.readouterr().out
    assert "sync_registry rows=" in out
    cm = ConnectionManager(db_path)
    with cm.reader() as con:
        count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count >= 1


def test_packaging_consoleScripts_smoke(monkeypatch, tmp_path) -> None:
    """覆盖范围：pyproject console_scripts 可导入
    测试对象：qmd-data / qmd-init-db / qmd-sync-registry entrypoints
    目的/目标：R3F-CLI-02/04 打包入口 smoke
    验证点：main 符号可解析；scripts 包无 sys.path.insert
    失败含义：editable install 后运维仍依赖手工 PYTHONPATH
    """
    from backend.app.cli.main import main as data_main
    from scripts.init_db import main as init_main
    from scripts.sync_registry import main as sync_main

    assert callable(data_main)
    assert callable(init_main)
    assert callable(sync_main)
    sync_src = (PROJECT_ROOT / "scripts/sync_registry.py").read_text(encoding="utf-8")
    assert "sys.path.insert" not in sync_src
    ci_src = (PROJECT_ROOT / "scripts/ci_ingestion_smoke.py").read_text(encoding="utf-8")
    assert "sys.path.insert" not in ci_src


def test_initBasic_noDryRun_syncsRegistry(tmp_path, monkeypatch, registry_yaml_fixture: Path) -> None:
    """覆盖范围：qmd data init-basic --no-dry-run 实写路径
    测试对象：backend.app.cli.data_commands.init_basic
    目的/目标：闭合 A7-PLAN-01 — steps 声明 sync_registry 时须真实同步
    验证点：registry_rows≥1；source_registry 表有行
    失败含义：运维误以为 init-basic 已加载 registry 导致路由失败
    """
    from backend.app.db.connection import ConnectionManager

    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    payload = data_commands.init_basic(dry_run=False, db_path=db_path)
    assert payload["registry_rows"] >= 1
    cm = ConnectionManager(db_path)
    with cm.reader() as con:
        count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count >= 1


def test_stagingE2eRunbook_documentsNoDefaultLive() -> None:
    """覆盖范围：R3F-CLI-05 staging E2E runbook
    测试对象：docs/ops/staging_data_e2e_runbook.md
    目的/目标：runbook 声明无默认 live、含 CI one-liner
    验证点：含 no default live；含 qmd-init-db --sync-registry；含 test_qmd_data_cli
    失败含义：授权 live 与 staging runbook 混用会导致误开联网抓取
    """
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "no default live" in text.lower() or "No default live" in text
    assert "qmd-init-db --sync-registry" in text
    assert "test_qmd_data_cli.py" in text
    assert "source_health_snapshot" in text


def test_qmdData_health_supportedProfile_notPlaceholder(
    registry_yaml_fixture: Path, monkeypatch, tmp_path
) -> None:
    """覆盖范围：qmd data health 支持 profile 非 placeholder
    测试对象：backend.app.cli.main health 子命令
    目的/目标：AC-4 — 不得返回 not_implemented_phase_c
    验证点：exit 0；JSON 无 placeholder status
    失败含义：CLI message-only 假完成
    """
    bundle = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"
    proc = _run_qmd_data(
        "health",
        "--domain",
        "market_bar_1d",
        "--profile",
        "market_bar_p0",
        "--evidence-dir",
        str(bundle),
        "--format",
        "json",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload.get("status") != "not_implemented_phase_c"
    assert payload["profile"] == "market_bar_p0"
    assert payload["domain"] == "market_bar_1d"


def test_qmdData_health_invalidProfile_documentedError(tmp_path: Path) -> None:
    """覆盖范围：未知 profile fail-closed
    测试对象：data_commands.health_check
    目的/目标：无效 profile 返回文档化错误
    验证点：CliFailure 含 docs_anchor
    失败含义：未知 profile 静默通过
    """
    bundle = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"
    with pytest.raises(CliFailure) as exc:
        data_commands.health_check(
            data_domain="market_bar_1d",
            profile="unknown_profile_xyz",
            evidence_dir=bundle,
        )
    assert exc.value.docs_anchor.startswith("docs/")
    assert exc.value.error_code == "CAPABILITY_MISSING"


def test_qmdData_health_invokesProfileRunner() -> None:
    """覆盖范围：CLI 调用 profile runner
    测试对象：data_commands.health_check
    目的/目标：rules_run 覆盖九 rule 闭包
    验证点：rules_run 集合等于 market_bar_p0 九 rule ID
    失败含义：CLI 未接全量 profile engine
    """
    from backend.app.ops.data_health_profiles import MARKET_BAR_P0_RULE_IDS

    bundle = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"
    payload = data_commands.health_check(
        data_domain="market_bar_1d",
        profile="market_bar_p0",
        evidence_dir=bundle,
    )
    assert isinstance(payload.get("rules_run"), list)
    assert set(payload["rules_run"]) == set(MARKET_BAR_P0_RULE_IDS)


def test_qmdData_health_noSideEffects() -> None:
    """覆盖范围：health 无副作用
    测试对象：health_check 输出信封
    目的/目标：side_effects_allowed=false；dry_run=true
    验证点：信封字段语义
    失败含义：健康检查触发写库或抓取
    """
    bundle = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"
    payload = data_commands.health_check(
        data_domain="market_bar_1d",
        profile="market_bar_p0",
        evidence_dir=bundle,
    )
    assert payload["dry_run"] is True
    assert payload["side_effects_allowed"] is False


def test_qmdData_health_jsonRequiredFields() -> None:
    """覆盖范围：JSON 信封 R3FR-06 §5
    测试对象：health_check CLI 输出
    目的/目标：AC-5 — 必填字段齐全
    验证点：command/domain/profile/status/rules_run/issue_counts/window/source_ids/hash_coverage/limitations
    失败含义：自动化无法消费健康报告
    """
    bundle = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"
    payload = data_commands.health_check(
        data_domain="market_bar_1d",
        profile="market_bar_p0",
        evidence_dir=bundle,
    )
    for key in (
        "command",
        "dry_run",
        "side_effects_allowed",
        "domain",
        "profile",
        "status",
        "rules_run",
        "issue_counts_by_severity",
        "row_count_checked",
        "window",
        "source_ids",
        "content_hash_coverage",
        "schema_hash_coverage",
        "limitations",
    ):
        assert key in payload, f"missing key: {key}"
    assert payload["command"] == "health"


def test_qmdData_health_defaultWindow_boundedRowCount() -> None:
    """覆盖范围：无 --start/--end 默认窗口
    测试对象：health_check 信封 row_count_checked
    目的/目标：AC-6 — 默认扫描有界（default_window_days + max_rows）
    验证点：row_count_checked ≤ max_rows；window 非空
    失败含义：无窗口时无界扫描
    """
    bundle = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"
    max_rows = 100
    payload = data_commands.health_check(
        data_domain="market_bar_1d",
        profile="market_bar_p0",
        evidence_dir=bundle,
        max_rows=max_rows,
    )
    assert payload["row_count_checked"] <= max_rows
    assert payload["window"]["start"] or payload["window"]["end"]


def test_qmdData_health_rejectsLiveCleanWriteFullScan() -> None:
    """覆盖范围：禁止 live/clean/full 扫描
    测试对象：health_check forbidden flags
    目的/目标：AC-6 fail-closed
    验证点：allow-network/clean-write/full-market/full-history 均 CliFailure
    失败含义：危险操作可从 health 路径启用
    """
    bundle = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"
    base = dict(
        data_domain="market_bar_1d",
        profile="market_bar_p0",
        evidence_dir=bundle,
    )
    for flag, kwargs in (
        ("allow_network", {"allow_network": True}),
        ("clean_write", {"clean_write": True}),
        ("full_market_scan", {"full_market_scan": True}),
        ("full_history", {"full_history": True}),
    ):
        with pytest.raises(CliFailure, match="not allowed|forbidden"):
            data_commands.health_check(**base, **kwargs)
