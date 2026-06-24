"""Staged ingestion evidence helpers (Batch 2.5 Phase 3 — not production clean write)."""

from __future__ import annotations

import uuid
from pathlib import Path

from backend.app.datasources.fetch_result import FetchResult
from backend.app.storage.path_compat import is_relative_to_data_root

STAGED_FILE_REGISTRY_QUALITY = "STAGED"
STAGED_FILE_REGISTRY_PARSE_STATUS = "PARSED"
STAGED_EVIDENCE_PHASE = "phase3_staged"

# R3Y-STAGED-REG-001: Public staging writes go through WriteManager (see
# ``ops/staged_pilot._StagedPilotFileRegistry`` + ``_StagedPilotValidationGate``).
# Metadata-only gate: ``can_write_clean=false`` — file_registry rows carry
# quality_flag=STAGED without validation_report-gated clean promotion.
# ``write_contract.yaml`` staging_table + validation_report_id still apply on
# the WriteManager path; this module keeps only a **private** legacy INSERT
# helper for in-module / test regression of path sandbox + phase token.

__all__ = (
    "STAGED_EVIDENCE_PHASE",
    "STAGED_FILE_REGISTRY_PARSE_STATUS",
    "STAGED_FILE_REGISTRY_QUALITY",
)


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


def _register_staged_file_registry_rows(
    con,
    result: FetchResult,
    *,
    data_root: Path,
    phase: str = STAGED_EVIDENCE_PHASE,
) -> tuple[str, ...]:
    """Private legacy INSERT for Phase 3 micro-fetch evidence (tests only).

    Documented staging exception: bypasses WriteManager because Phase 3 must not
    run validation_report-gated clean writes. Production staged pilot uses
    ``FileRegistry`` + ``WriteManager`` (metadata-only gate). Not exported;
    callers outside this module must use WriteManager.

    Paths must stay within ``data_root`` (ADV-A1-004).
    """
    if phase != STAGED_EVIDENCE_PHASE:
        raise ValueError(
            f"_register_staged_file_registry_rows requires "
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
