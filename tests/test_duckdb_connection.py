"""DuckDB connection manager tests (Round 1 task 007)."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager, WriteLockError
from backend.app.db.migrate import apply_migrations


def _init(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()


def test_writer_writesRow_readerSeesIt(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f1','qmt')")
    r = cm.reader()
    got = r.execute("SELECT source FROM file_registry WHERE file_id='f1'").fetchone()
    assert got[0] == "qmt"
    r.close()


def test_writer_whenLockHeld_raisesWriteLockError(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer():
        with pytest.raises(WriteLockError):
            with ConnectionManager(db).writer():
                pass


def test_applyPragmas_ecoProfile_setsThreadsAndMemory(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 1536, "max_threads": 2}},
    )
    with cm.writer() as w:
        threads = w.execute("SELECT current_setting('threads')").fetchone()[0]
    assert int(threads) == 2


def test_writer_afterExit_releasesLock(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer():
        pass
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f2','qmt')")
    r = cm.reader()
    assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='f2'").fetchone()[0] == 1
    r.close()


def test_writer_staleLockFromDeadPid_allowsNewWriter(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    lock_path = db.with_suffix(db.suffix + ".write.lock")
    lock_path.write_text(
        json.dumps({"pid": 999999999, "started_at": "2020-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    cm = ConnectionManager(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f3','qmt')")
    r = cm.reader()
    assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='f3'").fetchone()[0] == 1
    r.close()


def test_writer_corruptLockFile_raisesWriteLockError(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    lock_path = db.with_suffix(db.suffix + ".write.lock")
    lock_path.write_text("not-json", encoding="utf-8")
    cm = ConnectionManager(db)
    with pytest.raises(WriteLockError, match="corrupt write lock"):
        with cm.writer():
            pass
