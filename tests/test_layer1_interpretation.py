"""Layer 1 feature, interpretation, lineage, and WriteManager integration tests."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backend.app.core.resource_guard import Decision
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer1_axes.feature_engine import (
    AxisFeatureEngine,
    Layer1SnapshotError,
    ResourceGuardBlockedError,
)
from backend.app.layer1_axes.interpretation import (
    AxisInterpretationEngine,
    InterpretationRejectedError,
    Layer2WritebackError,
)
from backend.app.layer1_axes.lineage import (
    LINEAGE_REQUIRED_FIELDS,
    Layer1SnapshotWriter,
    LineageSnapshotError,
    SnapshotLineageBuilder,
)
from backend.app.layer1_axes.models import AxisObservation, ValidationReportRef

AS_OF = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)


def _obs(
    indicator_id: str,
    value: float,
    *,
    publish: datetime | None = None,
    source_switched: bool = False,
    fallback_policy: str | None = None,
) -> AxisObservation:
    pub = publish or AS_OF - timedelta(days=1)
    return AxisObservation(
        indicator_id=indicator_id,
        as_of_timestamp=AS_OF,
        publish_timestamp=pub,
        raw_value=value,
        source_used="fixture",
        source_switched=source_switched,
        fallback_policy=fallback_policy,
    )


def _history(indicator_id: str, n: int, value: float = 1.0) -> list[AxisObservation]:
    return [
        _obs(
            indicator_id,
            value,
            publish=AS_OF - timedelta(days=i + 2),
        )
        for i in range(n)
    ]


def test_axisFeatureEngine_insufficientHistory_noFakeZ() -> None:
    engine = AxisFeatureEngine(min_obs_required=10, window_len=20)
    hist = _history("ENV-E1-EFFR", 3)
    rows = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)
    row = rows[0]
    assert row.state_bucket == "insufficient_history"
    assert row.z_score is None
    assert row.percentile_rank is None
    assert "INSUFFICIENT_HISTORY" in row.quality_flags


def test_axisFeatureEngine_robustZUnavailable_whenMadZero() -> None:
    engine = AxisFeatureEngine(min_obs_required=5, window_len=10)
    hist = _history("ENV-E1-EFFR", 6, value=100.0)
    current = _obs("ENV-E1-EFFR", 100.0)
    row = engine.compute_features(as_of=AS_OF, observations=[current], history=hist)[0]
    assert row.robust_z_score is None
    assert "ROBUST_Z_UNAVAILABLE" in row.quality_flags


def test_axisFeatureEngine_sourceSwitched_recordsQualityFlag() -> None:
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    policy = "last_good_cache + stale_reason"
    current = _obs(
        "ENV-E1-EFFR",
        1.05,
        source_switched=True,
        fallback_policy=policy,
    )
    row = engine.compute_features(as_of=AS_OF, observations=[current], history=hist)[0]
    assert "SOURCE_SWITCHED" in row.quality_flags
    assert row.stale_reason == policy


def test_axisFeatureEngine_resourceGuard_ecoProfile() -> None:
    guard = MagicMock()
    guard.check.return_value = (Decision.HARD_STOP, "eco limit")
    engine = AxisFeatureEngine(resource_guard=guard, min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    with pytest.raises(ResourceGuardBlockedError):
        engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)


def test_snapshotRejectsFutureInput() -> None:
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    future = _obs("ENV-E1-EFFR", 1.0, publish=AS_OF + timedelta(days=1))
    with pytest.raises(Layer1SnapshotError, match="future input"):
        engine.compute_features(as_of=AS_OF, observations=[future], history=[future])


def test_axisInterpretation_rejectsForbiddenActionTerms() -> None:
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    interp_engine = AxisInterpretationEngine()
    with pytest.raises(InterpretationRejectedError):
        interp_engine.reject_if_forbidden("建议买入")
    rows = interp_engine.build_interpretation(
        as_of=AS_OF,
        features=[feat],
        templates={feat.indicator_id: "市场出现买入信号"},
    )
    assert rows[0].needs_human_review is True
    assert "买入" not in rows[0].summary_sentence
    assert "信号" not in rows[0].summary_sentence


def test_layer2ValueCannotWritebackToLayer1() -> None:
    with pytest.raises(Layer2WritebackError):
        AxisInterpretationEngine.guard_layer2_writeback(
            target_table="axis_feature_snapshot",
            layer_id="layer2",
        )


def _insert_validation_report(
    cm: ConnectionManager,
    report_id: str,
    *,
    fetch_ids: list[str] | None = None,
    hashes: list[str] | None = None,
) -> None:
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
                "run-layer1",
                "layer1_axis_feature",
                "fixture",
                "PASSED",
                1,
                0,
                0,
                True,
                False,
                "layer1_v1",
                "layer1_v1",
                json.dumps(fetch_ids or ["fetch-1"]),
                json.dumps(hashes or ["hash-abc"]),
            ],
        )


def _persist_lineage(
    tmp_path: Path,
    lineage,
    *,
    report_id: str = "vr-lineage",
    fetch_ids: list[str] | None = None,
    hashes: list[str] | None = None,
) -> ConnectionManager:
    db = tmp_path / "lineage_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    _insert_validation_report(
        cm,
        report_id,
        fetch_ids=fetch_ids,
        hashes=hashes,
    )
    writer = Layer1SnapshotWriter(cm)
    result = writer.write_lineage(lineage=lineage, validation_report_id=report_id)
    assert result.status == "SUCCESS"
    return cm


def test_snapshotLineageIncludesAllRequiredFields(migrated_con, tmp_path) -> None:
    report = ValidationReportRef(
        validation_report_id="vr-1",
        rule_version="layer1_v1",
        source_fetch_ids_json='["fetch-1"]',
        source_content_hashes_json='["hash-abc"]',
    )
    builder = SnapshotLineageBuilder()
    lineage = builder.build(
        snapshot_id="snap-1",
        snapshot_type="axis_feature_snapshot",
        as_of=AS_OF,
        validation_report=report,
        input_window_start=AS_OF - timedelta(days=30),
        input_window_end=AS_OF,
        source_dataset_ids=("ds-1",),
        parameter_hash="ph-1",
    )
    cm = _persist_lineage(tmp_path, lineage, report_id="vr-1")
    with cm.reader() as con:
        row = con.execute(
            "SELECT * FROM axis_snapshot_lineage WHERE snapshot_id = ?", ["snap-1"]
        ).fetchone()
        cols = [d[0] for d in con.description]
    assert row is not None
    for field in LINEAGE_REQUIRED_FIELDS:
        assert field in cols
        idx = cols.index(field)
        assert row[idx] is not None or field == "rebuild_reason"


def test_snapshotLineageContainsSourceHashes(migrated_con, tmp_path) -> None:
    report = ValidationReportRef(
        validation_report_id="vr-2",
        rule_version="layer1_v1",
        source_fetch_ids_json='["fetch-99"]',
        source_content_hashes_json='["deadbeef"]',
    )
    lineage = SnapshotLineageBuilder().build(
        snapshot_id="snap-2",
        snapshot_type="axis_feature_snapshot",
        as_of=AS_OF,
        validation_report=report,
        input_window_start=AS_OF - timedelta(days=7),
        input_window_end=AS_OF,
        source_dataset_ids=("vendor/bar",),
        parameter_hash="ph-2",
    )
    cm = _persist_lineage(tmp_path, lineage, report_id="vr-2")
    with cm.reader() as con:
        stored = con.execute(
            """
            SELECT source_content_hashes, source_fetch_ids
            FROM axis_snapshot_lineage WHERE snapshot_id=?
            """,
            ["snap-2"],
        ).fetchone()
    assert "deadbeef" in stored[0]
    assert "fetch-99" in stored[1]


def test_incrementalRebuildPreservesAsOfBoundary() -> None:
    report = ValidationReportRef(
        validation_report_id="vr-3",
        rule_version="layer1_v1",
        source_fetch_ids_json="[]",
        source_content_hashes_json="[]",
    )
    builder = SnapshotLineageBuilder()
    as_of = AS_OF
    lineage = builder.build(
        snapshot_id="snap-inc",
        snapshot_type="axis_feature_snapshot",
        as_of=as_of,
        validation_report=report,
        input_window_start=as_of - timedelta(days=5),
        input_window_end=as_of,
        source_dataset_ids=("ds",),
        parameter_hash="ph-inc",
        is_incremental=True,
        rebuild_reason="incremental",
    )
    assert lineage.input_data_window_end <= lineage.as_of_timestamp
    assert lineage.is_incremental is True


def test_snapshotDeterministicRebuild_sameInputsSameHash() -> None:
    inputs = ("ds-a", "ds-b")
    h1 = SnapshotLineageBuilder.parameter_hash_for(rule_version="layer1_v1", inputs=inputs)
    h2 = SnapshotLineageBuilder.parameter_hash_for(rule_version="layer1_v1", inputs=inputs)
    assert h1 == h2
    h3 = SnapshotLineageBuilder.parameter_hash_for(rule_version="layer1_v2", inputs=inputs)
    assert h1 != h3


def test_layer1Snapshot_writeViaWriteManager(tmp_path: Path) -> None:
    db = tmp_path / "layer1_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
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
                "vr-layer1-wm",
                "run-layer1",
                "layer1_axis_feature",
                "fixture",
                "PASSED",
                1,
                0,
                0,
                True,
                False,
                "layer1_v1",
                "layer1_v1",
                json.dumps(["fetch-1"]),
                json.dumps(["hash-abc"]),
            ],
        )
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    writer = Layer1SnapshotWriter(cm)
    result = writer.write_features(
        rows=[feat],
        validation_report_id="vr-layer1-wm",
    )
    assert result.status == "SUCCESS"
    with cm.reader() as con:
        cnt = con.execute("SELECT COUNT(*) FROM axis_feature_snapshot").fetchone()[0]
    assert cnt == 1


def test_axisFeatureEngine_windowLen_truncatesHistory() -> None:
    """600 observations with window_len=20 must use only trailing window for stats."""
    engine = AxisFeatureEngine(min_obs_required=5, window_len=20)
    hist = _history("ENV-E1-EFFR", 600, value=1.0)
    hist[-1] = _obs("ENV-E1-EFFR", 50.0)
    row = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    assert row.valid_obs_count == 20
    assert row.z_score is not None


def test_axisFeatureEngine_shuffledHistory_sortedBeforeStats() -> None:
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    shuffled = list(reversed(hist))
    row = engine.compute_features(as_of=AS_OF, observations=[shuffled[-1]], history=shuffled)[0]
    assert row.raw_delta_abs is not None


def test_snapshotLineage_agentOutputsNotSource_rejectsAgentProse() -> None:
    report = ValidationReportRef(
        validation_report_id="vr-agent",
        rule_version="layer1_v1",
        source_fetch_ids_json="[]",
        source_content_hashes_json='["hash"]',
    )
    builder = SnapshotLineageBuilder()
    with pytest.raises(LineageSnapshotError, match="agent outputs"):
        builder.build(
            snapshot_id="snap-agent",
            snapshot_type="axis_feature_snapshot",
            as_of=AS_OF,
            validation_report=report,
            input_window_start=AS_OF - timedelta(days=1),
            input_window_end=AS_OF,
            source_dataset_ids=("agent_summary:建议买入",),
            parameter_hash="ph-agent",
        )


def test_layer1Snapshot_forbiddenSubstitute_blocksWriteWithQualityError(
    tmp_path: Path,
) -> None:
    db = tmp_path / "layer1_substitute.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    _insert_validation_report(cm, "vr-sub")
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    feat = replace(
        feat,
        quality_flags=feat.quality_flags + ("FORBIDDEN_SUBSTITUTE_USED",),
    )
    writer = Layer1SnapshotWriter(cm)
    with pytest.raises(LineageSnapshotError, match="forbidden substitute"):
        writer.write_features(rows=[feat], validation_report_id="vr-sub")


def test_layer1Snapshot_writeLineageViaWriteManager(tmp_path: Path) -> None:
    report = ValidationReportRef(
        validation_report_id="vr-lineage-wm",
        rule_version="layer1_v1",
        source_fetch_ids_json='["fetch-1"]',
        source_content_hashes_json='["hash-lineage"]',
    )
    lineage = SnapshotLineageBuilder().build(
        snapshot_id="snap-wm-lineage",
        snapshot_type="axis_feature_snapshot",
        as_of=AS_OF,
        validation_report=report,
        input_window_start=AS_OF - timedelta(days=7),
        input_window_end=AS_OF,
        source_dataset_ids=("ds-wm",),
        parameter_hash="ph-wm",
    )
    cm = _persist_lineage(tmp_path, lineage, report_id="vr-lineage-wm")
    with cm.reader() as con:
        cnt = con.execute(
            "SELECT COUNT(*) FROM axis_snapshot_lineage WHERE snapshot_id = ?",
            ["snap-wm-lineage"],
        ).fetchone()[0]
        audit_cnt = con.execute(
            """
            SELECT COUNT(*) FROM write_audit_log
            WHERE target_table = 'axis_snapshot_lineage' AND status = 'SUCCESS'
            """
        ).fetchone()[0]
    assert cnt == 1
    assert audit_cnt >= 1


def test_layer1Interpretation_writeViaWriteManager(tmp_path: Path) -> None:
    db = tmp_path / "layer1_interp_wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    _insert_validation_report(cm, "vr-interp")
    engine = AxisFeatureEngine(min_obs_required=3, window_len=10)
    hist = _history("ENV-E1-EFFR", 5)
    feat = engine.compute_features(as_of=AS_OF, observations=[hist[-1]], history=hist)[0]
    interp_rows = AxisInterpretationEngine().build_interpretation(as_of=AS_OF, features=[feat])
    writer = Layer1SnapshotWriter(cm)
    result = writer.write_interpretation(
        rows=interp_rows,
        validation_report_id="vr-interp",
    )
    assert result.status == "SUCCESS"
    with cm.reader() as con:
        cnt = con.execute("SELECT COUNT(*) FROM axis_interpretation_snapshot").fetchone()[0]
    assert cnt == 1
