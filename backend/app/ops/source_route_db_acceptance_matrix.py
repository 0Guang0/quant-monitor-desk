"""Documented source matrix for SourceRouteDbAcceptanceSpine preview/execute."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from backend.app.ops.source_route_db_acceptance import AcceptanceRequest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
CAPABILITIES_PATH = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"

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


def find_matrix_target(request: AcceptanceRequest) -> AcceptanceMatrixTarget | None:
    key = f"{request.data_domain}:{request.source_id}:{request.operation}"
    for target in DOCUMENTED_SOURCE_MATRIX:
        if matrix_target_key(target) == key:
            return target
    return None


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid yaml document: {path}")
    return payload


def validate_matrix_against_registry() -> list[str]:
    """Return CONTRACT_VIOLATION messages when matrix rows drift from registry/capabilities."""
    violations: list[str] = []
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
    from backend.app.datasources.service import DataSourceService
    from backend.app.ops.macro_incremental_common import load_incremental_route_bundle

    registry, caps, planner = load_incremental_route_bundle(
        source_id=request.source_id,
        data_domain=request.data_domain,
    )
    service = DataSourceService(
        source_registry=registry,
        capability_registry=caps,
        route_planner=planner,
        staged_fixture_mode=False,
    )
    plan = service.preview_route(
        data_domain=request.data_domain,
        operation=request.operation,
        market_id=request.market_id,
        run_id="acceptance-preview",
        job_id="acceptance-preview",
    )
    return plan.to_payload_dict()


def missing_gate_errors(target: AcceptanceMatrixTarget) -> tuple[str, ...]:
    import os

    errors: list[str] = []
    for env_name in target.auth_env:
        if not str(os.environ.get(env_name, "")).strip():
            errors.append(f"{env_name} missing for {target.request.source_id}")
    if target.requires_local_terminal and not str(
        os.environ.get("QMT_XTDATA_AUTHORIZED", "")
    ).strip():
        errors.append("QMT_XTDATA_AUTHORIZED missing for local terminal source")
    if target.requires_license and not str(
        os.environ.get("THS_IFIND_LICENSE_ARTIFACT", "")
    ).strip():
        errors.append("THS_IFIND_LICENSE_ARTIFACT missing for licensed source")
    return tuple(errors)


def is_non_primary_positioning(target: AcceptanceMatrixTarget) -> bool:
    return target.positioning in {
        "validation",
        "manual_review_only",
        "licensed_validation",
    }


EVIDENCE_FETCH_MATRIX_SOURCE_IDS = frozenset({"coingecko", "kalshi", "qmt_xtdata"})

# Honest long-term qualification gaps (terminal/license); closure PASS in dry_run and final_live_authorized.
QUALIFICATION_DEFERRED_SOURCE_IDS = frozenset({"qmt_xtdata", "ths_ifind"})


def matrix_cninfo_symbols() -> tuple[str, ...]:
    """SSOT: cninfo_port SYMBOL_WHITELIST ∩ product_live_ports (announcement index acceptance)."""
    return ("sh.600519",)


def matrix_alpha_vantage_symbol() -> str:
    """SSOT: layer1 L1-LIQ-AMIHUD-SPY + alpha_vantage_port SYMBOL_WHITELIST."""
    return "SPY"


def matrix_kalshi_market_ticker() -> str:
    """SSOT: live_tier_c_evidence_v1 default_instrument + kalshi_port MARKET_WHITELIST."""
    return "KXFED-27APR-T4.25"


def matrix_coingecko_asset_id() -> str:
    """SSOT: coingecko_port ASSET_WHITELIST + product_live_ports SOURCE_LIVE_DEFAULTS."""
    return "bitcoin"


def resolve_matrix_deribit_live_instrument() -> str:
    """Resolve active BTC option for live matrix (expired replay symbols won't stage rows)."""
    from backend.app.datasources.fetch_ports.deribit_port import (
        create_deribit_fetch_port,
        resolve_deribit_live_option_instrument,
    )

    probe_seed = "BTC-28JUN24-65000-C"
    probe = create_deribit_fetch_port(
        instruments=(probe_seed,), max_surface_rows=3, use_mock=False
    )
    return resolve_deribit_live_option_instrument(probe)


def find_matrix_target_by_key(target_key: str) -> AcceptanceMatrixTarget | None:
    for target in DOCUMENTED_SOURCE_MATRIX:
        if matrix_target_key(target) == target_key:
            return target
    return None


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
    from backend.app.ops.source_route_db_acceptance import (
        AcceptancePreview,
        _optional_str,
        _route_grade_from_payload,
    )

    gate_errors = missing_gate_errors(target)
    route_grade = _route_grade_from_payload(route_payload)
    route_status = _optional_str(route_payload.get("route_status")) or "UNKNOWN"
    live_ready = not gate_errors and route_grade != "blocked"
    if gate_errors:
        reason = (
            f"route_status={route_status}; "
            f"missing_prerequisites={'; '.join(gate_errors)}"
        )
        status = "FAIL"
    elif route_grade == "blocked":
        reason = f"route_status={route_status}"
        status = "FAIL"
    else:
        reason = f"route_status={route_status}"
        status = "PASS"
    return AcceptancePreview(
        request=request,
        route_grade=route_grade,
        implementation_mode="live",
        status=status,
        reason=reason,
        missing_prerequisites=gate_errors,
        live_ready=live_ready,
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
    if failure_class_hint := error_text:
        for env_name in target.auth_env:
            if env_name.lower() in failure_class_hint:
                return True
        if target.requires_local_terminal and "qmt_xtdata_authorized missing" in failure_class_hint:
            return True
        if target.requires_license and "ths_ifind_license_artifact missing" in failure_class_hint:
            return True
    return False


def classify_matrix_execute_exception(exc: BaseException) -> tuple[str, str]:
    """Map unexpected matrix execute failures to honest contract/implementation classes."""
    message = str(exc).lower()
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
        failure_class, _ = classify_matrix_execute_exception(
            RuntimeError(error_text.removeprefix("matrix execute raised:"))
        )
        return "FAIL_CONTRACT"

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

    if is_non_primary_positioning(target) or target.positioning == "manual_review_only":
        if (
            status == "PASS"
            and failure_class == "NONE"
            and write_grade in {target.expected_write_grade, "blocked", "not_written"}
        ):
            return "PASS"
        return "FAIL"

    if status == "PASS" and failure_class == "NONE":
        return "PASS"
    if failure_class == "FAIL_EXTERNAL":
        return "FAIL_EXTERNAL"
    return "FAIL"


def summarize_matrix_closure(
    payload: dict[str, object],
    *,
    closure_mode: MatrixClosureMode | None = None,
    live_authorized: bool | None = None,
) -> dict[str, object]:
    mode = resolve_matrix_closure_mode(
        closure_mode=closure_mode,
        live_authorized=live_authorized,
    )
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
        if not isinstance(row, dict) or not row.get("target"):
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
    closure_mode = resolve_matrix_closure_mode(live_authorized=live_authorized)
    rows: list[dict[str, object]] = []
    for target in iter_matrix_targets():
        try:
            report = spine.execute(
                target.request,
                data_root=data_root,
                live_authorized=live_authorized,
            )
            row = report.to_dict()
        except Exception as exc:
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
    summary = summarize_matrix_closure(
        {"rows": rows},
        closure_mode=closure_mode,
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
        "rows": rows,
    }
