"""Shared sync test adapters (orchestrator / full_load / backfill paths)."""

from __future__ import annotations

from datetime import date

BACKFILL_3SHARD_START = date(2026, 1, 1)
BACKFILL_3SHARD_END = date(2026, 3, 5)
BACKFILL_1SHARD_END = date(2026, 1, 15)
BACKFILL_2SHARD_END = date(2026, 2, 15)

FULL_LOAD_3SHARD_START = date(2026, 1, 1)
FULL_LOAD_1SHARD_END = date(2026, 1, 15)
FULL_LOAD_2SHARD_END = date(2026, 2, 15)


class BackfillCountAdapter:
    """Minimal adapter for backfill shard tests with validate+write path."""

    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})
    STG = "stg_backfill"
    CLEAN = "stg_backfill_clean"

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.STG} (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {self.CLEAN} AS SELECT * FROM {self.STG} WHERE 1=0"
        )
        con.execute(f"DELETE FROM {self.STG}")
        con.execute(
            f"INSERT INTO {self.STG} VALUES (?, ?, ?, ?, ?, ?)",
            ["AAPL", "2026-06-15", 100.0, "baostock", "bf1", "baostock"],
        )
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table=self.STG,
            raw_file_paths=["/tmp/bf.parquet"],
            content_hash="abc",
            schema_hash="def",
        )


class BackfillFailOnSecondAdapter(BackfillCountAdapter):
    def __init__(self) -> None:
        self._calls = 0

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

        self._calls += 1
        if self._calls >= 2:
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="NETWORK_ERROR",
                row_count=0,
                fetch_time="2026-06-17T10:00:00Z",
                error_message="shard 2 failed",
            )
        return super().fetch(req, con=con, job_id=job_id)


class FullLoadCountAdapter:
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})
    STG = "stg_full_load"
    CLEAN = "stg_full_load_clean"

    def __init__(self) -> None:
        self.fetched_shard_ids: list[str] = []

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

        shard_id = f"{req.start_time}:{req.end_time}"
        self.fetched_shard_ids.append(shard_id)
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.STG} (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {self.CLEAN} AS SELECT * FROM {self.STG} WHERE 1=0"
        )
        con.execute(f"DELETE FROM {self.STG}")
        con.execute(
            f"INSERT INTO {self.STG} VALUES (?, ?, ?, ?, ?, ?)",
            ["AAPL", "2026-06-15", 100.0, "baostock", "fl1", "baostock"],
        )
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table=self.STG,
            raw_file_paths=["/tmp/fl.parquet"],
            content_hash="abc",
            schema_hash="def",
        )


class FullLoadFailOnSecondAdapter(FullLoadCountAdapter):
    def __init__(self) -> None:
        super().__init__()
        self._calls = 0

    def fetch(self, req, *, con, job_id=None):
        self._calls += 1
        if self._calls >= 2:
            from backend.app.datasources.fetch_result import FetchResult

            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="FAILED",
                row_count=0,
                fetch_time="2026-06-17T10:00:00Z",
                error_message="shard fail",
            )
        return super().fetch(req, con=con, job_id=job_id)
