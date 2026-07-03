"""Mootdx vendor adapter (R3-DCP-01).

L2: fetch_port gold path routes through adapter.fetch; staging mapping required
so run_incremental receives staging_table (mirrors baostock bar staging).
"""

from __future__ import annotations

import json

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
from backend.app.datasources.fetch_result import FetchRequest, FetchResult

_MOOTDX_STAGING_TABLE = "stg_foundation_smoke"


class MootdxAdapter(SkeletonAdapterBase):
    source_id = "mootdx"
    supported_domains = frozenset({"cn_equity_daily_bar", "cn_equity_basic_financial"})

    def fetch(
        self,
        req: FetchRequest,
        *,
        con,
        job_id: str | None = None,
        record_fetch_log: bool = True,
    ) -> FetchResult:
        result = super().fetch(req, con=con, job_id=job_id, record_fetch_log=record_fetch_log)
        if result.status != "SUCCESS":
            return result
        payload = self._fetch_port.fetch_payload(req)
        try:
            parsed = json.loads(payload.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return result
        if not isinstance(parsed, dict) or "bars" not in parsed:
            return result
        bars = parsed.get("bars") or []
        if not bars:
            return result.model_copy(update={"row_count": 0, "status": "EMPTY_RESPONSE"})
        con.execute(f"DELETE FROM {_MOOTDX_STAGING_TABLE}")
        for bar in bars:
            close = float(bar.get("close") or 0.0)
            con.execute(
                f"""
                INSERT INTO {_MOOTDX_STAGING_TABLE} (
                    instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
                    adjustment_type, source_used, batch_id, quality_flags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, 'none', ?, 'v1', NULL, CURRENT_TIMESTAMP)
                """,
                [
                    str(bar.get("instrument_id") or req.instrument_id or ""),
                    str(bar.get("trade_date") or ""),
                    float(bar.get("open") or close),
                    float(bar.get("high") or close),
                    float(bar.get("low") or close),
                    close,
                    float(bar.get("volume") or 0.0),
                    str(bar.get("source_used") or "mootdx"),
                ],
            )
        return result.model_copy(
            update={"staging_table": _MOOTDX_STAGING_TABLE, "row_count": len(bars)}
        )
