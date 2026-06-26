"""Read-only data health profiles (R3FR-02).

Attribution: OHLCV scan semantics adapted from EasyXT data_integrity_checker patterns
(see docs/architecture/10_external_references.md) — QMD-owned rule IDs only; no runtime
import from external reference repositories.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

import duckdb

from backend.app.config import PROJECT_ROOT
from backend.app.db.connection import ConnectionManager
from backend.app.ops.data_health import (
    DataHealthLoadError,
    DataHealthReport,
    _resolve_payload_path,
    require_evidence_bundle,
)
from backend.app.ops.data_health_profiles.report_builder import (
    MARKET_BAR_P0_RULE_IDS,
    build_market_bar_p0_checks,
    build_profile_report,
    issue_counts_by_severity,
    rules_run,
)
from backend.app.ops.staged_pilot import _equity_bar_rows

_SUPPORTED_PROFILES: frozenset[str] = frozenset({"market_bar_p0"})
_SUPPORTED_DOMAINS: frozenset[str] = frozenset({"market_bar_1d"})
_DEFAULT_MAX_ROWS = 1000
_MIN_HISTORY = 2
_SCHEMA_HASH_DB_ROW_LIMIT = 100
_RULES_PATH = PROJECT_ROOT / "specs" / "contracts" / "data_quality_rules.yaml"


class UnsupportedProfileError(ValueError):
    """Raised when profile_id or domain is not in supported closure."""


class DataHealthIngestLimitError(DataHealthLoadError):
    """Raised when evidence bar ingest exceeds max_rows hard cap."""


def _default_window_days() -> int:
    if not _RULES_PATH.is_file():
        return 90
    raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8")) or {}
    domain_cfg = (raw.get("ops_cli_profiles") or {}).get("market_bar_1d") or {}
    return int(domain_cfg.get("default_window_days") or 90)


def _schema_hash_coverage_from_db(db_path: Path) -> dict[str, list[str]]:
    """Read-only bounded fetch_log schema_hash scan (R3FR-07 repair A7-002/003)."""
    if not db_path.is_file():
        return {}
    coverage: dict[str, list[str]] = {}
    try:
        cm = ConnectionManager(db_path)
        with cm.reader() as con:
            tables = {
                str(row[0])
                for row in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'main'"
                ).fetchall()
            }
            if "fetch_log" not in tables:
                return {}
            rows = con.execute(
                """
                SELECT schema_hash, raw_file_paths
                FROM fetch_log
                WHERE schema_hash IS NOT NULL AND schema_hash != ''
                LIMIT ?
                """,
                [_SCHEMA_HASH_DB_ROW_LIMIT],
            ).fetchall()
        for schema_hash, raw_paths in rows:
            key = str(schema_hash)
            paths: list[str] = []
            if raw_paths:
                text = str(raw_paths).strip()
                if text.startswith("["):
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, list):
                            paths = [str(path) for path in parsed]
                    except json.JSONDecodeError:
                        paths = [text]
                else:
                    paths = [text]
            coverage.setdefault(key, []).extend(paths)
    except (OSError, duckdb.Error):
        return {}
    return coverage


def _profile_limitations(
    db_path: Path | None,
    *,
    db_opened: bool = False,
    has_schema_rows: bool = False,
) -> list[str]:
    limitations = [
        "read-only profile scan; no live fetch or production writes",
        "text CLI format is debug-oriented; use --format json for automation",
    ]
    if db_path is None:
        limitations.append(
            "db-path not set; evidence-only scan — use qmd ops db-inspect for metadata"
        )
    elif not db_path.is_file():
        limitations.append(
            "db-path provided but file missing; evidence-only scan performed"
        )
    elif db_opened and has_schema_rows:
        limitations.append(
            "db-path read-only schema_hash scan from fetch_log (bounded)"
        )
    elif db_opened:
        limitations.append(
            "db-path opened read-only; fetch_log has no schema_hash rows"
        )
    return limitations


def _content_hash_coverage(entries: list[dict[str, Any]]) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = {}
    for entry in entries:
        content_hash = entry.get("content_hash")
        if not content_hash:
            continue
        paths = entry.get("relative_paths") or []
        fetch_result = entry.get("fetch_result") or {}
        paths = paths or fetch_result.get("raw_file_paths") or []
        coverage[str(content_hash)] = [str(p) for p in paths]
    return coverage


def _apply_date_window(
    bars: list[dict[str, Any]],
    *,
    start_date: str | None,
    end_date: str | None,
    default_window_days: int,
) -> tuple[list[dict[str, Any]], dict[str, str | None]]:
    """Filter bars by explicit or default rolling window."""
    if start_date or end_date:
        filtered: list[dict[str, Any]] = []
        for row in bars:
            td = str(row.get("trade_date") or row.get("date") or "")
            if start_date and td < start_date:
                continue
            if end_date and td > end_date:
                continue
            filtered.append(row)
        return filtered, {"start": start_date or "", "end": end_date or ""}

    if not bars:
        return bars, {"start": "", "end": ""}

    dates: list[date] = []
    for row in bars:
        raw = row.get("trade_date") or row.get("date")
        if isinstance(raw, str) and raw.strip():
            try:
                dates.append(date.fromisoformat(raw[:10]))
            except ValueError:
                continue
    if not dates:
        return bars, {"start": "", "end": ""}

    window_end = max(dates)
    window_start = window_end - timedelta(days=default_window_days)
    start_s = window_start.isoformat()
    end_s = window_end.isoformat()
    filtered = [
        row
        for row in bars
        if start_s <= str(row.get("trade_date") or row.get("date") or "")[:10] <= end_s
    ]
    return filtered, {"start": start_s, "end": end_s}


def _bars_from_evidence(
    evidence_dir: Path,
    *,
    max_rows: int,
) -> tuple[list[dict[str, Any]], str | None, list[dict[str, Any]]]:
    bundle = require_evidence_bundle(evidence_dir)
    raw = bundle.raw_manifest or {}
    source_id = str(raw.get("source_id")) if raw.get("source_id") else None
    entries = [
        item
        for item in (raw.get("manifest_entries") or raw.get("fetches") or [])
        if isinstance(item, dict)
    ]
    bars: list[dict[str, Any]] = []
    for entry in entries:
        paths = entry.get("relative_paths") or []
        fetch_result = entry.get("fetch_result") or {}
        paths = paths or fetch_result.get("raw_file_paths") or []
        for rel in paths:
            resolved = _resolve_payload_path(str(rel), evidence_dir=evidence_dir)
            if resolved is None:
                continue
            try:
                payload = json.loads(resolved.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise DataHealthLoadError(
                    f"invalid bar payload {rel}: {exc}"
                ) from exc
            bars.extend(_equity_bar_rows(payload))
            if len(bars) > max_rows:
                raise DataHealthIngestLimitError(
                    f"bar ingest exceeds max_rows cap ({max_rows})"
                )
    return bars, source_id, entries


def run_data_health_profile(
    *,
    profile_id: str,
    domain: str,
    evidence_path: Path | None,
    db_path: Path | None,
    start_date: str | None,
    end_date: str | None,
    max_rows: int,
) -> tuple[
    DataHealthReport,
    list[str],
    dict[str, list[str]],
    dict[str, list[str]],
    dict[str, str | None],
]:
    """Single profile-runner boundary for market_bar_p0 (read-only)."""
    if profile_id not in _SUPPORTED_PROFILES:
        raise UnsupportedProfileError(f"unsupported profile: {profile_id!r}")
    if domain not in _SUPPORTED_DOMAINS:
        raise UnsupportedProfileError(f"unsupported domain: {domain!r}")
    if evidence_path is None:
        raise DataHealthLoadError("evidence_path required for market_bar_p0 in this slice")

    schema_coverage: dict[str, list[str]] = {}
    db_opened = False
    if db_path is not None and db_path.is_file():
        schema_coverage = _schema_hash_coverage_from_db(db_path)
        db_opened = True
    limitations = _profile_limitations(
        db_path,
        db_opened=db_opened,
        has_schema_rows=bool(schema_coverage),
    )
    cap = max_rows if max_rows > 0 else _DEFAULT_MAX_ROWS
    evidence_dir = Path(evidence_path)
    bars, source_id, entries = _bars_from_evidence(evidence_dir, max_rows=cap)
    bars, window = _apply_date_window(
        bars,
        start_date=start_date,
        end_date=end_date,
        default_window_days=_default_window_days(),
    )
    checks = build_market_bar_p0_checks(
        bars,
        domain="market_bar_1d",
        source_id=source_id,
        lineage_entries=entries,
        min_history=_MIN_HISTORY,
        max_rows=cap,
    )
    report = build_profile_report(checks, profile_id=profile_id)
    hash_coverage = _content_hash_coverage(entries)
    if not hash_coverage:
        limitations = [
            *limitations,
            "content_hash_coverage empty — manifest entries lack content_hash",
        ]
    return report, limitations, hash_coverage, schema_coverage, window


def cli_envelope_from_report(
    report: DataHealthReport,
    *,
    domain: str,
    profile: str,
    window: dict[str, str | None],
    source_ids: list[str],
    limitations: list[str],
    content_hash_coverage: dict[str, Any] | None = None,
    schema_hash_coverage: dict[str, Any] | None = None,
    report_path: str | None = None,
) -> dict[str, Any]:
    """Map DataHealthReport → R3FR-06 §5 JSON envelope."""
    row_count = max((c.row_count or 0 for c in report.checks), default=0)
    return {
        "command": "health",
        "dry_run": True,
        "side_effects_allowed": False,
        "domain": domain,
        "profile": profile,
        "status": report.overall_status,
        "rules_run": rules_run(report.checks),
        "issue_counts_by_severity": issue_counts_by_severity(report.checks),
        "row_count_checked": row_count,
        "window": window,
        "source_ids": source_ids,
        "limitations": limitations,
        "content_hash_coverage": content_hash_coverage or {},
        "schema_hash_coverage": schema_hash_coverage or {},
        **({"report_path": report_path} if report_path else {}),
    }


__all__ = [
    "DataHealthIngestLimitError",
    "MARKET_BAR_P0_RULE_IDS",
    "UnsupportedProfileError",
    "cli_envelope_from_report",
    "run_data_health_profile",
]
