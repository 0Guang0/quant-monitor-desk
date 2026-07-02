"""Build market_registry / calendar / breadth rows from staged fixture."""

from __future__ import annotations

import json
from dataclasses import fields
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.layer4_markets.lineage import Layer4LineageBuilder
from backend.app.layer4_markets.models import (
    MarketBreadthSnapshotRow,
    MarketCalendarRow,
    MarketRegistryRow,
    MarketStructureBuildResult,
)

STAGED_LAYER4_BUNDLE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "layer4_staged_market"

_RULE_VERSION = "layer4_market_staged_v1"
_CODE_VERSION = "layer4-staged-v1"
_CLEAN_RULE_VERSION = "layer4_market_tier_a_clean_v1"
_CLEAN_CODE_VERSION = "layer4-tier-a-clean-v1"

# ponytail: explicit frozensets for AC-022-7 boundary test; upgrade path: contract yaml loader
FORBIDDEN_LAYER5_HISTORY_FIELDS = frozenset(
    {
        "instrument_id",
        "bar_open",
        "bar_close",
        "bar_high",
        "bar_low",
        "ohlcv_history",
        "security_bar",
        "layer5_mapping_views",
    }
)
FORBIDDEN_LAYER1_STANDARDIZATION_FIELDS = frozenset(
    {
        "raw_value",
        "z_score",
        "delta",
        "percentile",
        "state_label",
        "standardization_suite",
    }
)

REGISTRY_SEEDS: tuple[MarketRegistryRow, ...] = (
    MarketRegistryRow(
        "CN_A",
        "A股",
        "equity_market",
        "Asia/Shanghai",
        "StagedCNAMarketAdapter",
        True,
    ),
    MarketRegistryRow(
        "US_EQ",
        "美股",
        "equity_market",
        "America/New_York",
        "USEquityMarketAdapter",
        True,
    ),
    MarketRegistryRow(
        "HK_EQ",
        "港股",
        "equity_market",
        "Asia/Hong_Kong",
        "HKMarketAdapter",
        True,
    ),
    MarketRegistryRow(
        "CN_FUT",
        "中国期货",
        "futures_market",
        "Asia/Shanghai",
        "ChinaFuturesMarketAdapter",
        True,
    ),
    MarketRegistryRow(
        "GLOBAL_FUT",
        "全球期货",
        "futures_market",
        "UTC",
        "GlobalFuturesMarketAdapter",
        True,
    ),
    MarketRegistryRow(
        "GLOBAL_OPTIONS",
        "期权市场",
        "options_market",
        "America/New_York",
        "OptionsMarketAdapter",
        True,
    ),
    MarketRegistryRow(
        "FX",
        "外汇",
        "fx_market",
        "UTC",
        "FXMarketAdapter",
        True,
    ),
    MarketRegistryRow(
        "CRYPTO_OPTIONAL",
        "加密资产",
        "optional_market",
        "UTC",
        "CryptoOptionalAdapter",
        False,
    ),
)

_BREADTH_REQUIRED = (
    "market_id",
    "trade_date",
    "advancers",
    "decliners",
    "total_amount",
    "breadth_label",
    "source",
    "quality_flag",
)
_CALENDAR_SOURCE_FIELDS = ("source", "quality_flag")


class Layer4MarketError(ValueError):
    """Invalid Layer 4 staged market structure build."""


def seed_registry_rows() -> tuple[MarketRegistryRow, ...]:
    """Return frozen registry seed rows (8 market_id metadata)."""
    return REGISTRY_SEEDS


class StagedFixtureMarketAdapter:
    """Staged fixture adapter for CN_A / US_EQ market structure rows."""

    def __init__(self, market_id: str) -> None:
        self.market_id = market_id

    def load_calendar(self, bundle_dir: Path) -> tuple[MarketCalendarRow, ...]:
        return _load_calendar_rows(bundle_dir)

    def load_breadth(self, bundle_dir: Path, trade_date: date) -> MarketBreadthSnapshotRow:
        return _load_breadth_row(bundle_dir, trade_date)


class StagedCNAMarketAdapter(StagedFixtureMarketAdapter):
    """Staged fixture adapter for CN_A market structure rows."""

    def __init__(self) -> None:
        super().__init__("CN_A")


