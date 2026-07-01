"""TDX manual probe — mocked CI path + opt-in live path (Batch 01 B01-TDX).

Probe orchestration only. TDX fetch implementation lives in
``TdxPytdxFetchPort`` (R3FR-03); ``TdxPytdxProbeFetchPort`` in
``interface_probe_fetch_ports`` is the thin delegate boundary.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload, FetchPort, PortError
from backend.app.datasources.adapters.tdx_pytdx import (
    build_equity_bar_manifest,
    build_index_bar_manifest,
    build_security_list_manifest,
)
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.interface_probe import capture_no_mutation_proof
from backend.app.ops.interface_probe_fetch_ports import TdxPytdxProbeFetchPort, content_hash_bytes
from backend.app.ops.tdx_live_manual_probe_gate import (
    MAX_TOTAL_ROWS,
    TdxLiveManualProbeAuthorizationError,
    TdxLiveManualProbeRequest,
    issue_tdx_live_authorization_after_gate,
    validate_tdx_live_manual_probe_authorization,
)
from backend.app.storage.raw_store import RawStore

DEFAULT_AUTH_PATH = (
    PROJECT_ROOT / "docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md"
)
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/tdx-pytdx-live-manual-probe"
DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / ".trellis/tasks/archive/2026-07/round3-tdx-manual-probe/execute-evidence"
DEFAULT_PRODUCTION_DB = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"

SECURITY_LIST_CAP = 20
EQUITY_INDEX_CAP = 3
MAX_NETWORK_CALLS = 5

TDX_PROBE_PASS_RAW_ONLY = "TDX_PROBE_PASS_RAW_ONLY"
TDX_PROBE_FAIL_AUTH_MISSING = "TDX_PROBE_FAIL_AUTH_MISSING"
TDX_PROBE_FAIL_DEPENDENCY = "TDX_PROBE_FAIL_DEPENDENCY"
TDX_PROBE_FAIL_NETWORK = "TDX_PROBE_FAIL_NETWORK"
TDX_PROBE_FAIL_SCHEMA = "TDX_PROBE_FAIL_SCHEMA"
TDX_PROBE_FAIL_VALIDATION = "TDX_PROBE_FAIL_VALIDATION"
TDX_PROBE_REJECTED = "TDX_PROBE_REJECTED"
TDX_PROBE_REDEFERRED = "TDX_PROBE_REDEFERRED"

OPEN_REGISTRY_ROWS = frozenset({"R3-B2.75-REQ2-EM", "R3-PROMPT14-AKSHARE-VAL-01"})


@dataclass(frozen=True)
class TdxProbeTarget:
    probe_id: str
    data_domain: str
    operation: str
    vendor_api: str
    instrument_id: str
    window_label: str
    max_rows: int


TDX_PROBE_TARGETS: tuple[TdxProbeTarget, ...] = (
    TdxProbeTarget(
        "probe-tdx-equity-daily",
        "cn_equity_daily_bar",
        "fetch_daily_bar",
        "pytdx.get_security_bars",
        "sh.600519",
        "recent 5 trading days",
        EQUITY_INDEX_CAP,
    ),
    TdxProbeTarget(
        "probe-tdx-index-daily",
        "cn_index_daily_bar",
        "fetch_index_daily_bar",
        "pytdx.get_index_bars",
        "000001.SH",
        "recent 5 trading days",
        EQUITY_INDEX_CAP,
    ),
    TdxProbeTarget(
        "probe-tdx-security-list",
        "security_list",
        "fetch_security_list",
        "pytdx.get_security_list",
        "sh",
        "max_rows=20 per market",
        SECURITY_LIST_CAP,
    ),
)

_MOCK_EQUITY_ROWS = [
    {
        "datetime": "2026-06-18",
        "open": 1400.0,
        "high": 1410.0,
        "low": 1395.0,
        "close": 1405.0,
        "vol": 1200000,
        "amount": 1686000000.0,
    },
    {
        "datetime": "2026-06-19",
        "open": 1405.0,
        "high": 1415.0,
        "low": 1400.0,
        "close": 1410.0,
        "vol": 1100000,
        "amount": 1551000000.0,
    },
]

_MOCK_INDEX_ROWS = [
    {
        "datetime": "2026-06-18",
        "open": 3050.0,
        "high": 3060.0,
        "low": 3040.0,
        "close": 3055.0,
        "vol": 250000000,
        "amount": 0.0,
    },
]

_MOCK_SECURITY_ROWS = [
    {"code": "600519", "name": "贵州茅台", "volunit": 100, "decimal_point": 2},
    {"code": "600036", "name": "招商银行", "volunit": 100, "decimal_point": 2},
]


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_fetch_id() -> str:
    return f"tdx-probe-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class MockTdxEquityDailyFetchPort:
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        symbol = req.instrument_id or "sh.600519"
        rows = _MOCK_EQUITY_ROWS[-self.max_rows :]
        manifest = build_equity_bar_manifest(symbol, rows)
        content = json.dumps(manifest, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(rows))


@dataclass(frozen=True)
class MockTdxIndexDailyFetchPort:
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        symbol = req.instrument_id or "000001.SH"
        rows = _MOCK_INDEX_ROWS[-self.max_rows :]
        manifest = build_index_bar_manifest(symbol, rows)
        content = json.dumps(manifest, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(rows))


@dataclass(frozen=True)
class MockTdxSecurityListFetchPort:
    max_rows: int
    requested_rows: int | None = None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        market = req.instrument_id or "sh"
        cap = min(self.max_rows, SECURITY_LIST_CAP)
        if self.requested_rows is not None and self.requested_rows > SECURITY_LIST_CAP:
            raise PortError(
                "FAILED",
                f"security_list requested_rows={self.requested_rows} "
                f"exceeds cap={SECURITY_LIST_CAP}",
            )
        rows = _MOCK_SECURITY_ROWS[:cap]
        manifest = build_security_list_manifest(market, rows)
        content = json.dumps(manifest, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(rows))


def _resolve_mock_port(target: TdxProbeTarget, *, requested_rows: int | None = None) -> FetchPort:
    if target.operation == "fetch_daily_bar":
        return MockTdxEquityDailyFetchPort(target.max_rows)
    if target.operation == "fetch_index_daily_bar":
        return MockTdxIndexDailyFetchPort(target.max_rows)
    if target.operation == "fetch_security_list":
        return MockTdxSecurityListFetchPort(target.max_rows, requested_rows=requested_rows)
    raise ValueError(f"unsupported mock operation: {target.operation}")


def _resolve_live_port(
    target: TdxProbeTarget,
    *,
    host: str,
    port: int,
    authorization_evidence: Path,
    authorized_session_id: str,
    remaining_network_calls: int | None = None,
) -> FetchPort:
    request = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain=target.data_domain,
        operation=target.operation,
        symbols_or_markets=(target.instrument_id,),
        date_window=target.window_label,
        max_rows=target.max_rows,
        authorization_evidence=str(authorization_evidence),
        tdx_host=host,
        tdx_port=port,
        authorized_session_id=authorized_session_id,
    )
    authorization = issue_tdx_live_authorization_after_gate(request)
    return TdxPytdxProbeFetchPort(
        (target.instrument_id,),
        target.max_rows,
        host=host,
        port=port,
        authorization=authorization,
        remaining_network_calls=remaining_network_calls,
    )


def _port_error_to_probe_status(exc: PortError) -> str:
    if exc.status == "USER_AUTH_REQUIRED":
        return TDX_PROBE_FAIL_AUTH_MISSING
    if exc.status == "DISABLED_SOURCE":
        return TDX_PROBE_FAIL_DEPENDENCY
    if exc.status == "NETWORK_ERROR":
        return TDX_PROBE_FAIL_NETWORK
    if exc.status == "EMPTY_RESPONSE":
        return TDX_PROBE_FAIL_SCHEMA
    if "exceeds cap" in exc.message:
        return TDX_PROBE_FAIL_VALIDATION
    return TDX_PROBE_REJECTED


def _run_single_probe(
    target: TdxProbeTarget,
    *,
    sandbox_root: Path,
    fetch_port: FetchPort,
    upstream: str,
    live: bool,
) -> dict[str, Any]:
    fetch_id = _new_fetch_id()
    req = FetchRequest(
        run_id=f"tdx-{target.probe_id}",
        source_id="tdx_pytdx",
        data_domain=target.data_domain,
        instrument_id=target.instrument_id,
        market_id="cn",
        end_time=datetime.now(UTC).date().isoformat(),
    )
    record: dict[str, Any] = {
        "probe_id": target.probe_id,
        "source_id": "tdx_pytdx",
        "operation": target.operation,
        "vendor_api": target.vendor_api,
        "upstream": upstream,
        "source_fetch_id": fetch_id,
        "params": {
            "instrument_id": target.instrument_id,
            "window_label": target.window_label,
            "max_rows": target.max_rows,
            "raw_only": True,
            "write_target": "sandbox",
            "allow_clean_write": False,
            "live": live,
        },
        "timestamp": _utc_now_iso(),
        "as_of": datetime.now(UTC).date().isoformat(),
        "status": TDX_PROBE_REDEFERRED,
    }
    try:
        payload = fetch_port.fetch_payload(req)
    except PortError as exc:
        record.update(
            {
                "status": _port_error_to_probe_status(exc),
                "failure_reason": exc.message,
                "port_status": exc.status,
            }
        )
        return record

    sandbox_root.mkdir(parents=True, exist_ok=True)
    saved = RawStore(sandbox_root).save(
        payload.content,
        source="tdx_pytdx",
        data_domain=target.data_domain,
        file_type=payload.file_type,
        as_of=datetime.now(UTC).date().isoformat(),
    )
    record.update(
        {
            "status": TDX_PROBE_PASS_RAW_ONLY,
            "row_count": payload.row_count,
            "content_hash": content_hash_bytes(payload.content),
            "sandbox_path": saved.local_path,
            "failure_reason": None,
            "retrieved_at": _utc_now_iso(),
        }
    )
    return record


def _check_live_authorization(
    *,
    authorization_evidence: Path,
    tdx_host: str,
    tdx_port: int,
    authorized_session_id: str,
) -> str | None:
    """Return probe status if auth blocks live; None if auth passes."""
    if not authorization_evidence.is_file():
        return TDX_PROBE_FAIL_AUTH_MISSING
    sample = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=EQUITY_INDEX_CAP,
        authorization_evidence=str(authorization_evidence),
        tdx_host=tdx_host,
        tdx_port=tdx_port,
        authorized_session_id=authorized_session_id,
    )
    try:
        validate_tdx_live_manual_probe_authorization(sample)
    except TdxLiveManualProbeAuthorizationError as exc:
        msg = str(exc).lower()
        if "missing" in msg:
            return TDX_PROBE_FAIL_AUTH_MISSING
        if "host/port" in msg or "session" in msg:
            return TDX_PROBE_REDEFERRED
        return TDX_PROBE_FAIL_AUTH_MISSING
    return None


def build_comparison_report(raw_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare TDX mock samples against baostock/akshare reference shapes (no network)."""
    equity = next(
        (r for r in raw_records if r.get("operation") == "fetch_daily_bar"),
        None,
    )
    sections: list[dict[str, Any]] = []
    if equity and equity.get("status") == TDX_PROBE_PASS_RAW_ONLY:
        sections.append(
            {
                "domain": "cn_equity_daily_bar",
                "symbol": "sh.600519",
                "tdx_status": equity["status"],
                "baostock": "missing_comparison_source",
                "akshare": "missing_comparison_source",
                "verdict": "comparable_fields_pending_reference",
                "notes": "TDX raw evidence captured; baostock/akshare not fetched in mocked probe",
            }
        )
    else:
        sections.append(
            {
                "domain": "cn_equity_daily_bar",
                "verdict": "missing_tdx_evidence",
            }
        )
    index_row = next(
        (r for r in raw_records if r.get("operation") == "fetch_index_daily_bar"),
        None,
    )
    if index_row and index_row.get("status") == TDX_PROBE_PASS_RAW_ONLY:
        sections.append(
            {
                "domain": "cn_index_daily_bar",
                "symbol": "000001.SH",
                "tdx_status": index_row["status"],
                "verdict": "comparable_fields_pending_reference",
            }
        )
    else:
        sections.append(
            {
                "domain": "cn_index_daily_bar",
                "verdict": "missing_tdx_evidence",
            }
        )
    list_row = next(
        (r for r in raw_records if r.get("operation") == "fetch_security_list"),
        None,
    )
    if list_row and list_row.get("status") == TDX_PROBE_PASS_RAW_ONLY:
        sections.append(
            {
                "domain": "security_list",
                "market": "sh",
                "tdx_status": list_row["status"],
                "verdict": "comparable_fields_pending_reference",
            }
        )
    else:
        sections.append(
            {
                "domain": "security_list",
                "verdict": "missing_tdx_evidence",
            }
        )
    conflicts = [s for s in sections if s.get("verdict") == "conflict"]
    missing = [s for s in sections if s.get("verdict", "").startswith("missing")]
    comparable = [s for s in sections if s.get("verdict", "").startswith("comparable")]
    return {
        "generated_at": _utc_now_iso(),
        "comparable": comparable,
        "missing": missing,
        "conflicts": conflicts,
        "sections": sections,
        "does_not_auto_overwrite_baostock_or_akshare": True,
    }


