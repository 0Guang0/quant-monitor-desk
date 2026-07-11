"""crypto_derivative_p0 profile checks (data health S-R2-F0)."""

from __future__ import annotations

from typing import Any

from backend.app.datasources.normalizers.crypto_market import CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION
from backend.app.ops.data_health import DataHealthCheckResult

CRYPTO_DERIVATIVE_P0_RULE_IDS: tuple[str, ...] = (
    "MISSING_PRIMARY_KEY",
    "MISSING_REQUIRED_FIELD",
    "MISSING_TIMESTAMP",
    "MISSING_SOURCE_USED",
    "INVALID_ENUM",
    "SCHEMA_DRIFT",
)

_VALID_OPTION_TYPES = frozenset({"call", "put", "CALL", "PUT"})


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


def build_crypto_derivative_p0_checks(
    payload: dict[str, Any],
    *,
    domain: str = "crypto_derivative",
) -> list[DataHealthCheckResult]:
    source_id = str(payload.get("source_id") or "")
    checks: list[DataHealthCheckResult] = []
    schema = str(payload.get("schema_version") or "")
    if schema != CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION:
        checks.append(
            _fail(
                "SCHEMA_DRIFT",
                domain=domain,
                message=f"expected {CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION}, got {schema!r}",
                source_id=source_id or None,
            )
        )
        return checks

    instruments = [
        row for row in (payload.get("instruments") or []) if isinstance(row, dict)
    ]
    if not instruments:
        checks.append(
            _fail(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="no instruments in bundle",
                source_id=source_id or None,
            )
        )
        return checks

    if not payload.get("as_of_timestamp") and not payload.get("retrieved_at"):
        checks.append(
            _fail(
                "MISSING_TIMESTAMP",
                domain=domain,
                message="bundle missing as_of_timestamp",
                source_id=source_id or None,
            )
        )
        return checks

    for inst in instruments:
        if not inst.get("instrument_name"):
            checks.append(
                _fail(
                    "MISSING_PRIMARY_KEY",
                    domain=domain,
                    message="instrument_name missing",
                    source_id=source_id or None,
                )
            )
            return checks
        option_type = inst.get("option_type")
        if option_type is not None and str(option_type) not in _VALID_OPTION_TYPES:
            checks.append(
                _fail(
                    "INVALID_ENUM",
                    domain=domain,
                    message=f"invalid option_type {option_type!r}",
                    source_id=source_id or None,
                )
            )
            return checks
        if not inst.get("source_used") and not source_id:
            checks.append(
                _fail(
                    "MISSING_SOURCE_USED",
                    domain=domain,
                    message="instrument missing source_used",
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

    row_count = len(instruments)
    for rule_id in CRYPTO_DERIVATIVE_P0_RULE_IDS:
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
