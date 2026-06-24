"""Pilot-local FRED evidence health validator (B01-FRED; not data_health.py)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

_NUMERIC_RE = re.compile(r"^-?\d+(\.\d+)?$")


def validate_fred_evidence_health(
    manifest: dict[str, Any],
    *,
    stale_after_days: int = 90,
) -> dict[str, Any]:
    """Check FRED pilot manifest rows for stale/missing/malformed/missing hash."""
    issues: list[dict[str, str]] = []
    series_entries = manifest.get("series") or []
    if not series_entries:
        issues.append({"code": "MISSING_SERIES", "severity": "FAIL", "detail": "no series entries"})

    for entry in series_entries:
        series_id = entry.get("series_id") or "?"
        if not entry.get("source_fetch_id"):
            issues.append(
                {
                    "code": "MISSING_FETCH_ID",
                    "severity": "FAIL",
                    "detail": f"{series_id}: missing source_fetch_id",
                }
            )
        if not entry.get("content_hash"):
            issues.append(
                {
                    "code": "MISSING_HASH",
                    "severity": "FAIL",
                    "detail": f"{series_id}: missing content_hash",
                }
            )
        rows = entry.get("rows") or []
        if not rows:
            issues.append(
                {
                    "code": "MISSING_ROWS",
                    "severity": "FAIL",
                    "detail": f"{series_id}: no observation rows",
                }
            )
            continue
        for row in rows:
            obs_date = row.get("observation_date")
            value = row.get("value")
            if not obs_date:
                issues.append(
                    {
                        "code": "MALFORMED_ROW",
                        "severity": "FAIL",
                        "detail": f"{series_id}: missing observation_date",
                    }
                )
            if value is None or not _NUMERIC_RE.match(str(value)):
                issues.append(
                    {
                        "code": "MALFORMED_VALUE",
                        "severity": "FAIL",
                        "detail": f"{series_id}: non-numeric value {value!r}",
                    }
                )
        latest = rows[0].get("observation_date") if rows else None
        if latest:
            try:
                obs = datetime.fromisoformat(str(latest)).date()
                age = (datetime.now(UTC).date() - obs).days
                if age > stale_after_days:
                    issues.append(
                        {
                            "code": "STALE_OBSERVATION",
                            "severity": "WARN",
                            "detail": f"{series_id}: latest observation {age}d old",
                        }
                    )
            except ValueError:
                issues.append(
                    {
                        "code": "MALFORMED_DATE",
                        "severity": "FAIL",
                        "detail": f"{series_id}: bad observation_date {latest!r}",
                    }
                )

    fail_count = sum(1 for i in issues if i["severity"] == "FAIL")
    warn_count = sum(1 for i in issues if i["severity"] == "WARN")
    status = "PASS"
    if fail_count:
        status = "FAIL"
    elif warn_count:
        status = "WARN"

    return {
        "status": status,
        "issue_count": len(issues),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "issues": issues,
    }
