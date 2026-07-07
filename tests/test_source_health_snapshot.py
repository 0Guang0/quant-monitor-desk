"""B3F-SH source_health_snapshot writer tests (R3F-SH-01 / SH-04)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest
from backend.app.ops.data_health import DataHealthService
from backend.app.ops.source_health_writer import (
    SourceHealthSnapshotRow,
    SourceHealthSnapshotWriter,
    persist_readiness_rollup,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "data_health"


def test_sourceHealthSnapshot_writer_insertsRow() -> None:
    """覆盖范围：isolated DB 上 source_health_snapshot writer 最小插入
    测试对象：SourceHealthSnapshotWriter.insert / ensure_schema
    目的/目标：R3F-SH-01 — Batch6 snapshot 行可持久化（非 MIG migration 路径）
    验证点：插入后 fetch_by_snapshot_id 可读且 health_status 匹配
    失败含义：无 writer 或 insert 失败，Batch6 无法跟踪 source health
    """
    con = duckdb.connect(":memory:")
    writer = SourceHealthSnapshotWriter(con)
    writer.ensure_schema()
    writer.insert(
        SourceHealthSnapshotRow(
            snapshot_id="snap-sh01",
            source_id="fred",
            as_of_timestamp=datetime(2024, 6, 30, 12, 0, tzinfo=UTC),
            health_status="PASS",
            notes="sh-01 isolated pytest",
        )
    )
    row = writer.fetch_by_snapshot_id("snap-sh01")
    assert row is not None
    assert row["source_id"] == "fred"
    assert row["health_status"] == "PASS"


def test_sourceHealthSnapshot_rollupPersist_fields() -> None:
    """覆盖范围：DH2 rollup evidence → snapshot notes 字段
    测试对象：persist_readiness_rollup + gate_complete fixture
    目的/目标：R3F-SH-04 — readiness rollup 可落库到 snapshot 行
    验证点：notes JSON 含 rollup_id 与 profiles；source_id=source_readiness_rollup
    失败含义：rollup 无法落库，readiness 仍停留在只读报告
    """
    evidence = _FIXTURES / "rollup" / "gate_complete"
    report = DataHealthService().check_evidence_dir(
        evidence, profile="source_readiness_rollup"
    )
    con = duckdb.connect(":memory:")
    snapshot_id = persist_readiness_rollup(
        con,
        evidence_dir=evidence,
        overall_status=report.overall_status,
        gate_ready=report.sandbox_clean_write_gate_ready,
        gate_rationale=report.gate_rationale,
    )
    row = SourceHealthSnapshotWriter(con).fetch_by_snapshot_id(snapshot_id)
    assert row is not None
    assert row["source_id"] == "source_readiness_rollup"
    assert row["health_status"] == report.overall_status
    notes = json.loads(row["notes"])
    assert notes["rollup_id"] == "dh2-gate-complete"
    assert "fred_sandbox_pilot" in notes["profiles"]


def test_sourceHealthSnapshot_rollupPersist_missingManifest(tmp_path) -> None:
    """覆盖范围：rollup persist 缺 manifest fail-closed
    测试对象：persist_readiness_rollup
    目的/目标：W-A8-04 — 无 rollup_manifest.json 不得静默空 persist
    验证点：FileNotFoundError 且消息含 rollup_manifest.json
    失败含义：缺 manifest 仍写 snapshot，rollup 字段不可追溯
    """
    import duckdb

    con = duckdb.connect(":memory:")
    empty_dir = tmp_path / "no_manifest"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="rollup_manifest.json"):
        persist_readiness_rollup(
            con,
            evidence_dir=empty_dir,
            overall_status="PASS",
            gate_ready=True,
            gate_rationale="test",
        )