def decide_registry_closeout(
    raw_records: list[dict[str, Any]],
    *,
    live_attempted: bool,
    overall_status: str,
) -> dict[str, Any]:
    mocked_ok = all(
        r.get("status") == TDX_PROBE_PASS_RAW_ONLY
        for r in raw_records
        if not live_attempted or r.get("params", {}).get("live") is False
    )
    tdx_decision = (
        "PROBE_PASS_RAW_ONLY"
        if mocked_ok and overall_status == TDX_PROBE_PASS_RAW_ONLY
        else "PROBE_REDEFERRED"
    )
    if overall_status == TDX_PROBE_FAIL_AUTH_MISSING and live_attempted:
        tdx_decision = "PROBE_REDEFERRED"
    return {
        "generated_at": _utc_now_iso(),
        "tdx_pytdx": tdx_decision,
        "tdx_pytdx_live_probe": "PROBE_REDEFERRED" if not live_attempted else tdx_decision,
        "registry_rows_must_remain_open": sorted(OPEN_REGISTRY_ROWS),
        "does_not_close_R3-B2.75-REQ2-EM": True,
        "does_not_close_R3-PROMPT14-AKSHARE-VAL-01": True,
        "overall_probe_status": overall_status,
        "validation_only_preserved": True,
        "enabled_by_default": False,
    }


