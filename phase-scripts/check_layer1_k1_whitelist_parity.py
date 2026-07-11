#!/usr/bin/env python3
"""Layer1 K1 whitelist 与 clean reader cap / P0 绑定对齐（阶段性 · 非业务 pytest）

功能：
  1）resolve_read_limit / resolve_window_cap 与 layer1_source_whitelist.yaml 对账；
  2）P0 clean 绑定 source_id 与 whitelist 行对齐（含 SPY / macro_supplementary）。
  对应原 test_dcp06Reader_capsMatchK1WhitelistYaml /
  test_dcp06K1_whitelistAlignsP0CleanBindings。

业务价值：
  防止 K1 白名单与 Tier A clean 读路径 / resource_limits 漂移。

退役 / 清理时间（满足任一即可删本文件）：
  1. reader 改为只读 YAML caps、不再维护模块常量；或
  2. 本核对迁入稳定 scripts/production_gate 子步。

运行：
  uv run python phase-scripts/check_layer1_k1_whitelist_parity.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.layer1_axes.clean_observation_reader import (  # noqa: E402
    P0_MACRO_DB_KEYS,
    resolve_read_limit,
    resolve_window_cap,
)
from tests.contract_gate_support import load_yaml  # noqa: E402

WHITELIST = PROJECT_ROOT / "specs" / "model_inputs" / "layer1_source_whitelist.yaml"

P0_BINDINGS: tuple[tuple[str, str, str], ...] = (
    ("ENV-E1-DGS10", "DGS10", "fred"),
    ("CRD.CS1.BAA10Y", "BAA10Y", "fred"),
    ("RA.R1.VIXCLS_30D_IMPLIED_VOL", "VIXCLS", "fred"),
    ("SEN-S1-COT_LF_NET", "088691", "cftc_cot"),
)

SPEC_TO_SERIES = {
    "ENV-E1-DGS10": "DGS10",
    "CRD.CS1.BAA10Y": "BAA10Y",
    "RA.R1.VIXCLS_30D_IMPLIED_VOL": "VIXCLS",
    "SEN-S1-COT_LF_NET": "088691",
    "LIQ.B-I1.AMIHUD_ILLIQ": "SPY",
}


def _parse_yaml_cap(value: object) -> int:
    if isinstance(value, int):
        return value
    return int(str(value).rstrip("dw"))


def _by_series(doc: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in doc.get("rows") or []:
        sym = row.get("symbol_or_series")
        key = str(sym[0] if isinstance(sym, list) else sym)
        out[key] = row
    return out


def _run() -> list[str]:
    errors: list[str] = []
    doc = load_yaml(WHITELIST)
    by_series = _by_series(doc)

    for spec_id, series in SPEC_TO_SERIES.items():
        row = by_series.get(series)
        if row is None:
            errors.append(f"missing whitelist row for {series}")
            continue
        if resolve_read_limit(spec_id) != int(row["row_cap"]):
            errors.append(
                f"{spec_id}: read_limit={resolve_read_limit(spec_id)} "
                f"yaml_row_cap={row['row_cap']!r}"
            )
        yaml_window = _parse_yaml_cap(row["window_cap"])
        if resolve_window_cap(spec_id) != yaml_window:
            errors.append(
                f"{spec_id}: window_cap={resolve_window_cap(spec_id)} "
                f"yaml={yaml_window}"
            )

    for spec_id, db_key, source_id in P0_BINDINGS:
        if P0_MACRO_DB_KEYS.get(spec_id) != db_key:
            errors.append(f"{spec_id}: P0_MACRO_DB_KEYS mismatch db_key={db_key}")
        row = by_series.get(db_key)
        if row is None:
            errors.append(f"missing whitelist row for {db_key}")
            continue
        if row.get("source_id") != source_id:
            errors.append(
                f"{db_key}: source_id={row.get('source_id')!r} expected={source_id!r}"
            )
        if row.get("role") == "validation_only" and source_id != "akshare":
            errors.append(f"{db_key}: unexpected validation_only role")

    liq = by_series.get("SPY")
    if liq is None:
        errors.append("missing whitelist row for SPY")
    else:
        if liq.get("source_id") != "alpha_vantage":
            errors.append(f"SPY source_id={liq.get('source_id')!r}")
        if liq.get("role") != "primary_candidate":
            errors.append(f"SPY role={liq.get('role')!r}")

    macro_supp = [
        r for r in (doc.get("rows") or []) if r.get("data_domain") == "macro_supplementary"
    ]
    if not macro_supp:
        errors.append("macro_supplementary rows missing")
    elif any(r.get("role") == "primary_candidate" for r in macro_supp):
        errors.append("macro_supplementary has primary_candidate")
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
        print("PASS: layer1 K1 whitelist parity")
        return 0
    print("FAIL: layer1 K1 whitelist parity")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
