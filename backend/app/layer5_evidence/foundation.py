"""Layer 5 evidence foundation validation (023A minimal slice)."""

from __future__ import annotations

import hashlib
import json
import re

from backend.app.layer5_evidence.models import (
    EvidenceFoundationRecord,
    EvidenceKind,
    ManualReviewState,
    SourceProvenance,
)

_AGENT_CREATED_BY_PATTERN = re.compile(r"^agent", re.IGNORECASE)
_AGENT_TEXT_PATTERN = re.compile(
    r"(agent[_-]?summary|generated_by=agent|建议|买入|卖出|信号)",
    re.IGNORECASE,
)


class EvidenceFoundationError(ValueError):
    """Invalid evidence foundation record or provenance."""


class EvidenceFoundationValidator:
    """Validate minimal evidence identity without ingestion or DB writes."""

    def validate_record(self, record: EvidenceFoundationRecord) -> None:
        if not record.evidence_id.strip():
            raise EvidenceFoundationError("evidence_id is required")
        if not record.target_id.strip():
            raise EvidenceFoundationError("target_id is required")
        if not record.target_type.strip():
            raise EvidenceFoundationError("target_type is required")

        self._validate_manual_review(record)
        self._validate_kind_provenance(record)

        if record.evidence_kind == EvidenceKind.FACTUAL_SOURCE:
            self.reject_agent_text_as_fact_source(
                text=record.evidence_summary,
                created_by=record.created_by,
            )

    def reject_agent_text_as_fact_source(self, *, text: str, created_by: str) -> None:
        if _AGENT_CREATED_BY_PATTERN.match(created_by.strip()):
            raise EvidenceFoundationError(
                "agent-created prose cannot be used as factual evidence source"
            )
        if _AGENT_TEXT_PATTERN.search(text):
            raise EvidenceFoundationError(
                "agent-generated text markers cannot appear in factual evidence summary"
            )

    def build_identity_hash(self, record: EvidenceFoundationRecord) -> str:
        self.validate_record(record)
        payload = {
            "evidence_id": record.evidence_id,
            "target_id": record.target_id,
            "target_type": record.target_type,
            "trade_date": record.trade_date.isoformat(),
            "evidence_kind": record.evidence_kind.value,
            "created_by": record.created_by,
            "rule_version": record.rule_version,
            "code_version": record.code_version,
            "parameter_hash": record.parameter_hash,
            "provenance": _provenance_payload(record.provenance),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _validate_manual_review(self, record: EvidenceFoundationRecord) -> None:
        needs_queue = (
            record.need_human_review
            and record.manual_review_state == ManualReviewState.NOT_REQUIRED
        )
        if needs_queue:
            raise EvidenceFoundationError(
                "need_human_review=True requires manual_review_state=queued "
                "(R3-PARTIAL-4 severe defer)"
            )
        if not record.need_human_review and record.manual_review_state == ManualReviewState.QUEUED:
            raise EvidenceFoundationError(
                "manual_review_state=queued requires need_human_review=True"
            )

    def _validate_kind_provenance(self, record: EvidenceFoundationRecord) -> None:
        if record.evidence_kind == EvidenceKind.AGENT_INTERPRETATION:
            if record.provenance is not None:
                raise EvidenceFoundationError(
                    "agent_interpretation must not carry factual source provenance"
                )
            return

        if record.provenance is None:
            raise EvidenceFoundationError(
                f"{record.evidence_kind.value} requires source provenance"
            )
        _validate_provenance_traceable(record.provenance)


def _validate_provenance_traceable(provenance: SourceProvenance) -> None:
    has_fetch = bool(provenance.source_fetch_ids)
    has_hash = bool(provenance.source_content_hashes)
    if not has_fetch and not has_hash:
        raise EvidenceFoundationError(
            "factual evidence must trace to source_fetch_ids or source_content_hashes"
        )
    for dataset_id in provenance.source_dataset_ids:
        if _AGENT_TEXT_PATTERN.search(dataset_id):
            raise EvidenceFoundationError(
                f"agent outputs must not appear in source_dataset_ids: {dataset_id!r}"
            )


def _provenance_payload(provenance: SourceProvenance | None) -> dict[str, list[str]] | None:
    if provenance is None:
        return None
    return {
        "source_fetch_ids": list(provenance.source_fetch_ids),
        "source_content_hashes": list(provenance.source_content_hashes),
        "source_dataset_ids": list(provenance.source_dataset_ids),
    }
