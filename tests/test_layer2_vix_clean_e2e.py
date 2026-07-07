"""S01 — L2-VIX Tier A clean read → snapshot + lineage e2e (DCP-07 / ADR-013)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from backend.app.layer2_sensors import (
    CLEAN_REPLAY_REGISTRY_FIXTURE,
    CrossAssetRegistryLoader,
    CrossAssetSnapshotBuilder,
    Layer2CleanObservationReader,
    Layer2SnapshotWriter,
)
from tests.layer1_clean_e2e_support import bootstrap_layer1_clean_db, seed_macro_series
from tests.layer2_e2e_support import insert_layer2_validation_report, layer2_cm

AS_OF = datetime(2026, 6, 20, 16, 0, tzinfo=UTC)
TRADE_DATE = date(2026, 6, 19)


def test_layer2_vix_clean_e2e_reads_axis_observation_and_builds_snapshot(
    tmp_path,
) -> None:
    """覆盖范围：切片 S01 — L2-VIX 从 axis_observation(VIXCLS) 读 clean 并产出 snapshot+lineage
    测试对象：Layer2CleanObservationReader + CrossAssetSnapshotBuilder + Layer2SnapshotWriter
    目的/目标：证明 P0 传感器非 staged_fixture_only；对齐 ADR-013 / to-issues S01 AC
    验证点：snapshot.source_used==fred；lineage 含 fred clean dataset_id 与 fetch/hash；DB 行与 VR 一致
    失败含义：Layer2 仍无法从 Tier A clean 绑真市况，G2 竖切与 ACC-LAYER-E2E-LIVE-001 L2 子集不成立
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="VIXCLS",
            n=40,
            start=date(2026, 5, 11),
            base_value=17.0,
            source_used="fred",
            step=0.2,
        )
        fetch_row = con.execute(
            """
            SELECT observation_id, content_hash
            FROM axis_observation
            WHERE indicator_id = 'VIXCLS'
            ORDER BY publish_timestamp DESC
            LIMIT 1
            """
        ).fetchone()
    assert fetch_row is not None
    fetch_id = str(fetch_row[0])
    content_hash = str(fetch_row[1])

    loaded = CrossAssetRegistryLoader().load(registry_path=CLEAN_REPLAY_REGISTRY_FIXTURE)
    vix = next(a for a in loaded.assets if a.asset_id == "L2-VIX")
    with cm.reader() as con:
        observations = Layer2CleanObservationReader().read_observations(
            con, vix, as_of_end=AS_OF
        )
    assert observations
    assert all(o.source == "fred" for o in observations)
    assert "staged_fixture" not in observations[-1].source
    day_obs = [o for o in observations if o.trade_time.date() == TRADE_DATE]
    assert day_obs, f"expected observations on trade_date={TRADE_DATE}"

    snap, lineage, roll = CrossAssetSnapshotBuilder().build_daily_snapshots(
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        registry_entry=vix,
        observations=day_obs,
        source_fetch_ids=(fetch_id,),
        source_content_hashes=(content_hash,),
    )
    assert roll is None
    assert snap.asset_id == "L2-VIX"
    assert snap.source_used == "fred"
    assert snap.close is not None
    assert lineage.source_fetch_ids == (fetch_id,)
    assert lineage.source_content_hashes == (content_hash,)
    assert lineage.source_dataset_ids == ("fred:axis_observation:VIXCLS",)
    assert not any(s.startswith("staged:") for s in lineage.source_dataset_ids)
    assert "LAYER1_AXIS_INPUT_DISPLAY_ONLY" in snap.quality_flags

    wm_cm = layer2_cm(tmp_path, "layer2_vix_clean_wm.duckdb")
    insert_layer2_validation_report(
        wm_cm,
        "vr-layer2-vix-clean",
        fetch_ids=[fetch_id],
        content_hashes=[content_hash],
        source_id="fred",
        rule_version="layer2_sensor_clean_replay_v1",
    )
    Layer2SnapshotWriter(wm_cm).write_daily_snapshot(
        snapshot=snap,
        lineage=lineage,
        roll_event=roll,
        validation_report_id="vr-layer2-vix-clean",
    )
    with wm_cm.reader() as con:
        snap_db = con.execute(
            """
            SELECT asset_id, trade_date, source_used
            FROM cross_asset_daily_snapshot
            WHERE snapshot_id = ?
            """,
            [snap.snapshot_id],
        ).fetchone()
        assert snap_db is not None
        assert snap_db[0] == "L2-VIX"
        assert str(snap_db[1]) == TRADE_DATE.isoformat()
        assert snap_db[2] == "fred"
        row = con.execute(
            """
            SELECT source_fetch_ids, source_content_hashes, layer_id
            FROM axis_snapshot_lineage
            WHERE snapshot_id = ?
            """,
            [lineage.snapshot_id],
        ).fetchone()
    assert row is not None
    assert json.loads(row[0]) == [fetch_id]
    assert json.loads(row[1]) == [content_hash]
    assert row[2] == "layer2"
