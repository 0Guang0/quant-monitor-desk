"""参考实现采纳护栏：静态扫描 backend/scripts，禁止从外部项目照搬危险模式。"""

from __future__ import annotations

import re

import yaml

from tests.contract_gate_support import (
    FORBIDDEN_REFERENCE_IMPORT_ROOTS,
    FORBIDDEN_TRADING_DEF_NAMES,
    PROJECT_ROOT,
    load_yaml,
    markdown_paths_missing_phrase,
    scan_forbidden_function_defs,
    scan_forbidden_import_roots,
    scan_guardrail_roots_for_patterns,
    scan_strategy_exec_patterns,
    scan_sys_path_mutation_with_reference_dir,
)

GUARDRAILS = PROJECT_ROOT / "specs/contracts/reference_adoption_guardrails.yaml"

_GUARDRAILS = yaml.safe_load(GUARDRAILS.read_text(encoding="utf-8")) or {}

_R3FR01_DOWNSTREAM_REL = (
    "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md",
    "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md",
    "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
    "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md",
    "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_02_MARKET_DATA_ADAPTERS.md",
    "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_03_CN_MARKET_ADAPTERS.md",
    "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md",
    "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md",
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_01_api_runtime_security.md",
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_02_agent_policy_runtime.md",
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_03_frontend_error_boundary_and_routes.md",
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_04_notification_report_runtime.md",
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md",
    "docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_01_security_ci_release_gate.md",
    "docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_02_integration_and_resource_smoke.md",
    "docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_03_release_manifest_and_package_cleanup.md",
)

_LOOSE_ROUND4_GLOB = "0[2-3][0-9]_*.md"


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
    assert rules.get("production_completion_coverage_map_file") == (
        "docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md"
    )
    assert rules.get("downstream_may_cite_production_plan_only_as_coverage_checklist") is True
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

    listed = set(_GUARDRAILS.get("required_tests") or [])
    assert listed == {
        "tests/test_reference_adoption_guardrails.py::test_r3fr01GuardrailsYamlContract",
        "tests/test_reference_adoption_guardrails.py::test_noTradingApiCopied",
        "tests/test_reference_adoption_guardrails.py::test_noAutoLoginCopied",
        "tests/test_reference_adoption_guardrails.py::test_noSilentFallbackCopied",
        "tests/test_reference_adoption_guardrails.py::test_noReferenceProjectRuntimeImport",
        "tests/test_reference_adoption_guardrails.py::test_noOpenbbRuntimeCopyIntroduced",
        "tests/test_reference_adoption_guardrails.py::test_jq2ptradeSchedulerHookNotCopied",
        "tests/test_reference_adoption_guardrails.py::test_jq2ptradeCompileExecPatternNotCopied",
        "tests/test_reference_adoption_guardrails.py::test_r3fr04Round4BacktestPlanningClosure",
        "tests/test_reference_adoption_guardrails.py::test_noAgentTriggeredWritePatterns",
        "tests/test_reference_adoption_guardrails.py::test_noEasyxtHardcodedTableInDataHealth",
        "tests/test_reference_adoption_guardrails.py::test_batch3frCardsDoNotRequireCentralInventory",
        "tests/test_reference_adoption_guardrails.py::test_r3fr01PlanningWordingAndLooseCardRedirects",
        "tests/test_reference_adoption_guardrails.py::test_productionCompletionPlanIsCoverageMapOnly",
        "tests/test_reference_adoption_guardrails.py::test_r3fr01DownstreamCardsGovernanceBoundaries",
        "tests/test_reference_adoption_guardrails.py::test_r3frAdaptingCardsDeclareReferenceProject",
        "tests/test_reference_adoption_guardrails.py::test_r3fr05ProviderCatalogClosure",
    }


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


def test_jq2ptradeSchedulerHookNotCopied() -> None:
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


