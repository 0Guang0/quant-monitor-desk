"""Fail-closed authorization gate for 018C TDX live manual probe (not Batch 2.75 live_pilot)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from backend.app.config import PROJECT_ROOT

AUTHORIZATION_FILENAME_RE = re.compile(
    r"^tdx_pytdx_live_manual_probe_authorization_\d{4}-\d{2}-\d{2}\.md$"
)

# Must match authorization_checklist.md §4 and live_manual_probe_plan.md §4
APPROVED_PROBE_ENVELOPES: frozenset[tuple[str, str, str, tuple[str, ...], str, int]] = frozenset(
    {
        (
            "tdx_pytdx",
            "security_list",
            "fetch_security_list",
            ("sh",),
            "max_rows=20 per market",
            20,
        ),
        (
            "tdx_pytdx",
            "cn_equity_daily_bar",
            "fetch_daily_bar",
            ("sh.600519",),
            "recent 5 trading days",
            3,
        ),
        (
            "tdx_pytdx",
            "cn_index_daily_bar",
            "fetch_index_daily_bar",
            ("000001.SH",),
            "recent 5 trading days",
            3,
        ),
    }
)

MAX_TOTAL_ROWS = 40
MAX_POLICY_ROW_CAP = 100

REQUIRED_PHRASE_MARKERS = (
    "tdx_pytdx live manual probe",
    "tdx_pytdx_live_manual_probe_authorization_",
    "R3-B2.75-REQ2-EM",
)

FORBIDDEN_LIVE_ENTRYPOINTS = frozenset(
    {
        "backend.app.ops.interface_probe.run_interface_probe",
        "backend.app.ops.interface_probe_fetch_ports.TdxPytdxProbeFetchPort",
        "backend.app.datasources.fetch_ports.tdx_pytdx_port.TdxPytdxFetchPort",
    }
)


def assert_live_entrypoint_not_forbidden(caller_fqn: str) -> None:
    """Reject direct live invocation from forbidden entrypoints (R3FR-03 §9.4)."""
    if caller_fqn in FORBIDDEN_LIVE_ENTRYPOINTS:
        raise TdxLiveManualProbeAuthorizationError(
            f"forbidden live entrypoint: {caller_fqn}; "
            "use run_tdx_live_manual_probe after gate authorization"
        )


class TdxLiveManualProbeAuthorizationError(RuntimeError):
    """Raised when TDX live manual probe authorization fails fail-closed gate."""


@dataclass(frozen=True)
class TdxLiveManualProbeRequest:
    source_id: str
    data_domain: str
    operation: str
    symbols_or_markets: tuple[str, ...]
    date_window: str
    max_rows: int
    authorization_evidence: str
    tdx_host: str
    tdx_port: int
    authorized_session_id: str
    raw_only: bool = True
    write_target: str = "sandbox"
    allow_clean_write: bool = False


def _resolve_authorization_path(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def validate_tdx_live_manual_probe_authorization(request: TdxLiveManualProbeRequest) -> None:
    """Fail-closed gate — must pass before any TDX HQ network connect.

    Do **not** call ``live_pilot.validate_authorization``; Batch 2.75 triples differ.
    """
    auth_path = _resolve_authorization_path(request.authorization_evidence)
    if not auth_path.is_file():
        raise TdxLiveManualProbeAuthorizationError(
            f"authorization evidence missing: {request.authorization_evidence}"
        )
    if not AUTHORIZATION_FILENAME_RE.match(auth_path.name):
        raise TdxLiveManualProbeAuthorizationError(
            f"authorization filename must match tdx_pytdx_live_manual_probe_authorization_YYYY-MM-DD.md: "
            f"{auth_path.name}"
        )

    auth_text = auth_path.read_text(encoding="utf-8")
    lowered = auth_text.lower()
    for marker in REQUIRED_PHRASE_MARKERS:
        if marker.lower() not in lowered and marker not in auth_text:
            raise TdxLiveManualProbeAuthorizationError(
                f"authorization evidence missing required marker: {marker!r}"
            )

    if "live_manual_probe_plan.md" not in auth_text:
        raise TdxLiveManualProbeAuthorizationError(
            "authorization evidence must cite live_manual_probe_plan.md"
        )

    if f"authorized_session_id: {request.authorized_session_id}" not in auth_text:
        raise TdxLiveManualProbeAuthorizationError(
            "authorization evidence authorized_session_id does not match request"
        )

    if request.source_id != "tdx_pytdx":
        raise TdxLiveManualProbeAuthorizationError("source_id must be tdx_pytdx")

    envelope = (
        request.source_id,
        request.data_domain,
        request.operation,
        request.symbols_or_markets,
        request.date_window,
        request.max_rows,
    )
    if envelope not in APPROVED_PROBE_ENVELOPES:
        raise TdxLiveManualProbeAuthorizationError(
            f"request envelope {envelope!r} not in approved TDX live manual probe set"
        )

    if not request.raw_only:
        raise TdxLiveManualProbeAuthorizationError("first live pass requires raw_only=true")
    if request.write_target != "sandbox":
        raise TdxLiveManualProbeAuthorizationError("write_target must be sandbox")
    if request.allow_clean_write:
        raise TdxLiveManualProbeAuthorizationError("allow_clean_write must be false")
    if request.max_rows <= 0 or request.max_rows > MAX_POLICY_ROW_CAP:
        raise TdxLiveManualProbeAuthorizationError(
            f"max_rows must be in 1..{MAX_POLICY_ROW_CAP}, got {request.max_rows}"
        )

    validate_runtime_host_port_matches_authorization(
        auth_text, host=request.tdx_host, port=request.tdx_port
    )


def validate_runtime_host_port_matches_authorization(
    auth_text: str,
    *,
    host: str,
    port: int,
) -> None:
    host_line = f"| {host} | {port} |"
    if host_line not in auth_text and f"| {host} | {port}|" not in auth_text.replace(" ", ""):
        # tolerate markdown table with spaces
        pattern = re.compile(
            rf"\|\s*{re.escape(host)}\s*\|\s*{port}\s*\|",
            re.IGNORECASE,
        )
        if not pattern.search(auth_text):
            raise TdxLiveManualProbeAuthorizationError(
                f"runtime host/port {host}:{port} not recorded in authorization file table"
            )


def parse_index_instrument(instrument_id: str) -> tuple[int, str]:
    """Map QMD index id (e.g. 000001.SH) to pytdx (market, code)."""
    normalized = instrument_id.strip().upper()
    if normalized.endswith(".SH"):
        return 1, normalized[:-3]
    if normalized.endswith(".SZ"):
        return 0, normalized[:-3]
    raise ValueError(f"unsupported index instrument_id: {instrument_id!r}")
