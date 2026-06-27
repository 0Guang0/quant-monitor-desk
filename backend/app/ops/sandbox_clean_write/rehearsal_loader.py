"""Bounded rehearsal evidence loader (JQ2PTrade DataBundle shape, QMD-owned)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
    RehearsalCandidate,
    RehearsalPlanError,
    validate_contract_source_caps,
)

FIXTURE_EVIDENCE_DIRS: dict[str, Path] = {
    "baostock": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/baostock",
    "cninfo": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/cninfo",
    "fred": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/fred",
    "akshare": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/akshare",
    "yahoo_finance": PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/yahoo_finance",
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


@dataclass(frozen=True)
class StagingRow:
    instrument_id: str
    trade_date: str
    close: float
    source_used: str
    batch_id: str


def _in_date_window(trade_date: str, start_date: str | None, end_date: str | None) -> bool:
    if start_date and trade_date < start_date:
        return False
    if end_date and trade_date > end_date:
        return False
    return True


def _baostock_staging_rows(
    bundle: RehearsalDataBundle,
    *,
    batch_id: str,
    max_rows: int,
    start_date: str | None,
    end_date: str | None,
) -> list[StagingRow]:
    bars_path = bundle.evidence_dir / "bars.json"
    bars = json.loads(bars_path.read_text(encoding="utf-8"))
    if isinstance(bars, dict):
        bars = bars.get("rows") or []
    allowed = set(bundle.symbols_or_series)
    rows: list[StagingRow] = []
    for row in bars:
        if len(rows) >= max_rows:
            break
        inst = str(row.get("instrument_id") or row.get("symbol") or "")
        if inst not in allowed:
            continue
        trade_date = str(row.get("trade_date") or "")
        if not trade_date or not _in_date_window(trade_date, start_date, end_date):
            continue
        rows.append(
            StagingRow(
                instrument_id=inst,
                trade_date=trade_date,
                close=float(row.get("close") or 0.0),
                source_used=bundle.source_id,
                batch_id=batch_id,
            )
        )
    return rows


def _fred_staging_rows(
    bundle: RehearsalDataBundle,
    *,
    batch_id: str,
    max_rows: int,
    start_date: str | None,
    end_date: str | None,
) -> list[StagingRow]:
    payload = json.loads((bundle.evidence_dir / "fred_evidence.json").read_text(encoding="utf-8"))
    series_id = str(payload.get("series_id") or bundle.symbols_or_series[0])
    if series_id not in bundle.symbols_or_series:
        series_id = bundle.symbols_or_series[0]
    rows: list[StagingRow] = []
    for obs in payload.get("observations") or []:
        if len(rows) >= max_rows:
            break
        trade_date = str(obs.get("date") or obs.get("observation_date") or "")
        if not trade_date or not _in_date_window(trade_date, start_date, end_date):
            continue
        inst = str(obs.get("series_id") or series_id)
        if inst not in bundle.symbols_or_series:
            continue
        rows.append(
            StagingRow(
                instrument_id=inst,
                trade_date=trade_date,
                close=float(obs.get("value") or 0.0),
                source_used=bundle.source_id,
                batch_id=batch_id,
            )
        )
    return rows


def _cninfo_staging_rows(
    bundle: RehearsalDataBundle,
    *,
    batch_id: str,
    max_rows: int,
    start_date: str | None,
    end_date: str | None,
) -> list[StagingRow]:
    # ponytail: cninfo manifest has row_count only; synthetic dates for rehearsal cap
    manifest = json.loads(
        (bundle.evidence_dir / "pilot_v3_manifest.json").read_text(encoding="utf-8")
    )
    fetches = manifest.get("fetches") or []
    cninfo = next(
        (f for f in fetches if (f.get("request") or {}).get("source_id") == "cninfo"),
        None,
    )
    row_count = int((cninfo or {}).get("row_count") or bundle.staged_row_count or 0)
    row_count = min(row_count, max_rows)
    if row_count <= 0:
        return []
    symbols = bundle.symbols_or_series or ("cninfo",)
    win_start = start_date or bundle.window_start
    if win_start == "unknown":
        win_start = "2024-01-01"
    base = date.fromisoformat(win_start)
    rows: list[StagingRow] = []
    for i in range(row_count):
        inst = symbols[i % len(symbols)]
        trade_date = (base + timedelta(days=i)).isoformat()
        if not _in_date_window(trade_date, start_date, end_date):
            continue
        rows.append(
            StagingRow(
                instrument_id=inst,
                trade_date=trade_date,
                close=float(i + 1),
                source_used=bundle.source_id,
                batch_id=batch_id,
            )
        )
    return rows


_STAGING_ROW_BUILDERS = {
    "baostock": _baostock_staging_rows,
    "akshare": _baostock_staging_rows,
    "yahoo_finance": _baostock_staging_rows,
    "fred": _fred_staging_rows,
    "cninfo": _cninfo_staging_rows,
}


def staging_rows_from_bundle(
    bundle: RehearsalDataBundle,
    *,
    batch_id: str,
    max_rows: int,
    start_date: str | None = None,
    end_date: str | None = None,
    allow_window_fallback: bool = False,
) -> tuple[StagingRow, ...]:
    """Map bounded rehearsal evidence into stg_foundation_smoke row shape."""
    builder = _STAGING_ROW_BUILDERS.get(bundle.source_id)
    if builder is None:
        raise RehearsalLoaderError(f"no staging row builder for source: {bundle.source_id}")
    cap = min(max_rows, bundle.staged_row_count) if bundle.staged_row_count else max_rows
    rows = builder(
        bundle,
        batch_id=batch_id,
        max_rows=cap,
        start_date=start_date,
        end_date=end_date,
    )
    if not rows and bundle.staged_row_count > 0 and (start_date or end_date) and allow_window_fallback:
        # ponytail: staged fixtures may predate approval window; upgrade: align evidence dates or fail-closed
        rows = builder(
            bundle,
            batch_id=batch_id,
            max_rows=cap,
            start_date=None,
            end_date=None,
        )
    if not rows and bundle.staged_row_count > 0:
        raise RehearsalLoaderError(
            f"evidence produced zero staging rows for {bundle.source_id} within window/cap"
        )
    return tuple(rows)


def populate_staging_from_bundle(con, bundle: RehearsalDataBundle, **kwargs: Any) -> int:
    """DELETE stg_foundation_smoke and INSERT rows from bundle evidence."""
    rows = staging_rows_from_bundle(bundle, **kwargs)
    con.execute("DELETE FROM stg_foundation_smoke")
    for row in rows:
        con.execute(
            """
            INSERT INTO stg_foundation_smoke
            (instrument_id, trade_date, close, source_used, batch_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            [row.instrument_id, row.trade_date, row.close, row.source_used, row.batch_id],
        )
    return len(rows)


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
    # ponytail: bars.json bundle shape shared by baostock/akshare/yahoo_finance
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
    "akshare": _load_baostock_bundle,
    "yahoo_finance": _load_baostock_bundle,
    "cninfo": _load_cninfo_bundle,
    "fred": _load_fred_bundle,
}


def load_rehearsal_bundle(
    candidate: RehearsalCandidate,
    *,
    evidence_dir: Path | None = None,
    dry_run: bool = True,
    cap_profile: str = "r3g01",
) -> RehearsalDataBundle:
    """Load bounded raw/staged evidence for one rehearsal candidate."""
    try:
        validate_contract_source_caps(
            source_id=candidate.source_id,
            domain=candidate.domain,
            symbols=candidate.symbols_or_series,
            window_days=candidate.window_days,
            metadata_only=candidate.metadata_only,
            profile=cap_profile,
            error_cls=RehearsalPlanError,
        )
    except RehearsalPlanError as exc:
        raise RehearsalLoaderError(str(exc)) from exc
    path = _resolve_evidence_dir(candidate.source_id, evidence_dir, dry_run=dry_run)
    loader = _LOADERS.get(candidate.source_id)
    if loader is None:
        raise RehearsalLoaderError(f"unsupported rehearsal source: {candidate.source_id}")
    return loader(path, candidate)
