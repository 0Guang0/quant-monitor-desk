"""disclosure_p0 profile checks (data health S-R2-F0)."""

from __future__ import annotations

from typing import Any

from backend.app.datasources.normalizers.cn_market import CN_MARKET_EVIDENCE_SCHEMA_VERSION
from backend.app.datasources.normalizers.sec_edgar import SEC_EDGAR_EVIDENCE_SCHEMA_VERSION
from backend.app.ops.data_health import DataHealthCheckResult

DISCLOSURE_P0_RULE_IDS: tuple[str, ...] = (
    "MISSING_PRIMARY_KEY",
    "MISSING_REQUIRED_FIELD",
    "MISSING_TIMESTAMP",
    "MISSING_SOURCE_USED",
    "SCHEMA_DRIFT",
)


def _fail(
    rule_id: str, *, domain: str, message: str, source_id: str | None
) -> DataHealthCheckResult:
    return DataHealthCheckResult(
        rule_id=rule_id,
        severity="FAIL",
        status="FAIL",
        source_id=source_id,
        domain=domain,
        evidence_path=None,
        row_count=None,
        message=message,
    )


def _pass_rule(
    rule_id: str, *, domain: str, message: str, source_id: str | None, row_count: int
) -> DataHealthCheckResult:
    return DataHealthCheckResult(
        rule_id=rule_id,
        severity="INFO",
        status="PASS",
        source_id=source_id,
        domain=domain,
        evidence_path=None,
        row_count=row_count,
        message=message,
    )


def _disclosure_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("filings", "rows", "announcements"):
        rows = payload.get(key)
        if isinstance(rows, list) and rows:
            return [r for r in rows if isinstance(r, dict)]
    return []


def _expected_schema(domain: str) -> str:
    return (
        CN_MARKET_EVIDENCE_SCHEMA_VERSION
        if domain == "cn_disclosure"
        else SEC_EDGAR_EVIDENCE_SCHEMA_VERSION
    )


def build_disclosure_p0_checks(
    payload: dict[str, Any],
    *,
    domain: str,
) -> list[DataHealthCheckResult]:
    source_id = str(payload.get("source_id") or "")
    checks: list[DataHealthCheckResult] = []
    schema = str(payload.get("schema_version") or "")
    expected = _expected_schema(domain)
    if schema != expected:
        checks.append(
            _fail(
                "SCHEMA_DRIFT",
                domain=domain,
                message=f"expected schema {expected}, got {schema!r}",
                source_id=source_id or None,
            )
        )
        return checks

    rows = _disclosure_rows(payload)
    if not rows:
        checks.append(
            _fail(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="no disclosure rows",
                source_id=source_id or None,
            )
        )
        return checks

    pk_field = "filing_id" if domain == "cn_disclosure" else "accession_number"
    ts_fields = (
        ("publish_timestamp", "observation_date")
        if domain == "cn_disclosure"
        else ("filing_date", "report_date")
    )

    for row in rows:
        if not row.get(pk_field):
            checks.append(
                _fail(
                    "MISSING_PRIMARY_KEY",
                    domain=domain,
                    message=f"missing {pk_field}",
                    source_id=source_id or None,
                )
            )
            return checks
        if domain == "cn_disclosure" and not str(row.get("title") or "").strip():
            checks.append(
                _fail(
                    "MISSING_REQUIRED_FIELD",
                    domain=domain,
                    message="cn disclosure title missing",
                    source_id=source_id or None,
                )
            )
            return checks
        if domain == "us_disclosure" and not row.get("form_type"):
            checks.append(
                _fail(
                    "MISSING_REQUIRED_FIELD",
                    domain=domain,
                    message="us filing form_type missing",
                    source_id=source_id or None,
                )
            )
            return checks
        if not any(row.get(f) for f in ts_fields):
            checks.append(
                _fail(
                    "MISSING_TIMESTAMP",
                    domain=domain,
                    message="disclosure timestamp missing",
                    source_id=source_id or None,
                )
            )
            return checks
        if not row.get("source_used") and not source_id:
            checks.append(
                _fail(
                    "MISSING_SOURCE_USED",
                    domain=domain,
                    message="disclosure row missing source_used",
                    source_id=None,
                )
            )
            return checks

    if not payload.get("source_fetch_id") or not payload.get("content_hash"):
        checks.append(
            _fail(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="bundle missing source_fetch_id or content_hash",
                source_id=source_id or None,
            )
        )
        return checks

    row_count = len(rows)
    for rule_id in DISCLOSURE_P0_RULE_IDS:
        checks.append(
            _pass_rule(
                rule_id,
                domain=domain,
                message=f"{rule_id} passed",
                source_id=source_id or None,
                row_count=row_count,
            )
        )
    return checks
