"""R3FR-07 legacy wrapper cleanup — doc redirect and batch-close guardrails."""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT

_PARENT_README = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md"
)
_BATCH_README = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR"
    / "BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md"
)
_IMPL_README = PROJECT_ROOT / "docs/implementation_tasks/README.md"
_INVENTORY_REDIRECT = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR"
    / "BATCH_3FR_REFERENCE_ADOPTION_REFACTOR"
    / "R3FR_01_REFERENCE_INVENTORY_AND_LICENSE_MATRIX.md"
)
_R3FR_06_CARD = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR"
    / "BATCH_3FR_REFERENCE_ADOPTION_REFACTOR"
    / "R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md"
)
_BATCH_MANIFEST = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR"
    / "BATCH_3FR_REFERENCE_ADOPTION_REFACTOR"
    / "BATCH_3FR_TASK_CARD_MANIFEST.md"
)
_GOOD_BUNDLE = PROJECT_ROOT / "tests/fixtures/data_health/good_bundle"

_STALE_HEALTH_PLACEHOLDER = re.compile(
    r"still returns [`']?not_implemented_phase_c[`']?",
    re.IGNORECASE,
)
_STALE_CLI_PLACEHOLDER_WHEEL = re.compile(
    r"CLI [`']?not_implemented_phase_c[`']? placeholder",
    re.IGNORECASE,
)
_DONE_ROW = re.compile(
    r"\|\s*`R3FR-0[67]`\s*\|[^|]*\|\s*\*\*Done\*\*",
    re.IGNORECASE,
)


def _assert_no_stale_health_placeholder(path: Path) -> None:
    body = path.read_text(encoding="utf-8")
    for pattern in (_STALE_HEALTH_PLACEHOLDER, _STALE_CLI_PLACEHOLDER_WHEEL):
        match = pattern.search(body)
        assert match is None, (
            f"{path.relative_to(PROJECT_ROOT)} still claims health_check placeholder: "
            f"{match.group(0) if match else ''}"
        )


@pytest.mark.parametrize(
    "path",
    [_PARENT_README, _BATCH_README, _IMPL_README],
    ids=["parent", "batch", "impl"],
)
def test_round3frReadmes_noStaleHealthCheckPlaceholder(path: Path) -> None:
    """覆盖范围：3F-R 规划 README stale placeholder 清扫（AC-07-01 / A2）
    测试对象：父/batch/impl README 三处入口
    目的/目标：不得仍声称 health_check 为 not_implemented_phase_c placeholder
    验证点：三文件均无 stale placeholder 正则命中
    失败含义：执行者误判 CLI 仍为 placeholder，重复 R3FR-06 工作
    """
    _assert_no_stale_health_placeholder(path)


def test_round3frParentReadme_referencesR3fr06Runtime() -> None:
    """覆盖范围：Round 3F-R 父 README 与 R3FR-06 闭环（AC-07-01）
    测试对象：ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md
    目的/目标：父 README 明确 run_data_health_profile 已交付
    验证点：正文含 run_data_health_profile 与 R3FR-06 字样
    失败含义：父入口未指向已完成的 CLI runtime
    """
    body = _PARENT_README.read_text(encoding="utf-8").lower()
    assert "run_data_health_profile" in body
    assert "r3fr-06" in body


def test_round3frBatchReadme_taskTable_r3fr06And07Done() -> None:
    """覆盖范围：Batch README §1 任务表 done 口径（G1 / AC-07-01）
    测试对象：BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md §1
    目的/目标：R3FR-06/07 表行均为 Done，防表行回退
    验证点：§1 表匹配 R3FR-06 与 R3FR-07 Done 行
    失败含义：manifest 显示完成但批次入口表仍 Pending
    """
    body = _BATCH_README.read_text(encoding="utf-8")
    section = body.split("## 1. Batch tasks", 1)[-1].split("## 2.", 1)[0]
    assert _DONE_ROW.search(section), "R3FR-06 Done row missing from §1 table"
    assert re.search(
        r"\|\s*`R3FR-07`\s*\|[^|]*\|\s*\*\*Done\*\*",
        section,
        re.IGNORECASE,
    ), "R3FR-07 Done row missing from §1 table"


