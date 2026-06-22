"""Raw Store and file_registry tests (Round 1 task 009)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteResult
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore, sha256_hex
from tests.db_helpers import create_test_write_manager


def test_sha256Hex_knownInput_matchesExpected() -> None:
    assert sha256_hex(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_save_writesFileAndComputesHash(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    saved = store.save(
        b"hello", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    assert Path(saved.local_path).read_bytes() == b"hello"
    assert saved.content_hash == sha256_hex(b"hello")
    assert saved.as_of == "2026-06-15"


def test_save_pathLayout_matchesConvention(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    saved = store.save(
        b"hello", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    expected_hash = sha256_hex(b"hello")
    assert f"raw{os.sep}qmt{os.sep}daily_bar{os.sep}2026-06-15{os.sep}" in saved.local_path
    assert saved.local_path.endswith(f"{expected_hash}.json")


def test_save_fileIdFormat_isHashPrefixPlusSource(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    saved = store.save(
        b"hello", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    assert saved.file_id == saved.content_hash[:16] + "qmt"


def test_save_pathTraversal_raises(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="invalid source"):
        store.save(b"x", source="..", data_domain="daily_bar", file_type="json", as_of="2026-06-15")


def test_save_invalidDataDomain_raises(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="invalid data_domain"):
        store.save(
            b"x",
            source="qmt",
            data_domain="../escape",
            file_type="json",
            as_of="2026-06-15",
        )


def test_save_invalidAsOf_raises(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="invalid as_of"):
        store.save(
            b"x",
            source="qmt",
            data_domain="daily_bar",
            file_type="json",
            as_of="bad as of!",
        )


def test_save_unsupportedFileType_raises(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="unsupported file_type"):
        store.save(b"x", source="qmt", data_domain="daily_bar", file_type="xml", as_of="2026-06-15")


def test_save_oversizedContent_raises(tmp_path: Path) -> None:
    from backend.app.storage import raw_store

    store = RawStore(tmp_path)
    huge = b"x" * (raw_store.MAX_RAW_FILE_BYTES + 1)
    with pytest.raises(ValueError, match="exceeds max size"):
        store.save(
            huge, source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
        )


def _cm(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    return ConnectionManager(db)


def _registry(cm: ConnectionManager) -> FileRegistry:
    return FileRegistry(
        cm,
        create_test_write_manager(cm),
        validation_report_id="stub-pass-registry",
    )


def test_register_newFile_insertsRegistryRow(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    fid = reg.register(saved)
    with cm.reader() as r:
        got = r.execute(
            "SELECT source, content_hash FROM file_registry WHERE file_id=?",
            [fid],
        ).fetchone()
    assert got == ("qmt", saved.content_hash)
    with cm.reader() as r:
        status = r.execute(
            "SELECT parse_status, quality_flag FROM file_registry WHERE file_id=?",
            [fid],
        ).fetchone()
    assert status == ("raw_saved", "pending_validation")


def test_register_writesAuditLog(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    reg.register(saved)
    with cm.reader() as r:
        audit = r.execute(
            "SELECT status, target_table FROM write_audit_log WHERE target_table='file_registry'"
        ).fetchone()
    assert audit == ("SUCCESS", "file_registry")


def test_register_asOfTimestamp_matchesAsOfArgument(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    reg.register(saved)
    with cm.reader() as r:
        as_of_ts = r.execute(
            "SELECT CAST(as_of_timestamp AS DATE) FROM file_registry WHERE file_id=?",
            [saved.file_id],
        ).fetchone()[0]
    assert str(as_of_ts) == "2026-06-15"


def test_exists_whenHashPresent_returnsTrue(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    assert reg.exists(saved.content_hash) is False
    reg.register(saved)
    assert reg.exists(saved.content_hash) is True


def test_register_duplicateHash_returnsSameFileId(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    fid1 = reg.register(saved)
    fid2 = reg.register(saved)
    assert fid1 == fid2
    with cm.reader() as r:
        cnt = r.execute(
            "SELECT COUNT(*) FROM file_registry WHERE content_hash=?",
            [saved.content_hash],
        ).fetchone()[0]
    assert cnt == 1


def test_register_duplicateHashViaConstraint_returnsSameFileId(tmp_path: Path) -> None:
    """Simulate race: pre-check misses duplicate but UNIQUE index catches insert."""
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )

    with cm.writer() as con:
        con.execute("BEGIN")
        con.execute(
            """
            INSERT INTO file_registry (
                file_id, file_type, source, local_path, content_hash,
                fetch_time, as_of_timestamp, parse_status, quality_flag
            ) VALUES (
                ?, 'json', 'qmt', '/p', ?,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'parsed', 'ok'
            )
            """,
            [saved.file_id, saved.content_hash],
        )
        con.execute("COMMIT")

    import backend.app.storage.file_registry as fr_mod

    original_lookup = FileRegistry._lookup_by_content_hash

    def _miss_once(self, content_hash, con=None):
        if not hasattr(_miss_once, "called"):
            _miss_once.called = True
            return None
        return original_lookup(self, content_hash, con=con)

    fr_mod.FileRegistry._lookup_by_content_hash = _miss_once  # type: ignore[method-assign]
    try:
        fid = reg.register(saved)
        assert fid == saved.file_id
    finally:
        fr_mod.FileRegistry._lookup_by_content_hash = original_lookup  # type: ignore[method-assign]

    with cm.reader() as r:
        cnt = r.execute(
            "SELECT COUNT(*) FROM file_registry WHERE content_hash=?",
            [saved.content_hash],
        ).fetchone()[0]
    assert cnt == 1


def test_register_whenWriteFails_raisesRuntimeError(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    wm = MagicMock()
    wm.write.return_value = WriteResult(write_id="x", status="FAILED", error_message="db error")
    reg = FileRegistry(cm, wm, validation_report_id="stub-pass-registry")
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    with pytest.raises(RuntimeError, match="file_registry write failed"):
        reg.register(saved)
    with cm.reader() as r:
        cnt = r.execute("SELECT COUNT(*) FROM file_registry").fetchone()[0]
    assert cnt == 0


def test_register_validationRejected_persistsFailedAudit(tmp_path: Path) -> None:
    """Failed validation must leave write_audit_log even when register raises."""
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = FileRegistry(
        cm,
        create_test_write_manager(cm),
        validation_report_id="stub-fail-registry",
    )
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    with pytest.raises(RuntimeError, match="file_registry write failed"):
        reg.register(saved)
    with cm.reader() as r:
        audit = r.execute(
            "SELECT status, target_table, error_message FROM write_audit_log"
        ).fetchone()
        file_cnt = r.execute("SELECT COUNT(*) FROM file_registry").fetchone()[0]
    assert file_cnt == 0
    assert audit == ("FAILED", "file_registry", "validation rejected: stub-fail-registry")


def test_stagedEvidence_pathEscape_rejected(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.storage.staged_evidence import register_staged_file_registry_rows

    cm = _cm(tmp_path)
    data_root = tmp_path / "data"
    data_root.mkdir()
    evil = tmp_path / "outside" / "evil.json"
    evil.parent.mkdir(parents=True)
    evil.write_text("{}", encoding="utf-8")
    result = FetchResult(
        run_id="r1",
        source_id="akshare",
        data_domain="macro_supplementary",
        status="SUCCESS",
        row_count=1,
        fetch_time=datetime.now(UTC).isoformat(),
        raw_file_paths=[str(evil)],
        content_hash="abc123",
        schema_hash="def456",
    )
    with cm.writer() as con:
        with pytest.raises(ValueError, match="escapes data_root"):
            register_staged_file_registry_rows(con, result, data_root=data_root)


def test_stagedEvidence_allowedPath_registersRow(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.storage.staged_evidence import register_staged_file_registry_rows

    cm = _cm(tmp_path)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw" / "akshare" / "macro_supplementary" / "2024-06-15"
    raw_dir.mkdir(parents=True)
    raw_file = raw_dir / "evidence.json"
    raw_file.write_text('{"v":1}', encoding="utf-8")
    result = FetchResult(
        run_id="r1",
        source_id="akshare",
        data_domain="macro_supplementary",
        status="SUCCESS",
        row_count=1,
        fetch_time=datetime.now(UTC).isoformat(),
        raw_file_paths=[str(raw_file)],
        content_hash="abc123unique",
        schema_hash="def456",
    )
    with cm.writer() as con:
        ids = register_staged_file_registry_rows(con, result, data_root=data_root)
    assert len(ids) == 1
    with cm.reader() as r:
        row = r.execute(
            "SELECT local_path, quality_flag FROM file_registry WHERE file_id = ?",
            [ids[0]],
        ).fetchone()
    assert row[1] == "STAGED"
    assert "evidence.json" in row[0]


def test_save_windowsLongPath_writesSuccessfully(tmp_path: Path) -> None:
    """Regression: deep evidence sandbox paths must not fail on Windows MAX_PATH."""
    import os

    if os.name != "nt":
        pytest.skip("Windows long-path regression only")
    deep_root = tmp_path
    for segment in (
        ".audit-sandbox",
        "pytest-9agent-restored-targeted",
        "test_layer1Ingestion_phase3_taskEvidenceArtifacts0",
        "evidence",
        ".phase3-micro-fetch-sandbox",
        "data",
    ):
        deep_root = deep_root / segment
    store = RawStore(deep_root)
    saved = store.save(
        b'{"observations":[{"metric_value":1.0}]}',
        source="akshare",
        data_domain="macro_supplementary",
        file_type="json",
        as_of="2024-06-15",
    )
    from backend.app.storage.path_compat import is_file

    assert is_file(Path(saved.local_path))
    assert len(str(Path(saved.local_path).resolve())) >= 260
