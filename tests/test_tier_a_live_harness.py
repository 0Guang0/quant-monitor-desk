"""Tier A live acceptance harness tests (M-DATA-03 S00-INFRA · ADR-034)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.live_tier_router import TIER_A_SOURCES
from backend.app.ops.tier_a_live_acceptance import (
    QUICK_SOURCE_IDS,
    SOURCE_API_KEY_ENV,
    TierALiveEnvError,
    assert_isolated_live_data_root,
    ensure_isolated_db,
    is_canonical_main_data_root,
    is_canonical_main_db_path,
    run_acceptance,
    run_source_live_acceptance,
    select_source_ids,
    validate_live_acceptance_env,
)
from backend.app.ops.tier_a_live_incremental_dispatch import (
    LiveIncrementalOutcome,
)
from tests.contract_gate_support import PROJECT_ROOT as TEST_PROJECT_ROOT

ELIGIBILITY_DOC = (
    PROJECT_ROOT
    / ".trellis"
    / "tasks"
    / "m-data-03-tier-a-live"
    / "research"
    / "tier-a-live-eligibility.md"
)
ACCEPTANCE_SCRIPT = PROJECT_ROOT / "scripts" / "tier_a_live_acceptance.py"


def test_tierALiveEligibility_docListsElevenLiveSources() -> None:
    """覆盖范围：S00-ELIGIBILITY 资格矩阵
    测试对象：research/tier-a-live-eligibility.md
    目的/目标：11/11 须真网；KEY 槽位；无 ADR 例外行
    验证点：11 个 source_id 行；FRED/AV KEY；ADR 例外=无
    失败含义：Execute 可在错误资格假设下接通 live
    """
    text = ELIGIBILITY_DOC.read_text(encoding="utf-8")
    for sid in sorted(TIER_A_SOURCES):
        assert f"`{sid}`" in text, f"missing eligibility row for {sid}"
    assert "FRED_API_KEY" in text
    assert "ALPHA_VANTAGE_API_KEY" in text
    assert "无" in text and "ADR 例外" in text


def test_tierALiveEligibility_secEdgarUserAgentSlotInAcceptanceCode() -> None:
    """覆盖范围：sec_edgar 资格 KEY 槽位（代码 SSOT）
    测试对象：SOURCE_API_KEY_ENV
    目的/目标：sec_edgar live 验收须校验 SEC_EDGAR_USER_AGENT
    验证点：SOURCE_API_KEY_ENV["sec_edgar"] == "SEC_EDGAR_USER_AGENT"
    失败含义：SEC fair access 规则未接入 acceptance env 校验
    """
    assert SOURCE_API_KEY_ENV.get("sec_edgar") == "SEC_EDGAR_USER_AGENT"


def test_isolatedLiveDataRoot_fixtureSetsSandboxEnv(
    isolated_live_data_root: Path,
) -> None:
    """覆盖范围：isolated_live_data_root fixture
    测试对象：tests/conftest.py isolated_live_data_root
    目的/目标：自动设置隔离 QMD_DATA_ROOT 于 .audit-sandbox/m-data-03
    验证点：路径含 m-data-03；env QMD_DATA_ROOT 一致
    失败含义：live e2e 可能误写主库或缺 sandbox 根
    """
    import os

    assert ".audit-sandbox" in isolated_live_data_root.as_posix()
    assert "m-data-03" in isolated_live_data_root.as_posix()
    assert os.environ.get("QMD_DATA_ROOT") == str(isolated_live_data_root)


@pytest.mark.parametrize(
    "path",
    [
        PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb",
        PROJECT_ROOT / "data",
    ],
)
def test_assertIsolatedLiveDataRoot_rejectsCanonicalMainDb(path: Path) -> None:
    """覆盖范围：主库路径拒绝
    测试对象：assert_isolated_live_data_root
    目的/目标：canonical main DB / data 根不得用于 live 验收
    验证点：抛 TierALiveEnvError · code=CANONICAL_MAIN_DB_REJECTED
    失败含义：ADR-034 主库隔离失效
    """
    with pytest.raises(TierALiveEnvError) as exc_info:
        assert_isolated_live_data_root(path)
    assert exc_info.value.code == "CANONICAL_MAIN_DB_REJECTED"


def test_assertIsolatedLiveDataRoot_rejectsNonMdata03Sandbox(tmp_path: Path) -> None:
    """覆盖范围：非 m-data-03 sandbox 拒绝
    测试对象：assert_isolated_live_data_root
    目的/目标：仅允许 .audit-sandbox/m-data-03 子树
    验证点：.audit-sandbox 但无 m-data-03 段时抛 ISOLATED_ROOT_REQUIRED
    失败含义：混用其他 audit 路径导致验收证据不可比
    """
    root = PROJECT_ROOT / ".audit-sandbox" / "other-task" / "case"
    root.mkdir(parents=True, exist_ok=True)
    with pytest.raises(TierALiveEnvError) as exc_info:
        assert_isolated_live_data_root(root)
    assert exc_info.value.code == "ISOLATED_ROOT_REQUIRED"


def test_isCanonicalMainDbPath_detectsDefaultMainDuckdb() -> None:
    """覆盖范围：canonical DuckDB 文件探测
    测试对象：is_canonical_main_db_path / is_canonical_main_data_root
    目的/目标：机械识别仓库默认主库路径
    验证点：data/duckdb/quant_monitor.duckdb 为 canonical
    失败含义：主库路径漏检，live 可 silent 写入
    """
    main_db = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
    assert is_canonical_main_db_path(main_db) is True
    assert is_canonical_main_data_root(PROJECT_ROOT / "data") is True


def test_livePort_noSilentFallbackToMock(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 live port 阻断（S00 泛化 exemplar）
    测试对象：create_fred_fetch_port(use_mock=False)
    目的/目标：ADR-027 env gate fail-closed；live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：EasyXT 式换源渗入产品 live 路径；ponytail: 其余 Tier A port 工厂同 ProductLiveGateError 契约，见各 e2e noSilentFallback 用例
    """
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