def test_r3fr01PlanningWordingAndLooseCardRedirects() -> None:
    """覆盖范围：R3FR-01-C/D 规划口径与松散卡 redirect
    测试对象：MODULE_COMPLETION_RATING、implementation_tasks/README、ROADMAP、029 松散卡
    目的/目标：地图不是工单；松散 Round4 卡不得作为独立执行入口
    验证点：三份规划文件含「地图不是工单」；029 含 do not implement / B04_05 / coverage map
    失败含义：执行者可能误用覆盖地图或松散卡当中央工单
    """
    planning_paths = (
        PROJECT_ROOT / "MODULE_COMPLETION_RATING.md",
        PROJECT_ROOT / "docs/implementation_tasks/README.md",
        PROJECT_ROOT / "PROJECT_IMPLEMENTATION_ROADMAP.md",
    )
    assert markdown_paths_missing_phrase("地图不是工单", planning_paths) == []

    loose_dir = PROJECT_ROOT / "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST"
    for card in sorted(loose_dir.glob(_LOOSE_ROUND4_GLOB)):
        body = card.read_text(encoding="utf-8").lower()
        assert "historical input notice" in body, card.name
        assert "do not implement" in body, card.name
        assert "batch_04_verified_audit_productization" in body, card.name

    loose = loose_dir / "029_implement_backtest_and_review.md"
    body = loose.read_text(encoding="utf-8").lower()
    for needle in ("b04_05_backtest_review_runtime.md", "coverage map"):
        assert needle in body, f"029 redirect missing: {needle}"


def test_r3fr01DownstreamCardsGovernanceBoundaries() -> None:
    """覆盖范围：R3FR-01 §5 下游 canonical 任务卡治理边界
    测试对象：R3G/R3H/B04/B05 共 16 张任务卡
    目的/目标：不得把中央 inventory 或覆盖地图当执行 SSOT；参考采纳卡须含禁止项
    验证点：inventory/plan 正向依赖为零；含参考项目卡有 Forbidden；B05 含 release blocker 口径
    失败含义：下游派发可能绕过任务卡本地细则或把发布批当功能后门
    """
    inventory_name = "reference_adoption_inventory.md"
    plan_token = "production_completion_vertical_slice_plan.md"
    inventory_positive = re.compile(
        r"(must read|execution dependency|depends on|required read|ssot:\s*.*inventory)",
        re.IGNORECASE,
    )
    plan_ok = (
        "coverage map",
        "coverage checklist",
        "coverage only",
        "not the execution",
        "not a standalone",
        "navigation",
        "only as a coverage",
    )
    offenders: list[str] = []
    for rel in _R3FR01_DOWNSTREAM_REL:
        path = PROJECT_ROOT / rel
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for line in text.splitlines():
            line_lower = line.lower()
            if inventory_name in line_lower and not any(
                t in line_lower for t in ("must not", "do not create", "forbidden", "cannot")
            ):
                if inventory_positive.search(line):
                    offenders.append(f"{rel}: inventory SSOT — {line.strip()}")
            if plan_token in line_lower and not any(ok in line_lower for ok in plan_ok):
                offenders.append(f"{rel}: production plan without coverage boundary — {line.strip()}")
        if "参考项目" in text and not any(
            token in lower
            for token in (
                "forbidden",
                "must not",
                "target qmd",
                "## 4. target",
                "target files",
                "qmd-owned target",
            )
        ):
            offenders.append(f"{rel}: missing reference forbidden/target boundary")
        if rel.startswith("docs/implementation_tasks/ROUND_5_"):
            release_posture = (
                "release blocker",
                "manifest limitation",
                "known_limitations",
                "must not implement missing product",
            )
            if not any(token in lower for token in release_posture):
                offenders.append(f"{rel}: missing release blocker/limitation posture")
    assert offenders == [], f"downstream governance gaps: {offenders}"


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
    assert "## 1. When a slice becomes executable (checklist only)" in text
    marker3 = "## 3. Production-incomplete module inventory"
    section2 = text.split(marker3, 1)[0].split("## 2.", 1)[-1]
    assert "backend/app/" not in section2, "§2 must not list implementation target paths"
    assert "**Not done if:**" not in section2, "§2 must not carry executable not-done lists"


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


