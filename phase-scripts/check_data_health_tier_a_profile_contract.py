#!/usr/bin/env python3
"""Tier-A data health 四族 profile / binding 契约盘点（阶段性 · 非业务 pytest）

功能：
  核对 data_quality_rules.yaml ops_cli_profiles 四族存在，且
  load_source_health_bindings 与契约 source_health_bindings 行数/族一致；
  11 源绑定路由到合法 profile+domain，并与 INCREMENTAL_GOLD_PATH_SOURCE_IDS 对齐。
  对应原 test_fourProfileFamilies_registeredInContract /
  test_allTierASources_bindingRoutesToSupportedProfile。

业务价值：
  防止 F0 health 路由与 Tier A registry 漂移；profile runner 行为仍留 pytest。

退役 / 清理时间（满足任一即可删本文件）：
  1. 四族 binding 迁入稳定 scripts/production_gate 子步；或
  2. F0 / Tier A 路由模型退役。

运行：
  uv run python phase-scripts/check_data_health_tier_a_profile_contract.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.datasources.live_prod_source_tiers import (  # noqa: E402
    INCREMENTAL_GOLD_PATH_SOURCE_IDS,
)
from backend.app.ops.data_health_profiles.source_health_bindings import (  # noqa: E402
    load_source_health_bindings,
)

RULES_PATH = PROJECT_ROOT / "specs" / "contracts" / "data_quality_rules.yaml"

SUPPORTED = {
    "market_bar_p0": {"market_bar_1d"},
    "layer1_observation_p0": {"layer1_observation"},
    "disclosure_p0": {"us_disclosure", "cn_disclosure"},
    "crypto_derivative_p0": {"crypto_derivative"},
}


def _run() -> list[str]:
    errors: list[str] = []
    raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8")) or {}
    profiles = raw.get("ops_cli_profiles") or {}
    for key in (
        "market_bar_1d",
        "layer1_observation",
        "us_disclosure",
        "crypto_derivative",
    ):
        if key not in profiles:
            errors.append(f"ops_cli_profiles missing {key}")

    bindings = load_source_health_bindings()
    contract_bindings = raw.get("source_health_bindings") or {}
    if len(bindings) != len(contract_bindings):
        errors.append(
            f"binding count drift runtime={len(bindings)} contract={len(contract_bindings)}"
        )
    families = {b["health_profile_id"] for b in bindings.values()}
    expected_families = set(SUPPORTED)
    if families != expected_families:
        errors.append(f"health_profile families={sorted(families)} expected={sorted(expected_families)}")

    if set(bindings.keys()) != set(INCREMENTAL_GOLD_PATH_SOURCE_IDS):
        errors.append(
            "source_health_bindings keys != INCREMENTAL_GOLD_PATH_SOURCE_IDS: "
            f"only_bindings={sorted(set(bindings) - set(INCREMENTAL_GOLD_PATH_SOURCE_IDS))} "
            f"only_gold={sorted(set(INCREMENTAL_GOLD_PATH_SOURCE_IDS) - set(bindings))}"
        )
    for source_id, binding in bindings.items():
        profile = binding["health_profile_id"]
        domain = binding["health_domain"]
        if profile not in SUPPORTED:
            errors.append(f"{source_id}: unsupported profile {profile!r}")
            continue
        if domain not in SUPPORTED[profile]:
            errors.append(f"{source_id}: domain {domain!r} not in {SUPPORTED[profile]}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when violations are found",
    )
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: data health Tier-A profile contract")
        return 0
    print("FAIL: data health Tier-A profile contract")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
