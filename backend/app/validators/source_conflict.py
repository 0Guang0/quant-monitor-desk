"""Pure source conflict validation rules for multi-source staging rows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from backend.app.validators.common import as_float, as_text, fetch_rows
from backend.app.validators.rule_contract import default_conflict_rule_contract

ConflictStatus = Literal["PASSED", "WARNING", "SEVERE_CONFLICT"]
ConflictSeverity = Literal["warning", "severe", "methodology_difference"]

_DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parents[3] / "specs/contracts/source_conflict_rules.yaml"
)
_WARNING = "warning"
_SEVERE = "severe"
_METHODOLOGY = "methodology_difference"


@dataclass(frozen=True)
class SourceConflictRequest:
    run_id: str
    job_id: str
    data_domain: str
    primary_source: str
    validation_sources: tuple[str, ...]
    key_fields: tuple[str, ...]
    comparable_fields: tuple[str, ...]
    tolerance_rule_set_id: str


@dataclass(frozen=True)
class SourceConflictFinding:
    field_name: str
    primary_value: str
    competing_source: str
    competing_value: str
    normalized_diff: float | None
    severity: ConflictSeverity
    manual_review_required: bool
    row_key: tuple[object, ...]


@dataclass(frozen=True)
class SourceConflictReport:
    conflict_report_id: str
    status: ConflictStatus
    can_write_primary_value: bool
    needs_reconcile: bool
    needs_manual_review: bool
    conflicts: tuple[SourceConflictFinding, ...]


@dataclass(frozen=True)
class _Threshold:
    relative_warning: float
    relative_severe: float


def _load_rules(
    rules_path: Path,
) -> tuple[dict[str, tuple[str, ...]], dict[str, dict[str, _Threshold]]]:
    if not rules_path.is_file():
        return {}, {}
    raw = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    comparable = raw.get("comparable_fields", {})
    field_groups = {
        str(group): tuple(str(field) for field in fields)
        for group, fields in comparable.items()
        if isinstance(fields, list)
    }
    thresholds: dict[str, dict[str, _Threshold]] = {}
    for domain, domain_rules in (raw.get("thresholds") or {}).items():
        if not isinstance(domain_rules, dict):
            continue
        thresholds[str(domain)] = {}
        for field, field_rules in domain_rules.items():
            if not isinstance(field_rules, dict):
                continue
            thresholds[str(domain)][str(field)] = _Threshold(
                relative_warning=float(field_rules["relative_warning"]),
                relative_severe=float(field_rules["relative_severe"]),
            )
    return field_groups, thresholds


def _key_for(row: dict[str, object], key_fields: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(row.get(field) for field in key_fields)


def _as_float(value: object) -> float | None:
    return as_float(value)


def _as_text(value: object) -> str:
    return as_text(value) or "None"


class SourceConflictValidator:
    """Compare primary-source rows against validation-source rows."""

    def __init__(self, rules_path: Path = _DEFAULT_RULES_PATH) -> None:
        self._field_groups, self._thresholds = _load_rules(rules_path)
        self._rule_set_id, self._rule_version = default_conflict_rule_contract()

    def _is_separate_by_source(self, field_name: str) -> bool:
        return field_name in set(self._field_groups.get("separate_by_source", ()))

    def _threshold_for(self, data_domain: str, field_name: str) -> _Threshold | None:
        return self._thresholds.get(data_domain, {}).get(field_name)

    def _normalized_diff(self, primary_value: object, competing_value: object) -> float | None:
        primary = _as_float(primary_value)
        competing = _as_float(competing_value)
        if primary is None or competing is None:
            return None
        denominator = abs(primary)
        if denominator == 0:
            return 0.0 if competing == 0 else None
        return abs(competing - primary) / denominator

    def _compare_field(
        self,
        request: SourceConflictRequest,
        primary_row: dict[str, object],
        peer_row: dict[str, object],
        field_name: str,
        *,
        row_key: tuple[object, ...],
    ) -> SourceConflictFinding | None:
        primary_value = primary_row.get(field_name)
        competing_value = peer_row.get(field_name)
        if primary_value == competing_value:
            return None

        competing_source = _as_text(peer_row.get("source_id"))
        if self._is_separate_by_source(field_name):
            return SourceConflictFinding(
                field_name=field_name,
                primary_value=_as_text(primary_value),
                competing_source=competing_source,
                competing_value=_as_text(competing_value),
                normalized_diff=None,
                severity=_METHODOLOGY,
                manual_review_required=False,
                row_key=row_key,
            )

        threshold = self._threshold_for(request.data_domain, field_name)
        diff = self._normalized_diff(primary_value, competing_value)
        if threshold is None or diff is None or diff <= threshold.relative_warning:
            return None
        severity: ConflictSeverity = _SEVERE if diff > threshold.relative_severe else _WARNING
        return SourceConflictFinding(
            field_name=field_name,
            primary_value=_as_text(primary_value),
            competing_source=competing_source,
            competing_value=_as_text(competing_value),
            normalized_diff=diff,
            severity=severity,
            manual_review_required=False,
            row_key=row_key,
        )

    def validate_rows(
        self,
        request: SourceConflictRequest,
        rows: list[dict[str, object]],
    ) -> SourceConflictReport:
        primary_rows = [row for row in rows if str(row.get("source_id")) == request.primary_source]
        peer_rows = [row for row in rows if str(row.get("source_id")) in request.validation_sources]
        peers_by_key: dict[tuple[object, ...], list[dict[str, object]]] = {}
        for row in peer_rows:
            peers_by_key.setdefault(_key_for(row, request.key_fields), []).append(row)

        conflicts: list[SourceConflictFinding] = []
        for primary_row in primary_rows:
            key = _key_for(primary_row, request.key_fields)
            for peer_row in peers_by_key.get(key, []):
                for field_name in request.comparable_fields:
                    finding = self._compare_field(
                        request,
                        primary_row,
                        peer_row,
                        field_name,
                        row_key=key,
                    )
                    if finding is not None:
                        conflicts.append(finding)

        has_severe = any(conflict.severity == _SEVERE for conflict in conflicts)
        has_warning = any(conflict.severity == _WARNING for conflict in conflicts)
        status: ConflictStatus = (
            "SEVERE_CONFLICT" if has_severe else "WARNING" if has_warning else "PASSED"
        )
        return SourceConflictReport(
            conflict_report_id=str(uuid.uuid4()),
            status=status,
            can_write_primary_value=not has_severe,
            needs_reconcile=has_severe,
            needs_manual_review=False,
            conflicts=tuple(conflicts),
        )

    def _fetch_rows(self, con, table_name: str) -> list[dict[str, object]]:
        return fetch_rows(con, table_name)

    def _market_id_for(self, row: dict[str, object]) -> str | None:
        value = row.get("market_id")
        return None if value is None else str(value)

    def _instrument_id_for(self, row: dict[str, object]) -> str | None:
        value = row.get("instrument_id")
        return None if value is None else str(value)

    def _as_of_timestamp_for(self, row: dict[str, object]) -> object | None:
        return row.get("as_of_timestamp") or row.get("trade_date")

    def _persist_report(
        self,
        con,
        request: SourceConflictRequest,
        report: SourceConflictReport,
        rows: list[dict[str, object]],
    ) -> None:
        primary_by_key = {
            _key_for(row, request.key_fields): row
            for row in rows
            if str(row.get("source_id")) == request.primary_source
        }
        created_at = datetime.now(UTC)
        for conflict in report.conflicts:
            if conflict.severity == _METHODOLOGY:
                continue
            conflict_id = str(uuid.uuid4())
            primary_row = primary_by_key.get(conflict.row_key, {})
            threshold = self._threshold_for(request.data_domain, conflict.field_name)
            manual_review_flag = False
            reconcile_status = "OPEN" if conflict.severity == _SEVERE else "N/A"
            con.execute(
                """
                INSERT INTO source_conflict (
                    conflict_id, run_id, job_id, data_domain, market_id,
                    instrument_id, field_name, as_of_timestamp, primary_source,
                    primary_value, competing_source, competing_value, normalized_diff,
                    tolerance_warning, tolerance_severe, tolerance_rule_set_id,
                    rule_version, severity, reconcile_status,
                    manual_review_required, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    conflict_id,
                    request.run_id,
                    request.job_id,
                    request.data_domain,
                    self._market_id_for(primary_row),
                    self._instrument_id_for(primary_row),
                    conflict.field_name,
                    self._as_of_timestamp_for(primary_row),
                    request.primary_source,
                    conflict.primary_value,
                    conflict.competing_source,
                    conflict.competing_value,
                    conflict.normalized_diff,
                    None if threshold is None else threshold.relative_warning,
                    None if threshold is None else threshold.relative_severe,
                    request.tolerance_rule_set_id,
                    self._rule_version,
                    conflict.severity,
                    reconcile_status,
                    manual_review_flag,
                    created_at,
                ],
            )

    def record_unresolved_reconcile(
        self,
        con,
        conflict_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
    ) -> None:
        """After ReconcileJob fails, enqueue manual review per resolution_policy."""
        row = con.execute(
            """
            SELECT field_name, primary_source, primary_value, competing_source, competing_value
            FROM source_conflict
            WHERE conflict_id = ?
            """,
            [conflict_id],
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown conflict_id: {conflict_id!r}")
        field_name, primary_source, primary_value, competing_source, competing_value = row
        created_at = datetime.now(UTC)
        con.execute(
            """
            UPDATE source_conflict
            SET reconcile_status = 'UNRESOLVED',
                manual_review_required = true
            WHERE conflict_id = ?
            """,
            [conflict_id],
        )
        con.execute(
            """
            INSERT INTO manual_review_queue (
                review_id, source_object_type, source_object_id, priority,
                title, description, suggested_action, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                str(uuid.uuid4()),
                "conflict",
                conflict_id,
                "HIGH",
                title or f"Severe source conflict on {field_name}",
                description
                or (f"{primary_source}={primary_value}; {competing_source}={competing_value}"),
                "manual review before any clean write or downstream manual_patch",
                "OPEN",
                created_at,
            ],
        )

    def validate_table(
        self,
        con,
        request: SourceConflictRequest,
        *,
        staging_table: str,
    ) -> SourceConflictReport:
        rows = self._fetch_rows(con, staging_table)
        report = self.validate_rows(request, rows)
        self._persist_report(con, request, report, rows)
        return report
