"""Plan protocol v4：EXECUTION_INDEX 与 manifest 生成测试。

覆盖范围：execution_index 解析/生成与 validate_plan_freeze v4 门禁。
测试对象：generate_manifests、freeze_task_card、validate_plan_freeze（v4 最小任务目录）。
目的/目标：冻结三件套与自动 jsonl 必须与索引 §3 一致。
验证点：implement 首条为 frozen 卡；§3 行进入 implement。
失败含义：Execute 会读到错误 SSOT 或漏读契约原文。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from common.execution_index import (  # noqa: E402
    freeze_task_card,
    generate_manifests,
    parse_manifest_rows,
)
from common.plan_protocol import (  # noqa: E402
    plan_freeze_required_before_start,
    plan_protocol_version,
)
from common.validate_plan_freeze import validate_plan_freeze  # noqa: E402

_SOURCE = (
    "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md"
)


def _v4_minimal(task_dir: Path) -> None:
    research = task_dir / "research"
    research.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.json").write_text(
        json.dumps(
            {
                "meta": {
                    "task_track": "complex",
                    "plan_protocol_version": "4",
                    "source_task_card": _SOURCE,
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (research / "plan-boot.md").write_text(
        "原计划已读\nPhase P0 complete\n", encoding="utf-8"
    )
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"trellis-plan"}\n{"skill":"grill-me"}\n'
        '{"skill":"to-issues"}\n{"skill":"writing-plans"}\n'
        '{"skill":"doubt-driven-development"}\n',
        encoding="utf-8",
    )
    (task_dir / "EXECUTION_INDEX.md").write_text(
        """# Index

P0i：索引完整

## 0. 冻结元数据
| source_card | `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` |

## 1. 步骤与证据
| Step | RED 命令 | GREEN 命令 |
| 9.0 | `true` | `true` |

## 2. AC ↔ 测试 / 验收
| AC | 测试 |
| AC-1 | pytest |

## 3. 必须读原文
| path | manifest | audience | extract | for |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | must-read | execute | policy | Boot |

## 4. 已并入冻结任务卡
| 来源 | 并入 | 摘要 |
| plan-boot | n/a | minimal |

> Execute **不读** `research/*` Plan 草稿（三件套）。

