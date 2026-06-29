"""Trellis Plan 协议校验器测试（v4 单轨 + phase 门禁）。

覆盖范围：validate_plan_freeze、validate_plan_phase 与 freeze warning 对任务目录的机械门禁。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from common.execution_index import generate_manifests  # noqa: E402
from common.validate_plan_freeze import (  # noqa: E402
    _load_plan_paths,
    validate_plan_freeze,
    validate_plan_freeze_warnings,
    validate_plan_phase,
)
from test_execution_index_protocol import _v4_minimal  # noqa: E402


def _legacy_master_only(task_dir: Path) -> None:
    (task_dir / "task.json").write_text(
        '{"meta":{"task_track":"complex","plan_protocol_version":"3"}}\n',
        encoding="utf-8",
    )
    (task_dir / "MASTER.plan.md").write_text("## 8.\nlegacy\n", encoding="utf-8")


def test_validatePlanFreeze_failsWithoutBoot(tmp_path: Path) -> None:
    """覆盖范围：缺 plan-boot 时的 freeze 失败
    测试对象：validate_plan_freeze（v4 最小目录）
    目的/目标：P0 boot 工件缺失必须阻断 freeze
    验证点：errors 含 plan-boot
    失败含义：未 boot 即可 freeze 会导致 Plan 协议形同虚设
    """
    _v4_minimal(tmp_path)
    (tmp_path / "research" / "plan-boot.md").unlink()
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("plan-boot" in e for e in errors)


def test_validatePlanFreeze_failsWithoutPlanConsolidation(tmp_path: Path) -> None:
    """覆盖范围：缺 plan-consolidation 时的 freeze 失败
    测试对象：validate_plan_freeze（v4）
    目的/目标：Phase 5e consolidation 为 v4 freeze 硬性要求
    验证点：errors 含 plan-consolidation
    失败含义：无 consolidation 无法证明 research 草稿已并入 INDEX/frozen
    """
    _v4_minimal(tmp_path)
    (tmp_path / "research" / "plan-consolidation.md").unlink()
    generate_manifests(tmp_path, _REPO)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("plan-consolidation" in e for e in errors)


def test_validatePlanFreeze_rejectsLegacyMasterOnly(tmp_path: Path) -> None:
    """覆盖范围：非归档 v3 MASTER 单轨拒绝
    测试对象：validate_plan_freeze（仅 MASTER.plan.md）
    目的/目标：活跃路径只接受 v4/v4.1，legacy MASTER 须归档
    验证点：errors 含 archive-only 或 v4 要求
    失败含义：v3 MASTER 仍可 freeze 会破坏单轨迁移
    """
    _legacy_master_only(tmp_path)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("v4" in e.lower() or "archive" in e.lower() for e in errors)


def test_validatePlanFreeze_skipsArchivedLegacy(tmp_path: Path) -> None:
    """覆盖范围：归档路径只读跳过 freeze
    测试对象：validate_plan_freeze（路径含 archive/）
    目的/目标：归档 v3 任务不阻断 validate-plan-freeze CLI
    验证点：errors == []
    失败含义：只读归档任务会被新门误伤
    """
    archive_dir = tmp_path / "tasks" / "archive" / "2026-06" / "legacy-task"
    archive_dir.mkdir(parents=True)
    _legacy_master_only(archive_dir)
    assert validate_plan_freeze(archive_dir, _REPO) == []


def test_validatePlanFreeze_passesWithArtifacts() -> None:
    """覆盖范围：齐备 v4 Plan 工件时的 freeze 通过
    测试对象：validate_plan_freeze（_example-plan-v4 样板任务）
    目的/目标：标准 complex 样板在工件齐全时应可通过 freeze（过滤 repo 级门）
    验证点：过滤 repo 前缀后 errors 为空
    失败含义：合规 v4 任务无法 freeze 会阻断 Trellis Plan 主流程
    """
    task = _REPO / ".trellis" / "tasks" / "_example-plan-v4"
    errors = validate_plan_freeze(task, _REPO)
    errors = [e for e in errors if not e.startswith("repo ")]
    assert errors == []


def test_validatePlanFreeze_loopVersionRequiresContextPack(tmp_path: Path) -> None:
    """覆盖范围：complex 轨道 freeze 自动生成 context_pack
    测试对象：validate_plan_freeze（task_track=complex + v4）
    目的/目标：freeze 时须调用 context_router 写出 context_pack.json
    验证点：context_pack.json 存在；errors 不含 missing context_pack
    失败含义：complex 无 context_pack 会导致 loop 单轨上下文缺失
    """
    _v4_minimal(tmp_path)
    generate_manifests(tmp_path, _REPO)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert (tmp_path / "context_pack.json").is_file()
    assert not any("missing context_pack" in e for e in errors)


def test_validatePlanFreeze_debtLiteSkipsContextPack(tmp_path: Path) -> None:
    """覆盖范围：debt-lite 轨道跳过 loop 四件套
    测试对象：validate_plan_freeze（task_track=debt-lite，无 v4 三件套）
    目的/目标：Phase 8D 轻量切片不应生成 context_pack 也不应报错
    验证点：无 context_pack.json；errors 不含 context_pack
    失败含义：debt-lite 误走 loop 会增加 Repair 切片成本
    """
    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"task_track": "debt-lite"}}),
        encoding="utf-8",
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert not (tmp_path / "context_pack.json").is_file()
    assert not any("context_pack" in e for e in errors)


def test_validatePlanFreeze_rejectsDeprecatedLoopMeta(tmp_path: Path) -> None:
    """覆盖范围：废弃 loop_engineering_* meta 字段
    测试对象：validate_plan_freeze（loop_engineering_exempt=True + v4）
    目的/目标：R1 后强制 task_track，拒绝旧双轨 flag 回流
    验证点：errors 含 deprecated meta.loop_engineering
    失败含义：旧 flag 复活会导致 loop 与 Trellis 双轨配置
    """
    _v4_minimal(tmp_path)
    generate_manifests(tmp_path, _REPO)
    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"loop_engineering_exempt": True, "task_track": "complex", "plan_protocol_version": "4"}}),
        encoding="utf-8",
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("deprecated meta.loop_engineering" in e for e in errors)


def test_validatePlanFreezeWarnings_flagsAuthorityGraphGap(tmp_path: Path) -> None:
    """覆盖范围：freeze 非阻塞 authority_graph 缺口 warning
    测试对象：validate_plan_freeze_warnings（INDEX 引用未收录 backend 路径）
    目的/目标：R3 以 warning 提示扩图，不拦 freeze
    验证点：warnings 含 authority_graph gap
    失败含义：无 warning 会静默遗漏新模块 authority 映射
    """
    _v4_minimal(tmp_path)
    index = (tmp_path / "EXECUTION_INDEX.md").read_text(encoding="utf-8")
    (tmp_path / "EXECUTION_INDEX.md").write_text(
        index + "\nbackend/app/brand_new_module/foo.py\n",
        encoding="utf-8",
    )
    generate_manifests(tmp_path, _REPO)
    warnings = validate_plan_freeze_warnings(tmp_path, _REPO)
    assert any("authority_graph gap" in w for w in warnings)


def test_validatePlanPhase_1b_requiresSummary(tmp_path: Path) -> None:
    """覆盖范围：Plan phase 1b 门禁
    测试对象：validate_plan_phase(tmp_path, '1b')
    目的/目标：1b 阶段须已写 gitnexus-summary.md
    验证点：errors 含 gitnexus-summary
    失败含义：缺摘会导致 GitNexus 影响面未在 Plan 留痕
    """
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"gitnexus-plan-1b"}\n', encoding="utf-8"
    )
    errors = validate_plan_phase(tmp_path, "1b", repo_root=_REPO)
    assert any("gitnexus-summary" in e for e in errors)


def test_validatePlanPhase_1b_passes(tmp_path: Path) -> None:
    """覆盖范围：Plan phase 1b 合规通过
    测试对象：validate_plan_phase(tmp_path, '1b')（含 summary 与 skill read）
    目的/目标：工件齐全时 1b 应零错误
    验证点：validate_plan_phase == []
    失败含义：合规 1b 误报会拖慢 Plan 阶段推进
    """
    research = tmp_path / "research"
    research.mkdir()
    (research / "gitnexus-summary.md").write_text("# ok\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"gitnexus-plan-1b"}\n', encoding="utf-8"
    )
    assert validate_plan_phase(tmp_path, "1b", repo_root=_REPO) == []


def test_validatePlanPhase_boot_requiresMarker(tmp_path: Path) -> None:
    """覆盖范围：Plan phase boot 完成标记
    测试对象：validate_plan_phase(tmp_path, 'boot')
    目的/目标：plan-boot.md 须含 Phase P0 complete 标记
    验证点：errors 含 Phase P0 complete
    失败含义：无完成标记会导致 agent 跳过 P0 boot
    """
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-boot.md").write_text("incomplete\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text('{"skill":"trellis-plan"}\n', encoding="utf-8")
    errors = validate_plan_phase(tmp_path, "boot", repo_root=_REPO)
    assert any("Phase P0 complete" in e for e in errors)


def test_loadPlanPaths_parsesPhases() -> None:
    """覆盖范围：plan-skill-paths.yaml 阶段配置加载
    测试对象：_load_plan_paths(_REPO)
    目的/目标：freeze 所需 phase 与 gitnexus-plan skill 须在配置中登记
    验证点：phases 含 1a/1b/5e；freeze_required_skills 含 gitnexus-plan-1a/1b
    失败含义：配置缺 phase 会导致 validate_plan_phase 无法路由
    """
    cfg = _load_plan_paths(_REPO)
    assert "1a" in cfg.get("phases", {})
    assert "1b" in cfg.get("phases", {})
    assert "5e" in cfg.get("phases", {})
    assert "gitnexus-plan-1a" in cfg.get("freeze_required_skills_v41", [])
    assert "gitnexus-plan-1b" in cfg.get("freeze_required_skills_v41", [])
    assert "trellis-research" in cfg.get("freeze_required_skills_v41", [])


def test_planPhaseHelp_lists5e() -> None:
    """覆盖范围：validate-plan-phase CLI phase 列表
    测试对象：plan_phase_help(_REPO)
    目的/目标：CLI help 从 yaml 派生且含 5e
    验证点：返回串含 5e
    失败含义：新增 phase 未出现在 CLI 提示
    """
    from common.validate_plan_freeze import plan_phase_help

    assert "5e" in plan_phase_help(_REPO)


def test_validatePlanPhase_5e_passesExample() -> None:
    """覆盖范围：Plan phase 5e consolidation 门禁
    测试对象：validate_plan_phase（_example-plan-v4）
    目的/目标：样板任务 5e 工件齐全时应零错误
    验证点：errors == []
    失败含义：5e 无法单独校验 consolidation
    """
    task = _REPO / ".trellis" / "tasks" / "_example-plan-v4"
    assert validate_plan_phase(task, "5e", repo_root=_REPO) == []
