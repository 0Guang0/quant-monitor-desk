"""数据适配器契约与 fetch_log 测试（Batch A）。

覆盖范围：FetchResult/FetchRequest 校验、FetchLogWriter 持久化与脱敏、
BaseDataAdapter.fetch 闸门与 opt-in 日志。
"""

from __future__ import annotations

import json

import duckdb
import pytest
from backend.app.datasources.adapters.fetch_port import PortErrorStatus
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.exceptions import SourceMismatchError
from backend.app.datasources.fetch_log import FetchLogValidationError, FetchLogWriter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import DomainNotAllowedError
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from pydantic import ValidationError

CONTRACT_STATUSES = [
    "SUCCESS",
    "EMPTY_RESPONSE",
    "NOT_PUBLISHED_YET",
    "DISABLED_SOURCE",
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "FAILED",
]
ERROR_TYPE_BY_STATUS = {
    "SUCCESS": None,
    "EMPTY_RESPONSE": "empty",
    "NOT_PUBLISHED_YET": "not_published",
    "DISABLED_SOURCE": "disabled_source",
    "AUTH_FAILED": "auth",
    "RATE_LIMITED": "rate_limit",
    "NETWORK_ERROR": "network",
    "SCHEMA_DRIFT": "schema",
    "FAILED": "failed",
}


class _EmptyResponseAdapter(BaseDataAdapter):
    """Returns EMPTY_RESPONSE for fetch_log contract tests."""

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


def _valid_result_for_status(status: str) -> FetchResult:
    base = {
        "run_id": "r",
        "source_id": "s",
        "data_domain": "d",
        "fetch_time": "2026-06-17T10:00:00Z",
    }
    if status == "SUCCESS":
        return FetchResult(**base, status=status, row_count=1, staging_table="stg_x")
    if status == "EMPTY_RESPONSE":
        return FetchResult(**base, status=status, row_count=0)
    if status == "NOT_PUBLISHED_YET":
        return FetchResult(
            **base,
            status=status,
            row_count=0,
            error_message="announcement not published yet",
        )
    if status == "DISABLED_SOURCE":
        return FetchResult(
            **base,
            status=status,
            row_count=0,
            error_message="source disabled by registry policy",
        )
    return FetchResult(**base, status=status, row_count=0, error_message="err")


@pytest.mark.parametrize("status", CONTRACT_STATUSES)
def test_fetchResult_allContractStatuses_areAccepted(status):
    """覆盖范围：抓取结果模型支持的全部状态码能否正常构造
    测试对象：FetchResult（parametrize CONTRACT_STATUSES）
    目的/目标：供应商返回的各种成败状态都应能被系统识别和记录
    验证点：九种 CONTRACT_STATUSES 均可被 Pydantic 接受；r.status == 入参 status
    失败含义：合法 vendor 状态被拒，fetch 结果无法序列化
    """
    r = _valid_result_for_status(status)
    assert r.status == status


def test_fetchRequest_missingRunId_raisesValidationError():
    """覆盖范围：抓取请求缺少运行批次号时的拒绝逻辑
    测试对象：FetchRequest 缺 run_id
    目的/目标：没有批次号的抓取请求不应被接受，否则无法追溯是哪次同步
    验证点：pytest.raises(ValidationError)
    失败含义：无 run 关联的抓取请求可创建，审计链断裂
    """
    with pytest.raises(ValidationError):
        FetchRequest(source_id="s", data_domain="d")


def test_fetchResult_notPublishedYet_withoutPublishMessage_raisesValidationError():
    """覆盖范围：「尚未发布」状态的错误说明是否足够明确
    测试对象：FetchResult status=NOT_PUBLISHED_YET 无 publish 文案
    目的/目标：「还没发布」和「返回为空」是两种不同情况，错误说明要能区分开
    验证点：error_message 缺 publish 关键词时 pytest.raises(ValidationError, match=publish-related)
    失败含义：未发布与空响应混淆，重试策略错误
    """
    with pytest.raises(ValidationError, match="publish-related"):
        FetchResult(
            run_id="r",
            source_id="s",
            data_domain="d",
            status="NOT_PUBLISHED_YET",
            row_count=0,
            fetch_time="2026-06-17T10:00:00Z",
            error_message="data not ready",
        )


