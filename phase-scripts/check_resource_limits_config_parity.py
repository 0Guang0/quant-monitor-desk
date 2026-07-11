#!/usr/bin/env python3
"""资源限额配置 ↔ 契约 YAML 对齐（阶段性 · 非业务 pytest）

功能：
  比对 configs/resource_limits.yaml 与 specs/contracts/resource_limits.yaml
  的 default_profile / profiles / thresholds / api_limits / actions 是否一致。
  对应原 tests/test_config_templates.py（artifact-guard）。

业务价值：
  防止运行时配置与 machine-readable 契约分叉，导致 CI 契约门与真实档位不一致。

退役 / 清理时间（满足任一即可删本文件）：
  1. ResourceGuard / ConnectionManager 已有从契约加载的集成测覆盖全部 profile 字段，
     且正式 CI（production_gate / pre-commit）已接同类 parity；或
  2. configs/ 改为由 design→runtime promote 单向生成，本比对失去独立意义。

运行：
  uv run python phase-scripts/check_resource_limits_config_parity.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run() -> list[str]:
    config = yaml.safe_load(
        (PROJECT_ROOT / "configs/resource_limits.yaml").read_text(encoding="utf-8")
    )
    contract = yaml.safe_load(
        (PROJECT_ROOT / "specs/contracts/resource_limits.yaml").read_text(encoding="utf-8")
    )
    errors: list[str] = []
    if not (config["default_profile"] == contract["default_profile"] == "eco"):
        errors.append("default_profile mismatch (expect eco on both)")
    for profile_name in ("eco", "normal"):
        if config["profiles"][profile_name] != contract["profiles"][profile_name]:
            errors.append(f"profiles.{profile_name} mismatch")
    batch_cfg = config["profiles"]["batch"]
    batch_contract = contract["profiles"]["batch"]
    for key in batch_contract:
        if batch_cfg.get(key) != batch_contract[key]:
            errors.append(f"batch.{key} mismatch")
    for field in ("system_thresholds", "project_size_thresholds", "api_limits", "actions"):
        if config.get(field) != contract.get(field):
            errors.append(f"{field} mismatch")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: resource_limits config ↔ contract")
        return 0
    print("FAIL: resource_limits config ↔ contract")
    for err in errors:
        print(f"  - {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
