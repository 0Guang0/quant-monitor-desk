"""TDX/pytdx disabled/raw-only provider port (R3FR-03).

MIT attribution: optional pytdx import and host-port lifecycle ideas adapted from
EasyXT tdx_provider.py (MIT); QMD rewrite only; no runtime import from external
reference trees; no auto server scan; no default live enablement.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_ports.tdx_fetch_guards import (
    EQUITY_INDEX_MAX_ROWS,
    FULL_MARKET_SCAN_ENABLED,
    MAX_NETWORK_CALLS,
    MINUTE_BARS_ENABLED,
    SECURITY_LIST_MAX_ROWS,
    domain_cap as _domain_cap,
    parse_equity_symbol as _parse_equity_symbol,
    reject_full_market_scan as _reject_full_market_scan,
    reject_over_cap as _reject_over_cap,
    reject_unsupported_domain as _reject_unsupported_domain,
)
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.tdx import (
    build_equity_bar_manifest,
    build_index_bar_manifest,
    build_security_list_manifest,
    manifest_content_hash,
    manifest_schema_hash,
    parse_index_instrument,
)
from backend.app.ops.tdx_live_manual_probe_gate import (
    TdxLiveManualProbeAuthorizationError,
    TdxPytdxAuthorization,
    enforce_live_entrypoint_stack,
    is_gate_issued_token,
)

@dataclass
class TdxPytdxFetchPort:
    """QMD-owned disabled/raw-only TDX fetch port."""

    symbols: Sequence[str]
    max_rows: int
    authorization: TdxPytdxAuthorization | None = None
    remaining_network_calls: int | None = None
    _network_calls_consumed: int = field(default=0, init=False, repr=False)

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        _reject_unsupported_domain(req)
        _reject_full_market_scan(req)
        _reject_over_cap(data_domain=req.data_domain, max_rows=self.max_rows)

        auth = self.authorization
        if auth is None or not is_gate_issued_token(auth.gate_token):
            raise PortError(
                "USER_AUTH_REQUIRED",
                "tdx_pytdx fetch blocked: use run_tdx_live_manual_probe after "
                "tdx_live_manual_probe_gate.validate_tdx_live_manual_probe_authorization",
            )

        try:
            enforce_live_entrypoint_stack()
        except TdxLiveManualProbeAuthorizationError as exc:
            raise PortError("USER_AUTH_REQUIRED", str(exc)) from exc

        if self.remaining_network_calls is not None:
            if self.remaining_network_calls <= 0:
                raise PortError(
                    "FAILED",
                    f"tdx_pytdx network call budget exhausted (remaining={self.remaining_network_calls})",
                )
            self.remaining_network_calls -= 1
            self._network_calls_consumed += 1

        try:
            from pytdx.hq import TdxHq_API
        except ImportError as exc:
            raise PortError("DISABLED_SOURCE", f"pytdx not installed: {exc}") from exc

        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        api = TdxHq_API()
        if not api.connect(auth.host, auth.port):
            raise PortError("NETWORK_ERROR", "tdx_pytdx probe could not connect")
        try:
            manifest, row_count = self._fetch_manifest(api, req, symbol)
        finally:
            api.disconnect()

        if row_count <= 0:
            raise PortError("EMPTY_RESPONSE", "tdx_pytdx returned no rows")

        content = json.dumps(manifest, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(
            content=content,
            file_type="json",
            row_count=row_count,
            schema_hash=manifest_schema_hash(manifest),
        )

    def _fetch_manifest(
        self, api: Any, req: FetchRequest, symbol: str
    ) -> tuple[dict[str, Any], int]:
        domain = req.data_domain
        if domain == "security_list":
            market_label = symbol or "sh"
            market_code = 1 if market_label.lower().startswith("sh") else 0
            rows = list(api.get_security_list(market_code, 0) or [])[: self.max_rows]
            manifest = build_security_list_manifest(market_label, rows)
            manifest["content_hash"] = manifest_content_hash(manifest)
            return manifest, len(rows)

        if domain == "cn_equity_daily_bar":
            market, code = _parse_equity_symbol(symbol)
            bars = api.get_security_bars(9, market, code, 0, self.max_rows) or []
            rows = list(bars)[-self.max_rows :]
            manifest = build_equity_bar_manifest(symbol, rows)
            manifest["content_hash"] = manifest_content_hash(manifest)
            return manifest, len(rows)

        if domain == "cn_index_daily_bar":
            market, code = parse_index_instrument(symbol)
            bars = api.get_index_bars(9, market, code, 0, self.max_rows) or []
            rows = list(bars)[-self.max_rows :]
            manifest = build_index_bar_manifest(symbol, rows)
            manifest["content_hash"] = manifest_content_hash(manifest)
            return manifest, len(rows)

        raise PortError("FAILED", f"unsupported operation for domain {domain!r}")