_R3FR04_JQ2PTRADE_PATHS = (
    "参考项目/JQ2PTrade/api_mapping.json",
    "参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py",
    "参考项目/JQ2PTrade/ptrade_local/engine/api.py",
    "参考项目/JQ2PTrade/ptrade_local/engine/context.py",
    "参考项目/JQ2PTrade/ptrade_local/engine/backtester.py",
    "参考项目/JQ2PTrade/ptrade_local/engine/report.py",
    "参考项目/JQ2PTrade/ptrade_local/run_backtest.py",
)

_R3FR04_EASYXT_PATHS = (
    "参考项目/EasyXT/easyxt_backtest/performance.py",
    "参考项目/EasyXT/easyxt_backtest/portfolio_daily_result.py",
    "参考项目/EasyXT/easyxt_backtest/core/backtest_core.py",
)

_R3FR04_FORBIDDEN_APIS = (
    "order",
    "order_value",
    "order_target",
    "order_target_value",
    "cancel_order",
    "get_open_orders",
    "get_portfolio",
    "get_positions",
    "get_orders",
    "get_trades",
    "run_daily",
    "run_weekly",
    "run_monthly",
)

_R3FR04_ROUND4_TARGET_REL = (
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/"
    "BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md",
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/"
    "BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_TASK_CARD_MANIFEST.md",
    "docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/"
    "BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_HARDENING_RULES.md",
)


def _slice_has_not_done(text: str, slice_id: str) -> bool:
    marker = f"### Slice {slice_id}"
    start = text.find(marker)
    if start < 0:
        return False
    nxt = text.find("### Slice ", start + len(marker))
    block = text[start:nxt] if nxt >= 0 else text[start:]
    return "**Not done if:**" in block


def test_jq2ptradeCompileExecPatternNotCopied() -> None:
    """覆盖范围：backend/scripts 源码中不得出现「编译并执行任意策略」的 JQ2PTrade 模式
    测试对象：scan_strategy_exec_patterns（backend/app 与 scripts）
    目的/目标：回测复盘必须是只读 review，不能把用户策略代码 compile+exec 跑起来
    验证点：AST 扫描 compile(...,'exec') 与 exec(...) 调用列表为空
    失败含义：Round4 可能照搬 JQ2PTrade 策略执行引擎，突破 no-action 边界
    """
    violations = scan_strategy_exec_patterns()
    assert violations == [], f"forbidden strategy exec patterns: {violations}"


