"""Tier A live B2 adapter — DataQualityValidator.validate_table on clean tables (S-R2-B2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.db.connection import ConnectionManager
from backend.app.layer1_axes.observation_contract import (
    AXIS_OBSERVATION_DDL_COLUMNS,
    AXIS_OBSERVATION_REQUIRED_FIELDS,
)
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator

_SECURITY_BAR_COLUMNS: tuple[str, ...] = (
    "instrument_id",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "volume",
    "amount",
    "adjustment_type",
    "source_used",
    "batch_id",
    "quality_flags",
    "created_at",
)
_CN_ANNOUNCEMENT_COLUMNS: tuple[str, ...] = (
    "announcement_id",
    "instrument_id",
    "title",
    "publish_timestamp",
    "announcement_url",
    "announcement_type",
    "data_domain",
    "source_used",
    "pdf_file_id",
    "extracted_text_file_id",
    "content_status",
    "batch_id",
    "source_fetch_id",
    "content_hash",
    "schema_hash",
    "quality_flags",
    "created_at",
)
_US_DISCLOSURE_COLUMNS: tuple[str, ...] = (
    "accession_number",
    "cik",
    "form_type",
    "filing_date",
    "report_date",
    "primary_document_url",
    "data_domain",
    "source_used",
    "batch_id",
    "source_fetch_id",
    "content_hash",
    "schema_hash",
    "quality_flags",
    "created_at",
)
_CRYPTO_DERIVATIVE_COLUMNS: tuple[str, ...] = (
    "instrument_name",
    "as_of_timestamp",
    "data_domain",
    "expiration_timestamp",
    "strike",
    "option_type",
    "mark_iv",
    "source_used",
    "batch_id",
    "source_fetch_id",
    "content_hash",
    "schema_hash",
    "quality_flags",
    "created_at",
)

_CLEAN_TABLE_SPECS: dict[str, dict[str, Any]] = {
    "security_bar_1d": {
        "expected_columns": _SECURITY_BAR_COLUMNS,
        "timestamp_fields": ("trade_date",),
        "required_fields": ("close", "source_used"),
    },
    "axis_observation": {
        "expected_columns": AXIS_OBSERVATION_DDL_COLUMNS,
        "timestamp_fields": ("as_of_timestamp", "publish_timestamp", "fetch_time"),
        "required_fields": AXIS_OBSERVATION_REQUIRED_FIELDS,
    },
    "cn_announcement_clean": {
        "expected_columns": _CN_ANNOUNCEMENT_COLUMNS,
        "timestamp_fields": ("publish_timestamp",),
        "required_fields": ("title", "source_used", "content_hash", "schema_hash"),
    },
    "us_disclosure_clean": {
        "expected_columns": _US_DISCLOSURE_COLUMNS,
        "timestamp_fields": ("filing_date",),
        "required_fields": ("form_type", "source_used", "content_hash", "schema_hash"),
    },
    "crypto_derivative_clean": {
        "expected_columns": _CRYPTO_DERIVATIVE_COLUMNS,
        "timestamp_fields": ("as_of_timestamp",),
        "required_fields": ("source_used", "content_hash", "schema_hash"),
    },
}


def _clean_table_spec(clean_table: str) -> dict[str, Any]:
    try:
        return _CLEAN_TABLE_SPECS[clean_table]
    except KeyError as exc:
        raise ValueError(f"no B2 validation spec for clean_table={clean_table!r}") from exc


def run_b2_validate_table(
    source_id: str,
    *,
    binding: dict[str, Any],
    db_path: Path,
    run_id: str,
    job_id: str,
    validator: DataQualityValidator | None = None,
) -> tuple[str, str]:
    """Validate one Tier A clean table via DataQualityValidator.validate_table."""
    clean_table = str(binding["clean_table"])
    data_domain = str(binding["data_domain"])
    rule_set_id = str(binding["rule_set_id"])
    target = resolve_clean_write_target(data_domain)
    spec = _clean_table_spec(clean_table)
    request = DataQualityRequest(
        run_id=run_id,
        job_id=job_id,
        data_domain=data_domain,
        source_id=source_id,
        staging_table=clean_table,
        primary_keys=target.primary_keys,
        required_fields=spec["required_fields"],
        rule_set_id=rule_set_id,
    )
    quality = validator or DataQualityValidator()
    cm = ConnectionManager(db_path=db_path)
    with cm.writer() as con:
        report = quality.validate_table(
            con,
            request,
            expected_columns=spec["expected_columns"],
            timestamp_fields=spec["timestamp_fields"],
        )
    detail = report.status
    if report.quality_flags:
        detail = f"{report.status} flags={','.join(report.quality_flags)}"
    return report.status, detail


__all__ = ["run_b2_validate_table"]
