"""Tier B live acceptance harness tests (M-DATA-03 AC-7 · validation_fetch)."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.live_tier_router import TIER_B_SOURCES
from backend.app.ops.tier_b_live_acceptance import (
    QUICK_SOURCE_IDS,
    SOURCE_API_KEY_ENV,
    TierBLiveEnvError,
    assert_isolated_live_data_root,
    run_acceptance,
    run_source_live_acceptance,
    select_source_ids,
    validate_live_acceptance_env,
)
from backend.app.ops.tier_b_live_validation_dispatch import (
    LiveValidationOutcome,
    run_tier_b_live_validation,
)
from tests.contract_gate_support import PROJECT_ROOT as TEST_PROJECT_ROOT

ACCEPTANCE_SCRIPT = PROJECT_ROOT / "scripts" / "tier_b_live_acceptance.py"


@pytest.fixture
def isolated_tier_b_data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated Tier B sandbox under .audit-sandbox/m-data-03/tier-b."""
    root = (
        PROJECT_ROOT
        / ".audit-sandbox"
        / "m-data-03"
        / "tier-b"
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
    目的/目标：canonical main DB / data 根不得用于 Tier B live 验收
    验证点：抛 TierBLiveEnvError · code=CANONICAL_MAIN_DB_REJECTED
    失败含义：ADR-034 主库隔离失效
    """
    with pytest.raises(TierBLiveEnvError) as exc_info:
        assert_isolated_live_data_root(path)
    assert exc_info.value.code == "CANONICAL_MAIN_DB_REJECTED"


def test_assertIsolatedLiveDataRoot_rejectsNonTierBSandbox(tmp_path: Path) -> None:
    """覆盖范围：非 tier-b sandbox 拒绝
    测试对象：assert_isolated_live_data_root
    目的/目标：仅允许 .audit-sandbox/m-data-03/tier-b 子树
    验证点：m-data-03 但无 tier-b 段时抛 ISOLATED_ROOT_REQUIRED
    失败含义：混用 Tier A sandbox 导致验收证据不可比
    """
    root = PROJECT_ROOT / ".audit-sandbox" / "m-data-03" / "pytest-only-tier-a"
    root.mkdir(parents=True, exist_ok=True)
    with pytest.raises(TierBLiveEnvError) as exc_info:
        assert_isolated_live_data_root(root)
    assert exc_info.value.code == "ISOLATED_ROOT_REQUIRED"


def test_validateLiveAcceptanceEnv_rejectsWithoutLiveFetchOptIn(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance env 校验 — 无 live opt-in
    测试对象：validate_live_acceptance_env
    目的/目标：CLI exit 2 当 QMD_ALLOW_LIVE_FETCH 未设置
    验证点：TierBLiveEnvError · LIVE_FETCH_NOT_OPTED_IN
    失败含义：acceptance 脚本可在未授权环境运行
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(TierBLiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_tier_b_data_root,
            source_ids=("yahoo_finance",),
        )
    assert exc_info.value.code == "LIVE_FETCH_NOT_OPTED_IN"


def test_validateLiveAcceptanceEnv_rejectsMissingThsIfindLicense(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance env 校验 — ths_ifind 缺 license
    测试对象：validate_live_acceptance_env
    目的/目标：ths_ifind 在 scope 时缺 THS_IFIND_LICENSE_ARTIFACT → exit 2
    验证点：TierBLiveEnvError · MISSING_API_KEYS
    失败含义：无 license 的 live 验收误标 pass
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.delenv("THS_IFIND_LICENSE_ARTIFACT", raising=False)
    with pytest.raises(TierBLiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_tier_b_data_root,
            source_ids=("ths_ifind",),
        )
    assert exc_info.value.code == "MISSING_API_KEYS"


def test_validateLiveAcceptanceEnv_acceptsValidSandbox(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：合法 tier-b sandbox + opt-in
    测试对象：validate_live_acceptance_env
    目的/目标：隔离路径与 env 齐备时通过校验
    验证点：返回 resolved root 等于 fixture 路径
    失败含义：合法验收环境被误拒
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    resolved = validate_live_acceptance_env(
        data_root=isolated_tier_b_data_root,
        source_ids=("yahoo_finance",),
    )
    assert resolved == isolated_tier_b_data_root.resolve()


def test_selectSourceIds_quickSubset() -> None:
    """覆盖范围：--quick 源列表
    测试对象：select_source_ids(quick=True)
    目的/目标：试点子集 yahoo_finance + akshare
    验证点：元组等于 QUICK_SOURCE_IDS
    失败含义：nightly quick 验收范围错误
    """
    assert select_source_ids(quick=True) == QUICK_SOURCE_IDS


def test_selectSourceIds_allTenByDefault() -> None:
    """覆盖范围：默认 10/10 源列表
    测试对象：select_source_ids()
    目的/目标：省略 --source-id 时遍历全部 Tier B
    验证点：长度 10；集合等于 TIER_B_SOURCES
    失败含义：AC-7 漏源
    """
    selected = frozenset(select_source_ids())
    assert selected == TIER_B_SOURCES
    assert len(selected) == 10


def test_tierBLiveAcceptanceCli_exit2WhenEnvInvalid(
    isolated_tier_b_data_root: Path,
) -> None:
    """覆盖范围：acceptance CLI exit 2 契约
    测试对象：scripts/tier_b_live_acceptance.py
    目的/目标：无效 env 时进程 exit 2
    验证点：subprocess returncode == 2
    失败含义：plan-spec exit 码契约未落地
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(TEST_PROJECT_ROOT)
    env["QMD_DATA_ROOT"] = str(isolated_tier_b_data_root)
    env.pop("QMD_ALLOW_LIVE_FETCH", None)
    proc = subprocess.run(
        [sys.executable, str(ACCEPTANCE_SCRIPT), "--source-id", "yahoo_finance"],
        cwd=str(TEST_PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "QMD_ALLOW_LIVE_FETCH" in proc.stderr or proc.stderr.strip() != ""


def test_tierBLiveAcceptance_exit1WhenSourceFails(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：acceptance exit 1 契约
    测试对象：run_acceptance
    目的/目标：源验收失败时进程 exit 1
    验证点：monkeypatch 必败 run_source_live_acceptance → return 1
    失败含义：plan-spec exit 码契约未落地
    """
    from backend.app.ops.tier_b_live_acceptance import SourceAcceptanceResult

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _fail(_sid: str, *, data_root: Path) -> SourceAcceptanceResult:
        return SourceAcceptanceResult(
            source_id="yahoo_finance",
            status="fail",
            detail="simulated acceptance failure",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance.run_source_live_acceptance",
        _fail,
    )
    assert run_acceptance(source_id="yahoo_finance", data_root=isolated_tier_b_data_root) == 1


def test_tierBLiveOps_mainDbFingerprintUnchangedAfterMockAcceptance(
    isolated_tier_b_data_root: Path,
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
            source_id="yahoo_finance",
            fetch_status="SUCCESS",
            row_count=2,
            detail="mock validation for main-db guard",
            inspect_status="NOT_APPLICABLE",
            clean_table="security_bar_1d",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_validation_dispatch.run_tier_b_live_validation",
        _mock_validation,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance._run_f0_data_health",
        lambda *_a, **_k: ("NOT_APPLICABLE", "f0 skipped for mock"),
    )
    result = run_source_live_acceptance("yahoo_finance", data_root=isolated_tier_b_data_root)
    assert result.status == "pass"
    after = main_db.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns


def test_sourceApiKeyEnv_thsIfindSlotInAcceptanceCode() -> None:
    """覆盖范围：ths_ifind 资格 KEY 槽位（代码 SSOT）
    测试对象：SOURCE_API_KEY_ENV
    目的/目标：ths_ifind live 验收须校验 THS_IFIND_LICENSE_ARTIFACT
    验证点：SOURCE_API_KEY_ENV["ths_ifind"] == "THS_IFIND_LICENSE_ARTIFACT"
    失败含义：iFinD license 规则未接入 acceptance env 校验
    """
    assert SOURCE_API_KEY_ENV.get("ths_ifind") == "THS_IFIND_LICENSE_ARTIFACT"


def test_validateLiveAcceptanceEnv_rejectsFredMockEnv(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：fred mock env 禁止（Tier B 同构）
    测试对象：validate_live_acceptance_env
    目的/目标：QMD_FRED_INCREMENTAL_USE_MOCK 在 live 验收 fail-closed
    验证点：TierBLiveEnvError · MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE
    失败含义：silent mock fallback 渗入 Tier B live 验收
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMD_FRED_INCREMENTAL_USE_MOCK", "1")
    with pytest.raises(TierBLiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_tier_b_data_root,
            source_ids=("yahoo_finance",),
        )
    assert exc_info.value.code == "MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE"


def test_validateLiveAcceptanceEnv_rejectsMissingQmtXtdataAuth(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：qmt_xtdata 缺授权 env
    测试对象：validate_live_acceptance_env
    目的/目标：qmt_xtdata 在 scope 时缺 QMT_XTDATA_AUTHORIZED → exit 2
    验证点：TierBLiveEnvError · MISSING_API_KEYS
    失败含义：无授权的 QMT live 验收误标 pass
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.delenv("QMT_XTDATA_AUTHORIZED", raising=False)
    with pytest.raises(TierBLiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_tier_b_data_root,
            source_ids=("qmt_xtdata",),
        )
    assert exc_info.value.code == "MISSING_API_KEYS"


def test_validateLiveAcceptanceEnv_rejectsMissingQmtXqshareRemote(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：qmt_xqshare 缺远程连接 env
    测试对象：validate_live_acceptance_env
    目的/目标：qmt_xqshare 须 QMT_XQSHARE_AUTHORIZED + XQSHARE_REMOTE_HOST/PORT
    验证点：TierBLiveEnvError · MISSING_API_KEYS
    失败含义：xqshare 无远程配置仍跑 live 验收
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("QMT_XQSHARE_AUTHORIZED", "1")
    monkeypatch.delenv("XQSHARE_REMOTE_HOST", raising=False)
    monkeypatch.delenv("XQSHARE_REMOTE_PORT", raising=False)
    with pytest.raises(TierBLiveEnvError) as exc_info:
        validate_live_acceptance_env(
            data_root=isolated_tier_b_data_root,
            source_ids=("qmt_xqshare",),
        )
    assert exc_info.value.code == "MISSING_API_KEYS"
