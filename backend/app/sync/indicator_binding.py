"""Layer1 indicator binding registry loader (M-G1-03 §9.1)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

ColdStartPolicy = Literal[
    "full_load", "bounded_backfill", "incremental_only", "adr_deferred"
]
Cabin = Literal["PRIMARY", "VALIDATION", "BLINDSPOT", "FORBIDDEN", "SHADOW"]

REGISTRY_PATH = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "layer1_axes"
    / "indicator_binding_registry.yaml"
)

_REQUIRED_ROW_KEYS = frozenset(
    {
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
    }
)

_COLD_START_POLICIES = frozenset(
    {"full_load", "bounded_backfill", "incremental_only", "adr_deferred"}
)
_CABINS = frozenset({"PRIMARY", "VALIDATION", "BLINDSPOT", "FORBIDDEN", "SHADOW"})


@dataclass(frozen=True)
class UnknownIndicatorError(LookupError):
    indicator_id: str
    error_code: str = "CAPABILITY_MISSING"
    docs_anchor: str = "docs/ops/ERROR_CODE_GUIDE.md#capability-missing"

    def __str__(self) -> str:
        return (
            f"unknown indicator_id={self.indicator_id!r} "
            f"error_code={self.error_code} docs_anchor={self.docs_anchor}"
        )


@dataclass(frozen=True)
class IndicatorBinding:
    indicator_id: str
    axis_id: str
    primary_source: str
    data_domain: str
    adapter_entry: str
    cold_start_policy: ColdStartPolicy
    incremental_watermark: str
    backfill_available: bool
    formula: str | None
    cabin: Cabin
    adr_id: str
    feature_outputs_expected: tuple[str, ...]


def _validate_row(raw: dict[str, Any], *, index: int) -> None:
    missing = _REQUIRED_ROW_KEYS - raw.keys()
    if missing:
        raise ValueError(
            f"registry row {index} indicator_id={raw.get('indicator_id')!r} "
            f"missing keys: {sorted(missing)}"
        )
    policy = raw["cold_start_policy"]
    if policy not in _COLD_START_POLICIES:
        raise ValueError(
            f"registry row {index} invalid cold_start_policy={policy!r}"
        )
    cabin = raw["cabin"]
    if cabin not in _CABINS:
        raise ValueError(f"registry row {index} invalid cabin={cabin!r}")
    outputs = raw["feature_outputs_expected"]
    if not isinstance(outputs, list) or not outputs:
        raise ValueError(
            f"registry row {index} feature_outputs_expected must be non-empty list"
        )


def _row_to_binding(raw: dict[str, Any]) -> IndicatorBinding:
    return IndicatorBinding(
        indicator_id=str(raw["indicator_id"]),
        axis_id=str(raw["axis_id"]),
        primary_source=str(raw["primary_source"]),
        data_domain=str(raw["data_domain"]),
        adapter_entry=str(raw["adapter_entry"]),
        cold_start_policy=raw["cold_start_policy"],
        incremental_watermark=str(raw["incremental_watermark"]),
        backfill_available=bool(raw["backfill_available"]),
        formula=raw["formula"] if raw["formula"] is not None else None,
        cabin=raw["cabin"],
        adr_id=str(raw["adr_id"]),
        feature_outputs_expected=tuple(str(x) for x in raw["feature_outputs_expected"]),
    )


def _load_registry_rows(path: Path = REGISTRY_PATH) -> list[IndicatorBinding]:
    if not path.is_file():
        raise FileNotFoundError(f"missing indicator binding registry: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = payload.get("bindings") or []
    if not isinstance(rows, list):
        raise ValueError("registry bindings must be a list")
    bindings: list[IndicatorBinding] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise ValueError(f"registry row {index} must be a mapping")
        _validate_row(raw, index=index)
        bindings.append(_row_to_binding(raw))
    return bindings


def load_all_bindings(*, path: Path = REGISTRY_PATH) -> tuple[IndicatorBinding, ...]:
    """Load and validate every binding row from the registry YAML."""
    return tuple(_load_registry_rows(path))


def load_binding(
    indicator_id: str, *, path: Path = REGISTRY_PATH
) -> IndicatorBinding:
    """Return one binding; unknown indicator_id fails closed."""
    for binding in _load_registry_rows(path):
        if binding.indicator_id == indicator_id:
            return binding
    raise UnknownIndicatorError(indicator_id=indicator_id)


def bindings_for_source(
    source_id: str, *, path: Path = REGISTRY_PATH
) -> tuple[IndicatorBinding, ...]:
    """Return registry rows whose primary_source matches source_id."""
    return tuple(
        binding
        for binding in load_all_bindings(path=path)
        if binding.primary_source == source_id
    )
