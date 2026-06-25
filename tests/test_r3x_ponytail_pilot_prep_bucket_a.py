"""R3X ponytail pilot-prep 桶 A 回归测试（PROMPT_16）。

覆盖范围：adapter 工厂默认无 DB 副作用、生产 fetch 须显式端口、staged evidence 旁路
phase 门禁、interface_probe 与 live_pilot 导入边界、sync guard 统一入口等 DS/SC/OP 项。
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.exceptions import AdapterConfigurationError
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.service import DataSourceService
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import DbValidationGate
from backend.app.ops import interface_probe
from backend.app.ops.mutation_proof import key_table_row_counts
from backend.app.storage.staged_evidence import (
    STAGED_EVIDENCE_PHASE,
    _register_staged_file_registry_rows,
)
from backend.app.sync.runners import _fetch_with_guard
from backend.app.validators.common import as_text


def _test_cm(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    return ConnectionManager(db)


def test_ds01_adapterFetchLogDefaultIsNoDbSideEffect() -> None:
    """覆盖范围：adapter fetch 默认不写 fetch_log（DS-01）
    测试对象：BaseDataAdapter.fetch 的 record_fetch_log 默认参数
    目的/目标：adapter 层默认无 DB 副作用，fetch_log 由 service 单点写入
    验证点：inspect.signature 中 record_fetch_log 默认值为 False
    失败含义：adapter 默认写 fetch_log，与 service 单点 owner 契约冲突、重复记账
    """
    sig = inspect.signature(BaseDataAdapter.fetch)
    default = sig.parameters["record_fetch_log"].default
    assert default is False


def test_ds02_buildAdapterDedupesFactoryPaths() -> None:
    """覆盖范围：adapter 工厂路径去重（DS-02）
    测试对象：adapters 模块 _build_adapter 与 create_* 入口
    目的/目标：create_adapter 与 create_test_adapter 应共用 _build_adapter 实现
    验证点：模块含 _build_adapter；两 create 函数源码均调用 _build_adapter(
    失败含义：双份工厂逻辑漂移，测试与生产 adapter 构造行为不一致
    """
    import backend.app.datasources.adapters as adapters_mod

    assert hasattr(adapters_mod, "_build_adapter")
    source = inspect.getsource(adapters_mod.create_adapter)
    assert "_build_adapter(" in source
    source_test = inspect.getsource(adapters_mod.create_test_adapter)
    assert "_build_adapter(" in source_test


def test_ds03_productionFetchRejectsImplicitTestAdapter(monkeypatch) -> None:
    """覆盖范围：生产 fetch 禁止隐式 test adapter（DS-03）
    测试对象：DataSourceService.fetch（无 fetch_port、非 fixture）
    目的/目标：生产路径须显式 fetch_port，不得静默 create_test_adapter
    验证点：pytest.raises(AdapterConfigurationError, match='fetch_port is required')
    失败含义：生产环境误用 test adapter，数据来源与审计边界被击穿
    """
    # ponytail: adapter-only; apply_migrations = prod-shaped log table; guard thresholds → test_resource_guard.py
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service = DataSourceService()
    req = FetchRequest(
        run_id="r1",
        source_id="akshare",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        instrument_id="sh.600519",
    )
    con = duckdb.connect(":memory:")
    apply_migrations(con)  # ponytail: prod-shaped con so guard WARN log does not CatalogException
    with pytest.raises(AdapterConfigurationError, match="fetch_port is required"):
        service.fetch(req, con=con, job_id=None)


def test_sc02_stagedEvidenceRejectsWrongPhase() -> None:
    """覆盖范围：staged evidence 旁路 phase 门禁（SC-02）
    测试对象：_register_staged_file_registry_rows
    目的/目标：非 phase3_staged 不得旁路写入 file_registry
    验证点：phase=phase4_clean 时 pytest.raises(ValueError, match='phase3_staged')
    失败含义：任意 phase 可写 registry，staged 旁路与 clean 路径混淆
    """
    con = duckdb.connect(":memory:")
    result = FetchResult(
        run_id="r1",
        source_id="akshare",
        data_domain="macro_supplementary",
        status="SUCCESS",
        row_count=1,
        fetch_time=datetime.now(UTC).isoformat(),
        raw_file_paths=["raw.json"],
        content_hash="hash1",
    )
    with pytest.raises(ValueError, match="phase3_staged"):
        _register_staged_file_registry_rows(
            con,
            result,
            data_root=Path("."),
            phase="phase4_clean",
        )


def test_sc02_stagedEvidenceAllowsPhase3Token(tmp_path: Path) -> None:
    """覆盖范围：staged evidence 合法 phase3 旁路（SC-02）
    测试对象：_register_staged_file_registry_rows（phase=STAGED_EVIDENCE_PHASE）
    目的/目标：显式 phase3_staged token 下应成功注册 file_registry 行
    验证点：返回 ids 长度为 1
    失败含义：合法 staged 旁路被误拒，Phase3 证据无法登记 raw 文件
    """
    cm = _test_cm(tmp_path)
    data_root = tmp_path / "data"
    raw = data_root / "nested" / "raw.json"
    raw.parent.mkdir(parents=True)
    raw.write_text("{}", encoding="utf-8")
    result = FetchResult(
        run_id="r1",
        source_id="akshare",
        data_domain="macro_supplementary",
        status="SUCCESS",
        row_count=1,
        fetch_time=datetime.now(UTC).isoformat(),
        raw_file_paths=[str(raw)],
        content_hash="unique-hash-sc02",
    )
    with cm.writer() as con:
        ids = _register_staged_file_registry_rows(
            con,
            result,
            data_root=data_root,
            phase=STAGED_EVIDENCE_PHASE,
        )
    assert len(ids) == 1


def test_op02_interfaceProbeUsesMutationProofNotLivePilotPrivate() -> None:
    """覆盖范围：interface_probe 与 live_pilot 导入边界（OP-02）
    测试对象：interface_probe 模块源码
    目的/目标：probe 经 mutation_proof 取 key counts，不依赖 live_pilot 私有 API
    验证点：源码不含 live_pilot；含 mutation_proof；key_table_row_counts 可引用
    失败含义：probe 耦合 live_pilot 私有实现，pilot 重构即破坏运维探针
    """
    source = inspect.getsource(interface_probe)
    assert "live_pilot" not in source
    assert "mutation_proof" in source
    assert key_table_row_counts is not None


def test_sy04_fetchWithGuardUnifiesAdapterAndCallablePaths(tmp_path: Path) -> None:
    """覆盖范围：sync fetch 与 ResourceGuard 统一入口（SY-04）
    测试对象：runners._fetch_with_guard
    目的/目标：adapter 路径应先过 guard 再 fetch，且返回 SUCCESS
    验证点：result.status=SUCCESS；calls 顺序为 ['guard', 'fetch']
    失败含义：guard 与 fetch 顺序错乱或分支不统一，资源暂停时仍可能拉数
    """
    cm = _test_cm(tmp_path)
    req = FetchRequest(
        run_id="r1",
        source_id="akshare",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        instrument_id="sh.600519",
    )
    calls: list[str] = []

    class StubAdapter:
        source_id = "akshare"

        def fetch(self, _req, *, con, job_id=None):
            calls.append("fetch")
            return FetchResult(
                run_id="r1",
                source_id="akshare",
                data_domain="cn_equity_daily_bar",
                status="SUCCESS",
                row_count=1,
                fetch_time="2026-06-22T00:00:00Z",
                staging_table="stg_test",
            )

    def begin_ok(_job_id: str) -> bool:
        calls.append("guard")
        return True

    result = _fetch_with_guard(
        begin_fetching=begin_ok,
        job_id="j1",
        cm=cm,
        req=req,
        adapter=StubAdapter(),
        fetch_callable=None,
    )
    assert result.status == "SUCCESS"
    assert calls == ["guard", "fetch"]


def test_va03_asTextNoneIsNotLiteralString() -> None:
    """覆盖范围：校验层文本规范化 None 语义（VA-03）
    测试对象：validators.common.as_text
    目的/目标：None 应保持 None，不得变成字面量字符串 "None"
    验证点：as_text(None) is None；as_text("None") == "None"
    失败含义：空值被写成 "None" 字符串，DB 与报表出现伪非空字段
    """
    assert as_text(None) is None
    assert as_text("None") == "None"


def test_db03_assertCanWriteSingleEntryWithOptionalCon() -> None:
    """覆盖范围：DbValidationGate 写入门面合并（DB-03）
    测试对象：DbValidationGate.assert_can_write
    目的/目标：单入口 assert_can_write 接受可选 con，废弃 assert_can_write_with
    验证点：signature 含 con 参数；类上无 assert_can_write_with 属性
    失败含义：双写入门面并存，调用方不知用哪条路径、行为易分叉
    """
    sig = inspect.signature(DbValidationGate.assert_can_write)
    assert "con" in sig.parameters
    assert not hasattr(DbValidationGate, "assert_can_write_with")


def test_mutationProof_keyTableCountsEmptyDb(tmp_path: Path) -> None:
    """覆盖范围：mutation_proof 缺失 DB 时的只读计数（OP-02）
    测试对象：key_table_row_counts
    目的/目标：DB 文件不存在应返回空 dict，供 probe/pilot 安全调用
    验证点：key_table_row_counts(不存在的路径) == {}
    失败含义：缺库抛错而非空结果，interface_probe 无法在无 DB 环境运行
    """
    missing = tmp_path / "missing.duckdb"
    assert key_table_row_counts(missing) == {}
