"""Test helpers for R3-DCP-03 post-write inspect (incremental → bundle → health)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.storage.path_compat import is_file
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark

from tests.incremental_baostock_support import (
    FIXTURE_DATE,
    SYMBOL,
    bootstrap_db,
    build_service,
    incremental_spec,
    seed_watermark_row,
)

SEED_DATE = "2024-06-24"


def run_two_incremental(
    tmp_path: Path,
    monkeypatch,
) -> tuple[ConnectionManager, Path, DataSyncOrchestrator]:
    """Bootstrap DB, seed watermark, run 2× incremental sync (baostock replay)."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, SEED_DATE)
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
    window = compute_incremental_window(wm, end=FIXTURE_DATE)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    service, orch = build_service(cm, raw_root)
    kwargs = dict(
        datasource_service=service,
        clean_table="security_bar_1d",
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
    )
    r1 = orch.run_incremental(incremental_spec(window, job_id="job-pwi-1"), **kwargs)
    r2 = orch.run_incremental(incremental_spec(window, job_id="job-pwi-2"), **kwargs)
    if r1.status != "COMPLETED" or r2.status != "COMPLETED":
        raise RuntimeError(f"incremental failed: {r1.status}, {r2.status}")
    return cm, raw_root, orch


def _parse_raw_file_paths(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    text = str(raw_value).strip()
    if text.startswith("["):
        parsed = json.loads(text)
        return [str(p) for p in parsed] if isinstance(parsed, list) else []
    return [text]


def _rows_from_cn_market_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bar in payload.get("bars") or []:
        if not isinstance(bar, dict):
            continue
        symbol = str(bar.get("instrument_id") or bar.get("symbol") or SYMBOL)
        rows.append(
            {
                "symbol": symbol,
                "instrument_id": symbol,
                "trade_date": str(bar.get("trade_date") or bar.get("date") or ""),
                "open": bar.get("open"),
                "high": bar.get("high"),
                "low": bar.get("low"),
                "close": bar.get("close"),
                "volume": bar.get("volume"),
            }
        )
    for row in payload.get("rows") or []:
        if isinstance(row, dict):
            symbol = str(row.get("symbol") or row.get("instrument_id") or SYMBOL)
            rows.append({**row, "symbol": symbol, "instrument_id": symbol})
    return rows


def _row_key(row: dict[str, Any]) -> tuple[str, str]:
    instrument_id = str(row.get("instrument_id") or row.get("symbol") or SYMBOL)
    trade_date = str(row.get("trade_date") or row.get("date") or "")
    return instrument_id, trade_date


def _rows_from_clean_table(con, instrument_ids: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instrument_id in instrument_ids:
        db_rows = con.execute(
            """
            SELECT instrument_id, trade_date, open, high, low, close, volume
            FROM security_bar_1d
            WHERE instrument_id = ?
              AND open IS NOT NULL AND high IS NOT NULL AND low IS NOT NULL
              AND close IS NOT NULL AND volume IS NOT NULL
            """,
            [instrument_id],
        ).fetchall()
        for instrument_id, trade_date, open_, high, low, close, volume in db_rows:
            rows.append(
                {
                    "symbol": str(instrument_id),
                    "instrument_id": str(instrument_id),
                    "trade_date": str(trade_date),
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": float(volume),
                }
            )
    return rows


def _merge_bar_rows(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for group in groups:
        for row in group:
            merged[_row_key(row)] = row
    return list(merged.values())


def build_evidence_bundle_from_fetch_log(
    cm: ConnectionManager,
    bundle_dir: Path,
    *,
    data_domain: str = "cn_equity_daily_bar",
    source_id: str = "baostock",
) -> Path:
    """Assemble minimal evidence bundle from latest fetch_log.raw_file_paths."""
    with cm.reader() as con:
        row = con.execute(
            """
            SELECT raw_file_paths, fetch_id, content_hash, fetch_time
            FROM fetch_log
            WHERE status = 'SUCCESS' AND raw_file_paths IS NOT NULL
            ORDER BY fetch_time DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        raise ValueError("fetch_log has no SUCCESS row with raw_file_paths")

    raw_paths = _parse_raw_file_paths(row[0])
    if not raw_paths:
        raise ValueError("fetch_log raw_file_paths empty")

    bundle_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []

    for idx, raw_path in enumerate(raw_paths):
        src = Path(raw_path)
        if not is_file(src):
            raise FileNotFoundError(f"raw file missing: {raw_path}")
        rel_name = f"raw_{idx}.json"
        from backend.app.storage.path_compat import read_bytes, write_bytes

        write_bytes(bundle_dir / rel_name, read_bytes(src))
        payload = json.loads(read_bytes(src).decode("utf-8"))
        all_rows.extend(_rows_from_cn_market_payload(payload))

    instrument_ids = {key[0] for key in (_row_key(row) for row in all_rows)} or {SYMBOL}
    with cm.reader() as con:
        clean_rows = _rows_from_clean_table(con, instrument_ids)
    all_rows = _merge_bar_rows(clean_rows, all_rows)

    (bundle_dir / "bars.json").write_text(
        json.dumps({"rows": all_rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "raw_evidence_manifest.json").write_text(
        json.dumps(
            {
                "data_domain": data_domain,
                "source_id": source_id,
                "generated_at": str(row[3] or ""),
                "manifest_entries": [
                    {
                        "source_used": source_id,
                        "source_fetch_id": str(row[1] or "fetch-0"),
                        "content_hash": str(row[2] or "hash-0"),
                        "as_of_timestamp": str(row[3] or ""),
                        "relative_paths": ["bars.json"],
                    }
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return bundle_dir.resolve()
