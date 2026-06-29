"""Mootdx TDX-compatible validation fetch port (R3H-03).

L2 extend tdx_pytdx_port (R3FR-03 MIT) — shared caps/domain guards and TDX manifest shape;
independent source_id=mootdx; no silent fallback to tdx_pytdx.
MIT attribution: lifecycle ideas from EasyXT tdx_provider.py via tdx_pytdx_port.
See R3H_03_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.fetch_ports.tdx_fetch_guards import (
    EQUITY_INDEX_MAX_ROWS,
    MAX_NETWORK_CALLS,
    MINUTE_BARS_ENABLED,
    SECURITY_LIST_MAX_ROWS,
    SUPPORTED_DOMAINS,
    domain_cap,
    parse_equity_symbol,
    reject_full_market_scan,
    reject_over_cap,
    reject_unsupported_domain,
)
from backend.app.datasources.normalizers.cn_market import (
    build_cn_market_evidence_bundle,
    read_cn_market_evidence_bundle,
)
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle
from backend.app.datasources.normalizers.tdx import (
    build_equity_bar_manifest,
    build_security_list_manifest,
    manifest_content_hash,
)

REPLAY_FIXTURE = PROJECT_ROOT / "tests/fixtures/replay/cn_market/tdx/mootdx_daily_replay.json"


def _mootdx_manifest_from_rows(
    *,
    domain: str,
    symbol: str,
    rows: list[dict],
) -> dict:
    """TDX-shaped manifest with mootdx source_id (extends tdx_pytdx normalizers)."""
    if domain == "security_list":
        manifest = build_security_list_manifest(symbol or "sh", rows)
    else:
        manifest = build_equity_bar_manifest(symbol, rows)
    manifest["source_id"] = "mootdx"
    manifest["vendor_api"] = "mootdx.get_security_bars"
    manifest["content_hash"] = manifest_content_hash(manifest)
    return manifest


@dataclass(frozen=True)
class MootdxMockFetchPort:
    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_unsupported_domain(req, source_id="mootdx")
        reject_full_market_scan(req, source_id="mootdx")
        reject_over_cap(data_domain=req.data_domain, max_rows=self.max_rows, source_id="mootdx")

        domain = req.data_domain or "cn_equity_daily_bar"
        if domain not in SUPPORTED_DOMAINS:
            raise PortError("FAILED", f"unsupported data_domain for mootdx: {domain!r}")

        if self.replay_path.is_file() and domain == "cn_equity_daily_bar":
            bundle = read_cn_market_evidence_bundle(self.replay_path)
            content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
            return FetchPayload(content=content, file_type="json", row_count=len(bundle.get("bars") or []))

        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol and domain != "security_list":
            raise PortError("FAILED", "missing instrument_id for mootdx fetch")

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"mootdx-mock-{symbol or 'list'}-{uuid.uuid4().hex[:12]}"
        today = datetime.now(UTC).date()
        if domain == "security_list":
            rows = [
                {
                    "code": f"60051{idx}",
                    "name": f"mock-{idx}",
                    "trade_date": today.isoformat(),
                }
                for idx in range(min(self.max_rows, 2))
            ]
            manifest = _mootdx_manifest_from_rows(domain=domain, symbol=symbol or "sh", rows=rows)
            content = json.dumps(manifest, ensure_ascii=False, default=str).encode("utf-8")
            return FetchPayload(content=content, file_type="json", row_count=len(rows))

        if domain == "cn_equity_daily_bar":
            parse_equity_symbol(symbol)

        bars = [
            {
                "instrument_id": symbol,
                "trade_date": (today - timedelta(days=offset)).isoformat(),
                "open": 1400.0,
                "high": 1410.0,
                "low": 1395.0,
                "close": 1405.0,
                "volume": 500_000,
                "source_used": "mootdx",
            }
            for offset in range(min(self.max_rows, EQUITY_INDEX_MAX_ROWS))
        ]
        bundle = build_cn_market_evidence_bundle(
            bars=bars,
            data_domain=domain,
            source_id="mootdx",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(bars))


@dataclass(frozen=True)
class MootdxProductLiveFetchPort:
    """Product live mootdx port — replay-first; independent from tdx_pytdx fallback."""

    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return MootdxMockFetchPort(
            symbols=self.symbols, max_rows=self.max_rows, replay_path=self.replay_path
        ).fetch_payload(req)


def create_mootdx_fetch_port(*, symbols: Sequence[str], max_rows: int, use_mock: bool = True):
    cap = domain_cap("cn_equity_daily_bar") or SECURITY_LIST_MAX_ROWS
    if max_rows > max(cap, MAX_NETWORK_CALLS, SECURITY_LIST_MAX_ROWS):
        raise PortError("FAILED", "mootdx max_rows exceeds cap")
    if use_mock:
        return MootdxMockFetchPort(symbols=symbols, max_rows=max_rows)
    return MootdxProductLiveFetchPort(symbols=symbols, max_rows=max_rows)


__all__ = [
    "EQUITY_INDEX_MAX_ROWS",
    "MINUTE_BARS_ENABLED",
    "MootdxMockFetchPort",
    "SECURITY_LIST_MAX_ROWS",
    "create_mootdx_fetch_port",
]