class MarketStructureBuilder:
    """Assemble registry/calendar/breadth + lineage from staged fixture bundle."""

    def __init__(
        self,
        *,
        rule_version: str = _RULE_VERSION,
        code_version: str = _CODE_VERSION,
    ) -> None:
        self._lineage_builder = Layer4LineageBuilder()
        self._rule_version = rule_version
        self._code_version = code_version
        self._cna_adapter = StagedCNAMarketAdapter()
        self._us_eq_adapter = StagedFixtureMarketAdapter("US_EQ")

    def build(
        self,
        *,
        market_id: str,
        trade_date: date,
        as_of: datetime,
        bundle_dir: Path | None = None,
        upstream_snapshot_ids: tuple[str, ...] = (),
        source_mode: str = "staged_fixture_only",
        clean_con=None,
    ) -> MarketStructureBuildResult:
        registry_rows = seed_registry_rows()
        if market_id not in {row.market_id for row in registry_rows}:
            raise Layer4MarketError(f"unknown market_id {market_id!r}")

        if market_id == "US_EQ":
            from backend.app.ops.data_health_profiles.us_trading_calendar import is_trading_day

            if not is_trading_day(trade_date):
                raise Layer4MarketError(
                    f"snapshot blocked on non-trading day for {market_id!r} {trade_date}"
                )

        if source_mode == "tier_a_clean":
            return self._build_tier_a_clean(
                market_id=market_id,
                trade_date=trade_date,
                as_of=as_of,
                clean_con=clean_con,
                registry_rows=registry_rows,
                upstream_snapshot_ids=upstream_snapshot_ids,
            )

        if source_mode != "staged_fixture_only":
            raise Layer4MarketError(
                f"source_mode {source_mode!r} is not supported; "
                "use staged_fixture_only or tier_a_clean"
            )

        root = _resolve_bundle_root(bundle_dir)
        manifest = _read_manifest(root)
        fetch_ids, content_hashes = _manifest_provenance(manifest)

        adapter = _adapter_for_market(market_id, self._cna_adapter, self._us_eq_adapter)
        calendar_rows = adapter.load_calendar(root)
        breadth_row = adapter.load_breadth(root, trade_date)

        return self._finalize_market_build(
            market_id=market_id,
            trade_date=trade_date,
            as_of=as_of,
            registry_rows=registry_rows,
            calendar_rows=calendar_rows,
            breadth_row=breadth_row,
            source_dataset_ids=(f"staged:layer4_market:{market_id}",),
            fetch_ids=fetch_ids,
            content_hashes=content_hashes,
            rule_version=self._rule_version,
            code_version=self._code_version,
            upstream_snapshot_ids=upstream_snapshot_ids,
        )

    def _build_tier_a_clean(
        self,
        *,
        market_id: str,
        trade_date: date,
        as_of: datetime,
        clean_con,
        registry_rows: tuple[MarketRegistryRow, ...],
        upstream_snapshot_ids: tuple[str, ...],
    ) -> MarketStructureBuildResult:
        if market_id != "US_EQ":
            raise Layer4MarketError(
                f"tier_a_clean source_mode only supports US_EQ in this ticket, got {market_id!r}"
            )
        if clean_con is None:
            raise Layer4MarketError("tier_a_clean build requires clean_con duckdb connection")

        from backend.app.layer4_markets.clean_read import (
            USEquityCleanMarketAdapter,
            collect_clean_lineage_provenance,
        )

        adapter = USEquityCleanMarketAdapter(clean_con)
        calendar_rows = adapter.load_calendar(trade_date, as_of)
        breadth_row = adapter.load_breadth(trade_date, as_of)

        source_dataset_ids, fetch_ids, content_hashes = collect_clean_lineage_provenance(
            clean_con,
            market_id=market_id,
            trade_date=trade_date,
        )
        return self._finalize_market_build(
            market_id=market_id,
            trade_date=trade_date,
            as_of=as_of,
            registry_rows=registry_rows,
            calendar_rows=calendar_rows,
            breadth_row=breadth_row,
            source_dataset_ids=source_dataset_ids,
            fetch_ids=fetch_ids,
            content_hashes=content_hashes,
            rule_version=_CLEAN_RULE_VERSION,
            code_version=_CLEAN_CODE_VERSION,
            upstream_snapshot_ids=upstream_snapshot_ids,
        )

    def _finalize_market_build(
        self,
        *,
        market_id: str,
        trade_date: date,
        as_of: datetime,
        registry_rows: tuple[MarketRegistryRow, ...],
        calendar_rows: tuple[MarketCalendarRow, ...],
        breadth_row: MarketBreadthSnapshotRow,
        source_dataset_ids: tuple[str, ...],
        fetch_ids: tuple[str, ...],
        content_hashes: tuple[str, ...],
        rule_version: str,
        code_version: str,
        upstream_snapshot_ids: tuple[str, ...],
    ) -> MarketStructureBuildResult:
        calendar_for_day = _calendar_for_day(
            calendar_rows, market_id=market_id, trade_date=trade_date
        )
        _reject_future_observation(
            as_of=as_of,
            market_id=market_id,
            label="calendar",
            observation_ts=calendar_for_day.as_of_timestamp,
        )
        _reject_future_observation(
            as_of=as_of,
            market_id=market_id,
            label="breadth",
            observation_ts=breadth_row.as_of_timestamp,
        )

        window_start = min(calendar_for_day.as_of_timestamp, breadth_row.as_of_timestamp)
        window_end = max(calendar_for_day.as_of_timestamp, breadth_row.as_of_timestamp)
        param_hash = Layer4LineageBuilder.parameter_hash_for(
            rule_version=rule_version,
            inputs=(market_id, trade_date.isoformat(), str(breadth_row.advancers)),
        )
        lineage = self._lineage_builder.build(
            snapshot_id=f"l4-market-{market_id}-{trade_date.isoformat()}",
            snapshot_type="market_breadth_snapshot",
            as_of=as_of,
            input_window_start=window_start,
            input_window_end=window_end,
            source_dataset_ids=source_dataset_ids,
            source_fetch_ids=fetch_ids,
            source_content_hashes=content_hashes,
            rule_version=rule_version,
            parameter_hash=param_hash,
            code_version=code_version,
            upstream_snapshot_ids=upstream_snapshot_ids,
        )

        return MarketStructureBuildResult(
            registry_rows=registry_rows,
            calendar_rows=calendar_rows,
            breadth_row=breadth_row,
            lineage_envelope=lineage,
        )


