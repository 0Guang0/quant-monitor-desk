"""Reference adoption guardrails — static scans for forbidden copied patterns."""

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
    patterns = _high_signal_patterns("real_trading_or_order_api")
    violations = scan_backend_python_for_patterns(patterns)
    assert violations == [], f"forbidden trading API patterns in backend: {violations}"


def test_noAutoLoginCopied() -> None:
    patterns = _forbidden_examples("auto_login_or_captcha")
    violations = scan_backend_python_for_patterns(patterns)
    assert violations == [], f"forbidden auto-login/captcha patterns in backend: {violations}"


def test_noSilentFallbackCopied() -> None:
    patterns = _forbidden_examples("silent_fallback")
    violations = scan_backend_python_for_patterns(patterns)
    assert violations == [], f"forbidden silent-fallback patterns in backend: {violations}"
