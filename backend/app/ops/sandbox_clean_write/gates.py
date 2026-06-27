"""Public gate-chain API for sandbox / limited-production clean-write runners.

ponytail: thin re-export from rehearsal_runner; upgrade path is extract compose_clean_write_gates().
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.datasources.service import DataSourceService
from backend.app.ops.sandbox_clean_write.rehearsal_plan import RehearsalCandidate
from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
    REQUIRED_GATES,
    _assert_data_health_admission,
    _coverage_ratio,
    _preview_route,
    _run_source_data_health,
    _validation_status_from_dh,
)

assert_data_health_admission = _assert_data_health_admission
coverage_ratio = _coverage_ratio
preview_route = _preview_route
validation_status_from_dh = _validation_status_from_dh


def run_source_data_health(
    candidate: RehearsalCandidate,
    evidence_dir: Path,
    *,
    max_rows: int = 1000,
):
    return _run_source_data_health(candidate, evidence_dir, max_rows=max_rows)


def preview_route_for_candidate(
    candidate: RehearsalCandidate,
    service: DataSourceService,
) -> dict[str, Any]:
    return _preview_route(candidate, service)


__all__ = [
    "REQUIRED_GATES",
    "assert_data_health_admission",
    "coverage_ratio",
    "preview_route_for_candidate",
    "run_source_data_health",
    "validation_status_from_dh",
]
