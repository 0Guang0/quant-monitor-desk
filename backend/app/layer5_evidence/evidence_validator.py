"""Staged Layer 5 evidence row validation (023b SLICE-MODELS)."""

from __future__ import annotations

from datetime import date

from backend.app.layer5_evidence.models import SecurityBarDaily

_REQUIRED_BAR_FIELDS = (
    "instrument_id",
    "source",
    "quality_flag",
)


class EvidenceValidationError(ValueError):
    """Invalid staged evidence row."""


class StagedEvidenceValidator:
    """Validate staged bar/event rows against contract and as_of window."""

    def validate_bar(self, bar: SecurityBarDaily, *, as_of_end: date) -> None:
        for field_name in _REQUIRED_BAR_FIELDS:
            if not getattr(bar, field_name).strip():
                raise EvidenceValidationError(f"{field_name} is required")
        if bar.trade_date > as_of_end:
            raise EvidenceValidationError(
                f"future trade_date {bar.trade_date} exceeds as_of window end {as_of_end}"
            )
        if bar.high < bar.low:
            raise EvidenceValidationError("high must be >= low")
        if bar.volume < 0 or bar.amount < 0:
            raise EvidenceValidationError("volume and amount must be non-negative")
