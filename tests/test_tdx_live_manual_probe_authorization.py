"""Authorization gate tests for 018C TDX live manual probe (no network)."""

from __future__ import annotations

from pathlib import Path

import pytest
from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.interface_probe_fetch_ports import TdxPytdxProbeFetchPort
from backend.app.ops.tdx_live_manual_probe_gate import (
    TdxLiveManualProbeAuthorizationError,
    TdxLiveManualProbeRequest,
    parse_index_instrument,
    validate_tdx_live_manual_probe_authorization,
)


def _sample_auth_text(*, session_id: str = "sess-planning-test-001") -> str:
    return f"""# TDX Live Manual Probe Authorization

authorized_session_id: {session_id}

I authorize the Round 3 018C tdx_pytdx live manual probe scoped to
docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-22.md only.
See `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md`.
This probe does not close Eastmoney stock_zh_a_hist / R3-B2.75-REQ2-EM.

## TDX host

| host | port | provided_by | provided_on | reachability_note | reference_only_default | user_attestation |
| ---- | ---- | ----------- | ----------- | ----------------- | ---------------------- | ---------------- |
| 127.0.0.1 | 7709 | owner | 2026-06-22 | user confirms | false | bounded read-only probe |
"""


def test_tdxProbeFetchPort_blocksWithoutAuthorization() -> None:
    port = TdxPytdxProbeFetchPort(("sh.600519",), 10)
    with pytest.raises(PortError, match="fetch blocked"):
        port.fetch_payload(
            FetchRequest(
                run_id="t",
                source_id="tdx_pytdx",
                data_domain="cn_equity_daily_bar",
                instrument_id="sh.600519",
                market_id="cn",
                end_time="2026-06-22",
            )
        )


def test_validateTdxLiveManualProbe_missingFile_blocks() -> None:
    req = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/tdx_pytdx_live_manual_probe_authorization_2099-01-01.md",
        tdx_host="127.0.0.1",
        tdx_port=7709,
        authorized_session_id="sess-x",
    )
    with pytest.raises(TdxLiveManualProbeAuthorizationError, match="missing"):
        validate_tdx_live_manual_probe_authorization(req)


def test_validateTdxLiveManualProbe_validFile_passes(tmp_path: Path) -> None:
    auth = tmp_path / "tdx_pytdx_live_manual_probe_authorization_2026-06-22.md"
    auth.write_text(_sample_auth_text(), encoding="utf-8")
    req = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence=str(auth),
        tdx_host="127.0.0.1",
        tdx_port=7709,
        authorized_session_id="sess-planning-test-001",
    )
    validate_tdx_live_manual_probe_authorization(req)


def test_validateTdxLiveManualProbe_hostPortMismatch_blocks(tmp_path: Path) -> None:
    auth = tmp_path / "tdx_pytdx_live_manual_probe_authorization_2026-06-22.md"
    auth.write_text(_sample_auth_text(), encoding="utf-8")
    req = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence=str(auth),
        tdx_host="10.0.0.1",
        tdx_port=7709,
        authorized_session_id="sess-planning-test-001",
    )
    with pytest.raises(TdxLiveManualProbeAuthorizationError, match="host/port"):
        validate_tdx_live_manual_probe_authorization(req)


def test_parseIndexInstrument_000001SH() -> None:
    assert parse_index_instrument("000001.SH") == (1, "000001")