def _aggregate_status(records: list[dict[str, Any]], *, live: bool) -> str:
    if not records:
        return TDX_PROBE_REDEFERRED
    statuses = {r["status"] for r in records}
    if TDX_PROBE_FAIL_AUTH_MISSING in statuses:
        return TDX_PROBE_FAIL_AUTH_MISSING
    if all(s == TDX_PROBE_PASS_RAW_ONLY for s in statuses):
        return TDX_PROBE_PASS_RAW_ONLY
    if live and TDX_PROBE_REDEFERRED in statuses:
        return TDX_PROBE_REDEFERRED
    if any(s.startswith("TDX_PROBE_FAIL_") for s in statuses):
        for fail in (
            TDX_PROBE_FAIL_DEPENDENCY,
            TDX_PROBE_FAIL_NETWORK,
            TDX_PROBE_FAIL_SCHEMA,
            TDX_PROBE_FAIL_VALIDATION,
            TDX_PROBE_REJECTED,
        ):
            if fail in statuses:
                return fail
    return TDX_PROBE_REDEFERRED


def run_tdx_manual_probe(
    *,
    evidence_dir: Path | None = None,
    sandbox_root: Path | None = None,
    db_path: Path | None = None,
    fetch_ports: dict[str, FetchPort] | None = None,
) -> dict[str, Any]:
    """Mocked probe path for default CI — no live network."""
    return _run_probe_bundle(
        live=False,
        evidence_dir=evidence_dir,
        sandbox_root=sandbox_root,
        db_path=db_path,
        fetch_ports=fetch_ports,
    )


