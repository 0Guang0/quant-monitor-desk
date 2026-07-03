"""Tier C live acceptance harness tests (M-DATA-03 AC-7 · validation_fetch)."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.live_tier_router import TIER_C_SOURCES
from backend.app.ops.tier_c_live_acceptance import (
    QUICK_SOURCE_IDS,
    SOURCE_API_KEY_ENV,
    TierCLiveEnvError,
    assert_isolated_live_data_root,
    run_acceptance,
    run_source_live_acceptance,
    select_source_ids,
    validate_live_acceptance_env,
)
from backend.app.ops.tier_c_live_validation_dispatch import (
    LiveValidationOutcome,
    run_tier_c_live_validation,
)
from tests.contract_gate_support import PROJECT_ROOT as TEST_PROJECT_ROOT

ACCEPTANCE_SCRIPT = PROJECT_ROOT / "scripts" / "tier_c_live_acceptance.py"


@pytest.fixture
def isolated_tier_c_data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated Tier C sandbox under .audit-sandbox/m-data-03/tier-c."""
    root = (
        PROJECT_ROOT
        / ".audit-sandbox"
        / "m-data-03"
        / "tier-c"
        / f"pytest-{tmp_path.name}-{uuid.uuid4().hex[:8]}"
    )
    root.mkdir(parents=True, exist_ok=True)
    resolved = assert_isolated_live_data_root(root)
    monkeypatch.setenv("QMD_DATA_ROOT", str(resolved))
    monkeypatch.delenv("DATA_ROOT", raising=False)
    return resolved


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
    目的/目标：canonical main DB / data 根不得用于 Tier C live 验收
    验证点：抛 TierCLiveEnvError · code=CANONICAL_MAIN_DB_REJECTED
    失败含义：ADR-034 主库隔离失效
    """
    with pytest.raises(TierCLiveEnvError) as exc_info:
        assert_isolated_live_data_root(path)
    assert exc_info.value.code == "CANONICAL_MAIN_DB_REJECTED"


def test_assertIsolatedLiveDataRoot_rejectsNonTierCSandbox(tmp_path: Path) -> None:
    """覆盖范围：非 tier-c sandbox 拒绝
    测试对象：assert_isolated_live_data_root
    目的/目标：仅允许 .audit-sandbox/m-data-03/tier-c 子树
    验证点：m-data-03 但无 tier-c 段时抛 ISOLATED_ROOT_REQUIRED
    失败含义：混用 Tier A sandbox 导致验收证据不可比
    """
    root = PROJECT_ROOT / ".audit-sandbox" / "m-data-03" / "pytest-only-tier-a"
    root.mkdir(parents=True, exist_ok=True)
    with pytest.raises(TierCLiveEnvError) as exc_info:
        assert_isolated_live_data_root(root)
    assert exc_info.value.code == "ISOLATED_ROOT_REQUIRED"


def test_validateLiveAcceptanceEnv_rejectsWithoutLiveFetchOptIn(
    isolated_tier_c_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance env 校验 — 无 live opt-in
    测试对象：validate_live_acceptance_env
    目的/目标：CLI exit 2 当 QMD_ALLOW_LIVE_FETCH 未设置
    验证点：TierCLiveEnvError · LIVE_FETCH_NOT_OPTED_IN
    失败含义：acceptance 脚本可在未授权环境运行
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(TierCLiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_tier_c_data_root,
            source_ids=("kalshi",),
        )
    assert exc_info.value.code == "LIVE_FETCH_NOT_OPTED_IN"


def test_sourceApiKeyEnv_emptyForTierC() -> None:
    """覆盖范围：Tier C 无强制 API KEY 槽位（除 QMD_ALLOW_LIVE_FETCH）
    测试对象：SOURCE_API_KEY_ENV
    目的/目标：kalshi/polymarket/web_search 验收不在 env 层硬依赖密钥
    验证点：SOURCE_API_KEY_ENV 为空 dict
    失败含义：Tier C 误继承 Tier B gated 源 env 规则
    """
    assert SOURCE_API_KEY_ENV == {}


def test_validateLiveAcceptanceEnv_acceptsValidSandbox(
    isolated_tier_c_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：合法 tier-c sandbox + opt-in
    测试对象：validate_live_acceptance_env
    目的/目标：隔离路径与 env 齐备时通过校验
    验证点：返回 resolved root 等于 fixture 路径
    失败含义：合法验收环境被误拒
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    resolved = validate_live_acceptance_env(
        data_root=isolated_tier_c_data_root,
        source_ids=("kalshi",),
    )
    assert resolved == isolated_tier_c_data_root.resolve()


def test_validateLiveAcceptanceEnv_rejectsFredMockEnv(
    isolated_tier_c_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：fred mock env 禁止（Tier C 同构）
    测试对象：validate_live_acceptance_env
    目的/目标：QMD_FRED_INCREMENTAL_USE_MOCK 在 live 验收 fail-closed
    验证点：TierCLiveEnvError · MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE
    失败含义：silent mock fallback 渗入 Tier C live 验收
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMD_FRED_INCREMENTAL_USE_MOCK", "1")
    with pytest.raises(TierCLiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_tier_c_data_root,
            source_ids=("kalshi",),
        )
    assert exc_info.value.code == "MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE"


def test_validateLiveAcceptanceEnv_rejectsUnknownTierCSource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：未知 source_id 拒绝
    测试对象：select_source_ids
    目的/目标：非 Tier C 源不得进入验收
    验证点：TierCLiveEnvError 含 unknown Tier C source_id
    失败含义：验收范围泄漏到非 Tier C 源
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    with pytest.raises(TierCLiveEnvError):
        select_source_ids(source_id="fred")


def test_selectSourceIds_quickSubset() -> None:
    """覆盖范围：--quick 源列表
    测试对象：select_source_ids(quick=True)
    目的/目标：试点子集 kalshi + polymarket
    验证点：元组等于 QUICK_SOURCE_IDS
    失败含义：nightly quick 验收范围错误
    """
    assert select_source_ids(quick=True) == QUICK_SOURCE_IDS


def test_selectSourceIds_allThreeByDefault() -> None:
    """覆盖范围：默认 3/3 源列表
    测试对象：select_source_ids()
    目的/目标：省略 --source-id 时遍历全部 Tier C
    验证点：长度 3；集合等于 TIER_C_SOURCES
    失败含义：AC-7 漏源
    """
    selected = frozenset(select_source_ids())
    assert selected == TIER_C_SOURCES
    assert len(selected) == 3


def test_tierCLiveAcceptanceCli_exit2WhenEnvInvalid(
    isolated_tier_c_data_root: Path,
) -> None:
    """覆盖范围：acceptance CLI exit 2 契约
    测试对象：scripts/tier_c_live_acceptance.py
    目的/目标：无效 env 时进程 exit 2
    验证点：subprocess returncode == 2
    失败含义：plan-spec exit 码契约未落地
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(TEST_PROJECT_ROOT)
    env["QMD_DATA_ROOT"] = str(isolated_tier_c_data_root)
    env.pop("QMD_ALLOW_LIVE_FETCH", None)
    proc = subprocess.run(
        [sys.executable, str(ACCEPTANCE_SCRIPT), "--source-id", "kalshi"],
        cwd=str(TEST_PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "QMD_ALLOW_LIVE_FETCH" in proc.stderr or proc.stderr.strip() != ""


def test_tierCLiveAcceptance_exit1WhenSourceFails(
    isolated_tier_c_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance exit 1 契约
    测试对象：run_acceptance
    目的/目标：源验收失败时进程 exit 1
    验证点：monkeypatch 必败 run_source_live_acceptance → return 1
    失败含义：plan-spec exit 码契约未落地
    """
    from backend.app.ops.tier_c_live_acceptance import SourceAcceptanceResult

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _fail(_sid: str, *, data_root: Path) -> SourceAcceptanceResult:
        return SourceAcceptanceResult(
            source_id="kalshi",
            status="fail",
            detail="simulated acceptance failure",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_c_live_acceptance.run_source_live_acceptance",
        _fail,
    )
    assert run_acceptance(source_id="kalshi", data_root=isolated_tier_c_data_root) == 1


def test_tierCLiveOps_mainDbFingerprintUnchangedAfterMockAcceptance(
    isolated_tier_c_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：mock validation acceptance 后主库零污染
    测试对象：run_source_live_acceptance + canonical main DB
    目的/目标：mock dispatch acceptance 不得改变主库文件指纹
    验证点：主库存在时 stat 前后 size/mtime_ns 一致
    失败含义：validation dispatch 路径误写主库
    """
    main_db = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
    if not main_db.is_file():
        pytest.skip("canonical main DB absent on this host")
    before = main_db.stat()
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _mock_validation(_source_id: str, _data_root: Path) -> LiveValidationOutcome:
        return LiveValidationOutcome(
            source_id="kalshi",
            fetch_status="SUCCESS",
            row_count=2,
            detail="mock validation for main-db guard",
            inspect_status="NOT_APPLICABLE",
            clean_table="not_applicable",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_c_live_validation_dispatch.run_tier_c_live_validation",
        _mock_validation,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_c_live_acceptance._run_f0_data_health",
        lambda *_a, **_k: ("NOT_APPLICABLE", "f0 skipped for mock"),
    )
    result = run_source_live_acceptance("kalshi", data_root=isolated_tier_c_data_root)
    assert result.status == "pass"
    after = main_db.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns
