"""R3G-01 rehearsal plan — capped candidates and FRED authorization (fail-closed)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.ops.fred_sandbox_pilot import (
    FredPilotAuthorizationError,
    load_authorization_yaml,
)

DEFAULT_FRED_AUTHORIZATION_PATH = (
    PROJECT_ROOT / ".audit-sandbox/round3g/fred_user_authorization.yaml"
)
CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"
PROVIDER_CATALOG_PATH = PROJECT_ROOT / "specs/datasource_registry/provider_catalog.yaml"

R3G01_MAX_SERIES = 3
R3G01_FRED_MAX_WINDOW_DAYS = 120

_CAP_PROFILE_DEFAULTS: dict[str, dict[str, int]] = {
    "r3g01": {
        "max_symbols": 3,
        "max_series": R3G01_MAX_SERIES,
        "max_window_baostock": 30,
        "max_window_fred": R3G01_FRED_MAX_WINDOW_DAYS,
    },
    "r3g03": {
        "max_symbols": 10,
        "max_series": 10,
        "max_window": 120,
    },
}


class RehearsalPlanError(RuntimeError):
    """Candidate set or authorization failed fail-closed gate."""


@dataclass(frozen=True)
class RehearsalCandidate:
    source_id: str
    domain: str
    operation: str
    symbols_or_series: tuple[str, ...]
    window_days: int
    metadata_only: bool = False


def _load_contract_caps() -> dict[str, Any]:
    if not CONTRACT_PATH.is_file():
        raise RehearsalPlanError(f"missing contract: {CONTRACT_PATH}")
    raw = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    return raw.get("candidate_caps") or {}


def _r3g_p0_candidates() -> tuple[RehearsalCandidate, ...]:
    return (
        RehearsalCandidate(
            source_id="baostock",
            domain="cn_equity_daily_bar",
            operation="fetch_daily_bar",
            symbols_or_series=("sh.600519", "sh.600000", "sz.000001"),
            window_days=30,
        ),
        RehearsalCandidate(
            source_id="cninfo",
            domain="cn_announcements",
            operation="fetch_announcement_index",
            symbols_or_series=("sh.600519",),
            window_days=30,
            metadata_only=True,
        ),
        RehearsalCandidate(
            source_id="fred",
            domain="macro_series",
            operation="fetch_macro_series",
            symbols_or_series=("DGS10", "T10Y3M", "VIXCLS"),
            window_days=120,
        ),
    )


_CANDIDATE_SETS: dict[str, tuple[RehearsalCandidate, ...]] = {
    "r3g_p0": _r3g_p0_candidates(),
}


def load_candidate_set(name: str) -> tuple[RehearsalCandidate, ...]:
    """Return frozen R3G-01 candidate set by name."""
    try:
        return _CANDIDATE_SETS[name]
    except KeyError as exc:
        raise RehearsalPlanError(f"unknown candidate set: {name!r}") from exc


def validate_contract_source_caps(
    *,
    source_id: str,
    domain: str,
    symbols: tuple[str, ...],
    window_days: int,
    metadata_only: bool,
    profile: str,
    error_cls: type[Exception] = RehearsalPlanError,
) -> None:
    """Parameterized cap validation for r3g01 (rehearse) and r3g03 (promote) profiles."""
    caps = _load_contract_caps()
    source_caps = caps.get(source_id)
    if source_caps is None:
        raise error_cls(f"forbidden or unknown source: {source_id}")

    allowed_domains = source_caps.get("allowed_domains") or []
    if domain not in allowed_domains:
        raise error_cls(f"domain {domain!r} not allowed for {source_id}")

    defaults = _CAP_PROFILE_DEFAULTS[profile]
    symbol_count = len(symbols)
    if source_id == "fred":
        max_series_key = f"{profile}_max_series"
        max_series = int(source_caps.get(max_series_key) or defaults["max_series"])
        if symbol_count > max_series:
            raise error_cls(f"fred max {max_series} series, got {symbol_count}")
        if profile == "r3g01":
            max_window = int(
                source_caps.get("r3g01_max_window_days") or defaults["max_window_fred"]
            )
        else:
            max_window = int(source_caps.get("r3g03_max_window_days") or defaults["max_window"])
    else:
        max_symbols_key = f"{profile}_max_symbols"
        max_symbols = int(source_caps.get(max_symbols_key) or defaults["max_symbols"])
        if symbol_count > max_symbols:
            raise error_cls(f"{source_id} max {max_symbols} symbols, got {symbol_count}")
        if profile == "r3g01":
            max_window = int(source_caps.get("r3g01_max_window_days") or defaults["max_window_baostock"])
        else:
            max_window = int(source_caps.get("r3g03_max_window_days") or defaults["max_window"])

    if window_days > max_window:
        raise error_cls(f"{source_id} max window {max_window}d, got {window_days}d")

    if source_caps.get("metadata_only") is True and not metadata_only:
        if source_id == "cninfo":
            raise error_cls(f"{source_id} requires metadata_only=true")


def validate_source_caps(candidate: RehearsalCandidate) -> None:
    """Hard-reject candidates exceeding contract r3g01 caps."""
    validate_contract_source_caps(
        source_id=candidate.source_id,
        domain=candidate.domain,
        symbols=candidate.symbols_or_series,
        window_days=candidate.window_days,
        metadata_only=candidate.metadata_only,
        profile="r3g01",
        error_cls=RehearsalPlanError,
    )


def validate_fred_authorization(
    path: str | Path | None,
    *,
    series_ids: tuple[str, ...],
    require_live_credentials: bool = False,
) -> dict[str, Any]:
    """Fail-closed FRED authorization — reuses fred_sandbox_pilot semantics + R3G caps."""
    if path is None:
        path = DEFAULT_FRED_AUTHORIZATION_PATH
    try:
        auth = load_authorization_yaml(path)
    except FredPilotAuthorizationError as exc:
        raise RehearsalPlanError(str(exc)) from exc

    if auth.get("source_id") != "fred":
        raise RehearsalPlanError("authorization source_id must be fred")
    if auth.get("allow_production_clean_write"):
        raise RehearsalPlanError("allow_production_clean_write must be false")

    max_series = int(auth.get("max_series") or R3G01_MAX_SERIES)
    if len(series_ids) > max_series:
        raise RehearsalPlanError(f"fred authorization max {max_series} series")
    if len(series_ids) > R3G01_MAX_SERIES:
        raise RehearsalPlanError(f"r3g01 contract max {R3G01_MAX_SERIES} series")

    authorized = tuple(auth.get("symbols_or_series") or ())
    unknown = [s for s in series_ids if s not in authorized]
    if unknown:
        raise RehearsalPlanError(f"series not in authorization artifact: {unknown}")

    max_window = int(auth.get("max_window_days") or R3G01_FRED_MAX_WINDOW_DAYS)
    if max_window > R3G01_FRED_MAX_WINDOW_DAYS:
        raise RehearsalPlanError(
            f"authorization max_window_days {max_window} exceeds r3g01 cap"
        )
    if require_live_credentials:
        api_env = str(auth.get("api_key_env") or "FRED_API_KEY")
        if not os.environ.get(api_env):
            raise RehearsalPlanError(f"missing API key env {api_env}")
    return auth


def assert_sandbox_route_posture(source_id: str) -> None:
    """Ensure provider catalog marks production_default_enabled=false for rehearsal sources."""
    if not PROVIDER_CATALOG_PATH.is_file():
        raise RehearsalPlanError(f"missing provider catalog: {PROVIDER_CATALOG_PATH}")
    catalog = yaml.safe_load(PROVIDER_CATALOG_PATH.read_text(encoding="utf-8")) or {}
    providers = catalog.get("providers") or []
    match = next((p for p in providers if source_id in (p.get("source_ids") or [])), None)
    if match is None:
        raise RehearsalPlanError(f"provider catalog missing source: {source_id}")
    if match.get("production_default_enabled"):
        raise RehearsalPlanError(
            f"{source_id} production_default_enabled must be false for R3G-01"
        )


def validate_candidate_set(
    name: str,
    *,
    fred_authorization: Path | None = None,
    require_live_credentials: bool = False,
) -> None:
    """Validate entire candidate set caps and FRED authorization when present."""
    candidates = load_candidate_set(name)
    for candidate in candidates:
        validate_source_caps(candidate)
        assert_sandbox_route_posture(candidate.source_id)
    fred = next((c for c in candidates if c.source_id == "fred"), None)
    if fred is not None:
        auth_path = fred_authorization or DEFAULT_FRED_AUTHORIZATION_PATH
        validate_fred_authorization(
            auth_path,
            series_ids=fred.symbols_or_series,
            require_live_credentials=require_live_credentials,
        )
