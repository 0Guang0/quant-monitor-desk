#!/usr/bin/env python3
"""网页/预测源 registry 策略盘点（阶段性 · 非业务 pytest）

功能：
  核对 source_registry.yaml：web/prediction domain fallback_policy，以及
  kalshi/polymarket/web_search 默认禁用。
  对应原 test_webAndPredictionDomains_fallbackPolicyNotCleanWriter /
  test_no_clean_write_sources_defaultDisabledInRegistry。

业务价值：
  防止非事实源被默认可写 clean 或 silent promote；runtime staging/port 负例仍留 pytest。

退役 / 清理时间（满足任一即可删本文件）：
  1. 策略迁入稳定 scripts/production_gate 子步；或
  2. 三源退役且 domain_roles 无对应 fallback 条款。

运行：
  uv run python phase-scripts/check_web_prediction_registry_policy.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"

DOMAIN_FALLBACKS = {
    "supplemental_web_evidence": "manual_review_required",
    "vix_cds_supplement": "manual_review_required",
    "event_resolution_evidence": "manual_review_required",
    "prediction_market_probability": "mark_missing",
    "regulated_event_contract": "mark_missing",
}
DISABLED_SOURCES = ("kalshi", "polymarket", "web_search")


def _run() -> list[str]:
    errors: list[str] = []
    doc = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    roles = doc.get("domain_roles") or {}
    for domain, expected in DOMAIN_FALLBACKS.items():
        actual = (roles.get(domain) or {}).get("fallback_policy")
        if actual != expected:
            errors.append(f"{domain}: fallback_policy={actual!r} expected={expected!r}")
    sources = {s["source_id"]: s for s in (doc.get("sources") or [])}
    for source_id in DISABLED_SOURCES:
        entry = sources.get(source_id)
        if entry is None:
            errors.append(f"missing source: {source_id}")
        elif entry.get("enabled_by_default") is not False:
            errors.append(f"{source_id}: enabled_by_default={entry.get('enabled_by_default')!r}")
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
        print("PASS: web/prediction registry policy")
        return 0
    print("FAIL: web/prediction registry policy")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
