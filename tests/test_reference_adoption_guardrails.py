"""参考实现采纳护栏：静态扫描 backend/scripts，禁止从外部项目照搬危险模式。"""

from __future__ import annotations

import re

import yaml

from tests.contract_gate_support import (
    FORBIDDEN_REFERENCE_IMPORT_ROOTS,
    FORBIDDEN_TRADING_DEF_NAMES,
    PROJECT_ROOT,
    scan_forbidden_function_defs,
    scan_forbidden_import_roots,
    scan_guardrail_roots_for_patterns,
    scan_sys_path_mutation_with_reference_dir,
)

GUARDRAILS = PROJECT_ROOT / "specs/contracts/reference_adoption_guardrails.yaml"

_GUARDRAILS = yaml.safe_load(GUARDRAILS.read_text(encoding="utf-8")) or {}


def _forbidden_examples(category: str) -> tuple[str, ...]:
    block = (_GUARDRAILS.get("forbidden_adoption") or {}).get(category) or {}
    return tuple(block.get("examples") or [])


def _trading_substring_patterns() -> tuple[str, ...]:
    # ponytail: order/buy/sell via AST def scan; bare tokens false-positive in prose.
    skip = FORBIDDEN_TRADING_DEF_NAMES
    return tuple(p for p in _forbidden_examples("real_trading_or_order_api") if p not in skip)


def test_noTradingApiCopied() -> None:
    """覆盖范围：参考采纳护栏对 backend/scripts 的交易 API 静态扫描
    测试对象：real_trading_or_order_api + 禁止函数名 AST
    目的/目标：确保未从参考项目复制实盘下单/交易 API
    验证点：子串模式与 def order/buy/sell 等均为零命中
    失败含义：backend 或 scripts 出现禁止交易 API，存在误用参考代码风险
    """
    violations = list(scan_guardrail_roots_for_patterns(_trading_substring_patterns()))
    violations.extend(scan_forbidden_function_defs(FORBIDDEN_TRADING_DEF_NAMES))
    assert violations == [], f"forbidden trading API patterns: {violations}"


def test_noAutoLoginCopied() -> None:
    """覆盖范围：参考采纳护栏对 backend/scripts 的全局静态扫描
    测试对象：auto_login_or_captcha 禁止模式列表
    目的/目标：防止照搬自动登录、验证码绕过等不安全认证逻辑
    验证点：scan_guardrail_roots_for_patterns 返回空列表
    失败含义：含自动登录/验证码相关复制代码，安全边界被突破
    """
    patterns = _forbidden_examples("auto_login_or_captcha")
    violations = scan_guardrail_roots_for_patterns(patterns)
    assert violations == [], f"forbidden auto-login/captcha patterns: {violations}"


def test_noSilentFallbackCopied() -> None:
    """覆盖范围：参考采纳护栏对 backend/scripts 的全局静态扫描
    测试对象：silent_fallback 禁止模式列表
    目的/目标：禁止静默降级——出错时必须显式 fail-closed
    验证点：scan_guardrail_roots_for_patterns 返回空列表
    失败含义：存在静默 fallback 模式，故障可能被掩盖
    """
    patterns = _forbidden_examples("silent_fallback")
    violations = scan_guardrail_roots_for_patterns(patterns)
    assert violations == [], f"forbidden silent-fallback patterns: {violations}"


