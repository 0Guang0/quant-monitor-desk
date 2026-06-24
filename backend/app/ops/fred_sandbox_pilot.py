"""FRED-only authorized sandbox pilot orchestration (B01-FRED)."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.ops.fred_evidence_validator import validate_fred_evidence_health
from backend.app.ops.fred_fetch_ports import create_fred_fetch_port
from backend.app.ops.live_pilot_constants import FRED_PRIMARY_DEFERRED_NOTE

PILOT_ID = "r3e-fred-sandbox-20260625"
DATA_DOMAIN = "macro_series"
OPERATION = "fetch_macro_series"
P0_SERIES_WHITELIST = frozenset({"DGS10", "T10Y3M", "VIXCLS", "SP500", "DFII10"})
MAX_SERIES = 5
MAX_ROWS_PER_SERIES = 100
MAX_NETWORK_CALLS_PER_RUN = 10
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/r3e-fred-sandbox"
DEFAULT_AUTHORIZATION_REL = (
    ".trellis/tasks/round3-fred-authorized-sandbox-pilot/execute-evidence/authorization.yaml"
)


class FredPilotStatus(StrEnum):
    FRED_PILOT_PASS_RAW_ONLY = "FRED_PILOT_PASS_RAW_ONLY"
    FRED_PILOT_PASS_SANDBOX_STAGING = "FRED_PILOT_PASS_SANDBOX_STAGING"
    FRED_PILOT_FAIL_AUTH = "FRED_PILOT_FAIL_AUTH"
    FRED_PILOT_FAIL_NETWORK = "FRED_PILOT_FAIL_NETWORK"
    FRED_PILOT_FAIL_SCHEMA = "FRED_PILOT_FAIL_SCHEMA"
    FRED_PILOT_FAIL_VALIDATION = "FRED_PILOT_FAIL_VALIDATION"
    FRED_PILOT_REDEFERRED = "FRED_PILOT_REDEFERRED"


class FredPilotAuthorizationError(RuntimeError):
    """Authorization evidence missing or invalid."""


class FredPilotSeriesRejectedError(RuntimeError):
    """Series not in P0 whitelist or exceeds caps."""


@dataclass(frozen=True)
class FredPilotRequest:
    series_ids: tuple[str, ...]
    authorization_evidence: str | None = None
    dry_run: bool = True
    skip_live_fetch: bool = True
    max_rows_per_series: int = MAX_ROWS_PER_SERIES
    date_window: str = "3y"
    sandbox_root: Path | None = None
    use_mock_port: bool = True


def _fred_fetch_request(series_id: str) -> FetchRequest:
    return FetchRequest(
        run_id=f"fred-{PILOT_ID}",
        source_id="fred",
        data_domain=DATA_DOMAIN,
        instrument_id=series_id,
    )


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def load_authorization_yaml(path: str | Path) -> dict[str, Any]:
    resolved = _resolve_path(str(path))
    if not resolved.is_file():
        raise FredPilotAuthorizationError(f"authorization evidence missing: {path}")
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    if not payload.get("authorization_present"):
        raise FredPilotAuthorizationError("authorization_present must be true")
    return payload


def validate_series_whitelist(series_ids: Sequence[str]) -> None:
    if len(series_ids) > MAX_SERIES:
        raise FredPilotSeriesRejectedError(
            f"max {MAX_SERIES} series allowed, got {len(series_ids)}"
        )
    unknown = [s for s in series_ids if s not in P0_SERIES_WHITELIST]
    if unknown:
        raise FredPilotSeriesRejectedError(f"series not in P0 whitelist: {unknown}")


def validate_authorization(request: FredPilotRequest) -> dict[str, Any]:
    """Fail-closed authorization gate for live fetch."""
    if request.skip_live_fetch or request.use_mock_port:
        return {"authorization_present": False, "skip_live_fetch": True}
    if not request.authorization_evidence:
        raise FredPilotAuthorizationError("authorization_evidence required for live fetch")
    auth = load_authorization_yaml(request.authorization_evidence)
    if auth.get("source_id") != "fred":
        raise FredPilotAuthorizationError("authorization source_id must be fred")
    if auth.get("allow_production_clean_write"):
        raise FredPilotAuthorizationError("allow_production_clean_write must be false")
    api_env = auth.get("api_key_env") or "FRED_API_KEY"
    if not os.environ.get(api_env):
        raise FredPilotAuthorizationError(f"missing API key env {api_env}")
    return auth


def build_route_preview(request: FredPilotRequest) -> dict[str, Any]:
    """Dry-run route preview for whitelisted FRED series (sandbox/raw-only)."""
    validate_series_whitelist(request.series_ids)
    registry = SourceRegistry()
    registry.load()
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(
        source_registry=registry,
        capability_registry=capabilities,
    )
    plan = planner.plan(
        data_domain=DATA_DOMAIN,
        operation=OPERATION,
        run_id=f"fred-preview-{PILOT_ID}",
        job_id="fred-route-preview",
        extra_candidates=[("fred", "Primary")],
    )
    fred_candidate = next((c for c in plan.candidates if c.source_id == "fred"), None)
    return {
        "pilot_id": PILOT_ID,
        "data_domain": DATA_DOMAIN,
        "operation": OPERATION,
        "series_ids": list(request.series_ids),
        "dry_run": request.dry_run,
        "write_target": "sandbox",
        "production_clean_write": False,
        "route_status": plan.route_status,
        "selected_source_id": plan.selected_source_id,
        "fred_candidate": None
        if fred_candidate is None
        else {
            "source_id": fred_candidate.source_id,
            "enabled": fred_candidate.enabled,
            "disabled_reason": fred_candidate.disabled_reason,
            "skip_reason": fred_candidate.skip_reason,
        },
        "sandbox_only": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
    }


def _content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def run_mock_fetch(request: FredPilotRequest) -> dict[str, Any]:
    """Mocked FRED fetch producing raw manifest with hash and fetch_id."""
    validate_series_whitelist(request.series_ids)
    if request.max_rows_per_series <= 0 or request.max_rows_per_series > MAX_ROWS_PER_SERIES:
        raise FredPilotSeriesRejectedError(
            f"max_rows_per_series must be 1..{MAX_ROWS_PER_SERIES}"
        )

    port = create_fred_fetch_port(
        series_ids=request.series_ids,
        max_rows=request.max_rows_per_series,
        date_window=request.date_window,
        use_mock=True,
    )
    series_manifest: list[dict[str, Any]] = []
    network_calls = 0
    for series_id in request.series_ids:
        if network_calls >= MAX_NETWORK_CALLS_PER_RUN:
            break
        network_calls += 1
        try:
            payload = port.fetch_payload(_fred_fetch_request(series_id))
        except PortError as exc:
            status = FredPilotStatus.FRED_PILOT_FAIL_NETWORK
            if "schema" in str(exc).lower():
                status = FredPilotStatus.FRED_PILOT_FAIL_SCHEMA
            return {
                "pilot_id": PILOT_ID,
                "status": status,
                "error": str(exc),
                "series": [],
            }
        body = json.loads(payload.content.decode("utf-8"))
        content_hash = _content_hash(payload.content)
        if not body.get("source_fetch_id"):
            return {
                "pilot_id": PILOT_ID,
                "status": FredPilotStatus.FRED_PILOT_FAIL_SCHEMA,
                "error": "missing source_fetch_id",
                "series": [],
            }
        rows = body.get("rows") or []
        for row in rows:
            row.setdefault("series_id", series_id)
        series_manifest.append(
            {
                "series_id": series_id,
                "source_fetch_id": body["source_fetch_id"],
                "content_hash": content_hash,
                "as_of_timestamp": body.get("as_of_timestamp"),
                "retrieved_at": body.get("retrieved_at"),
                "rows": rows,
            }
        )

    manifest = {
        "pilot_id": PILOT_ID,
        "status": FredPilotStatus.FRED_PILOT_PASS_RAW_ONLY,
        "source_id": "fred",
        "data_domain": DATA_DOMAIN,
        "operation": OPERATION,
        "dry_run": request.dry_run,
        "write_target": "sandbox",
        "production_clean_write": False,
        "network_calls": network_calls,
        "series": series_manifest,
    }
    sandbox = request.sandbox_root or DEFAULT_SANDBOX_ROOT
    sandbox.mkdir(parents=True, exist_ok=True)
    out_path = sandbox / "fred_raw_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        manifest["manifest_path"] = str(out_path.relative_to(PROJECT_ROOT))
    except ValueError:
        manifest["manifest_path"] = str(out_path)
    return manifest


def run_live_fetch(request: FredPilotRequest) -> dict[str, Any]:
    """Authorized live FRED fetch (opt-in)."""
    try:
        auth = validate_authorization(request)
    except FredPilotAuthorizationError as exc:
        return {
            "pilot_id": PILOT_ID,
            "status": FredPilotStatus.FRED_PILOT_FAIL_AUTH,
            "error": str(exc),
        }

    validate_series_whitelist(request.series_ids)
    port = create_fred_fetch_port(
        series_ids=request.series_ids,
        max_rows=min(request.max_rows_per_series, auth.get("max_rows", MAX_ROWS_PER_SERIES)),
        date_window=str(auth.get("window") or request.date_window),
        use_mock=False,
    )
    series_manifest: list[dict[str, Any]] = []
    max_calls = int(auth.get("max_calls") or MAX_NETWORK_CALLS_PER_RUN)
    network_calls = 0
    for series_id in request.series_ids:
        if network_calls >= max_calls:
            break
        network_calls += 1
        try:
            payload = port.fetch_payload(_fred_fetch_request(series_id))
        except PortError as exc:
            code = str(exc)
            status = FredPilotStatus.FRED_PILOT_FAIL_NETWORK
            if "FRED_API_KEY" in code or "auth" in code.lower():
                status = FredPilotStatus.FRED_PILOT_FAIL_AUTH
            return {
                "pilot_id": PILOT_ID,
                "status": status,
                "error": code,
                "authorized": True,
            }
        body = json.loads(payload.content.decode("utf-8"))
        series_manifest.append(
            {
                "series_id": series_id,
                "source_fetch_id": body["source_fetch_id"],
                "content_hash": _content_hash(payload.content),
                "as_of_timestamp": body.get("as_of_timestamp"),
                "retrieved_at": body.get("retrieved_at"),
                "rows": body.get("rows") or [],
            }
        )

    result = {
        "pilot_id": PILOT_ID,
        "status": FredPilotStatus.FRED_PILOT_PASS_SANDBOX_STAGING,
        "source_id": "fred",
        "authorized": True,
        "network_calls": network_calls,
        "production_clean_write": False,
        "series": series_manifest,
    }
    sandbox = request.sandbox_root or DEFAULT_SANDBOX_ROOT
    sandbox.mkdir(parents=True, exist_ok=True)
    evidence_path = sandbox / "fred_live_fetch_evidence.json"
    evidence_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        result["evidence_path"] = str(evidence_path.relative_to(PROJECT_ROOT))
    except ValueError:
        result["evidence_path"] = str(evidence_path)
    return result


def build_pilot_status_report(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return {"pilot_id": PILOT_ID, "scenarios": scenarios}


def build_pilot_closeout(*, manifest: dict[str, Any], health: dict[str, Any]) -> dict[str, Any]:
    """B2.5-O-05 closeout — FRED-only evidence required; macro cannot close."""
    has_fred_evidence = manifest.get("source_id") == "fred" and bool(manifest.get("series"))
    health_ok = health.get("status") in {"PASS", "WARN"}
    b250_close = False
    decision = "RE-DEFERRED"
    if has_fred_evidence and health_ok:
        decision = "FRED_SANDBOX_EVIDENCE_RECORDED"
    return {
        "pilot_id": PILOT_ID,
        "b2_5_o_05_decision": decision,
        "b2_5_o_05_closed": b250_close,
        "fred_only_evidence": has_fred_evidence,
        "macro_supplementary_cannot_close": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        "health_status": health.get("status"),
        "production_live_claim": False,
    }


def run_failure_scenario(scenario: str, request: FredPilotRequest | None = None) -> dict[str, Any]:
    """Explicit failure taxonomy for pilot evidence."""
    req = request or FredPilotRequest(series_ids=("DGS10",))
    if scenario == "missing_auth":
        live_req = FredPilotRequest(
            series_ids=req.series_ids,
            skip_live_fetch=False,
            use_mock_port=False,
            authorization_evidence=None,
        )
        return run_live_fetch(live_req)
    if scenario == "network":
        return {
            "pilot_id": PILOT_ID,
            "status": FredPilotStatus.FRED_PILOT_FAIL_NETWORK,
            "error": "simulated network failure",
        }
    if scenario == "schema":
        return {
            "pilot_id": PILOT_ID,
            "status": FredPilotStatus.FRED_PILOT_FAIL_SCHEMA,
            "error": "missing required manifest fields",
        }
    if scenario == "validation":
        bad_manifest = {"series": [{"series_id": "DGS10", "rows": [{"value": "not-a-number"}]}]}
        health = validate_fred_evidence_health(bad_manifest)
        return {
            "pilot_id": PILOT_ID,
            "status": FredPilotStatus.FRED_PILOT_FAIL_VALIDATION,
            "health": health,
        }
    return {
        "pilot_id": PILOT_ID,
        "status": FredPilotStatus.FRED_PILOT_REDEFERRED,
        "error": f"unknown scenario {scenario!r}",
    }
