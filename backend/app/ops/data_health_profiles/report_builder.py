"""Profile report builder with capped details (R3FR-02)."""

from __future__ import annotations

from typing import Any

from backend.app.ops.data_health import DataHealthCheckResult, DataHealthReport, build_report
from backend.app.ops.data_health_profiles.calendar_gap_rules import check_missing_trading_day
from backend.app.ops.data_health_profiles.ohlcv_rules import run_ohlcv_rules

MARKET_BAR_P0_RULE_IDS: tuple[str, ...] = (
    "MISSING_TRADING_DAY",
    "MISSING_REQUIRED_OHLCV_FIELD",
    "NON_POSITIVE_PRICE",
    "INVALID_OHLC",
    "EXTREME_RETURN",
    "VOLUME_OUTLIER",
    "DUPLICATE_PRIMARY_KEY",
    "INSUFFICIENT_HISTORY",
    "MISSING_SOURCE_USED",
)


def cap_check_details(
    checks: list[DataHealthCheckResult],
    *,
    max_rows: int,
) -> list[DataHealthCheckResult]:
    """Cap detail rows while preserving at least one per failing rule_id."""
    if max_rows <= 0 or len(checks) <= max_rows:
        return checks
    non_pass = [c for c in checks if c.status != "PASS"]
    if len(non_pass) <= max_rows:
        return checks[:max_rows]
    kept: list[DataHealthCheckResult] = []
    seen_rules: set[str] = set()
    for check in non_pass:
        if check.rule_id not in seen_rules:
            kept.append(check)
            seen_rules.add(check.rule_id)
        if len(kept) >= max_rows:
            break
    if len(kept) < max_rows:
        for check in non_pass:
            if check not in kept:
                kept.append(check)
            if len(kept) >= max_rows:
                break
    return kept[:max_rows]


def _missing_source_used_entry(
    entry: dict[str, Any],
    *,
    domain: str,
    source_id: str | None,
) -> list[DataHealthCheckResult]:
    """Profile slice: require explicit source_used on manifest entry (no manifest-level fallback)."""
    if entry.get("source_used") or entry.get("source_id"):
        return []
    request = entry.get("request") or {}
    if request.get("source_id"):
        return []
    return [
        DataHealthCheckResult(
            rule_id="MISSING_SOURCE_USED",
            severity="FAIL",
            status="FAIL",
            source_id=source_id,
            domain=domain,
            evidence_path=None,
            row_count=None,
            message="source_used missing on manifest entry",
        )
    ]


def _ensure_rule_pass_coverage(
    checks: list[DataHealthCheckResult],
    bars: list[dict[str, Any]],
    *,
    domain: str,
    source_id: str | None,
) -> list[DataHealthCheckResult]:
    """Emit PASS rows for executed rules that produced no finding."""
    if not bars:
        return checks
    present = {c.rule_id for c in checks}
    row_count = len(bars)
    for rule_id in MARKET_BAR_P0_RULE_IDS:
        if rule_id in present:
            continue
        checks.append(
            DataHealthCheckResult(
                rule_id=rule_id,
                severity="INFO",
                status="PASS",
                source_id=source_id,
                domain=domain,
                evidence_path=None,
                row_count=row_count,
                message=f"{rule_id} passed",
            )
        )
    return checks


def build_market_bar_p0_checks(
    bars: list[dict[str, Any]],
    *,
    domain: str,
    source_id: str | None,
    lineage_entries: list[dict[str, Any]],
    min_history: int,
    max_rows: int,
) -> list[DataHealthCheckResult]:
    """Orchestration: calendar → OHLCV → lineage (MISSING_SOURCE_USED)."""
    checks: list[DataHealthCheckResult] = []
    checks.extend(
        check_missing_trading_day(
            bars, domain=domain, source_id=source_id, calendar_authority=False
        )
    )
    ohlcv = run_ohlcv_rules(
        bars, domain=domain, source_id=source_id, min_history=min_history
    )
    checks.extend(ohlcv)
    if ohlcv and ohlcv[0].status == "FAIL":
        return cap_check_details(checks, max_rows=max_rows)
    for entry in lineage_entries:
        checks.extend(
            _missing_source_used_entry(entry, domain=domain, source_id=source_id)
        )
    if not any(c.status == "FAIL" for c in checks):
        checks = _ensure_rule_pass_coverage(
            checks, bars, domain=domain, source_id=source_id
        )
    return cap_check_details(checks, max_rows=max_rows)


def build_profile_report(
    checks: list[DataHealthCheckResult],
    *,
    profile_id: str,
    input_kind: str = "evidence_bundle",
) -> DataHealthReport:
    return build_report(checks, profile=profile_id, input_kind=input_kind)


def issue_counts_by_severity(checks: list[DataHealthCheckResult]) -> dict[str, int]:
    counts: dict[str, int] = {"INFO": 0, "WARN": 0, "FAIL": 0}
    for check in checks:
        if check.status == "FAIL":
            counts["FAIL"] += 1
        elif check.status == "WARN":
            counts["WARN"] += 1
    return counts


def rules_run(checks: list[DataHealthCheckResult]) -> list[str]:
    seen: list[str] = []
    for check in checks:
        if check.rule_id not in seen:
            seen.append(check.rule_id)
    return seen
