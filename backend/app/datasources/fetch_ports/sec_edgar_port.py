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
from typing import Any, Literal

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.sec_edgar import (
    build_filings_evidence_bundle,
    build_form4_evidence_bundle,
)

# R3H-01 caps SSOT (frozen §7 production-entry defaults)
CIK_WHITELIST = frozenset({"0000320193", "0000789019", "0001018724"})
MAX_CIKS = 5
MAX_FILINGS = 50

SecEdgarDomain = Literal["us_filings", "us_insider_form4"]


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

        if self.data_domain == "us_filings":
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


@dataclass(frozen=True)
class SecEdgarLiveFetchPort:
    """Product live SEC EDGAR port — ponytail: mock delegate when live branch enabled."""

    ciks: Sequence[str]
    max_filings: int
    data_domain: SecEdgarDomain

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        if not _sec_user_agent():
            raise PortError(
                "USER_AUTH_REQUIRED",
                "SEC_EDGAR_USER_AGENT missing or lacks contact identity for live fetch",
            )
        return SecEdgarMockFetchPort(
            ciks=self.ciks, max_filings=self.max_filings, data_domain=self.data_domain
        ).fetch_payload(req)


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
    return SecEdgarLiveFetchPort(ciks=ciks, max_filings=max_filings, data_domain=data_domain)
