"""Foundation end-to-end smoke tests (Round 1 task 010)."""

from __future__ import annotations

from pathlib import Path

import duckdb
from backend.app.core.resource_guard import Decision, ResourceGuard, ResourceSnapshot
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore

FOUNDATION_TABLES = {
    "schema_version",
    "file_registry",
    "write_audit_log",
    "resource_guard_log",
    "stg_foundation_smoke",
}


def test_foundation_endToEnd_writesCleanAndAudits(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "smoke.duckdb"
    con = duckdb.connect(str(db))
    applied = apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    con.close()
    assert "001_foundation" in applied
    assert "002_registry_hardening" in applied
    assert FOUNDATION_TABLES.issubset(tables)

    cm = ConnectionManager(db)

    guard_warn = ResourceGuard(profile="eco", con=duckdb.connect(str(db)))
    monkeypatch.setattr(
        guard_warn,
        "snapshot",
        lambda: ResourceSnapshot(3.5, 100, 300, 1),
    )
    warn_decision, _ = guard_warn.check()
    assert warn_decision == Decision.WARN
    assert (
        guard_warn.con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0] == 1
    )
    guard_warn.con.close()

    guard = ResourceGuard(profile="eco", con=None)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: ResourceSnapshot(8, 100, 300, 1),
    )
    decision, _ = guard.check()
    assert decision == Decision.OK

    store = RawStore(tmp_path)
    reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(
        b"raw-bytes", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    fid = reg.register(saved)
    with cm.reader() as r_reg:
        assert (
            r_reg.execute("SELECT COUNT(*) FROM file_registry WHERE file_id=?", [fid]).fetchone()[0]
            == 1
        )

    with cm.writer() as w:
        w.execute(
            "INSERT INTO stg_foundation_smoke VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')"
        )
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
    ok = WriteManager(cm).write(
        WriteRequest(
            run_id="r1",
            job_id="j1",
            target_table="security_bar_smoke_clean",
            staging_table="stg_foundation_smoke",
            write_mode="append_only",
            primary_keys=["instrument_id", "trade_date"],
            validation_report_id="stub-pass-1",
            source_used="qmt",
        )
    )
    assert ok.status == "SUCCESS" and ok.rows_inserted == 1

    with cm.reader() as r:
        close_val = r.execute(
            "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'"
        ).fetchone()[0]
        assert close_val == 195.0
        assert (
            r.execute(
                "SELECT status FROM write_audit_log WHERE write_id=?",
                [ok.write_id],
            ).fetchone()[0]
            == "SUCCESS"
        )

    bad = WriteManager(cm).write(
        WriteRequest(
            run_id="r2",
            job_id="j2",
            target_table="security_bar_smoke_clean",
            staging_table="stg_foundation_smoke",
            write_mode="append_only",
            primary_keys=["instrument_id", "trade_date"],
            validation_report_id="stub-fail-1",
            source_used="qmt",
        )
    )
    assert bad.status == "FAILED"
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
        failed_audits = r.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'"
        ).fetchone()[0]
        assert failed_audits == 1