def test_round3frImplReadme_item9ClosedAnd3gNext() -> None:
    """覆盖范围：implementation_tasks 执行顺序（G3 / AC-07-03）
    测试对象：docs/implementation_tasks/README.md 条目 9–10
    目的/目标：条目 9 标明 CLOSED @ R3FR-07；条目 10 为 3G 下一入口
    验证点：条目 9 含 CLOSED @ R3FR-07；当前下一执行入口后为 ROUND_3_SANDBOX_CLEAN_WRITE
    失败含义：全局执行顺序仍指向活跃 3F-R 或 3G 入口模糊
    """
    body = _IMPL_README.read_text(encoding="utf-8")
    item9 = body.split("9. `ROUND_3_REFERENCE_ADOPTION_REFACTOR/`", 1)[-1].split(
        "10.", 1
    )[0]
    assert "closed" in item9.lower()
    assert "r3fr-07" in item9.lower()
    assert "当前下一执行入口" in body
    assert "ROUND_3_SANDBOX_CLEAN_WRITE" in body.split("当前下一执行入口", 1)[-1]


def test_r3fr06Card_hasRedirectHeader() -> None:
    """覆盖范围：R3FR-06 历史卡 redirect 头注（G2 / ADV-07-R3）
    测试对象：R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md 顶部
    目的/目标：已完成卡有 Done/redirect 头，正文保留 traceability
    验证点：头注含 Done 与 run_data_health_profile canonical 指引
    失败含义：历史卡仍像可执行工单，误导重复实现
    """
    body = _R3FR_06_CARD.read_text(encoding="utf-8")
    head = body.split("---", 1)[0].lower()
    assert "done" in head
    assert "run_data_health_profile" in head
    assert "do not re-implement" in head or "historical" in head


def test_batch3frManifest_allTasksDone() -> None:
    """覆盖范围：BATCH_3FR_TASK_CARD_MANIFEST DONE 表（G7）
    测试对象：BATCH_3FR_TASK_CARD_MANIFEST.md §1
    目的/目标：R3FR-01..07 均在 manifest 标为 Done
    验证点：§1 表每行 R3FR-0x 均含 Done
    失败含义：manifest 与 batch close 叙事不一致
    """
    body = _BATCH_MANIFEST.read_text(encoding="utf-8")
    section = body.split("## 1. Task summary", 1)[-1].split("## 2.", 1)[0]
    for task_id in ("01", "02", "03", "04", "05", "06", "07"):
        row = next(
            (line for line in section.splitlines() if f"`R3FR-{task_id}`" in line),
            "",
        )
        assert row, f"R3FR-{task_id} row missing from manifest"
        assert "done" in row.lower(), f"R3FR-{task_id} not marked Done in manifest"


def test_inventoryRedirectCard_intact() -> None:
    """覆盖范围：R3FR-01 inventory redirect 卡（AC-07-08）
    测试对象：R3FR_01_REFERENCE_INVENTORY_AND_LICENSE_MATRIX.md
    目的/目标：中央 inventory 卡仍 redirect，guardrails 治理边界不被 cleanup 破坏
    验证点：含 redirected / do not implement；禁止 executable inventory 依赖
    失败含义：cleanup 误删或弱化 inventory redirect，复活中央 SSOT 风险
    """
    assert _INVENTORY_REDIRECT.is_file(), "inventory redirect card missing"
    body = _INVENTORY_REDIRECT.read_text(encoding="utf-8").lower()
    assert "redirected" in body
    assert "do not implement" in body
    assert "reference_adoption_inventory.md" in body


def test_checkDailyBars_canonicalRedirectDoc() -> None:
    """覆盖范围：data health evidence-path shim redirect（AC-07-02 / G5）
    测试对象：backend.app.ops.data_health.check_daily_bars
    目的/目标：薄 wrapper 文档指向 canonical profile runtime
    验证点：docstring 同时含 run_data_health_profile 与 canonical/market_bar_p0
    失败含义：证据路径 shim 无 redirect，执行者继续在旧函数上堆逻辑
    """
    from backend.app.ops import data_health

    doc = (inspect.getdoc(data_health.check_daily_bars) or "").lower()
    assert "run_data_health_profile" in doc
    assert "market_bar_p0" in doc or "data_health_profiles" in doc
    assert "canonical" in doc


def test_healthCheck_canonicalRedirectDoc() -> None:
    """覆盖范围：qmd data health CLI redirect（AC-07-02 / G5）
    测试对象：backend.app.cli.data_commands.health_check
    目的/目标：CLI 入口文档指向 run_data_health_profile
    验证点：docstring 含 run_data_health_profile 与 data_health_profiles
    失败含义：CLI 看起来像独立实现，偏离 data_cli_contract must_use
    """
    from backend.app.cli import data_commands

    doc = inspect.getdoc(data_commands.health_check) or ""
    assert "run_data_health_profile" in doc
    assert "data_health_profiles" in doc