def test_r3fr01GuardrailsYamlContract() -> None:
    """覆盖范围：R3FR-01 全局护栏契约完整机读验收
    测试对象：specs/contracts/reference_adoption_guardrails.yaml
    目的/目标：structure/license_gate/completion_rules 与任务卡 §2 语义一致
    验证点：8 字段 license_gate、3 allowed_use、4 rules、structure 全布尔、status 激活
    失败含义：后续 R3FR-02+ 缺少可审计 gate 或仍沿用 draft/中央 inventory 口径
    """
    rules = _GUARDRAILS.get("structure_rules") or {}
    assert rules.get("task_card_local_reference_details") is True
    assert rules.get("one_task_id_one_task_card") is True
    assert rules.get("executable_reference_details_must_be_task_card_local") is True
    assert rules.get("separate_reference_inventory_may_exist_only_as_non_executable_index") is True
    assert rules.get("planning_map_may_exist_only_as_non_executable_coverage_map") is True
    assert rules.get("planning_map_must_not_replace_task_card_local_details") is True
    assert rules.get("batch3fr_separate_reference_inventory_allowed") is False
    assert rules.get("batch3g_separate_reference_inventory_allowed") is False
    assert _GUARDRAILS.get("status") == "active_round3fr"

    gate = _GUARDRAILS.get("license_gate") or {}
    required = set(gate.get("required_task_card_fields") or [])
    assert required == {
        "reference_project.path",
        "reference_project.license",
        "reference_project.allowed_use",
        "reference_project.qmd_target_files",
        "reference_project.direct_copy_allowed",
        "reference_project.rewrite_required",
        "reference_project.forbidden_semantics",
        "reference_project.attribution_required",
    }
    assert set(gate.get("allowed_use_values") or []) == {
        "direct_adaptation",
        "architecture_only",
        "forbidden_until_review",
    }
    assert len(gate.get("rules") or []) >= 4

    completion = _GUARDRAILS.get("completion_rules") or {}
    assert completion.get("max_implementation_batches_to_full_stable") == 3
    assert completion.get("first_batch_must_be_vertical_slice") is True
    assert completion.get("rating_authority_file") == "MODULE_COMPLETION_RATING.md"
    assert completion.get("design_docs_remain_complete_product_targets") is True


def test_noReferenceProjectRuntimeImport() -> None:
    """覆盖范围：禁止 runtime 耦合参考项目目录或危险 import 根
    测试对象：forbidden_adoption.runtime_import + AST import 根 + sys.path+参考项目
    目的/目标：参考项目仅作设计/改写素材，不是 runtime 包
    验证点：yaml examples、import 根、sys.path 共现扫描均为零
    失败含义：runtime 直接依赖外部参考仓库，license 与边界失控
    """
    patterns = _forbidden_examples("runtime_import_from_reference_project") + ("参考项目",)
    violations = list(scan_guardrail_roots_for_patterns(patterns))
    violations.extend(scan_forbidden_import_roots(FORBIDDEN_REFERENCE_IMPORT_ROOTS))
    violations.extend(scan_sys_path_mutation_with_reference_dir())
    assert violations == [], f"reference-project runtime coupling: {violations}"


def test_noOpenbbRuntimeCopyIntroduced() -> None:
    """覆盖范围：禁止把 OpenBB AGPL runtime 复制进 QMD
    测试对象：forbidden_adoption.copied_openbb_runtime_source + openbb import
    目的/目标：OpenBB 仅作架构参考，不得引入 provider fetcher 运行时
    验证点：护栏列出的 OpenBB 禁止模式在 backend/scripts 中为零命中
    失败含义：AGPL runtime 渗入，存在 license 与维护风险
    """
    patterns = _forbidden_examples("copied_openbb_runtime_source") + (
        "from openbb",
        "import openbb",
    )
    violations = scan_guardrail_roots_for_patterns(patterns)
    assert violations == [], f"OpenBB runtime copy patterns: {violations}"


def test_jq2ptradeExecPatternNotCopied() -> None:
    """覆盖范围：禁止从 JQ2PTrade 复制策略调度/执行钩子
    测试对象：forbidden_adoption.scheduler_or_execution_hook
    目的/目标：QMD 只做 read-only loader/review，不引入 run_daily 等执行语义
    验证点：scan_guardrail_roots_for_patterns 对调度钩子模式返回空
    失败含义：参考项目的策略执行面渗入 QMD runtime
    """
    patterns = _forbidden_examples("scheduler_or_execution_hook")
    violations = scan_guardrail_roots_for_patterns(patterns)
    assert violations == [], f"forbidden scheduler/exec patterns: {violations}"


def test_noAgentTriggeredWritePatterns() -> None:
    """覆盖范围：禁止 agent 触发写路径渗入 backend/scripts
    测试对象：forbidden_adoption.round3g_agent_triggered_write
    目的/目标：Round3G 前不得出现 agent 扩样/代批/触发写语义
    验证点：yaml P0 examples 在扫描根内零命中
    失败含义：agent 可绕过用户审批触发写入，sandbox 边界失效
    """
    patterns = _forbidden_examples("round3g_agent_triggered_write")
    violations = scan_guardrail_roots_for_patterns(patterns)
    assert violations == [], f"agent-triggered write patterns: {violations}"


