"""Data adapter contract and fetch_log tests (Batch A)."""

from __future__ import annotations

import json

import duckdb
import pytest
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.fetch_log import FetchLogWriter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import DomainNotAllowedError, SourceDisabledError
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from pydantic import ValidationError

CONTRACT_STATUSES = [
    "SUCCESS",
    "EMPTY_RESPONSE",
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "FAILED",
]
ERROR_TYPE_BY_STATUS = {
    "SUCCESS": None,
    "EMPTY_RESPONSE": "empty",
    "AUTH_FAILED": "auth",
    "RATE_LIMITED": "rate_limit",
    "NETWORK_ERROR": "network",
    "SCHEMA_DRIFT": "schema",
    "FAILED": "failed",
}
# NOT_PUBLISHED_YET: Batch B+ only (data_sources.md §5.7) — intentionally excluded


@pytest.mark.parametrize("status", CONTRACT_STATUSES)
def test_fetchResult_allContractStatuses_areAccepted(status):
    r = FetchResult(
        run_id="r",
        source_id="s",
        data_domain="d",
        status=status,
        fetch_time="2026-06-17T10:00:00Z",
    )
    assert r.status == status


def test_fetchRequest_missingRunId_raisesValidationError():
    with pytest.raises(ValidationError):
        FetchRequest(source_id="s", data_domain="d")


def test_fetchResult_stagingTableField_roundTrips():
    r = FetchResult(
        run_id="r",
        source_id="s",
        data_domain="d",
        status="SUCCESS",
        fetch_time="2026-06-17T10:00:00Z",
        staging_table="stg_x",
    )
    assert r.staging_table == "stg_x"


def test_write_successResult_insertsFetchLogRow(
    tmp_path, migrated_con, success_result, request_factory,
):
    con = migrated_con(tmp_path)
    req = request_factory("baostock")
    fetch_id = FetchLogWriter().write(con, success_result(), req=req, job_id="job-1")
    row = con.execute(
        "SELECT status, row_count, job_id, raw_file_paths, error_type, request_params_hash "
        "FROM fetch_log WHERE fetch_id=?",
        [fetch_id],
    ).fetchone()
    assert row[0] == "SUCCESS" and row[1] == 42 and row[2] == "job-1"
    assert json.loads(row[3]) == ["/data/raw/baostock/run-1.parquet"]
    assert row[4] is None
    assert row[5]


def test_write_failedResult_stillPersists(tmp_path, migrated_con, network_error_result):
    con = migrated_con(tmp_path)
    fetch_id = FetchLogWriter().write(con, network_error_result())
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()
    assert row[0] == "NETWORK_ERROR" and row[1] == "network"


@pytest.mark.parametrize("status", CONTRACT_STATUSES)
def test_write_allContractStatuses_mapsErrorType(tmp_path, migrated_con, status):
    con = migrated_con(tmp_path)
    result = FetchResult(
        run_id="run-1",
        source_id="baostock",
        data_domain="market_bar_1d",
        status=status,
        row_count=0 if status != "SUCCESS" else 1,
        fetch_time="2026-06-17T10:00:00Z",
        error_message="err" if status != "SUCCESS" else None,
    )
    fetch_id = FetchLogWriter().write(con, result)
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()
    assert row[0] == status
    assert row[1] == ERROR_TYPE_BY_STATUS[status]


def test_write_closedConnection_propagates(tmp_path, migrated_con, success_result):
    con = migrated_con(tmp_path)
    con.close()
    with pytest.raises(duckdb.Error):
        FetchLogWriter().write(con, success_result())


def test_write_underWriterLock_insertsFetchLogRow(tmp_path, success_result, request_factory):
    db = tmp_path / "writer.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    req = request_factory("baostock")
    with cm.writer() as con:
        fetch_id = FetchLogWriter().write(con, success_result(), req=req)
    with cm.writer() as con:
        row = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE fetch_id=?", [fetch_id]
        ).fetchone()[0]
    assert row == 1


