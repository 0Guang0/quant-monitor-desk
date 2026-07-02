"""Tier A live acceptance harness (M-DATA-03 S00-INFRA · ADR-034)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.datasources.live_tier_router import TIER_A_SOURCES
from backend.app.datasources.product_live_gate import is_product_live_fetch_allowed
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path
from backend.app.ops.tier_a_live_status import (
    PASS_SYNC_STATUSES,
    _BAR_SOURCE_IDS,
    live_acceptance_mock_env_enabled,
    validate_sec_edgar_user_agent,
)
from backend.app.sync.incremental_source_registry import iter_tier_a_incremental_sources

M_DATA_03_SANDBOX_SEGMENT = "m-data-03"
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox" / M_DATA_03_SANDBOX_SEGMENT

QUICK_SOURCE_IDS: tuple[str, ...] = ("fred", "baostock")

SOURCE_API_KEY_ENV: dict[str, str] = {
    "fred": "FRED_API_KEY",
    "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
    "sec_edgar": "SEC_EDGAR_USER_AGENT",
}


class TierALiveEnvError(RuntimeError):
    """Invalid live acceptance environment (CLI exit 2)."""

    def __init__(self, message: str, *, code: str = "INVALID_LIVE_ENV") -> None:
        super().__init__(message)
        self.code = code


def canonical_main_db_paths() -> frozenset[Path]:
    return frozenset(
        {
            (PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb").resolve(),
            (DATA_ROOT / "duckdb" / "quant_monitor.duckdb").resolve(),
        }
    )


def is_canonical_main_db_path(path: Path | str) -> bool:
    return resolve_sandbox_path(path).resolve() in canonical_main_db_paths()


def is_canonical_main_data_root(data_root: Path | str) -> bool:
    resolved = resolve_sandbox_path(data_root).resolve()
    if resolved == (PROJECT_ROOT / "data").resolve():
        return True
    return is_canonical_main_db_path(resolved / "duckdb" / "quant_monitor.duckdb")


def assert_isolated_live_data_root(data_root: Path | str) -> Path:
    """Reject canonical main DB paths; require `.audit-sandbox/m-data-03`."""
    resolved = resolve_sandbox_path(data_root).resolve()
    if is_canonical_main_db_path(resolved) or is_canonical_main_data_root(resolved):
        raise TierALiveEnvError(
            f"canonical main DB/data root rejected for live acceptance: {resolved}",
            code="CANONICAL_MAIN_DB_REJECTED",
        )
    posix = resolved.as_posix()
    if ".audit-sandbox" not in posix or M_DATA_03_SANDBOX_SEGMENT not in posix:
        raise TierALiveEnvError(
            f"DATA_ROOT must be under .audit-sandbox/{M_DATA_03_SANDBOX_SEGMENT}: {resolved}",
            code="ISOLATED_ROOT_REQUIRED",
        )
    return resolved


def resolve_live_data_root(data_root: Path | str | None = None) -> Path:
    raw = data_root
    if raw is None:
        raw = os.environ.get("QMD_DATA_ROOT") or os.environ.get("DATA_ROOT")
    if raw is None or str(raw).strip() == "":
        return DEFAULT_SANDBOX_ROOT
    return assert_isolated_live_data_root(Path(raw))


def missing_api_keys_for_sources(source_ids: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for sid in source_ids:
        env_name = SOURCE_API_KEY_ENV.get(sid)
        if env_name is None:
            continue
        raw = os.environ.get(env_name, "")
        if sid == "sec_edgar":
            if validate_sec_edgar_user_agent(raw) is None:
                missing.append(
                    f"{env_name} missing or lacks contact identity (required for {sid})"
                )
            continue
        if not str(raw).strip():
            missing.append(f"{env_name} (required for {sid})")
    return missing


def validate_live_acceptance_env(
    *,
    data_root: Path | str | None = None,
    source_ids: tuple[str, ...] | None = None,
) -> Path:
    """Validate env for live acceptance; raise TierALiveEnvError on failure."""
    if not is_product_live_fetch_allowed():
        raise TierALiveEnvError(
            "QMD_ALLOW_LIVE_FETCH not set to opt-in value (ADR-027)",
            code="LIVE_FETCH_NOT_OPTED_IN",
        )
    if live_acceptance_mock_env_enabled():
        raise TierALiveEnvError(
            "QMD_FRED_INCREMENTAL_USE_MOCK forbidden in live acceptance (ADR-027/034)",
            code="MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE",
        )
    resolved_root = resolve_live_data_root(data_root)
    os.environ["QMD_DATA_ROOT"] = str(resolved_root)
    targets = source_ids or tuple(iter_tier_a_incremental_sources())
    missing = missing_api_keys_for_sources(targets)
    if missing:
        raise TierALiveEnvError(
            "missing API keys: " + "; ".join(missing),
            code="MISSING_API_KEYS",
        )
    return resolved_root


def select_source_ids(
    *,
    source_id: str | None = None,
    quick: bool = False,
) -> tuple[str, ...]:
    if source_id is not None:
        if source_id not in TIER_A_SOURCES:
            raise TierALiveEnvError(f"unknown Tier A source_id: {source_id!r}")
        return (source_id,)
    if quick:
        return QUICK_SOURCE_IDS
    return tuple(iter_tier_a_incremental_sources())


def ensure_isolated_db(data_root: Path) -> Path:
    """Create isolated DuckDB under data_root; apply migrations + registry sync."""
    import duckdb

    from backend.app.datasources.source_registry import SourceRegistry
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    db = data_root / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    if not db.is_file():
        con = duckdb.connect(str(db))
        try:
            apply_migrations(con)
        finally:
            con.close()
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        registry = SourceRegistry()
        registry.load()
        registry.sync_to_db(con, tombstone_missing=True)
    return db


def _latest_raw_evidence_dir(data_root: Path, source_id: str) -> Path | None:
    raw_root = data_root / "raw" / source_id
    if not raw_root.is_dir():
        legacy = data_root / "raw"
        if source_id == "fred" and legacy.is_dir():
            return legacy
        return None
    candidates = [p for p in raw_root.rglob("*") if p.is_file() and p.suffix == ".json"]
    if not candidates:
        return raw_root if any(raw_root.iterdir()) else None
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return newest.parent


def _run_f0_data_health(
    source_id: str, *, data_root: Path, db_path: Path
) -> tuple[str, str]:
    """Run F0 data health on latest raw evidence; return (status, detail)."""
    evidence_dir = _latest_raw_evidence_dir(data_root, source_id)
    if evidence_dir is None:
        return "SKIP", "no raw evidence; caught-up inspect-only gate"

    # ponytail: live incremental writes hash-named bundles, not fred_sandbox_pilot fred_evidence.json
    if source_id == "fred" and not (evidence_dir / "fred_evidence.json").is_file():
        return "SKIP", "live incremental evidence; fred_sandbox_pilot partial F0 skipped"

    from backend.app.ops.data_health import DataHealthLoadError, DataHealthService
    from backend.app.ops.data_health_profiles import run_data_health_profile

    try:
        if source_id in _BAR_SOURCE_IDS:
            report, *_ = run_data_health_profile(
                profile_id="market_bar_p0",
                domain="market_bar_1d",
                evidence_path=evidence_dir,
                db_path=db_path if db_path.is_file() else None,
                start_date=None,
                end_date=None,
                max_rows=1000,
            )
        else:
            profile = "staged_pilot_v3" if source_id == "cninfo" else "fred_sandbox_pilot"
            report = DataHealthService().check_evidence_dir(evidence_dir, profile=profile)
    except DataHealthLoadError as exc:
        return "SKIP", f"partial F0 evidence unloadable: {exc}"

    status = str(report.overall_status)
    detail = report.gate_rationale or status
    if status in {"FAIL", "BLOCKED"}:
        return "FAIL", f"data-health {status}: {detail}"
    if not report.sandbox_clean_write_gate_ready:
        # ponytail: live incremental raw may not satisfy full sandbox gate; E2 inspect remains authoritative
        return "SKIP", f"partial F0 gate not ready: {detail}"
    return status, detail


@dataclass(frozen=True)
class SourceAcceptanceResult:
    source_id: str
    status: Literal["pass", "fail"]
    detail: str = ""


def run_source_live_acceptance(source_id: str, *, data_root: Path) -> SourceAcceptanceResult:
    """Run sync→clean→inspect→data health for one Tier A source (S-ACCEPT)."""
    from backend.app.ops.tier_a_live_incremental_dispatch import run_tier_a_live_incremental

    resolved = assert_isolated_live_data_root(data_root)
    os.environ["QMD_DATA_ROOT"] = str(resolved)
    db_path = ensure_isolated_db(resolved)
    try:
        outcome = run_tier_a_live_incremental(source_id, resolved)
    except Exception as exc:
        return SourceAcceptanceResult(source_id=source_id, status="fail", detail=str(exc))

    health_status, health_detail = _run_f0_data_health(
        source_id, data_root=resolved, db_path=db_path
    )
    if health_status == "FAIL":
        return SourceAcceptanceResult(
            source_id=source_id,
            status="fail",
            detail=f"data-health FAIL: {health_detail}",
        )

    if outcome.inspect_status == "FAIL":
        return SourceAcceptanceResult(
            source_id=source_id,
            status="fail",
            detail=f"db-inspect FAIL: {outcome.detail}",
        )
    if outcome.sync_status not in PASS_SYNC_STATUSES:
        return SourceAcceptanceResult(
            source_id=source_id,
            status="fail",
            detail=f"sync failed: {outcome.detail}",
        )
    if outcome.sync_status == "COMPLETED" and outcome.clean_row_count < 1:
        raw_dir = resolved / "raw" / source_id
        fred_raw = resolved / "raw"
        has_raw = (raw_dir.is_dir() and any(raw_dir.rglob("*"))) or (
            source_id == "fred" and fred_raw.is_dir() and any(fred_raw.rglob("*"))
        )
        if not has_raw:
            return SourceAcceptanceResult(
                source_id=source_id,
                status="fail",
                detail=f"COMPLETED but {outcome.clean_table} empty: {outcome.detail}",
            )
    return SourceAcceptanceResult(
        source_id=source_id,
        status="pass",
        detail=(
            f"sync={outcome.sync_status} inspect={outcome.inspect_status} "
            f"health={health_status} {outcome.clean_table}={outcome.clean_row_count}"
        ),
    )


def run_acceptance(
    *,
    source_id: str | None = None,
    quick: bool = False,
    data_root: Path | str | None = None,
) -> int:
    """Return CLI exit code: 0 pass · 1 source failure · 2 invalid env."""
    try:
        sources = select_source_ids(source_id=source_id, quick=quick)
        resolved_root = validate_live_acceptance_env(data_root=data_root, source_ids=sources)
    except TierALiveEnvError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    failures: list[SourceAcceptanceResult] = []
    for sid in sources:
        outcome = run_source_live_acceptance(sid, data_root=resolved_root)
        if outcome.status != "pass":
            failures.append(outcome)

    if failures:
        for item in failures:
            print(f"{item.source_id}: {item.detail}")
        return 1
    return 0


__all__ = [
    "DEFAULT_SANDBOX_ROOT",
    "M_DATA_03_SANDBOX_SEGMENT",
    "QUICK_SOURCE_IDS",
    "SOURCE_API_KEY_ENV",
    "SourceAcceptanceResult",
    "TierALiveEnvError",
    "assert_isolated_live_data_root",
    "canonical_main_db_paths",
    "ensure_isolated_db",
    "is_canonical_main_data_root",
    "is_canonical_main_db_path",
    "missing_api_keys_for_sources",
    "resolve_live_data_root",
    "run_acceptance",
    "run_source_live_acceptance",
    "select_source_ids",
    "validate_live_acceptance_env",
]
