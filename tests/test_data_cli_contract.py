"""Round 2.6 阶段 B — data CLI 设计与契约门禁测试。

覆盖范围：specs/contracts/data_cli_contract.yaml 与 ERROR_CODE_GUIDE、任务 2 文档交叉引用。
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_CONTRACT = PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml"
ERROR_GUIDE = PROJECT_ROOT / "docs/ops/ERROR_CODE_GUIDE.md"
TASK2_DIR = PROJECT_ROOT / ".trellis/tasks/archive/2026-06/06-19-round2-6-routing-service-gate"
TASK2_MASTER = TASK2_DIR / "MASTER.plan.md"
TASK2_IMPLEMENT = TASK2_DIR / "implement.jsonl"


def _load_contract() -> dict:
    return yaml.safe_load(CLI_CONTRACT.read_text(encoding="utf-8")) or {}


def test_routePreviewContract_isReadOnly() -> None:
    """覆盖范围：qmd data route-preview 命令契约
    测试对象：data_cli_contract.yaml commands['qmd data route-preview']
    目的/目标：路由预览必须只读、无副作用，输出 SourceRoutePlan
    验证点：side_effects_allowed 为 False；output 为 SourceRoutePlan
    失败含义：预览命令若可写库会误触发生产同步
    """
    contract = _load_contract()
    route_preview = contract["commands"]["qmd data route-preview"]
    assert route_preview["side_effects_allowed"] is False
    assert route_preview["output"] == "SourceRoutePlan"


def test_syncDryRunDoesNotWrite() -> None:
    """覆盖范围：qmd data sync 命令契约
    测试对象：data_cli_contract.yaml commands['qmd data sync']
    目的/目标：同步须支持 dry-run 并强制走 ResourceGuard 与 SourceRoutePlan
    验证点：optional_args 含 dry-run；must_use 含 ResourceGuard 与 SourceRoutePlan
    失败含义：缺 dry-run 或护栏会导致未授权写入
    """
    contract = _load_contract()
    sync_cmd = contract["commands"]["qmd data sync"]
    assert "dry-run" in sync_cmd.get("optional_args", [])
    assert "ResourceGuard" in sync_cmd.get("must_use", [])
    assert "SourceRoutePlan" in sync_cmd.get("must_use", [])


def test_initBasic_defaultsToDryRun() -> None:
    """覆盖范围：qmd data init-basic 命令契约
    测试对象：data_cli_contract.yaml commands['qmd data init-basic']
    目的/目标：初始化基础数据默认 dry_run，避免首次运行误写
    验证点：default_mode == 'dry_run'
    失败含义：默认实写会破坏 staged-only 初始化策略
    """
    contract = _load_contract()
    init_cmd = contract["commands"]["qmd data init-basic"]
    assert init_cmd.get("default_mode") == "dry_run"


def test_cliFailure_mustExposeErrorCodeAndDocsAnchor() -> None:
    """覆盖范围：CLI 失败时的错误码与文档锚点
    测试对象：data_cli_contract.yaml rules 与 docs/ops/ERROR_CODE_GUIDE.md
    目的/目标：失败须可机械映射到 error_code 与 docs_anchor
    验证点：rules 中同时含 error_code 与 docs_anchor；指南含 DISABLED_SOURCE
    失败含义：运维无法从退出码定位修复文档
    """
    contract = _load_contract()
    rules = contract.get("rules") or []
    assert any("error_code" in r and "docs_anchor" in r for r in rules)
    guide = ERROR_GUIDE.read_text(encoding="utf-8")
    assert "DISABLED_SOURCE" in guide
    assert "docs_anchor" in guide or "ERROR_CODE" in guide.upper()


def test_productionCli_notYetImplemented_documentedInTask2() -> None:
    """覆盖范围：生产等价 CLI 尚未实现的文档追溯
    测试对象：round2-6-routing-service-gate 任务 MASTER 与 implement.jsonl
    目的/目标：DataSourceService 生产路径须在任务卡与 implement 中登记契约路径
    验证点：MASTER 含 DataSourceService 与 production_equivalent_smoke/016F；implement 引用 data_cli_contract.yaml
    失败含义：生产 CLI 缺口无文档锚点会导致误宣称已上线
    """
    assert TASK2_MASTER.is_file()
    text = TASK2_MASTER.read_text(encoding="utf-8")
    assert "DataSourceService" in text
    assert "production_equivalent_smoke" in text or "016F" in text
    assert (PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml").is_file()
    gate_impl = TASK2_IMPLEMENT.read_text(encoding="utf-8")
    assert "data_cli_contract.yaml" in gate_impl
