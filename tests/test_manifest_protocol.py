"""Trellis manifest 协议 E1–E20 门禁测试。

覆盖范围：common.manifest_protocol 与 validate_plan_freeze 对 Batch D 示例任务的机械校验。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

REPO = PROJECT_ROOT
SCRIPTS = REPO / ".trellis" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from common.manifest_protocol import (  # noqa: E402
    is_negative_implement_path,
    parse_master_section9_paths,
    parse_trace_manifest,
    suggest_implement_context,
    validate_manifest_freeze,
    validate_plan_manifest_audit,
)
from common.validate_plan_freeze import validate_plan_freeze  # noqa: E402

BATCH_D_SLUG = "06-18-round2-batch-d-orchestrator"
BATCH_D = REPO / ".trellis/tasks" / BATCH_D_SLUG
if not BATCH_D.exists():
    BATCH_D = REPO / ".trellis/tasks/archive/2026-06" / BATCH_D_SLUG


def _resolve_task_artifact(rel: str) -> Path | None:
    """Resolve implement.jsonl task artifact paths across active/archive locations."""
    full = REPO / rel
    if full.is_file():
        return full
    if not rel.startswith(".trellis/tasks/"):
        return None
    parts = Path(rel).parts
    if len(parts) < 3:
        return None
    slug = parts[2]
    suffix = Path(*parts[3:]) if len(parts) > 3 else Path()
    candidates = [
        REPO / ".trellis/tasks" / slug / suffix,
        REPO / ".trellis/tasks/archive/2026-06" / slug / suffix,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def test_negative_implement_paths():
    """覆盖范围：implement.jsonl 负向路径判定
    测试对象：is_negative_implement_path
    目的/目标：编排器与 sync_registry 等业务路径应标记为负向；migrate 等允许路径除外
    验证点：orchestrator/sync_registry 为 True；db/migrate 为 False
    失败含义：负向路径误判会导致 manifest 建议错误上下文
    """
    assert is_negative_implement_path("backend/app/sync/orchestrator.py")
    assert is_negative_implement_path("scripts/sync_registry.py")
    assert not is_negative_implement_path("backend/app/db/migrate.py")


def test_parse_trace_manifest_required():
    """覆盖范围：original-plan-trace 解析为 manifest 状态
    测试对象：parse_trace_manifest（Batch D research/original-plan-trace.md）
    目的/目标：设计文档须为 required、延期脚本为 deferred
    验证点：data_sync_orchestrator.md 为 required；sync_registry.py 为 deferred
    失败含义：trace 解析错误会导致 freeze 时缺权威输入
    """
    trace = BATCH_D / "research/original-plan-trace.md"
    manifest = parse_trace_manifest(trace)
    assert manifest.get("docs/modules/data_sync_orchestrator.md") == "required"
    assert manifest.get("scripts/sync_registry.py") == "deferred"


def test_batch_d_suggest_implement_empty():
    """覆盖范围：Batch D implement 上下文建议
    测试对象：suggest_implement_context（Batch D 任务目录）
    目的/目标：已合规任务不应再产生额外 implement 建议
    验证点：suggestions == []
    失败含义：非空建议意味着 manifest 与 implement 仍未对齐
    """
    suggestions = suggest_implement_context(BATCH_D, REPO)
    assert suggestions == []


def test_batch_d_manifest_freeze_passes():
    """覆盖范围：Batch D plan freeze 全量门禁
    测试对象：validate_plan_freeze（Batch D）
    目的/目标：归档示例任务须零错误通过 freeze 校验
    验证点：errors == []
    失败含义：示例任务 freeze 失败会阻断 manifest 协议回归基线
    """
    errors = validate_plan_freeze(BATCH_D, REPO)
    assert errors == [], f"unexpected errors: {errors}"


def test_plan_manifest_audit_present():
    """覆盖范围：Plan manifest audit 钩子
    测试对象：validate_plan_manifest_audit（Batch D）
    目的/目标：审计阶段 manifest 检查须对合规任务无报错
    验证点：errors == []
    失败含义：audit 门禁误报会拦 handoff
    """
    errors: list[str] = []
    validate_plan_manifest_audit(BATCH_D, errors)
    assert errors == []


def test_section9_paths_parsed_from_master():
    """覆盖范围：MASTER §9 测试路径解析
    测试对象：parse_master_section9_paths（Batch D MASTER.plan.md）
    目的/目标：freeze 须能从 MASTER 抽出 sync/batch_d 相关测试路径
    验证点：路径列表含 test_sync_migration.py 或 test_batch_d
    失败含义：§9 解析失败会导致 AC 测试链断裂
    """
    master = (BATCH_D / "MASTER.plan.md").read_text(encoding="utf-8")
    paths = parse_master_section9_paths(master)
    assert any("test_sync_migration.py" in p for p in paths) or any(
        "test_batch_d" in p for p in paths
    )


def test_implement_jsonl_paths_exist():
    """覆盖范围：implement.jsonl 所列文件存在性
    测试对象：Batch D implement.jsonl 每行 file/path
    目的/目标：manifest 引用的仓库与任务内文件必须可解析且存在
    验证点：任务内路径在 BATCH_D 下存在；.trellis/tasks 路径经 _resolve_task_artifact 可定位
    失败含义：幽灵 implement 条目会导致 Execute 读不到权威上下文
    """
    impl = BATCH_D / "implement.jsonl"
    task_prefix = f".trellis/tasks/{BATCH_D_SLUG}/"
    for line in impl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        rel = obj.get("file") or obj.get("path")
        if not rel:
            continue
        if rel.startswith(task_prefix):
            suffix = rel[len(task_prefix) :]
            assert (BATCH_D / suffix).is_file(), rel
            continue
        if rel.startswith(".trellis/tasks/"):
            resolved = _resolve_task_artifact(rel)
            assert resolved is not None and resolved.is_file(), rel
            continue
        assert (REPO / rel).is_file(), rel


def test_batch_d_v3_artifacts():
    """覆盖范围：manifest 协议 v3 工件（input inventory / integration ledger / audit）
    测试对象：validate_input_inventory、validate_integration_ledger、validate_integration_audit
    目的/目标：Batch D 须满足 v3 集成清单与审计字段
    验证点：三校验合并后 errors == []
    失败含义：v3 工件缺失会导致复杂任务 freeze 不可复现
    """
    errors: list[str] = []
    from common.manifest_protocol import (
        validate_input_inventory,
        validate_integration_audit,
        validate_integration_ledger,
    )

    validate_input_inventory(BATCH_D, errors)
    validate_integration_ledger(BATCH_D, REPO, errors)
    validate_integration_audit(BATCH_D, errors)
    assert errors == [], errors


def test_batch_d_manifest_protocol_version():
    """覆盖范围：task.json manifest_protocol_version 元数据
    测试对象：Batch D task.json meta.manifest_protocol_version
    目的/目标：示例任务须声明协议版本 3
    验证点：manifest_protocol_version == '3'
    失败含义：版本字段缺失会导致新旧 manifest 规则混用
    """
    import json

    data = json.loads((BATCH_D / "task.json").read_text(encoding="utf-8"))
    assert data.get("meta", {}).get("manifest_protocol_version") == "3"


def test_batch_d_v7_implement_reasons():
    """覆盖范围：manifest 协议 v7 implement reason 覆盖
    测试对象：validate_implement_reason_coverage（Batch D）
    目的/目标：implement.jsonl 每条须有 reason 覆盖审计要求
    验证点：errors == []
    失败含义：缺 reason 会导致 Execute 无法解释为何读该文件
    """
    from common.manifest_protocol import validate_implement_reason_coverage

    errors: list[str] = []
    validate_implement_reason_coverage(BATCH_D, errors)
    assert errors == [], errors


def test_batch_d_v8_ledger_anchors():
    """覆盖范围：manifest 协议 v8 integration ledger MASTER 锚点
    测试对象：validate_ledger_master_anchors（Batch D）
    目的/目标：集成台账条目须锚定 MASTER 章节
    验证点：errors == []
    失败含义：锚点断裂会导致集成审计无法对照计划
    """
    from common.manifest_protocol import validate_ledger_master_anchors

    errors: list[str] = []
    validate_ledger_master_anchors(BATCH_D, errors)
    assert errors == [], errors


def test_batch_d_v9_integration_ledger_in_implement():
    """覆盖范围：manifest 协议 v9 integration ledger 出现在 implement
    测试对象：validate_integration_ledger_in_implement（Batch D）
    目的/目标：implement.jsonl 须引用 integration ledger
    验证点：errors == []
    失败含义：ledger 未入 implement 会导致 Execute 跳过集成上下文
    """
    from common.manifest_protocol import validate_integration_ledger_in_implement

    errors: list[str] = []
    validate_integration_ledger_in_implement(BATCH_D, errors)
    assert errors == [], errors


def test_validate_manifest_freeze_bundle():
    """覆盖范围：validate_manifest_freeze 捆绑校验
    测试对象：validate_manifest_freeze（Batch D + REPO）
    目的/目标：freeze 时 manifest 全套规则须一次通过
    验证点：errors == []
    失败含义：捆绑校验失败意味着 Plan freeze 与 manifest 协议分叉
    """
    errors: list[str] = []
    validate_manifest_freeze(BATCH_D, REPO, errors)
    assert errors == [], errors
