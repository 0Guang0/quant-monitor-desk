"""Staged ingestion evidence helpers (Batch 2.5 Phase 3 — not production clean write)."""

from __future__ import annotations

import uuid
from pathlib import Path

from backend.app.datasources.fetch_result import FetchResult
from backend.app.storage.path_compat import is_relative_to_data_root

STAGED_FILE_REGISTRY_QUALITY = "STAGED"
STAGED_FILE_REGISTRY_PARSE_STATUS = "PARSED"
STAGED_EVIDENCE_PHASE = "phase3_staged"

# ADV-POST14-B-007: Layer1 Phase 3 retains this documented WriteManager bypass for
# micro-fetch rows that must never trigger validation_report-gated clean writes.
# PROMPT_14 staged pilot uses WriteManager via ``staged_pilot._StagedPilotFileRegistry``
# plus ``_StagedPilotValidationGate`` (``can_write_clean=false`` metadata-only gate)
# instead of this raw INSERT helper.


def _resolve_under_data_root(local_path: str, data_root: Path) -> Path:
    resolved_root = Path(data_root).resolve()
    candidate = Path(local_path)
    if not candidate.is_absolute():
        candidate = (resolved_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not is_relative_to_data_root(candidate, resolved_root):
        raise ValueError(f"staged path escapes data_root: {local_path!r}")
    return candidate


def register_staged_file_registry_rows(
    con,
    result: FetchResult,
    *,
    data_root: Path,
    phase: str = STAGED_EVIDENCE_PHASE,
) -> tuple[str, ...]:
    """Append file_registry rows for micro-fetch raw evidence (Phase 3 only).

    Documented staging exception: bypasses WriteManager because Phase 3 must not
    run validation_report-gated clean writes. Phase 4 clean path must use
    ``FileRegistry`` + ``WriteManager``.

    Paths must stay within ``data_root`` (ADV-A1-004).
    """
    if phase != STAGED_EVIDENCE_PHASE:
        raise ValueError(
            f"register_staged_file_registry_rows requires "
            f"phase={STAGED_EVIDENCE_PHASE!r}; got {phase!r}"
        )
    if result.status != "SUCCESS" or not result.raw_file_paths:
        return ()
    registered: list[str] = []
    for local_path in result.raw_file_paths:
        safe_path = _resolve_under_data_root(local_path, data_root)
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
                str(safe_path),
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
