"""ResourceGuard tests (Round 1 task 006)."""

from __future__ import annotations

import duckdb
from backend.app.core.resource_guard import Decision, ResourceSnapshot, evaluate, format_pause_event

THRESH = {
    "profiles": {
        "eco": {
            "process_rss_warn_mb": 800,
            "process_rss_pause_mb": 1200,
            "process_rss_hard_stop_mb": 1800,
        },
    },
    "system_thresholds": {
        "available_memory_warn_gb": 4,
        "available_memory_pause_gb": 2,
        "available_memory_hard_stop_gb": 1,
        "disk_free_warn_gb": 30,
        "disk_free_pause_gb": 20,
        "disk_free_hard_stop_gb": 10,
    },
    "project_size_thresholds": {
        "project_warn_gb": 15,
        "project_pause_gb": 25,
        "project_hard_stop_gb": 40,
    },
}


def test_evaluate_healthyResources_returnsOk() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=8, disk_free_gb=100, process_rss_mb=300, project_size_gb=1
    )
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.OK


def test_evaluate_lowMemory_returnsPause() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=1.5, disk_free_gb=100, process_rss_mb=300, project_size_gb=1
    )
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "memory" in reason.lower()


def test_evaluate_criticalDisk_returnsHardStop() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=8, disk_free_gb=5, process_rss_mb=300, project_size_gb=1
    )
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP


def test_evaluate_multipleSignals_picksMostSevere() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=3.5, disk_free_gb=5, process_rss_mb=300, project_size_gb=1
    )
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP


def test_evaluate_warnMemory_returnsWarn() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=3.5, disk_free_gb=100, process_rss_mb=300, project_size_gb=1
    )
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.WARN
    assert "memory" in reason.lower()


def test_evaluate_largeProject_returnsPause() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=8, disk_free_gb=100, process_rss_mb=300, project_size_gb=30
    )
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "project" in reason.lower()


def test_evaluate_rssAboveWarnNotPause_returnsWarn() -> None:
    eco = THRESH["profiles"]["eco"]
    snap = ResourceSnapshot(
        available_memory_gb=8,
        disk_free_gb=100,
        process_rss_mb=eco["process_rss_pause_mb"] - 1,
        project_size_gb=1,
    )
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.WARN
    assert "rss" in reason.lower()


def test_evaluate_memoryExactlyAtHardStopThreshold_isPause() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=1.0, disk_free_gb=100, process_rss_mb=300, project_size_gb=1
    )
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE


def test_evaluate_diskFreeExactlyAtWarnThreshold_isOk() -> None:
    snap = ResourceSnapshot(
        available_memory_gb=8, disk_free_gb=30.0, process_rss_mb=300, project_size_gb=1
    )
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.OK


def test_formatPauseEvent_includesSentinelAndMetrics() -> None:
    snap = ResourceSnapshot(1.5, 15.0, 900.0, 2.0)
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
        lambda: ResourceSnapshot(8, 100, 300, 1),
    )
    decision, _ = guard.check()
    assert decision == Decision.OK
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 0
    assert "RESOURCE_GUARD_PAUSED" not in capsys.readouterr().err


def test_check_lowMemorySnapshot_writesGuardLog(monkeypatch, capsys) -> None:
    from backend.app.core.resource_guard import ResourceGuard
    from backend.app.db.migrate import apply_migrations

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: ResourceSnapshot(1.5, 100, 300, 1),
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
        lambda: ResourceSnapshot(0.5, 100, 300, 1),
    )
    decision, _ = guard.check()
    assert decision == Decision.HARD_STOP
    row = con.execute("SELECT decision FROM resource_guard_log").fetchone()
    assert row[0] == "HARD_STOP"
    assert "RESOURCE_GUARD_PAUSED" in capsys.readouterr().err
