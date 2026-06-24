"""Layer 5 evidence read ports (023b SLICE-PORT)."""

from __future__ import annotations

from typing import Any, Protocol


class EvidenceReadPort(Protocol):
    """Inject staged bundle reads; builder must not import concrete storage."""

    def load_staged_bundle(self, instrument_id: str) -> dict[str, Any]:
        """Return staged evidence dict for the given instrument."""