def collect_result_field_names(result: MarketStructureBuildResult) -> set[str]:
    """ponytail: flat field-name scan for AC-022-7; ceiling O(rows*fields)."""
    names: set[str] = set()
    for row in (*result.registry_rows, *result.calendar_rows, result.breadth_row):
        for field in fields(row):
            names.add(field.name)
    for field in fields(result.lineage_envelope):
        names.add(field.name)
    return names


def _calendar_for_day(
    calendar_rows: tuple[MarketCalendarRow, ...],
    *,
    market_id: str,
    trade_date: date,
) -> MarketCalendarRow:
    if not any(row.market_id == market_id and row.trade_date == trade_date for row in calendar_rows):
        raise Layer4MarketError(
            f"no calendar row for market_id={market_id!r} trade_date={trade_date}"
        )
    calendar_for_day = next(
        row for row in calendar_rows if row.market_id == market_id and row.trade_date == trade_date
    )
    if not calendar_for_day.is_trading_day:
        raise Layer4MarketError(
            f"snapshot blocked on non-trading day for {market_id!r} {trade_date}"
        )
    return calendar_for_day


def _adapter_for_market(
    market_id: str,
    cna: StagedCNAMarketAdapter,
    us_eq: StagedFixtureMarketAdapter,
) -> StagedCNAMarketAdapter | StagedFixtureMarketAdapter:
    if market_id == "CN_A":
        return cna
    if market_id == "US_EQ":
        return us_eq
    raise Layer4MarketError(
        f"no staged adapter for market_id {market_id!r}; only CN_A and US_EQ fixtures are bundled"
    )


def _resolve_bundle_root(bundle_dir: Path | None) -> Path:
    root = (bundle_dir or STAGED_LAYER4_BUNDLE_DIR).resolve()
    try:
        root.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise Layer4MarketError(
            f"bundle_dir must be under project root, got {root!s}"
        ) from exc
    return root


def _read_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        raise Layer4MarketError(f"missing Layer 4 manifest: {manifest_path}")
    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Layer4MarketError(f"invalid yaml in Layer 4 manifest: {manifest_path}") from exc
    if not isinstance(raw, dict):
        raise Layer4MarketError("Layer 4 manifest root must be a mapping")
    mode = str(raw.get("source_mode", ""))
    if mode != "staged_fixture_only":
        raise Layer4MarketError(
            f"source_mode {mode!r} is not staged_fixture_only; "
            "non-staged market source is forbidden on 022"
        )
    return raw


