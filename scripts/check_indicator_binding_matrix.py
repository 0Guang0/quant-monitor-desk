#!/usr/bin/env python3
"""M-G1-03 P1-01 — 62×指标绑定矩阵校验（SSOT: indicator_binding_registry.yaml）."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "specs/layer1_axes/indicator_binding_registry.yaml"
AXES_DIR = REPO_ROOT / "specs/layer1_axes/restructured_axes_v1_1"
EXPECTED_ROWS = 62

_REQUIRED_ROW_KEYS = (
    "indicator_id",
    "axis_id",
    "primary_source",
    "data_domain",
    "adapter_entry",
    "cold_start_policy",
    "incremental_watermark",
    "backfill_available",
    "formula",
    "cabin",
    "adr_id",
    "feature_outputs_expected",
)

_COLD_START_POLICIES = frozenset(
    {"full_load", "bounded_backfill", "incremental_only", "adr_deferred"}
)
_CABINS = frozenset({"PRIMARY", "VALIDATION", "BLINDSPOT", "FORBIDDEN", "SHADOW"})


def _collect_axis_indicator_ids() -> set[str]:
    ids: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if "indicator_id" in node and isinstance(node["indicator_id"], str):
                ids.add(node["indicator_id"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for spec_path in sorted(AXES_DIR.glob("*/*_indicator_spec.yaml")):
        payload = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        walk(payload)
    return ids


def _validate_row(row: dict, *, index: int, strict: bool) -> list[str]:
    errors: list[str] = []
    missing = [key for key in _REQUIRED_ROW_KEYS if key not in row]
    if missing:
        errors.append(
            f"row {index} indicator_id={row.get('indicator_id')!r} missing {missing}"
        )
        return errors
    if row["cold_start_policy"] not in _COLD_START_POLICIES:
        errors.append(
            f"row {index} {row['indicator_id']!r} invalid cold_start_policy"
        )
    if row["cabin"] not in _CABINS:
        errors.append(f"row {index} {row['indicator_id']!r} invalid cabin")
    outputs = row["feature_outputs_expected"]
    if not isinstance(outputs, list) or not outputs:
        errors.append(
            f"row {index} {row['indicator_id']!r} feature_outputs_expected empty"
        )
    if strict and row["adr_id"] == "PENDING":
        errors.append(f"row {index} {row['indicator_id']!r} adr_id still PENDING")
    return errors


def validate_registry(*, strict: bool = False) -> list[str]:
    errors: list[str] = []
    if not REGISTRY.is_file():
        return [f"missing registry {REGISTRY.relative_to(REPO_ROOT)}"]

    payload = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    rows = payload.get("bindings") or []
    if not isinstance(rows, list):
        return ["registry bindings must be a list"]

    if len(rows) != EXPECTED_ROWS:
        errors.append(f"expected {EXPECTED_ROWS} rows, got {len(rows)}")

    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row {index} must be a mapping")
            continue
        errors.extend(_validate_row(row, index=index, strict=strict))
        indicator_id = row.get("indicator_id")
        if isinstance(indicator_id, str):
            if indicator_id in seen:
                errors.append(f"duplicate indicator_id {indicator_id!r}")
            seen.add(indicator_id)

    axis_ids = _collect_axis_indicator_ids()
    missing_from_registry = sorted(axis_ids - seen)
    extra_in_registry = sorted(seen - axis_ids)
    if missing_from_registry:
        errors.append(
            "registry missing axis indicator_ids: "
            + ", ".join(missing_from_registry[:5])
            + (f" (+{len(missing_from_registry) - 5} more)" if len(missing_from_registry) > 5 else "")
        )
    if extra_in_registry:
        errors.append(
            "registry has unknown indicator_ids: "
            + ", ".join(extra_in_registry[:5])
            + (f" (+{len(extra_in_registry) - 5} more)" if len(extra_in_registry) > 5 else "")
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Layer1 indicator binding matrix")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Phase 2: adr_id must not be PENDING; all bindings complete",
    )
    args = parser.parse_args(argv)
    errors = validate_registry(strict=args.strict)
    if errors:
        print("Indicator binding matrix check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    mode = "strict" if args.strict else "phase1"
    print(
        f"Indicator binding matrix check passed ({mode}, {EXPECTED_ROWS} rows)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
