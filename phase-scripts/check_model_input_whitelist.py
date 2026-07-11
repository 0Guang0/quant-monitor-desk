#!/usr/bin/env python3
"""五层 model input 白名单 YAML schema/hardening 盘点（阶段性 · 非业务 pytest）

功能：
  扫描 specs/model_inputs/*.yaml：必填字段、DCP-06 proven 行、macro_supplementary
  不得顶替 FRED primary、L4 US deferred、akshare/fred 角色上限。
  对应原 tests/test_model_input_whitelist.py 静态断言（不含 runtime loader）。

业务价值：
  守住规划白名单契约，避免错误 readiness/role 被当成可生产输入。

退役 / 清理时间（满足任一即可删本文件）：
  1. model_inputs 白名单退役或迁入稳定 scripts/production_gate 子步；或
  2. 下游 runtime loader + data_health profile 已完整覆盖同等语义并正式关账。

运行：
  uv run python phase-scripts/check_model_input_whitelist.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.contract_gate_support import load_yaml  # noqa: E402

MODEL_INPUTS = PROJECT_ROOT / "specs" / "model_inputs"

REQUIRED_ROW_FIELDS = (
    "input_id",
    "layer",
    "business_purpose",
    "data_domain",
    "source_id",
    "operation",
    "role",
    "readiness",
    "symbol_or_series",
    "window_cap",
    "row_cap",
    "requires_user_authorization",
    "allowed_next_gate",
    "forbidden_claims",
    "closure_test",
    "notes",
)

LAYER1_P0_SERIES = frozenset({"DGS10", "T10Y3M", "VIXCLS", "SP500", "DFII10"})
DCP06_CLEAN_REPLAY_PROVEN = frozenset({"DGS10", "BAA10Y", "VIXCLS", "SPY", "088691"})

WHITELIST_FILES = {
    "layer1": MODEL_INPUTS / "layer1_source_whitelist.yaml",
    "layer2": MODEL_INPUTS / "layer2_source_whitelist.yaml",
    "layer3": MODEL_INPUTS / "layer3_anchor_source_plan.yaml",
    "layer4": MODEL_INPUTS / "layer4_market_source_plan.yaml",
    "layer5": MODEL_INPUTS / "layer5_instrument_source_plan.yaml",
}


def _load_whitelist_rows(layer_key: str) -> list[dict[str, Any]]:
    path = WHITELIST_FILES[layer_key]
    if not path.is_file():
        raise FileNotFoundError(f"missing whitelist file: {path.relative_to(PROJECT_ROOT)}")
    doc = load_yaml(path)
    rows = doc.get("rows") or []
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain non-empty rows list")
    return rows


def _series_value(row: dict[str, Any]) -> str:
    sym = row.get("symbol_or_series")
    if isinstance(sym, list):
        return str(sym[0]) if sym else ""
    return str(sym or "")


def _all_whitelist_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in WHITELIST_FILES:
        rows.extend(_load_whitelist_rows(key))
    return rows


def _run() -> list[str]:
    errors: list[str] = []
    try:
        for layer_key in WHITELIST_FILES:
            for row in _load_whitelist_rows(layer_key):
                missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
                if missing:
                    errors.append(f"{layer_key}/{row.get('input_id')}: missing {missing}")

        rows_l1 = _load_whitelist_rows("layer1")
        proven = [r for r in rows_l1 if _series_value(r) in DCP06_CLEAN_REPLAY_PROVEN]
        found = {_series_value(r) for r in proven}
        if found != DCP06_CLEAN_REPLAY_PROVEN:
            errors.append(f"DCP-06 proven series mismatch: {sorted(found)}")
        for row in proven:
            if row.get("readiness") != "clean_replay_proven":
                errors.append(f"{row.get('input_id')}: readiness != clean_replay_proven")
            if row.get("readiness") == "production_candidate":
                errors.append(f"{row.get('input_id')}: must not be production_candidate")
            if row.get("row_cap") is None or int(row["row_cap"]) <= 0:
                errors.append(f"{row.get('input_id')}: row_cap invalid")
            if row.get("window_cap") is None:
                errors.append(f"{row.get('input_id')}: window_cap missing")

        macro_rows = [r for r in rows_l1 if r.get("data_domain") == "macro_supplementary"]
        if not macro_rows:
            errors.append("macro_supplementary domain missing")
        for row in macro_rows:
            if row.get("source_id") != "akshare":
                errors.append(f"{row.get('input_id')}: macro_supplementary source != akshare")
            if row.get("role") == "primary_candidate":
                errors.append(f"{row.get('input_id')}: macro_supplementary is primary_candidate")
            if row.get("readiness") == "production_candidate":
                errors.append(f"{row.get('input_id')}: macro_supplementary production_candidate")
            series = _series_value(row)
            if series in LAYER1_P0_SERIES:
                errors.append(
                    f"macro_supplementary must not claim FRED P0 series {series}"
                )

        rows_l4 = _load_whitelist_rows("layer4")
        us = next((r for r in rows_l4 if r.get("input_id") == "L4-US-DEFERRED"), None)
        if us is None:
            errors.append("L4-US-DEFERRED missing")
        else:
            if us.get("readiness") != "deferred":
                errors.append("L4-US-DEFERRED readiness != deferred")
            if us.get("role") != "deferred":
                errors.append("L4-US-DEFERRED role != deferred")
            if _series_value(us) != "US":
                errors.append("L4-US-DEFERRED symbol_or_series != US")

        all_rows = _all_whitelist_rows()
        ak_rows = [r for r in all_rows if r.get("source_id") == "akshare"]
        if not ak_rows:
            errors.append("no akshare rows in whitelist")
        for row in ak_rows:
            if row.get("role") == "primary_candidate":
                errors.append(f"akshare primary_candidate: {row.get('input_id')}")

        fred_rows = [r for r in all_rows if r.get("source_id") == "fred"]
        if not fred_rows:
            errors.append("no fred rows in whitelist")
        for row in fred_rows:
            if row.get("readiness") == "production_candidate":
                errors.append(f"fred production_candidate: {row.get('input_id')}")
            if row.get("requires_user_authorization") is not True:
                errors.append(
                    f"fred requires_user_authorization != True: {row.get('input_id')}"
                )
    except (FileNotFoundError, ValueError) as exc:
        errors.append(str(exc))
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
        print("PASS: model input whitelist YAML")
        return 0
    print("FAIL: model input whitelist YAML")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
