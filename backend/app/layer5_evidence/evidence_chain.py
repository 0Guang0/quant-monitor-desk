"""Layer 5 evidence chain builder (023b SLICE-CHAIN / CONFLICT)."""

from __future__ import annotations

from typing import Any

from backend.app.layer5_evidence.evidence_validator import StagedEvidenceValidator
from backend.app.layer5_evidence.foundation import EvidenceFoundationValidator
from backend.app.layer5_evidence.models import (
    EvidenceChainRecord,
    EvidenceFoundationRecord,
    LayerContextBundle,
    ManualReviewState,
    SecurityBarDaily,
)
from backend.app.layer5_evidence.ports import EvidenceReadPort


class EvidenceChainError(ValueError):
    """Invalid evidence chain build input or conflict policy violation."""


class EvidenceChainBuilder:
    """Compose foundation validation with upstream layer context slots."""

    def __init__(
        self,
        *,
        foundation: EvidenceFoundationValidator | None = None,
        staged_validator: StagedEvidenceValidator | None = None,
        read_port: EvidenceReadPort | None = None,
    ) -> None:
        self._foundation = foundation or EvidenceFoundationValidator()
        self._staged = staged_validator or StagedEvidenceValidator()
        self._read_port = read_port

    def build(
        self,
        *,
        record: EvidenceFoundationRecord,
        layer_context: LayerContextBundle,
        conflict_severity: str | None = None,
        confidence: float = 0.8,
    ) -> EvidenceChainRecord:
        self._foundation.validate_record(record)
        need_human_review, manual_review_state = self._resolve_manual_review(
            record, conflict_severity
        )
        if not layer_context.upstream_snapshot_ids:
            raise EvidenceChainError("upstream_snapshot_ids required for evidence chain")
        if not layer_context.layer3_context.strip() or not layer_context.layer4_context.strip():
            raise EvidenceChainError("layer3_context and layer4_context are required")

        return EvidenceChainRecord(
            evidence_id=record.evidence_id,
            target_id=record.target_id,
            target_type=record.target_type,
            trade_date=record.trade_date,
            layer1_context=layer_context.layer1_context,
            layer2_context=layer_context.layer2_context,
            layer3_context=layer_context.layer3_context,
            layer4_context=layer_context.layer4_context,
            layer5_context=layer_context.layer5_context or record.evidence_summary,
            evidence_summary=record.evidence_summary,
            confidence=confidence,
            need_human_review=need_human_review,
            manual_review_state=manual_review_state,
            created_by=record.created_by,
            upstream_snapshot_ids=layer_context.upstream_snapshot_ids,
        )

    def build_from_port(self, instrument_id: str) -> EvidenceChainRecord:
        if self._read_port is None:
            raise EvidenceChainError("EvidenceReadPort required for build_from_port")
        bundle = self._read_port.load_staged_bundle(instrument_id)
        record = _record_from_bundle(bundle)
        layer_context = _layer_context_from_bundle(bundle)
        conflict = bundle.get("conflict_severity")
        return self.build(
            record=record,
            layer_context=layer_context,
            conflict_severity=str(conflict) if conflict else None,
        )

    def validate_bar_from_bundle(self, bundle: dict[str, Any]) -> SecurityBarDaily:
        bar = _bar_from_bundle(bundle)
        as_of_end = record_trade_date(bundle)
        self._staged.validate_bar(bar, as_of_end=as_of_end)
        return bar

    def _resolve_manual_review(
        self,
        record: EvidenceFoundationRecord,
        conflict_severity: str | None,
    ) -> tuple[bool, ManualReviewState]:
        if conflict_severity == "severe":
            return True, ManualReviewState.QUEUED
        if record.manual_review_state == ManualReviewState.QUEUED and not record.need_human_review:
            raise EvidenceChainError(
                "manual_review_state=queued requires need_human_review=True"
            )
        return record.need_human_review, record.manual_review_state


def _bar_from_bundle(bundle: dict[str, Any]) -> SecurityBarDaily:
    raw = bundle.get("security_bar") or {}
    return SecurityBarDaily(
        instrument_id=str(raw.get("instrument_id") or bundle.get("instrument_id") or ""),
        trade_date=record_trade_date(bundle),
        open=float(raw.get("open", 0)),
        high=float(raw.get("high", 0)),
        low=float(raw.get("low", 0)),
        close=float(raw.get("close", 0)),
        volume=float(raw.get("volume", 0)),
        amount=float(raw.get("amount", 0)),
        source=str(raw.get("source") or "staged_fixture"),
        quality_flag=str(raw.get("quality_flag") or "STAGED"),
        adjust_type=str(raw.get("adjust_type") or "none"),
    )


def record_trade_date(bundle: dict[str, Any]) -> Any:
    from datetime import date

    raw = bundle.get("trade_date") or (bundle.get("security_bar") or {}).get("trade_date")
    if isinstance(raw, date):
        return raw
    return date.fromisoformat(str(raw))


def _record_from_bundle(bundle: dict[str, Any]) -> EvidenceFoundationRecord:
    from backend.app.layer5_evidence.models import EvidenceKind, SourceProvenance

    provenance_raw = bundle.get("provenance") or {}
    provenance = SourceProvenance(
        source_fetch_ids=tuple(provenance_raw.get("source_fetch_ids") or ()),
        source_content_hashes=tuple(provenance_raw.get("source_content_hashes") or ()),
        source_dataset_ids=tuple(provenance_raw.get("source_dataset_ids") or ()),
    )
    return EvidenceFoundationRecord(
        evidence_id=str(bundle.get("evidence_id") or ""),
        target_id=str(bundle.get("target_id") or bundle.get("instrument_id") or ""),
        target_type=str(bundle.get("target_type") or "instrument"),
        trade_date=record_trade_date(bundle),
        evidence_kind=EvidenceKind.FACTUAL_SOURCE,
        evidence_summary=str(bundle.get("evidence_summary") or ""),
        need_human_review=bool(bundle.get("need_human_review", False)),
        manual_review_state=ManualReviewState(
            str(bundle.get("manual_review_state") or ManualReviewState.NOT_REQUIRED.value)
        ),
        created_by=str(bundle.get("created_by") or "layer5_evidence_chain"),
        provenance=provenance,
    )


def _layer_context_from_bundle(bundle: dict[str, Any]) -> LayerContextBundle:
    upstream = bundle.get("upstream_snapshot_ids") or ()
    return LayerContextBundle(
        layer3_context=str(bundle.get("layer3_context") or ""),
        layer4_context=str(bundle.get("layer4_context") or ""),
        upstream_snapshot_ids=tuple(str(item) for item in upstream),
        layer1_context=str(bundle.get("layer1_context") or ""),
        layer2_context=str(bundle.get("layer2_context") or ""),
        layer5_context=str(bundle.get("layer5_context") or ""),
    )


def reject_agent_text_as_fact(*, text: str, created_by: str) -> None:
    """Fail-closed guard reused by chain tests; delegates to foundation validator."""
    EvidenceFoundationValidator().reject_agent_text_as_fact_source(text=text, created_by=created_by)
