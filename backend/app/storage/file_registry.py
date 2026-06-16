"""File registry — index raw files via WriteManager."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.storage.raw_store import SavedFile

STG_FILE_REGISTRY = "stg_file_registry"


class FileRegistry:
    def __init__(self, conn_manager, write_manager: WriteManager) -> None:
        self.conn_manager = conn_manager
        self.write_manager = write_manager

    def _lookup_by_content_hash(
        self, content_hash: str, con: duckdb.DuckDBPyConnection | None = None
    ) -> str | None:
        if con is not None:
            row = con.execute(
                "SELECT file_id FROM file_registry WHERE content_hash = ? LIMIT 1",
                [content_hash],
            ).fetchone()
            return row[0] if row else None
        reader = self.conn_manager.reader()
        try:
            row = reader.execute(
                "SELECT file_id FROM file_registry WHERE content_hash = ? LIMIT 1",
                [content_hash],
            ).fetchone()
        finally:
            reader.close()
        return row[0] if row else None

    def exists(self, content_hash: str) -> bool:
        return self._lookup_by_content_hash(content_hash) is not None

    def register(self, saved: SavedFile) -> str:
        now = datetime.now(UTC)
        req = WriteRequest(
            run_id="raw_store",
            job_id="register",
            target_table="file_registry",
            staging_table=STG_FILE_REGISTRY,
            write_mode="append_only",
            primary_keys=["file_id"],
            validation_report_id="stub-pass-registry",
            source_used=saved.source,
        )

        with self.conn_manager.writer() as con:
            con.execute("BEGIN")
            try:
                existing = self._lookup_by_content_hash(saved.content_hash, con=con)
                if existing:
                    con.execute("COMMIT")
                    return existing

                con.execute(f"DELETE FROM {STG_FILE_REGISTRY}")
                con.execute(
                    f"""
                    INSERT INTO {STG_FILE_REGISTRY} (
                        file_id, file_type, source, source_url, local_path,
                        content_hash, schema_hash, fetch_time, as_of_timestamp,
                        parse_status, quality_flag
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        saved.file_id,
                        saved.file_type,
                        saved.source,
                        None,
                        saved.local_path,
                        saved.content_hash,
                        None,
                        now,
                        now,
                        "parsed",
                        "ok",
                    ],
                )
                result = self.write_manager.write(req, con=con, own_transaction=False)
                if result.status != "SUCCESS":
                    con.execute("ROLLBACK")
                    raise RuntimeError(f"file_registry write failed: {result.error_message}")
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise

        return saved.file_id