def run_tdx_live_manual_probe(
    *,
    authorization_evidence: Path | str | None = None,
    tdx_host: str = "",
    tdx_port: int = 0,
    authorized_session_id: str = "b01-tdx-live-2026-06-24",
    evidence_dir: Path | None = None,
    sandbox_root: Path | None = None,
    db_path: Path | None = None,
    max_network_calls: int = MAX_NETWORK_CALLS,
) -> dict[str, Any]:
    """Opt-in live probe — requires authorization MD + matching host/port."""
    auth_path = Path(authorization_evidence or DEFAULT_AUTH_PATH)
    if max_network_calls <= 0:
        status = TDX_PROBE_FAIL_VALIDATION
        invalid_reason = f"max_network_calls={max_network_calls} is invalid (must be positive)"
        return {
            "overall_status": status,
            "live_attempted": True,
            "authorization_present": auth_path.is_file(),
            "raw_records": [
                {
                    "probe_id": target.probe_id,
                    "status": status,
                    "failure_reason": invalid_reason,
                }
                for target in TDX_PROBE_TARGETS
            ],
            "comparison": build_comparison_report([]),
            "registry_closeout": decide_registry_closeout(
                [], live_attempted=True, overall_status=status
            ),
            "network_calls": 0,
            "failure_reason": invalid_reason,
        }
    auth_block = _check_live_authorization(
        authorization_evidence=auth_path,
        tdx_host=tdx_host,
        tdx_port=tdx_port,
        authorized_session_id=authorized_session_id,
    )
    if auth_block is not None:
        return {
            "overall_status": auth_block,
            "live_attempted": True,
            "authorization_present": auth_path.is_file(),
            "raw_records": [],
            "comparison": build_comparison_report([]),
            "registry_closeout": decide_registry_closeout(
                [], live_attempted=True, overall_status=auth_block
            ),
            "network_calls": 0,
            "failure_reason": "live authorization gate blocked",
        }
    return _run_probe_bundle(
        live=True,
        evidence_dir=evidence_dir,
        sandbox_root=sandbox_root,
        db_path=db_path,
        authorization_evidence=auth_path,
        tdx_host=tdx_host,
        tdx_port=tdx_port,
        authorized_session_id=authorized_session_id,
        max_network_calls=max_network_calls,
    )


