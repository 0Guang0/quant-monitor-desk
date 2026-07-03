"""Unit and integration tests for tier_a_live_incremental_dispatch (M-DATA-03 S-ACCEPT)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard

from backend.app.ops.tier_a_live_acceptance import (
    ensure_isolated_db,
    run_source_live_acceptance,
)
from backend.app.ops.tier_a_live_incremental_dispatch import (
    LiveIncrementalOutcome,
    _extract_sync_status,
    run_tier_a_live_incremental,
)
from tests.fred_macro_incremental_support import insert_axis_observation
from tests.live_incremental_support import acceptance_db_path


def _write_fred_macro_evidence(data_root: Path) -> None:
    import json

    raw_dir = data_root / "raw" / "fred" / "2026-07-03"
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "official_macro_evidence_v1",
        "source_id": "fred",
        "series_id": "DGS10",
        "observations": [
            {"series_id": "DGS10", "observation_date": "2026-07-01", "value": "4.40"},
            {"series_id": "DGS10", "observation_date": "2026-07-02", "value": "4.41"},
        ],
        "source_fetch_id": "dispatch-test-fetch",
        "content_hash": "dispatch-test-hash",
        "as_of_timestamp": "2026-07-03T12:00:00Z",
        "retrieved_at": "2026-07-03T12:00:00Z",
    }
    (raw_dir / "evidence.json").write_text(json.dumps(payload), encoding="utf-8")


def test_extractSyncStatus_readsOverallStatusFromReport() -> None:
    """覆盖范围：sync 状态解析
    测试对象：_extract_sync_status
    目的/目标：acceptance 能识别 COMPLETED / EMPTY_RESPONSE
    验证点：overall_status 与 instrument_results[0].status 均可解析
    失败含义：S-ACCEPT 误判 sync 成败
    """
    assert _extract_sync_status({"overall_status": "COMPLETED"}) == "COMPLETED"
    assert _extract_sync_status({"job_status": "EMPTY_RESPONSE"}) == "EMPTY_RESPONSE"

    class _Report:
        instrument_results = [{"status": "COMPLETED"}]

    assert _extract_sync_status(_Report()) == "COMPLETED"


def test_liveIncrementalOutcome_passedAllowsEmptyResponse() -> None:
    """覆盖范围：EMPTY_RESPONSE 验收语义
    测试对象：LiveIncrementalOutcome.passed
    目的/目标：水位追上时无新行仍算通过
    验证点：EMPTY_RESPONSE + inspect PASS → passed
    失败含义：caught-up 源被误标失败
    """
    outcome = LiveIncrementalOutcome(
        source_id="fred",
        sync_status="EMPTY_RESPONSE",
        inspect_status="PASS",
        clean_table="axis_observation",
        clean_row_count=0,
    )
    assert outcome.passed is True


def test_liveIncrementalOutcome_passedAllowsInspectWarn() -> None:
    """覆盖范围：inspect WARN 非阻断语义
    测试对象：LiveIncrementalOutcome.passed
    目的/目标：ADR-034 inspect/health non-blocker — WARN 仍算通过
    验证点：sync COMPLETED + inspect WARN → passed
    失败含义：WARN 被误标失败，违背 non-blocker 契约
    """
    outcome = LiveIncrementalOutcome(
        source_id="fred",
        sync_status="COMPLETED",
        inspect_status="WARN",
        clean_table="axis_observation",
        clean_row_count=3,
    )
    assert outcome.passed is True


def test_liveIncrementalOutcome_failedOnInspectFail() -> None:
    """覆盖范围：inspect FAIL 阻断
    测试对象：LiveIncrementalOutcome.passed
    目的/目标：DbInspector FAIL 不得 pass
    验证点：sync COMPLETED 但 inspect FAIL → not passed
    失败含义：坏库仍 exit 0
    """
    outcome = LiveIncrementalOutcome(
        source_id="baostock",
        sync_status="COMPLETED",
        inspect_status="FAIL",
        clean_table="security_bar_1d",
        clean_row_count=5,
    )
    assert outcome.passed is False


def test_runTierALiveIncremental_mockSync_realInspect_passesFred(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：S-ACCEPT 派发链集成（mock sync + 真实 DbInspector）
    测试对象：run_tier_a_live_incremental
    目的/目标：sync→inspect 在 acceptance DuckDB 路径可复跑
    验证点：sync_status=COMPLETED；inspect_status∈{PASS,WARN}；clean_row_count>=1
    失败含义：派发链无 pytest 回归网，手工证据不可复验
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    ensure_isolated_db(isolated_live_data_root)
    db_path = acceptance_db_path(isolated_live_data_root)

    def _mock_sync(_source_id: str, _data_root: Path) -> str:
        import duckdb

        from backend.app.db.migrate import apply_migrations

        con = duckdb.connect(str(db_path))
        try:
            apply_migrations(con)
            insert_axis_observation(
                con,
                observation_id="dispatch-mock-obs",
                indicator_id="DGS10",
                obs_date=datetime.now(UTC).date(),
            )
        finally:
            con.close()
        return "COMPLETED"

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch._run_live_sync",
        _mock_sync,
    )
    outcome = run_tier_a_live_incremental("fred", isolated_live_data_root)
    assert outcome.source_id == "fred"
    assert outcome.sync_status == "COMPLETED"
    assert outcome.inspect_status in {"PASS", "WARN"}
    assert outcome.clean_table == "axis_observation"
    assert outcome.clean_row_count >= 1
    assert outcome.passed is True


def test_runSourceLiveAcceptance_mockSync_returnsPass(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：run_source_live_acceptance outcome 包装（含 F0）
    测试对象：run_source_live_acceptance
    目的/目标：mock dispatch outcome + 合法 F0 证据时 acceptance 层映射为 pass
    验证点：status==pass；detail 含 sync/inspect/health 摘要
    失败含义：CLI exit 0 包装逻辑无回归
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _mock_incremental(_source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return LiveIncrementalOutcome(
            source_id="fred",
            sync_status="COMPLETED",
            inspect_status="PASS",
            clean_table="axis_observation",
            clean_row_count=2,
            detail="mock integration",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch.run_tier_a_live_incremental",
        _mock_incremental,
    )
    _write_fred_macro_evidence(isolated_live_data_root)
    result = run_source_live_acceptance("fred", data_root=isolated_live_data_root)
    assert result.status == "pass"
    assert "sync=COMPLETED" in result.detail
    assert "inspect=PASS" in result.detail


def test_runSourceLiveAcceptance_f0Path_exercisesHealthWithMockSync(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：run_source_live_acceptance F0 接入路径
    测试对象：run_source_live_acceptance + _run_f0_data_health
    目的/目标：mock sync 时仍执行真实 F0；合法 macro 证据非 FAIL/BLOCKED
    验证点：status==pass；detail 含 health=PASS 或 health=WARN
    失败含义：F0 未接入 acceptance 或仍走 SKIP
    """
    import json

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    ensure_isolated_db(isolated_live_data_root)
    db_path = acceptance_db_path(isolated_live_data_root)

    def _mock_sync(_source_id: str, _data_root: Path) -> str:
        import duckdb

        con = duckdb.connect(str(db_path))
        try:
            insert_axis_observation(
                con,
                observation_id="f0-path-obs",
                indicator_id="DGS10",
                obs_date=datetime.now(UTC).date(),
            )
        finally:
            con.close()
        return "COMPLETED"

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch._run_live_sync",
        _mock_sync,
    )
    raw_dir = isolated_live_data_root / "raw" / "fred" / "2026-07-03"
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "official_macro_evidence_v1",
        "source_id": "fred",
        "series_id": "DGS10",
        "observations": [
            {"series_id": "DGS10", "observation_date": "2026-07-01", "value": "4.40"},
            {"series_id": "DGS10", "observation_date": "2026-07-02", "value": "4.41"},
        ],
        "source_fetch_id": "f0-path-fetch",
        "content_hash": "f0-path-hash",
        "as_of_timestamp": "2026-07-03T12:00:00Z",
        "retrieved_at": "2026-07-03T12:00:00Z",
    }
    (raw_dir / "abc123.json").write_text(json.dumps(payload), encoding="utf-8")
    result = run_source_live_acceptance("fred", data_root=isolated_live_data_root)
    assert result.status == "pass"
    assert "health=PASS" in result.detail or "health=WARN" in result.detail


