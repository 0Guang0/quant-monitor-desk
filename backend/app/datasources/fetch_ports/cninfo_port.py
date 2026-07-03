"""CNINFO filings metadata fetch port (R3H-03, replay-first + capped PDF live smoke).

L2 migrate from backend/app/ops/staged_pilot_fetch_ports.py (CninfoMetadataStagedFetchPort) and
backend/app/datasources/adapters/cninfo.py skeleton domains; PDF path capped at MAX_PDF_BYTES.
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
from backend.app.datasources.normalizers.cn_market import (
    build_cn_market_evidence_bundle,
    read_cn_market_evidence_bundle,
)
from backend.app.datasources.normalizers.evidence_bundle import (
    finalize_bundle,
    parse_fetch_window_date,
    reject_over_cap,
    replay_rows_caught_up_fallback,
)

MAX_ISSUERS = 5
MAX_FILINGS = 20
MAX_PDF_BYTES = 5 * 1024 * 1024
DEFAULT_PDF_LIVE_BYTES = 4096
SYMBOL_WHITELIST = frozenset({"sh.600519", "sz.000001"})

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/cn_market/cninfo/sh600519_filings_replay.json"
)


def _filter_filings_by_window(
    filings: list[dict],
    *,
    start_time: str | None,
    end_time: str | None,
) -> list[dict]:
    start = parse_fetch_window_date(start_time)
    end = parse_fetch_window_date(end_time)
    if start is None or end is None:
        return filings
    if start > end:
        return []
    filtered: list[dict] = []
    for row in filings:
        obs = parse_fetch_window_date(str(row.get("observation_date") or row.get("publish_timestamp") or ""))
        if obs is not None and start <= obs <= end:
            filtered.append(row)
    return filtered


@dataclass(frozen=True)
class CninfoMockFetchPort:
    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE
    pdf_bytes: int = 0
    enable_pdf_live: bool = False
    replay_caught_up_fallback: bool = False

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
            all_filings = list(bundle.get("filings") or [])
            filtered = _filter_filings_by_window(
                all_filings,
                start_time=req.start_time,
                end_time=req.end_time,
            )
            filings = (
                replay_rows_caught_up_fallback(
                    all_filings,
                    filtered,
                    start_time=req.start_time,
                    end_time=req.end_time,
                    sort_key=lambda row: str(
                        row.get("observation_date") or row.get("publish_timestamp") or ""
                    ),
                    min_rows=1,
                )
                if self.replay_caught_up_fallback
                else filtered
            )
            bundle = {**bundle, "filings": filings}
            content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
            return FetchPayload(content=content, file_type="json", row_count=len(filings))

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


@dataclass(frozen=True)
class CninfoLiveFetchPort:
    """Product live cninfo port — real HTTP via cninfo disclosure API (akshare transport)."""

    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        from backend.app.datasources.fetch_ports.cn_rehearsal_live_ports import (
            _cninfo_numeric_symbol,
            _run_akshare_call,
            parse_pilot_date_window,
        )

        try:
            import akshare as ak
        except ImportError as exc:
            raise PortError("FAILED", f"akshare package not installed: {exc}") from exc

        reject_over_cap(value=self.max_rows, cap=MAX_FILINGS, label="max_filings")
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for cninfo live fetch")
        if symbol not in SYMBOL_WHITELIST:
            raise PortError("FAILED", f"symbol not in cninfo whitelist: {symbol!r}")
        numeric = _cninfo_numeric_symbol(symbol)
        if not numeric:
            raise PortError("FAILED", f"invalid cninfo symbol: {symbol!r}")

        date_window = "recent 365 calendar days"
        start = datetime.now(UTC).date() - timedelta(days=parse_pilot_date_window(date_window))
        end = datetime.now(UTC).date()

        def _fetch_disclosure():
            return ak.stock_zh_a_disclosure_report_cninfo(
                symbol=numeric,
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
            )

        try:
            frame = _run_akshare_call(_fetch_disclosure)
        except PortError:
            raise
        except Exception as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc

        if frame is None or frame.empty:
            raise PortError("EMPTY_RESPONSE", "cninfo disclosure metadata returned no rows")

        trimmed = frame.tail(self.max_rows)
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"cninfo-live-{symbol}-{uuid.uuid4().hex[:12]}"
        domain = req.data_domain or "cn_announcements"
        filings: list[dict] = []
        for idx, record in enumerate(trimmed.to_dict(orient="records")):
            publish = str(
                record.get("公告时间")
                or record.get("publish_time")
                or record.get("publish_timestamp")
                or retrieved_at
            )
            obs_date = publish[:10] if len(publish) >= 10 else retrieved_at[:10]
            filings.append(
                {
                    "filing_id": f"cninfo-live-{symbol}-{idx}",
                    "instrument_id": symbol,
                    "title": str(record.get("公告标题") or record.get("title") or f"公告-{idx}"),
                    "publish_timestamp": publish,
                    "observation_date": obs_date,
                    "source_used": "cninfo",
                }
            )
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


@dataclass(frozen=True)
class CninfoProductLiveFetchPort:
    """Product live cninfo port — replay-first; not rehearsal cn_rehearsal_live_ports."""

    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        from backend.app.datasources.fetch_ports.cn_product_live_replay import (
            replay_first_fetch_payload,
        )

        return replay_first_fetch_payload(
            CninfoMockFetchPort,
            symbols=self.symbols,
            max_rows=self.max_rows,
            replay_path=self.replay_path,
            req=req,
            replay_caught_up_fallback=True,
        )


def create_cninfo_fetch_port(*, symbols: Sequence[str], max_rows: int, use_mock: bool = True):
    if len(symbols) > MAX_ISSUERS:
        raise PortError("FAILED", f"max {MAX_ISSUERS} issuers allowed, got {len(symbols)}")
    if use_mock:
        return CninfoMockFetchPort(symbols=symbols, max_rows=max_rows)
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="cninfo")
    return CninfoLiveFetchPort(symbols=symbols, max_rows=max_rows)


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
