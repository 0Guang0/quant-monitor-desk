"""Layer5 provenance bridge from evidence fetch bundles (R3-DCP-10 / ADR-012)."""

from __future__ import annotations

from typing import Any

from backend.app.datasources.normalizers.evidence_bundle import bundle_layer5_provenance
from backend.app.layer5_evidence.models import SourceProvenance


def build_source_provenance_from_bundle(
    bundle: dict[str, Any],
    *,
    clean_table: str = "security_bar_1d",
) -> SourceProvenance:
    """Map a finalized evidence bundle to Layer5 SourceProvenance (ADR-012)."""
    fetch_id = str(bundle.get("source_fetch_id") or "")
    content_hash = str(bundle.get("content_hash") or "")
    if not fetch_id:
        raise ValueError("bundle missing source_fetch_id for Layer5 provenance")
    if not content_hash:
        raise ValueError("bundle missing content_hash for Layer5 provenance")
    fields = bundle_layer5_provenance(bundle, clean_table=clean_table)
    return SourceProvenance(
        source_fetch_ids=fields["source_fetch_ids"],
        source_content_hashes=fields["source_content_hashes"],
        source_dataset_ids=fields["source_dataset_ids"],
    )
