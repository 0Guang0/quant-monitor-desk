"""Contract gate: reference adoption guardrails static scan (artifact-guard).

CI 主责可迁至 scripts/check_*；pytest 保留契约 pattern 扫描 + 少量 runtime 行为锚点。
"""

from __future__ import annotations

import yaml

from tests.contract_gate_support import (
    FORBIDDEN_REFERENCE_IMPORT_ROOTS,
    FORBIDDEN_TRADING_DEF_NAMES,
    PROJECT_ROOT,
    scan_forbidden_function_defs,
    scan_forbidden_import_roots,
    scan_guardrail_roots_for_patterns,
    scan_strategy_exec_patterns,
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


def test_jq2ptradeCompileExecPatternNotCopied() -> None:
    """覆盖范围：backend/scripts 源码中不得出现「编译并执行任意策略」的 JQ2PTrade 模式
    测试对象：scan_strategy_exec_patterns（backend/app 与 scripts）
    目的/目标：回测复盘必须是只读 review，不能把用户策略代码 compile+exec 跑起来
    验证点：AST 扫描 compile(...,'exec') 与 exec(...) 调用列表为空
    失败含义：Round4 可能照搬 JQ2PTrade 策略执行引擎，突破 no-action 边界
    """
    violations = scan_strategy_exec_patterns()
    assert violations == [], f"forbidden strategy exec patterns: {violations}"


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
