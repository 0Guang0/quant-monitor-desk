"""SEC EDGAR disclosure evidence normalizer (R3H-01)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

SEC_EDGAR_EVIDENCE_SCHEMA_VERSION = "sec_edgar_evidence_v1"

SecEdgarDomain = Literal["us_filings", "us_insider_form4"]


class SecEdgarEvidenceError(ValueError):
    """SEC EDGAR evidence bundle is invalid or incomplete."""


def _normalize_filing(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "accession_number": str(row.get("accession_number") or ""),
        "cik": str(row.get("cik") or ""),
        "form_type": str(row.get("form_type") or ""),
        "filing_date": str(row.get("filing_date") or ""),
        "report_date": str(row.get("report_date") or row.get("filing_date") or ""),
        "primary_document_url": str(row.get("primary_document_url") or ""),
        "source_used": str(row.get("source_used") or "sec_edgar"),
    }


def _normalize_form4(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "accession_number": str(row.get("accession_number") or ""),
        "cik": str(row.get("cik") or ""),
        "issuer_symbol": str(row.get("issuer_symbol") or ""),
        "owner_name": str(row.get("owner_name") or ""),
        "transaction_date": str(row.get("transaction_date") or ""),
        "transaction_code": str(row.get("transaction_code") or ""),
        "shares": row.get("shares"),
        "price": row.get("price"),
        "source_used": str(row.get("source_used") or "sec_edgar"),
    }


def build_filings_evidence_bundle(
    *,
    filings: list[dict[str, Any]],
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "sec_edgar",
) -> dict[str, Any]:
    norm = [_normalize_filing(row) for row in filings]
    if not norm:
        raise SecEdgarEvidenceError("filings evidence bundle requires filings")
    return {
        "schema_version": SEC_EDGAR_EVIDENCE_SCHEMA_VERSION,
        "source_id": source_id,
        "data_domain": "us_filings",
        "filings": norm,
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
    }


def build_form4_evidence_bundle(
    *,
    transactions: list[dict[str, Any]],
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "sec_edgar",
) -> dict[str, Any]:
    norm = [_normalize_form4(row) for row in transactions]
    if not norm:
        raise SecEdgarEvidenceError("form4 evidence bundle requires transactions")
    return {
        "schema_version": SEC_EDGAR_EVIDENCE_SCHEMA_VERSION,
        "source_id": source_id,
        "data_domain": "us_insider_form4",
        "transactions": norm,
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
    }


def read_filings_evidence_bundle(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path)
    if not evidence_path.is_file():
        raise SecEdgarEvidenceError(f"missing filings evidence: {evidence_path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    filings = [_normalize_filing(row) for row in payload.get("filings") or []]
    if not filings:
        raise SecEdgarEvidenceError("filings evidence bundle has no filings")
    return build_filings_evidence_bundle(
        filings=filings,
        source_id=str(payload.get("source_id") or "sec_edgar"),
        source_fetch_id=str(payload.get("source_fetch_id") or "sec-edgar-unknown"),
        content_hash=str(payload.get("content_hash") or "sec-edgar-unknown-hash"),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
    )


def read_form4_evidence_bundle(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path)
    if not evidence_path.is_file():
        raise SecEdgarEvidenceError(f"missing form4 evidence: {evidence_path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    transactions = [_normalize_form4(row) for row in payload.get("transactions") or []]
    if not transactions:
        raise SecEdgarEvidenceError("form4 evidence bundle has no transactions")
    return build_form4_evidence_bundle(
        transactions=transactions,
        source_id=str(payload.get("source_id") or "sec_edgar"),
        source_fetch_id=str(payload.get("source_fetch_id") or "sec-edgar-unknown"),
        content_hash=str(payload.get("content_hash") or "sec-edgar-unknown-hash"),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
    )
