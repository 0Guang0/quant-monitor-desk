"""CNINFO filings metadata fetch port (R3H-03, replay-first + capped PDF live smoke).

L2 migrate from backend/app/ops/staged_pilot_fetch_ports.py (CninfoMetadataStagedFetchPort) and
backend/app/datasources/adapters/cninfo.py skeleton domains; PDF path capped at MAX_PDF_BYTES.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.cn_market import (
    build_cn_market_evidence_bundle,
    read_cn_market_evidence_bundle,
)
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap

MAX_ISSUERS = 5
MAX_FILINGS = 20
MAX_PDF_BYTES = 5 * 1024 * 1024
DEFAULT_PDF_LIVE_BYTES = 4096
SYMBOL_WHITELIST = frozenset({"sh.600519", "sz.000001"})

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/cn_market/cninfo/sh600519_filings_replay.json"
)


@dataclass(frozen=True)
class CninfoMockFetchPort:
    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE
    pdf_bytes: int = 0
    enable_pdf_live: bool = False

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_FILINGS, label="max_filings")
        if len(self.symbols) > MAX_ISSUERS:
            raise PortError("FAILED", f"max {MAX_ISSUERS} issuers allowed")
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for cninfo fetch")
        if symbol not in SYMBOL_WHITELIST:
            raise PortError("FAILED", f"symbol not in cninfo whitelist: {symbol!r}")

        domain = req.data_domain or "cn_announcements"
        if domain == "cn_pdf_reports":
            return self._fetch_capped_pdf(req, symbol, domain)

        if self.replay_path.is_file():
            bundle = read_cn_market_evidence_bundle(self.replay_path)
            content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
            return FetchPayload(
                content=content,
                file_type="json",
                row_count=len(bundle.get("filings") or []),
            )

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"cninfo-mock-{symbol}-{uuid.uuid4().hex[:12]}"
        filings = [
            {
                "filing_id": f"cninfo-{idx}",
                "instrument_id": symbol,
                "title": f"公告样例-{idx}",
                "publish_timestamp": retrieved_at,
                "observation_date": retrieved_at[:10],
                "source_used": "cninfo",
            }
            for idx in range(min(self.max_rows, 2))
        ]
        bundle = build_cn_market_evidence_bundle(
            filings=filings,
            data_domain=domain,
            source_id="cninfo",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(filings))

    def _fetch_capped_pdf(
        self, req: FetchRequest, symbol: str, domain: str
    ) -> FetchPayload:
        if not self.enable_pdf_live:
            raise PortError(
                "USER_AUTH_REQUIRED",
                "cninfo PDF live smoke requires enable_pdf_live=True (capped tier-B)",
            )
        payload_bytes = self.pdf_bytes or DEFAULT_PDF_LIVE_BYTES
        if payload_bytes > MAX_PDF_BYTES:
            raise PortError("FAILED", f"pdf bytes {payload_bytes} exceeds cap {MAX_PDF_BYTES}")
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"cninfo-pdf-live-{symbol}-{uuid.uuid4().hex[:12]}"
        filings = [
            {
                "filing_id": f"cninfo-pdf-{symbol}",
                "instrument_id": symbol,
                "title": "capped PDF live smoke",
                "observation_date": retrieved_at[:10],
                "source_used": "cninfo",
            }
        ]
        bundle = build_cn_market_evidence_bundle(
            filings=filings,
            data_domain=domain,
            source_id="cninfo",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle["pdf_document"] = {
            "byte_length": payload_bytes,
            "content_type": "application/pdf",
            "capped": True,
            "max_bytes": MAX_PDF_BYTES,
            "payload_stub": "A" * min(payload_bytes, 64),
        }
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=1)


def create_cninfo_fetch_port(*, symbols: Sequence[str], max_rows: int):
    if len(symbols) > MAX_ISSUERS:
        raise PortError("FAILED", f"max {MAX_ISSUERS} issuers allowed, got {len(symbols)}")
    return CninfoMockFetchPort(symbols=symbols, max_rows=max_rows)


def create_cninfo_pdf_live_fetch_port(
    *,
    symbols: Sequence[str],
    max_rows: int = 1,
    pdf_bytes: int = DEFAULT_PDF_LIVE_BYTES,
):
    """Tier-B capped PDF live smoke entry (user-gated via enable_pdf_live)."""
    if pdf_bytes > MAX_PDF_BYTES:
        raise PortError("FAILED", f"pdf bytes {pdf_bytes} exceeds cap {MAX_PDF_BYTES}")
    return CninfoMockFetchPort(
        symbols=symbols,
        max_rows=max_rows,
        pdf_bytes=pdf_bytes,
        enable_pdf_live=True,
    )