def test_tdxProbePort_delegateDoc() -> None:
    """覆盖范围：TDX probe 瘦委托边界（AC-07-02 / G5）
    测试对象：interface_probe_fetch_ports 模块与 TdxPytdxProbeFetchPort
    目的/目标：probe 层文档指向 TdxPytdxFetchPort canonical provider
    验证点：模块与类 doc 均含 delegate 与 TdxPytdxFetchPort
    失败含义：probe 文件被当作 TDX 下载主实现，违背 R3FR-03 边界
    """
    from backend.app.ops import interface_probe_fetch_ports as ports

    module_doc = (inspect.getdoc(ports) or "").lower()
    class_doc = (inspect.getdoc(ports.TdxPytdxProbeFetchPort) or "").lower()
    assert "tdxpytdxfetchport" in module_doc.replace("_", "")
    assert "delegate" in module_doc
    assert "delegate" in class_doc
    assert "tdxpytdxfetchport" in class_doc.replace("_", "")


def test_tdxManualProbe_canonicalRedirectDoc() -> None:
    """覆盖范围：tdx_manual_probe 编排边界 redirect（G4 / A7-005）
    测试对象：backend.app.ops.tdx_manual_probe 模块
    目的/目标：probe 编排文档指向 TdxPytdxProbeFetchPort / TdxPytdxFetchPort
    验证点：模块 docstring 含 canonical 边界与 delegate 字样
    失败含义：manual probe 被当作 provider 主实现
    """
    from backend.app.ops import tdx_manual_probe

    doc = (inspect.getdoc(tdx_manual_probe) or "").lower()
    assert "tdxpytdxprobefetchport" in doc.replace("_", "").replace(" ", "")
    assert "canonical" in doc or "delegate" in doc


def test_akshareValidationPort_sandboxOnlyNotDefaultCli() -> None:
    """覆盖范围：Akshare validation port 沙箱边界（A3-O1）
    测试对象：AkshareSinaDailyValidationFetchPort
    目的/目标：live akshare 能力仅沙箱 validation，非默认 CLI 路径
    验证点：类 doc 含 sandbox/validation-only；data_commands 不引用该类
    失败含义：live 网络面被误当作默认数据路径
    """
    from backend.app.cli import data_commands
    from backend.app.ops import interface_probe_fetch_ports as ports

    doc = (inspect.getdoc(ports.AkshareSinaDailyValidationFetchPort) or "").lower()
    assert "sandbox" in doc or "validation" in doc
    assert "not" in doc and ("default" in doc or "cli" in doc)
    cli_src = inspect.getsource(data_commands)
    assert "AkshareSinaDailyValidationFetchPort" not in cli_src


def test_ac0706_healthCheck_behaviorRegressionOnGoodBundle() -> None:
    """覆盖范围：AC-07-06 §5 行为回归 — health CLI（G6）
    测试对象：data_commands.health_check on good_bundle
    目的/目标：cleanup 后 CLI 仍委托 profile runner 并返回合法信封
    验证点：status 为 PASS/WARN；must_use 字段齐全；无副作用
    失败含义：仅 doc redirect 通过但 runtime 回归
    """
    from backend.app.cli import data_commands

    payload = data_commands.health_check(
        data_domain="market_bar_1d",
        profile="market_bar_p0",
        evidence_dir=_GOOD_BUNDLE,
    )
    assert payload["status"] in {"PASS", "WARN"}
    assert payload["command"] == "health"
    assert payload["dry_run"] is True
    assert payload["side_effects_allowed"] is False
    assert payload["domain"] == "market_bar_1d"
    assert payload["profile"] == "market_bar_p0"
    assert isinstance(payload["rules_run"], list)


