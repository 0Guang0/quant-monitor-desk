"""018C low-cost data-interface probe tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from backend.app.datasources.adapters.fetch_port import FetchPayload, StubFetchPort
from backend.app.datasources.capability_registry import (
    OperationDisabledError,
    SourceCapabilityRegistry,
)
from backend.app.ops.interface_probe import (
    SIDECAR_SINA_OPERATION,
    build_route_matrix,
    decide_closeout,
    run_interface_probe,
)

ROOT = Path(__file__).resolve().parents[1]


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_tdxPytdx_disabledByDefault() -> None:
    entry = next(
        s
        for s in _yaml(ROOT / "specs/datasource_registry/source_registry.yaml")["sources"]
        if s["source_id"] == "tdx_pytdx"
    )
    assert entry["enabled_by_default"] is False
    assert entry["validation_only"] is True


def test_capabilityRegistry_rejectsTdxPytdx() -> None:
    reg = SourceCapabilityRegistry()
    reg.load()
    with pytest.raises(OperationDisabledError):
        reg.assert_source_domain_operation("tdx_pytdx", "cn_equity_daily_bar", "fetch_daily_bar")


def test_sinaSidecar_distinctFromEastmoneyHist() -> None:
    ops = _yaml(ROOT / "specs/datasource_registry/source_capabilities.yaml")["sources"]["akshare"][
        "domains"
    ]["cn_equity_daily_bar"]["operations"]
    assert ops["fetch_daily_bar_validation"]["vendor_api"] == "stock_zh_a_hist"
    assert ops["fetch_daily_bar_sina_validation"]["vendor_api"] == "stock_zh_a_daily"


def test_routeMatrix_tdxFailClosed() -> None:
    for row in build_route_matrix()["routes"]:
        if row["source_id"] == "tdx_pytdx":
            assert not row["source_enabled_by_default"]
            assert row["selected_source_id"] != "tdx_pytdx"


def test_decision_doesNotCloseRequest2() -> None:
    d = decide_closeout(
        [{"operation": SIDECAR_SINA_OPERATION, "status": "SUCCESS"}],
        build_route_matrix(),
    )
    assert d["does_not_close_R3-B2.75-REQ2-EM"]
    assert d["does_not_unblock_production_live_readiness"]


def test_runInterfaceProbe_writesEvidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("backend.app.ops.interface_probe._safe_key_table_row_counts", lambda _p: {})

    class Ok:
        def fetch_payload(self, req):
            return FetchPayload(content=b"{}", file_type="json", row_count=0)

    monkeypatch.setattr(
        "backend.app.ops.interface_probe._resolve_fetch_port",
        lambda t: Ok() if t.operation == SIDECAR_SINA_OPERATION else StubFetchPort(payload=b"{}"),
    )
    db = tmp_path / "db.duckdb"
    db.write_bytes(b"x")
    ev = tmp_path / "evidence"
    run_interface_probe(evidence_dir=ev, sandbox_root=tmp_path / "sb", db_path=db)
    assert (ev / "interface_probe_decision.md").is_file()


def test_tdxAdapter_notInFactory() -> None:
    from backend.app.datasources.adapters import _ADAPTER_TYPES

    assert "tdx_pytdx" not in _ADAPTER_TYPES
