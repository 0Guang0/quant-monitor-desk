"""File registry — index raw files via WriteManager."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.storage.raw_store import SavedFile

STG_FILE_REGISTRY = "stg_file_registry"


def _parse_as_of_timestamp(as_of: str) -> datetime:
    """Parse YYYY-MM-DD as-of date into UTC midnight timestamp."""
    return datetime.fromisoformat(as_of).replace(tzinfo=UTC)


class FileRegistry:
    def __init__(
        self,
        conn_manager,
        write_manager: WriteManager,
        *,
        validation_report_id: str,
    ) -> None:
        self.conn_manager = conn_manager
        self.write_manager = write_manager
        self._validation_report_id = validation_report_id

    def _lookup_by_content_hash(
        self, content_hash: str, con: duckdb.DuckDBPyConnection | None = None
    ) -> str | None:
        if con is not None:
            row = con.execute(
                "SELECT file_id FROM file_registry WHERE content_hash = ? LIMIT 1",
                [content_hash],
            ).fetchone()
            return row[0] if row else None
        with self.conn_manager.reader() as reader:
            row = reader.execute(
                "SELECT file_id FROM file_registry WHERE content_hash = ? LIMIT 1",
                [content_hash],
            ).fetchone()
        return row[0] if row else None

    def exists(self, content_hash: str) -> bool:
        return self._lookup_by_content_hash(content_hash) is not None

    def register(self, saved: SavedFile) -> str:
        with self.conn_manager.writer() as con:
            return self.register_on_connection(
                con,
                saved,
                run_id="raw_store",
                job_id="register",
                own_transaction=True,
            )

    def register_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        saved: SavedFile,
        *,
        run_id: str,
        job_id: str,
        own_transaction: bool = False,
    ) -> str:
        existing = self._lookup_by_content_hash(saved.content_hash, con=con)
        if existing:
            return existing

        now = datetime.now(UTC)
        as_of_ts = _parse_as_of_timestamp(saved.as_of)
        req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table="file_registry",
            staging_table=STG_FILE_REGISTRY,
            write_mode="append_only",
            primary_keys=("file_id",),
            validation_report_id=self._validation_report_id,
            source_used=saved.source,
            data_domain=saved.data_domain,
        )

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
                as_of_ts,
                "raw_saved",
                "pending_validation",
            ],
        )
        result = self.write_manager.write(req, con=con, own_transaction=own_transaction)
        if result.status != "SUCCESS":
            err = result.error_message or ""
            if "onstraint" in err:
                existing = self._lookup_by_content_hash(saved.content_hash, con=con)
                if existing:
                    return existing
            raise RuntimeError(f"file_registry write failed: {result.error_message}")

        return saved.file_id