def _run_probe_bundle(
    *,
    live: bool,
    evidence_dir: Path | None = None,
    sandbox_root: Path | None = None,
    db_path: Path | None = None,
    fetch_ports: dict[str, FetchPort] | None = None,
    authorization_evidence: Path | None = None,
    tdx_host: str = "",
    tdx_port: int = 0,
    authorized_session_id: str = "b01-tdx-live-2026-06-24",
    max_network_calls: int = MAX_NETWORK_CALLS,
) -> dict[str, Any]:
    evidence_dir = Path(evidence_dir or DEFAULT_EVIDENCE_DIR)
    sandbox_root = Path(sandbox_root or DEFAULT_SANDBOX_ROOT)
    db_path = Path(db_path or DEFAULT_PRODUCTION_DB)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    before_bytes = db_path.read_bytes() if db_path.is_file() else None
    raw_records: list[dict[str, Any]] = []
    network_calls = 0
    upstream = (
        f"tdx_hq_host:{tdx_host}:{tdx_port}"
        if live
        else "mocked:tdx_pytdx"
    )

    for target in TDX_PROBE_TARGETS:
        if live:
            if network_calls >= max_network_calls:
                raw_records.append(
                    {
                        "probe_id": target.probe_id,
                        "status": TDX_PROBE_FAIL_VALIDATION,
                        "failure_reason": f"max_network_calls={max_network_calls} exceeded",
                    }
                )
                continue
            port = _resolve_live_port(
                target,
                host=tdx_host,
                port=tdx_port,
                authorization_evidence=authorization_evidence or DEFAULT_AUTH_PATH,
                authorized_session_id=authorized_session_id,
                remaining_network_calls=max_network_calls - network_calls,
            )
            network_calls += 1
        else:
            port = (fetch_ports or {}).get(target.probe_id) or _resolve_mock_port(target)
        raw_records.append(
            _run_single_probe(
                target,
                sandbox_root=sandbox_root / ("raw" if live else "mocked"),
                fetch_port=port,
                upstream=upstream,
                live=live,
            )
        )

    total_rows = sum(r.get("row_count", 0) for r in raw_records)
    if total_rows > MAX_TOTAL_ROWS:
        for r in raw_records:
            if r.get("status") == TDX_PROBE_PASS_RAW_ONLY:
                r["status"] = TDX_PROBE_FAIL_VALIDATION
                r["failure_reason"] = f"aggregate rows {total_rows} > {MAX_TOTAL_ROWS}"

    overall = _aggregate_status(raw_records, live=live)
    comparison = build_comparison_report(raw_records)
    mutation = capture_no_mutation_proof(db_path, before_bytes=before_bytes)
    registry = decide_registry_closeout(
        raw_records, live_attempted=live, overall_status=overall
    )

    result = {
        "overall_status": overall,
        "live_attempted": live,
        "authorization_present": bool(authorization_evidence and authorization_evidence.is_file())
        if live
        else False,
        "raw_records": raw_records,
        "comparison": comparison,
        "registry_closeout": registry,
        "mutation_proof": mutation,
        "network_calls": network_calls,
        "total_rows": total_rows,
    }

    suffix = "live" if live else "mocked"
    (evidence_dir / f"tdx_manual_probe_{suffix}_raw_evidence.json").write_text(
        json.dumps({"records": raw_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / f"tdx_manual_probe_{suffix}_comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "interface_probe_decision.md").write_text(
        _format_decision_md(registry, overall),
        encoding="utf-8",
    )
    return result


def _format_decision_md(registry: dict[str, Any], overall: str) -> str:
    lines = [
        "# Batch 01 TDX Manual Probe Decision",
        "",
        f"- **Overall probe status:** `{overall}`",
        f"- **tdx_pytdx:** `{registry.get('tdx_pytdx')}`",
        f"- **tdx_pytdx_live_probe:** `{registry.get('tdx_pytdx_live_probe')}`",
        "- **Does not close R3-B2.75-REQ2-EM:** True",
        "- **Does not close R3-PROMPT14-AKSHARE-VAL-01:** True",
        "- **Validation-only / disabled-by-default:** True",
        "",
        "Open registry rows:",
    ]
    for row in registry.get("registry_rows_must_remain_open", []):
        lines.append(f"- `{row}` — must remain OPEN")
    return "\n".join(lines) + "\n"


def run_security_list_cap_probe(*, requested_rows: int) -> dict[str, Any]:
    """TDX-04 helper — explicit cap enforcement for security list."""
    target = next(t for t in TDX_PROBE_TARGETS if t.operation == "fetch_security_list")
    port = MockTdxSecurityListFetchPort(SECURITY_LIST_CAP, requested_rows=requested_rows)
    return _run_single_probe(
        target,
        sandbox_root=DEFAULT_SANDBOX_ROOT / "cap-check",
        fetch_port=port,
        upstream="mocked:tdx_pytdx",
        live=False,
    )
