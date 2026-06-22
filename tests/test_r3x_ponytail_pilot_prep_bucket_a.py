"""R3X ponytail pilot-prep bucket A umbrella regression tests (PROMPT_16)."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.exceptions import AdapterConfigurationError
from backend.app.datasources.service import DataSourceService
from backend.app.db.validation_gate import DbValidationGate
from backend.app.ops import interface_probe
from backend.app.ops.mutation_proof import key_table_row_counts
from backend.app.storage.staged_evidence import (
    STAGED_EVIDENCE_PHASE,
    register_staged_file_registry_rows,
)
from backend.app.sync.runners import _fetch_with_guard
from backend.app.validators.common import as_text


def test_ds01_adapterFetchLogDefaultIsNoDbSideEffect() -> None:
    """覆盖范围：BaseDataAdapter.fetch 默认 fetch_log 写入策略。
    测试对象：BaseDataAdapter.fetch 的 record_fetch_log 默认值。
    目的/目标：adapter 默认不写 fetch_log；service 为单点 owner（DS-01）。
    """
    sig = inspect.signature(BaseDataAdapter.fetch)
    default = sig.parameters["record_fetch_log"].default
    assert default is False


def test_ds02_buildAdapterDedupesFactoryPaths() -> None:
    """覆盖范围：datasources adapter factory 内部实现。
    测试对象：adapters.__init__ 模块中的 _build_adapter。
    目的/目标：create_adapter/create_test_adapter 共享 _build_adapter（DS-02）。
    """
    import backend.app.datasources.adapters as adapters_mod

    assert hasattr(adapters_mod, "_build_adapter")
    source = inspect.getsource(adapters_mod.create_adapter)
    assert "_build_adapter(" in source
    source_test = inspect.getsource(adapters_mod.create_test_adapter)
    assert "_build_adapter(" in source_test


def test_ds03_productionFetchRejectsImplicitTestAdapter() -> None:
    """覆盖范围：DataSourceService 生产 fetch 路径。
    测试对象：DataSourceService.fetch 在无 file_registry_factory 且非 fixture 时的行为。
    目的/目标：production fetch 不得隐式 create_test_adapter（DS-03）。
    """
    import duckdb
    from backend.app.datasources.fetch_result import FetchRequest

    service = DataSourceService()
    req = FetchRequest(
        run_id="r1",
        source_id="akshare",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        instrument_id="sh.600519",
    )
    con = duckdb.connect(":memory:")
    with pytest.raises(AdapterConfigurationError, match="fetch_port is required"):
        service.fetch(req, con=con, job_id=None)


def test_sc02_stagedEvidenceRejectsWrongPhase() -> None:
    """覆盖范围：staged_evidence WriteManager 旁路契约。
    测试对象：register_staged_file_registry_rows 的 phase 门禁。
    目的/目标：非 phase3_staged 不得旁路写入 file_registry（SC-02）。
    """
    import duckdb
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult

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
        register_staged_file_registry_rows(
            con,
            result,
            data_root=Path("."),
            phase="phase4_clean",
        )


def _test_cm(tmp_path: Path) -> ConnectionManager:
    import duckdb
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    return ConnectionManager(db)


def test_sc02_stagedEvidenceAllowsPhase3Token(tmp_path: Path) -> None:
    """覆盖范围：staged_evidence 合法 phase 路径。
    测试对象：register_staged_file_registry_rows phase=phase3_staged。
    目的/目标：文档化 phase3 旁路在显式 token 下可用（SC-02）。
    """
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.db.connection import ConnectionManager

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
        ids = register_staged_file_registry_rows(
            con,
            result,
            data_root=data_root,
            phase=STAGED_EVIDENCE_PHASE,
        )
    assert len(ids) == 1


def test_op02_interfaceProbeUsesMutationProofNotLivePilotPrivate() -> None:
    """覆盖范围：interface_probe 与 live_pilot 导入边界。
    测试对象：interface_probe 模块导入面。
    目的/目标：probe 经 mutation_proof 取 key counts，不 import live_pilot 私有 API（OP-02）。
    """
    source = inspect.getsource(interface_probe)
    assert "live_pilot" not in source
    assert "mutation_proof" in source
    assert key_table_row_counts is not None


def test_sy04_fetchWithGuardUnifiesAdapterAndCallablePaths(tmp_path: Path) -> None:
    """覆盖范围：sync runners fetch + ResourceGuard 统一入口。
    测试对象：runners._fetch_with_guard。
    目的/目标：adapter 与 fetch_callable 共用 helper（SY-04）。
    """
    from backend.app.datasources.fetch_result import FetchRequest, FetchResult
    from backend.app.db.connection import ConnectionManager

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
    """覆盖范围：validators common 文本规范化。
    测试对象：common.as_text(None)。
    目的/目标：None 不变成字面量 \"None\" 字符串（VA-03）。
    """
    assert as_text(None) is None
    assert as_text("None") == "None"


def test_db03_assertCanWriteSingleEntryWithOptionalCon() -> None:
    """覆盖范围：DbValidationGate 写入门面。
    测试对象：DbValidationGate.assert_can_write。
    目的/目标：合并 assert_can_write_with 为 con= 可选单入口（DB-03）。
    """
    sig = inspect.signature(DbValidationGate.assert_can_write)
    assert "con" in sig.parameters
    assert not hasattr(DbValidationGate, "assert_can_write_with")


def test_mutationProof_keyTableCountsEmptyDb(tmp_path: Path) -> None:
    """覆盖范围：mutation_proof 只读计数。
    测试对象：key_table_row_counts。
    目的/目标：缺失 DB 文件返回空 dict，供 probe/pilot 共享（OP-02）。
    """
    missing = tmp_path / "missing.duckdb"
    assert key_table_row_counts(missing) == {}
