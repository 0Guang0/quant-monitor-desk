"""Round 2 Batch B 适配器骨架：fetch 路径、错误映射与工厂注入契约。"""

from pathlib import Path

import pytest
from backend.app.storage.raw_store import sha256_hex


def test_adapterPackage_importable():
    """覆盖范围：datasources.adapters 包可导入性
    测试对象：backend.app.datasources.adapters
    目的/目标：适配器包须无循环依赖且可被测试/工厂加载
    验证点：import 不抛异常
    失败含义：适配器包损坏，所有数据源集成无法启动
    """
    import backend.app.datasources.adapters  # noqa: F401


def test_skeletonAdapterBase_successWritesRawFile(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_class,
):
    """覆盖范围：SkeletonAdapterBase 成功 fetch 写 raw 文件
    测试对象：BaostockSkeleton.fetch + StubFetchPort
    目的/目标：成功拉取数据后应留下原始文件、抓取日志和内容指纹
    验证点：status=SUCCESS；raw 文件存在；fetch_log 1 条；hash 匹配
    失败含义：骨架成功路径不写原始文件或日志，数据源血缘无法追溯
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.status == "SUCCESS"
    assert result.row_count == 1
    assert len(result.raw_file_paths) == 1
    assert Path(result.raw_file_paths[0]).is_file()
    assert result.content_hash == sha256_hex(stub_fetch_bytes)
    fetch_log_count = con.execute(
        "SELECT COUNT(*) FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()[0]
    assert fetch_log_count == 1


def test_skeletonAdapterBase_registersFileRegistryWhenInjected(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：注入 file_registry 时登记 raw 路径
    测试对象：SkeletonAdapterBase + file_registry
    目的/目标：抓取成功后须在文件登记表记录路径与内容指纹
    验证点：DB 行存在且 path/hash 与 FetchResult 一致
    失败含义：raw 文件未进注册表，下游无法按 hash 去重与追溯
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con)
    con.close()
    with stack["cm"].reader() as reader:
        row = reader.execute(
            "SELECT local_path, content_hash FROM file_registry WHERE local_path = ?",
            [result.raw_file_paths[0]],
        ).fetchone()
    assert row is not None
    assert row[0] == result.raw_file_paths[0]
    assert row[1] == result.content_hash


@pytest.mark.parametrize(
    "status,error_type",
    [
        ("AUTH_FAILED", "auth"),
        ("RATE_LIMITED", "rate_limit"),
        ("NETWORK_ERROR", "network"),
        ("SCHEMA_DRIFT", "schema"),
        ("EMPTY_RESPONSE", "empty"),
        ("NOT_PUBLISHED_YET", "not_published"),
        ("FAILED", "failed"),
    ],
)
def test_portErrors_mapStatusAndFetchLog(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    baostock_skeleton_market_only_class,
    status,
    error_type,
):
    """覆盖范围：FailingPort 各错误状态映射（参数化）
    测试对象：SkeletonAdapterBase + FailingPort(status)
    目的/目标：各类端口错误应映射到统一的抓取状态与日志错误类型
    验证点：result.status 等于注入 status；log 的 error_type 匹配
    失败含义：错误分类不一致，运维与重试策略无法按类型处理
    """
    from backend.app.datasources.adapters.fetch_port import FailingPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=FailingPort(status=status, message=f"simulated {status}"),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.status == status
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == status and row[1] == error_type


def test_baostockAdapter_matchesRegistryDomains(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    """覆盖范围：BaostockAdapter 与 registry 域对齐
    测试对象：BaostockAdapter.supported_domains
    目的/目标：适配器声明域须含 cn_equity_basic_financial 且可成功 fetch
    验证点：source_id=baostock；基本面域 fetch SUCCESS
    失败含义：registry 与适配器域不一致，路由选中后 fetch 失败
    """
    from backend.app.datasources.adapters.baostock import BaostockAdapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    assert adapter.source_id == "baostock"
    assert "cn_equity_basic_financial" in adapter.supported_domains
    req = request_factory("baostock", "cn_equity_basic_financial")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"


def test_qmtAdapter_localClientMissing_returnsAuthFailed(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
):
    """覆盖范围：QMT 本地客户端未运行
    测试对象：QmtXtdataAdapter + FailingPort(AUTH_FAILED)
    目的/目标：QMT 未连接时应判定为认证失败，并记录为认证类错误
    验证点：status=AUTH_FAILED；fetch_log error_type=auth
    失败含义：客户端缺失被标为网络错误，用户无法按文档排查
    """
    from backend.app.datasources.adapters.fetch_port import FailingPort
    from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = QmtXtdataAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=FailingPort("AUTH_FAILED", "QMT client not running"),
    )
    req = request_factory("qmt_xtdata", "cn_equity_minute_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.status == "AUTH_FAILED"
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == "AUTH_FAILED" and row[1] == "auth"


def test_qmtAdapter_stubClient_successWritesRaw(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    """覆盖范围：QMT stub 客户端成功 fetch
    测试对象：QmtXtdataAdapter + StubFetchPort
    目的/目标：分钟线数据在测试端口下应能成功拉取并生成原始文件路径
    验证点：status=SUCCESS；raw_file_paths 非空
    失败含义：QMT 骨架成功路径不通，分钟线集成无法验证
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = QmtXtdataAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("qmt_xtdata", "cn_equity_minute_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.raw_file_paths


@pytest.mark.parametrize(
    "adapter_cls,source_id,domain",
    [
        ("AkshareAdapter", "akshare", "macro_supplementary"),
        ("CninfoAdapter", "cninfo", "cn_announcements"),
    ],
)
def test_vendorSkeleton_exposesSourceId(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    adapter_cls,
    source_id,
    domain,
):
    """覆盖范围：Akshare/Cninfo 骨架 source_id 与 fetch（参数化）
    测试对象：vendor 适配器类 + StubFetchPort
    目的/目标：各供应商骨架应暴露正确的数据源标识，且对应业务域可成功拉取
    验证点：adapter.source_id 匹配；fetch.status=SUCCESS
    失败含义：供应商骨架标识错误或域不可用，数据源矩阵出现缺口
    """
    import importlib

    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    mod = importlib.import_module("backend.app.datasources.adapters")
    cls = getattr(mod, adapter_cls)
    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = cls(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    assert adapter.source_id == source_id
    req = request_factory(source_id, domain)
    assert adapter.fetch(req, con=con).status == "SUCCESS"


def test_cninfoAdapter_unpublished_returnsNotPublishedYet(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
):
    """覆盖范围：Cninfo 未发布接口
    测试对象：CninfoAdapter + UnpublishedPort
    目的/目标：尚未上线的接口应明确标记为「未发布」，而非普通失败
    验证点：status 与 message 语义；fetch_log 一致
    失败含义：未发布接口被标为普通失败，调用方无法区分等待上线
    """
    from backend.app.datasources.adapters.cninfo import CninfoAdapter
    from backend.app.datasources.adapters.fetch_port import UnpublishedPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = CninfoAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=UnpublishedPort(),
    )
    req = request_factory("cninfo", "cn_announcements")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.status == "NOT_PUBLISHED_YET"
    assert "not published" in (result.error_message or "").lower()
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == "NOT_PUBLISHED_YET" and row[1] == "not_published"


def test_yahooAdapter_registryMarkedValidationOnly(batch_b_registry):
    """覆盖范围：yahoo_finance registry 仅校验标记
    测试对象：batch_b_registry.get('yahoo_finance')
    目的/目标：Yahoo 源只能用于校验对照，不得作为生产主数据源
    验证点：rec.validation_only is True
    失败含义：Yahoo 可作主源，违反多源路由与合规策略
    """
    rec = batch_b_registry.get("yahoo_finance")
    assert rec.validation_only is True


def test_createAdapter_unknownSource_raisesAdapterNotSupportedError(
    batch_b_registry,
    raw_data_root,
    file_registry_stack,
    stub_fetch_bytes,
):
    """覆盖范围：create_adapter 未知 source_id
    测试对象：create_adapter('not_a_source', ...)
    目的/目标：请求未注册的数据源时应明确报错，并提示已知源列表
    验证点：异常含 source_id 与 known 列表（含 baostock）
    失败含义：未知源静默失败或 generic 异常，调用方无法纠错
    """
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.exceptions import AdapterNotSupportedError

    stack = file_registry_stack
    with pytest.raises(AdapterNotSupportedError) as exc_info:
        create_adapter(
            "not_a_source",
            batch_b_registry,
            raw_data_root,
            fetch_port=StubFetchPort(payload=stub_fetch_bytes),
            file_registry=stack["file_registry"],
        )
    assert exc_info.value.source_id == "not_a_source"
    assert "baostock" in exc_info.value.known


def test_createAdapter_withoutFetchPort_raisesAdapterConfigurationError(
    batch_b_registry,
    raw_data_root,
    file_registry_stack,
):
    """覆盖范围：create_adapter 缺 fetch_port
    测试对象：create_adapter 不传 fetch_port
    目的/目标：生产环境创建适配器时必须注入抓取端口，禁止隐式默认值
    验证点：AdapterConfigurationError 消息含 fetch_port is required
    失败含义：无端口仍能建适配器，可能静默使用错误的测试替身
    """
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.exceptions import AdapterConfigurationError

    stack = file_registry_stack
    with pytest.raises(AdapterConfigurationError, match="fetch_port is required"):
        create_adapter(
            "baostock",
            batch_b_registry,
            raw_data_root,
            file_registry=stack["file_registry"],
        )


def test_createAdapter_withoutFileRegistry_raisesAdapterConfigurationError(
    batch_b_registry,
    raw_data_root,
    stub_fetch_bytes,
):
    """覆盖范围：create_adapter 缺 file_registry
    测试对象：create_adapter 不传 file_registry
    目的/目标：生产环境创建适配器时必须注入文件登记表
    验证点：AdapterConfigurationError 消息含 file_registry is required
    失败含义：raw 文件无法登记，血缘与去重链路断裂
    """
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.exceptions import AdapterConfigurationError

    with pytest.raises(AdapterConfigurationError, match="file_registry is required"):
        create_adapter(
            "baostock",
            batch_b_registry,
            raw_data_root,
            fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        )


def test_createTestAdapter_defaultStubFetchPort_success(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    raw_data_root,
):
    """覆盖范围：create_test_adapter 默认 stub 端口
    测试对象：create_test_adapter + 默认 StubFetchPort
    目的/目标：测试用工厂应零配置即可完成一次成功抓取
    验证点：fetch.status == SUCCESS
    失败含义：测试辅助工厂不可用，大量集成测试无法起步
    """
    from backend.app.datasources.adapters import create_test_adapter

    con = migrated_con(tmp_path)
    adapter = create_test_adapter("baostock", batch_b_registry, raw_data_root)
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"


def test_skeletonAdapterBase_resolveAsOfFromEndTime(
    tmp_path,
    migrated_con,
    batch_b_registry,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：end_time 推导 as_of 与 raw 路径分区
    测试对象：SkeletonAdapterBase.fetch(end_time=...)
    目的/目标：截止时间应规范为按日对齐的时间戳，并体现在原始文件路径的日期段
    验证点：as_of_timestamp=2026-06-01；路径含 2026-06-01
    失败含义：as_of 与物理 raw 分区不一致，按日落盘错乱
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.fetch_result import FetchRequest

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = FetchRequest(
        run_id="run-asof",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        end_time="2026-06-01T15:30:00Z",
    )
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.as_of_timestamp == "2026-06-01"
    assert "2026-06-01" in Path(result.raw_file_paths[0]).parts


def test_yahooAdapter_createAdapter_fetchesSuccessfully(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    raw_data_root,
    file_registry_stack,
    stub_fetch_bytes,
):
    """覆盖范围：create_adapter 实例化 yahoo_finance
    测试对象：create_adapter('yahoo_finance', ...)
    目的/目标：校验专用的 Yahoo 适配器经工厂创建后应能成功抓取
    验证点：SUCCESS；row_count=1；raw 路径 1 条
    失败含义：Yahoo 工厂路径断裂，美股校验源无法集成测试
    """
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = create_adapter(
        "yahoo_finance",
        batch_b_registry,
        raw_data_root,
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory("yahoo_finance", "us_equity_daily_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.row_count == 1
    assert len(result.raw_file_paths) == 1


@pytest.mark.parametrize(
    "source_id,domain",
    [
        ("baostock", "cn_equity_daily_bar"),
        ("qmt_xtdata", "cn_equity_minute_bar"),
        ("akshare", "macro_supplementary"),
        ("cninfo", "cn_announcements"),
        ("yahoo_finance", "us_equity_daily_bar"),
    ],
)
def test_createAdapter_allRegisteredSources_success(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    raw_data_root,
    file_registry_stack,
    stub_fetch_bytes,
    source_id,
    domain,
):
    """覆盖范围：已注册五源工厂矩阵（参数化）
    测试对象：create_adapter 对各 source_id/domain
    目的/目标：已注册的全部数据源经工厂创建后，在测试端口下都应能成功抓取
    验证点：各组合 status=SUCCESS 且 raw_file_paths 非空
    失败含义：某注册源工厂或域组合断裂，源矩阵不完整
    """
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = create_adapter(
        source_id,
        batch_b_registry,
        raw_data_root,
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory(source_id, domain)
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.raw_file_paths


def test_largePayload_returnsFailedAndDoesNotWriteRaw(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：payload 超 max_payload_bytes
    测试对象：SkeletonAdapterBase(max_payload_bytes=100) + 200 字节 payload
    目的/目标：超大响应须 FAILED 且不写 raw 文件
    验证点：status=FAILED；message 含 payload too large；raw_file_paths 空
    失败含义：巨包可落盘，磁盘与内存 DoS 风险
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    huge = b"x" * 200
    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=huge),
        max_payload_bytes=100,
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "FAILED"
    assert "payload too large" in (result.error_message or "")
    assert not result.raw_file_paths


def test_payloadRowCount_propagatesToFetchResultAndFetchLog(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：FetchPayload.row_count 传播
    测试对象：StubFetchPort(row_count=42)
    目的/目标：端口声明行数须同步到 FetchResult 与 fetch_log
    验证点：result.row_count=42；fetch_log.row_count=42
    失败含义：行数元数据丢失，质量校验与审计统计不准
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes, row_count=42),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.row_count == 42
    row = con.execute("SELECT row_count FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] == 42


def test_payloadSchemaHash_propagatesToFetchResultAndFetchLog(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：FetchPayload.schema_hash 传播
    测试对象：StubFetchPort(schema_hash=...)
    目的/目标：schema_hash 须写入 FetchResult 与 fetch_log
    验证点：两处 schema_hash 均等于注入值
    失败含义： schema 版本无法追溯，漂移检测失效
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    schema_hash = "abc123schema"
    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=b'{"a":1}', schema_hash=schema_hash),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.schema_hash == schema_hash
    row = con.execute("SELECT schema_hash FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] == schema_hash


def test_payloadRetryCount_propagatesToFetchResultAndFetchLog(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：FetchPayload.retry_count 传播
    测试对象：StubFetchPort(retry_count=3)
    目的/目标：重试次数须同步到 FetchResult 与 fetch_log
    验证点：result.retry_count=3；fetch_log.retry_count=3
    失败含义：重试信息丢失，SLA 与故障分析无据
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes, retry_count=3),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.retry_count == 3
    row = con.execute("SELECT retry_count FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] == 3


def test_fetchRecordsLatencyMsWhenPayloadOmitsIt(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：payload 未提供 latency 时的自动记录
    测试对象：SkeletonAdapterBase.fetch(record_fetch_log=True)
    目的/目标：即使端口未给 latency_ms，也须记录非负延迟到 result 与 log
    验证点：result.latency_ms 非空且 ≥0；fetch_log.latency_ms 非空
    失败含义：延迟指标缺失，性能监控与 SLO 无法统计
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.latency_ms is not None
    assert result.latency_ms >= 0
    row = con.execute("SELECT latency_ms FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] is not None


def test_inferSchemaHash_detectsNestedStructureDrift():
    """覆盖范围：_infer_schema_hash 嵌套结构漂移
    测试对象：_infer_schema_hash(JSON 嵌套键不同)
    目的/目标：嵌套字段名变化应产生不同 schema_hash
    验证点：base != nested
    失败含义：结构漂移检测不敏感，schema 变更被漏报
    """
    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.adapters.skeleton_base import _infer_schema_hash

    base = _infer_schema_hash(FetchPayload(content=b'{"a": {"b": 1}}', file_type="json"))
    nested = _infer_schema_hash(FetchPayload(content=b'{"a": {"c": 1}}', file_type="json"))
    assert base != nested


def test_inferSchemaHash_detectsTypeDrift():
    """覆盖范围：_infer_schema_hash 类型漂移
    测试对象：_infer_schema_hash(数值 vs 字符串)
    目的/目标：同键不同类型应产生不同 schema_hash
    验证点：as_int != as_str
    失败含义：类型漂移无法检测，下游解析可能静默出错
    """
    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.adapters.skeleton_base import _infer_schema_hash

    as_int = _infer_schema_hash(FetchPayload(content=b'{"a": 1}', file_type="json"))
    as_str = _infer_schema_hash(FetchPayload(content=b'{"a": "1"}', file_type="json"))
    assert as_int != as_str


def test_resolveAsOf_isoTimestamp_normalizesToDate(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：ISO end_time 规范为日期 as_of
    测试对象：fetch(end_time='2026-06-17T15:30:00Z')
    目的/目标：带时戳的 end_time 应归一化为 YYYY-MM-DD as_of_timestamp
    验证点：result.as_of_timestamp == '2026-06-17'
    失败含义：as_of 截断错误，按日对齐与 raw 分区错乱
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.fetch_result import FetchRequest

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = FetchRequest(
        run_id="r1",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        end_time="2026-06-17T15:30:00Z",
    )
    result = adapter.fetch(req, con=con)
    assert result.as_of_timestamp == "2026-06-17"


def test_resolveAsOf_invalidDate_returnsFailedFetch(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    baostock_skeleton_market_only_class,
):
    """覆盖范围：非法 end_time 的 fail-closed
    测试对象：fetch(end_time='not-a-date')
    目的/目标：无法解析的 end_time 应 FAILED 且说明 invalid end_time
    验证点：status=FAILED；error_message 含 invalid end_time
    失败含义：脏时间仍走成功路径，raw 分区与 as_of 不可信
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.fetch_result import FetchRequest

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_market_only_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = FetchRequest(
        run_id="r2",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        end_time="not-a-date",
    )
    result = adapter.fetch(req, con=con)
    assert result.status == "FAILED"
    assert "invalid end_time" in (result.error_message or "")
