"""Trellis Plan 协议 v2 校验器测试。

覆盖范围：validate_plan_freeze、validate_plan_phase 与 plan freeze warning 对任务目录的机械门禁。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from common.validate_plan_freeze import (  # noqa: E402
    _load_plan_paths,
    validate_plan_freeze,
    validate_plan_freeze_warnings,
    validate_plan_phase,
)


def _minimal_master(task_dir: Path) -> None:
    task_card = (
        "015_implement_data_quality_validator.md + 016_implement_source_conflict_validator.md"
    )
    (task_dir / "MASTER.plan.md").write_text(
        f"## 0.\n原计划任务: {task_card}\n"
        "## 1.\n### 1.3 原计划归并\n"
        "### 1.5 停止条件\n"
        "| # | 条件 | 动作 |\n"
        "| 5 | 自定义：AC 未全绿不得 handoff | 停止并回 Plan |\n"
        "## 8.\n### 8.0\n| RED 命令 | x |\n| GREEN 命令 | x |\n"
        "| RED 证据 | x |\n| GREEN 证据 | x |\n| 已执行 | [ ] |\n",
        encoding="utf-8",
    )
    (task_dir / "AUDIT.plan.md").write_text("# audit\nno placeholders\n", encoding="utf-8")
    dq_task = (
        "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/"
        "015_implement_data_quality_validator.md"
    )
    sc_task = (
        "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/"
        "016_implement_source_conflict_validator.md"
    )
    impl_lines = [
        '{"file": "MASTER.plan.md"}',
        '{"file": "docs/implementation_tasks/README.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md"}',
        f'{{"file": "{dq_task}"}}',
        f'{{"file": "{sc_task}"}}',
    ]
    (task_dir / "implement.jsonl").write_text("\n".join(impl_lines) + "\n", encoding="utf-8")
    freeze = task_dir / "plan.freeze.md"
    freeze.write_text("## 3.\n### 3.0b 原计划包门禁\n- [x] all done\n", encoding="utf-8")


def _plan_boot_artifacts(task_dir: Path) -> None:
    research = task_dir / "research"
    research.mkdir(parents=True, exist_ok=True)
    (research / "plan-boot.md").write_text("原计划已读\nPhase P0 complete\n", encoding="utf-8")
    (research / "project-overview.md").write_text("# overview\n", encoding="utf-8")
    (research / "original-plan-trace.md").write_text(
        "# Original Plan Trace\n## 任务卡清单\n015\n016\n", encoding="utf-8"
    )
    (research / "gitnexus-summary.md").write_text("# summary\n", encoding="utf-8")
    (research / "grill-me-session.md").write_text("# grill\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text(
        "\n".join(
            [
                '{"phase":"boot","skill":"agent-toolchain"}',
                '{"phase":"boot","skill":"trellis-plan"}',
                '{"phase":"1a","skill":"gitnexus-plan-1a"}',
                '{"phase":"1b","skill":"gitnexus-plan-1b"}',
                '{"phase":"2a","skill":"trellis-brainstorm"}',
                '{"phase":"2b","skill":"spec-driven-development"}',
                '{"phase":"3","skill":"grill-me"}',
                '{"phase":"3.5","skill":"to-issues"}',
                '{"phase":"5a","skill":"planning-and-task-breakdown"}',
                '{"phase":"5b","skill":"writing-plans"}',
                '{"phase":"5c","skill":"trellis-before-dev"}',
                '{"phase":"5d","skill":"doubt-driven-development"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (task_dir / "prd.md").write_text("# prd\n", encoding="utf-8")


def test_validatePlanFreeze_failsWithoutBoot(tmp_path: Path) -> None:
    """覆盖范围：缺 plan-boot 时的 freeze 失败
    测试对象：validate_plan_freeze（仅 _minimal_master）
    目的/目标：P0 boot 工件缺失必须阻断 freeze
    验证点：errors 含 plan-boot
    失败含义：未 boot 即可 freeze 会导致 Plan 协议形同虚设
    """
    _minimal_master(tmp_path)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("plan-boot" in e for e in errors)


def test_validatePlanFreeze_failsWithoutOriginalPlanTrace(tmp_path: Path) -> None:
    """覆盖范围：缺 original-plan-trace 时的 freeze 失败
    测试对象：validate_plan_freeze（有 plan-boot 无 trace）
    目的/目标：原计划追溯文档为 freeze 硬性要求
    验证点：errors 含 original-plan-trace
    失败含义：无 trace 无法证明 §2 AC 与原任务卡对齐
    """
    _minimal_master(tmp_path)
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-boot.md").write_text("Phase P0 complete\n", encoding="utf-8")
    (research / "project-overview.md").write_text("# ov\n", encoding="utf-8")
    (research / "gitnexus-summary.md").write_text("# gnx\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text('{"skill":"trellis-plan"}\n', encoding="utf-8")
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("original-plan-trace" in e for e in errors)


def test_validatePlanFreeze_doesNotRequireGlobalOriginalTaskRulesInImplementJsonl(
    tmp_path: Path,
) -> None:
    """覆盖范围：implement.jsonl 不必重复列 GLOBAL_* 规则文件
    测试对象：validate_plan_freeze（implement 仅 MASTER.plan.md）
    目的/目标：全局规则由 boot 读取，不应在 implement 重复强制
    验证点：errors 不含 GLOBAL_EXECUTION_RULES
    失败含义：误强制 GLOBAL 条目会增加 implement 维护负担且无安全收益
    """
    _minimal_master(tmp_path)
    (tmp_path / "implement.jsonl").write_text('{"file": "MASTER.plan.md"}\n', encoding="utf-8")
    _plan_boot_artifacts(tmp_path)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert not any("GLOBAL_EXECUTION_RULES" in e for e in errors)


def test_validatePlanFreeze_requiresCustomStopCondition(tmp_path: Path) -> None:
    """覆盖范围：MASTER §1.5 自定义停止条件
    测试对象：validate_plan_freeze（仅模板示例行 1–4）
    目的/目标：freeze 须至少一行 #≥5 或「自定义」停止条件，防抄示例
    验证点：errors 含 §1.5
    失败含义：无自定义停止条件会导致计划冻结后无退出策略
    """
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)
    (tmp_path / "task.json").write_text(
        '{"meta":{"task_track":"simple"}}', encoding="utf-8"
    )
    (tmp_path / "MASTER.plan.md").write_text(
        "## 0.\n原计划任务: 015\n## 1.\n### 1.3 原计划归并\n"
        "### 1.5 停止条件\n"
        "| # | 条件 | 动作 |\n"
        "| 1 | 示例 | x |\n"
        "| 2 | 示例 | x |\n"
        "| 3 | 示例 | x |\n"
        "| 4 | 示例 | x |\n"
        "## 8.\n### 8.0\n| RED 命令 | x |\n",
        encoding="utf-8",
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("§1.5" in e for e in errors)


def test_validatePlanFreeze_passesWithArtifacts(tmp_path: Path) -> None:
    """覆盖范围：齐备 Plan 工件时的 freeze 通过
    测试对象：validate_plan_freeze（_minimal_master + _plan_boot_artifacts + simple）
    目的/目标：标准 simple 任务在工件齐全时应零错误 freeze
    验证点：errors == []
    失败含义：合规任务无法 freeze 会阻断 Trellis Plan 主流程
    """
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)
    (tmp_path / "task.json").write_text(
        '{"meta":{"task_track":"simple"}}', encoding="utf-8"
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert errors == []


def test_validatePlanFreeze_loopVersionRequiresContextPack(tmp_path: Path) -> None:
    """覆盖范围：complex 轨道 freeze 自动生成 context_pack
    测试对象：validate_plan_freeze（task_track=complex）
    目的/目标：freeze 时须调用 context_router 写出 context_pack.json
    验证点：context_pack.json 存在；errors 不含 missing context_pack
    失败含义：complex 无 context_pack 会导致 loop 单轨上下文缺失
    """
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)

    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"task_track": "complex"}}),
        encoding="utf-8",
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert (tmp_path / "context_pack.json").is_file()
    assert not any("missing context_pack" in e for e in errors)


def test_validatePlanFreeze_debtLiteSkipsContextPack(tmp_path: Path) -> None:
    """覆盖范围：debt-lite 轨道跳过 loop 四件套
    测试对象：validate_plan_freeze（task_track=debt-lite）
    目的/目标：Phase 8D 轻量切片不应生成 context_pack 也不应报错
    验证点：无 context_pack.json；errors 不含 context_pack
    失败含义：debt-lite 误走 loop 会增加 Repair 切片成本
    """
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)

    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"task_track": "debt-lite"}}),
        encoding="utf-8",
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert not (tmp_path / "context_pack.json").is_file()
    assert not any("context_pack" in e for e in errors)


def test_validatePlanFreeze_rejectsDeprecatedLoopMeta(tmp_path: Path) -> None:
    """覆盖范围：废弃 loop_engineering_* meta 字段
    测试对象：validate_plan_freeze（loop_engineering_exempt=True）
    目的/目标：R1 后强制 task_track，拒绝旧双轨 flag 回流
    验证点：errors 含 deprecated meta.loop_engineering
    失败含义：旧 flag 复活会导致 loop 与 Trellis 双轨配置
    """
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)

    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"loop_engineering_exempt": True}}),
        encoding="utf-8",
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("deprecated meta.loop_engineering" in e for e in errors)


def test_validatePlanFreezeWarnings_flagsAuthorityGraphGap(tmp_path: Path) -> None:
    """覆盖范围：freeze 非阻塞 authority_graph 缺口 warning
    测试对象：validate_plan_freeze_warnings（MASTER 引用未收录 backend 路径）
    目的/目标：R3 以 warning 提示扩图，不拦 freeze
    验证点：warnings 含 authority_graph gap
    失败含义：无 warning 会静默遗漏新模块 authority 映射
    """
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)
    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"task_track": "complex"}}),
        encoding="utf-8",
    )
    (tmp_path / "MASTER.plan.md").write_text(
        "backend/app/brand_new_module/foo.py\n## 8.\n", encoding="utf-8"
    )
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
    assert "gitnexus-plan-1a" in cfg.get("freeze_required_skills", [])
    assert "gitnexus-plan-1b" in cfg.get("freeze_required_skills", [])


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