def _manifest_provenance(manifest: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    fetch_raw = manifest.get("source_fetch_ids", [])
    hash_raw = manifest.get("source_content_hashes", [])
    if not isinstance(fetch_raw, list) or not fetch_raw:
        raise Layer4MarketError("Layer 4 manifest missing source_fetch_ids")
    if not isinstance(hash_raw, list) or not hash_raw:
        raise Layer4MarketError("Layer 4 manifest missing source_content_hashes")
    return tuple(str(x) for x in fetch_raw), tuple(str(x) for x in hash_raw)


def _load_calendar_rows(bundle_dir: Path) -> tuple[MarketCalendarRow, ...]:
    calendar_path = bundle_dir / "calendar.json"
    if not calendar_path.is_file():
        raise Layer4MarketError(f"missing calendar fixture: {calendar_path}")
    try:
        raw = json.loads(calendar_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Layer4MarketError(f"invalid calendar json: {calendar_path}") from exc
    if not isinstance(raw, list):
        raise Layer4MarketError("calendar fixture root must be a list")

    seen: set[tuple[str, str]] = set()
    rows: list[MarketCalendarRow] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise Layer4MarketError("calendar entry must be a mapping")
        market_id = str(entry.get("market_id", ""))
        trade_date_raw = entry.get("trade_date")
        if not market_id or trade_date_raw is None:
            raise Layer4MarketError("calendar entry missing market_id or trade_date")
        trade_date = date.fromisoformat(str(trade_date_raw))
        pk = (market_id, trade_date.isoformat())
        if pk in seen:
            raise Layer4MarketError(
                f"duplicate calendar primary key market_id={market_id!r} "
                f"trade_date={trade_date}"
            )
        seen.add(pk)
        for key in _CALENDAR_SOURCE_FIELDS:
            value = entry.get(key)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                raise Layer4MarketError(f"calendar missing required field {key!r}")
        rows.append(
            MarketCalendarRow(
                market_id=market_id,
                trade_date=trade_date,
                is_trading_day=bool(entry.get("is_trading_day", False)),
                session_type=str(entry.get("session_type", "")),
                timezone=str(entry.get("timezone", "")),
                source=str(entry["source"]),
                quality_flag=str(entry["quality_flag"]),
                as_of_timestamp=_parse_ts(entry.get("as_of_timestamp")),
            )
        )
    return tuple(rows)


def _load_breadth_row(bundle_dir: Path, trade_date: date) -> MarketBreadthSnapshotRow:
    breadth_path = bundle_dir / "breadth.json"
    if not breadth_path.is_file():
        raise Layer4MarketError(f"missing breadth fixture: {breadth_path}")
    try:
        entry = json.loads(breadth_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Layer4MarketError(f"invalid breadth json: {breadth_path}") from exc
    if not isinstance(entry, dict):
        raise Layer4MarketError("breadth fixture root must be a mapping")

    row_trade_date = date.fromisoformat(str(entry.get("trade_date", "")))
    if row_trade_date != trade_date:
        raise Layer4MarketError(
            f"breadth trade_date {row_trade_date} does not match requested {trade_date}"
        )

    for key in _BREADTH_REQUIRED:
        value = entry.get(key)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise Layer4MarketError(f"breadth missing required field {key!r}")

    advancers = int(entry["advancers"])
    decliners = int(entry["decliners"])
    total_amount = float(entry["total_amount"])
    if advancers < 0 or decliners < 0 or total_amount < 0:
        raise Layer4MarketError(
            "breadth volume fields must be non-negative "
            f"(advancers={advancers}, decliners={decliners}, total_amount={total_amount})"
        )

    return MarketBreadthSnapshotRow(
        market_id=str(entry["market_id"]),
        trade_date=row_trade_date,
        advancers=advancers,
        decliners=decliners,
        total_amount=total_amount,
        breadth_label=str(entry["breadth_label"]),
        source=str(entry["source"]),
        quality_flag=str(entry["quality_flag"]),
        as_of_timestamp=_parse_ts(entry.get("as_of_timestamp")),
    )


def _parse_ts(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise Layer4MarketError(f"timestamp must be timezone-aware, got naive {parsed!r}")
    return parsed


def _reject_future_observation(
    *,
    as_of: datetime,
    market_id: str,
    label: str,
    observation_ts: datetime,
) -> None:
    if observation_ts > as_of:
        raise Layer4MarketError(
            f"future input blocked for {market_id!r} {label}: "
            f"as_of_timestamp {observation_ts!s} > snapshot as_of {as_of!s}"
        )
