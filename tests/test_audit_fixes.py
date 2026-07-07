"""多维度审计修复回归：写入事务、API 限额、资源守护与连接调优。"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest
from backend.app.core.api_limits import clamp_agent_rows, clamp_page_size, load_api_limits
from backend.app.core.resource_guard import ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator


def _cm(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "audit.duckdb"
    cm = ConnectionManager(db, profile="eco")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _market_bar_quality(
    con,
    *,
    run_id: str,
    job_id: str,
    staging_table: str,
):
    return DataQualityValidator().validate_table(
        con,
        DataQualityRequest(
            run_id=run_id,
            job_id=job_id,
            data_domain="market_bar_1d",
            source_id="qmt_xtdata",
            staging_table=staging_table,
            primary_keys=("instrument_id", "trade_date"),
            required_fields=("close", "source_used"),
            rule_set_id="p0_round_1",
        ),
        expected_columns=(
            "instrument_id",
            "trade_date",
            "close",
            "source_used",
            "batch_id",
            "source_id",
        ),
        timestamp_fields=("trade_date",),
    )


def test_writeManager_defaultTransaction_withDbValidationGate_succeeds(tmp_path: Path) -> None:
    """覆盖范围：WriteManager 在外部事务中写入 + DbValidationGate
    测试对象：WriteManager.write(own_transaction=False)
    目的/目标：审计修复后，共享数据库连接的事务内写入应成功并留下审计记录
    验证点：status=SUCCESS；clean 1 行；write_audit_log 含 primary/market_bar_1d/system
    失败含义：外部事务写入路径断裂，编排层无法与校验同事务提交
    """
    cm = _cm(tmp_path)
    with cm.writer() as con:
        con.execute(
            """
            CREATE TABLE stg_audit AS
            SELECT 'AAPL'::VARCHAR AS instrument_id, '2026-06-15'::VARCHAR AS trade_date,
                   100.0::DOUBLE AS close, 'qmt'::VARCHAR AS source_used,
                   'b1'::VARCHAR AS batch_id, 'qmt'::VARCHAR AS source_id
            """
        )
        con.execute(
            """
            CREATE TABLE clean_audit (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        quality = _market_bar_quality(
            con, run_id="run-audit", job_id="job-audit", staging_table="stg_audit"
        )
        result = WriteManager(cm, DbValidationGate(cm)).write(
            WriteRequest(
                run_id="run-audit",
                job_id="job-audit",
                target_table="clean_audit",
                staging_table="stg_audit",
                write_mode="append_only",
                primary_keys=("instrument_id", "trade_date"),
                validation_report_id=quality.validation_report_id,
                source_used="qmt_xtdata",
                data_domain="market_bar_1d",
            ),
            con=con,
            own_transaction=False,
        )
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_audit").fetchone()[0]
        audit = con.execute(
            "SELECT source_role, data_domain, requested_by FROM write_audit_log"
        ).fetchone()

    assert result.status == "SUCCESS"
    assert clean_rows == 1
    assert audit == ("primary", "market_bar_1d", "system")


def test_writeManager_ownTransactionDefault_withDbValidationGate_succeeds(tmp_path: Path) -> None:
    """覆盖范围：WriteManager 默认自管事务写入
    测试对象：WriteManager.write() 不传 con/own_transaction
    目的/目标：写入管理器自行开启事务时，在校验门控下也应能成功落库
    验证点：status=SUCCESS；reader 侧 clean 表 1 行
    失败含义：默认事务模式写入失败，命令行与编排独立调用无法写入正式表
    """
    cm = _cm(tmp_path)
    with cm.writer() as con:
        con.execute(
            """
            CREATE TABLE stg_audit_default AS
            SELECT 'MSFT'::VARCHAR AS instrument_id, '2026-06-16'::VARCHAR AS trade_date,
                   200.0::DOUBLE AS close, 'qmt'::VARCHAR AS source_used,
                   'b2'::VARCHAR AS batch_id, 'qmt'::VARCHAR AS source_id
            """
        )
        con.execute(
            """
            CREATE TABLE clean_audit_default (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        quality = _market_bar_quality(
            con,
            run_id="run-audit-default",
            job_id="job-audit-default",
            staging_table="stg_audit_default",
        )
        report_id = quality.validation_report_id

    result = WriteManager(cm, DbValidationGate(cm)).write(
        WriteRequest(
            run_id="run-audit-default",
            job_id="job-audit-default",
            target_table="clean_audit_default",
            staging_table="stg_audit_default",
            write_mode="append_only",
            primary_keys=("instrument_id", "trade_date"),
            validation_report_id=report_id,
            source_used="qmt_xtdata",
            data_domain="market_bar_1d",
        )
    )
    with cm.reader() as con:
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_audit_default").fetchone()[0]
    assert result.status == "SUCCESS"
    assert clean_rows == 1


def test_syncJob_invalidStatus_rejectedByDbCheck(tmp_path: Path) -> None:
    """覆盖范围：data_sync_job.status 数据库 CHECK 约束
    测试对象：DuckDB INSERT 非法 status
    目的/目标：同步 job 状态机须在 DB 层拒绝未知枚举值
    验证点：插入 BROKEN 抛出 duckdb.ConstraintException
    失败含义：脏状态可入库，job 状态追踪与编排语义不一致
    """
    cm = _cm(tmp_path)
    with cm.writer() as con, pytest.raises(duckdb.ConstraintException, match="CHECK constraint failed"):
        con.execute("INSERT INTO data_sync_job (job_id, status) VALUES ('bad-job', 'BROKEN')")


def test_apiLimits_enforcesMaxPageSize() -> None:
    """覆盖范围：load_api_limits 与 clamp_* 辅助函数
    测试对象：clamp_page_size、clamp_agent_rows
    目的/目标：单次查询返回的行数不得超过安全合约上限
    验证点：max_page_size=1000；超限时截断且 truncated=True
    失败含义：接口可能一次返回过多数据，拖垮服务或占满内存
    """
    limits = load_api_limits()
    assert limits["max_page_size"] == 1000
    assert clamp_page_size(999) == 999
    assert clamp_page_size(0) == limits["default_page_size"]
    rows, truncated = clamp_agent_rows(999)
    assert rows == 999
    assert truncated is False
    rows, truncated = clamp_agent_rows(2000)
    assert rows == 1000
    assert truncated is True


def test_resourceGuard_reusesSnapshotWithinTtl(tmp_path: Path) -> None:
    """覆盖范围：ResourceGuard.snapshot TTL 缓存
    测试对象：ResourceGuard.snapshot / force_refresh
    目的/目标：短时间内重复读取资源快照应复用缓存，强制刷新才重新计算
    验证点：第二次 is 第一次；force_refresh 后对象不同；_compute_snapshot 仅多调 1 次
    失败含义：每次 check 都全量扫描磁盘，资源探针性能退化
    """
    guard = ResourceGuard()
    first = guard.snapshot(force_refresh=True)
    with patch.object(guard, "_compute_snapshot", wraps=guard._compute_snapshot) as compute:
        second = guard.snapshot()
        third = guard.snapshot(force_refresh=True)
    assert second is first
    assert third is not first
    assert compute.call_count == 1


def test_connection_lowMemoryForcesEcoThreads(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：ConnectionManager 低可用内存时的 DuckDB 线程/内存限制
    测试对象：ConnectionManager eco profile 连接参数
    目的/目标：系统可用内存不足时须降为单线程并收紧 memory_limit
    验证点：threads=1；memory_limit 含 732/768/767 之一
    失败含义：低内存环境仍多线程大缓冲，进程可能被系统强制终止
    """
    db = tmp_path / "lowmem.duckdb"
    with duckdb.connect(str(db)) as con:
        apply_migrations(con)

    class _Mem:
        total = 6 * 1024 * 1024 * 1024
        available = 2 * 1024 * 1024 * 1024

    monkeypatch.setattr("backend.app.db.connection.psutil.virtual_memory", lambda: _Mem())
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 1536, "max_threads": 2, "duckdb_temp_max_gb": 2}},
    )
    with cm.reader() as r:
        threads = int(r.execute("SELECT current_setting('threads')").fetchone()[0])
        mem = r.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    assert threads == 1
    assert "732" in mem or "768" in mem or "767" in mem


@pytest.mark.perf
def test_resourceGuard_largeCacheDir_completesWithinReasonableTime(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：大 cache 目录下 ResourceGuard.check 性能
    测试对象：ResourceGuard.check
    目的/目标：数百小文件 cache 扫描须在合理时间内完成且返回合法决策
    验证点：decision 在 OK/WARN/PAUSE/HARD_STOP；elapsed < 5s
    失败含义：cache 扫描过慢阻塞同步编排，或决策枚举异常
    """
    cache = tmp_path / "data" / "cache" / "many_files"
    cache.mkdir(parents=True)
    for i in range(500):
        (cache / f"f{i}.bin").write_bytes(b"x" * 64)

    import backend.app.core.resource_guard as rg_mod

    monkeypatch.setattr(rg_mod, "DATA_ROOT", tmp_path / "data")
    guard = ResourceGuard()
    start = time.perf_counter()
    decision, _ = guard.check()
    elapsed = time.perf_counter() - start

    assert decision.value in {"OK", "WARN", "PAUSE", "HARD_STOP"}
    assert elapsed < 5.0
