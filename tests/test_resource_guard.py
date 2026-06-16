"""ResourceGuard tests (Round 1 task 006)."""

from __future__ import annotations

import duckdb
import pytest
from backend.app.core.resource_guard import Decision, ResourceSnapshot, evaluate, format_pause_event

THRESH = {
    "profiles": {
        "eco": {
            "process_rss_warn_mb": 800,
            "process_rss_pause_mb": 1200,
            "process_rss_hard_stop_mb": 1800,
            "duckdb_temp_max_gb": 2,
        },
    },
    "system_thresholds": {
        "available_memory_warn_gb": 4,
        "available_memory_pause_gb": 2,
        "available_memory_hard_stop_gb": 1,
        "system_memory_usage_warn_pct": 70,
        "system_memory_usage_pause_pct": 80,
        "system_memory_usage_hard_stop_pct": 90,
        "disk_free_warn_gb": 30,
        "disk_free_pause_gb": 20,
        "disk_free_hard_stop_gb": 10,
        "system_disk_usage_warn_pct": 75,
        "system_disk_usage_pause_pct": 85,
        "system_disk_usage_hard_stop_pct": 92,
    },
    "project_size_thresholds": {
        "project_warn_gb": 15,
        "project_pause_gb": 25,
        "project_hard_stop_gb": 40,
        "cache_warn_gb": 1,
        "cache_pause_gb": 2,
        "cache_hard_stop_gb": 4,
    },
}


def _snap(**overrides) -> ResourceSnapshot:
    defaults = {
        "available_memory_gb": 8,
        "disk_free_gb": 100,
        "process_rss_mb": 300,
        "project_size_gb": 1,
        "duckdb_temp_size_gb": 0.1,
        "cache_size_gb": 0.1,
        "system_memory_usage_pct": 50.0,
        "system_disk_usage_pct": 50.0,
    }
    defaults.update(overrides)
    return ResourceSnapshot(**defaults)


def test_evaluate_healthyResources_returnsOk() -> None:
    snap = _snap()
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.OK


def test_evaluate_lowMemory_returnsPause() -> None:
    snap = _snap(available_memory_gb=1.5)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "memory" in reason.lower()


def test_evaluate_criticalDisk_returnsHardStop() -> None:
    snap = _snap(disk_free_gb=5)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP


def test_evaluate_multipleSignals_picksMostSevere() -> None:
    snap = _snap(available_memory_gb=3.5, disk_free_gb=5)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP


def test_evaluate_warnMemory_returnsWarn() -> None:
    snap = _snap(available_memory_gb=3.5)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.WARN
    assert "memory" in reason.lower()


def test_evaluate_largeProject_returnsPause() -> None:
    snap = _snap(project_size_gb=30)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "project" in reason.lower()


def test_evaluate_rssAboveWarnNotPause_returnsWarn() -> None:
    eco = THRESH["profiles"]["eco"]
    snap = _snap(process_rss_mb=eco["process_rss_pause_mb"] - 1)
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.WARN
    assert "rss" in reason.lower()


def test_evaluate_memoryExactlyAtHardStopThreshold_isPause() -> None:
    snap = _snap(available_memory_gb=1.0)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE


def test_evaluate_diskFreeExactlyAtWarnThreshold_isOk() -> None:
    snap = _snap(disk_free_gb=30.0)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.OK


def test_evaluate_cacheAbovePause_returnsPause() -> None:
    snap = _snap(cache_size_gb=2.5)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "cache" in reason.lower()


def test_evaluate_duckdbTempAboveHardStop_returnsHardStop() -> None:
    eco = THRESH["profiles"]["eco"]
    temp_max = eco["duckdb_temp_max_gb"]
    snap = _snap(duckdb_temp_size_gb=temp_max * 1.05)
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.HARD_STOP
    assert "temp" in reason.lower()


def test_evaluate_duckdbTempAboveMax_returnsPause() -> None:
    eco = THRESH["profiles"]["eco"]
    temp_max = eco["duckdb_temp_max_gb"]
    snap = _snap(duckdb_temp_size_gb=temp_max * 0.9)
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.PAUSE
    assert "temp" in reason.lower()


def test_evaluate_systemMemoryUsageAbovePause_returnsPause() -> None:
    snap = _snap(system_memory_usage_pct=85.0)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "memory usage" in reason.lower()


def test_evaluate_systemMemoryUsageHigh_returnsPause() -> None:
    test_evaluate_systemMemoryUsageAbovePause_returnsPause()


def test_evaluate_systemDiskUsageAboveHardStop_returnsHardStop() -> None:
    snap = _snap(system_disk_usage_pct=95.0)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP
    assert "disk usage" in reason.lower()


def test_evaluate_systemDiskUsageCritical_returnsHardStop() -> None:
    test_evaluate_systemDiskUsageAboveHardStop_returnsHardStop()


