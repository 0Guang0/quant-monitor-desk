"""R3-DCP-09 wave3 isolated acceptance quick profile tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts/wave3_isolated_production_acceptance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("wave3_isolated", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_wave3_isolated_acceptance_quick_profile_skips_pytest_full() -> None:
    """覆盖范围：--quick profile 跳过 pytest_full
    测试对象：wave3_isolated_production_acceptance._build_steps
    目的/目标：WAVE3-ACC-OPT-01 quick 分层关账
    验证点：quick=True 无 pytest_full；full 含 pytest_full
    失败含义：quick 仍跑全量 pytest，PR/本地无法 <5min 验收
    """
    mod = _load_module()
    quick_names = [name for name, _cmd in mod._build_steps(quick=True)]
    full_names = [name for name, _cmd in mod._build_steps(quick=False)]
    assert "pytest_full" not in quick_names
    assert "pytest_full" in full_names
    assert len(quick_names) < len(full_names)
