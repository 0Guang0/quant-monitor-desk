"""Data quality validation rules for staging rows and fetch evidence."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

import yaml
from backend.app.db.sql_identifiers import quote_ident
from backend.app.validators.common import as_float, as_text, fetch_rows, is_missing

ValidationStatus = Literal["PASSED", "WARNING", "FAILED"]
FindingSeverity = Literal["failed", "warning"]

_DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parents[3] / "specs/contracts/data_quality_rules.yaml"
)
_FAILED = "failed"
_WARNING = "warning"


@dataclass(frozen=True)
class DataQualityRequest:
    run_id: str
    job_id: str
    data_domain: str
    source_id: str
    staging_table: str
    primary_keys: tuple[str, ...]
    required_fields: tuple[str, ...]
    rule_set_id: str


@dataclass(frozen=True)
class DataQualityFinding:
    rule_id: str
    severity: FindingSeverity
    row_key: str | None
    field_name: str | None
    observed_value: str | None
    expected_condition: str
    message: str


@dataclass(frozen=True)
class DataQualityReport:
    validation_report_id: str
    status: ValidationStatus
    checked_rows: int
    failed_rows: int
    warning_rows: int
    quality_flags: tuple[str, ...]
    can_write_clean: bool
    needs_manual_review: bool
    findings: tuple[DataQualityFinding, ...]


def _load_rule_severities(rules_path: Path) -> dict[str, str]:
    if not rules_path.is_file():
        return {}
    raw = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    severities: dict[str, str] = {}
    for value in raw.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and item.get("id") and item.get("severity"):
                severity = str(item["severity"])
                if severity == "failed_or_warning":
                    severity = _FAILED
                severities[str(item["id"])] = severity
    return severities


def _is_missing(value: object) -> bool:
    return is_missing(value)


def _as_text(value: object) -> str | None:
    return as_text(value)


def _as_float(value: object) -> float | None:
    return as_float(value)


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


class DataQualityValidator:
    """Validate staging rows against Batch C data quality rules."""

    def __init__(self, rules_path: Path = _DEFAULT_RULES_PATH) -> None:
        self._rule_severities = _load_rule_severities(rules_path)

    def _severity(self, rule_id: str) -> FindingSeverity:
        severity = self._rule_severities.get(rule_id, _FAILED)
        return _WARNING if severity == _WARNING else _FAILED

    def _finding(
        self,
        rule_id: str,
        *,
        row_key: str | None,
        field_name: str | None,
        observed_value: object,
        expected_condition: str,
        message: str,
    ) -> DataQualityFinding:
        return DataQualityFinding(
            rule_id=rule_id,
            severity=self._severity(rule_id),
            row_key=row_key,
            field_name=field_name,
            observed_value=_as_text(observed_value),
            expected_condition=expected_condition,
            message=message,
        )

    def _row_key(self, request: DataQualityRequest, row: dict[str, object]) -> str:
        parts = [f"{field}={row.get(field)}" for field in request.primary_keys]
        return "|".join(parts)

    def _build_report(
        self,
        *,
        checked_rows: int,
        findings: list[DataQualityFinding],
    ) -> DataQualityReport:
        failed_keys = {finding.row_key for finding in findings if finding.severity == _FAILED}
        warning_keys = {finding.row_key for finding in findings if finding.severity == _WARNING}
        failed_rows = len(failed_keys)
        warning_rows = len(warning_keys)
        has_failed = any(finding.severity == _FAILED for finding in findings)
        has_warning = any(finding.severity == _WARNING for finding in findings)
        status: ValidationStatus = (
            "FAILED" if has_failed else "WARNING" if has_warning else "PASSED"
        )
        flags = tuple(dict.fromkeys(finding.rule_id for finding in findings))

        return DataQualityReport(
            validation_report_id=str(uuid.uuid4()),
            status=status,
            checked_rows=checked_rows,
            failed_rows=failed_rows,
            warning_rows=warning_rows,
            quality_flags=flags,
            can_write_clean=not has_failed,
            needs_manual_review=any(finding.rule_id == "SCHEMA_DRIFT" for finding in findings),
            findings=tuple(findings),
        )

    def _add_schema_drift_findings(
        self,
        request: DataQualityRequest,
        rows: list[dict[str, object]],
        expected_columns: tuple[str, ...] | None,
        findings: list[DataQualityFinding],
    ) -> None:
        if expected_columns is None:
            return
        expected = set(expected_columns)
        for row in rows:
            actual = set(row)
            if actual == expected:
                continue
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            findings.append(
                self._finding(
                    "SCHEMA_DRIFT",
                    row_key=self._row_key(request, row),
                    field_name=None,
                    observed_value=f"missing={missing}; extra={extra}",
                    expected_condition="staging columns match expected schema",
                    message="schema drift detected; manual review is required before clean write",
                )
            )

    def _add_required_field_findings(
        self,
        request: DataQualityRequest,
        row: dict[str, object],
        row_key: str,
        findings: list[DataQualityFinding],
    ) -> None:
        for field in request.primary_keys:
            if _is_missing(row.get(field)):
                findings.append(
                    self._finding(
                        "MISSING_PRIMARY_KEY",
                        row_key=row_key,
                        field_name=field,
                        observed_value=row.get(field),
                        expected_condition="primary key field is present and non-empty",
                        message=f"primary key field {field!r} is required for clean writes",
                    )
                )

        for field in request.required_fields:
            if field == "source_used" and _is_missing(row.get(field)):
                findings.append(
                    self._finding(
                        "MISSING_SOURCE_USED",
                        row_key=row_key,
                        field_name=field,
                        observed_value=row.get(field),
                        expected_condition="source_used must be recorded for lineage",
                        message="source_used is required for Layer 1 lineage",
                    )
                )
                continue
            if _is_missing(row.get(field)):
                findings.append(
                    self._finding(
                        "MISSING_REQUIRED_FIELD",
                        row_key=row_key,
                        field_name=field,
                        observed_value=row.get(field),
                        expected_condition=f"required field {field!r} is present",
                        message=f"required field {field!r} is missing",
                    )
                )

    def _add_timestamp_findings(
        self,
        row: dict[str, object],
        row_key: str,
        *,
        timestamp_fields: tuple[str, ...],
        findings: list[DataQualityFinding],
    ) -> None:
        for field in timestamp_fields:
            parsed = _parse_datetime(row.get(field))
            if parsed is None:
                findings.append(
                    self._finding(
                        "MISSING_TIMESTAMP",
                        row_key=row_key,
                        field_name=field,
                        observed_value=row.get(field),
                        expected_condition="valid ISO date or timestamp",
                        message=f"timestamp field {field!r} is missing or invalid",
                    )
                )

    def _add_market_bar_findings(
        self,
        row: dict[str, object],
        row_key: str,
        *,
        enum_values: dict[str, tuple[str, ...]],
        findings: list[DataQualityFinding],
    ) -> None:
        for field, allowed_values in enum_values.items():
            value = row.get(field)
            if not _is_missing(value) and str(value) not in allowed_values:
                findings.append(
                    self._finding(
                        "INVALID_ENUM",
                        row_key=row_key,
                        field_name=field,
                        observed_value=value,
                        expected_condition=f"one of {sorted(allowed_values)!r}",
                        message=f"field {field!r} has a value outside the allowed enum",
                    )
                )

        high = _as_float(row.get("high"))
        low = _as_float(row.get("low"))
        if high is not None and low is not None and high < low:
            findings.append(
                self._finding(
                    "INVALID_PRICE_RANGE",
                    row_key=row_key,
                    field_name="high",
                    observed_value=high,
                    expected_condition="high >= low",
                    message="market bar price range is invalid: high is below low",
                )
            )

        for field in ("open", "high", "low", "close", "pre_close"):
            value = _as_float(row.get(field))
            if value is not None and value < 0:
                findings.append(
                    self._finding(
                        "NEGATIVE_PRICE",
                        row_key=row_key,
                        field_name=field,
                        observed_value=value,
                        expected_condition="price field >= 0",
                        message=f"price field {field!r} cannot be negative",
                    )
                )

        volume = _as_float(row.get("volume"))
        if volume is not None and volume < 0:
            findings.append(
                self._finding(
                    "INVALID_VOLUME",
                    row_key=row_key,
                    field_name="volume",
                    observed_value=volume,
                    expected_condition="volume >= 0",
                    message="volume cannot be negative",
                )
            )

        amount = _as_float(row.get("amount"))
        if amount is not None and amount < 0:
            findings.append(
                self._finding(
                    "INVALID_AMOUNT",
                    row_key=row_key,
                    field_name="amount",
                    observed_value=amount,
                    expected_condition="amount >= 0",
                    message="amount cannot be negative",
                )
            )

    def _add_row_findings(
        self,
        request: DataQualityRequest,
        row: dict[str, object],
        row_key: str,
        *,
        timestamp_fields: tuple[str, ...],
        enum_values: dict[str, tuple[str, ...]],
        findings: list[DataQualityFinding],
    ) -> None:
        self._add_required_field_findings(request, row, row_key, findings)
        self._add_timestamp_findings(
            row, row_key, timestamp_fields=timestamp_fields, findings=findings
        )
        self._add_market_bar_findings(row, row_key, enum_values=enum_values, findings=findings)

    def _truthy(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return False

    def _add_layer1_findings(
        self,
        request: DataQualityRequest,
        row: dict[str, object],
        row_key: str,
        findings: list[DataQualityFinding],
    ) -> None:
        if self._truthy(row.get("fallback_used")) and _is_missing(row.get("fallback_reason")):
            findings.append(
                self._finding(
                    "FALLBACK_WITHOUT_REASON",
                    row_key=row_key,
                    field_name="fallback_reason",
                    observed_value=row.get("fallback_reason"),
                    expected_condition="fallback_reason present when fallback_used",
                    message="fallback was used without a recorded reason",
                )
            )
        blindspot = self._truthy(row.get("is_blindspot")) or self._truthy(row.get("blindspot"))
        if blindspot and not _is_missing(row.get("raw_value")):
            findings.append(
                self._finding(
                    "BLINDSPOT_SHOULD_NOT_HAVE_VALUE",
                    row_key=row_key,
                    field_name="raw_value",
                    observed_value=row.get("raw_value"),
                    expected_condition="BlindSpot rows must not carry raw_value",
                    message="BlindSpot row must not contain raw_value",
                )
            )

    def _add_layer3_findings(
        self,
        anchors: list[dict[str, object]],
        known_node_ids: frozenset[str],
        findings: list[DataQualityFinding],
    ) -> None:
        seen_anchor_ids: set[object] = set()
        for anchor in anchors:
            anchor_id = anchor.get("anchor_id")
            if anchor_id is not None:
                if anchor_id in seen_anchor_ids:
                    findings.append(
                        self._finding(
                            "DUPLICATE_ANCHOR_ID",
                            row_key=str(anchor_id),
                            field_name="anchor_id",
                            observed_value=anchor_id,
                            expected_condition="anchor_id is unique within config batch",
                            message="duplicate anchor_id in Layer 3 config",
                        )
                    )
                seen_anchor_ids.add(anchor_id)
            node_id = anchor.get("node_id")
            if node_id is not None and str(node_id) not in known_node_ids:
                findings.append(
                    self._finding(
                        "MISSING_NODE_REFERENCE",
                        row_key=str(anchor_id) if anchor_id is not None else None,
                        field_name="node_id",
                        observed_value=node_id,
                        expected_condition="node_id exists in known node registry",
                        message="anchor references a node_id that does not exist",
                    )
                )
            priority = str(anchor.get("priority", "")).upper()
            if priority == "P0" and _is_missing(anchor.get("source_keys")):
                findings.append(
                    self._finding(
                        "P0_MISSING_SOURCE_KEYS",
                        row_key=str(anchor_id) if anchor_id is not None else None,
                        field_name="source_keys",
                        observed_value=anchor.get("source_keys"),
                        expected_condition="P0 anchors must declare source_keys",
                        message="P0 anchor is missing source_keys",
                    )
                )

    def validate_rows(
        self,
        request: DataQualityRequest,
        rows: list[dict[str, object]],
        *,
        expected_columns: tuple[str, ...] | None = None,
        timestamp_fields: tuple[str, ...] = (),
        enum_values: dict[str, tuple[str, ...]] | None = None,
        as_of_field: str | None = None,
        max_stale_days: int | None = None,
        min_history_rows: int | None = None,
        reference_time: datetime | None = None,
        layer3_anchors: list[dict[str, object]] | None = None,
        known_node_ids: frozenset[str] | None = None,
    ) -> DataQualityReport:
        findings: list[DataQualityFinding] = []
        enum_values = enum_values or {}

        self._add_schema_drift_findings(request, rows, expected_columns, findings)

        seen_keys: set[tuple[object, ...]] = set()
        for row in rows:
            row_key = self._row_key(request, row)
            pk_values = tuple(row.get(field) for field in request.primary_keys)
            if not any(_is_missing(value) for value in pk_values):
                if pk_values in seen_keys:
                    findings.append(
                        self._finding(
                            "DUPLICATE_PRIMARY_KEY",
                            row_key=row_key,
                            field_name=",".join(request.primary_keys),
                            observed_value=row_key,
                            expected_condition="primary key tuple is unique",
                            message="duplicate primary key found in staging rows",
                        )
                    )
                seen_keys.add(pk_values)

            self._add_row_findings(
                request,
                row,
                row_key,
                timestamp_fields=timestamp_fields,
                enum_values=enum_values,
                findings=findings,
            )
            self._add_layer1_findings(request, row, row_key, findings)

        if layer3_anchors is not None:
            self._add_layer3_findings(
                layer3_anchors,
                known_node_ids or frozenset(),
                findings,
            )

        if min_history_rows is not None and len(rows) < min_history_rows:
            findings.append(
                self._finding(
                    "INSUFFICIENT_HISTORY",
                    row_key=None,
                    field_name=None,
                    observed_value=len(rows),
                    expected_condition=f"at least {min_history_rows} rows",
                    message="insufficient history for downstream calculations",
                )
            )

        if as_of_field and max_stale_days is not None and rows:
            reference = reference_time or datetime.now(UTC)
            reference = reference if reference.tzinfo else reference.replace(tzinfo=UTC)
            parsed_times = [_parse_datetime(row.get(as_of_field)) for row in rows]
            valid_times = [value for value in parsed_times if value is not None]
            if valid_times:
                latest = max(valid_times)
                if (reference - latest).days > max_stale_days:
                    findings.append(
                        self._finding(
                            "STALE_DATA",
                            row_key=None,
                            field_name=as_of_field,
                            observed_value=latest.isoformat(),
                            expected_condition=f"latest data age <= {max_stale_days} days",
                            message="staging data is stale relative to validation time",
                        )
                    )

        return self._build_report(checked_rows=len(rows), findings=findings)

    def _table_exists(self, con, table_name: str) -> bool:
        quote_ident(table_name)
        row = con.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = ?
            """,
            [table_name],
        ).fetchone()
        return bool(row and row[0])

    def _fetch_rows(self, con, table_name: str) -> list[dict[str, object]]:
        return fetch_rows(con, table_name)

    def _persist_report(
        self,
        con,
        request: DataQualityRequest,
        report: DataQualityReport,
    ) -> None:
        created_at = datetime.now(UTC)
        stale_reason = "STALE_DATA" if "STALE_DATA" in report.quality_flags else None
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, job_id, data_domain,
                staging_table, source_id, status, checked_rows, failed_rows,
                warning_rows, quality_flags, stale_reason, can_write_clean,
                needs_manual_review, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                report.validation_report_id,
                request.run_id,
                request.job_id,
                request.data_domain,
                request.staging_table,
                request.source_id,
                report.status,
                report.checked_rows,
                report.failed_rows,
                report.warning_rows,
                json.dumps(list(report.quality_flags)),
                stale_reason,
                report.can_write_clean,
                report.needs_manual_review,
                created_at,
            ],
        )
        for finding in report.findings:
            con.execute(
                """
                INSERT INTO data_quality_log (
                    log_id, validation_report_id, run_id, job_id, data_domain,
                    source_id, table_name, row_key, field_name, rule_id,
                    severity, observed_value, expected_condition, message,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(uuid.uuid4()),
                    report.validation_report_id,
                    request.run_id,
                    request.job_id,
                    request.data_domain,
                    request.source_id,
                    request.staging_table,
                    finding.row_key,
                    finding.field_name,
                    finding.rule_id,
                    finding.severity,
                    finding.observed_value,
                    finding.expected_condition,
                    finding.message,
                    created_at,
                ],
            )

    def _missing_staging_finding(self, request: DataQualityRequest) -> DataQualityFinding:
        return self._finding(
            "MISSING_STAGING_TABLE",
            row_key="fetch_result",
            field_name="staging_table",
            observed_value=request.staging_table,
            expected_condition="SUCCESS fetch result has a readable staging table",
            message="SUCCESS fetch result cannot be clean-write-ready without staging data",
        )

    def _missing_raw_finding(self, raw_path: str) -> DataQualityFinding:
        return self._finding(
            "MISSING_RAW_EVIDENCE",
            row_key="fetch_result",
            field_name="raw_file_paths",
            observed_value=raw_path,
            expected_condition="raw evidence path exists when provided",
            message="SUCCESS fetch result references raw evidence that does not exist",
        )

    def validate_table(
        self,
        con,
        request: DataQualityRequest,
        *,
        expected_columns: tuple[str, ...] | None = None,
        timestamp_fields: tuple[str, ...] = (),
        enum_values: dict[str, tuple[str, ...]] | None = None,
        as_of_field: str | None = None,
        max_stale_days: int | None = None,
        min_history_rows: int | None = None,
        reference_time: datetime | None = None,
    ) -> DataQualityReport:
        if not self._table_exists(con, request.staging_table):
            report = self._build_report(
                checked_rows=0,
                findings=[self._missing_staging_finding(request)],
            )
            self._persist_report(con, request, report)
            return report

        rows = self._fetch_rows(con, request.staging_table)
        report = self.validate_rows(
            request,
            rows,
            expected_columns=expected_columns,
            timestamp_fields=timestamp_fields,
            enum_values=enum_values,
            as_of_field=as_of_field,
            max_stale_days=max_stale_days,
            min_history_rows=min_history_rows,
            reference_time=reference_time,
        )
        self._persist_report(con, request, report)
        return report

    def validate_fetch_result(
        self,
        con,
        request: DataQualityRequest,
        fetch_result,
        *,
        expected_columns: tuple[str, ...] | None = None,
        timestamp_fields: tuple[str, ...] = (),
        enum_values: dict[str, tuple[str, ...]] | None = None,
        as_of_field: str | None = None,
        max_stale_days: int | None = None,
        min_history_rows: int | None = None,
        reference_time: datetime | None = None,
    ) -> DataQualityReport:
        findings: list[DataQualityFinding] = []
        if fetch_result.status != "SUCCESS":
            findings.append(
                self._finding(
                    "FETCH_NOT_SUCCESS",
                    row_key="fetch_result",
                    field_name="status",
                    observed_value=fetch_result.status,
                    expected_condition="fetch status is SUCCESS before clean validation",
                    message="non-success fetch results cannot be clean-write-ready",
                )
            )

        if (
            con is None
            or not fetch_result.staging_table
            or not self._table_exists(con, request.staging_table)
        ):
            findings.append(self._missing_staging_finding(request))

        for raw_path in fetch_result.raw_file_paths:
            if not Path(raw_path).is_file():
                findings.append(self._missing_raw_finding(raw_path))

        if findings:
            report = self._build_report(checked_rows=0, findings=findings)
            if con is not None:
                self._persist_report(con, request, report)
            return report

        return self.validate_table(
            con,
            request,
            expected_columns=expected_columns,
            timestamp_fields=timestamp_fields,
            enum_values=enum_values,
            as_of_field=as_of_field,
            max_stale_days=max_stale_days,
            min_history_rows=min_history_rows,
            reference_time=reference_time,
        )
