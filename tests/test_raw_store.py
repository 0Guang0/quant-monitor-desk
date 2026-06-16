"""Raw Store and file_registry tests (Round 1 task 009)."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteManager
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore, sha256_hex


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
        store.save(
            b"x", source="..", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
        )


def test_save_unsupportedFileType_raises(tmp_path: Path) -> None:
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="unsupported file_type"):
        store.save(
            b"x", source="qmt", data_domain="daily_bar", file_type="xml", as_of="2026-06-15"
        )


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


def test_register_newFile_insertsRegistryRow(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    fid = reg.register(saved)
    r = cm.reader()
    got = r.execute(
        "SELECT source, content_hash FROM file_registry WHERE file_id=?",
        [fid],
    ).fetchone()
    assert got == ("qmt", saved.content_hash)
    r.close()


def test_register_writesAuditLog(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    reg.register(saved)
    r = cm.reader()
    audit = r.execute(
        "SELECT status, target_table FROM write_audit_log WHERE target_table='file_registry'"
    ).fetchone()
    assert audit == ("SUCCESS", "file_registry")
    r.close()


def test_exists_whenHashPresent_returnsTrue(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    assert reg.exists(saved.content_hash) is False
    reg.register(saved)
    assert reg.exists(saved.content_hash) is True


def test_register_duplicateHash_returnsSameFileId(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(
        b"x", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    fid1 = reg.register(saved)
    fid2 = reg.register(saved)
    assert fid1 == fid2
    cnt = cm.reader().execute(
        "SELECT COUNT(*) FROM file_registry WHERE content_hash=?",
        [saved.content_hash],
    ).fetchone()[0]
    assert cnt == 1