def test_noEasyxtHardcodedTableInDataHealth() -> None:
    """覆盖范围：data health 模块不得保留 EasyXT 式硬编码表名
    测试对象：backend/app/ops/data_health.py 与 data_health_profiles/**
    目的/目标：采纳参考代码时必须 remove_hardcoded_table_names（如 stock_daily）
    验证点：上述路径内 stock_daily 字面量为零
    失败含义：data health 仍绑定参考项目表名，与 QMD schema 耦合
    """
    from tests.contract_gate_support import scan_file_for_forbidden_substrings

    paths = [PROJECT_ROOT / "backend/app/ops/data_health.py"]
    profiles = PROJECT_ROOT / "backend/app/ops/data_health_profiles"
    if profiles.is_dir():
        paths.extend(profiles.rglob("*.py"))
    violations: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        hits = scan_file_for_forbidden_substrings(path, ("stock_daily",))
        if hits:
            violations.append(f"{path.relative_to(PROJECT_ROOT)}: {hits}")
    assert violations == [], f"EasyXT hardcoded table in data health: {violations}"


def test_batch3frCardsDoNotRequireCentralInventory() -> None:
    """覆盖范围：Batch 3F-R 任务卡不得把中央 reference inventory 列为执行依赖
    测试对象：BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/*.md
    目的/目标：可执行采纳细节留在各任务卡本地，inventory 最多是非执行索引
    验证点：无正向执行依赖句式；redirect 卡须标明不可直接实现
    失败含义：3F-R 派发会回到已否决的中央 inventory 工作流
    """
    batch_dir = PROJECT_ROOT / (
        "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/"
        "BATCH_3FR_REFERENCE_ADOPTION_REFACTOR"
    )
    inventory_name = "reference_adoption_inventory.md"
    offenders: list[str] = []
    positive = re.compile(
        r"(must read|execution dependency|depends on|required read|ssot:\s*.*inventory|see\s+`.*inventory)",
        re.IGNORECASE,
    )
    for card in sorted(batch_dir.glob("R3FR_*.md")):
        for line in card.read_text(encoding="utf-8").splitlines():
            lower = line.lower()
            if inventory_name not in lower:
                continue
            if any(
                token in lower
                for token in ("must not", "cannot", "forbidden", "no `", "do not create", "redirected")
            ):
                continue
            if positive.search(line):
                offenders.append(f"{card.relative_to(PROJECT_ROOT)}: {line.strip()}")
    redirect = batch_dir / "R3FR_01_REFERENCE_INVENTORY_AND_LICENSE_MATRIX.md"
    if redirect.is_file():
        body = redirect.read_text(encoding="utf-8").lower()
        assert "do not implement" in body or "redirected" in body
    assert offenders == [], f"3F-R cards treat central inventory as execution SSOT: {offenders}"


def test_productionCompletionPlanIsCoverageMapOnly() -> None:
    """覆盖范围：新增生产补齐总计划不得成为中央执行工单
    测试对象：PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md 顶部边界说明
    目的/目标：确保总计划只是覆盖地图，具体执行仍回到 owning task card
    验证点：文件明确包含 coverage map、not a standalone execution task card、owning canonical task card
    失败含义：执行者可能绕过具体任务卡，回到中央 inventory 风险
    """
    path = PROJECT_ROOT / "docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md"
    text = path.read_text(encoding="utf-8")
    assert "coverage map" in text
    assert "not a standalone execution task card" in text
    assert "owning canonical task card" in text
    assert "must not replace task-card-local reference-adoption details" in text


def test_r3frAdaptingCardsDeclareReferenceProject() -> None:
    """覆盖范围：引用参考项目的 3F-R 实现卡必须含 reference_project 块
    测试对象：R3FR_02..07 任务卡
    目的/目标：license gate 在任务卡可解析，非仅全局 yaml 文档
    验证点：含 参考项目 的卡必须有 reference_project: 与 allowed_use
    失败含义：执行 agent 可跳过 license 决策直接改代码
    """
    batch_dir = PROJECT_ROOT / (
        "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/"
        "BATCH_3FR_REFERENCE_ADOPTION_REFACTOR"
    )
    missing: list[str] = []
    for card in sorted(batch_dir.glob("R3FR_0[2-7]_*.md")):
        text = card.read_text(encoding="utf-8")
        if "参考项目" not in text:
            continue
        if "reference_project:" not in text or "allowed_use:" not in text:
            missing.append(str(card.relative_to(PROJECT_ROOT)))
    assert missing == [], f"adapting cards missing reference_project block: {missing}"
