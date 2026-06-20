"""Staged ingestion evidence helpers (Batch 2.5 Phase 3 — not production clean write)."""

from __future__ import annotations

import uuid

from backend.app.datasources.fetch_result import FetchResult

STAGED_FILE_REGISTRY_QUALITY = "STAGED"
STAGED_FILE_REGISTRY_PARSE_STATUS = "PARSED"


def register_staged_file_registry_rows(con, result: FetchResult) -> tuple[str, ...]:
    """Append file_registry rows for micro-fetch raw evidence (Phase 3 only).

    Documented staging exception: bypasses WriteManager because Phase 3 must not
    run validation_report-gated clean writes. Phase 4 clean path must use
    ``FileRegistry`` + ``WriteManager``.
    """
    if result.status != "SUCCESS" or not result.raw_file_paths:
        return ()
    registered: list[str] = []
    for local_path in result.raw_file_paths:
        content_hash = result.content_hash
        if content_hash:
            existing = con.execute(
                "SELECT file_id FROM file_registry WHERE content_hash = ? LIMIT 1",
                [content_hash],
            ).fetchone()
            if existing:
                registered.append(existing[0])
                continue
        file_id = str(uuid.uuid4())
        con.execute(
            """
            INSERT INTO file_registry (
                file_id, file_type, source, source_url, local_path,
                content_hash, schema_hash, fetch_time, as_of_timestamp,
                parse_status, quality_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                file_id,
                "json",
                result.source_id,
                None,
                local_path,
                result.content_hash,
                result.schema_hash,
                result.fetch_time,
                result.as_of_timestamp,
                STAGED_FILE_REGISTRY_PARSE_STATUS,
                STAGED_FILE_REGISTRY_QUALITY,
            ],
        )
        registered.append(file_id)
    return tuple(registered)
