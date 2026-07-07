"""Shared Layer3 snapshot build helpers for layer3/layer4 cross-layer tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from backend.app.layer3_chains.loader import STAGED_LAYER3_BUNDLE_DIR, IndustryChainLoader
from backend.app.layer3_chains.models import IndustryChainSnapshotBuildResult
from backend.app.layer3_chains.snapshot_builder import IndustryChainSnapshotBuilder

FIXTURE_L5 = Path(__file__).resolve().parent / "fixtures" / "layer3_l5_staged_bars"
AS_OF = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)
TRADE_DATE = date(2026, 6, 14)


def build_layer3_snapshot(
    *,
    l5_bundle_dir: Path = FIXTURE_L5,
    as_of: datetime = AS_OF,
) -> IndustryChainSnapshotBuildResult:
    """ponytail: shared build for layer3/layer4 AC tests."""
    load_result = IndustryChainLoader().load(bundle_dir=STAGED_LAYER3_BUNDLE_DIR)
    return IndustryChainSnapshotBuilder().build(
        load_result=load_result,
        as_of=as_of,
        trade_date=TRADE_DATE,
        l5_bundle_dir=l5_bundle_dir,
    )
