"""layer1_observation_p0 profile checks (data health S-R2-F0)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.ops.data_health import DataHealthCheckResult

LAYER1_OBSERVATION_P0_RULE_IDS: tuple[str, ...] = (
    "MISSING_SOURCE_USED",
    "FALLBACK_WITHOUT_REASON",
    "BLINDSPOT_SHOULD_NOT_HAVE_VALUE",
    "MISSING_REQUIRED_FIELD",
    "STALE_DATA",
)

_STALE_DAYS = 30


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


def _observation_has_value(obs: dict[str, Any]) -> bool:
    for key in ("value", "yield_percent", "metric_value", "raw_value", "policy_rate"):
        val = obs.get(key)
        if val is not None and str(val).strip() not in {"", "."}:
            return True
    long_c = obs.get("long_contracts")
    short_c = obs.get("short_contracts")
    if long_c not in (None, "", ".") and short_c not in (None, "", "."):
        return True
    return False


def _observation_date(obs: dict[str, Any]) -> str:
    for key in ("observation_date", "report_date", "date"):
        raw = obs.get(key)
        if raw is not None and str(raw).strip():
            return str(raw)[:10]
    return ""


def _warn(
    rule_id: str, *, domain: str, message: str, source_id: str | None
) -> DataHealthCheckResult:
    return DataHealthCheckResult(
        rule_id=rule_id,
        severity="WARN",
        status="WARN",
        source_id=source_id,
        domain=domain,
        evidence_path=None,
        row_count=None,
        message=message,
    )


def build_layer1_observation_p0_checks(
    bundle: dict[str, Any],
    *,
    domain: str = "layer1_observation",
) -> list[DataHealthCheckResult]:
    source_id = str(bundle.get("source_id") or "")
    checks: list[DataHealthCheckResult] = []

    if not source_id:
        checks.append(
            _fail(
                "MISSING_SOURCE_USED",
                domain=domain,
                message="bundle source_id missing",
                source_id=None,
            )
        )
        return checks

    if not bundle.get("source_fetch_id") or not bundle.get("content_hash"):
        checks.append(
            _fail(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="missing source_fetch_id or content_hash",
                source_id=source_id,
            )
        )

    observations = bundle.get("observations") or []
    if not observations:
        checks.append(
            _fail(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="no observations in bundle",
                source_id=source_id,
            )
        )
        return checks

    for obs in observations:
        if not isinstance(obs, dict):
            continue
        if not _observation_date(obs) or not _observation_has_value(obs):
            checks.append(
                _fail(
                    "MISSING_REQUIRED_FIELD",
                    domain=domain,
                    message="observation missing observation_date or value",
                    source_id=source_id,
                )
            )
            break
        if not obs.get("source_used") and not source_id:
            checks.append(
                _fail(
                    "MISSING_SOURCE_USED",
                    domain=domain,
                    message="observation missing source_used",
                    source_id=source_id,
                )
            )
            break

    as_of = bundle.get("as_of_timestamp") or bundle.get("retrieved_at")
    if as_of:
        try:
            parsed = datetime.fromisoformat(str(as_of).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            if datetime.now(UTC) - parsed > timedelta(days=_STALE_DAYS):
                checks.append(
                    _warn(
                        "STALE_DATA",
                        domain=domain,
                        message=f"as_of older than {_STALE_DAYS} days",
                        source_id=source_id,
                    )
                )
        except ValueError:
            checks.append(
                _fail(
                    "MISSING_REQUIRED_FIELD",
                    domain=domain,
                    message="invalid as_of_timestamp",
                    source_id=source_id,
                )
            )

    if bundle.get("fallback_used") and not bundle.get("fallback_reason"):
        checks.append(
            _fail(
                "FALLBACK_WITHOUT_REASON",
                domain=domain,
                message="fallback without documented reason",
                source_id=source_id,
            )
        )

    if not checks:
        row_count = len(observations)
        for rule_id in LAYER1_OBSERVATION_P0_RULE_IDS:
            if rule_id in {"FALLBACK_WITHOUT_REASON", "BLINDSPOT_SHOULD_NOT_HAVE_VALUE"}:
                checks.append(
                    _pass_rule(
                        rule_id,
                        domain=domain,
                        message=f"{rule_id} not applicable",
                        source_id=source_id,
                        row_count=row_count,
                    )
                )
            else:
                checks.append(
                    _pass_rule(
                        rule_id,
                        domain=domain,
                        message=f"{rule_id} passed",
                        source_id=source_id,
                        row_count=row_count,
                    )
                )
    return checks
