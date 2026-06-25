"""Sync job support matrix — contract loader and deferred job errors (B3V-SYNC)."""

from __future__ import annotations

from pathlib import Path

import yaml

DEFERRED_JOB_TYPE_CODE = "DEFERRED_JOB_TYPE"
DEFERRED_OWNER = "Round3F"
DEFERRED_PHASE = "R3F-SH-*"
DOCS_ANCHOR_D2_P1_1 = "D2-P1-1"

IMPLEMENTED_JOB_TYPES: frozenset[str] = frozenset(
    {"incremental", "backfill", "reconcile"}
)
RESERVED_JOB_TYPES: frozenset[str] = frozenset(
    {"full_load", "data_quality", "revision_audit"}
)

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / "specs" / "contracts" / "sync_job_contract.yaml"
)


class DeferredJobTypeError(Exception):
    """Reserved sync job type — stable deferred error (VR-SYNC-002 / D2-P1-1)."""

    def __init__(self, job_type: str, *, entrypoint: str) -> None:
        self.code = DEFERRED_JOB_TYPE_CODE
        self.job_type = job_type
        self.owner = DEFERRED_OWNER
        self.phase = DEFERRED_PHASE
        self.docs_anchor = DOCS_ANCHOR_D2_P1_1
        self.entrypoint = entrypoint
        super().__init__(
            f"{entrypoint}: job_type {job_type!r} is reserved ({self.code}); "
            f"owner={self.owner} phase={self.phase} docs_anchor={self.docs_anchor}"
        )


def load_sync_job_contract() -> dict:
    with _CONTRACT_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def raise_deferred_job_type(job_type: str, *, entrypoint: str) -> None:
    raise DeferredJobTypeError(job_type, entrypoint=entrypoint)