def test_fetchResult_notPublishedYet_withPublishMessage_isAccepted():
    """覆盖范围：「尚未发布」与「成功」两种合法结果能否正确建模
    测试对象：FetchResult NOT_PUBLISHED_YET / SUCCESS 样例
    目的/目标：说明里写清「公告未发布」应被接受；成功结果必须带上可核验的数据落点
    验证点：含 announcement not published yet 可构造；SUCCESS 样例 staging_table=stg_x
    失败含义：合法未发布或成功结果建模失败
    """
    r = FetchResult(
        run_id="r",
        source_id="s",
        data_domain="d",
        status="NOT_PUBLISHED_YET",
        row_count=0,
        fetch_time="2026-06-17T10:00:00Z",
        error_message="announcement not published yet",
    )
    assert r.status == "NOT_PUBLISHED_YET"
    r = FetchResult(
        run_id="r",
        source_id="s",
        data_domain="d",
        status="SUCCESS",
        row_count=1,
        fetch_time="2026-06-17T10:00:00Z",
        staging_table="stg_x",
    )
    assert r.staging_table == "stg_x"


def test_write_successResult_insertsFetchLogRow(
    tmp_path,
    migrated_con,
    success_result,
    request_factory,
):
    """覆盖范围：成功抓取结果写入 fetch_log 时各列应完整落库
    测试对象：FetchLogWriter.write（success_result + job_id）
    目的/目标：fetch_log 含 status/row_count/job_id/raw_paths/hash
    验证点：row SUCCESS,42,job-1；raw JSON；error_type None；hash 非空
    失败含义：成功抓取无日志，血缘无法关联 fetch_id
    """
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
    """覆盖范围：网络失败时抓取日志是否仍会落库
    测试对象：FetchLogWriter.write（NETWORK_ERROR）
    目的/目标：即使拉数失败，也应留下失败记录供运维统计和排查
    验证点：status=NETWORK_ERROR；error_type=network
    失败含义：失败抓取无记录，运维无法统计失败率
    """
    con = migrated_con(tmp_path)
    fetch_id = FetchLogWriter().write(con, network_error_result())
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()
    assert row[0] == "NETWORK_ERROR" and row[1] == "network"


@pytest.mark.parametrize("status", CONTRACT_STATUSES)
def test_write_allContractStatuses_mapsErrorType(tmp_path, migrated_con, status):
    """覆盖范围：各抓取状态写入 fetch_log 时 error_type 与约定映射表一致
    测试对象：FetchLogWriter.write（parametrize status）
    目的/目标：CONTRACT_STATUSES 与 ERROR_TYPE_BY_STATUS 一致
    验证点：row status 与 error_type 匹配表
    失败含义：错误分类漂移，监控与告警规则失效
    """
    con = migrated_con(tmp_path)
    result = _valid_result_for_status(status)
    fetch_id = FetchLogWriter().write(con, result)
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()
    assert row[0] == status
    assert row[1] == ERROR_TYPE_BY_STATUS[status]


def test_portErrorStatus_doesNotDriftFromFetchStatusFailures() -> None:
    """覆盖范围：适配器端口错误码与抓取结果状态码是否对齐
    测试对象：PortErrorStatus.__args__ vs CONTRACT_STATUSES
    目的/目标：适配器能报出的错误类型不应超出系统约定的失败状态范围
    验证点：PortErrorStatus 集合与预期七项一致，且为 CONTRACT_STATUSES 子集
    失败含义：adapter 端口与 FetchResult 状态不同步，映射 bug
    """
    expected_port_statuses = {
        "AUTH_FAILED",
        "RATE_LIMITED",
        "NETWORK_ERROR",
        "SCHEMA_DRIFT",
        "EMPTY_RESPONSE",
        "NOT_PUBLISHED_YET",
        "DISABLED_SOURCE",
        "USER_AUTH_REQUIRED",
        "FAILED",
    }

    assert set(PortErrorStatus.__args__) == expected_port_statuses
    port_layer_only = {"USER_AUTH_REQUIRED"}
    assert (expected_port_statuses - port_layer_only).issubset(set(CONTRACT_STATUSES))