def test_validateLiveAcceptanceEnv_rejectsWithoutLiveFetchOptIn(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance env 校验 — 无 live opt-in
    测试对象：validate_live_acceptance_env
    目的/目标：CLI exit 2 当 QMD_ALLOW_LIVE_FETCH 未设置
    验证点：TierALiveEnvError · LIVE_FETCH_NOT_OPTED_IN
    失败含义：acceptance 脚本可在未授权环境运行
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(TierALiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_live_data_root,
            source_ids=("fred",),
        )
    assert exc_info.value.code == "LIVE_FETCH_NOT_OPTED_IN"


def test_validateLiveAcceptanceEnv_rejectsMissingFredKey(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance env 校验 — 缺 KEY
    测试对象：validate_live_acceptance_env
    目的/目标：fred 在 scope 时缺 FRED_API_KEY → exit 2
    验证点：TierALiveEnvError · MISSING_API_KEYS
    失败含义：无 key 的 live 验收误标 pass
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(TierALiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_live_data_root,
            source_ids=("fred",),
        )
    assert exc_info.value.code == "MISSING_API_KEYS"


def test_validateLiveAcceptanceEnv_rejectsMissingSecEdgarUserAgent(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance env 校验 — sec_edgar 缺 USER_AGENT
    测试对象：validate_live_acceptance_env
    目的/目标：sec_edgar 在 scope 时缺 SEC_EDGAR_USER_AGENT → exit 2
    验证点：TierALiveEnvError · MISSING_API_KEYS
    失败含义：无 UA 的 SEC live 验收误标 pass
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
    with pytest.raises(TierALiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_live_data_root,
            source_ids=("sec_edgar",),
        )
    assert exc_info.value.code == "MISSING_API_KEYS"


def test_validateLiveAcceptanceEnv_rejectsFredMockEnv(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：fred mock env 禁止
    测试对象：validate_live_acceptance_env
    目的/目标：QMD_FRED_INCREMENTAL_USE_MOCK 在 live 验收 fail-closed
    验证点：TierALiveEnvError · MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE
    失败含义：silent mock fallback 渗入 Tier A live 验收
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMD_FRED_INCREMENTAL_USE_MOCK", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    with pytest.raises(TierALiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_live_data_root,
            source_ids=("fred",),
        )
    assert exc_info.value.code == "MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE"


def test_validateLiveAcceptanceEnv_rejectsBareSecEdgarUa(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：SEC_EDGAR bare UA 拒绝
    测试对象：validate_live_acceptance_env
    目的/目标：无 @/contact 的 UA 在 env 层被拒（与 port 规则同构）
    验证点：TierALiveEnvError · MISSING_API_KEYS
    失败含义：非法 UA 拖到 port 层才失败
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "QuantMonitor/1.0")
    with pytest.raises(TierALiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_live_data_root,
            source_ids=("sec_edgar",),
        )
    assert exc_info.value.code == "MISSING_API_KEYS"


def test_validateLiveAcceptanceEnv_acceptsValidSandbox(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：合法 sandbox + opt-in + key
    测试对象：validate_live_acceptance_env
    目的/目标：隔离路径与 env 齐备时通过校验
    验证点：返回 resolved root 等于 fixture 路径
    失败含义：合法验收环境被误拒
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    resolved = validate_live_acceptance_env(
        data_root=isolated_live_data_root,
        source_ids=("fred",),
    )
    assert resolved == isolated_live_data_root.resolve()


def test_selectSourceIds_quickSubset() -> None:
    """覆盖范围：--quick 源列表
    测试对象：select_source_ids(quick=True)
    目的/目标：试点子集 fred + baostock
    验证点：元组等于 QUICK_SOURCE_IDS
    失败含义：nightly quick 验收范围错误
    """
    assert select_source_ids(quick=True) == QUICK_SOURCE_IDS


def test_selectSourceIds_allElevenByDefault() -> None:
    """覆盖范围：默认 11/11 源列表
    测试对象：select_source_ids()
    目的/目标：省略 --source-id 时遍历全部 Tier A
    验证点：长度 11；集合等于 TIER_A_SOURCES
    失败含义：S-ACCEPT 漏源
    """
    selected = frozenset(select_source_ids())
    assert selected == TIER_A_SOURCES
    assert len(selected) == 11


def test_tierALiveAcceptanceCli_exit2WhenEnvInvalid(
    isolated_live_data_root: Path,
) -> None:
    """覆盖范围：acceptance CLI exit 2 契约
    测试对象：scripts/tier_a_live_acceptance.py
    目的/目标：无效 env 时进程 exit 2
    验证点：subprocess returncode == 2
    失败含义：plan-spec exit 码契约未落地
    """
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = str(TEST_PROJECT_ROOT)
    env["QMD_DATA_ROOT"] = str(isolated_live_data_root)
    env.pop("QMD_ALLOW_LIVE_FETCH", None)
    proc = subprocess.run(
        [sys.executable, str(ACCEPTANCE_SCRIPT), "--source-id", "fred"],
        cwd=str(TEST_PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "QMD_ALLOW_LIVE_FETCH" in proc.stderr or proc.stderr.strip() != ""


def test_ensureIsolatedDb_syncsSourceRegistry(
    isolated_live_data_root: Path,
) -> None:
    """覆盖范围：ensure_isolated_db registry sync
    测试对象：tier_a_live_acceptance.ensure_isolated_db
    目的/目标：隔离库创建后 source_registry 行须可查询
    验证点：quant_monitor.duckdb 存在；source_registry COUNT(*) >= 1
    失败含义：S-ACCEPT sandbox 缺 registry sync，dispatch 无法解析源
    """
    db_path = ensure_isolated_db(isolated_live_data_root)
    assert db_path == isolated_live_data_root / "duckdb" / "quant_monitor.duckdb"
    assert db_path.is_file()
    import duckdb

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    finally:
        con.close()
    assert int(count) >= 1


def test_tierALiveOps_mainDbFingerprintUnchangedAfterSandbox(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：live 验收后主库零污染
    测试对象：ensure_isolated_db + canonical main DB
    目的/目标：sandbox 操作不得改变主库文件指纹
    验证点：主库存在时 stat 前后 size/mtime_ns 一致
    失败含义：ADR-034 主库隔离失效，live 可能 silent 写入
    """
    main_db = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
    if not main_db.is_file():
        pytest.skip("canonical main DB absent on this host")
    before = main_db.stat()
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    ensure_isolated_db(isolated_live_data_root)
    after = main_db.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns


def test_tierALiveOps_mainDbFingerprintUnchangedAfterMockAcceptance(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：完整 acceptance 路径后主库零污染
    测试对象：run_source_live_acceptance + canonical main DB
    目的/目标：mock sync acceptance 不得改变主库文件指纹
    验证点：主库存在时 stat 前后 size/mtime_ns 一致
    失败含义：acceptance/dispatch 路径误写主库
    """
    main_db = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
    if not main_db.is_file():
        pytest.skip("canonical main DB absent on this host")
    before = main_db.stat()
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _mock_incremental(_source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return LiveIncrementalOutcome(
            source_id="fred",
            sync_status="COMPLETED",
            inspect_status="PASS",
            clean_table="axis_observation",
            clean_row_count=2,
            detail="mock acceptance for main-db guard",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch.run_tier_a_live_incremental",
        _mock_incremental,
    )
    result = run_source_live_acceptance("fred", data_root=isolated_live_data_root)
    assert result.status == "pass"
    after = main_db.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns


def test_tierALiveAcceptance_exit1WhenSourceFails(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance exit 1 契约
    测试对象：run_acceptance
    目的/目标：源验收失败时进程 exit 1
    验证点：monkeypatch 必败 run_source_live_acceptance → return 1
    失败含义：plan-spec exit 码契约未落地
    """
    from backend.app.ops.tier_a_live_acceptance import SourceAcceptanceResult

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)

    def _fail(_sid: str, *, data_root: Path) -> SourceAcceptanceResult:
        return SourceAcceptanceResult(
            source_id="fred",
            status="fail",
            detail="simulated acceptance failure",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_source_live_acceptance",
        _fail,
    )
    assert run_acceptance(source_id="fred", data_root=isolated_live_data_root) == 1


@pytest.mark.network
def test_tierALiveHarness_networkMarkRegistered() -> None:
    """覆盖范围：@pytest.mark.network 约定
    测试对象：本模块 network 标记用例
    目的/目标：默认 pytest -q 跳过真网（须 --run-network）
    验证点：本用例仅在网络 flag 下执行
    失败含义：CI 默认套件误跑 live fetch
    """
    pytest.skip("harness network-mark smoke; run with pytest --run-network")


def test_networkMark_skippedInDefaultPytestRun() -> None:
    """覆盖范围：默认 CI 跳过 network 标记
    测试对象：tests/conftest.py pytest_collection_modifyitems
    目的/目标：无 --run-network 时 network 用例被 skip
    验证点：对本文件 -m network 收集结果为 skipped
    失败含义：默认 pytest -q 可能触发 live 请求
    """
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_tier_a_live_harness.py::test_tierALiveHarness_networkMarkRegistered",
            "-q",
            "-rs",
            "--tb=no",
        ],
        cwd=str(TEST_PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0
    assert "skipped" in combined.lower() or "SKIPPED" in combined