## 5. Audit 追溯集
| frozen | frozen/x.md |
""",
        encoding="utf-8",
    )
    (task_dir / "AUDIT.plan.md").write_text(
        "# Audit\nEXECUTION_INDEX.md trace\nno placeholders\n", encoding="utf-8"
    )
    (task_dir / "plan.freeze.md").write_text(
        "## 3.\n### 3.0v4 协议 v4\n- [x] done\n### 3.0b 原计划包门禁\n",
        encoding="utf-8",
    )
    (research / "plan-consolidation.md").write_text(
        "| plan-boot.md | x | n/a |\nPhase 5e complete\n", encoding="utf-8"
    )
    (task_dir / "prd.md").write_text(
        "<!-- thin-index: true -->\n# T\n\n> frozen/x.md + EXECUTION_INDEX\n",
        encoding="utf-8",
    )
    frozen = task_dir / "frozen"
    frozen.mkdir(exist_ok=True)
    (frozen / "GLOBAL_TASK_TEMPLATE.md").write_text(
        "## 8. 边界\n停止条件\n| 5 | 自定义 | stop |\n## 9. 实现步骤\n### 9.0\n",
        encoding="utf-8",
    )


def test_parseManifestRows_extractsSection3() -> None:
    """覆盖范围：§3 表格解析
    测试对象：parse_manifest_rows
    目的/目标：manifest 行可被 generate_manifests 消费
    验证点：至少一行 GLOBAL_TESTING_POLICY
    失败含义：自动 jsonl 将为空
    """
    text = (
        "## 3. 必须读原文\n| path | manifest | audience |\n"
        "| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | must-read | execute |\n"
    )
    rows = parse_manifest_rows(text)
    assert rows and "GLOBAL_TESTING_POLICY" in rows[0]["path"]


def test_generateManifests_firstEntryIsFrozen(tmp_path: Path) -> None:
    """覆盖范围：implement.jsonl 槽位
    测试对象：generate_manifests
    目的/目标：Boot 第一条必须是 frozen SSOT
    验证点：首行含 frozen/
    失败含义：Execute hook 仍指向 MASTER
    """
    _v4_minimal(tmp_path)
    assert not generate_manifests(tmp_path, _REPO)
    first = (tmp_path / "implement.jsonl").read_text(encoding="utf-8").splitlines()[0]
    assert "frozen/" in first


def test_freezeTaskCard_copiesSource(tmp_path: Path) -> None:
    """覆盖范围：freeze-task-card
    测试对象：freeze_task_card
    目的/目标：从仓库活卡复制到 frozen/
    验证点：frozen 文件存在且含 FROZEN 头
    失败含义：并行改活卡会污染 Execute 口径
    """
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "task.json").write_text(
        json.dumps({"meta": {"source_task_card": _SOURCE}}) + "\n",
        encoding="utf-8",
    )
    (task_dir / "EXECUTION_INDEX.md").write_text(
        "## 0. 冻结元数据\n| source_card | `"
        + _SOURCE
        + "` |\n## 1. 步骤与证据\n| RED | GREEN |\n| x | x |\n## 3. 必须读原文\n| path | manifest | audience |\n",
        encoding="utf-8",
    )
    assert not freeze_task_card(task_dir, _REPO)
    frozen = list((task_dir / "frozen").glob("*.md"))
    assert frozen and "FROZEN" in frozen[0].read_text(encoding="utf-8")


def test_validatePlanFreeze_v4_passesMinimal(tmp_path: Path) -> None:
    """覆盖范围：v4 freeze 门禁（宽松项）
    测试对象：validate_plan_freeze
    目的/目标：最小 v4 目录可通过或仅缺可选 5d 产物
    验证点：不含「missing EXECUTION_INDEX」
    失败含义：v4 协议无法冻结新任务
    """
    _v4_minimal(tmp_path)
    generate_manifests(tmp_path, _REPO)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert not any("missing EXECUTION_INDEX" in e for e in errors)
    assert not any("frozen task card" in e and "missing" in e for e in errors)


def test_planProtocolVersion_prefersV4WhenMasterAndIndex(tmp_path: Path) -> None:
    """覆盖范围：v4/v3 版本启发式
    测试对象：plan_protocol_version
    目的/目标：同目录既有 MASTER 又有 v4 三件套时应判 v4
    验证点：返回 '4'
    失败含义：遗留 MASTER 会让 start/freeze 走错旧协议
    """
    _v4_minimal(tmp_path)
    (tmp_path / "MASTER.plan.md").write_text("## 8.\nlegacy\n", encoding="utf-8")
    assert plan_protocol_version(tmp_path) == "4"


def test_planFreezeRequiredBeforeStart_v4WithoutMaster(tmp_path: Path) -> None:
    """覆盖范围：task.py start 冻结门
    测试对象：plan_freeze_required_before_start
    目的/目标：无 MASTER 的 v4 任务仍须在 planning 时过 validate-plan-freeze
    验证点：返回 True
    失败含义：v4 未冻结即可 start
    """
    _v4_minimal(tmp_path)
    assert plan_freeze_required_before_start(tmp_path)


def test_validateInputInventory_acceptsV4ExecutionIndex(tmp_path: Path) -> None:
    """覆盖范围：P0i 输入清单（v4）
    测试对象：validate_input_inventory
    目的/目标：v4 用 EXECUTION_INDEX 标记索引完整即可
    验证点：errors 为空
    失败含义：v4 被误要求 source-index.md
    """
    from common.manifest_protocol import validate_input_inventory

    _v4_minimal(tmp_path)
    errors: list[str] = []
    validate_input_inventory(tmp_path, errors)
    assert errors == []


def test_validatePlanFreeze_v4_rejectsMissingConsolidation(tmp_path: Path) -> None:
    """覆盖范围：Phase 5e plan-consolidation 机械门
    测试对象：validate_plan_freeze（v4）
    目的/目标：缺 plan-consolidation.md 时冻结失败
    验证点：errors 含 plan-consolidation
    失败含义：research 草稿可散落而仍冻结
    """
    _v4_minimal(tmp_path)
    (tmp_path / "research" / "plan-consolidation.md").unlink()
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("plan-consolidation" in e for e in errors)


def test_validatePlanFreeze_v4_rejectsFatPrd(tmp_path: Path) -> None:
    """覆盖范围：v4 薄 prd 门禁
    测试对象：validate_plan_freeze（v4）
    目的/目标：长 prd 无 frozen/ 引用时冻结失败
    验证点：errors 含 thin index
    失败含义：prd 与 frozen 双 SSOT
    """
    _v4_minimal(tmp_path)
    (tmp_path / "prd.md").write_text("# " + "x\n" * 40, encoding="utf-8")
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("thin index" in e for e in errors)


def test_validatePlanFreeze_v4_triadGate_rejectsPointerOnSpecNotes(tmp_path: Path) -> None:
    """覆盖范围：Phase 5e.1 三件套 Triad gate
    测试对象：validate_plan_freeze（v4）
    目的/目标：可执行决策草稿不得标 pointer
    验证点：errors 含 Triad gate 与 spec-driven
    失败含义：Execute 会漏读契约映射仍被允许冻结
    """
    _v4_minimal(tmp_path)
    research = tmp_path / "research"
    (research / "spec-driven-development-notes.md").write_text("contract map\n", encoding="utf-8")
    (research / "plan-consolidation.md").write_text(
        "| spec-driven-development-notes.md | contract | pointer |\n"
        "Phase 5e complete\n",
        encoding="utf-8",
    )
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("Triad gate" in e and "spec-driven" in e for e in errors)


def test_examplePlanV4_passesValidatePlanFreeze() -> None:
    """覆盖范围：仓库内 v4 样板任务
    测试对象：.trellis/tasks/_example-plan-v4
    目的/目标：参考目录须通过 validate-plan-freeze
    验证点：errors == []
    失败含义：新任务无可靠 v4 样板可复制
    """
    task = _REPO / ".trellis" / "tasks" / "_example-plan-v4"
    errors = validate_plan_freeze(task, _REPO)
    assert errors == []