class FakeAdapter(BaseDataAdapter):
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})

    def _fetch_impl(self, req):
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_test",
            raw_file_paths=["/tmp/x"],
        )


class ExplodingAdapter(BaseDataAdapter):
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})

    def _fetch_impl(self, req):
        raise RuntimeError("boom")


class WrongSourceAdapter(BaseDataAdapter):
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})

    def _fetch_impl(self, req):
        return FetchResult(
            run_id=req.run_id,
            source_id="other_source",
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_test",
            raw_file_paths=["/tmp/x"],
        )


class NarrowDomainAdapter(BaseDataAdapter):
    source_id = "baostock"
    supported_domains = frozenset({"fundamental"})

    def _fetch_impl(self, req):
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_test",
            raw_file_paths=["/tmp/x"],
        )


class BroadDomainAdapter(BaseDataAdapter):
    """Supports fundamental so registry-level rejection is testable (QA-A8-1)."""

    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d", "fundamental"})

    def _fetch_impl(self, req):
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_test",
            raw_file_paths=["/tmp/x"],
        )


def test_fetch_disabledSource_raisesBeforeImpl_andWritesNoFetchLog(
    tmp_path, migrated_con, disabled_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(disabled_registry)
    req = request_factory("baostock")
    with pytest.raises(SourceDisabledError):
        adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0


def test_fetch_unsupportedDomainOnAdapter_raises_andWritesNoFetchLog(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = NarrowDomainAdapter(loaded_registry)
    req = request_factory("baostock", domain="market_bar_1d")
    with pytest.raises(DomainNotAllowedError):
        adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0


def test_fetch_registryDomainNotAllowed_raisesBeforeImpl_andWritesNoFetchLog(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = BroadDomainAdapter(loaded_registry)
    req = request_factory("baostock", domain="fundamental")
    with pytest.raises(DomainNotAllowedError):
        adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0


def test_fetch_successResult_writesExactlyOneFetchLogRow(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 1


def test_fetch_calledTwice_writesTwoRows(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con)
    adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 2


def test_fetch_alwaysWritesFetchLog_evenOnEmptyResponse(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    class EmptyAdapter(BaseDataAdapter):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

        def _fetch_impl(self, req):
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="EMPTY_RESPONSE",
                row_count=0,
                fetch_time="2026-06-17T10:00:00Z",
                staging_table=None,
                raw_file_paths=[],
            )

    con = migrated_con(tmp_path)
    adapter = EmptyAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 1


def test_fetch_emptyResponse_hasNoStagingEvidence(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    class EmptyAdapter(BaseDataAdapter):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

        def _fetch_impl(self, req):
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="EMPTY_RESPONSE",
                row_count=0,
                fetch_time="2026-06-17T10:00:00Z",
                staging_table=None,
                raw_file_paths=[],
            )

    con = migrated_con(tmp_path)
    adapter = EmptyAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con)
    row = con.execute(
        "SELECT raw_file_paths FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()[0]
    assert json.loads(row) == []


def test_fetch_implRaises_stillWritesFetchLogAndReturnsFailed(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = ExplodingAdapter(loaded_registry)
    req = request_factory("baostock")
    result = adapter.fetch(req, con=con)
    assert result.status == "FAILED"
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 1


def test_fetch_implDoesNotSwitchSourceId(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = WrongSourceAdapter(loaded_registry)
    req = request_factory("baostock")
    result = adapter.fetch(req, con=con)
    assert result.source_id == "baostock"
    row = con.execute(
        "SELECT source_id FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()[0]
    assert row == "baostock"


def test_fetch_success_carriesEvidenceFields(
    tmp_path, migrated_con, loaded_registry, request_factory,
):
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("baostock")
    result = adapter.fetch(req, con=con)
    assert result.staging_table
    assert result.raw_file_paths