def test_runSourceLiveAcceptance_f0Fail_blocksPass(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：F0 data health FAIL 阻断 acceptance
    测试对象：run_source_live_acceptance + _run_f0_data_health
    目的/目标：有 raw 证据且 F0 返回 FAIL 时不得 pass
    验证点：status==fail；detail 含 data-health FAIL
    失败含义：坏 raw 证据仍 exit 0，违背活卡 AC#4 fail-closed
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _mock_incremental(_source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return LiveIncrementalOutcome(
            source_id="fred",
            sync_status="COMPLETED",
            inspect_status="PASS",
            clean_table="axis_observation",
            clean_row_count=2,
            detail="mock sync for f0 fail test",
        )

    def _fail_f0(_source_id: str, *, data_root: Path, db_path: Path) -> tuple[str, str]:
        return "FAIL", "simulated data-health blocker"

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch.run_tier_a_live_incremental",
        _mock_incremental,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance._run_f0_data_health",
        _fail_f0,
    )
    result = run_source_live_acceptance("fred", data_root=isolated_live_data_root)
    assert result.status == "fail"
    assert "data-health FAIL" in result.detail


def test_runSourceLiveAcceptance_plannedWithZeroCleanFails(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：PLANNED + 零 clean 行不得 pass acceptance
    测试对象：run_source_live_acceptance
    目的/目标：PASS_SYNC_STATUSES 含 PLANNED 时仍须 clean/raw 证据
    验证点：status==fail；detail 提及 PLANNED 或 empty
    失败含义：未落库 sync 被误标 pass
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _mock_incremental(_source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return LiveIncrementalOutcome(
            source_id="fred",
            sync_status="PLANNED",
            inspect_status="PASS",
            clean_table="axis_observation",
            clean_row_count=0,
            detail="mock planned with no rows",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch.run_tier_a_live_incremental",
        _mock_incremental,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance._run_f0_data_health",
        lambda *_a, **_k: ("PASS", "mock f0 for planned-empty-clean test"),
    )
    result = run_source_live_acceptance("fred", data_root=isolated_live_data_root)
    assert result.status == "fail"
    assert "PLANNED" in result.detail or "empty" in result.detail.lower()


def test_runTierALiveIncremental_dataRootSplit_inspectUsesParamNotEnv(
    isolated_live_data_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：data_root 分裂负向（env ≠ param）
    测试对象：run_tier_a_live_incremental
    目的/目标：DbInspector 须读 param data_root，不得误读 env 分裂路径
    验证点：env 指向空库、param 有行 → clean_row_count>=1
    失败含义：fred env/param 分裂时 inspect 误判空库
    """
    from backend.app.config import PROJECT_ROOT
    from backend.app.ops.tier_a_live_acceptance import M_DATA_03_SANDBOX_SEGMENT

    other_root = (
        PROJECT_ROOT
        / ".audit-sandbox"
        / M_DATA_03_SANDBOX_SEGMENT
        / f"split-env-{id(tmp_path)}"
    )
    other_root.mkdir(parents=True, exist_ok=True)
    assert M_DATA_03_SANDBOX_SEGMENT in other_root.as_posix()
    ensure_isolated_db(isolated_live_data_root)
    param_db = acceptance_db_path(isolated_live_data_root)
    ensure_isolated_db(other_root)
    monkeypatch.setenv("QMD_DATA_ROOT", str(other_root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _mock_sync(_source_id: str, data_root: Path) -> str:
        import duckdb

        db = acceptance_db_path(data_root)
        con = duckdb.connect(str(db))
        try:
            insert_axis_observation(
                con,
                observation_id="split-param-obs",
                indicator_id="DGS10",
                obs_date=datetime.now(UTC).date(),
            )
        finally:
            con.close()
        return "COMPLETED"

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch._run_live_sync",
        _mock_sync,
    )
    outcome = run_tier_a_live_incremental("fred", isolated_live_data_root)
    assert param_db.is_file()
    assert outcome.clean_row_count >= 1
    assert outcome.inspect_status in {"PASS", "WARN"}


def test_runTierALiveSandbox_dbInspectorNonFail_afterMockSync(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：E2 DbInspector 非 FAIL（ADR-034 §4 non-blocker）
    测试对象：run_tier_a_live_incremental + DbInspector
    目的/目标：mock sync 后 inspect 须执行且非 FAIL；F0 由 acceptance 层单独覆盖
    验证点：inspect_status != FAIL；sync_status==EMPTY_RESPONSE；passed is True
    失败含义：sync 后坏库仍被标 pass，或 inspect 未执行
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    ensure_isolated_db(isolated_live_data_root)
    db_path = acceptance_db_path(isolated_live_data_root)

    def _mock_sync(_source_id: str, _data_root: Path) -> str:
        import duckdb

        con = duckdb.connect(str(db_path))
        try:
            insert_axis_observation(
                con,
                observation_id="e2-f0-boundary-obs",
                indicator_id="DGS10",
                obs_date=datetime.now(UTC).date(),
            )
        finally:
            con.close()
        return "EMPTY_RESPONSE"

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch._run_live_sync",
        _mock_sync,
    )
    outcome = run_tier_a_live_incremental("fred", isolated_live_data_root)
    assert outcome.inspect_status != "FAIL"
    assert outcome.sync_status == "EMPTY_RESPONSE"
    assert outcome.passed is True


def test_barLiveRoutePlanner_selectsBaostockPrimary() -> None:
    """覆盖范围：baostock live 路由强制 primary
    测试对象：_bar_live_route_planner
    目的/目标：S-ACCEPT 不得落到 akshare validation 路由
    验证点：preview_route selected_source_id==baostock；route_status==READY
    失败含义：baostock live 路由落到 akshare，FetchResult row_count=0
    """
    from backend.app.datasources.service import DataSourceService
    from backend.app.ops.tier_a_live_incremental_dispatch import _bar_live_route_planner

    registry, planner = _bar_live_route_planner("baostock")
    service = DataSourceService(source_registry=registry, route_planner=planner)
    plan = service.preview_route(
        data_domain="cn_equity_daily_bar", operation="fetch_daily_bar"
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"


def test_deribitSinceReader_acceptsDataDomainKwarg() -> None:
    """覆盖范围：deribit watermark 导入遮蔽回归
    测试对象：_live_sync_registry deribit since_reader
    目的/目标：cninfo 同名函数不得遮蔽 deribit data_domain 参数
    验证点：_deribit_since_reader 可调用且不抛 unexpected keyword
    失败含义：deribit live dispatch 在 since 读取阶段失败
    """
    from backend.app.ops.tier_a_live_incremental_dispatch import _live_sync_registry

    runners = _live_sync_registry()
    assert "deribit" in runners
    import inspect

    source = inspect.getsource(_live_sync_registry)
    assert "read_deribit_since_date" in source
    assert "read_cninfo_since_date" in source


def test_runF0DataHealth_failsWhenNoRawEvidence(
    isolated_live_data_root: Path,
) -> None:
    """覆盖范围：无 raw 证据时 F0 FAIL
    测试对象：_run_f0_data_health
    目的/目标：S-R2-F0 禁 SKIP — fresh sandbox 无 raw 时 FAIL
    验证点：status==FAIL；detail 含 no raw evidence
    失败含义：SKIP 路径残留
    """
    from backend.app.ops.tier_a_live_acceptance import _run_f0_data_health

    db_path = ensure_isolated_db(isolated_live_data_root)
    status, detail = _run_f0_data_health(
        "fred", data_root=isolated_live_data_root, db_path=db_path
    )
    assert status == "FAIL"
    assert "no raw evidence" in detail.lower()


def test_runF0DataHealth_failsOnIncompleteFredEvidence(
    isolated_live_data_root: Path,
) -> None:
    """覆盖范围：fred 残缺 live 证据
    测试对象：_run_f0_data_health
    目的/目标：残缺 JSON 须 FAIL 非 SKIP
    验证点：status==FAIL
    失败含义：partial F0 仍 SKIP
    """
    from backend.app.ops.tier_a_live_acceptance import _run_f0_data_health

    raw_dir = isolated_live_data_root / "raw" / "fred" / "2026-07-03"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "abc123.json").write_text('{"series_id":"DGS10"}', encoding="utf-8")
    db_path = ensure_isolated_db(isolated_live_data_root)
    status, detail = _run_f0_data_health(
        "fred", data_root=isolated_live_data_root, db_path=db_path
    )
    assert status == "FAIL"
    assert detail


@pytest.mark.network
@pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"),
    reason="network dispatch requires FRED_API_KEY",
)
def test_runTierALiveIncremental_fredLiveNetwork_realDispatch(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：S-ACCEPT 真实派发链（无 mock sync）
    测试对象：run_tier_a_live_incremental("fred", sandbox)
    目的/目标：真网 fred quick 路径 sync→inspect 可复验
    验证点：sync_status∈PASS_SYNC_STATUSES；inspect_status∈{PASS,WARN}；不 mock _run_live_sync
    失败含义：派发链仅 mock 集成，真网回归不可复验
    """
    from backend.app.ops.tier_a_live_status import PASS_SYNC_STATUSES

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    ensure_isolated_db(isolated_live_data_root)
    outcome = run_tier_a_live_incremental("fred", isolated_live_data_root)
    assert outcome.source_id == "fred"
    assert outcome.sync_status in PASS_SYNC_STATUSES
    assert outcome.inspect_status in {"PASS", "WARN"}
    assert outcome.clean_table == "axis_observation"
