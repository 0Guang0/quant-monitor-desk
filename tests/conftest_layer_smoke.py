"""Shared Layer5 factual_source smoke helpers for adapter replay tests."""

from __future__ import annotations

from datetime import date
from typing import Any

from backend.app.layer5_evidence.foundation import EvidenceFoundationValidator
from backend.app.layer5_evidence.models import (
    EvidenceFoundationRecord,
    EvidenceKind,
    InstrumentEvidenceRef,
    ManualReviewState,
    SourceProvenance,
)


def assert_layer5_factual_source_record(
    prov_fields: dict[str, Any],
  *,
  evidence_id: str,
  target_id: str,
  target_type: str,
  trade_date: date,
  evidence_summary: str,
  created_by: str,
  instrument_ref: InstrumentEvidenceRef,
) -> None:
    """Build a minimal factual_source record and assert foundation validation passes."""
    assert prov_fields["source_fetch_ids"]
    assert prov_fields["source_content_hashes"]
    record = EvidenceFoundationRecord(
        evidence_id=evidence_id,
        target_id=target_id,
        target_type=target_type,
        trade_date=trade_date,
        evidence_kind=EvidenceKind.FACTUAL_SOURCE,
        evidence_summary=evidence_summary,
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by=created_by,
        instrument_ref=instrument_ref,
        provenance=SourceProvenance(
            source_fetch_ids=prov_fields["source_fetch_ids"],
            source_content_hashes=prov_fields["source_content_hashes"],
        ),
    )
    EvidenceFoundationValidator().validate_record(record)
