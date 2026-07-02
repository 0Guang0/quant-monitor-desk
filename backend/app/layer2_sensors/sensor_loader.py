"""Load cross_asset_registry from staged fixture YAML (Batch 3 / 019)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.layer2_sensors.double_count_guard import validate_registry_double_count_rules
from backend.app.layer2_sensors.models import CrossAssetLoadResult, CrossAssetRegistryEntry
from backend.app.layer2_sensors.schema_ddl import ensure_layer2_staging_tables

STAGED_REGISTRY_FIXTURE = (
    PROJECT_ROOT / "tests" / "fixtures" / "layer2_cross_asset_registry_fixture.yaml"
)
CLEAN_REPLAY_REGISTRY_FIXTURE = (
    PROJECT_ROOT / "tests" / "fixtures" / "layer2_cross_asset_registry_clean_replay.yaml"
)

P0_CLEAN_REPLAY_ASSET_IDS = frozenset({"L2-VIX"})

CONTRACT_ASSET_GROUPS = frozenset(
    {
        "USD",
        "Rates",
        "Metals",
        "Energy",
        "CreditETF",
        "EquityETF",
        "Volatility",
        "Shipping",
        "Futures",
    }
)

CONTRACT_REQUIRED_REGISTRY_FIELDS = (
    "asset_id",
    "display_name_cn",
    "asset_group",
    "asset_type",
    "market",
    "primary_source",
    "validation_source",
    "fallback_policy",
    "is_axis_input",
    "display_only",
    "eligible_for_model",
    "double_count_guard",
)

ALLOWED_PRIMARY_SOURCES_STAGED = frozenset({"staged_fixture"})
ALLOWED_PRIMARY_SOURCES_CLEAN_REPLAY = frozenset({"fred", "staged_fixture"})


class CrossAssetRegistryLoadError(ValueError):
    """Registry YAML failed validation."""


class CrossAssetRegistryLoader:
    """Parse cross_asset_registry staged fixture into typed entries."""

    def load(self, *, registry_path: Path | None = None) -> CrossAssetLoadResult:
        path = (registry_path or STAGED_REGISTRY_FIXTURE).resolve()
        if not path.is_file():
            raise CrossAssetRegistryLoadError(f"missing registry file: {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise CrossAssetRegistryLoadError("registry root must be a mapping")

        mode = str(raw.get("mode", ""))
        if mode not in ("staged_fixture_only", "production_clean_replay"):
            raise CrossAssetRegistryLoadError(
                f"registry mode {mode!r} is not allowed; "
                "only staged_fixture_only or production_clean_replay on 019/DCP-07"
            )
        allowed_primary = (
            ALLOWED_PRIMARY_SOURCES_CLEAN_REPLAY
            if mode == "production_clean_replay"
            else ALLOWED_PRIMARY_SOURCES_STAGED
        )

        version = str(raw.get("version", "unknown"))
        assets_raw = raw.get("assets")
        if not isinstance(assets_raw, list) or not assets_raw:
            raise CrossAssetRegistryLoadError("registry must contain a non-empty assets list")

        entries: list[CrossAssetRegistryEntry] = []
        for item in assets_raw:
            if not isinstance(item, dict):
                raise CrossAssetRegistryLoadError("each asset entry must be a mapping")
            entries.append(_parse_asset(item, mode=mode, allowed_primary=allowed_primary))

        validate_registry_double_count_rules(entries)
        _assert_contract_fields(entries)
        _assert_unique_instrument_ids(entries)
        return CrossAssetLoadResult(
            assets=tuple(entries),
            registry_version=version,
            mode=mode,
        )


def registry_row_to_db_tuple(entry: CrossAssetRegistryEntry) -> list:
    return [
        entry.asset_id,
        entry.display_name,
        entry.display_name_cn,
        entry.asset_group,
        entry.asset_type,
        entry.market,
        entry.instrument_id,
        entry.layer5_instrument_id,
        entry.primary_source,
        entry.validation_source,
        entry.fallback_policy,
        entry.mapped_axis,
        entry.is_axis_input,
        entry.display_only,
        entry.eligible_for_model,
        entry.double_count_guard,
        datetime.now(UTC),
    ]


class CrossAssetRegistryWriter:
    """Sync staged registry entries to sandbox cross_asset_registry table."""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._cm = conn_manager
        self._wm = WriteManager(conn_manager, DbValidationGate(conn_manager))

    def sync_registry(
        self,
        entries: tuple[CrossAssetRegistryEntry, ...],
        *,
        validation_report_id: str,
        con: duckdb.DuckDBPyConnection | None = None,
    ):
        if con is None:
            with self._cm.writer() as writer_con:
                ensure_layer2_staging_tables(writer_con)
                return self._sync_on_connection(
                    writer_con,
                    entries=entries,
                    validation_report_id=validation_report_id,
                )
        ensure_layer2_staging_tables(con)
        return self._sync_on_connection(
            con, entries=entries, validation_report_id=validation_report_id
        )

    def _sync_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        entries: tuple[CrossAssetRegistryEntry, ...],
        validation_report_id: str,
    ):
        staging = f"stg_l2_reg_{uuid.uuid4().hex[:8]}"
        con.execute(f"CREATE TABLE {staging} AS SELECT * FROM cross_asset_registry WHERE 1=0")
        for entry in entries:
            con.execute(
                f"INSERT INTO {staging} VALUES ({','.join(['?'] * 17)})",
                registry_row_to_db_tuple(entry),
            )
        req = WriteRequest(
            run_id="layer2-staged-run",
            job_id="layer2-registry-sync",
            target_table="cross_asset_registry",
            staging_table=staging,
            write_mode="upsert_by_pk",
            primary_keys=("asset_id",),
            validation_report_id=validation_report_id,
            source_used="layer2_staged_fixture",
            data_domain="layer2_cross_asset_registry",
        )
        return self._wm.write(req, con=con)


def _parse_asset(
    item: dict[str, Any],
    *,
    mode: str,
    allowed_primary: frozenset[str],
) -> CrossAssetRegistryEntry:
    asset_id = str(item.get("asset_id", "")).strip()
    if not asset_id:
        raise CrossAssetRegistryLoadError("asset entry missing asset_id")

    asset_group = str(item.get("asset_group", ""))
    if asset_group not in CONTRACT_ASSET_GROUPS:
        raise CrossAssetRegistryLoadError(
            f"asset {asset_id!r} has invalid asset_group {asset_group!r}"
        )

    primary_source = str(item.get("primary_source", ""))
    if primary_source in ("none", ""):
        raise CrossAssetRegistryLoadError(
            f"asset {asset_id!r} primary_source must not be empty/none in staged registry"
        )
    if primary_source not in allowed_primary:
        raise CrossAssetRegistryLoadError(
            f"asset {asset_id!r} primary_source {primary_source!r} not allowed for mode {mode!r}"
        )
    if mode == "production_clean_replay" and primary_source == "fred":
        if asset_id not in P0_CLEAN_REPLAY_ASSET_IDS:
            raise CrossAssetRegistryLoadError(
                f"asset {asset_id!r} primary_source fred is P0-whitelist only (L2-VIX)"
            )

    return CrossAssetRegistryEntry(
        asset_id=asset_id,
        display_name=str(item.get("display_name", asset_id)),
        display_name_cn=str(item.get("display_name_cn", asset_id)),
        asset_group=asset_group,
        asset_type=str(item.get("asset_type", "")),
        market=str(item.get("market", "")),
        instrument_id=str(item.get("instrument_id", "")),
        layer5_instrument_id=str(item.get("layer5_instrument_id", "")),
        primary_source=primary_source,
        validation_source=str(item.get("validation_source", "none")),
        fallback_policy=str(item.get("fallback_policy", "none")),
        mapped_axis=str(item.get("mapped_axis", "")),
        is_axis_input=bool(item.get("is_axis_input", False)),
        display_only=bool(item.get("display_only", False)),
        eligible_for_model=bool(item.get("eligible_for_model", False)),
        double_count_guard=str(item.get("double_count_guard", "none")),
        contract_code=str(item.get("contract_code", "")),
        roll_rule=str(item.get("roll_rule", "")),
    )


def _assert_unique_instrument_ids(entries: list[CrossAssetRegistryEntry]) -> None:
    seen: dict[str, str] = {}
    for entry in entries:
        if not entry.instrument_id:
            continue
        prior = seen.get(entry.instrument_id)
        if prior and prior != entry.asset_id:
            raise CrossAssetRegistryLoadError(
                f"duplicate instrument_id {entry.instrument_id!r} "
                f"for assets {prior!r} and {entry.asset_id!r}"
            )
        seen[entry.instrument_id] = entry.asset_id


def _assert_contract_fields(entries: list[CrossAssetRegistryEntry]) -> None:
    for entry in entries:
        payload = {
            "asset_id": entry.asset_id,
            "display_name_cn": entry.display_name_cn,
            "asset_group": entry.asset_group,
            "asset_type": entry.asset_type,
            "market": entry.market,
            "primary_source": entry.primary_source,
            "validation_source": entry.validation_source,
            "fallback_policy": entry.fallback_policy,
            "is_axis_input": entry.is_axis_input,
            "display_only": entry.display_only,
            "eligible_for_model": entry.eligible_for_model,
            "double_count_guard": entry.double_count_guard,
        }
        for field in CONTRACT_REQUIRED_REGISTRY_FIELDS:
            value = payload[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                raise CrossAssetRegistryLoadError(
                    f"asset {entry.asset_id!r} missing contract field {field!r}"
                )