def test_r3fr04Round4BacktestPlanningClosure() -> None:
    """覆盖范围：R3FR-04 完成后 Round4 回测/复盘规划是否可直接派发实现
    测试对象：B04_05、Batch04 manifest/hardening 与 backtest/review 四份契约 YAML
    目的/目标：Round4 不能再是空白引擎设计；须写清三批上限、切片未完成条件、参考路径与 attribution
    验证点：Batch A/B/C、九参考路径、五切片各含 Not done if、manifest/hardening 同步、forbidden_api 完整
    失败含义：执行 agent 仍可能从零设计回测引擎，或跳过 evidence 绑定与 no-action deny-list
    """
    b04_path = PROJECT_ROOT / _R3FR04_ROUND4_TARGET_REL[0]
    text = b04_path.read_text(encoding="utf-8")
    for needle in (
        "Batch A",
        "Batch B",
        "Batch C",
        "at most three implementation batches",
        "reference_project:",
        "attribution_required: true",
    ):
        assert needle in text, f"B04_05 missing R3FR-04 planning marker: {needle}"
    for path in _R3FR04_JQ2PTRADE_PATHS + _R3FR04_EASYXT_PATHS:
        assert path in text, f"B04_05 missing reference path: {path}"
    for slice_id in ("B04_05-A", "B04_05-B", "B04_05-C", "B04_05-D", "B04_05-E"):
        assert slice_id in text, f"B04_05 missing slice {slice_id}"
        assert _slice_has_not_done(text, slice_id), f"B04_05 slice {slice_id} missing Not done if"

    manifest = (PROJECT_ROOT / _R3FR04_ROUND4_TARGET_REL[1]).read_text(encoding="utf-8")
    hardening = (PROJECT_ROOT / _R3FR04_ROUND4_TARGET_REL[2]).read_text(encoding="utf-8")
    for doc_name, body in (("manifest", manifest), ("hardening", hardening)):
        for needle in ("Batch A", "Batch B", "Batch C", "B04_05-A", "**Not done if:**"):
            assert needle in body, f"BATCH_04 {doc_name} missing R3FR-04 sync marker: {needle}"

    backtest = load_yaml(PROJECT_ROOT / "specs/contracts/backtest_contract.yaml")
    ref = backtest.get("reference_adoption") or {}
    assert ref.get("attribution_required") is True, "backtest_contract missing attribution_required"
    jq_paths = tuple(ref.get("allowed_reference_paths", {}).get("jq2ptrade") or [])
    for path in _R3FR04_JQ2PTRADE_PATHS:
        assert path in jq_paths, f"backtest_contract missing jq2ptrade path: {path}"
    forbidden_names = set(backtest.get("forbidden_api_names") or [])
    assert forbidden_names >= set(_R3FR04_FORBIDDEN_APIS), "backtest_contract forbidden_api_names incomplete"

    metric = load_yaml(PROJECT_ROOT / "specs/contracts/backtest_metric_contract.yaml")
    assert "reference_adoption" in metric, "backtest_metric_contract missing reference_adoption"
    assert metric.get("reference_adoption", {}).get("attribution_required") is True
    easyxt = (metric.get("reference_adoption") or {}).get("allowed_reference_paths", {}).get(
        "easyxt"
    ) or []
    for path in _R3FR04_EASYXT_PATHS:
        assert path in easyxt, f"backtest_metric_contract missing easyxt path: {path}"
    risk_adj = (metric.get("reference_adoption") or {}).get("metric_groups", {}).get(
        "risk_adjusted"
    ) or []
    assert risk_adj, "backtest_metric_contract missing Batch B risk_adjusted metric targets"

    repro = load_yaml(PROJECT_ROOT / "specs/contracts/backtest_reproducibility_contract.yaml")
    assert "reference_adoption" in repro, "backtest_reproducibility_contract missing reference_adoption"
    assert repro.get("reference_adoption", {}).get("attribution_required") is True
    assert "input_evidence_ids" in repro.get("required_artifacts", {}).get(
        "frozen_dataset_manifest", {}
    ).get("fields", []), "repro contract missing evidence binding field"

    sandbox = load_yaml(PROJECT_ROOT / "specs/contracts/review_sandbox_contract.yaml")
    assert sandbox.get("static_analysis_only") is True, "review_sandbox must be static_analysis_only in first slice"
    forbidden = set(sandbox.get("forbidden_api") or [])
    missing_apis = [name for name in _R3FR04_FORBIDDEN_APIS if name not in forbidden]
    assert missing_apis == [], f"review_sandbox missing forbidden APIs: {missing_apis}"


_R3FR05_CARD_REL = (
    "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/"
    "BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md"
)
_R3FR05_CATALOG_REL = "specs/datasource_registry/provider_catalog.yaml"