def test_fetchLogWriter_redactsSensitiveErrorMessage(tmp_path, migrated_con):
    """覆盖范围：错误消息敏感信息脱敏
    测试对象：FetchLogWriter.write（含 token/password/api_key/Bearer）
    目的/目标：密钥类片段替换为 [redacted]，明文不得落库
    验证点：[redacted] 在 stored；abc/secret/api_key/bearer 不在
    失败含义：凭证写入 fetch_log，安全审计事故
    """
    con = migrated_con(tmp_path)
    result = FetchResult(
        run_id="run-1",
        source_id="baostock",
        data_domain="market_bar_1d",
        status="AUTH_FAILED",
        row_count=0,
        fetch_time="2026-06-17T10:00:00Z",
        error_message=("token=abc password=secret api_key=k authorization: Bearer live-secret"),
    )

    fetch_id = FetchLogWriter().write(con, result)
    stored = con.execute(
        "SELECT error_message FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()[0]

    lowered = stored.lower()
    assert "[redacted]" in lowered
    assert "abc" not in lowered
    assert "secret" not in lowered
    assert "api_key=k" not in lowered
    assert "bearer live-secret" not in lowered


def test_fetchLogWriter_redactsApikeyWithoutUnderscore(tmp_path, migrated_con):
    """覆盖范围：无下划线的 apikey 写法是否也会被脱敏
    测试对象：FetchLogWriter.write（apikey=live123）
    目的/目标：密钥字段写法稍有不同也不应把明文写进日志
    验证点：stored 含 [REDACTED]；live123 不在 stored
    失败含义：部分密钥格式漏脱敏
    """
    con = migrated_con(tmp_path)
    result = FetchResult(
        run_id="run-1",
        source_id="baostock",
        data_domain="market_bar_1d",
        status="FAILED",
        row_count=0,
        fetch_time="2026-06-17T10:00:00Z",
        error_message="apikey=live123",
    )

    fetch_id = FetchLogWriter().write(con, result)
    stored = con.execute(
        "SELECT error_message FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()[0]

    assert "[REDACTED]" in stored
    assert "live123" not in stored


def test_fetchResult_successWithoutEvidence_raisesValidationError():
    """覆盖范围：声明「抓取成功」时是否必须附带可核验证据
    测试对象：FetchResult SUCCESS 无 raw/staging
    目的/目标：只说成功却不指明数据落在哪，下游无法核对，应直接拒绝
    验证点：缺 raw_file_paths 与 staging_table 时 pytest.raises(ValidationError, match=raw_file_paths or staging_table)
    失败含义：空成功可声明，下游 validation 无物可验
    """
    with pytest.raises(ValidationError, match="raw_file_paths or staging_table"):
        FetchResult(
            run_id="r",
            source_id="s",
            data_domain="d",
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
        )


def test_fetchResult_negativeRowCount_raisesValidationError():
    """覆盖范围：抓取行数不允许为负数
    测试对象：FetchResult row_count=-1
    目的/目标：行数是基本计数，负数没有业务含义，应在建模阶段就拦住
    验证点：row_count=-1 时 pytest.raises(ValidationError)
    失败含义：负行数进入模型，聚合统计异常
    """
    with pytest.raises(ValidationError):
        FetchResult(
            run_id="r",
            source_id="s",
            data_domain="d",
            status="EMPTY_RESPONSE",
            row_count=-1,
            fetch_time="2026-06-17T10:00:00Z",
        )


def test_fetchLogWriter_negativeRowCount_rejected(tmp_path, migrated_con):
    """覆盖范围：写日志时对行数的二次校验
    测试对象：FetchLogWriter.write（model_construct row_count=-1）
    目的/目标：就算有人绕过正常构造路径，写库前仍应拒绝非法行数
    验证点：model_construct row_count=-1 时 pytest.raises(FetchLogValidationError, match=row_count)
    失败含义：缺陷构造可写库，数据质量 gate 失效
    """
    con = migrated_con(tmp_path)
    result = FetchResult.model_construct(
        run_id="r",
        source_id="s",
        data_domain="d",
        status="EMPTY_RESPONSE",
        row_count=-1,
        fetch_time="2026-06-17T10:00:00Z",
    )
    with pytest.raises(FetchLogValidationError, match="row_count"):
        FetchLogWriter().write(con, result)


def test_fetchLogWriter_invalidFetchTime_raisesFetchLogValidationError(
    tmp_path,
    migrated_con,
    success_result,
):
    """覆盖范围：抓取时间字段格式是否合法
    测试对象：FetchLogWriter.write（fetch_time=not-a-timestamp）
    目的/目标：无法解析的抓取时间不应写入数据库，否则时序查询会乱
    验证点：fetch_time=not-a-timestamp 时 pytest.raises(FetchLogValidationError, match=invalid timestamp)
    失败含义：乱时间戳入库，时序查询与 TTL 错误
    """
    con = migrated_con(tmp_path)
    bad = success_result().model_copy(update={"fetch_time": "not-a-timestamp"})
    with pytest.raises(FetchLogValidationError, match="invalid timestamp"):
        FetchLogWriter().write(con, bad)


def test_fetchLogWriter_invalidAsOfTimestamp_raisesFetchLogValidationError(
    tmp_path,
    migrated_con,
    success_result,
):
    """覆盖范围：数据截止时刻字段格式是否合法
    测试对象：FetchLogWriter.write（as_of 月 13）
    目的/目标：不存在的日期不应作为「数据截至何时」写入日志
    验证点：as_of_timestamp=2026-13-40 时 pytest.raises(FetchLogValidationError, match=invalid timestamp)
    失败含义：as_of 边界不可信，快照对齐失败
    """
    con = migrated_con(tmp_path)
    bad = success_result().model_copy(update={"as_of_timestamp": "2026-13-40"})
    with pytest.raises(FetchLogValidationError, match="invalid timestamp"):
        FetchLogWriter().write(con, bad)


def test_write_closedConnection_propagates(tmp_path, migrated_con, success_result):
    """覆盖范围：已关闭连接错误上抛
    测试对象：FetchLogWriter.write（con 已 close）
    目的/目标：duckdb.Error 原样传播
    验证点：pytest.raises(duckdb.Error)
    失败含义：写失败被吞，调用方误以为已记日志
    """
    con = migrated_con(tmp_path)
    con.close()
    with pytest.raises(duckdb.Error):
        FetchLogWriter().write(con, success_result())


def test_write_underWriterLock_insertsFetchLogRow(tmp_path, success_result, request_factory):
    """覆盖范围：ConnectionManager writer 锁内成功写入 fetch_log
    测试对象：FetchLogWriter.write under cm.writer()
    目的/目标：迁移后 writer 上下文可插 fetch_log
    验证点：reader 侧 COUNT(*)==1
    失败含义：WM 锁路径写不进 fetch_log，并发 job 日志丢失
    """
    db = tmp_path / "writer.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    req = request_factory("baostock")
    with cm.writer() as con:
        fetch_id = FetchLogWriter().write(con, success_result(), req=req)
    with cm.reader() as con:
        row = con.execute("SELECT COUNT(*) FROM fetch_log WHERE fetch_id=?", [fetch_id]).fetchone()[
            0
        ]
    assert row == 1


def test_write_latencyAndRetryCount_persistFromResult(tmp_path, migrated_con):
    """覆盖范围：成功抓取带延迟与重试元数据时字段应原样落库
    测试对象：FetchLogWriter.write（带 latency/retry）
    目的/目标：性能与重试元数据落库
    验证点：row == (42, 2)
    失败含义：SLO 与重试分析缺原始字段
    """
    con = migrated_con(tmp_path)
    result = FetchResult(
        run_id="run-1",
        source_id="baostock",
        data_domain="market_bar_1d",
        status="SUCCESS",
        row_count=1,
        fetch_time="2026-06-17T10:00:00Z",
        staging_table="stg_x",
        latency_ms=42,
        retry_count=2,
    )
    fetch_id = FetchLogWriter().write(con, result)
    row = con.execute(
        "SELECT latency_ms, retry_count FROM fetch_log WHERE fetch_id=?", [fetch_id]
    ).fetchone()
    assert row == (42, 2)


def test_fetch_requestSourceDoesNotMatchAdapter_raisesAndWritesNoFetchLog(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：请求源与 adapter 不一致
    测试对象：BaseDataAdapter.fetch（req akshare vs adapter baostock）
    目的/目标：SourceMismatchError 且不写 fetch_log
    验证点：pytest.raises(SourceMismatchError)；fetch_log count 0
    失败含义：错源请求仍记日志或静默成功
    """
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("akshare")
    with pytest.raises(SourceMismatchError):
        adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0


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
    tmp_path,
    migrated_con,
    disabled_registry,
    request_factory,
):
    """覆盖范围：数据源被禁用时是否在真正拉数前就拦住
    测试对象：FakeAdapter.fetch（disabled_registry）
    目的/目标：已禁用的源不应再去调供应商，也不应留下抓取日志
    验证点：result.status=DISABLED_SOURCE；fetch_log COUNT(*)=0
    失败含义：禁用源仍调 vendor 或写日志
    """
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(disabled_registry)
    req = request_factory("baostock")
    result = adapter.fetch(req, con=con)
    assert result.status == "DISABLED_SOURCE"
    assert (
        con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0
    )


def test_fetch_unsupportedDomainOnAdapter_raises_andWritesNoFetchLog(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：adapter 不支持请求域时拒绝且不落 fetch_log
    测试对象：NarrowDomainAdapter.fetch(market_bar_1d)
    目的/目标：DomainNotAllowedError 且无 fetch_log
    验证点：pytest.raises(DomainNotAllowedError)；count 0
    失败含义：adapter 域声明可绕过，错误域进 vendor
    """
    con = migrated_con(tmp_path)
    adapter = NarrowDomainAdapter(loaded_registry)
    req = request_factory("baostock", domain="market_bar_1d")
    with pytest.raises(DomainNotAllowedError):
        adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0


def test_fetch_registryDomainNotAllowed_raisesBeforeImpl_andWritesNoFetchLog(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：registry 域不在源 allowed_domains
    测试对象：BroadDomainAdapter.fetch(fundamental)
    目的/目标：DISABLED_SOURCE 且未达 _fetch_impl
    验证点：result.status DISABLED_SOURCE；fetch_log 0
    失败含义：registry 域限制失效，未授权域可 fetch
    """
    con = migrated_con(tmp_path)
    adapter = BroadDomainAdapter(loaded_registry)
    req = request_factory("baostock", domain="fundamental")
    result = adapter.fetch(req, con=con)
    assert result.status == "DISABLED_SOURCE"
    assert (
        con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0
    )


def test_fetch_successResult_defaultWritesNoFetchLogRow(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：成功 fetch 默认不写日志
    测试对象：FakeAdapter.fetch（record_fetch_log 默认 False）
    目的/目标：opt-in 前 fetch_log 为空
    验证点：COUNT(*)==0
    失败含义：成功默认写日志，磁盘与隐私成本失控
    """
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 0


def test_fetch_successResult_optInWritesExactlyOneFetchLogRow(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：record_fetch_log=True 写一行
    测试对象：FakeAdapter.fetch(record_fetch_log=True)
    目的/目标：显式 opt-in 恰好一条 fetch_log
    验证点：COUNT(*)==1
    失败含义：opt-in 无效或多写，审计重复
    """
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con, record_fetch_log=True)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 1


def test_fetch_calledTwice_writesTwoRows(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：两次 opt-in fetch 两条日志
    测试对象：FakeAdapter.fetch 连续两次
    目的/目标：每次 fetch 独立 fetch_id 行
    验证点：COUNT(*)==2
    失败含义：重复 fetch 覆盖同一条日志，重试不可追溯
    """
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con, record_fetch_log=True)
    adapter.fetch(req, con=con, record_fetch_log=True)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 2


def test_fetch_alwaysWritesFetchLog_evenOnEmptyResponse(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：EMPTY_RESPONSE 也写日志（opt-in）
    测试对象：EmptyAdapter.fetch(record_fetch_log=True)
    目的/目标：空响应仍记一次 fetch
    验证点：COUNT(*)==1
    失败含义：空抓取无记录，与「失败也记」策略不一致
    """
    con = migrated_con(tmp_path)
    adapter = _EmptyResponseAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con, record_fetch_log=True)
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 1


def test_fetch_emptyResponse_hasNoStagingEvidence(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：空响应 raw_file_paths 为空数组
    测试对象：EmptyAdapter + fetch_log raw_file_paths 列
    目的/目标：EMPTY 时 JSON 为 []
    验证点：json.loads(row)==[]
    失败含义：空响应伪造 staging 路径，validation 误判有数据
    """
    con = migrated_con(tmp_path)
    adapter = _EmptyResponseAdapter(loaded_registry)
    req = request_factory("baostock")
    adapter.fetch(req, con=con, record_fetch_log=True)
    row = con.execute(
        "SELECT raw_file_paths FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()[0]
    assert json.loads(row) == []


def test_fetch_implRaises_stillWritesFetchLogAndReturnsFailed(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：_fetch_impl 异常转 FAILED
    测试对象：ExplodingAdapter.fetch(record_fetch_log=True)
    目的/目标：RuntimeError 捕获为 FAILED 且写 fetch_log
    验证点：result.status FAILED；count 1
    失败含义：vendor 异常无日志，故障静默
    """
    con = migrated_con(tmp_path)
    adapter = ExplodingAdapter(loaded_registry)
    req = request_factory("baostock")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.status == "FAILED"
    assert con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 1


def test_fetch_implDoesNotSwitchSourceId(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：impl 不得篡改 source_id
    测试对象：WrongSourceAdapter 返回 other_source
    目的/目标：FetchResult 与 fetch_log 均强制 adapter.source_id
    验证点：result.source_id 与 log 行均为 baostock
    失败含义：impl 可冒充他源，路由审计失真
    """
    con = migrated_con(tmp_path)
    adapter = WrongSourceAdapter(loaded_registry)
    req = request_factory("baostock")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.source_id == "baostock"
    row = con.execute("SELECT source_id FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()[0]
    assert row == "baostock"


def test_fetch_success_carriesEvidenceFields(
    tmp_path,
    migrated_con,
    loaded_registry,
    request_factory,
):
    """覆盖范围：成功结果携带证据字段
    测试对象：FakeAdapter.fetch 默认路径
    目的/目标：staging_table 与 raw_file_paths 非空
    验证点：result.staging_table 与 raw_file_paths 真值
    失败含义：成功无证据，下游 staging 无法挂载
    """
    con = migrated_con(tmp_path)
    adapter = FakeAdapter(loaded_registry)
    req = request_factory("baostock")
    result = adapter.fetch(req, con=con)
    assert result.staging_table
    assert result.raw_file_paths


def test_fetch_disabledPrimaryDomain_returnsDisabledSource(
    tmp_path,
    migrated_con,
    request_factory,
):
    """覆盖范围：registry 默认禁用域（分钟线）
    测试对象：MinuteBarAdapter.fetch(cn_equity_minute_bar)
    目的/目标：DISABLED_SOURCE 且 _fetch_impl 不可达
    验证点：status/row_count；fetch_log 0
    失败含义：禁用分钟线仍触达 qmt vendor
    """
    from backend.app.datasources.source_registry import SourceRegistry

    reg = SourceRegistry()
    reg.load()

    class MinuteBarAdapter(BaseDataAdapter):
        source_id = "qmt_xtdata"
        supported_domains = frozenset({"cn_equity_minute_bar"})

        def _fetch_impl(self, req):
            raise AssertionError("disabled domain must not reach vendor fetch")

    con = migrated_con(tmp_path)
    adapter = MinuteBarAdapter(reg)
    req = request_factory("qmt_xtdata", domain="cn_equity_minute_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "DISABLED_SOURCE"
    assert result.row_count == 0
    assert (
        con.execute("SELECT COUNT(*) FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()[0]
        == 0
    )


def test_dataAdapterContract_documentsStructuredSchemaHashRequirement():
    """覆盖范围：data_adapter_contract 结构化 schema_hash 契约段
    测试对象：specs/contracts/data_adapter_contract.md
    目的/目标：AC-DATA-01 — SUCCESS 结构化抓取必须非空 schema_hash，且写明 csv/parquet 有界推导
    验证点：契约含 structured 规则、json/csv/parquet、SUCCESS+row_count 约束
    失败含义：契约未冻结 fail-closed 语义，实现与审计 VR-DATA-001 无法对齐
    """
    from pathlib import Path

    text = Path("specs/contracts/data_adapter_contract.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "structured schema_hash" in lowered or "structured file types" in lowered
    for token in ("json", "csv", "parquet"):
        assert token in lowered
    assert "success" in lowered and "row_count" in lowered
    assert "schemaless" in lowered


def test_fetch_disabledDomain_returnsDisabledSourceBeforeDomainAllowed(
    tmp_path,
    migrated_con,
    request_factory,
):
    """覆盖范围：禁用域优先于 adapter 域检查
    测试对象：DailyBarAdapter.fetch(cn_equity_minute_bar)
    目的/目标：域禁用短路 DISABLED_SOURCE，即使 adapter 支持日线域
    验证点：result DISABLED_SOURCE
    失败含义：域禁用被 adapter allowed 覆盖，策略顺序错误
    """
    from backend.app.datasources.source_registry import SourceRegistry

    reg = SourceRegistry()
    reg.load()

    class DailyBarAdapter(BaseDataAdapter):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar"})

        def _fetch_impl(self, req):
            raise AssertionError("disabled domain must not reach vendor fetch")

    con = migrated_con(tmp_path)
    adapter = DailyBarAdapter(reg)
    req = request_factory("baostock", domain="cn_equity_minute_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "DISABLED_SOURCE"