def test_roadmapAndHandoff_mark3frClosed() -> None:
    """覆盖范围：3F-R 关门与 3G 下一入口（AC-07-03）
    测试对象：PROJECT_IMPLEMENTATION_ROADMAP.md、docs/ROUND3_HANDOFF.md
    目的/目标：路线图与 handoff 标明 Batch 3F-R CLOSED、Round 3G 为下一入口
    验证点：含 3F-R CLOSED；handoff 无 NEAR CLOSE；下一批次指向 3G
    失败含义：批次关门状态不可审计，3G 门禁仍模糊
    """
    roadmap = (PROJECT_ROOT / "PROJECT_IMPLEMENTATION_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    handoff = (PROJECT_ROOT / "docs/ROUND3_HANDOFF.md").read_text(encoding="utf-8")
    roadmap_lower = roadmap.lower()
    handoff_lower = handoff.lower()

    assert "3f-r" in roadmap_lower and "closed" in roadmap_lower
    assert "3g" in roadmap_lower
    assert "当前下一入口" in roadmap or "下一执行入口" in roadmap
    assert "near close" not in handoff_lower
    assert "3f-r" in handoff_lower and "closed" in handoff_lower
    assert "3g" in handoff_lower


def test_batch3gReadme_preconditionsSatisfied() -> None:
    """覆盖范围：Batch 3G README 前置条件（AC-07-04）
    测试对象：BATCH_3G_SANDBOX_CLEAN_WRITE/README.md §3
    目的/目标：3G 前置引用已完成的 3F-R 产出，不以「被 3F-R 阻塞」为唯一表述
    验证点：含 3F-R complete/satisfied；引用 data health / provider catalog 等闭环
    失败含义：3G 仍显示 blocked-only，执行者不敢开工
    """
    readme = (
        PROJECT_ROOT
        / "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE"
        / "BATCH_3G_SANDBOX_CLEAN_WRITE/README.md"
    )
    body = readme.read_text(encoding="utf-8")
    lowered = body.lower()
    assert "3f-r" in lowered
    assert "complete" in lowered or "satisfied" in lowered or "closed" in lowered
    assert "run_data_health_profile" in lowered or "market_bar_p0" in lowered
    assert "provider catalog" in lowered or "provider_catalog" in lowered
    assert "blocked by round 3f-r" not in lowered


def test_batch3gCoordinator_preconditionWording() -> None:
    """覆盖范围：Batch 3G coordinator 门禁措辞（AC-07-04）
    测试对象：BATCH_3G_COORDINATOR_PLAYBOOK.md §0
    目的/目标：coordinator 承认 3F-R 条件 A 已满足时可启动 3G
    验证点：§0 含 3F-R complete/closed 与 3G 启动条件
    失败含义：coordinator 仍只写 blocked，派工口径与 roadmap 不一致
    """
    playbook = (
        PROJECT_ROOT
        / "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE"
        / "BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_COORDINATOR_PLAYBOOK.md"
    )
    body = playbook.read_text(encoding="utf-8").lower()
    assert "3f-r" in body
    assert "complete" in body or "closed" in body or "condition a" in body
    assert "3g" in body


def test_moduleRating_providerCatalogPostR3fr05() -> None:
    """覆盖范围：MODULE_COMPLETION_RATING provider catalog 评级（AC-07-05 / G5）
    测试对象：MODULE_COMPLETION_RATING.md provider catalog 行
    目的/目标：评级反映 R3FR-05 provider catalog SSOT 已合并
    验证点：provider catalog 段含 provider_catalog.yaml 与 R2_MINIMAL
    失败含义：完成度表仍写 scaffold-only，与 catalog 交付脱节
    """
    rating = (PROJECT_ROOT / "MODULE_COMPLETION_RATING.md").read_text(encoding="utf-8")
    lowered = rating.lower()
    catalog_idx = lowered.find("provider catalog")
    assert catalog_idx >= 0
    section = lowered[catalog_idx : catalog_idx + 800]
    assert "provider_catalog.yaml" in section
    assert "r2_minimal_vertical_slice" in section
    assert "r3fr-05" in section or "r3fr_05" in section


def test_batchImplementationMap_checkpointPost3fr07() -> None:
    """覆盖范围：ROUND3_BATCH_IMPLEMENTATION_MAP checkpoint（AC-07-07）
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md 顶部 checkpoint
    目的/目标：地图 checkpoint 反映 3F-R 关门、3G 为活跃下一批
    验证点：checkpoint 含 3F-R CLOSED；不再写 only R3FR-07 remains
    失败含义：历史地图仍显示 3F-R active，与 roadmap/handoff 冲突
    """
    body = (PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md").read_text(
        encoding="utf-8"
    )
    lowered = body.lower()
    assert "checkpoint" in lowered
    assert "3f-r" in lowered and "closed" in lowered
    assert "3g" in lowered
    assert "only `r3fr-07`" not in lowered and "only r3fr-07" not in lowered
