"""参考实现采纳护栏：静态扫描 backend，禁止从外部项目照搬危险模式。"""

from __future__ import annotations

import yaml
from tests.contract_gate_support import PROJECT_ROOT, scan_backend_python_for_patterns

GUARDRAILS = PROJECT_ROOT / "specs/contracts/reference_adoption_guardrails.yaml"


def _forbidden_examples(category: str) -> tuple[str, ...]:
    data = yaml.safe_load(GUARDRAILS.read_text(encoding="utf-8")) or {}
    block = (data.get("forbidden_adoption") or {}).get(category) or {}
    return tuple(block.get("examples") or [])


def _high_signal_patterns(category: str) -> tuple[str, ...]:
    patterns = _forbidden_examples(category)
    # Bare tokens like "order" false-positive on SQL/migration prose; use API-shaped names.
    skip = {"order"}
    return tuple(p for p in patterns if p not in skip)


def test_noTradingApiCopied() -> None:
    """覆盖范围：参考采纳护栏对 backend Python 的全局静态扫描
    测试对象：real_trading_or_order_api 禁止模式列表
    目的/目标：确保未从参考项目复制实盘下单/交易 API 符号
    验证点：scan_backend_python_for_patterns 返回空列表
    失败含义：backend 出现禁止交易 API 痕迹，存在误用参考代码风险
    """
    patterns = _high_signal_patterns("real_trading_or_order_api")
    violations = scan_backend_python_for_patterns(patterns)
    assert violations == [], f"forbidden trading API patterns in backend: {violations}"


def test_noAutoLoginCopied() -> None:
    """覆盖范围：参考采纳护栏对 backend Python 的全局静态扫描
    测试对象：auto_login_or_captcha 禁止模式列表
    目的/目标：防止照搬自动登录、验证码绕过等不安全认证逻辑
    验证点：scan_backend_python_for_patterns 返回空列表
    失败含义：backend 含自动登录/验证码相关复制代码，安全边界被突破
    """
    patterns = _forbidden_examples("auto_login_or_captcha")
    violations = scan_backend_python_for_patterns(patterns)
    assert violations == [], f"forbidden auto-login/captcha patterns in backend: {violations}"


def test_noSilentFallbackCopied() -> None:
    """覆盖范围：参考采纳护栏对 backend Python 的全局静态扫描
    测试对象：silent_fallback 禁止模式列表
    目的/目标：禁止静默降级——出错时必须显式 fail-closed 而非偷偷换路径
    验证点：scan_backend_python_for_patterns 返回空列表
    失败含义：存在静默 fallback 模式，故障可能被掩盖而非上报
    """
    patterns = _forbidden_examples("silent_fallback")
    violations = scan_backend_python_for_patterns(patterns)
    assert violations == [], f"forbidden silent-fallback patterns in backend: {violations}"
