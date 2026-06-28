"""Bounded rehearsal evidence loader (JQ2PTrade DataBundle shape, QMD-owned)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.normalizers.official_macro import read_fred_evidence_bundle
from backend.app.layer1_axes.observation_contract import AXIS_OBSERVATION_DDL_COLUMNS
from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
    RehearsalCandidate,
    RehearsalPlanError,
    validate_contract_source_caps,
)

# ponytail: pilot bundle byte cap; upgrade: stream parse / Parquet evidence (Wave 3 live)
_MAX_BARS_JSON_BYTES = 8 * 1024 * 1024

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
    open: float | None = None
    high: float | None = None
    low: float | None = None
    pre_close: float | None = None
    volume: float | None = None
    amount: float | None = None
    adjustment_type: str = "none"
    quality_flags: str | None = None
    created_at: datetime | None = None

    def to_bar_staging_values(self) -> list[object]:
        # ponytail: close-only sources backfill open/high/low from close; upgrade: fail-closed
        # when bar domain requires explicit OHLCV (Wave 3 live sources).
        close = self.close
        open_ = self.open if self.open is not None else close
        high = self.high if self.high is not None else close
        low = self.low if self.low is not None else close
        created = self.created_at or datetime.now(UTC)
        return [
            self.instrument_id,
            self.trade_date,
            open_,
            high,
            low,
            close,
            self.pre_close,
            self.volume,
            self.amount,
            self.adjustment_type,
            self.source_used,
            self.batch_id,
            self.quality_flags,
            created,
        ]


_BAR_STAGING_COLUMNS = (
    "instrument_id",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "volume",
    "amount",
    "adjustment_type",
    "source_used",
    "batch_id",
    "quality_flags",
    "created_at",
)


@dataclass(frozen=True)
class DisclosureStagingRow:
    announcement_id: str
    instrument_id: str
    title: str
    publish_timestamp: datetime
    announcement_url: str | None
    announcement_type: str | None
    data_domain: str
    source_used: str
    pdf_file_id: str | None
    extracted_text_file_id: str | None
    content_status: str
    batch_id: str
    source_fetch_id: str | None
    content_hash: str | None
    schema_hash: str | None
    quality_flags: str | None
    created_at: datetime

    def to_staging_values(self) -> list[object]:
        return [
            self.announcement_id,
            self.instrument_id,
            self.title,
            self.publish_timestamp,
            self.announcement_url,
            self.announcement_type,
            self.data_domain,
            self.source_used,
            self.pdf_file_id,
            self.extracted_text_file_id,
            self.content_status,
            self.batch_id,
            self.source_fetch_id,
            self.content_hash,
            self.schema_hash,
            self.quality_flags,
            self.created_at,
        ]


_DISCLOSURE_STAGING_COLUMNS = (
    "announcement_id",
    "instrument_id",
    "title",
    "publish_timestamp",
    "announcement_url",
    "announcement_type",
    "data_domain",
    "source_used",
    "pdf_file_id",
    "extracted_text_file_id",
    "content_status",
    "batch_id",
    "source_fetch_id",
    "content_hash",
    "schema_hash",
    "quality_flags",
    "created_at",
)


def _validate_announcement_url(url: str | None) -> None:
    if url is None:
        return
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):
        raise RehearsalLoaderError(f"announcement_url scheme not allowed: {url!r}")


def _validate_pdf_file_id(con, pdf_file_id: str | None) -> None:
    if pdf_file_id is None:
        return
    row = con.execute(
        "SELECT 1 FROM file_registry WHERE file_id = ? LIMIT 1", [pdf_file_id]
    ).fetchone()
    if row is None:
        raise RehearsalLoaderError(f"pdf_file_id not in file_registry: {pdf_file_id!r}")


def _validate_disclosure_staging_row(con, row: DisclosureStagingRow) -> None:
    _validate_announcement_url(row.announcement_url)
    _validate_pdf_file_id(con, row.pdf_file_id)


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
    # ponytail: full-file json.loads; upgrade: stream-parse or byte cap per GLOBAL_RESOURCE_LIMITS
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
        close = float(row.get("close") or 0.0)
        rows.append(
            StagingRow(
                instrument_id=inst,
                trade_date=trade_date,
                close=close,
                source_used=bundle.source_id,
                batch_id=batch_id,
                open=float(row["open"]) if row.get("open") is not None else close,
                high=float(row["high"]) if row.get("high") is not None else close,
                low=float(row["low"]) if row.get("low") is not None else close,
                pre_close=float(row["pre_close"]) if row.get("pre_close") is not None else None,
                volume=float(row["volume"]) if row.get("volume") is not None else None,
                amount=float(row["amount"]) if row.get("amount") is not None else None,
                adjustment_type=str(row.get("adjustment_type") or "none"),
            )
        )
    return rows


def _disclosure_rows_from_bundle(
    bundle: RehearsalDataBundle,
    *,
    batch_id: str,
    max_rows: int,
    start_date: str | None,
    end_date: str | None,
) -> list[DisclosureStagingRow]:
    # ponytail: cninfo manifest has row_count only; synthetic announcement metadata for rehearsal
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
    fr = (cninfo or {}).get("fetch_result") or {}
    source_fetch_id = str(fr.get("run_id") or bundle.source_fetch_ids[0] if bundle.source_fetch_ids else "")
    content_hash = str(fr.get("content_hash") or (bundle.content_hashes[0] if bundle.content_hashes else ""))
    symbols = bundle.symbols_or_series or ("cninfo",)
    win_start = start_date or bundle.window_start
    if win_start == "unknown":
        win_start = "2024-01-01"
    base = date.fromisoformat(win_start)
    now = datetime.now(UTC)
    rows: list[DisclosureStagingRow] = []
    for i in range(row_count):
        inst = symbols[i % len(symbols)]
        pub_date = (base + timedelta(days=i)).isoformat()
        if not _in_date_window(pub_date, start_date, end_date):
            continue
        filing_id = f"cninfo-{inst}-{i}"
        announcement_id = filing_id  # normalizer: filing_id → announcement_id
        publish_ts = datetime.combine(date.fromisoformat(pub_date), time(0, 0), tzinfo=UTC)
        rows.append(
            DisclosureStagingRow(
                announcement_id=announcement_id,
                instrument_id=inst,
                title=f"公告-{i}",
                publish_timestamp=publish_ts,
                announcement_url=None,
                announcement_type=None,
                data_domain=bundle.domain,
                source_used=bundle.source_id,
                pdf_file_id=None,
                extracted_text_file_id=None,
                content_status="metadata_only",
                batch_id=batch_id,
                source_fetch_id=source_fetch_id,
                content_hash=content_hash,
                schema_hash=bundle.schema_hashes[0] if bundle.schema_hashes else None,
                quality_flags="STAGED_FIXTURE",
                created_at=now,
            )
        )
    return rows


def _macro_observation_rows_from_bundle(
    bundle: RehearsalDataBundle,
    *,
    batch_id: str,
    max_rows: int,
    start_date: str | None,
    end_date: str | None,
) -> list[dict[str, object]]:
    payload = read_fred_evidence_bundle(bundle.evidence_dir)
    series_id = str(payload.get("series_id") or bundle.symbols_or_series[0])
    content_hash = str(payload.get("content_hash") or (bundle.content_hashes[0] if bundle.content_hashes else ""))
    schema_hash = str(payload.get("schema_hash") or (bundle.schema_hashes[0] if bundle.schema_hashes else ""))
    fetch_time_raw = payload.get("retrieved_at") or payload.get("as_of_timestamp")
    if isinstance(fetch_time_raw, str):
        fetch_time = datetime.fromisoformat(fetch_time_raw.replace("Z", "+00:00"))
        if fetch_time.tzinfo is None:
            fetch_time = fetch_time.replace(tzinfo=UTC)
    else:
        fetch_time = datetime.now(UTC)
    rows: list[dict[str, object]] = []
    for obs in payload.get("observations") or []:
        if len(rows) >= max_rows:
            break
        obs_date = str(obs.get("observation_date") or obs.get("date") or "")
        if not obs_date or not _in_date_window(obs_date, start_date, end_date):
            continue
        indicator_id = str(obs.get("series_id") or series_id)
        if indicator_id not in bundle.symbols_or_series and series_id in bundle.symbols_or_series:
            indicator_id = series_id
        if indicator_id not in bundle.symbols_or_series:
            continue
        as_of = date.fromisoformat(obs_date)
        as_of_dt = datetime.combine(as_of, time(16, 0), tzinfo=UTC)
        publish_dt = datetime.combine(as_of, time(0, 0), tzinfo=UTC)
        obs_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{indicator_id}|{obs_date}|{content_hash}"))
        rows.append(
            {
                "observation_id": obs_id,
                "indicator_id": indicator_id,
                "as_of_timestamp": as_of_dt,
                "publish_timestamp": publish_dt,
                "fetch_time": fetch_time,
                "raw_value": float(obs.get("value") or 0.0),
                "raw_unit": "index",
                "frequency": "daily",
                "source_used": bundle.source_id,
                "source_channel_id": bundle.source_id,
                "data_lag_days": 0.0,
                "stale_reason": None,
                "quality_flags": "STAGED_FIXTURE",
                "content_hash": content_hash,
                "schema_hash": schema_hash,
                "source_switched": False,
                "created_at": datetime.now(UTC),
            }
        )
    return rows


_STAGING_ROW_BUILDERS = {
    "baostock": _baostock_staging_rows,
    "akshare": _baostock_staging_rows,
    "yahoo_finance": _baostock_staging_rows,
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
    """DELETE stg_foundation_smoke and INSERT OHLCV bar rows from bundle evidence."""
    rows = staging_rows_from_bundle(bundle, **kwargs)
    con.execute("DELETE FROM stg_foundation_smoke")
    col_list = ", ".join(_BAR_STAGING_COLUMNS)
    placeholders = ", ".join("?" for _ in _BAR_STAGING_COLUMNS)
    for row in rows:
        con.execute(
            f"INSERT INTO stg_foundation_smoke ({col_list}) VALUES ({placeholders})",
            row.to_bar_staging_values(),
        )
    return len(rows)


def populate_disclosure_from_bundle(con, bundle: RehearsalDataBundle, **kwargs: Any) -> int:
    """DELETE stg_disclosure_smoke and INSERT cninfo announcement metadata rows."""
    cap = kwargs.get("max_rows", bundle.staged_row_count)
    rows = _disclosure_rows_from_bundle(
        bundle,
        batch_id=str(kwargs.get("batch_id") or ""),
        max_rows=int(cap),
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
    )
    if not rows and bundle.staged_row_count > 0:
        raise RehearsalLoaderError(
            f"evidence produced zero disclosure rows for {bundle.source_id} within window/cap"
        )
    con.execute("DELETE FROM stg_disclosure_smoke")
    col_list = ", ".join(_DISCLOSURE_STAGING_COLUMNS)
    placeholders = ", ".join("?" for _ in _DISCLOSURE_STAGING_COLUMNS)
    for row in rows:
        _validate_disclosure_staging_row(con, row)
        con.execute(
            f"INSERT INTO stg_disclosure_smoke ({col_list}) VALUES ({placeholders})",
            row.to_staging_values(),
        )
    return len(rows)


def populate_macro_from_bundle(con, bundle: RehearsalDataBundle, **kwargs: Any) -> int:
    """DELETE stg_axis_observation_smoke and INSERT fred → axis_observation rows."""
    cap = kwargs.get("max_rows", bundle.staged_row_count)
    rows = _macro_observation_rows_from_bundle(
        bundle,
        batch_id=str(kwargs.get("batch_id") or ""),
        max_rows=int(cap),
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
    )
    if not rows and bundle.staged_row_count > 0:
        raise RehearsalLoaderError(
            f"evidence produced zero macro rows for {bundle.source_id} within window/cap"
        )
    con.execute("DELETE FROM stg_axis_observation_smoke")
    col_list = ", ".join(AXIS_OBSERVATION_DDL_COLUMNS)
    placeholders = ", ".join("?" for _ in AXIS_OBSERVATION_DDL_COLUMNS)
    for row in rows:
        con.execute(
            f"INSERT INTO stg_axis_observation_smoke ({col_list}) VALUES ({placeholders})",
            [row[col] for col in AXIS_OBSERVATION_DDL_COLUMNS],
        )
    return len(rows)


def populate_staging_for_target(
    con,
    bundle: RehearsalDataBundle,
    staging_table: str,
    **kwargs: Any,
) -> int:
    """Route bundle → staging table (bar / disclosure / macro SSOT)."""
    # ponytail: per-row INSERT; upgrade: executemany / INSERT SELECT (A6-NB-2)
    if staging_table == "stg_foundation_smoke":
        return populate_staging_from_bundle(con, bundle, **kwargs)
    if staging_table == "stg_disclosure_smoke":
        return populate_disclosure_from_bundle(con, bundle, **kwargs)
    if staging_table == "stg_axis_observation_smoke":
        return populate_macro_from_bundle(con, bundle, **kwargs)
    raise RehearsalLoaderError(f"unsupported staging table: {staging_table!r}")


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
    raw = bars_path.read_bytes()
    if len(raw) > _MAX_BARS_JSON_BYTES:
        raise RehearsalLoaderError(
            f"bars.json exceeds {_MAX_BARS_JSON_BYTES} bytes (got {len(raw)})"
        )
    bars = json.loads(raw.decode("utf-8"))
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
