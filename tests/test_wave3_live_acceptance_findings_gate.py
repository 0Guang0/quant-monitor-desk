"""R3-DCP-09 wave3 live acceptance findings severity gate tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts/wave3_live_production_acceptance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("wave3_live", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_wave3_live_acceptance_findings_gate_high_critical() -> None:
    """覆盖范围：--fail-on-severity HIGH,CRITICAL 硬门禁
    测试对象：_count_severity_gate_violations
    目的/目标：ACC-LIVE-ACCEPT-NIGHTLY-001 findings 关账
    验证点：HIGH finding 计入门禁；EXPECTED_DEFER 不计入
    失败含义：nightly live 验收无法 fail-closed 业务偏差
    """
    mod = _load_module()
    fail_on = mod._parse_fail_on_severity("HIGH,CRITICAL")
    findings = [{"id": "X", "severity": "HIGH"}]
    plan_alignment = [{"id": "Y", "severity": "EXPECTED_DEFER"}]
    assert mod._count_severity_gate_violations(findings, plan_alignment, fail_on=fail_on) == 1


def test_wave3_live_acceptance_findings_gate_medium_passes() -> None:
    """覆盖范围：MEDIUM findings 不触发 HIGH,CRITICAL 门禁
    测试对象：_count_severity_gate_violations
    目的/目标：门禁仅拦截配置 severity
    验证点：MEDIUM only → 0 hits
    失败含义：门禁过宽，已知 MEDIUM 偏差阻塞 nightly
    """
    mod = _load_module()
    fail_on = mod._parse_fail_on_severity("HIGH,CRITICAL")
    findings = [{"id": "Z", "severity": "MEDIUM"}]
    assert mod._count_severity_gate_violations(findings, [], fail_on=fail_on) == 0
