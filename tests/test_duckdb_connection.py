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
    with cm.reader() as r:
        got = r.execute("SELECT source FROM file_registry WHERE file_id='f1'").fetchone()
    assert got[0] == "qmt"


def test_writer_whenLockHeld_raisesWriteLockError(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer():
        with pytest.raises(WriteLockError):
            with ConnectionManager(db).writer():
                pass


def test_applyPragmas_readerProfile_setsThreadsAndMemory(tmp_path: Path) -> None:
    """Alias: GPT P0-3 test_reader_appliesThreadsAndMemoryLimit."""
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 1536, "max_threads": 2}},
    )
    with cm.reader() as r:
        threads = r.execute("SELECT current_setting('threads')").fetchone()[0]
        mem = r.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    assert int(threads) == 2
    assert "1536" in mem or "1.5" in mem.lower() or "1.4" in mem.lower()


def test_reader_appliesThreadsAndMemoryLimit(tmp_path: Path) -> None:
    test_applyPragmas_readerProfile_setsThreadsAndMemory(tmp_path)


def test_reader_appliesTempDirectory(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    import backend.app.db.connection as conn_mod

    data_root = tmp_path / "data"
    monkeypatch.setattr(conn_mod, "DATA_ROOT", data_root)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 512, "max_threads": 1}},
    )
    with cm.reader() as r:
        temp = r.execute("SELECT current_setting('temp_directory')").fetchone()[0]
    assert "duckdb_tmp" in temp
    assert data_root.joinpath("cache", "duckdb_tmp").exists()


def test_applyPragmas_setsMaxTempDirectorySize(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 512, "max_threads": 1, "duckdb_temp_max_gb": 3}},
    )
    with cm.writer() as w:
        temp_max = w.execute(
            "SELECT current_setting('max_temp_directory_size')"
        ).fetchone()[0]
    assert "gib" in str(temp_max).lower()


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


def test_applyPragmas_batchProfile_usesConfiguredMaxThreads(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(
        db,
        profile="batch",
        limits={"batch": {"duckdb_memory_max_mb": 6144, "max_threads": 4}},
    )
    with cm.writer() as w:
        threads = w.execute("SELECT current_setting('threads')").fetchone()[0]
    assert int(threads) == 4


def test_writer_afterExit_releasesLock(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer():
        pass
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f2','qmt')")
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='f2'").fetchone()[0] == 1


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
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='f3'").fetchone()[0] == 1


def test_writer_corruptLockFile_raisesWriteLockError(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    lock_path = db.with_suffix(db.suffix + ".write.lock")
    lock_path.write_text("not-json", encoding="utf-8")
    cm = ConnectionManager(db)
    with pytest.raises(WriteLockError, match="corrupt write lock"):
        with cm.writer():
            pass


def test_writer_exceptionInsideContext_releasesLock(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with pytest.raises(ValueError, match="simulated error"):
        with cm.writer() as w:
            raise ValueError("simulated error inside write")
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('x','test')")
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='x'").fetchone()[0] == 1


def test_writer_connectFailure_releasesLock(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "t.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db)
    import backend.app.db.connection as conn_mod

    real_connect = conn_mod.duckdb.connect
    calls = {"n": 0}

    def _connect_once_fail(path, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise duckdb.Error("simulated connect failure")
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(conn_mod.duckdb, "connect", _connect_once_fail)
    with pytest.raises(duckdb.Error, match="simulated connect"):
        with cm.writer():
            pass
    _init(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('lock_ok','qmt')")
    with cm.reader() as r:
        cnt = r.execute(
            "SELECT COUNT(*) FROM file_registry WHERE file_id='lock_ok'"
        ).fetchone()[0]
        assert cnt == 1


def test_applyPragmas_tempDirectoryWithQuote_doesNotBreakPragma(
    tmp_path: Path, monkeypatch
) -> None:
    db = tmp_path / "t.duckdb"
    _init(db)
    import backend.app.db.connection as conn_mod

    quoted_root = tmp_path / "data'quote"
    monkeypatch.setattr(conn_mod, "DATA_ROOT", quoted_root)
    limits = {"eco": {"duckdb_memory_max_mb": 512, "max_threads": 1}}
    cm = ConnectionManager(db, profile="eco", limits=limits)
    with cm.writer() as w:
        temp = w.execute("SELECT current_setting('temp_directory')").fetchone()[0]
    assert "duckdb_tmp" in temp