def test_formatPauseEvent_includesSentinelAndMetrics() -> None:
    snap = _snap(
        available_memory_gb=1.5,
        disk_free_gb=15.0,
        process_rss_mb=900.0,
        project_size_gb=2.0,
    )
    msg = format_pause_event(Decision.PAUSE, "available memory below threshold", snap, "eco")
    assert msg.startswith("RESOURCE_GUARD_PAUSED")
    assert "available_memory_gb=1.50" in msg
    assert "profile=eco" in msg


def test_check_okDecision_doesNotWriteGuardLog(monkeypatch, capsys) -> None:
    from backend.app.core.resource_guard import ResourceGuard
    from backend.app.db.migrate import apply_migrations

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: _snap(),
    )
    decision, _ = guard.check()
    assert decision == Decision.OK
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 0
    assert "RESOURCE_GUARD_PAUSED" not in capsys.readouterr().err


def test_check_lowMemorySnapshot_writesExtendedGuardLogColumns(monkeypatch) -> None:
    from backend.app.core.resource_guard import ResourceGuard
    from backend.app.db.migrate import apply_migrations

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: _snap(
            available_memory_gb=1.5,
            system_memory_usage_pct=88.0,
            system_disk_usage_pct=80.0,
            cache_size_gb=2.5,
            duckdb_temp_size_gb=1.8,
        ),
    )
    guard.check()
    row = con.execute(
        """
        SELECT system_memory_usage_pct, system_disk_usage_pct,
               cache_size_gb, duckdb_temp_size_gb
        FROM resource_guard_log
        """
    ).fetchone()
    assert row[0] == 88.0
    assert row[1] == 80.0
    assert row[2] == 2.5
    assert row[3] == 1.8


def test_check_lowMemorySnapshot_writesGuardLog(monkeypatch, capsys) -> None:
    from backend.app.core.resource_guard import ResourceGuard
    from backend.app.db.migrate import apply_migrations

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: _snap(available_memory_gb=1.5),
    )
    decision, _ = guard.check()
    assert decision == Decision.PAUSE
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 1
    assert "RESOURCE_GUARD_PAUSED" in capsys.readouterr().err


def test_check_hardStopDecision_writesGuardLog(monkeypatch, capsys) -> None:
    from backend.app.core.resource_guard import ResourceGuard
    from backend.app.db.migrate import apply_migrations

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: _snap(available_memory_gb=0.5),
    )
    decision, _ = guard.check()
    assert decision == Decision.HARD_STOP
    row = con.execute("SELECT decision FROM resource_guard_log").fetchone()
    assert row[0] == "HARD_STOP"
    assert "RESOURCE_GUARD_PAUSED" in capsys.readouterr().err


def test_check_warnDecision_writesGuardLog(monkeypatch, capsys) -> None:
    from backend.app.core.resource_guard import ResourceGuard
    from backend.app.db.migrate import apply_migrations

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: _snap(available_memory_gb=3.5),
    )
    decision, _ = guard.check()
    assert decision == Decision.WARN
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 1
    row = con.execute("SELECT decision FROM resource_guard_log").fetchone()
    assert row[0] == "WARN"
    assert "RESOURCE_GUARD_PAUSED" not in capsys.readouterr().err


def test_snapshot_realCall_doesNotRaise() -> None:
    from backend.app.core.resource_guard import ResourceGuard

    snap = ResourceGuard().snapshot()
    assert snap.available_memory_gb >= 0
    assert snap.disk_free_gb >= 0
    assert snap.process_rss_mb >= 0
    assert snap.project_size_gb >= 0


def test_resourceSnapshot_negativeValue_raises() -> None:
    with pytest.raises(ValueError, match="available_memory_gb"):
        ResourceSnapshot(-1, 1, 1, 1)


def test_evaluate_largeCache_returnsPause() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=8,
        disk_free_gb=100,
        process_rss_mb=300,
        project_size_gb=1,
        cache_size_gb=3.0,
    )
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "cache" in reason.lower()


def test_evaluate_highSystemMemoryPct_returnsHardStop() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=8,
        disk_free_gb=100,
        process_rss_mb=300,
        project_size_gb=1,
        system_memory_usage_pct=95.0,
    )
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP
    assert "memory" in reason.lower()


def test_evaluate_highDuckdbTemp_returnsPause() -> None:
    eco = THRESH["profiles"]["eco"]
    snap = ResourceSnapshot(
        available_memory_gb=8,
        disk_free_gb=100,
        process_rss_mb=300,
        project_size_gb=1,
        duckdb_temp_size_gb=eco["duckdb_temp_max_gb"] * 0.9,
    )
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.PAUSE
    assert "temp" in reason.lower()
