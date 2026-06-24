"""写入管理器测试（Round 1 任务 008）。

覆盖范围：校验门闸、append/upsert 写入、失败回滚与审计留痕。
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest
import backend.app.db.write_manager as wm_mod
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import (
    StubValidationGate,
    ValidationGateError,
    ValidationRejected,
)
from backend.app.db.write_manager import WriteManager, WriteRequest
from tests.db_helpers import create_test_write_manager


def _setup(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / "t.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
        con.execute(
            "INSERT INTO stg_foundation_smoke VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')"
        )
    return cm


def _empty_clean_table(w, table: str = "security_bar_smoke_clean") -> None:
    w.execute(
        f"CREATE TABLE {table} AS SELECT * FROM stg_foundation_smoke WHERE 1=0"
    )


def _patch_connect_calls(monkeypatch) -> list[bool]:
    original_connect = duckdb.connect
    connect_calls: list[bool] = []

    def _tracking_connect(path, *args, **kwargs):
        connect_calls.append(True)
        return original_connect(path, *args, **kwargs)

    monkeypatch.setattr(wm_mod.duckdb, "connect", _tracking_connect)
    return connect_calls


def _req(mode: str = "append_only", report: str = "stub-pass-1") -> WriteRequest:
    return WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="security_bar_smoke_clean",
        staging_table="stg_foundation_smoke",
        write_mode=mode,
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id=report,
        source_used="qmt",
        data_domain="cn_equity_daily_bar",
    )


def test_assertCanWrite_stubPass_allowsWhileStubFailRejects() -> None:
    """覆盖范围：测试用校验门闸对通过/拒绝报告的分流
    测试对象：StubValidationGate.assert_can_write
    目的/目标：校验通过的报告应放行写入，明确失败的报告应拒绝
    验证点：stub-pass-001 不抛错；stub-fail-001 抛 ValidationRejected
    失败含义：门闸分不清通过和拒绝，脏数据可能写进正式表
    """
    gate = StubValidationGate()
    gate.assert_can_write("stub-pass-001", "append_only")
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("stub-fail-001", "append_only")


def test_assertCanWrite_unknownId_raisesGateError() -> None:
    """覆盖范围：非测试前缀的 validation_report_id 须拒绝
    测试对象：StubValidationGate.assert_can_write
    目的/目标：真实校验报告 ID 在测试门闸下不能误放行
    验证点：real-123 抛 ValidationGateError
    失败含义：没验过的报告被当成可写，生产门禁形同虚设
    """
    with pytest.raises(ValidationGateError):
        StubValidationGate().assert_can_write("real-123", "append_only")


def test_writeManager_withoutGate_raisesValueError(tmp_path: Path) -> None:
    """覆盖范围：WriteManager 构造时 validation_gate 为必填
    测试对象：WriteManager.__init__
    目的/目标：不允许没有校验门闸就创建写入管理器，必须显式注入
    验证点：WriteManager(cm, None) 抛 ValueError 且含 requires an explicit ValidationGate
    失败含义：可以绕过校验门闸创建写入器，违反 fail-closed 设计
    """
    cm = _setup(tmp_path)
    with pytest.raises(ValueError, match="requires an explicit ValidationGate"):
        WriteManager(cm, None)


def test_writeManager_defaultConstructor_raisesTypeError(tmp_path: Path) -> None:
    """覆盖范围：WriteManager 不接受省略 gate 的默认构造
    测试对象：WriteManager.__init__ 参数签名
    目的/目标：类型层面阻止只传连接、不传门闸的旧式调用
    验证点：WriteManager(cm) 抛 TypeError
    失败含义：旧式无门闸构造仍可用，静态检查和运行时约束不一致
    """
    cm = _setup(tmp_path)
    with pytest.raises(TypeError):
        WriteManager(cm)  # type: ignore[call-arg]


def test_write_invalidIdentifier_raisesBeforeWrite(tmp_path: Path) -> None:
    """覆盖范围：目标表名含 SQL 注入字符时写入前拒绝
    测试对象：WriteManager.write 的标识符校验
    目的/目标：表名必须是合法 SQL 标识符，防止拼接注入破坏数据
    验证点：含 DROP 的 target_table 抛 ValueError match invalid SQL identifier
    失败含义：恶意表名能拼进 SQL，存在删表或破坏数据的风险
    """
    cm = _setup(tmp_path)
    bad = WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="file_registry; DROP TABLE write_audit_log; --",
        staging_table="stg_foundation_smoke",
        write_mode="append_only",
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id="stub-pass-1",
        source_used="qmt",
    )
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        create_test_write_manager(cm).write(bad)


def test_write_appendOnlyStubPass_insertsAndAudits(tmp_path: Path) -> None:
    """覆盖范围：append_only 模式校验通过后成功写入与审计
    测试对象：WriteManager.write
    目的/目标：校验通过后 staging 行应插入 clean 表，并留下成功审计记录
    验证点：status=SUCCESS；rows_inserted=1；clean 表 1 行；audit 三元组一致
    失败含义：主写入 happy path 断了，同步流水线没法把数据落进正式表
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
    res = create_test_write_manager(cm).write(_req())
    assert res.status == "SUCCESS"
    assert res.rows_inserted == 1
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
        audit = r.execute(
            "SELECT status, rows_inserted, rows_in_staging FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
    assert audit == ("SUCCESS", 1, 1)


def test_write_stubFail_rollsBackAndAuditsFailed(tmp_path: Path) -> None:
    """覆盖范围：校验明确拒绝时回滚且不写 clean
    测试对象：WriteManager.write 对 ValidationRejected 的处理
    目的/目标：校验失败应回滚事务、正式表保持空、并记下失败审计
    验证点：status=FAILED；clean COUNT=0；write_audit_log 一条 FAILED
    失败含义：校验失败仍落盘或不留审计，数据质量门禁失效
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
    res = create_test_write_manager(cm).write(_req(report="stub-fail-1"))
    assert res.status == "FAILED"
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 0
        cnt = r.execute("SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'").fetchone()[0]
        assert cnt == 1


def test_write_gateError_rollsBackAndAuditsFailed(tmp_path: Path) -> None:
    """覆盖范围：未知 validation_report_id 导致门闸错误时的失败路径
    测试对象：WriteManager.write 对 ValidationGateError 的处理
    目的/目标：门闸异常须回滚、记 FAILED 审计并带 error_message
    验证点：status=FAILED；error_message 非空；clean 零行；validation_status=FAILED
    失败含义：门闸错误被吞或 clean 已写入，审计无法追溯拒绝原因
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
    res = create_test_write_manager(cm).write(_req(report="real-report-1"))
    assert res.status == "FAILED"
    assert res.error_message
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 0
        audit = r.execute(
            "SELECT validation_status FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()[0]
        assert audit == "FAILED"


def test_write_sqlError_rollsBackAndAuditsError(tmp_path: Path) -> None:
    """覆盖范围：目标表不存在等 SQL 执行错误
    测试对象：WriteManager.write 对 duckdb 执行失败的处理
    目的/目标：SQL 错误须记 validation_status=ERROR、status=FAILED
    验证点：status=FAILED；error_message 非空；audit=(ERROR, FAILED)
    失败含义：SQL 失败无审计或状态码混淆，运维无法区分校验与执行错误
    """
    cm = _setup(tmp_path)
    res = create_test_write_manager(cm).write(_req())
    assert res.status == "FAILED"
    assert res.error_message
    with cm.reader() as r:
        audit = r.execute(
            "SELECT validation_status, status FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
        assert audit == ("ERROR", "FAILED")


def test_write_emptyStaging_rejected(tmp_path: Path) -> None:
    """覆盖范围：staging 表零行时拒绝写入（ADV-A1-012/015）
    测试对象：WriteManager.write 的最小行数校验
    目的/目标：空 staging 不得进入 clean 写入，避免无意义或误导性 SUCCESS
    验证点：空 staging 抛 ValueError match minimum
    失败含义：空批次可写 clean，增量同步误报成功
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("DELETE FROM stg_foundation_smoke")
        _empty_clean_table(w)
    with pytest.raises(ValueError, match="minimum"):
        create_test_write_manager(cm).write(_req())


def test_write_unsupportedMode_raises(tmp_path: Path) -> None:
    """覆盖范围：未实现的 write_mode 须早拒
    测试对象：WriteManager.write 的模式分发
    目的/目标：replace_partition 等未支持模式不得静默失败或误写
    验证点：write_mode=replace_partition 抛 ValueError
    失败含义：不支持的模式被当作 append，分区替换语义 silently 错误
    """
    cm = _setup(tmp_path)
    with pytest.raises(ValueError):
        create_test_write_manager(cm).write(_req(mode="replace_partition"))


def test_write_upsertByPk_replacesExistingRow(tmp_path: Path) -> None:
    """覆盖范围：upsert_by_pk 更新已存在主键行
    测试对象：WriteManager.write write_mode=upsert_by_pk
    目的/目标：同 PK 行应 UPDATE 而非重复 INSERT
    验证点：status=SUCCESS；rows_updated=1、rows_inserted=0；close=200；clean 仍 1 行
    失败含义：upsert 变重复插入或计数错误，增量修正无法覆盖旧值
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("CREATE TABLE security_bar_smoke_clean AS SELECT * FROM stg_foundation_smoke")
        w.execute("UPDATE stg_foundation_smoke SET close=200.0")
    res = create_test_write_manager(cm).write(_req(mode="upsert_by_pk"))
    assert res.status == "SUCCESS"
    assert res.rows_updated == 1
    assert res.rows_inserted == 0
    with cm.reader() as r:
        close = r.execute(
            "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'"
        ).fetchone()[0]
        assert close == 200.0
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
        audit = r.execute(
            "SELECT rows_updated, rows_inserted FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
        assert audit == (1, 0)


def test_write_upsertByPk_pureNewRow_reportsZeroUpdated(tmp_path: Path) -> None:
    """覆盖范围：upsert_by_pk 仅插入新主键行
    测试对象：WriteManager.write upsert 插入分支
    目的/目标：staging PK 在 clean 不存在时应 INSERT 且 rows_updated=0
    验证点：rows_inserted=1；clean 总行数 3；audit=(0,1)
    失败含义：新行被误报为 update 或计数颠倒，监控指标失真
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
        w.execute(
            "INSERT INTO security_bar_smoke_clean VALUES ('MSFT','2026-06-14',100.0,'qmt','b0')"
        )
        w.execute(
            "INSERT INTO security_bar_smoke_clean VALUES ('GOOG','2026-06-13',200.0,'qmt','b0')"
        )
        w.execute("DELETE FROM stg_foundation_smoke")
        w.execute("INSERT INTO stg_foundation_smoke VALUES ('NVDA','2026-06-16',300.0,'qmt','b2')")
    res = create_test_write_manager(cm).write(_req(mode="upsert_by_pk"))
    assert res.status == "SUCCESS"
    assert res.rows_updated == 0
    assert res.rows_inserted == 1
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 3
        audit = r.execute(
            "SELECT rows_updated, rows_inserted FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
        assert audit == (0, 1)


def test_write_upsertByPk_emptyPrimaryKeys_raises(tmp_path: Path) -> None:
    """覆盖范围：upsert_by_pk 要求非空 primary_keys
    测试对象：WriteManager.write 对 upsert 前置校验
    目的/目标：无主键无法定义 upsert 语义，须早拒
    验证点：primary_keys=() 抛 ValueError match upsert_by_pk requires primary_keys
    失败含义：空 PK upsert 可能全表覆盖或行为未定义
    """
    cm = _setup(tmp_path)
    bad = WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="security_bar_smoke_clean",
        staging_table="stg_foundation_smoke",
        write_mode="upsert_by_pk",
        primary_keys=(),
        validation_report_id="stub-pass-1",
        source_used="qmt",
        data_domain="cn_equity_daily_bar",
    )
    with pytest.raises(ValueError, match="upsert_by_pk requires primary_keys"):
        create_test_write_manager(cm).write(bad)


def test_write_upsertByPk_duplicateStagingPk_raises(tmp_path: Path) -> None:
    """覆盖范围：staging 内主键重复时 upsert 前拒绝
    测试对象：WriteManager.write staging PK 唯一性校验
    目的/目标：同一批次 duplicate PK 不得进入 merge，避免不确定写入
    验证点：stg 两行同 PK 抛 ValueError match duplicate primary keys
    失败含义：重复 PK 静默取一行，clean 数据不可复现
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
        w.execute(
            """
            CREATE TABLE stg_upsert_dup AS
            SELECT * FROM stg_foundation_smoke WHERE 1=0
            """
        )
        w.execute("INSERT INTO stg_upsert_dup VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')")
        w.execute("INSERT INTO stg_upsert_dup VALUES ('AAPL','2026-06-15',196.0,'qmt','b2')")
    dup_req = WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="security_bar_smoke_clean",
        staging_table="stg_upsert_dup",
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id="stub-pass-1",
        source_used="qmt",
        data_domain="cn_equity_daily_bar",
    )
    with pytest.raises(ValueError, match="duplicate primary keys"):
        create_test_write_manager(cm).write(dup_req)


def test_write_stubFail_ownTransaction_doesNotOpenSecondAuditConnection(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：失败审计复用 writer 连接，不另开 duckdb.connect
    测试对象：WriteManager.write 审计连接策略
    目的/目标：自有事务模式下审计与写入共连接，避免双连接竞态
    验证点：stub-fail 后 status=FAILED；duckdb.connect 仅调用 1 次（建库）
    失败含义：失败路径多开连接，锁争用或审计与主事务不一致
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
    connect_calls = _patch_connect_calls(monkeypatch)
    connect_calls.clear()
    res = create_test_write_manager(cm).write(_req(report="stub-fail-1"))
    assert res.status == "FAILED"
    assert len(connect_calls) == 1


def test_write_upsertByPk_mixedNewAndExisting_reportsCorrectCounts(tmp_path: Path) -> None:
    """覆盖范围：upsert 批次同时含更新行与新增行
    测试对象：WriteManager.write upsert 混合场景计数
    目的/目标：rows_updated 与 rows_inserted 须分别统计正确
    验证点：updated=1、inserted=1；clean 2 行；AAPL close=200
    失败含义：混合 upsert 计数错误，作业报告与真实写入不符
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("CREATE TABLE security_bar_smoke_clean AS SELECT * FROM stg_foundation_smoke")
        w.execute("INSERT INTO stg_foundation_smoke VALUES ('MSFT','2026-06-15',120.0,'qmt','b2')")
        w.execute("UPDATE stg_foundation_smoke SET close=200.0 WHERE instrument_id='AAPL'")
    res = create_test_write_manager(cm).write(_req(mode="upsert_by_pk"))
    assert res.status == "SUCCESS"
    assert res.rows_updated == 1
    assert res.rows_inserted == 1
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 2
        aapl_close = r.execute(
            "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'"
        ).fetchone()[0]
        assert aapl_close == 200.0


def test_write_ownTransactionFalse_stubFail_sidecarSurvivesOuterRollback(tmp_path: Path) -> None:
    """覆盖范围：own_transaction=False 失败时 sidecar 审计 survives 外层 ROLLBACK（ADV-A1-005）
    测试对象：WriteManager.write audit_sidecar_root
    目的/目标：外层事务回滚后 FAILED 记录仍可在 ndjson sidecar 追溯
    验证点：sidecar 1 行 JSON status=FAILED；write_audit_log 表 0 行
    失败含义：外层回滚抹掉失败审计，运维无法追查拒写原因
    """
    cm = _setup(tmp_path)
    data_root = tmp_path / "data"
    data_root.mkdir()
    sidecar = data_root / "logs" / "failed_write_audit.ndjson"
    with cm.writer() as w:
        _empty_clean_table(w)
        w.execute("BEGIN")
        res = create_test_write_manager(cm).write(
            _req(report="stub-fail-1"),
            con=w,
            own_transaction=False,
            audit_sidecar_root=data_root,
        )
        assert res.status == "FAILED"
        w.execute("ROLLBACK")
    lines = [ln for ln in sidecar.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["status"] == "FAILED"
    assert entry["validation_report_id"] == "stub-fail-1"
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM write_audit_log").fetchone()[0] == 0


def test_write_ownTransactionFalse_stubFail_doesNotRollbackOuterTxn(tmp_path: Path) -> None:
    """覆盖范围：own_transaction=False 失败不触发外层事务回滚
    测试对象：WriteManager.write 与调用方事务边界
    目的/目标：写入失败只记 FAILED 审计，调用方 BEGIN 内其他 DML 仍可见
    验证点：FAILED 审计 1 条；stg_foundation_smoke COUNT=2（含外层 INSERT）
    失败含义：嵌套写入失败误回滚外层，编排器大事务被整批撤销
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
        w.execute("BEGIN")
        w.execute("INSERT INTO stg_foundation_smoke VALUES ('MSFT','2026-06-16',120.0,'qmt','b2')")
        res = create_test_write_manager(cm).write(
            _req(report="stub-fail-1"), con=w, own_transaction=False
        )
        assert res.status == "FAILED"
        audit_cnt = w.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'"
        ).fetchone()[0]
        assert audit_cnt == 1
        # Outer transaction still active: staging insert from above remains visible.
        cnt = w.execute("SELECT COUNT(*) FROM stg_foundation_smoke").fetchone()[0]
        assert cnt == 2
        w.execute("ROLLBACK")


def test_write_ownTransactionFalse_duckdbError_doesNotOpenSecondAuditConnection(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：own_transaction=False 且 SQL 错误时不 spawn 独立审计连接（GPT P1）
    测试对象：WriteManager.write 失败路径连接策略
    目的/目标：merge 失败用同一 con 记审计，禁止 duckdb.connect 二次打开
    验证点：status=FAILED；connect_calls 为空列表
    失败含义：SQL 错误路径偷偷开第二连接写审计，锁与事务语义混乱
    """
    cm = _setup(tmp_path)
    with cm.writer() as w:
        _empty_clean_table(w)
        w.execute("BEGIN")
        connect_calls = _patch_connect_calls(monkeypatch)

        original_execute = duckdb.DuckDBPyConnection.execute

        def _fail_merge(self, sql, *args, **kwargs):
            if "INSERT INTO" in sql and "security_bar_smoke_clean" in sql:
                raise duckdb.Error("simulated merge failure")
            return original_execute(self, sql, *args, **kwargs)

        monkeypatch.setattr(duckdb.DuckDBPyConnection, "execute", _fail_merge)
        res = create_test_write_manager(cm).write(_req(), con=w, own_transaction=False)
        assert res.status == "FAILED"
        assert connect_calls == []
        w.execute("ROLLBACK")


def test_assertCanWrite_unknownId_exposesReportId() -> None:
    """覆盖范围：ValidationGateError 携带 validation_report_id
    测试对象：StubValidationGate.assert_can_write 异常载荷
    目的/目标：调用方可从异常取回被拒报告 ID 用于日志与重试
    验证点：exc_info.value.validation_report_id == 'real-123'
    失败含义：门闸错误丢失报告 ID，上游无法关联校验工件
    """
    with pytest.raises(ValidationGateError) as exc_info:
        StubValidationGate().assert_can_write("real-123", "append_only")
    assert exc_info.value.validation_report_id == "real-123"


def test_assertCanWrite_stubFail_exposesReportId() -> None:
    """覆盖范围：ValidationRejected 携带 validation_report_id
    测试对象：StubValidationGate.assert_can_write 异常载荷
    目的/目标：拒绝写入时异常须暴露具体 stub-fail 报告 ID
    验证点：exc_info.value.validation_report_id == 'stub-fail-001'
    失败含义：拒绝原因无法映射到校验报告，审计链断档
    """
    with pytest.raises(ValidationRejected) as exc_info:
        StubValidationGate().assert_can_write("stub-fail-001", "append_only")
    assert exc_info.value.validation_report_id == "stub-fail-001"