def test_r3fr05ProviderCatalogClosure() -> None:
    """覆盖范围：R3FR-05 provider catalog 任务闭环与护栏登记
    测试对象：R3FR-05 任务卡、provider_catalog.yaml、reference_adoption_guardrails.yaml
    目的/目标：catalog SSOT 存在、OpenBB architecture_only、guardrails 登记 closure 测试
    验证点：任务卡 qmd_target_files、catalog 25 providers、guardrails required_tests 含本测试
    失败含义：R3FR-05 交付不可审计或 OpenBB catalog 路径/护栏未闭环
    """
    card = (PROJECT_ROOT / _R3FR05_CARD_REL).read_text(encoding="utf-8")
    for needle in (
        "reference_project:",
        "allowed_use: architecture_only",
        "provider_catalog.yaml",
        "no_openbb_runtime_source_copy",
        "openbb_provider_reference",
    ):
        assert needle in card, f"R3FR-05 card missing marker: {needle}"

    catalog_path = PROJECT_ROOT / _R3FR05_CATALOG_REL
    assert catalog_path.is_file(), "provider catalog SSOT missing"
    catalog = load_yaml(catalog_path)
    providers = catalog.get("providers") or []
    assert len(providers) == 25

    openbb = next(p for p in providers if p.get("provider_id") == "openbb_provider_reference")
    assert openbb.get("runtime_source_copy_allowed") is False

    listed = set(_GUARDRAILS.get("required_tests") or [])
    assert "tests/test_reference_adoption_guardrails.py::test_r3fr05ProviderCatalogClosure" in listed

    openbb_adoption = (_GUARDRAILS.get("allowed_adoption") or {}).get("openbb_provider_architecture") or {}
    assert "architecture_only_provider_catalog_pattern" in (openbb_adoption.get("allowed_as") or [])


_R3G01_MODULE_ROOT = PROJECT_ROOT / "backend/app/ops/sandbox_clean_write"


def test_r3g01SandboxCleanWrite_noReferenceProjectRuntimeImport() -> None:
    """覆盖范围：R3G-01 sandbox_clean_write 无参考项目 runtime import
    测试对象：backend/app/ops/sandbox_clean_write/**
    目的/目标：AC-07 禁止 参考项目/** runtime import
    验证点：scan_forbidden_import_roots 对 sandbox_clean_write 为空
    失败含义：排练模块从参考项目直接 import
    """
    violations = scan_forbidden_import_roots(
        FORBIDDEN_REFERENCE_IMPORT_ROOTS,
        scan_roots=(_R3G01_MODULE_ROOT,),
    )
    assert violations == [], f"reference project imports: {violations}"


def test_r3g01SandboxCleanWrite_noJq2ptradeTradingApiSurface() -> None:
    """覆盖范围：R3G-01 无 JQ2PTrade 交易 API 名
    测试对象：sandbox_clean_write/** 源码
    目的/目标：AC-08 禁止 order/get_portfolio 等交易 API 兼容层
    验证点：禁止函数名 AST 扫描为空
    失败含义：排练模块暴露 JQ2PTrade 交易 API
    """
    violations = scan_forbidden_function_defs(
        FORBIDDEN_TRADING_DEF_NAMES,
        roots=(_R3G01_MODULE_ROOT,),
    )
    assert violations == [], f"trading API defs: {violations}"


def test_r3g01SandboxCleanWrite_openbbArchitectureOnly() -> None:
    """覆盖范围：OpenBB 仅架构引用
    测试对象：sandbox_clean_write/** 源码
    目的/目标：AC-09 无 OpenBB runtime copy 模式
    验证点：无 openbb_platform/providers 路径与 copied fetcher 类名
    失败含义：OpenBB runtime 源码被复制进排练模块
    """
    text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in _R3G01_MODULE_ROOT.rglob("*.py")
        if p.is_file()
    )
    assert "openbb_platform/providers" not in text
    assert "OBBject" not in text
    assert "from openbb" not in text


def test_r3g01SandboxCleanWrite_noProductionLiveClaim() -> None:
    """覆盖范围：排练模块不宣称 production-live
    测试对象：rehearsal_runner + rehearsal_report
    目的/目标：AC-14 对齐 production_live_pilot_policy
    验证点：production_live_claim 硬编码 False；无 production_live_readiness_claim True
    失败含义：排练误宣称 production-live ready
    """
    runner = (PROJECT_ROOT / "backend/app/ops/sandbox_clean_write/rehearsal_runner.py").read_text(
        encoding="utf-8"
    )
    report_mod = (PROJECT_ROOT / "backend/app/ops/sandbox_clean_write/rehearsal_report.py").read_text(
        encoding="utf-8"
    )
    assert "production_live_readiness_claim" not in runner
    assert '"production_live_claim": False' in report_mod


