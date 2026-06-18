"""Validation and write pipeline ports for DataSyncOrchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest, WriteResult
from backend.app.validators.data_quality import (
    DataQualityReport,
    DataQualityRequest,
    DataQualityValidator,
)
from backend.app.validators.source_conflict import (
    SourceConflictReport,
    SourceConflictRequest,
    SourceConflictValidator,
)


@dataclass(frozen=True)
class ValidationPipelineResult:
    quality: DataQualityReport
    conflict: SourceConflictReport | None


class SyncValidationPipeline:
    """Encapsulates quality + conflict validation for sync jobs."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        *,
        quality_validator: DataQualityValidator | None = None,
        conflict_validator: SourceConflictValidator | None = None,
    ) -> None:
        self._cm = connection_manager
        self._quality = quality_validator or DataQualityValidator()
        self._conflict = conflict_validator or SourceConflictValidator()

    def validate_staging(
        self,
        con,
        *,
        quality_request: DataQualityRequest,
        expected_columns: tuple[str, ...],
        timestamp_fields: tuple[str, ...],
        conflict_request: SourceConflictRequest | None = None,
        conflict_staging_table: str | None = None,
    ) -> ValidationPipelineResult:
        quality = self._quality.validate_table(
            con,
            quality_request,
            expected_columns=expected_columns,
            timestamp_fields=timestamp_fields,
        )
        conflict: SourceConflictReport | None = None
        if conflict_request is not None and conflict_staging_table is not None:
            conflict = self._conflict.validate_table(
                con,
                conflict_request,
                staging_table=conflict_staging_table,
            )
        return ValidationPipelineResult(quality=quality, conflict=conflict)


class SyncWritePipeline:
    """Encapsulates ValidationGate + WriteManager clean writes."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._cm = connection_manager
        self._write_manager = WriteManager(connection_manager, DbValidationGate(connection_manager))

    def write_clean(
        self,
        con,
        request: WriteRequest,
        *,
        own_transaction: bool = False,
    ) -> WriteResult:
        return self._write_manager.write(request, con=con, own_transaction=own_transaction)
