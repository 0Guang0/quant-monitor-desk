"""Bounded rehearsal evidence loader (JQ2PTrade DataBundle shape, QMD-owned)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
    RehearsalCandidate,
    RehearsalPlanError,
    validate_source_caps,
)

FIXTURE_EVIDENCE_DIRS: dict[str, Path] = {
    "baostock": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/baostock",
    "cninfo": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/cninfo",
    "fred": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/fred",
}


class RehearsalLoaderError(RuntimeError):
    """Evidence bundle could not be loaded within rehearsal bounds."""


@dataclass(frozen=True)
class RehearsalDataBundle:
    source_id: str
    domain: str
    symbols_or_series: tuple[str, ...]
    window_start: str
    window_end: str
    raw_row_count: int
    staged_row_count: int
    source_fetch_ids: tuple[str, ...]
    content_hashes: tuple[str, ...]
    schema_hashes: tuple[str, ...]
    evidence_dir: Path


def _resolve_evidence_dir(source_id: str, evidence_dir: Path | None, *, dry_run: bool) -> Path:
    if evidence_dir is not None:
        resolved = evidence_dir
        if not resolved.is_absolute():
            resolved = PROJECT_ROOT / resolved
        if not resolved.is_dir():
            raise RehearsalLoaderError(f"evidence dir missing: {evidence_dir}")
        return resolved.resolve()
    if dry_run:
        fixture = FIXTURE_EVIDENCE_DIRS.get(source_id)
        if fixture is None or not fixture.is_dir():
            raise RehearsalLoaderError(f"no dry_run fixture for source: {source_id}")
        return fixture
    raise RehearsalLoaderError("evidence_dir required when dry_run=false")


def _load_baostock_bundle(path: Path, candidate: RehearsalCandidate) -> RehearsalDataBundle:
    # ponytail: evidence row cap enforced upstream via validate_source_caps + max_rows in DH
    bars_path = path / "bars.json"
    if not bars_path.is_file():
        raise RehearsalLoaderError(f"missing bars.json in {path}")
    bars = json.loads(bars_path.read_text(encoding="utf-8"))
    if isinstance(bars, dict):
        bars = bars.get("rows") or []
    if not isinstance(bars, list):
        raise RehearsalLoaderError("bars.json must contain a list of rows")
    raw_manifest_path = path / "raw_evidence_manifest.json"
    fetch_ids: list[str] = []
    content_hashes: list[str] = []
    schema_hashes: list[str] = []
    if raw_manifest_path.is_file():
        manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("fetches") or []:
            fr = item.get("fetch_result") or {}
            if fr.get("source_fetch_id"):
                fetch_ids.append(str(fr["source_fetch_id"]))
            if fr.get("content_hash"):
                content_hashes.append(str(fr["content_hash"]))
            if fr.get("schema_hash"):
                schema_hashes.append(str(fr["schema_hash"]))
    dates = sorted(str(row.get("trade_date")) for row in bars if row.get("trade_date"))
    return RehearsalDataBundle(
        source_id=candidate.source_id,
        domain=candidate.domain,
        symbols_or_series=candidate.symbols_or_series,
        window_start=dates[0] if dates else "unknown",
        window_end=dates[-1] if dates else "unknown",
        raw_row_count=len(bars),
        staged_row_count=len(bars),
        source_fetch_ids=tuple(fetch_ids),
        content_hashes=tuple(content_hashes),
        schema_hashes=tuple(schema_hashes),
        evidence_dir=path,
    )


def _load_cninfo_bundle(path: Path, candidate: RehearsalCandidate) -> RehearsalDataBundle:
    manifest_path = path / "pilot_v3_manifest.json"
    if not manifest_path.is_file():
        raise RehearsalLoaderError(f"missing pilot_v3_manifest.json in {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fetches = manifest.get("fetches") or []
    cninfo = next(
        (f for f in fetches if (f.get("request") or {}).get("source_id") == "cninfo"),
        None,
    )
    if cninfo is None:
        raise RehearsalLoaderError("cninfo fetch missing from manifest")
    row_count = int(cninfo.get("row_count") or 0)
    fr = cninfo.get("fetch_result") or {}
    return RehearsalDataBundle(
        source_id=candidate.source_id,
        domain=candidate.domain,
        symbols_or_series=candidate.symbols_or_series,
        window_start="2024-01-01",
        window_end="2024-01-30",
        raw_row_count=row_count,
        staged_row_count=row_count,
        source_fetch_ids=(str(fr.get("run_id") or "cninfo-staged"),),
        content_hashes=(str(fr.get("content_hash") or "cninfo-hash"),),
        schema_hashes=(),
        evidence_dir=path,
    )


def _load_fred_bundle(path: Path, candidate: RehearsalCandidate) -> RehearsalDataBundle:
    evidence_path = path / "fred_evidence.json"
    if not evidence_path.is_file():
        raise RehearsalLoaderError(f"missing fred_evidence.json in {path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    observations = payload.get("observations") or []
    return RehearsalDataBundle(
        source_id=candidate.source_id,
        domain=candidate.domain,
        symbols_or_series=candidate.symbols_or_series,
        window_start=str(observations[0].get("date")) if observations else "unknown",
        window_end=str(observations[-1].get("date")) if observations else "unknown",
        raw_row_count=len(observations),
        staged_row_count=len(observations),
        source_fetch_ids=(str(payload.get("source_fetch_id") or "fred-fetch"),),
        content_hashes=(str(payload.get("content_hash") or "fred-hash"),),
        schema_hashes=(),
        evidence_dir=path,
    )


_LOADERS = {
    "baostock": _load_baostock_bundle,
    "cninfo": _load_cninfo_bundle,
    "fred": _load_fred_bundle,
}


def load_rehearsal_bundle(
    candidate: RehearsalCandidate,
    *,
    evidence_dir: Path | None = None,
    dry_run: bool = True,
) -> RehearsalDataBundle:
    """Load bounded raw/staged evidence for one rehearsal candidate."""
    try:
        validate_source_caps(candidate)
    except RehearsalPlanError as exc:
        raise RehearsalLoaderError(str(exc)) from exc
    path = _resolve_evidence_dir(candidate.source_id, evidence_dir, dry_run=dry_run)
    loader = _LOADERS.get(candidate.source_id)
    if loader is None:
        raise RehearsalLoaderError(f"unsupported rehearsal source: {candidate.source_id}")
    return loader(path, candidate)
