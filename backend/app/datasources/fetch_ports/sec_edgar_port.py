"""SEC EDGAR disclosure fetch port (R3H-01 L3 greenfield).

No 1:1 upstream reference file; SEC fair-access identity via SEC_EDGAR_USER_AGENT.
Mock-first filings + Form 4; live fetch deferred by default.
See R3H_01_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import httpx2 as httpx

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.evidence_bundle import (
    finalize_bundle,
    parse_fetch_window_date,
    reject_over_cap,
    replay_rows_caught_up_fallback,
)
from backend.app.datasources.normalizers.sec_edgar import (
    build_filings_evidence_bundle,
    build_form4_evidence_bundle,
    read_filings_evidence_bundle,
)

# R3H-01 caps SSOT (frozen §7 production-entry defaults)
CIK_WHITELIST = frozenset({"0000320193", "0000789019", "0001018724"})
MAX_CIKS = 5
MAX_FILINGS = 50

SecEdgarDomain = Literal["us_filings", "us_insider_form4"]

FILINGS_REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/sec_edgar/filings_replay_bundle.json"
)


def _filter_filings_by_window(
    filings: list[dict[str, Any]],
    *,
    start_time: str | None,
    end_time: str | None,
) -> list[dict[str, Any]]:
    start = parse_fetch_window_date(start_time)
    end = parse_fetch_window_date(end_time)
    if start is None or end is None:
        return filings
    if start > end:
        return []
    filtered: list[dict[str, Any]] = []
    for row in filings:
        filed = parse_fetch_window_date(str(row.get("filing_date") or ""))
        if filed is not None and start <= filed <= end:
            filtered.append(row)
    return filtered


def _sec_user_agent() -> str | None:
    raw = os.environ.get("SEC_EDGAR_USER_AGENT")
    if not raw or not str(raw).strip():
        return None
    agent = str(raw).strip()
    # ponytail: SEC requires contact info in User-Agent; reject bare product names
    if "@" not in agent and "contact" not in agent.lower():
        return None
    return agent


def _reject_unknown_cik(cik: str) -> None:
    if cik not in CIK_WHITELIST:
        raise PortError("FAILED", f"CIK not in whitelist: {cik!r}")


@dataclass(frozen=True)
class SecEdgarMockFetchPort:
    """Deterministic mock SEC EDGAR port (no network)."""

    ciks: Sequence[str]
    max_filings: int
    data_domain: SecEdgarDomain
    replay_path: Path = FILINGS_REPLAY_FIXTURE
    replay_caught_up_fallback: bool = False

    def _mock_filings(self, cik: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_filings, 2)):
            rows.append(
                {
                    "accession_number": f"0000320193-26-{offset:06d}",
                    "cik": cik,
                    "form_type": "10-K" if offset == 0 else "10-Q",
                    "filing_date": (today - timedelta(days=90 * offset)).isoformat(),
                    "report_date": (today - timedelta(days=90 * offset)).isoformat(),
                    "primary_document_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/mock.htm",
                    "source_used": "sec_edgar",
                }
            )
        return rows

    def _mock_form4(self, cik: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_filings, 2)):
            rows.append(
                {
                    "accession_number": f"0000320193-26-{offset:06d}",
                    "cik": cik,
                    "issuer_symbol": "AAPL",
                    "owner_name": "Mock Insider",
                    "transaction_date": (today - timedelta(days=7 * offset)).isoformat(),
                    "transaction_code": "P",
                    "shares": str(1000 - offset * 100),
                    "price": str(180.0 + offset),
                    "source_used": "sec_edgar",
                }
            )
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_filings, cap=MAX_FILINGS, label="max_filings")
        cik = req.instrument_id or (self.ciks[0] if self.ciks else "")
        if not cik:
            raise PortError("FAILED", "missing CIK for SEC EDGAR mock fetch")
        _reject_unknown_cik(cik)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"sec-edgar-mock-{cik}-{uuid.uuid4().hex[:12]}"

        if self.data_domain == "us_filings" and self.replay_path.is_file():
            bundle = read_filings_evidence_bundle(self.replay_path)
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
                    sort_key=lambda row: str(row.get("filing_date") or ""),
                    min_rows=1,
                )
                if self.replay_caught_up_fallback
                else filtered
            )
            bundle = build_filings_evidence_bundle(
                filings=filings,
                source_fetch_id=str(bundle.get("source_fetch_id") or fetch_id),
                content_hash=str(bundle.get("content_hash") or "pending"),
                as_of_timestamp=str(bundle.get("as_of_timestamp") or retrieved_at),
                retrieved_at=str(bundle.get("retrieved_at") or retrieved_at),
            )
            row_count = len(filings)
        elif self.data_domain == "us_filings":
            filings = self._mock_filings(cik)
            bundle = build_filings_evidence_bundle(
                filings=filings,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
            row_count = len(filings)
        else:
            transactions = self._mock_form4(cik)
            bundle = build_form4_evidence_bundle(
                transactions=transactions,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
            row_count = len(transactions)

        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=row_count)


def _pad_cik(cik: str) -> str:
    return str(cik).lstrip("0").zfill(10)


def _fetch_sec_submissions_json(cik_padded: str, *, user_agent: str) -> dict[str, Any]:
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    last_error: Exception | None = None
    for _attempt in range(3):
        try:
            response = httpx.get(url, headers=headers, timeout=60.0)
            if response.status_code in (401, 403):
                raise PortError(
                    "USER_AUTH_REQUIRED",
                    f"SEC EDGAR access denied: HTTP {response.status_code}",
                )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return payload
            raise PortError("FAILED", "SEC submissions JSON root is not an object")
        except PortError:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise PortError("USER_AUTH_REQUIRED", f"SEC EDGAR access denied: {exc}") from exc
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        except (httpx.TransportError, json.JSONDecodeError) as exc:
            last_error = exc
            continue
    raise PortError("NETWORK_ERROR", str(last_error)) from last_error


def _sec_live_filings(
    cik: str,
    *,
    user_agent: str,
    max_filings: int,
    start_time: str | None,
    end_time: str | None,
) -> list[dict[str, Any]]:
    padded = _pad_cik(cik)
    raw = _fetch_sec_submissions_json(padded, user_agent=user_agent)
    recent = (raw.get("filings") or {}).get("recent") or {}
    accession_numbers = recent.get("accessionNumber") or []
    filing_dates = recent.get("filingDate") or []
    forms = recent.get("form") or []
    primary_docs = recent.get("primaryDocument") or []
    report_dates = recent.get("reportDate") or []

    filings: list[dict[str, Any]] = []
    for idx, accession in enumerate(accession_numbers):
        if len(filings) >= max_filings:
            break
        filing_date = filing_dates[idx] if idx < len(filing_dates) else ""
        row = {
            "accession_number": str(accession),
            "cik": padded,
            "form_type": str(forms[idx]) if idx < len(forms) else "",
            "filing_date": str(filing_date),
            "report_date": str(report_dates[idx] if idx < len(report_dates) else filing_date),
            "primary_document_url": (
                f"https://www.sec.gov/Archives/edgar/data/{padded.lstrip('0')}/{str(accession).replace('-', '')}/"
                f"{primary_docs[idx] if idx < len(primary_docs) else ''}"
            ),
            "source_used": "sec_edgar",
        }
        filings.append(row)
    filtered = _filter_filings_by_window(filings, start_time=start_time, end_time=end_time)
    if not filtered and filings:
        return filings[:max_filings]
    if not filtered:
        raise PortError("EMPTY_RESPONSE", f"no SEC filings for CIK {cik}")
    return filtered[:max_filings]


@dataclass(frozen=True)
class SecEdgarLiveFetchPort:
    """Bounded live SEC EDGAR submissions API fetch (fair-access User-Agent required)."""

    ciks: Sequence[str]
    max_filings: int
    data_domain: SecEdgarDomain

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_filings, cap=MAX_FILINGS, label="max_filings")
        user_agent = _sec_user_agent()
        if not user_agent:
            raise PortError(
                "USER_AUTH_REQUIRED",
                "SEC_EDGAR_USER_AGENT missing or lacks contact identity for live fetch",
            )
        cik = req.instrument_id or (self.ciks[0] if self.ciks else "")
        if not cik:
            raise PortError("FAILED", "missing CIK for SEC EDGAR live fetch")
        _reject_unknown_cik(cik)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"sec-edgar-live-{cik}-{uuid.uuid4().hex[:12]}"

        if self.data_domain == "us_filings":
            filings = _sec_live_filings(
                cik,
                user_agent=user_agent,
                max_filings=self.max_filings,
                start_time=req.start_time,
                end_time=req.end_time,
            )
            bundle = build_filings_evidence_bundle(
                filings=filings,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
            row_count = len(filings)
        else:
            # ponytail: Form 4 live parser deferred; upgrade = SEC ownership XML feed
            raise PortError("FAILED", "live SEC Form 4 fetch deferred; use us_filings domain")

        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=row_count)


def create_sec_edgar_fetch_port(
    *,
    ciks: Sequence[str],
    max_filings: int,
    data_domain: SecEdgarDomain,
    use_mock: bool = True,
):
    if len(ciks) > MAX_CIKS:
        raise PortError("FAILED", f"max {MAX_CIKS} CIKs allowed, got {len(ciks)}")
    if use_mock:
        return SecEdgarMockFetchPort(ciks=ciks, max_filings=max_filings, data_domain=data_domain)
    if not _sec_user_agent():
        raise PortError(
            "USER_AUTH_REQUIRED",
            "SEC_EDGAR_USER_AGENT missing or lacks contact identity for live fetch",
        )
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="sec_edgar")
    return SecEdgarLiveFetchPort(
        ciks=ciks,
        max_filings=max_filings,
        data_domain=data_domain,
    )
