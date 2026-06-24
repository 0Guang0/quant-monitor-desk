"""Layer 5 evidence foundation domain models (Round 3 Batch 5A / 023A)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class EvidenceKind(StrEnum):
    """Distinguish factual source evidence from derived validation and Agent prose."""

    FACTUAL_SOURCE = "factual_source"
    DERIVED_VALIDATION = "derived_validation"
    AGENT_INTERPRETATION = "agent_interpretation"


class ManualReviewState(StrEnum):
    """Explicit manual-review queue semantics for foundation slice.

    Severe instant queue UX remains deferred under ``R3-PARTIAL-4``.
    """

    NOT_REQUIRED = "not_required"
    QUEUED = "queued"


@dataclass(frozen=True)
class SecurityBarDaily:
    """Staged security_bar_daily row per layer5_evidence_contract.yaml."""

    instrument_id: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    source: str
    quality_flag: str
    adjust_type: str = "none"


@dataclass(frozen=True)
class LayerContextBundle:
    """Upstream layer context slots for evidence_chain builder."""

    layer3_context: str
    layer4_context: str
    upstream_snapshot_ids: tuple[str, ...]
    layer1_context: str = ""
    layer2_context: str = ""
    layer5_context: str = ""


@dataclass(frozen=True)
class EvidenceChainRecord:
    """Staged evidence_chain row; not a DB persistence type."""

    evidence_id: str
    target_id: str
    target_type: str
    trade_date: date
    layer1_context: str
    layer2_context: str
    layer3_context: str
    layer4_context: str
    layer5_context: str
    evidence_summary: str
    confidence: float
    need_human_review: bool
    manual_review_state: ManualReviewState
    created_by: str
    upstream_snapshot_ids: tuple[str, ...]


@dataclass(frozen=True)
class InstrumentEvidenceRef:
    """Minimal instrument identity reference for Layer2-4 downstream use."""

    instrument_id: str
    symbol: str
    asset_type: str
    market_id: str
    exchange: str
    currency: str
    is_active: bool


@dataclass(frozen=True)
class SourceProvenance:
    """Traceability surface: every factual evidence must cite fetch IDs or content hashes."""

    source_fetch_ids: tuple[str, ...]
    source_content_hashes: tuple[str, ...]
    source_dataset_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceFoundationRecord:
    """Minimal evidence identity record; not the full evidence_chain table row."""

    evidence_id: str
    target_id: str
    target_type: str
    trade_date: date
    evidence_kind: EvidenceKind
    evidence_summary: str
    need_human_review: bool
    manual_review_state: ManualReviewState
    created_by: str
    instrument_ref: InstrumentEvidenceRef | None = None
    provenance: SourceProvenance | None = None
    rule_version: str = "layer5-foundation-v1"
    code_version: str = "layer5-foundation-v1"
    parameter_hash: str = ""
