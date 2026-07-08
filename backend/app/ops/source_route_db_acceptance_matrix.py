"""Documented source matrix for SourceRouteDbAcceptanceSpine preview/execute."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.ops.source_route_db_acceptance import AcceptanceRequest

REGISTRY_PATH = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
CAPABILITIES_PATH = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
SOURCE_ROUTE_DB_SANDBOX_SEGMENT = "source-route-db"

_MATRIX_BY_KEY: dict[str, AcceptanceMatrixTarget] | None = None

SourcePositioning = Literal[
    "primary",
    "validation",
    "prediction_probability",
    "manual_review_only",
    "licensed_validation",
    "local_terminal_primary",
]


@dataclass(frozen=True, kw_only=True)
class AcceptanceMatrixTarget:
    display_name: str
    request: AcceptanceRequest
    positioning: SourcePositioning
    auth_env: tuple[str, ...] = ()
    requires_local_terminal: bool = False
    requires_license: bool = False
    expected_write_grade: str = "primary_grade_clean"
    downstream_expectation: str = "PRIMARY_GRADE_READ"


# ponytail: Python tuple is the matrix SSOT for closure semantics; YAML registry/capabilities
# are validated via validate_matrix_against_registry() — not generated from YAML (CS-16).
DOCUMENTED_SOURCE_MATRIX: tuple[AcceptanceMatrixTarget, ...] = (
    AcceptanceMatrixTarget(
        display_name="QMT / xtdata",
        request=AcceptanceRequest(
            data_domain="cn_equity_daily_bar",
            source_id="qmt_xtdata",
            operation="fetch_daily_bar",
        ),
        positioning="local_terminal_primary",
        auth_env=("QMT_XTDATA_AUTHORIZED",),
        requires_local_terminal=True,
    ),
    AcceptanceMatrixTarget(
        display_name="baostock",
        request=AcceptanceRequest(
            data_domain="cn_equity_daily_bar",
            source_id="baostock",
            operation="fetch_daily_bar",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="AkShare",
        request=AcceptanceRequest(
            data_domain="cn_equity_daily_bar",
            source_id="akshare",
            operation="fetch_daily_bar_validation",
        ),
        positioning="validation",
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="CNINFO",
        request=AcceptanceRequest(
            data_domain="cn_announcements",
            source_id="cninfo",
            operation="fetch_announcement_index",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="Yahoo Finance / yfinance",
        request=AcceptanceRequest(
            data_domain="us_equity_daily_bar",
            source_id="yahoo_finance",
            operation="fetch_us_daily_bar_validation",
        ),
        positioning="validation",
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="Alpha Vantage",
        request=AcceptanceRequest(
            data_domain="us_equity_daily_bar",
            source_id="alpha_vantage",
            operation="fetch_us_daily_bar",
        ),
        positioning="primary",
        auth_env=("ALPHA_VANTAGE_API_KEY",),
    ),
    AcceptanceMatrixTarget(
        display_name="Stooq",
        request=AcceptanceRequest(
            data_domain="global_market_daily_bar",
            source_id="stooq",
            operation="fetch_global_daily_bar",
        ),
        positioning="validation",
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="Deribit",
        request=AcceptanceRequest(
            data_domain="crypto_derivatives",
            source_id="deribit",
            operation="fetch_derivatives_instruments",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="CoinGecko",
        request=AcceptanceRequest(
            data_domain="crypto_spot_market",
            source_id="coingecko",
            operation="fetch_spot_market_reference",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="US Treasury",
        request=AcceptanceRequest(
            data_domain="us_treasury_yield_curve",
            source_id="us_treasury",
            operation="fetch_yield_curve",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="SEC EDGAR",
        request=AcceptanceRequest(
            data_domain="us_filings",
            source_id="sec_edgar",
            operation="fetch_company_filings",
        ),
        positioning="primary",
        auth_env=("SEC_EDGAR_USER_AGENT",),
    ),
    AcceptanceMatrixTarget(
        display_name="CFTC COT",
        request=AcceptanceRequest(
            data_domain="cot_positioning",
            source_id="cftc_cot",
            operation="fetch_cot_positioning",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="BIS",
        request=AcceptanceRequest(
            data_domain="central_bank_policy",
            source_id="bis",
            operation="fetch_policy_rate",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="World Bank",
        request=AcceptanceRequest(
            data_domain="development_indicator",
            source_id="world_bank",
            operation="fetch_indicator_series",
        ),
        positioning="primary",
    ),
    AcceptanceMatrixTarget(
        display_name="FRED",
        request=AcceptanceRequest(
            data_domain="macro_series",
            source_id="fred",
            operation="fetch_macro_series",
        ),
        positioning="primary",
        auth_env=("FRED_API_KEY",),
    ),
    AcceptanceMatrixTarget(
        display_name="Kalshi",
        request=AcceptanceRequest(
            data_domain="prediction_market_probability",
            source_id="kalshi",
            operation="fetch_regulated_probability_signal",
        ),
        positioning="prediction_probability",
        expected_write_grade="primary_grade_clean",
        downstream_expectation="PROBABILITY_SIGNAL_READ",
    ),
    AcceptanceMatrixTarget(
        display_name="Polymarket",
        request=AcceptanceRequest(
            data_domain="prediction_market_probability",
            source_id="polymarket",
            operation="fetch_prediction_market_probability",
        ),
        positioning="validation",
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="mootdx / TDX compatible",
        request=AcceptanceRequest(
            data_domain="cn_equity_daily_bar",
            source_id="mootdx",
            operation="fetch_daily_bar",
        ),
        positioning="validation",
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="东方财富",
        request=AcceptanceRequest(
            data_domain="cn_equity_daily_bar",
            source_id="eastmoney",
            operation="fetch_daily_bar_validation",
        ),
        positioning="validation",
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="新浪财经",
        request=AcceptanceRequest(
            data_domain="cn_equity_daily_bar",
            source_id="sina_finance",
            operation="fetch_daily_bar_validation",
        ),
        positioning="validation",
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="同花顺 / iFinD",
        request=AcceptanceRequest(
            data_domain="concept_theme",
            source_id="ths_ifind",
            operation="fetch_concept_theme",
        ),
        positioning="licensed_validation",
        auth_env=("THS_IFIND_LICENSE_ARTIFACT",),
        requires_license=True,
        expected_write_grade="blocked",
        downstream_expectation="VALIDATION_ONLY",
    ),
    AcceptanceMatrixTarget(
        display_name="Web Search",
        request=AcceptanceRequest(
            data_domain="supplemental_web_evidence",
            source_id="web_search",
            operation="fetch_supplemental_web_evidence",
        ),
        positioning="manual_review_only",
        expected_write_grade="blocked",
        downstream_expectation="MANUAL_REVIEW_ONLY",
    ),
)


def matrix_target_key(target: AcceptanceMatrixTarget) -> str:
    req = target.request
    return f"{req.data_domain}:{req.source_id}:{req.operation}"


def iter_matrix_targets() -> tuple[AcceptanceMatrixTarget, ...]:
    return DOCUMENTED_SOURCE_MATRIX


def _matrix_by_key() -> dict[str, AcceptanceMatrixTarget]:
    global _MATRIX_BY_KEY
    if _MATRIX_BY_KEY is None:
        _MATRIX_BY_KEY = {matrix_target_key(target): target for target in DOCUMENTED_SOURCE_MATRIX}
    return _MATRIX_BY_KEY


def resolve_matrix_data_root(data_root: Path | str) -> Path:
    """Require `.audit-sandbox/<source-route-db>` for matrix/spine acceptance runs."""
    from backend.app.ops.acceptance_isolation import assert_isolated_live_data_root

    return assert_isolated_live_data_root(
        data_root,
        required_segment=SOURCE_ROUTE_DB_SANDBOX_SEGMENT,
    )


def find_matrix_target(request: AcceptanceRequest) -> AcceptanceMatrixTarget | None:
    return _matrix_by_key().get(
        f"{request.data_domain}:{request.source_id}:{request.operation}"
    )


def find_matrix_target_by_key(target_key: str) -> AcceptanceMatrixTarget | None:
    return _matrix_by_key().get(target_key)


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid yaml document: {path}")
    return payload


def validate_matrix_target_metadata() -> list[str]:
    """Ensure requires_* flags stay consistent with auth_env (Chesterton gate SSOT)."""
    violations: list[str] = []
    for target in DOCUMENTED_SOURCE_MATRIX:
        if target.requires_local_terminal:
            if not target.auth_env:
                violations.append(
                    f"{target.request.source_id} requires_local_terminal=True but auth_env empty"
                )
        if target.requires_license:
            if not target.auth_env:
                violations.append(
                    f"{target.request.source_id} requires_license=True but auth_env empty"
                )
        if target.request.source_id == "qmt_xtdata" and "QMT_XTDATA_AUTHORIZED" not in target.auth_env:
            violations.append("qmt_xtdata requires_local_terminal without QMT_XTDATA_AUTHORIZED auth_env")
        if target.request.source_id == "ths_ifind" and "THS_IFIND_LICENSE_ARTIFACT" not in target.auth_env:
            violations.append("ths_ifind requires_license without THS_IFIND_LICENSE_ARTIFACT auth_env")
    return violations


def validate_matrix_against_registry() -> list[str]:
    """Return CONTRACT_VIOLATION messages when matrix rows drift from registry/capabilities."""
    violations: list[str] = list(validate_matrix_target_metadata())
    registry = _load_yaml(REGISTRY_PATH)
    capabilities = _load_yaml(CAPABILITIES_PATH)
    registry_ids = {
        str(item["source_id"])
        for item in registry.get("sources", [])
        if isinstance(item, dict) and item.get("source_id")
    }
    cap_sources = capabilities.get("sources", {})
    if not isinstance(cap_sources, dict):
        return ["capabilities document missing sources map"]

    for target in DOCUMENTED_SOURCE_MATRIX:
        req = target.request
        if req.source_id not in registry_ids:
            violations.append(f"missing registry source_id={req.source_id}")
            continue
        source_caps = cap_sources.get(req.source_id)
        if not isinstance(source_caps, dict):
            violations.append(f"missing capabilities for source_id={req.source_id}")
            continue
        domains = source_caps.get("domains", {})
        if not isinstance(domains, dict):
            violations.append(f"missing domains for source_id={req.source_id}")
            continue
        domain_caps = domains.get(req.data_domain)
        if not isinstance(domain_caps, dict):
            violations.append(
                f"missing capability domain={req.data_domain} for source_id={req.source_id}"
            )
            continue
        operations = domain_caps.get("operations", {})
        if not isinstance(operations, dict) or req.operation not in operations:
            violations.append(
                f"missing operation={req.operation} for "
                f"{req.data_domain}:{req.source_id}"
            )
    return violations


def preview_route_payload(request: AcceptanceRequest) -> dict[str, object]:
    """Route preview via DataSourceService for any matrix target."""
    return build_incremental_preview_service(
        request.source_id,
        request.data_domain,
    ).preview_route(
        data_domain=request.data_domain,
        operation=request.operation,
        market_id=request.market_id,
        run_id="acceptance-preview",
        job_id="acceptance-preview",
    ).to_payload_dict()


def build_incremental_preview_service(source_id: str, data_domain: str):
    """Shared preview service factory for matrix rows and incremental runners."""
    from backend.app.datasources.service import DataSourceService

    registry, caps, planner = _cached_route_preview_bundle(source_id, data_domain)
    return DataSourceService(
        source_registry=registry,
        capability_registry=caps,
        route_planner=planner,
        staged_fixture_mode=False,
    )


@lru_cache(maxsize=32)
def _cached_route_preview_bundle(source_id: str, data_domain: str):
    from backend.app.ops.macro_incremental_common import load_incremental_route_bundle

    return load_incremental_route_bundle(source_id=source_id, data_domain=data_domain)


def missing_gate_errors(target: AcceptanceMatrixTarget) -> tuple[str, ...]:
    """Gate errors aligned with tier SOURCE_API_KEY_ENV SSOT and matrix auth_env rows."""
    import os

    from backend.app.ops.tier_a_evidence_runner import (
        SOURCE_API_KEY_ENV,
        validate_sec_edgar_user_agent,
    )

    sid = target.request.source_id
    if sid in SOURCE_API_KEY_ENV:
        env_name = SOURCE_API_KEY_ENV[sid]
        raw = os.environ.get(env_name, "")
        if sid == "sec_edgar":
            if validate_sec_edgar_user_agent(raw) is None:
                return (f"gate:{env_name}:missing for {sid}",)
            return ()
        if not str(raw).strip():
            return (f"gate:{env_name}:missing for {sid}",)
        return ()
    errors: list[str] = []
    for env_name in target.auth_env:
        if not str(os.environ.get(env_name, "")).strip():
            errors.append(f"gate:{env_name}:missing for {target.request.source_id}")
    return tuple(errors)


_QUALIFICATION_PLACEHOLDER_VALUES = frozenset({"1", "true", "yes", "placeholder", "stub"})


def validate_qualification_credentials(target: AcceptanceMatrixTarget) -> tuple[str, ...]:
    """When qualification_deferred env is present, reject placeholder values and invalid artifacts."""
    import os

    if target.request.source_id not in QUALIFICATION_DEFERRED_SOURCE_IDS:
        return ()
    errors: list[str] = []
    for env_name in target.auth_env:
        raw = str(os.environ.get(env_name, "")).strip()
        if not raw:
            continue
        if raw.lower() in _QUALIFICATION_PLACEHOLDER_VALUES:
            errors.append(
                f"gate:{env_name}:placeholder for {target.request.source_id}"
            )
            continue
        if target.request.source_id == "ths_ifind" and not Path(raw).is_file():
            errors.append(
                f"gate:{env_name}:invalid_artifact for {target.request.source_id}"
            )
    return tuple(errors)


def is_non_primary_positioning(target: AcceptanceMatrixTarget) -> bool:
    """Route-only PASS positioning (validation / manual_review / licensed_validation).

    Not included (require live proof via dispatch):
    - local_terminal_primary (qmt_xtdata → evidence_fetch)
    - prediction_probability (kalshi → evidence_fetch)
    - primary (incremental clean write handlers)
    """
    return target.positioning in {
        "validation",
        "manual_review_only",
        "licensed_validation",
    }


EVIDENCE_FETCH_MATRIX_SOURCE_IDS = frozenset({"coingecko", "kalshi", "qmt_xtdata", "ths_ifind"})


QUALIFICATION_DEFERRED_SOURCE_IDS = frozenset({"qmt_xtdata", "ths_ifind"})

# Environment/upstream failures that must stay FAIL_EXTERNAL on the matrix row but may closure PASS (ADR-016 §4).
EXTERNAL_DEFERRED_SOURCE_IDS = frozenset({"sec_edgar", "stooq", "mootdx"})

_CLOSURE_OUTCOMES = frozenset({"PASS", "FAIL_EXTERNAL", "FAIL_CONTRACT", "FAIL"})


_MATRIX_CNINFO_SYMBOLS: tuple[str, ...] | None = None
_MATRIX_ALPHA_VANTAGE_SYMBOL: str | None = None
_MATRIX_KALSHI_MARKET_TICKER: str | None = None
_MATRIX_COINGECKO_ASSET_ID: str | None = None


def _load_matrix_live_defaults() -> None:
    global _MATRIX_CNINFO_SYMBOLS, _MATRIX_ALPHA_VANTAGE_SYMBOL
    global _MATRIX_KALSHI_MARKET_TICKER, _MATRIX_COINGECKO_ASSET_ID
    if _MATRIX_CNINFO_SYMBOLS is not None:
        return
    from backend.app.datasources.product_live_ports import SOURCE_LIVE_DEFAULTS

    _MATRIX_CNINFO_SYMBOLS = tuple(SOURCE_LIVE_DEFAULTS["cninfo"]["symbols"])
    _MATRIX_ALPHA_VANTAGE_SYMBOL = str(SOURCE_LIVE_DEFAULTS["alpha_vantage"]["symbols"][0])
    _MATRIX_KALSHI_MARKET_TICKER = str(SOURCE_LIVE_DEFAULTS["kalshi"]["market_tickers"][0])
    _MATRIX_COINGECKO_ASSET_ID = str(SOURCE_LIVE_DEFAULTS["coingecko"]["asset_ids"][0])


def matrix_cninfo_symbols() -> tuple[str, ...]:
    _load_matrix_live_defaults()
    assert _MATRIX_CNINFO_SYMBOLS is not None
    return _MATRIX_CNINFO_SYMBOLS


def matrix_alpha_vantage_symbol() -> str:
    _load_matrix_live_defaults()
    assert _MATRIX_ALPHA_VANTAGE_SYMBOL is not None
    return _MATRIX_ALPHA_VANTAGE_SYMBOL


def matrix_kalshi_market_ticker() -> str:
    _load_matrix_live_defaults()
    assert _MATRIX_KALSHI_MARKET_TICKER is not None
    return _MATRIX_KALSHI_MARKET_TICKER


def matrix_coingecko_asset_id() -> str:
    _load_matrix_live_defaults()
    assert _MATRIX_COINGECKO_ASSET_ID is not None
    return _MATRIX_COINGECKO_ASSET_ID


def resolve_matrix_deribit_live_instrument() -> str:
    """Resolve active BTC option via lightweight get_instruments (no full fetch_payload probe)."""
    from backend.app.datasources.fetch_ports.deribit_port import resolve_deribit_live_option_name

    return resolve_deribit_live_option_name(currency="BTC")


MatrixClosureMode = Literal["dry_run", "final_live_authorized"]
ClosureOutcome = Literal["PASS", "FAIL_EXTERNAL", "FAIL_CONTRACT", "FAIL"]


def resolve_matrix_closure_mode(
    *,
    closure_mode: MatrixClosureMode | None = None,
    live_authorized: bool | None = None,
) -> MatrixClosureMode:
    if closure_mode is not None:
        return closure_mode
    if live_authorized is None:
        raise TypeError("evaluate_matrix_row_closure requires closure_mode or live_authorized")
    return "final_live_authorized" if live_authorized else "dry_run"


def build_matrix_preview(
    request: AcceptanceRequest,
    target: AcceptanceMatrixTarget,
    route_payload: dict[str, object],
):
    from backend.app.ops.source_route_db_acceptance import preview_from_route_payload

    return preview_from_route_payload(
        request,
        route_payload,
        missing_prerequisites=missing_gate_errors(target),
    )


def _row_error_text(row: dict[str, object]) -> str:
    errors = row.get("errors") or []
    if not isinstance(errors, list):
        return ""
    return "; ".join(str(item) for item in errors).lower()


def _is_missing_live_authorization_block(error_text: str) -> bool:
    return "live authorization missing" in error_text


def _is_deferred_qualification_block(
    target: AcceptanceMatrixTarget,
    error_text: str,
) -> bool:
    """True when terminal/license is missing on qualification_deferred sources (expected honest BLOCKED)."""
    if target.request.source_id not in QUALIFICATION_DEFERRED_SOURCE_IDS:
        return False
    if _is_missing_live_authorization_block(error_text):
        return False
    for env_name in target.auth_env:
        if f"gate:{env_name.lower()}:missing" in error_text:
            return True
    return False


def classify_matrix_execute_exception(exc: BaseException) -> tuple[str, str]:
    """Map unexpected matrix execute failures to honest contract/implementation classes."""
    from backend.app.datasources.adapters.fetch_port import PortError

    if isinstance(exc, PortError):
        return "FAIL_EXTERNAL", "FAIL"
    if isinstance(exc, (TimeoutError, OSError)):
        return "FAIL_EXTERNAL", "FAIL"
    message = str(exc).lower()
    if "timeout" in message or "timed out" in message:
        return "FAIL_EXTERNAL", "FAIL"
    if "no adapter" in message or "no clean write target" in message:
        return "CONTRACT_VIOLATION", "FAIL"
    if isinstance(exc, (ValueError, KeyError, TypeError, AttributeError)):
        return "CONTRACT_VIOLATION", "FAIL"
    return "CONTRACT_VIOLATION", "FAIL"


def evaluate_matrix_row_closure(
    target: AcceptanceMatrixTarget,
    row: dict[str, object],
    *,
    closure_mode: MatrixClosureMode | None = None,
    live_authorized: bool | None = None,
) -> ClosureOutcome:
    mode = resolve_matrix_closure_mode(
        closure_mode=closure_mode,
        live_authorized=live_authorized,
    )
    failure_class = str(row.get("failure_class", ""))
    status = str(row.get("status", ""))
    write_grade = str(row.get("write_grade", ""))
    error_text = _row_error_text(row)

    if error_text.startswith("matrix execute raised:"):
        classified_failure, _ = classify_matrix_execute_exception(
            RuntimeError(error_text.removeprefix("matrix execute raised:"))
        )
        if classified_failure != "FAIL_EXTERNAL":
            return "FAIL_CONTRACT"
        failure_class = classified_failure

    if failure_class == "CONTRACT_VIOLATION":
        return "FAIL_CONTRACT"
    if failure_class == "NOT_IMPLEMENTED":
        return "FAIL_CONTRACT"

    if mode == "dry_run":
        if failure_class == "BLOCKED" and (
            _is_missing_live_authorization_block(error_text)
            or _is_deferred_qualification_block(target, error_text)
        ):
            return "PASS"
        return "FAIL"

    if failure_class == "BLOCKED":
        if _is_deferred_qualification_block(target, error_text):
            return "PASS"
        return "FAIL"

    if is_non_primary_positioning(target):
        if (
            status == "PASS"
            and failure_class == "NONE"
            and write_grade in {target.expected_write_grade, "blocked", "not_written"}
        ):
            return "PASS"
        if (
            failure_class == "FAIL_EXTERNAL"
            and mode == "final_live_authorized"
            and target.request.source_id in EXTERNAL_DEFERRED_SOURCE_IDS
        ):
            return "PASS"
        return "FAIL"

    if status == "PASS" and failure_class == "NONE":
        return "PASS"
    if failure_class == "FAIL_EXTERNAL":
        if (
            mode == "final_live_authorized"
            and target.request.source_id in EXTERNAL_DEFERRED_SOURCE_IDS
        ):
            return "PASS"
        return "FAIL_EXTERNAL"
    return "FAIL"


def summarize_matrix_closure(
    payload: dict[str, object],
    *,
    closure_mode: MatrixClosureMode | None = None,
    live_authorized: bool | None = None,
    trust_stored_outcomes: bool = False,
) -> dict[str, object]:
    mode = resolve_matrix_closure_mode(
        closure_mode=closure_mode,
        live_authorized=live_authorized,
    )
    payload_mode = payload.get("closure_mode")
    trust_cached = trust_stored_outcomes and payload_mode == mode
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return {
            "closure_status": "FAIL",
            "pass_count": 0,
            "fail_external_count": 0,
            "fail_contract_count": 0,
            "fail_count": 0,
        }

    outcomes: list[ClosureOutcome] = []
    enriched_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            outcomes.append("FAIL")
            continue
        cached = row.get("closure_outcome")
        if trust_cached and isinstance(cached, str) and cached in _CLOSURE_OUTCOMES:
            outcomes.append(cached)  # type: ignore[arg-type]
            enriched_rows.append(dict(row))
            continue
        if not row.get("target"):
            outcomes.append("FAIL")
            continue
        target = find_matrix_target_by_key(str(row["target"]))
        if target is None:
            outcomes.append("FAIL")
            continue
        outcome = evaluate_matrix_row_closure(
            target,
            row,
            closure_mode=mode,
        )
        outcomes.append(outcome)
        enriched = dict(row)
        enriched["closure_outcome"] = outcome
        enriched_rows.append(enriched)

    pass_count = sum(1 for outcome in outcomes if outcome == "PASS")
    fail_external_count = sum(1 for outcome in outcomes if outcome == "FAIL_EXTERNAL")
    fail_contract_count = sum(1 for outcome in outcomes if outcome == "FAIL_CONTRACT")
    fail_count = sum(1 for outcome in outcomes if outcome == "FAIL")
    closure_status = "PASS" if outcomes and all(outcome == "PASS" for outcome in outcomes) else "FAIL"
    return {
        "closure_status": closure_status,
        "pass_count": pass_count,
        "fail_external_count": fail_external_count,
        "fail_contract_count": fail_contract_count,
        "fail_count": fail_count,
        "rows": enriched_rows,
    }


def execute_documented_matrix(
    spine,
    *,
    data_root,
    live_authorized: bool,
) -> dict[str, object]:
    from backend.app.ops.source_route_db_acceptance import _bootstrap_acceptance_db

    closure_mode = resolve_matrix_closure_mode(live_authorized=live_authorized)
    resolved_root = resolve_matrix_data_root(data_root)
    cm = _bootstrap_acceptance_db(resolved_root)
    rows: list[dict[str, object]] = []
    for target in iter_matrix_targets():
        try:
            report = spine.execute(
                target.request,
                data_root=resolved_root,
                live_authorized=live_authorized,
                cm=cm,
                persist_route_evidence=live_authorized,
                skip_data_root_validation=cm is not None,
            )
            row = report.to_dict()
        except Exception as exc:
            from backend.app.datasources.adapters.fetch_port import PortError
            from backend.app.datasources.product_live_gate import ProductLiveGateError

            if not isinstance(
                exc,
                (
                    PortError,
                    ProductLiveGateError,
                    RuntimeError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                    TimeoutError,
                    OSError,
                ),
            ):
                raise
            failure_class, status = classify_matrix_execute_exception(exc)
            row = {
                "source_id": target.request.source_id,
                "data_domain": target.request.data_domain,
                "operation": target.request.operation,
                "status": status,
                "failure_class": failure_class,
                "implementation_mode": "live",
                "errors": [f"matrix execute raised: {exc}"],
            }
        if not live_authorized and row.get("failure_class") == "BLOCKED":
            row["implementation_mode"] = "dry_run"
        row_payload = {
            "target": matrix_target_key(target),
            "display_name": target.display_name,
            "positioning": target.positioning,
            **row,
        }
        row_payload["closure_outcome"] = evaluate_matrix_row_closure(
            target,
            row_payload,
            closure_mode=closure_mode,
        )
        rows.append(row_payload)
    outcomes = [str(row.get("closure_outcome", "FAIL")) for row in rows]
    summary = summarize_matrix_closure(
        {"rows": rows, "closure_mode": closure_mode},
        closure_mode=closure_mode,
        trust_stored_outcomes=True,
    )
    return {
        "matrix_count": len(rows),
        "live_authorized": live_authorized,
        "closure_mode": closure_mode,
        "closure_status": summary["closure_status"],
        "pass_count": summary["pass_count"],
        "fail_external_count": summary["fail_external_count"],
        "fail_contract_count": summary["fail_contract_count"],
        "fail_count": summary["fail_count"],
        "data_root": str(resolved_root),
        "rows": rows,
    }
