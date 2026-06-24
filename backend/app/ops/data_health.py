"""Read-only staged evidence data health checks (Round 3 C-20)."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.source_registry import SourceNotFoundError, SourceRegistry
from backend.app.ops.staged_pilot import _equity_bar_rows, _resolve_evidence_path

Severity = Literal["INFO", "WARN", "FAIL"]
CheckStatus = Literal["PASS", "WARN", "FAIL", "NOT_APPLICABLE", "BLOCKED"]
OverallStatus = Literal["PASS", "WARN", "FAIL", "BLOCKED"]

VALID_SEVERITIES: frozenset[str] = frozenset({"INFO", "WARN", "FAIL"})
VALID_CHECK_STATUSES: frozenset[str] = frozenset(
    {"PASS", "WARN", "FAIL", "NOT_APPLICABLE", "BLOCKED"}
)

MODEL_INPUTS_DIR = PROJECT_ROOT / "specs" / "model_inputs"
V2_PROFILES: frozenset[str] = frozenset(
    {
        "model_input_whitelist",
        "fred_sandbox_pilot",
        "tdx_manual_probe",
        "staged_pilot_v3",
        "source_readiness_rollup",
    }
)
# ponytail: v3 pilot default caps when manifest omits explicit resource_caps
_V3_DEFAULT_CAPS: dict[str, int] = {
    "baostock_max_rows": 2000,
    "cninfo_max_rows": 500,
    "akshare_max_rows": 1000,
}

_RAW_MANIFEST_CANDIDATES: tuple[str, ...] = (
    "raw_evidence_manifest_v2.json",
    "raw_evidence_manifest.json",
)
_STAGING_MANIFEST_CANDIDATES: tuple[str, ...] = (
    "staging_evidence_manifest_v2.json",
    "staging_evidence_manifest.json",
)
_VALIDATION_CANDIDATES: tuple[str, ...] = (
    "validation_report_v2.json",
    "validation_report_summary.json",
)

# ponytail: minimal history floor for INSUFFICIENT_HISTORY in evidence-path mode
_MIN_DAILY_BAR_HISTORY = 2
# ponytail: stale if as_of older than this many days (tests use fixed old dates)
_STALE_DATA_DAYS = 30


@dataclass(frozen=True)
class DataHealthCheckResult:
    rule_id: str
    severity: Severity
    status: CheckStatus
    source_id: str | None
    domain: str
    evidence_path: str | None
    row_count: int | None
    message: str


@dataclass
class DataHealthReport:
    report_id: str
    generated_at: str
    input_kind: str
    profile: str
    overall_status: OverallStatus
    checks: list[DataHealthCheckResult] = field(default_factory=list)
    production_db_mutated: bool = False
    source_fetch_performed: bool = False
    sandbox_clean_write_gate_ready: bool = False
    gate_rationale: str = ""
    text_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [check_result_to_dict(c) for c in self.checks]
        return payload


@dataclass(frozen=True)
class EvidenceBundle:
    evidence_dir: Path
    raw_manifest: dict[str, Any] | None
    staging_manifest: dict[str, Any] | None
    validation_report: dict[str, Any] | None
    load_error: str | None = None


class DataHealthLoadError(Exception):
    """Raised when required evidence manifests are missing."""


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _loaded_source_registry() -> SourceRegistry:
    reg = SourceRegistry()
    if not reg.is_loaded():
        reg.load()
    return reg


def _fail_check(
    rule_id: str,
    *,
    domain: str,
    message: str,
    source_id: str | None = None,
    evidence_path: str | None = None,
    row_count: int | None = None,
    severity: Severity = "FAIL",
) -> DataHealthCheckResult:
    return DataHealthCheckResult(
        rule_id=rule_id,
        severity=severity,
        status="FAIL",
        source_id=source_id,
        domain=domain,
        evidence_path=evidence_path,
        row_count=row_count,
        message=message,
    )


def _pass_check(
    rule_id: str,
    *,
    domain: str,
    message: str,
    source_id: str | None = None,
) -> DataHealthCheckResult:
    return DataHealthCheckResult(
        rule_id=rule_id,
        severity="INFO",
        status="PASS",
        source_id=source_id,
        domain=domain,
        evidence_path=None,
        row_count=None,
        message=message,
    )


def _warn_check(
    rule_id: str,
    *,
    domain: str,
    message: str,
    source_id: str | None = None,
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


def _blocked_check(
    rule_id: str,
    *,
    domain: str,
    message: str,
    source_id: str | None = None,
) -> DataHealthCheckResult:
    return DataHealthCheckResult(
        rule_id=rule_id,
        severity="WARN",
        status="BLOCKED",
        source_id=source_id,
        domain=domain,
        evidence_path=None,
        row_count=None,
        message=message,
    )


def check_result_to_dict(result: DataHealthCheckResult) -> dict[str, Any]:
    if result.severity not in VALID_SEVERITIES:
        msg = f"invalid severity: {result.severity}"
        raise ValueError(msg)
    if result.status not in VALID_CHECK_STATUSES:
        msg = f"invalid status: {result.status}"
        raise ValueError(msg)
    return asdict(result)


def check_result_from_dict(payload: dict[str, Any]) -> DataHealthCheckResult:
    severity = str(payload["severity"])
    status = str(payload["status"])
    if severity not in VALID_SEVERITIES:
        msg = f"invalid severity: {severity}"
        raise ValueError(msg)
    if status not in VALID_CHECK_STATUSES:
        msg = f"invalid status: {status}"
        raise ValueError(msg)
    return DataHealthCheckResult(
        rule_id=str(payload["rule_id"]),
        severity=severity,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        source_id=payload.get("source_id"),
        domain=str(payload["domain"]),
        evidence_path=payload.get("evidence_path"),
        row_count=payload.get("row_count"),
        message=str(payload["message"]),
    )


def _find_first(evidence_dir: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = evidence_dir / name
        if candidate.is_file():
            return candidate
    return None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_dir_within_project(evidence_dir: Path) -> bool:
    """Return True when evidence_dir resolves under PROJECT_ROOT (R3Y-DH-02)."""
    try:
        return evidence_dir.resolve().is_relative_to(PROJECT_ROOT.resolve())
    except (OSError, ValueError):
        return False


def _resolve_payload_path(raw_path: str, *, evidence_dir: Path) -> Path | None:
    """Evidence-local path first, then staged_pilot project-relative resolver."""
    local = (evidence_dir / raw_path).resolve()
    resolved = local if local.is_file() else _resolve_evidence_path(raw_path)
    if not resolved.is_file():
        return None
    try:
        if not resolved.is_relative_to(PROJECT_ROOT.resolve()):
            return None
    except (OSError, ValueError):
        return None
    return resolved


def load_evidence_bundle(evidence_dir: Path) -> EvidenceBundle:
    """Load staged pilot evidence manifests read-only."""
    if not evidence_dir.is_dir():
        return EvidenceBundle(
            evidence_dir=evidence_dir,
            raw_manifest=None,
            staging_manifest=None,
            validation_report=None,
            load_error=f"evidence directory not found: {evidence_dir}",
        )

    raw_path = _find_first(evidence_dir, _RAW_MANIFEST_CANDIDATES)
    if raw_path is None:
        return EvidenceBundle(
            evidence_dir=evidence_dir,
            raw_manifest=None,
            staging_manifest=None,
            validation_report=None,
            load_error="missing raw evidence manifest",
        )

    try:
        raw_manifest = _read_json(raw_path)
    except (OSError, json.JSONDecodeError) as exc:
        return EvidenceBundle(
            evidence_dir=evidence_dir,
            raw_manifest=None,
            staging_manifest=None,
            validation_report=None,
            load_error=f"invalid raw evidence manifest: {exc}",
        )

    staging_path = _find_first(evidence_dir, _STAGING_MANIFEST_CANDIDATES)
    staging_manifest: dict[str, Any] | None = None
    if staging_path is not None:
        try:
            staging_manifest = _read_json(staging_path)
        except (OSError, json.JSONDecodeError) as exc:
            return EvidenceBundle(
                evidence_dir=evidence_dir,
                raw_manifest=raw_manifest,
                staging_manifest=None,
                validation_report=None,
                load_error=f"invalid staging evidence manifest: {exc}",
            )

    validation_path = _find_first(evidence_dir, _VALIDATION_CANDIDATES)
    validation_report: dict[str, Any] | None = None
    if validation_path is not None:
        try:
            validation_report = _read_json(validation_path)
        except (OSError, json.JSONDecodeError) as exc:
            return EvidenceBundle(
                evidence_dir=evidence_dir,
                raw_manifest=raw_manifest,
                staging_manifest=staging_manifest,
                validation_report=None,
                load_error=f"invalid validation report: {exc}",
            )
    return EvidenceBundle(
        evidence_dir=evidence_dir,
        raw_manifest=raw_manifest,
        staging_manifest=staging_manifest,
        validation_report=validation_report,
        load_error=None,
    )


def require_evidence_bundle(evidence_dir: Path) -> EvidenceBundle:
    bundle = load_evidence_bundle(evidence_dir)
    if bundle.load_error:
        raise DataHealthLoadError(bundle.load_error)
    return bundle


def check_daily_bars(
    bars: list[dict[str, Any]],
    *,
    domain: str = "cn_equity_daily_bar",
    source_id: str | None = "baostock",
    min_history: int = _MIN_DAILY_BAR_HISTORY,
) -> list[DataHealthCheckResult]:
    checks: list[DataHealthCheckResult] = []
    if not bars:
        checks.append(
            _fail_check(
                "EMPTY_RESPONSE",
                domain=domain,
                message="no daily bar rows",
                source_id=source_id,
                row_count=0,
            )
        )
        return checks

    if len(bars) < min_history:
        checks.append(
            _fail_check(
                "INSUFFICIENT_HISTORY",
                domain=domain,
                message=f"expected at least {min_history} bars, got {len(bars)}",
                source_id=source_id,
                row_count=len(bars),
            )
        )

    seen_keys: set[str] = set()
    for row in bars:
        symbol = row.get("symbol") or row.get("code")
        trade_date = row.get("trade_date") or row.get("date")
        row_key = f"{symbol}|{trade_date}"
        if row_key in seen_keys:
            checks.append(
                _fail_check(
                    "DUPLICATE_PRIMARY_KEY",
                    domain=domain,
                    message=f"duplicate bar key {row_key}",
                    source_id=source_id,
                    row_count=len(bars),
                )
            )
            break
        seen_keys.add(row_key)

        open_px = row.get("open")
        high = row.get("high")
        low = row.get("low")
        close = row.get("close")
        if None not in (open_px, high, low, close):
            try:
                o, h, lo, c = float(open_px), float(high), float(low), float(close)
            except (TypeError, ValueError):
                o = h = lo = c = -1.0
            if h < max(o, c, lo) or lo > min(o, c, h) or h < lo:
                checks.append(
                    _fail_check(
                        "INVALID_OHLC",
                        domain=domain,
                        message=f"invalid OHLC for {row_key}",
                        source_id=source_id,
                        row_count=len(bars),
                    )
                )
                break

        volume = row.get("volume")
        if volume is not None:
            try:
                if float(volume) < 0:
                    checks.append(
                        _fail_check(
                            "NEGATIVE_VOLUME",
                            domain=domain,
                            message=f"negative volume for {row_key}",
                            source_id=source_id,
                            row_count=len(bars),
                        )
                    )
                    break
            except (TypeError, ValueError):
                pass

    if not checks:
        checks.append(
            _pass_check(
                "INVALID_OHLC",
                domain=domain,
                message="daily bar OHLC/volume/history checks passed",
                source_id=source_id,
            )
        )
    return checks


def check_metadata_rows(
    rows: list[dict[str, Any]],
    *,
    domain: str = "cn_announcements",
    source_id: str | None = "cninfo",
) -> list[DataHealthCheckResult]:
    checks: list[DataHealthCheckResult] = []
    for row in rows:
        title = row.get("title")
        if title is None or (isinstance(title, str) and not title.strip()):
            checks.append(
                _fail_check(
                    "MISSING_REQUIRED_FIELD",
                    domain=domain,
                    message="metadata title is empty or missing",
                    source_id=source_id,
                    row_count=len(rows),
                )
            )
            return checks
    if not checks:
        checks.append(
            _pass_check(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="metadata required fields present",
                source_id=source_id,
            )
        )
    return checks


def check_lineage_entry(
    entry: dict[str, Any],
    *,
    domain: str,
    primary_source_id: str | None = None,
    default_as_of: str | None = None,
    registry: SourceRegistry | None = None,
) -> list[DataHealthCheckResult]:
    checks: list[DataHealthCheckResult] = []
    request = entry.get("request") or {}
    source_used = (
        entry.get("source_used")
        or entry.get("source_id")
        or request.get("source_id")
        or primary_source_id
    )
    source_id = primary_source_id or entry.get("source_id") or source_used
    if not source_used:
        checks.append(
            _fail_check(
                "MISSING_SOURCE_USED",
                domain=domain,
                message="source_used missing",
                source_id=str(source_id) if source_id else None,
            )
        )
    fetch_id = entry.get("source_fetch_id") or entry.get("fetch_id")
    if not fetch_id:
        fetch_result = entry.get("fetch_result") or {}
        fetch_id = fetch_result.get("run_id")
    if not fetch_id:
        checks.append(
            _fail_check(
                "MISSING_SOURCE_FETCH_ID",
                domain=domain,
                message="source_fetch_id missing",
                source_id=str(source_id) if source_id else None,
            )
        )
    content_hash = entry.get("content_hash")
    if not content_hash:
        fetch_result = entry.get("fetch_result") or {}
        content_hash = fetch_result.get("content_hash")
    if not content_hash:
        checks.append(
            _fail_check(
                "MISSING_CONTENT_HASH",
                domain=domain,
                message="content_hash missing",
                source_id=str(source_id) if source_id else None,
            )
        )
    as_of = entry.get("as_of_timestamp") or entry.get("generated_at") or default_as_of
    if not as_of:
        checks.append(
            _fail_check(
                "MISSING_AS_OF_TIMESTAMP",
                domain=domain,
                message="as_of_timestamp missing",
                source_id=str(source_id) if source_id else None,
            )
        )

    reg = registry or _loaded_source_registry()
    registry_ids: list[str] = []
    for candidate in (str(source_used or ""), str(primary_source_id or "")):
        if candidate and candidate not in registry_ids:
            registry_ids.append(candidate)
    for resolved_source in registry_ids:
        try:
            rec = reg.get(resolved_source)
        except SourceNotFoundError:
            checks.append(
                _fail_check(
                    "DISABLED_SOURCE_USED",
                    domain=domain,
                    message=f"source {resolved_source} not found in registry",
                    source_id=resolved_source,
                )
            )
            continue
        if not rec.is_enabled:
            checks.append(
                _fail_check(
                    "DISABLED_SOURCE_USED",
                    domain=domain,
                    message=f"source {resolved_source} disabled by default",
                    source_id=resolved_source,
                )
            )
        is_primary = resolved_source == str(primary_source_id or source_used or "")
        if rec.validation_only and (entry.get("role") == "primary" or is_primary):
            checks.append(
                _fail_check(
                    "VALIDATION_ONLY_AS_PRIMARY",
                    domain=domain,
                    message=f"validation-only source {resolved_source} used as primary",
                    source_id=resolved_source,
                )
            )

    return checks


def check_staleness(
    *,
    rows: list[dict[str, Any]] | None = None,
    as_of_timestamp: str | None = None,
    domain: str = "cn_equity_daily_bar",
    source_id: str | None = None,
    max_age_days: int = _STALE_DATA_DAYS,
) -> list[DataHealthCheckResult]:
    if rows is not None and len(rows) == 0:
        return [
            _fail_check(
                "EMPTY_RESPONSE",
                domain=domain,
                message="empty response rows",
                source_id=source_id,
                row_count=0,
            )
        ]

    if as_of_timestamp:
        parsed = _parse_iso(as_of_timestamp)
        if parsed and datetime.now(UTC) - parsed > timedelta(days=max_age_days):
            return [
                _warn_check(
                    "STALE_DATA",
                    domain=domain,
                    message=f"as_of_timestamp older than {max_age_days} days",
                    source_id=source_id,
                )
            ]

    return [
        _pass_check(
            "STALE_DATA",
            domain=domain,
            message="staleness window acceptable",
            source_id=source_id,
        )
    ]


def _aggregate_status(checks: list[DataHealthCheckResult]) -> OverallStatus:
    if any(c.status == "FAIL" for c in checks):
        return "FAIL"
    if any(c.status == "BLOCKED" for c in checks):
        return "BLOCKED"
    if any(c.status == "WARN" for c in checks):
        return "WARN"
    return "PASS"


def build_text_summary(report: DataHealthReport) -> str:
    lines = [
        f"Data Health Report {report.report_id}",
        f"Overall: {report.overall_status}",
        f"Profile: {report.profile}",
        f"Checks: {len(report.checks)}",
    ]
    for check in report.checks:
        if check.status != "PASS":
            lines.append(f"- [{check.status}] {check.rule_id}: {check.message}")
    lines.append(f"production_db_mutated={report.production_db_mutated}")
    lines.append(f"source_fetch_performed={report.source_fetch_performed}")
    lines.append(f"sandbox_clean_write_gate_ready={report.sandbox_clean_write_gate_ready}")
    if report.gate_rationale:
        lines.append(f"gate_rationale: {report.gate_rationale}")
    return "\n".join(lines)


def build_report(
    checks: list[DataHealthCheckResult],
    *,
    profile: str,
    input_kind: str = "staged_pilot_evidence",
    gate_ready: bool = False,
    gate_rationale: str = "",
) -> DataHealthReport:
    report = DataHealthReport(
        report_id=str(uuid.uuid4()),
        generated_at=_now_iso(),
        input_kind=input_kind,
        profile=profile,
        overall_status=_aggregate_status(checks),
        checks=checks,
        production_db_mutated=False,
        source_fetch_performed=False,
        sandbox_clean_write_gate_ready=gate_ready,
        gate_rationale=gate_rationale,
    )
    report.text_summary = build_text_summary(report)
    return report


def _checks_from_bundle(bundle: EvidenceBundle) -> list[DataHealthCheckResult]:
    checks: list[DataHealthCheckResult] = []
    raw = bundle.raw_manifest or {}
    domain = str(raw.get("data_domain") or "staged_pilot_bundle")
    source_id = str(raw.get("source_id")) if raw.get("source_id") else None
    default_as_of = str(raw.get("generated_at")) if raw.get("generated_at") else None
    fetches = [item for item in (raw.get("fetches") or []) if isinstance(item, dict)]
    manifest_entries = [
        item for item in (raw.get("manifest_entries") or []) if isinstance(item, dict)
    ]
    entries = fetches or manifest_entries

    for entry in entries:
        request = entry.get("request") or {}
        entry_domain = str(request.get("data_domain") or domain)
        entry_source = request.get("source_id") or source_id
        entry_source_str = str(entry_source) if entry_source else None
        primary = entry_source_str or source_id
        checks.extend(
            check_lineage_entry(
                entry,
                domain=entry_domain,
                primary_source_id=primary,
                default_as_of=default_as_of,
            )
        )

        fetch_result = entry.get("fetch_result") or {}
        raw_paths = fetch_result.get("raw_file_paths") or entry.get("relative_paths") or []
        for raw_path in raw_paths:
            if not raw_path:
                continue
            resolved = _resolve_payload_path(str(raw_path), evidence_dir=bundle.evidence_dir)
            if resolved is None:
                checks.append(
                    _fail_check(
                        "MISSING_REQUIRED_FIELD",
                        domain=entry_domain,
                        message=f"raw payload not found or outside project: {raw_path}",
                        source_id=entry_source_str,
                        evidence_path=str(raw_path),
                    )
                )
                continue
            try:
                payload = _read_json(resolved)
            except (OSError, json.JSONDecodeError) as exc:
                checks.append(
                    _fail_check(
                        "MISSING_REQUIRED_FIELD",
                        domain=entry_domain,
                        message=f"invalid raw payload {raw_path}: {exc}",
                        source_id=entry_source_str,
                        evidence_path=str(resolved),
                    )
                )
                continue

            rel_path = str(resolved.relative_to(PROJECT_ROOT.resolve()))
            rows = _equity_bar_rows(payload)
            if entry_domain == "cn_equity_daily_bar":
                bar_checks = check_daily_bars(
                    rows, domain=entry_domain, source_id=entry_source_str
                )
            elif entry_domain == "cn_announcements":
                bar_checks = check_metadata_rows(
                    rows, domain=entry_domain, source_id=entry_source_str
                )
            else:
                bar_checks = []
            checks.extend(
                replace(check, evidence_path=rel_path) if check.evidence_path is None else check
                for check in bar_checks
            )

    validation = bundle.validation_report or {}
    for item in validation.get("validations") or []:
        if not isinstance(item, dict):
            continue
        as_of = item.get("as_of_timestamp") or raw.get("generated_at")
        checks.extend(
            check_staleness(
                rows=[{"row": 1}] if item.get("row_count", 1) else [],
                as_of_timestamp=str(as_of) if as_of else None,
                domain=str(item.get("data_domain") or domain),
                source_id=str(item.get("source_id")) if item.get("source_id") else None,
            )
        )

    if bundle.staging_manifest is None:
        checks.append(
            _fail_check(
                "MISSING_REQUIRED_FIELD",
                domain="staged_pilot_bundle",
                message="staging evidence manifest missing",
                source_id=source_id,
            )
        )

    deduped: list[DataHealthCheckResult] = []
    seen: set[tuple[str, str, str, str | None]] = set()
    for check in checks:
        key = (check.rule_id, check.domain, check.message, check.evidence_path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(check)

    if not deduped:
        deduped.append(
            _pass_check(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="evidence bundle structure acceptable",
                source_id=source_id,
            )
        )
    return deduped


def evaluate_gate(bundle: EvidenceBundle, checks: list[DataHealthCheckResult]) -> tuple[bool, str]:
    if bundle.load_error:
        return False, f"evidence load failed: {bundle.load_error}"
    has_fail = any(c.status == "FAIL" for c in checks)
    validation = bundle.validation_report or {}
    allow_clean = bool(validation.get("allow_clean_write"))
    closeout_path = bundle.evidence_dir / "pilot_v2_closeout.json"
    rehearsal = False
    if closeout_path.is_file():
        closeout = _read_json(closeout_path)
        rehearsal = bool(closeout.get("sandbox_clean_write_rehearsal"))
    if has_fail:
        return (
            False,
            "FAIL checks present; sandbox clean-write gate blocked until "
            "evidence quality issues resolved",
        )
    if not allow_clean:
        return (
            False,
            "staged-only: validation_report allow_clean_write=false; "
            "structure checks may pass but clean-write not authorized",
        )
    if not rehearsal:
        return (
            False,
            "pilot closeout has sandbox_clean_write_rehearsal=false; "
            "gate input sufficient for review only",
        )
    return (
        True,
        "evidence manifests complete, no FAIL checks, "
        "allow_clean_write authorized for sandbox rehearsal",
    )


def _model_inputs_whitelist_available() -> bool:
    if not MODEL_INPUTS_DIR.is_dir():
        return False
    return any(MODEL_INPUTS_DIR.glob("**/*.yaml"))


def _read_profile_json(evidence_dir: Path, names: tuple[str, ...]) -> dict[str, Any] | None:
    for name in names:
        path = evidence_dir / name
        if path.is_file():
            try:
                return _read_json(path)
            except (OSError, json.JSONDecodeError):
                return None
    return None


def _checks_model_input_whitelist(evidence_dir: Path) -> list[DataHealthCheckResult]:
    domain = "model_input_whitelist"
    if _model_inputs_whitelist_available():
        return [
            _pass_check(
                "MODEL_INPUT_WHITELIST",
                domain=domain,
                message="specs/model_inputs whitelist artifacts present",
            )
        ]
    fixture_yaml = list(evidence_dir.glob("*.yaml")) + list(evidence_dir.glob("**/*.yaml"))
    if fixture_yaml and "whitelist" in evidence_dir.as_posix():
        return [
            _pass_check(
                "MODEL_INPUT_WHITELIST",
                domain=domain,
                message="fixture whitelist YAML present for staged review",
                source_id="B01-WL-fixture",
            )
        ]
    return [
        _blocked_check(
            "MODEL_INPUT_WHITELIST_MISSING",
            domain=domain,
            message=(
                "specs/model_inputs/** not merged; whitelist profile BLOCKED "
                "(owner: B01-WL; do not guess scope)"
            ),
        )
    ]


def _checks_fred_sandbox(evidence_dir: Path) -> list[DataHealthCheckResult]:
    domain = "fred_sandbox_pilot"
    data = _read_profile_json(evidence_dir, ("fred_evidence.json",))
    if data is None:
        return [
            _fail_check(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="fred_evidence.json missing",
                source_id="fred",
            )
        ]

    checks: list[DataHealthCheckResult] = []
    source_id = str(data.get("source_id") or "fred")
    for required_field in ("series_id", "source_fetch_id", "content_hash", "retrieved_at"):
        if not data.get(required_field):
            checks.append(
                _fail_check(
                    "MISSING_REQUIRED_FIELD",
                    domain=domain,
                    message=f"FRED evidence missing {required_field}",
                    source_id=source_id,
                )
            )

    observations = data.get("observations") or []
    if not observations:
        checks.append(
            _fail_check(
                "EMPTY_RESPONSE",
                domain=domain,
                message="FRED observations missing",
                source_id=source_id,
            )
        )
    else:
        obs = observations[0] if isinstance(observations[0], dict) else {}
        if not obs.get("date") or obs.get("value") is None:
            checks.append(
                _fail_check(
                    "MISSING_REQUIRED_FIELD",
                    domain=domain,
                    message="FRED observation missing date/value",
                    source_id=source_id,
                )
            )

    if not data.get("as_of_timestamp"):
        checks.append(
            _fail_check(
                "MISSING_AS_OF_TIMESTAMP",
                domain=domain,
                message="FRED evidence missing as_of_timestamp",
                source_id=source_id,
            )
        )

    if source_id == "macro_supplementary":
        checks.append(
            _warn_check(
                "FRED_PRIMARY_NOT_CLOSED",
                domain=domain,
                message="macro_supplementary does not close FRED primary readiness",
                source_id=source_id,
            )
        )
        return checks

    if not any(c.status == "FAIL" for c in checks):
        checks.append(
            _pass_check(
                "FRED_SANDBOX_EVIDENCE",
                domain=domain,
                message="FRED sandbox evidence fields complete",
                source_id=source_id,
            )
        )
    return checks


def _checks_tdx_manual_probe(evidence_dir: Path) -> list[DataHealthCheckResult]:
    domain = "tdx_manual_probe"
    data = _read_profile_json(evidence_dir, ("tdx_probe_evidence.json",))
    if data is None:
        return [
            _fail_check(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="tdx_probe_evidence.json missing",
                source_id="tdx_pytdx",
            )
        ]

    source_id = str(data.get("source_id") or "tdx_pytdx")
    role = str(data.get("role") or "")
    auth = data.get("authorization") or {}
    if not auth.get("authorized") or not auth.get("statement"):
        return [
            _fail_check(
                "MISSING_AUTHORIZATION",
                domain=domain,
                message="TDX probe missing authorization statement",
                source_id=source_id,
            )
        ]

    if role == "primary" or not data.get("validation_only", True):
        return [
            _fail_check(
                "VALIDATION_ONLY_AS_PRIMARY",
                domain=domain,
                message="TDX cannot be used as production primary",
                source_id=source_id,
            )
        ]

    return [
        _pass_check(
            "TDX_VALIDATION_ONLY",
            domain=domain,
            message="TDX probe authorized and validation-only",
            source_id=source_id,
        )
    ]


def _checks_staged_pilot_v3(evidence_dir: Path) -> list[DataHealthCheckResult]:
    domain = "staged_pilot_v3"
    manifest = _read_profile_json(evidence_dir, ("pilot_v3_manifest.json",))
    if manifest is None:
        return [
            _fail_check(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="pilot_v3_manifest.json missing",
            )
        ]

    caps = {**_V3_DEFAULT_CAPS, **(manifest.get("resource_caps") or {})}
    checks: list[DataHealthCheckResult] = []
    for entry in manifest.get("fetches") or []:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request") or {}
        source_id = str(entry.get("source_used") or request.get("source_id") or "")
        role = str(entry.get("role") or request.get("role") or "")
        data_domain = str(request.get("data_domain") or "")
        row_count = int(entry.get("row_count") or 0)

        if source_id == "akshare" and role == "primary":
            checks.append(
                _fail_check(
                    "VALIDATION_ONLY_AS_PRIMARY",
                    domain=domain,
                    message="AkShare cannot be primary in v3 pilot",
                    source_id=source_id,
                )
            )

        if data_domain == "cn_pdf_reports" or entry.get("bulk_pdf_download"):
            checks.append(
                _fail_check(
                    "CNINFO_PDF_BULK_FORBIDDEN",
                    domain=domain,
                    message="cninfo PDF bulk download forbidden for v3 metadata-only profile",
                    source_id="cninfo",
                )
            )

        cap_key = f"{source_id}_max_rows"
        cap_limit = caps.get(cap_key)
        if cap_limit is not None and (entry.get("cap_breach") or row_count > int(cap_limit)):
            checks.append(
                _fail_check(
                    "RESOURCE_CAP_BREACH",
                    domain=domain,
                    message=f"{source_id} row_count {row_count} exceeds cap {cap_limit}",
                    source_id=source_id,
                    row_count=row_count,
                )
            )

    if not checks:
        checks.append(
            _pass_check(
                "STAGED_PILOT_V3",
                domain=domain,
                message="staged pilot v3 caps/roles acceptable",
            )
        )
    return checks


def _evaluate_rollup_gate(
    rollup: dict[str, Any], checks: list[DataHealthCheckResult]
) -> tuple[bool, str]:
    if any(c.status == "FAIL" for c in checks):
        return (
            False,
            "FAIL checks present; sandbox clean-write gate blocked until issues resolved",
        )
    safety = rollup.get("safety_evidence") or {}
    required = ("role_checks", "schema_checks", "conflict_summary", "no_mutation_proof")
    missing = [key for key in required if not safety.get(key)]
    if missing:
        return (
            False,
            f"missing safety evidence: {', '.join(missing)}; gate blocked",
        )
    validation = rollup.get("validation_report") or {}
    closeout = rollup.get("pilot_closeout") or {}
    if not validation.get("allow_clean_write"):
        return (
            False,
            "staged-only: allow_clean_write=false; rehearsal not authorized",
        )
    if not closeout.get("sandbox_clean_write_rehearsal"):
        return (
            False,
            "pilot closeout missing sandbox_clean_write_rehearsal authorization",
        )
    return (
        True,
        "safety evidence complete; sandbox clean-write rehearsal eligible "
        "(staged/sandbox only, not production-live)",
    )


def _checks_source_readiness_rollup(evidence_dir: Path) -> list[DataHealthCheckResult]:
    domain = "source_readiness_rollup"
    rollup = _read_profile_json(evidence_dir, ("rollup_manifest.json",))
    if rollup is None:
        return [
            _fail_check(
                "MISSING_REQUIRED_FIELD",
                domain=domain,
                message="rollup_manifest.json missing",
            )
        ]

    checks: list[DataHealthCheckResult] = []
    service = DataHealthService()
    for profile_name, rel_path in (rollup.get("profiles") or {}).items():
        sub_dir = PROJECT_ROOT / str(rel_path)
        if not evidence_dir_within_project(sub_dir):
            checks.append(
                _fail_check(
                    "EVIDENCE_PATH_OUT_OF_BOUNDS",
                    domain=domain,
                    message=(
                        f"rollup profile {profile_name} path outside project: {rel_path}"
                    ),
                    evidence_path=str(rel_path),
                )
            )
            continue
        sub_report = service.check_evidence_dir(sub_dir, profile=str(profile_name))
        rollup_severity = (
            "INFO"
            if sub_report.overall_status == "PASS"
            else "FAIL"
            if sub_report.overall_status == "FAIL"
            else "WARN"
        )
        checks.append(
            DataHealthCheckResult(
                rule_id=f"ROLLUP_{profile_name}",
                severity=rollup_severity,
                status=(
                    "PASS"
                    if sub_report.overall_status == "PASS"
                    else sub_report.overall_status  # type: ignore[arg-type]
                ),
                source_id=None,
                domain=domain,
                evidence_path=str(rel_path),
                row_count=len(sub_report.checks),
                message=f"{profile_name} overall={sub_report.overall_status}",
            )
        )
        checks.extend(sub_report.checks)

    if rollup.get("staged_only"):
        checks.append(
            _warn_check(
                "STAGED_ONLY_ROLLUP",
                domain=domain,
                message=(
                    "rollup evidence is staged-only; insufficient for production "
                    "clean-write rehearsal"
                ),
            )
        )
    elif not any(c.status in {"FAIL", "BLOCKED"} for c in checks):
        checks.append(
            _pass_check(
                "SOURCE_READINESS_ROLLUP",
                domain=domain,
                message="rollup profile checks collected",
            )
        )
    return checks


def _evaluate_profile_gate(
    profile: str,
    evidence_dir: Path,
    checks: list[DataHealthCheckResult],
) -> tuple[bool, str]:
    if profile == "source_readiness_rollup":
        rollup = _read_profile_json(evidence_dir, ("rollup_manifest.json",)) or {}
        return _evaluate_rollup_gate(rollup, checks)
    if any(c.status == "FAIL" for c in checks):
        return False, "FAIL checks present; sandbox clean-write gate blocked"
    if any(c.status == "BLOCKED" for c in checks):
        return False, "BLOCKED prerequisites; gate not ready"
    if profile == "model_input_whitelist" and not _model_inputs_whitelist_available():
        return False, "whitelist BLOCKED until specs/model_inputs merged (B01-WL)"
    return False, "staged-only profile; gate input sufficient for review only"


_PROFILE_CHECKERS = {
    "model_input_whitelist": _checks_model_input_whitelist,
    "fred_sandbox_pilot": _checks_fred_sandbox,
    "tdx_manual_probe": _checks_tdx_manual_probe,
    "staged_pilot_v3": _checks_staged_pilot_v3,
    "source_readiness_rollup": _checks_source_readiness_rollup,
}


class DataHealthService:
    """Read-only data health over staged pilot evidence directories."""

    def check_evidence_dir(
        self, evidence_dir: Path, *, profile: str | None = None
    ) -> DataHealthReport:
        resolved = profile or "staged_pilot_bundle"
        if resolved in V2_PROFILES:
            return self._check_v2_profile(resolved, evidence_dir)
        return self._check_staged_pilot_bundle(evidence_dir)

    def _check_v2_profile(self, profile: str, evidence_dir: Path) -> DataHealthReport:
        checker = _PROFILE_CHECKERS[profile]
        checks = checker(evidence_dir)
        gate_ready, rationale = _evaluate_profile_gate(profile, evidence_dir, checks)
        return build_report(
            checks,
            profile=profile,
            input_kind="data_health_v2_profile",
            gate_ready=gate_ready,
            gate_rationale=rationale,
        )

    def _check_staged_pilot_bundle(self, evidence_dir: Path) -> DataHealthReport:
        bundle = load_evidence_bundle(evidence_dir)
        if bundle.load_error:
            checks = [
                _fail_check(
                    "MISSING_REQUIRED_FIELD",
                    domain="staged_pilot_bundle",
                    message=bundle.load_error,
                )
            ]
            gate_ready, rationale = evaluate_gate(bundle, checks)
            return build_report(
                checks,
                profile="staged_pilot_bundle",
                gate_ready=gate_ready,
                gate_rationale=rationale,
            )

        checks = _checks_from_bundle(bundle)
        gate_ready, rationale = evaluate_gate(bundle, checks)
        profile = str((bundle.raw_manifest or {}).get("data_domain") or "staged_pilot_bundle")
        return build_report(
            checks,
            profile=profile,
            gate_ready=gate_ready,
            gate_rationale=rationale,
        )