_R3G03_MODULE_ROOT = PROJECT_ROOT / "backend/app/ops/sandbox_clean_write"


def test_r3g03LimitedProduction_noReferenceProjectRuntimeImport() -> None:
    """覆盖范围：R3G-03 promote 模块无参考项目 runtime import
    测试对象：approval_contract + limited_production_entry + rollback_plan
    目的/目标：AC-08 禁止 参考项目/** runtime import
    验证点：scan_forbidden_import_roots 对 r3g03 新模块为空
    失败含义：promote 模块从参考项目直接 import
    """
    from tests.contract_gate_support import FORBIDDEN_REFERENCE_IMPORT_ROOTS, scan_forbidden_import_roots

    violations = scan_forbidden_import_roots(
        FORBIDDEN_REFERENCE_IMPORT_ROOTS,
        scan_roots=(_R3G03_MODULE_ROOT,),
    )
    r3g03_only = [
        v
        for v in violations
        if any(
            name in v
            for name in (
                "approval_contract",
                "limited_production_entry",
                "rollback_plan",
            )
        )
    ]
    assert r3g03_only == [], f"r3g03 reference imports: {r3g03_only}"


def test_r3g03LimitedProduction_noJq2ptradeTradingApiSurface() -> None:
    """覆盖范围：R3G-03 无 JQ2PTrade 交易 API 名
    测试对象：r3g03 promote 源码
    目的/目标：禁止 order/get_portfolio 等交易 API 兼容层
    验证点：禁止函数名 AST 扫描对 r3g03 文件为空
    失败含义：promote 模块暴露 JQ2PTrade 交易 API
    """
    from tests.contract_gate_support import FORBIDDEN_TRADING_DEF_NAMES, scan_forbidden_function_defs

    r3g03_files = (
        _R3G03_MODULE_ROOT / "approval_contract.py",
        _R3G03_MODULE_ROOT / "limited_production_entry.py",
        _R3G03_MODULE_ROOT / "rollback_plan.py",
    )
    violations = scan_forbidden_function_defs(FORBIDDEN_TRADING_DEF_NAMES, roots=r3g03_files)
    assert violations == [], f"r3g03 trading API defs: {violations}"


def test_r3g03LimitedProduction_openbbArchitectureOnly() -> None:
    """覆盖范围：R3G-03 OpenBB 仅架构引用
    测试对象：r3g03 promote 源码
    目的/目标：无 OpenBB runtime copy 模式
    验证点：无 openbb_platform/providers 路径
    失败含义：OpenBB runtime 源码被复制进 promote 模块
    """
    text = "\n".join(
        (_R3G03_MODULE_ROOT / name).read_text(encoding="utf-8")
        for name in ("approval_contract.py", "limited_production_entry.py", "rollback_plan.py")
    )
    assert "openbb_platform/providers" not in text
    assert "from openbb" not in text


def test_r3g03LimitedProduction_noAgentTriggeredWriteMarker() -> None:
    """覆盖范围：R3G-03 agent 触发写拒绝（行为测）
    测试对象：validate_approval_contract no_agent_triggered_write
    目的/目标：no_agent_triggered_write=false 时 fail-closed
    验证点：篡改 approval 后抛 agent_triggered_write_path
    失败含义：agent 可替代用户 approval 触发生产写
    """
    import pytest
    import tempfile
    from pathlib import Path

    import yaml

    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    raw = yaml.safe_load(
        (PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g03/approval_minimal.yaml").read_text(
            encoding="utf-8"
        )
    )
    raw["no_agent_triggered_write"] = False
    with tempfile.TemporaryDirectory() as tmp:
        approval_path = Path(tmp) / "approval.yaml"
        audit_path = Path(tmp) / "audit.json"
        audit_path.write_text(
            (
                PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g03/audit_decision_allow.json"
            ).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        raw["audit_decision_file"] = str(audit_path)
        approval_path.write_text(yaml.dump(raw), encoding="utf-8")
        with pytest.raises(ApprovalContractError, match="agent_triggered_write_path"):
            validate_approval_contract(approval_path, audit_path)
