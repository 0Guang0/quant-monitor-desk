"""Layer 5 instrument_registry staged row validation (023b SLICE-REGISTRY)."""

from __future__ import annotations

from collections.abc import Sequence

from backend.app.layer5_evidence.models import InstrumentEvidenceRef

_REQUIRED_STRING_FIELDS = (
    "instrument_id",
    "symbol",
    "asset_type",
    "market_id",
    "exchange",
    "currency",
)


class InstrumentRegistryError(ValueError):
    """Invalid instrument_registry row or duplicate instrument_id in bundle."""


class InstrumentRegistryValidator:
    """Validate staged instrument_registry rows; reuse 023A InstrumentEvidenceRef shape."""

    def validate_row(self, row: InstrumentEvidenceRef) -> None:
        for field_name in _REQUIRED_STRING_FIELDS:
            if not getattr(row, field_name).strip():
                raise InstrumentRegistryError(f"{field_name} is required")

    def validate_bundle(self, rows: Sequence[InstrumentEvidenceRef]) -> None:
        seen: set[str] = set()
        for row in rows:
            self.validate_row(row)
            instrument_id = row.instrument_id.strip()
            if instrument_id in seen:
                raise InstrumentRegistryError(f"duplicate instrument_id {instrument_id!r}")
            seen.add(instrument_id)
