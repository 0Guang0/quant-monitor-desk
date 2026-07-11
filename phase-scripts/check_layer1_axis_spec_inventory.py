#!/usr/bin/env python3
"""Layer1 轴规格字段完整性与工程规则路径盘点（阶段性 · 非业务 pytest）

功能：
  用 AxisSpecLoader 加载 specs/layer1_axes/restructured_axes_v1_1，核对可观测指标契约字段、
  画像中文摘要，以及 ENVIRONMENT 轴 engineering_rules_path 文件存在。
  对应原 tests/test_layer1_axis_loader.py 中字段完整性与工程规则投影元数据检查
  （不含 forbidden/blindspot/shadow 诊断类用例）。

业务价值：
  规格 YAML 缺字段或工程规则路径断链时尽早在门禁暴露，避免指标注册与特征引擎运行时崩。

退役 / 清理时间（满足任一即可删本文件）：
  1. AxisSpecLoader 运行时测试已用 tmp_path fixtures 单独覆盖字段完整性 + engineering_rules 路径；或
  2. 已有正式 schema validator CLI 覆盖同等契约。

运行：
  uv run python phase-scripts/check_layer1_axis_spec_inventory.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.layer1_axes.axis_loader import AxisSpecLoader  # noqa: E402

SPEC_ROOT = PROJECT_ROOT / "specs/layer1_axes/restructured_axes_v1_1"
DEFINITION_FIELDS = (
    "frequency",
    "unit",
    "primary_source",
    "validation_source",
    "fallback_policy",
)


def _check_observable_contract_fields(errors: list[str]) -> None:
    result = AxisSpecLoader().load(spec_root=SPEC_ROOT)
    observable = [i for i in result.indicators if i.is_observable]
    if not observable:
        errors.append("expected observable indicators, got none")
        return
    profiles_by_id = {p.indicator_id: p for p in result.profiles}
    for ind in observable:
        profile = profiles_by_id.get(ind.indicator_id)
        if profile is None:
            errors.append(f"{ind.indicator_id}: missing profile")
            continue
        if not profile.plain_language_summary:
            errors.append(f"{ind.indicator_id}: empty plain_language_summary")
        if not profile.display_name_cn:
            errors.append(f"{ind.indicator_id}: empty display_name_cn")
        if not ind.layer_tag:
            errors.append(f"{ind.indicator_id}: empty layer_tag")
        for field in DEFINITION_FIELDS:
            if getattr(ind, field, None) in (None, ""):
                errors.append(f"{ind.indicator_id}: missing contract field {field!r}")


def _check_environment_engineering_rules(errors: list[str]) -> None:
    try:
        result = AxisSpecLoader().load(spec_root=SPEC_ROOT, enabled_axes=["environment"])
    except Exception as exc:  # noqa: BLE001 — surface load failure as check error
        errors.append(f"ENVIRONMENT axis load failed: {exc}")
        return
    env_guard = next((g for g in result.guardrails if g.axis_id == "ENVIRONMENT"), None)
    if env_guard is None:
        errors.append("ENVIRONMENT guardrail missing from load result")
        return
    if not env_guard.engineering_rules_path:
        errors.append("ENVIRONMENT guardrail has empty engineering_rules_path")
        return
    eng_path = PROJECT_ROOT / env_guard.engineering_rules_path
    if not eng_path.is_file():
        errors.append(f"engineering_rules_path not a file under PROJECT_ROOT: {eng_path}")


def _run() -> list[str]:
    errors: list[str] = []
    if not SPEC_ROOT.is_dir():
        return [f"spec root missing: {SPEC_ROOT}"]
    _check_observable_contract_fields(errors)
    _check_environment_engineering_rules(errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: layer1 axis spec inventory")
        return 0
    print("FAIL: layer1 axis spec inventory")
    for err in errors:
        print(f"  - {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
