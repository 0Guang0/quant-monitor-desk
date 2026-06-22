"""018C low-cost data-interface sidecar probe (sandbox raw-only, fail-closed)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPort, PortError, StubFetchPort
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.ops.db_inspector import KEY_TABLES
from backend.app.ops.interface_probe_fetch_ports import (
    EASTMONEY_HIST_VENDOR_API,
    SINA_DAILY_VENDOR_API,
    AkshareSinaDailyValidationFetchPort,
    TdxPytdxProbeFetchPort,
    content_hash_bytes,
)
from backend.app.ops.live_pilot import _key_table_row_counts
from backend.app.storage.raw_store import RawStore

DEFAULT_PRODUCTION_DB = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/data-interface-probe"
DEFAULT_EVIDENCE_DIR = (
    PROJECT_ROOT / ".trellis/tasks/06-22-round3-018c-low-cost-probe/execute-evidence"
)

SIDECAR_SINA_OPERATION = "fetch_daily_bar_sina_validation"


@dataclass(frozen=True)
class ProbeTarget:
    probe_id: str
    source_id: str
    data_domain: str
    operation: str
    vendor_api: str
    upstream: str
    instrument_id: str
    window_label: str
    max_rows: int


PROBE_TARGETS: tuple[ProbeTarget, ...] = (
    ProbeTarget(
        "probe-sina-daily-validation",
        "akshare",
        "cn_equity_daily_bar",
        SIDECAR_SINA_OPERATION,
        SINA_DAILY_VENDOR_API,
        "finance.sina.com.cn",
        "sh.600519",
        "recent 5 trading days",
        10,
    ),
    ProbeTarget(
        "probe-tdx-equity-daily",
        "tdx_pytdx",
        "cn_equity_daily_bar",
        "fetch_daily_bar",
        "pytdx.get_security_bars",
        "tdx_hq_host",
        "sh.600519",
        "recent 5 trading days",
        10,
    ),
    ProbeTarget(
        "probe-tdx-security-list",
        "tdx_pytdx",
        "security_list",
        "fetch_security_list",
        "pytdx.get_security_list",
        "tdx_hq_host",
        "sh",
        "max_rows=20 per market",
        20,
    ),
    ProbeTarget(
        "probe-tdx-index-daily",
        "tdx_pytdx",
        "cn_index_daily_bar",
        "fetch_index_daily_bar",
        "pytdx.get_index_bars",
        "tdx_hq_host",
        "000001.SH",
        "recent 5 trading days",
        10,
    ),
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_key_table_row_counts(db_path: Path) -> dict[str, int | None]:
    if not db_path.is_file():
        return {}
    try:
        return _key_table_row_counts(db_path)
    except Exception:
        return {}


def build_route_matrix() -> dict[str, Any]:
    registry = SourceRegistry()
    registry.load()
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(
        source_registry=registry,
        capability_registry=capabilities,
    )
    rows = []
    for target in PROBE_TARGETS:
        plan = planner.plan(
            data_domain=target.data_domain,
            operation=target.operation,
            run_id=f"018c-{target.probe_id}",
            job_id=f"018c-{target.probe_id}",
            extra_candidates=[(target.source_id, "Validation")],
        )
        rec = registry.get(target.source_id)
        rows.append(
            {
                "probe_id": target.probe_id,
                "source_id": target.source_id,
                "operation": target.operation,
                "vendor_api": target.vendor_api,
                "source_enabled_by_default": rec.is_enabled,
                "route_status": plan.route_status,
                "selected_source_id": plan.selected_source_id,
            }
        )
    return {"generated_at": _utc_now_iso(), "routes": rows}


def _resolve_fetch_port(target: ProbeTarget) -> FetchPort:
    if target.operation == SIDECAR_SINA_OPERATION:
        return AkshareSinaDailyValidationFetchPort((target.instrument_id,), target.max_rows)
    if target.source_id == "tdx_pytdx" and target.operation == "fetch_daily_bar":
        return TdxPytdxProbeFetchPort((target.instrument_id,), target.max_rows)
    return StubFetchPort(payload=b"{}")


def run_single_probe(
    target: ProbeTarget,
    *,
    sandbox_root: Path,
    fetch_port: FetchPort | None = None,
) -> dict[str, Any]:
    port = fetch_port or _resolve_fetch_port(target)
    req = FetchRequest(
        run_id=f"018c-{target.probe_id}",
        source_id=target.source_id,
        data_domain=target.data_domain,
        instrument_id=target.instrument_id,
        market_id="cn",
        end_time=datetime.now(UTC).date().isoformat(),
    )
    record: dict[str, Any] = {
        "probe_id": target.probe_id,
        "source_id": target.source_id,
        "operation": target.operation,
        "vendor_api": target.vendor_api,
        "upstream": target.upstream,
        "params": {
            "instrument_id": target.instrument_id,
            "window_label": target.window_label,
            "max_rows": target.max_rows,
            "raw_only": True,
            "write_target": "sandbox",
            "allow_clean_write": False,
        },
        "timestamp": _utc_now_iso(),
        "status": "PENDING",
    }
    if target.source_id == "tdx_pytdx" and target.operation != "fetch_daily_bar":
        record.update(
            {
                "status": "DEFERRED",
                "failure_reason": f"{target.operation} deferred in 018C bounded slice",
            }
        )
        return record
    try:
        payload = port.fetch_payload(req)
    except PortError as exc:
        record.update(
            {"status": "FAILED", "failure_reason": exc.message, "port_status": exc.status}
        )
        return record
    sandbox_root.mkdir(parents=True, exist_ok=True)
    saved = RawStore(sandbox_root).save(
        payload.content,
        source=target.source_id,
        data_domain=target.data_domain,
        file_type=payload.file_type,
        as_of=datetime.now(UTC).date().isoformat(),
    )
    record.update(
        {
            "status": "SUCCESS",
            "row_count": payload.row_count,
            "content_hash": content_hash_bytes(payload.content),
            "sandbox_path": saved.local_path,
            "failure_reason": None,
        }
    )
    return record


def capture_no_mutation_proof(
    db_path: Path,
    *,
    before_counts: dict[str, int | None] | None = None,
    before_bytes: bytes | None = None,
) -> dict[str, Any]:
    db_path = Path(db_path)
    if before_counts is None:
        before_counts = _safe_key_table_row_counts(db_path)
    if before_bytes is None and db_path.is_file():
        before_bytes = db_path.read_bytes()
    after_bytes = db_path.read_bytes() if db_path.is_file() else None
    after_counts = _safe_key_table_row_counts(db_path)
    return {
        "generated_at": _utc_now_iso(),
        "db_path": str(db_path),
        "db_hash_unchanged": before_bytes == after_bytes,
        "before_key_table_counts": before_counts,
        "after_key_table_counts": after_counts,
        "zero_mutation": before_counts == after_counts and before_bytes == after_bytes,
    }


def decide_closeout(
    raw_records: list[dict[str, Any]],
    route_matrix: dict[str, Any],
) -> dict[str, Any]:
    tdx_rows = [r for r in route_matrix["routes"] if r["source_id"] == "tdx_pytdx"]
    tdx_ok = all(
        not r["source_enabled_by_default"] and r["selected_source_id"] != "tdx_pytdx"
        for r in tdx_rows
    )
    sina = next((r for r in raw_records if r.get("operation") == SIDECAR_SINA_OPERATION), None)
    tdx_live = next(
        (
            r
            for r in raw_records
            if r.get("source_id") == "tdx_pytdx" and r.get("operation") == "fetch_daily_bar"
        ),
        None,
    )
    per = {
        "tdx_pytdx": "PROBE_ACCEPT_DISABLED_CANDIDATE" if tdx_ok else "PROBE_REJECT_SOURCE",
        "akshare_sina_sidecar": "PROBE_ACCEPT_DISABLED_CANDIDATE"
        if sina and sina.get("status") == "SUCCESS"
        else "PROBE_REDEFERRED",
        "tdx_pytdx_live_probe": "PROBE_ACCEPT_DISABLED_CANDIDATE"
        if tdx_live and tdx_live.get("status") == "SUCCESS"
        else "PROBE_REDEFERRED",
    }
    overall = "PROBE_ACCEPT_DISABLED_CANDIDATE"
    if per["tdx_pytdx"] == "PROBE_REJECT_SOURCE":
        overall = "PROBE_REJECT_SOURCE"
    elif all(v == "PROBE_REDEFERRED" for v in per.values()):
        overall = "PROBE_REDEFERRED"
    return {
        "generated_at": _utc_now_iso(),
        "overall_outcome": overall,
        "per_candidate": per,
        "does_not_close_R3-B2.75-REQ2-EM": True,
        "does_not_unblock_production_live_readiness": True,
        "original_request2_vendor_api": EASTMONEY_HIST_VENDOR_API,
        "sidecar_vendor_api": SINA_DAILY_VENDOR_API,
    }


def run_interface_probe(
    *,
    evidence_dir: Path | None = None,
    sandbox_root: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    evidence_dir = Path(evidence_dir or DEFAULT_EVIDENCE_DIR)
    sandbox_root = Path(sandbox_root or DEFAULT_SANDBOX_ROOT)
    db_path = Path(db_path or DEFAULT_PRODUCTION_DB)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    before_bytes = db_path.read_bytes() if db_path.is_file() else None
    before_counts = _safe_key_table_row_counts(db_path)
    route_matrix = build_route_matrix()
    raw_records = [run_single_probe(t, sandbox_root=sandbox_root) for t in PROBE_TARGETS]
    mutation = capture_no_mutation_proof(
        db_path, before_counts=before_counts, before_bytes=before_bytes
    )
    decision = decide_closeout(raw_records, route_matrix)

    (evidence_dir / "interface_probe_route_matrix.json").write_text(
        json.dumps(route_matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (evidence_dir / "interface_probe_raw_evidence.json").write_text(
        json.dumps({"records": raw_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "interface_probe_no_mutation_proof.md").write_text(
        _format_no_mutation_md(mutation), encoding="utf-8"
    )
    (evidence_dir / "interface_probe_decision.md").write_text(
        _format_decision_md(decision), encoding="utf-8"
    )
    return {"decision": decision, "mutation_proof": mutation, "raw_records": raw_records}


def _format_no_mutation_md(proof: dict[str, Any]) -> str:
    lines = [
        "# 018C No Production DB Mutation Proof",
        "",
        f"- **Zero mutation:** {proof['zero_mutation']}",
        f"- **DB path:** `{proof['db_path']}`",
        "",
        "| Table | Before | After |",
        "| ----- | ------ | ----- |",
    ]
    before = proof.get("before_key_table_counts") or {}
    after = proof.get("after_key_table_counts") or {}
    for name in KEY_TABLES:
        lines.append(f"| {name} | {before.get(name)} | {after.get(name)} |")
    return "\n".join(lines) + "\n"


def _format_decision_md(decision: dict[str, Any]) -> str:
    lines = [
        "# 018C Interface Probe Decision",
        "",
        f"- **Overall:** `{decision['overall_outcome']}`",
        "- **Unblocks production-live readiness:** False",
        "",
    ]
    for k, v in decision.get("per_candidate", {}).items():
        lines.append(f"- {k}: `{v}`")
    return "\n".join(lines) + "\n"
