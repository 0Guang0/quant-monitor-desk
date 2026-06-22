"""Layer 2 cross-asset sensor loader, guard, lineage, and staged snapshot tests."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer2_sensors import (
    CrossAssetObservation,
    CrossAssetRegistryLoader,
    CrossAssetRegistryWriter,
    CrossAssetSnapshotBuilder,
    DoubleCountGuardError,
    FuturesRollHandler,
    Layer2LineageBuilder,
    Layer2ObservationWriter,
    Layer2RollEventWriter,
    Layer2SnapshotWriter,
    ResourceGuardBlockedError,
    assert_model_eligible,
)
from backend.app.layer2_sensors.futures_roll import ContractLiquidity
from backend.app.layer2_sensors.lineage import LINEAGE_REQUIRED_FIELDS
from backend.app.layer2_sensors.observation import reject_future_observation
from backend.app.layer2_sensors.schema_ddl import ensure_layer2_staging_tables
from backend.app.layer2_sensors.sensor_loader import STAGED_REGISTRY_FIXTURE

AS_OF = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)
TRADE_DATE = date(2026, 6, 14)
TRADE_DT = datetime(2026, 6, 14, 16, 0, tzinfo=UTC)


def _obs(
    asset_id: str,
    *,
    trade_time: datetime | None = None,
    close: float = 100.0,
    as_of_visibility: datetime | None = None,
    fetch_time: datetime | None = None,
    source: str = "staged_fixture",
) -> CrossAssetObservation:
    tt = trade_time or TRADE_DT
    vis = as_of_visibility or tt
    ft = fetch_time or vis
    return CrossAssetObservation(
        asset_id=asset_id,
        trade_time=tt,
        market="US",
        asset_type="index",
        open=close - 1,
        high=close + 1,
        low=close - 2,
        close=close,
        pre_close=close - 0.5,
        volume=1_000_000.0,
        amount=None,
        open_interest=None,
        source=source,
        as_of_timestamp=vis,
        fetch_time=ft,
    )


def _insert_validation_report(cm: ConnectionManager, report_id: str) -> None:
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review,
                rule_set_id, rule_version,
                source_fetch_ids_json, source_content_hashes_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                report_id,
                "run-layer2",
                "layer2_cross_asset_daily",
                "staged_fixture",
                "PASSED",
                1,
                0,
                0,
                True,
                False,
                "layer2_v1",
                "layer2_sensor_staged_v1",
                json.dumps(["fetch-l2-wm"]),
                json.dumps(["hash-l2-wm"]),
            ],
        )


def test_crossAssetRegistryLoader_stagedFixture_loadsAxisInputAssets() -> None:
    result = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    assert result.mode == "staged_fixture_only"
    vix = next(a for a in result.assets if a.asset_id == "L2-VIX")
    assert vix.is_axis_input is True
    assert vix.display_only is True
    assert vix.eligible_for_model is False
    assert vix.double_count_guard == "layer1_axis_input_display_only"


def test_crossAssetRegistryLoader_rejectsNonStagedMode(tmp_path: Path) -> None:
    bad = tmp_path / "bad_registry.yaml"
    bad.write_text(
        "version: v1\nmode: production_live\nassets:\n"
        "  - asset_id: X\n    display_name_cn: x\n    asset_group: USD\n"
        "    asset_type: index\n    market: US\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="staged_fixture_only"):
        CrossAssetRegistryLoader().load(registry_path=bad)


def test_crossAssetRegistryLoader_rejectsPrimarySourceNone(tmp_path: Path) -> None:
    bad = tmp_path / "bad_none_primary.yaml"
    bad.write_text(
        "version: v1\nmode: staged_fixture_only\nassets:\n"
        "  - asset_id: X\n    display_name_cn: x\n    asset_group: USD\n"
        "    asset_type: index\n    market: US\n    primary_source: none\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: false\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="primary_source"):
        CrossAssetRegistryLoader().load(registry_path=bad)


def test_crossAssetRegistryLoader_rejectsDuplicateInstrumentId(tmp_path: Path) -> None:
    bad = tmp_path / "dup_instrument.yaml"
    bad.write_text(
        "version: v1\nmode: staged_fixture_only\nassets:\n"
        "  - asset_id: A\n    display_name_cn: a\n    asset_group: Metals\n"
        "    asset_type: futures\n    market: US\n    instrument_id: FUT:DUP\n"
        "    layer5_instrument_id: L5-A\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n"
        "  - asset_id: B\n    display_name_cn: b\n    asset_group: Metals\n"
        "    asset_type: futures\n    market: US\n    instrument_id: FUT:DUP\n"
        "    layer5_instrument_id: L5-B\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="duplicate instrument_id"):
        CrossAssetRegistryLoader().load(registry_path=bad)


def test_doubleCountGuard_axisInputCannotEnterModelAggregation() -> None:
    result = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    vix = next(a for a in result.assets if a.asset_id == "L2-VIX")
    with pytest.raises(DoubleCountGuardError, match="display/reference only"):
        assert_model_eligible(vix)


def test_snapshotBuilder_forModel_blocksAxisInput() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    vix = next(a for a in loader.assets if a.asset_id == "L2-VIX")
    builder = CrossAssetSnapshotBuilder()
    with pytest.raises(DoubleCountGuardError):
        builder.build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=vix,
            observations=[_obs("L2-VIX")],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
            for_model=True,
        )


def test_doubleCountGuard_modelEligibleAsset_passes() -> None:
    result = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in result.assets if a.asset_id == "L2-COPPER")
    assert_model_eligible(copper)


def test_snapshotRejectsFutureInput() -> None:
    future = _obs("L2-COPPER", as_of_visibility=AS_OF + timedelta(hours=1))
    with pytest.raises(Exception, match="future input blocked"):
        reject_future_observation(as_of=AS_OF, observation=future)


def test_snapshotRejectsFutureTradeTime() -> None:
    future = _obs(
        "L2-COPPER",
        trade_time=AS_OF + timedelta(hours=1),
    )
    with pytest.raises(Exception, match="future trade_time blocked"):
        reject_future_observation(as_of=AS_OF, observation=future)


def test_snapshotRejectsFutureFetch_viaBuilder() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    future_fetch = _obs("L2-COPPER", fetch_time=AS_OF + timedelta(hours=1))
    builder = CrossAssetSnapshotBuilder()
    with pytest.raises(Exception, match="future fetch blocked"):
        builder.build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[future_fetch],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_snapshotBuilder_rejectsMixedTradeDateBatch() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    mixed = [
        _obs("L2-COPPER"),
        _obs(
            "L2-COPPER",
            trade_time=datetime(2026, 6, 13, 16, 0, tzinfo=UTC),
        ),
    ]
    with pytest.raises(Exception, match="mixed trade_date batch"):
        CrossAssetSnapshotBuilder().build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=mixed,
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_snapshotBuilder_rejectsTradeDateMismatch() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    wrong_day = _obs(
        "L2-COPPER",
        trade_time=datetime(2026, 6, 13, 16, 0, tzinfo=UTC),
    )
    with pytest.raises(Exception, match="no observations"):
        CrossAssetSnapshotBuilder().build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[wrong_day],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_stagedSource_rejectsTdxPytdx_viaBuilder() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    tdx_obs = _obs("L2-COPPER", source="tdx_pytdx")
    with pytest.raises(Exception, match="tdx_pytdx"):
        CrossAssetSnapshotBuilder().build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[tdx_obs],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_crossAssetSnapshotBuilder_buildsDailySnapshotWithLineage() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    obs = [
        _obs(
            "L2-COPPER",
            trade_time=datetime(2026, 6, 14, 10, 0, tzinfo=UTC),
            close=90.0,
        ),
        _obs(
            "L2-COPPER",
            trade_time=datetime(2026, 6, 14, 15, 0, tzinfo=UTC),
            close=100.0,
        ),
    ]
    snap, lineage, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=obs,
        source_fetch_ids=("fetch-l2-1",),
        source_content_hashes=("hash-l2-abc",),
    )
    assert roll is None
    assert snap.close == 100.0
    assert snap.pct_change == pytest.approx(100.0 / 90.0 - 1.0)
    assert lineage.layer_id == "layer2"
    assert lineage.source_fetch_ids == ("fetch-l2-1",)


def test_snapshotDeterministicRebuild_sameInputsSameHash() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    obs = [_obs("L2-COPPER")]
    builder = CrossAssetSnapshotBuilder()
    snap1, lin1, _ = builder.build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=obs,
        source_fetch_ids=("f",),
        source_content_hashes=("hash-det",),
    )
    snap2, lin2, _ = builder.build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=obs,
        source_fetch_ids=("f",),
        source_content_hashes=("hash-det",),
    )
    assert snap1.close == snap2.close
    assert snap1.pct_change == snap2.pct_change
    assert lin1.parameter_hash == lin2.parameter_hash


def test_snapshotLineageContainsSourceHashes() -> None:
    lineage = Layer2LineageBuilder().build(
        snapshot_id="l2-test-lineage",
        snapshot_type="cross_asset_daily_snapshot",
        as_of=AS_OF,
        input_window_start=AS_OF - timedelta(days=5),
        input_window_end=AS_OF - timedelta(days=1),
        source_dataset_ids=("staged:cross_asset_observation:L2-COPPER",),
        source_fetch_ids=("fetch-1",),
        source_content_hashes=("sha256-deadbeef",),
        rule_version="layer2_sensor_staged_v1",
        parameter_hash="param-hash-1",
    )
    for field in LINEAGE_REQUIRED_FIELDS:
        if field == "rebuild_reason":
            continue
        assert getattr(lineage, field) is not None


def test_futuresRollHandler_emitsExplicitRollEvent_notSilentSwitch() -> None:
    roll = FuturesRollHandler().detect_roll(
        asset_id="L2-HG-MAIN",
        roll_date=TRADE_DATE,
        incumbent=ContractLiquidity("HGZ25", TRADE_DATE, volume=1000, open_interest=5000),
        challenger=ContractLiquidity("HGF26", TRADE_DATE, volume=5000, open_interest=5200),
    )
    assert roll is not None
    assert roll.roll_event is True
    assert roll.old_contract == "HGZ25"
    assert roll.new_contract == "HGF26"


def test_futuresRollEvent_persistedViaWriteManager(tmp_path: Path) -> None:
    db = tmp_path / "layer2_roll.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_layer2_staging_tables(con)
    _insert_validation_report(cm, "vr-roll-1")

    roll = FuturesRollHandler().detect_roll(
        asset_id="L2-HG-MAIN",
        roll_date=TRADE_DATE,
        incumbent=ContractLiquidity("HGZ25", TRADE_DATE, volume=1000, open_interest=5000),
        challenger=ContractLiquidity("HGF26", TRADE_DATE, volume=5000, open_interest=5200),
    )
    assert roll is not None
    res = Layer2RollEventWriter(cm).write_roll_event(roll, validation_report_id="vr-roll-1")
    assert res.status == "SUCCESS"
    with cm.reader() as con:
        row = con.execute(
            "SELECT roll_event, old_contract, new_contract FROM cross_asset_roll_event"
        ).fetchone()
        assert row[0] is True
        assert row[1] == "HGZ25"
        assert row[2] == "HGF26"


def test_crossAssetSnapshotBuilder_resourceGuardBlocksBatchBuild() -> None:
    guard = MagicMock()
    guard.check.return_value = (Decision.HARD_STOP, "eco limit")
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    with pytest.raises(ResourceGuardBlockedError):
        CrossAssetSnapshotBuilder(resource_guard=guard).build_daily_snapshots(
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            registry_entry=copper,
            observations=[_obs("L2-COPPER")],
            source_fetch_ids=("fetch-1",),
            source_content_hashes=("hash-1",),
        )


def test_resourceGuard_realInstance_returnsDecision(tmp_path: Path) -> None:
    db = tmp_path / "rg.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        decision, _ = ResourceGuard(con=con).check()
    assert decision in (Decision.OK, Decision.WARN, Decision.PAUSE, Decision.HARD_STOP)


def test_noAcceptedChannel_notModelEligible() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    missing = next(a for a in loader.assets if a.asset_id == "L2-NO-CHANNEL")
    with pytest.raises(DoubleCountGuardError):
        assert_model_eligible(missing)


def test_vixAxisInput_displayOnlySnapshot_carriesGuardFlag() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    vix = next(a for a in loader.assets if a.asset_id == "L2-VIX")
    snap, _, _ = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=vix,
        observations=[_obs("L2-VIX", close=18.5)],
        source_fetch_ids=("fetch-vix",),
        source_content_hashes=("hash-vix",),
    )
    assert "LAYER1_AXIS_INPUT_DISPLAY_ONLY" in snap.quality_flags


def test_incrementalRebuildPreservesAsOfBoundary() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    _snap, lineage, _ = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=[_obs("L2-COPPER")],
        source_fetch_ids=("fetch-inc2",),
        source_content_hashes=("hash-inc2",),
        is_incremental=True,
        rebuild_reason="incremental",
    )
    assert lineage.is_incremental is True
    assert lineage.input_data_window_end <= lineage.as_of_timestamp


def test_upstreamSnapshotIds_propagateToLineage() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    upstream = ("l1-snap-env-2026-06-14",)
    _snap, lineage, _ = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=[_obs("L2-COPPER")],
        source_fetch_ids=("fetch-inc",),
        source_content_hashes=("hash-inc",),
        upstream_snapshot_ids=upstream,
    )
    assert lineage.upstream_snapshot_ids == upstream


def test_rollEvent_integratedInSnapshotBuild_setsActiveContract() -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    main = next(a for a in loader.assets if a.asset_id == "L2-HG-MAIN")
    snap, _, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=main,
        observations=[_obs("L2-HG-MAIN")],
        source_fetch_ids=("fetch-roll",),
        source_content_hashes=("hash-roll",),
        roll_incumbent=ContractLiquidity("HGZ25", TRADE_DATE, 1000, 5000),
        roll_challenger=ContractLiquidity("HGF26", TRADE_DATE, 5000, 5200),
    )
    assert roll is not None
    assert snap.active_contract == "HGF26"


def test_layer2Observation_blocksAxisInputWithoutDisplayOnlyWrite(tmp_path: Path) -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    vix = next(a for a in loader.assets if a.asset_id == "L2-VIX")
    cm = ConnectionManager(tmp_path / "block.duckdb")
    with pytest.raises(DoubleCountGuardError):
        Layer2ObservationWriter(cm).write_observations(
            registry_entry=vix,
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            observations=[_obs("L2-VIX")],
            validation_report_id="vr-x",
            display_only_write=False,
        )


def test_layer2Snapshot_writeWithRollEvent_persistsAllTables(tmp_path: Path) -> None:
    db = tmp_path / "layer2_roll_snap.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_layer2_staging_tables(con)
    _insert_validation_report(cm, "vr-roll-snap")

    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    main = next(a for a in loader.assets if a.asset_id == "L2-HG-MAIN")
    snap, lineage, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=main,
        observations=[_obs("L2-HG-MAIN")],
        source_fetch_ids=("fetch-roll-snap",),
        source_content_hashes=("hash-roll-snap",),
        roll_incumbent=ContractLiquidity("HGZ25", TRADE_DATE, 1000, 5000),
        roll_challenger=ContractLiquidity("HGF26", TRADE_DATE, 5000, 5200),
    )
    assert roll is not None
    Layer2SnapshotWriter(cm).write_daily_snapshot(
        snapshot=snap,
        lineage=lineage,
        roll_event=roll,
        validation_report_id="vr-roll-snap",
    )
    with cm.reader() as con:
        roll_row = con.execute("SELECT COUNT(*) FROM cross_asset_roll_event").fetchone()[0]
        snap_row = con.execute("SELECT active_contract FROM cross_asset_daily_snapshot").fetchone()
        assert roll_row == 1
        assert snap_row[0] == "HGF26"


def test_layer2Observation_writeViaWriteManager(tmp_path: Path) -> None:
    db = tmp_path / "layer2_obs_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_layer2_staging_tables(con)
    _insert_validation_report(cm, "vr-layer2-obs-1")

    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    result = Layer2ObservationWriter(cm).write_observations(
        registry_entry=copper,
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        observations=[_obs("L2-COPPER")],
        validation_report_id="vr-layer2-obs-1",
    )
    assert result.status == "SUCCESS"


def test_layer2Observation_rejectsAssetIdMismatch(tmp_path: Path) -> None:
    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    with pytest.raises(Exception, match="asset_id"):
        Layer2ObservationWriter(ConnectionManager(tmp_path / "x.duckdb")).write_observations(
            registry_entry=copper,
            as_of=AS_OF,
            trade_date=TRADE_DATE,
            observations=[_obs("L2-VIX")],
            validation_report_id="vr-x",
        )


def test_layer2Snapshot_writeViaWriteManager(tmp_path: Path) -> None:
    db = tmp_path / "layer2_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_layer2_staging_tables(con)
    _insert_validation_report(cm, "vr-layer2-1")

    loader = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    copper = next(a for a in loader.assets if a.asset_id == "L2-COPPER")
    snap, lineage, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=copper,
        observations=[_obs("L2-COPPER")],
        source_fetch_ids=("fetch-l2-wm",),
        source_content_hashes=("hash-l2-wm",),
    )
    snap_res, lin_res = Layer2SnapshotWriter(cm).write_daily_snapshot(
        snapshot=snap,
        lineage=lineage,
        roll_event=roll,
        validation_report_id="vr-layer2-1",
    )
    assert snap_res.status == "SUCCESS"
    assert lin_res.status == "SUCCESS"
    with cm.reader() as con:
        lin = con.execute(
            "SELECT layer_id FROM axis_snapshot_lineage WHERE snapshot_id = ?",
            [lineage.snapshot_id],
        ).fetchone()
        assert lin[0] == "layer2"


def test_layer2Registry_syncViaWriteManager(tmp_path: Path) -> None:
    db = tmp_path / "layer2_reg.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_layer2_staging_tables(con)
    _insert_validation_report(cm, "vr-reg-1")
    loaded = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    res = CrossAssetRegistryWriter(cm).sync_registry(
        loaded.assets, validation_report_id="vr-reg-1"
    )
    assert res.status == "SUCCESS"
    with cm.reader() as con:
        count = con.execute("SELECT COUNT(*) FROM cross_asset_registry").fetchone()[0]
        assert count == len(loaded.assets)


def test_layer2Loader_defaultRejectsProductionLiveMode(tmp_path: Path) -> None:
    bad = tmp_path / "production_live.yaml"
    bad.write_text(
        "version: v1\nmode: production_live\nassets:\n"
        "  - asset_id: X\n    display_name_cn: x\n    asset_group: USD\n"
        "    asset_type: index\n    market: US\n    primary_source: staged_fixture\n"
        "    validation_source: none\n    fallback_policy: none\n"
        "    is_axis_input: false\n    display_only: false\n"
        "    eligible_for_model: true\n    double_count_guard: none\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="staged_fixture_only"):
        CrossAssetRegistryLoader().load(registry_path=bad)
    result = CrossAssetRegistryLoader().load(registry_path=STAGED_REGISTRY_FIXTURE)
    assert result.mode == "staged_fixture_only"
