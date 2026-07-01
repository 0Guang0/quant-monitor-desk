"""Batch 2.75 线上试点门禁测试（fail-closed 编排证据）。

覆盖范围：Phase -1 至 Phase 4 的授权、路由预览、HITL、raw-only 微拉取、
校验与 Request 2 对账；确保无授权、禁用源或 fixture 端口不得冒充 live 证据。
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from tests.contract_gate_support import PROJECT_ROOT, trellis_task_dir

BATCH275_TASK_SLUG = "06-21-round3-batch2-75-live-pilot"
TASK_DIR = trellis_task_dir(BATCH275_TASK_SLUG)
EVIDENCE_DIR = TASK_DIR / "execute-evidence"


def _restore_batch275_execute_evidence() -> None:
    """ponytail: pre-commit pytest must not leave task execute-evidence dirty."""
    rel = EVIDENCE_DIR.relative_to(PROJECT_ROOT).as_posix()
    subprocess.run(
        ["git", "checkout", "--", rel],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
    )

TRACKED_IDS = (
    "R3-B2.75-01",
    "GLOBAL-P2-01",
    "B2.5-O-05",
    "R3-B25-PERF-BUDGET-01",
    "R3-B25-HYG-03",
)

REGISTRY_PATHS = (
    PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md",
    PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md",
    PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md",
    PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected artifact: {path}"
    return path.read_text(encoding="utf-8")


def _fetch_call_tracker(deny_message: str) -> tuple[dict[str, bool], object]:
    """ponytail: shared fetch-not-called guard for authorization/source gate tests."""
    called = {"value": False}

    def _track(*_args, **_kwargs):
        called["value"] = True
        raise AssertionError(deny_message)

    return called, _track


def _phase3_evidence_with_hitl(tmp_path: Path, label: str) -> Path:
    """ponytail: HITL confirmation file required before Phase 3 live fetch."""
    out = tmp_path / "evidence"
    out.mkdir()
    (out / "phase3_hitl_user_confirmation.md").write_text(
        f"User confirmation: {label}\n",
        encoding="utf-8",
    )
    return out


def test_livePilot_phase3RawValidationReport_populatesRuleContract() -> None:
    """覆盖范围：phase3 raw-only validation_report stub INSERT
    测试对象：live_pilot_phase3._ensure_raw_file_registry_validation_report
    目的/目标：migration 010 要求 rule_set_id/rule_version NOT NULL，stub INSERT 须对齐 rule_contract
    验证点：INSERT 后行存在且 rule_set_id、rule_version 等于 default_quality_rule_contract()；
            quality_flags=staged_raw_metadata_only 且 can_write_clean=False
    失败含义：缺 rule 列或 gate 语义错误导致 live pilot phase3 写库失败
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.live_pilot import LivePilotRequest
    from backend.app.ops.live_pilot_phase3 import (
        RAW_FILE_REGISTRY_VALIDATION_REPORT_ID,
        _ensure_raw_file_registry_validation_report,
    )
    from backend.app.ops.staged_pilot import STAGED_RAW_METADATA_QUALITY_FLAG
    from backend.app.validators.rule_contract import default_quality_rule_contract

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    request = LivePilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/prompt14_user_authorization_batch275.md",
        raw_only=True,
    )
    _ensure_raw_file_registry_validation_report(con, request, "run-phase3-unit")
    rule_set_id, rule_version = default_quality_rule_contract()
    row = con.execute(
        """
        SELECT rule_set_id, rule_version, quality_flags, can_write_clean
        FROM validation_report
        WHERE validation_report_id = ?
        """,
        [RAW_FILE_REGISTRY_VALIDATION_REPORT_ID],
    ).fetchone()
    assert row is not None
    assert row[0] == rule_set_id
    assert row[1] == rule_version
    assert row[2] == STAGED_RAW_METADATA_QUALITY_FLAG
    assert row[3] is False


def test_livePilot_phaseMinus1_registryReconciliationRequired() -> None:
    """覆盖范围：Batch 2.75 Phase -1 是否完成五 ID registry 对账与读档证据
    测试对象：execute-evidence/phase_minus1_reconciliation.md、phase-1-registry-read.txt 及三份 registry
    目的/目标：开工前要把五类待对账项与 registry 对齐，不能把「规划已通过」误当成「线上试点已通过」
    验证点：reconciliation 含五个 ID 与 out-of-scope 说明；read log 含四 registry 路径；resolved 含 PLAN-01 且写明不闭合 R3-B2.75-01；pending 含 R3-B2.75-01 等
    失败含义：对账证据缺失，后续 live 阶段可能在错误的开放项状态下推进
    """
    reconciliation = EVIDENCE_DIR / "phase_minus1_reconciliation.md"
    registry_read = EVIDENCE_DIR / "phase-1-registry-read.txt"
    assert reconciliation.is_file(), "phase_minus1_reconciliation.md required"
    assert registry_read.is_file(), "phase-1-registry-read.txt required"

    text = _read(reconciliation)
    for item_id in TRACKED_IDS:
        assert item_id in text, f"reconciliation must map tracked ID {item_id}"

    assert "not-in-scope" in text.lower() or "out of scope" in text.lower()
    assert "R2b" in text or "ingestion split" in text.lower()

    read_log = _read(registry_read)
    for registry_path in REGISTRY_PATHS:
        rel = registry_path.relative_to(PROJECT_ROOT).as_posix()
        assert rel in read_log, f"registry read log must include {rel}"

    round3_map = _read(PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md")
    assert "R3-B2.75-PROD-LIVE-PILOT" in round3_map
    assert "Batch 2.75" in round3_map

    # AC-PM2: must not reopen resolved planning-only rows as live PASS
    resolved = _read(PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md")
    assert "R3-B2.75-PLAN-01" in resolved
    assert "Does not close `R3-B2.75-01`" in resolved

    pending = _read(PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md")
    for item_id in ("R3-B2.75-01", "GLOBAL-P2-01", "B2.5-O-05"):
        assert item_id in pending, f"pending fix registry must reference {item_id}"


def test_livePilot_perfAndHygieneRedefer_areAuthoritativeRegistryRows() -> None:
    """覆盖范围：性能与 hygiene 重 defer 项是否在权威 registry 有行
    测试对象：AUDIT_DEFERRED、UNRESOLVED、ROUND3_BATCH25_PENDING_FIX_REGISTRY
    目的/目标：R3-B25-PERF-BUDGET-01 与 R3-B25-HYG-03 在三表均可查
    验证点：两个 item_id 在三个 registry 正文均出现
    失败含义：perf/hygiene 债未双登记，Batch 2.75 closeout 无法引用 SSOT 行
    """
    required_ids = ("R3-B25-PERF-BUDGET-01", "R3-B25-HYG-03")
    registry_text = {
        path.name: _read(path)
        for path in (
            PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md",
            PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md",
            PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md",
        )
    }
    for item_id in required_ids:
        for registry_name, text in registry_text.items():
            assert item_id in text, f"{registry_name} must track {item_id}"


def test_livePilot_missingAuthorization_blocksBeforeFetch() -> None:
    """覆盖范围：缺少授权文件时 live pilot 是否在 fetch 前阻断
    测试对象：run_live_pilot_raw_only 与 DataSourceService.fetch（mock）
    目的/目标：没有真实授权文件时，必须在发起拉数之前就拒绝请求
    验证点：pytest.raises(LivePilotAuthorizationError)；fetch_called 仍为 False
    失败含义：无授权也能触发拉数，线上试点授权链形同虚设
    """
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        LivePilotRequest,
        run_live_pilot_raw_only,
    )

    request = LivePilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/nonexistent_batch275_authorization.md",
    )
    fetch_called, _track_fetch = _fetch_call_tracker(
        "fetch must not be called without authorization"
    )

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        with pytest.raises(LivePilotAuthorizationError):
            run_live_pilot_raw_only(
                request,
                sandbox_root=PROJECT_ROOT / ".audit-sandbox/batch275-live-pilot",
            )
    assert fetch_called["value"] is False


def test_livePilot_disabledSource_blocksBeforeFetch() -> None:
    """覆盖范围：禁用数据源（qmt_xtdata）是否在 fetch 前阻断
    测试对象：run_live_pilot_raw_only 对 qmt_xtdata 请求
    目的/目标：即便用户授权文件齐全，默认禁用的数据源也不能开始拉数
    验证点：pytest.raises(LivePilotDisabledSourceError)；fetch_called 为 False
    失败含义：高风险禁用源仍能拉数，试点范围可能被悄悄扩大
    """
    from backend.app.ops.live_pilot import (
        LivePilotDisabledSourceError,
        LivePilotRequest,
        run_live_pilot_raw_only,
    )

    request = LivePilotRequest(
        source_id="qmt_xtdata",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/batch275_user_authorization_2026-06-21.md",
    )
    fetch_called, _track_fetch = _fetch_call_tracker(
        "fetch must not be called for disabled source"
    )

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        with pytest.raises(LivePilotDisabledSourceError):
            run_live_pilot_raw_only(
                request,
                sandbox_root=PROJECT_ROOT / ".audit-sandbox/batch275-live-pilot",
            )
    assert fetch_called["value"] is False


def test_livePilot_authorization_approvedRequestPassesGate() -> None:
    """覆盖范围：已批准的 baostock 请求能否通过 Phase 0 授权校验
    测试对象：validate_authorization 与 batch275_user_authorization 证据路径
    目的/目标：符号、窗口、行数与授权文件匹配的请求不应被误拒
    验证点：对合法 LivePilotRequest 调用 validate_authorization 不抛异常
    失败含义：合法 pilot 请求过不了授权门，已批准 envelope 与实现脱节
    """
    from backend.app.ops.live_pilot import LivePilotRequest, validate_authorization

    request = LivePilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/batch275_user_authorization_2026-06-21.md",
    )
    validate_authorization(request)


def test_livePilot_authorization_rejectsExpandedRequestEnvelope() -> None:
    """覆盖范围：授权是否绑定精确 symbols/窗口/行数上限
    测试对象：validate_authorization 对 approved_pilot_requests 的扩 envelope 变体
    目的/目标：换股票、拉长窗口或增大 max_rows 必须拒掉
    验证点：三处 replace 变体均 pytest.raises(LivePilotAuthorizationError)
    失败含义：授权可被套利扩大，micro-fetch 行数上限形同虚设
    """
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        approved_pilot_requests,
        validate_authorization,
    )

    approved = approved_pilot_requests()[0]
    expanded_requests = (
        replace(approved, symbols_or_indicators=("sh.600000",)),
        replace(approved, date_window="recent 30 trading days"),
        replace(approved, max_rows=approved.max_rows + 1),
    )

    for request in expanded_requests:
        with pytest.raises(LivePilotAuthorizationError):
            validate_authorization(request)


def test_livePilot_authorization_rejectsUnapprovedOptionalSource() -> None:
    """覆盖范围：未在默认 envelope 内的可选源 cninfo 是否被拒
    测试对象：validate_authorization 对 cninfo/announcements 请求
    目的/目标：仅有通用授权文件不足以批准额外源域操作
    验证点：cninfo 请求 pytest.raises(LivePilotAuthorizationError)
    失败含义：可选源无单独批准也能过门，pilot 范围会被悄悄扩大
    """
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        LivePilotRequest,
        validate_authorization,
    )

    request = LivePilotRequest(
        source_id="cninfo",
        data_domain="cn_announcements",
        operation="fetch_announcement_index",
        symbols_or_indicators=("600519",),
        date_window="recent 7 calendar days",
        max_rows=20,
        authorization_evidence="docs/quality/batch275_user_authorization_2026-06-21.md",
    )

    with pytest.raises(LivePilotAuthorizationError):
        validate_authorization(request)


def test_livePilot_authorization_recordDocumentsSourceRiskRationale() -> None:
    """覆盖范围：Phase 0 授权记录是否写明各源风险 rationale
    测试对象：execute-evidence/phase0_authorization_record.md
    目的/目标：证据解释为何 baostock/akshare 低于 qmt/fred/yahoo，并引用用户授权文件
    验证点：文件存在；含 baostock、akshare、qmt、fred、yahoo；含 batch275_user_authorization 相对路径
    失败含义：缺风险说明，审计无法判断源选择是否与策略一致
    """
    record = EVIDENCE_DIR / "phase0_authorization_record.md"
    assert record.is_file(), "phase0_authorization_record.md required"
    text = _read(record)
    assert "baostock" in text.lower()
    assert "akshare" in text.lower()
    for riskier in ("qmt", "fred", "yahoo"):
        assert riskier in text.lower(), f"source risk rationale must mention {riskier}"
    auth_rel = "docs/quality/batch275_user_authorization_2026-06-21.md"
    assert auth_rel in text


def test_livePilot_phase1Baseline_readOnly(tmp_path: Path) -> None:
    """覆盖范围：Phase 1 基线采集是否只读且不改动 DB 哈希
    测试对象：capture_phase1_baseline 与临时 DuckDB
    目的/目标：基线盘点只能读库、不能改库，并产出完整的能力快照与无写入证明
    验证点：db 字节前后相同；mutation_proof 两 flag 为 True；inspect mode 为 read_only；capability 含 baostock/akshare 三请求；任务 execute-evidence 三文件存在
    失败含义：基线阶段偷偷改库或缺能力快照，后续「生产库未动」证明不可信
    """
    import duckdb
    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.db_inspector import REQUIRED_TOP_LEVEL_FIELDS
    from backend.app.ops.live_pilot import capture_phase1_baseline

    db = tmp_path / "quant_monitor.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    before_hash = db.read_bytes()

    out = tmp_path / "phase1-out"
    result = capture_phase1_baseline(
        db_path=db,
        data_root=data_root,
        evidence_dir=out,
    )

    assert db.read_bytes() == before_hash
    assert result["mutation_proof"]["db_hash_unchanged"] is True
    assert result["mutation_proof"]["phase1_zero_mutation"] is True

    inventory = result["inspect"]
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in inventory
    assert inventory["mode"] == "read_only"
    assert inventory["db"]["read_only_open"] is True

    capability = result["capability_snapshot"]
    assert len(capability["pilot_requests"]) == 3
    request_keys = {
        (item["source_id"], item["data_domain"], item["operation"])
        for item in capability["pilot_requests"]
    }
    assert ("baostock", "cn_equity_daily_bar", "fetch_daily_bar") in request_keys
    assert ("akshare", "cn_equity_daily_bar", "fetch_daily_bar_validation") in request_keys
    assert ("akshare", "macro_supplementary", "fetch_macro_series") in request_keys

    for name in (
        "phase1_baseline_inventory.json",
        "phase1_baseline_inventory.md",
        "phase1_no_mutation_proof.md",
        "phase1_capability_snapshot.json",
    ):
        assert (out / name).is_file(), f"missing artifact {name}"

    task_inventory = EVIDENCE_DIR / "phase1_baseline_inventory.json"
    task_capability = EVIDENCE_DIR / "phase1_capability_snapshot.json"
    task_proof = EVIDENCE_DIR / "phase1_no_mutation_proof.md"
    assert task_inventory.is_file(), "execute-evidence phase1_baseline_inventory.json required"
    assert task_capability.is_file(), "execute-evidence phase1_capability_snapshot.json required"
    assert task_proof.is_file(), "execute-evidence phase1_no_mutation_proof.md required"


AUTH_EVIDENCE = "docs/quality/batch275_user_authorization_2026-06-21.md"


def test_livePilot_phase2RouteMatrix_threeRequests(tmp_path: Path) -> None:
    """覆盖范围：Phase 2 三路 dry-run 路由矩阵是否不触发 fetch
    测试对象：capture_phase2_route_matrix 与 approved_pilot_requests
    目的/目标：三条已授权请求只做路由预览与资源守卫检查，不真正拉数
    验证点：fetch 未调用；dry_run True；三 preview 各有 route_status/resource_guard；macro 请求 explicit_source_route_status 为 VALIDATION_ONLY_BLOCKED 或 DISABLED_SOURCE；任务 evidence 中 matrix JSON dry_run 且 fred_primary_deferred
    失败含义：预览阶段仍去拉 vendor 数据，dry-run 与真实 live 边界混淆
    """
    from backend.app.ops.live_pilot import (
        approved_pilot_requests,
        capture_phase2_route_matrix,
    )

    fetch_called, _track_fetch = _fetch_call_tracker("Phase 2 must not invoke fetch")

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        result = capture_phase2_route_matrix(
            requests=approved_pilot_requests(),
            evidence_dir=tmp_path / "phase2-out",
            db_path=tmp_path / "unused.duckdb",
        )

    assert fetch_called["value"] is False
    assert result["dry_run"] is True
    assert len(result["previews"]) == 3
    for preview in result["previews"]:
        req = preview["request"]
        domain = preview["route_plan"]["data_domain"]
        if req["source_id"] == "akshare" and domain == "macro_supplementary":
            assert preview["explicit_source_route_status"] in {
                "VALIDATION_ONLY_BLOCKED",
                "DISABLED_SOURCE",
            }
        else:
            assert preview["explicit_source_route_status"] == "READY"
        assert preview["resource_guard_decision"] in {"OK", "PAUSE"}
        assert preview["route_plan"]["data_domain"]
        assert preview["route_plan"]["operation"]
        assert preview["request"]["authorization_evidence"] == AUTH_EVIDENCE

    matrix_path = EVIDENCE_DIR / "phase2_route_preview_matrix.json"
    assert matrix_path.is_file(), "execute-evidence phase2_route_preview_matrix.json required"
    payload = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert payload["dry_run"] is True
    assert len(payload["previews"]) == 3
    assert payload.get("fred_primary_deferred") is True


def test_livePilot_phase2_previewIncludesResourceGuardDecision(tmp_path: Path) -> None:
    """覆盖范围：单条 route preview 是否携带 ResourceGuard 决策字段
    测试对象：preview_live_pilot 对首个 approved 请求
    目的/目标：每条预览除路由状态外还须暴露 guard 决策与原因
    验证点：preview 含 resource_guard_decision、resource_guard_reason；dry_run True；explicit_source_route_status==READY
    失败含义：预览缺 guard 字段，Phase 3 可能在资源压力下仍尝试 fetch
    """
    from backend.app.ops.live_pilot import approved_pilot_requests, preview_live_pilot

    request = approved_pilot_requests()[0]
    preview = preview_live_pilot(request)
    assert "resource_guard_decision" in preview
    assert "resource_guard_reason" in preview
    assert preview["dry_run"] is True
    assert preview["explicit_source_route_status"] == "READY"


def test_livePilot_phase3_requiresHitlBeforeFetch(tmp_path: Path) -> None:
    """覆盖范围：Phase 3 live fetch 是否要求 HITL 确认文件
    测试对象：run_live_pilot_raw_only(dry_run=False) 无 phase3_hitl 文件时
    目的/目标：无人机确认不得进入真实 fetch
    验证点：pytest.raises(LivePilotAuthorizationError, match='HITL')
    失败含义：缺 HITL 也能拉 live 数据，违背 Batch 2.75 人工确认门
    """
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        approved_pilot_requests,
        run_live_pilot_raw_only,
    )

    out = tmp_path / "no-hitl"
    out.mkdir()
    request = approved_pilot_requests()[0]
    with pytest.raises(LivePilotAuthorizationError, match="HITL"):
        run_live_pilot_raw_only(
            replace(request, dry_run=False),
            sandbox_root=tmp_path / "sandbox",
            evidence_dir=out,
        )


def test_livePilot_phase3_rejectsFixtureFetchPort(tmp_path: Path) -> None:
    """覆盖范围：StubFetchPort 是否不能满足 live pilot 证据要求
    测试对象：_assert_live_fetch_port(StubFetchPort(...))
    目的/目标：测试用 stub 端口必须被显式拒绝
    验证点：pytest.raises(LivePilotFixtureForbiddenError)
    失败含义：stub 端口可通过 live 检查，fixture 数据会被当成 live 证据
    """
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.ops.live_pilot import (
        LivePilotFixtureForbiddenError,
        _assert_live_fetch_port,
    )

    with pytest.raises(LivePilotFixtureForbiddenError):
        _assert_live_fetch_port(StubFetchPort(payload=b"{}"))


def test_livePilot_phase3_rejectsLocalFixtureAndStagedService(tmp_path: Path) -> None:
    """覆盖范围：LocalFixtureFetchPort 与 staged fixture service 是否被拒
    测试对象：_assert_live_fetch_port 对本地 fixture 与 build_staged_fixture_service
    目的/目标：本地 JSON fixture 与 staged service 端口不能冒充 live fetch
    验证点：两处均 pytest.raises(LivePilotFixtureForbiddenError)
    失败含义：staged fixture 服务可过 live 门，Request 3 证据与 Batch 2.5 叙事冲突
    """
    from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort
    from backend.app.datasources.service import build_staged_fixture_service
    from backend.app.ops.live_pilot import (
        LivePilotFixtureForbiddenError,
        _assert_live_fetch_port,
    )

    fixture = tmp_path / "fixture.json"
    fixture.write_text("{}", encoding="utf-8")
    fixture_port = LocalFixtureFetchPort(fixture, row_count=1)
    with pytest.raises(LivePilotFixtureForbiddenError):
        _assert_live_fetch_port(fixture_port)

    staged_service = build_staged_fixture_service(
        data_root=tmp_path / "data",
        fixture_path=fixture,
    )
    with pytest.raises(LivePilotFixtureForbiddenError):
        _assert_live_fetch_port(getattr(staged_service, "_fetch_port"))


@pytest.mark.parametrize(
    "route_status",
    ("DISABLED_SOURCE", "CAPABILITY_MISSING", "USER_AUTH_REQUIRED", "RESOURCE_GUARD_PAUSED"),
)
def test_livePilot_phase3_routeNotReady_stopsBeforeFetch(
    tmp_path: Path,
    route_status: str,
) -> None:
    """覆盖范围：非 READY 显式路由是否在构建 fetch port 前停止
    测试对象：run_live_pilot_raw_only 在 mock preview 返回 DISABLED/CAPABILITY_MISSING 等状态时
    目的/目标：路由未就绪时不得创建 live fetch port
    验证点：pytest.raises(LivePilotRouteNotReadyError, match=route_status)；fetch_port_called 为 False
    失败含义：坏路由仍建 fetch 端口，live pilot 可能在禁用源上拉数
    """
    from backend.app.ops.live_pilot import (
        LivePilotRouteNotReadyError,
        approved_pilot_requests,
        run_live_pilot_raw_only,
    )

    out = _phase3_evidence_with_hitl(tmp_path, "test route gate only")
    fetch_port_called = {"value": False}

    def _unexpected_fetch_port(**_kwargs):
        fetch_port_called["value"] = True
        raise AssertionError("fetch port must not be built when route is not READY")

    with (
        patch(
            "backend.app.ops.live_pilot_phase3.preview_live_pilot",
            return_value={"explicit_source_route_status": route_status},
        ),
        patch(
            "backend.app.ops.live_pilot_fetch_ports.create_live_fetch_port",
            side_effect=_unexpected_fetch_port,
        ),
    ):
        with pytest.raises(LivePilotRouteNotReadyError, match=route_status):
            run_live_pilot_raw_only(
                replace(approved_pilot_requests()[0], dry_run=False),
                sandbox_root=tmp_path / "sandbox",
                evidence_dir=out,
            )

    assert fetch_port_called["value"] is False


def test_livePilot_phase3_akshareMacroDisabled_stopsBeforeFetch(tmp_path: Path) -> None:
    """覆盖范围：akshare macro_supplementary 在 DISABLED_SOURCE 时 fail-closed
    测试对象：run_live_pilot_raw_only 对 approved 第 3 路 macro 请求
    目的/目标：政策要求 DISABLED_SOURCE 停止 pilot，不得借 staged_fixture 旁路 fetch
    验证点：pytest.raises(LivePilotRouteNotReadyError, match=DISABLED_SOURCE)；fetch_port 未构建
    失败含义：macro 旁路破坏 production_live_pilot_policy §4 与 AKSHARE-MACRO-PILOT-POLICY
    """
    from backend.app.ops.live_pilot import (
        LivePilotRouteNotReadyError,
        approved_pilot_requests,
        run_live_pilot_raw_only,
    )

    macro_request = approved_pilot_requests()[2]
    out = _phase3_evidence_with_hitl(tmp_path, "macro route gate")
    fetch_port_called = {"value": False}

    def _unexpected_fetch_port(**_kwargs):
        fetch_port_called["value"] = True
        raise AssertionError("fetch port must not be built for DISABLED_SOURCE macro route")

    with (
        patch(
            "backend.app.ops.live_pilot_phase3.preview_live_pilot",
            return_value={"explicit_source_route_status": "DISABLED_SOURCE"},
        ),
        patch(
            "backend.app.ops.live_pilot_fetch_ports.create_live_fetch_port",
            side_effect=_unexpected_fetch_port,
        ),
    ):
        with pytest.raises(LivePilotRouteNotReadyError, match="DISABLED_SOURCE"):
            run_live_pilot_raw_only(
                replace(macro_request, dry_run=False),
                sandbox_root=tmp_path / "sandbox",
                evidence_dir=out,
            )

    assert fetch_port_called["value"] is False


def test_livePilot_phase3_sandboxPathOutsideRaisesAuthorizationError(tmp_path: Path) -> None:
    """覆盖范围：raw 证据路径越界时抛授权错误而非 NameError
    测试对象：run_live_pilot_raw_only 在 fetch 返回 sandbox 外路径时
    目的/目标：路径校验 fail-closed 且异常类型可审计
    验证点：pytest.raises(LivePilotAuthorizationError, match=outside sandbox)
    失败含义：未 import 或错误类型导致运维看到 NameError 而非授权失败
    """
    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        approved_pilot_requests,
        run_live_pilot_raw_only,
    )

    out = _phase3_evidence_with_hitl(tmp_path, "sandbox path gate")
    outside = tmp_path / "outside" / "evil.json"
    outside.parent.mkdir(parents=True)
    outside.write_text("{}", encoding="utf-8")

    fake_result = FetchResult(
        run_id="pilot-req-live",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        status="SUCCESS",
        row_count=1,
        fetch_time="2026-01-01T00:00:00+00:00",
        raw_file_paths=[str(outside)],
        content_hash="abc",
    )

    with (
        patch(
            "backend.app.ops.live_pilot_phase3.preview_live_pilot",
            return_value={"explicit_source_route_status": "READY"},
        ),
        patch(
            "backend.app.ops.live_pilot_fetch_ports.create_live_fetch_port",
            return_value=object(),
        ),
        patch(
            "backend.app.ops.live_pilot_phase3.DataSourceService.fetch",
            return_value=fake_result,
        ),
    ):
        with pytest.raises(LivePilotAuthorizationError, match="outside sandbox"):
            run_live_pilot_raw_only(
                replace(approved_pilot_requests()[0], dry_run=False),
                sandbox_root=tmp_path / "sandbox",
                evidence_dir=out,
            )


def test_livePilot_phase3_resourceGuardHardStop_stopsBeforeFetch(tmp_path: Path) -> None:
    """覆盖范围：ResourceGuard HARD_STOP 是否在 fetch port 构建前终止
    测试对象：run_live_pilot_raw_only 当 preview 抛 ResourceGuard HARD_STOP 时
    目的/目标：资源硬停必须比 fetch 更早，且不得创建 fetch port
    验证点：pytest.raises(RuntimeError, match='ResourceGuard HARD_STOP')；fetch_port_called 为 False
    失败含义：guard 硬停后仍建端口，可能在高负载下继续 live 拉数
    """
    from backend.app.ops.live_pilot import approved_pilot_requests, run_live_pilot_raw_only

    out = _phase3_evidence_with_hitl(tmp_path, "test guard gate only")
    fetch_port_called = {"value": False}

    def _unexpected_fetch_port(**_kwargs):
        fetch_port_called["value"] = True
        raise AssertionError("fetch port must not be built when ResourceGuard blocks")

    with (
        patch(
            "backend.app.ops.live_pilot_phase3.preview_live_pilot",
            side_effect=RuntimeError("ResourceGuard HARD_STOP: test"),
        ),
        patch(
            "backend.app.ops.live_pilot_fetch_ports.create_live_fetch_port",
            side_effect=_unexpected_fetch_port,
        ),
    ):
        with pytest.raises(RuntimeError, match="ResourceGuard HARD_STOP"):
            run_live_pilot_raw_only(
                replace(approved_pilot_requests()[0], dry_run=False),
                sandbox_root=tmp_path / "sandbox",
                evidence_dir=out,
            )

    assert fetch_port_called["value"] is False


def test_livePilot_phase3_failureLeavesDurableEvidence(tmp_path: Path) -> None:
    """覆盖范围：Phase 3 vendor 失败是否留下可重跑的结构化证据
    测试对象：capture_phase3_raw_evidence 在第二次 fetch 抛 timeout 时
    目的/目标：某一路拉数失败时，仍要留下可复查的失败记录，且允许安全重跑
    验证点：payload rerun_safe True；第二路 status FAILED 含 vendor timeout；存在 phase3_fetch_failure 与 phase3_raw_micro_fetch_evidence 文件
    失败含义：失败无持久记录，重跑会丢失失败语义或覆盖审计轨迹
    """
    from backend.app.ops.live_pilot import approved_pilot_requests, capture_phase3_raw_evidence

    calls = {"count": 0}

    def _fake_run(_request, *, sandbox_root: Path, pilot_request_id: str, evidence_dir: Path):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("vendor timeout")
        return {
            "pilot_request_id": pilot_request_id,
            "sandbox_root": str(sandbox_root),
            "fetch_result": {
                "status": "SUCCESS",
                "row_count": 1,
                "raw_file_paths": [],
                "content_hash": "abc",
            },
            "production_mutation_proof": {
                "db_hash_unchanged": True,
                "row_counts_unchanged": True,
            },
        }

    with patch("backend.app.ops.live_pilot_phase3.run_live_pilot_raw_only", side_effect=_fake_run):
        payload = capture_phase3_raw_evidence(
            requests=approved_pilot_requests(),
            sandbox_root=tmp_path / "sandbox",
            evidence_dir=tmp_path / "evidence",
        )

    assert payload["rerun_safe"] is True
    assert payload["fetches"][1]["fetch_result"]["status"] == "FAILED"
    assert "vendor timeout" in payload["fetches"][1]["fetch_result"]["error_message"]
    assert (tmp_path / "evidence" / "phase3_fetch_failure_pilot-req-2.json").is_file()
    assert (tmp_path / "evidence" / "phase3_raw_micro_fetch_evidence.json").is_file()


def test_livePilot_phase3_repeatExecution_isRerunSafe(tmp_path: Path) -> None:
    """覆盖范围：重复执行 Phase 3 证据采集是否保持 rerun_safe 语义
    测试对象：capture_phase3_raw_evidence 连续调用两次
    目的/目标：重复执行采集时仍应保留三路结果，且生产库未被改动
    验证点：两次 rerun_safe True；持久化 JSON 含 pilot-req-1/2/3 且各 proof db_hash_unchanged 与 row_counts_unchanged
    失败含义：重跑破坏结构化证据或未改库证明，沙箱语义不可复现
    """
    from backend.app.ops.live_pilot import approved_pilot_requests, capture_phase3_raw_evidence

    def _fake_run(_request, *, sandbox_root: Path, pilot_request_id: str, evidence_dir: Path):
        raw_path = sandbox_root / "data" / "raw" / f"{pilot_request_id}.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text('{"rows":[{"date":"2026-06-21"}]}', encoding="utf-8")
        return {
            "pilot_request_id": pilot_request_id,
            "sandbox_root": str(sandbox_root),
            "fetch_result": {
                "status": "SUCCESS",
                "row_count": 1,
                "raw_file_paths": [str(raw_path)],
                "content_hash": f"hash-{pilot_request_id}",
            },
            "production_mutation_proof": {
                "db_hash_unchanged": True,
                "row_counts_unchanged": True,
            },
        }

    evidence_dir = tmp_path / "evidence"
    sandbox_root = tmp_path / "sandbox"
    with patch("backend.app.ops.live_pilot_phase3.run_live_pilot_raw_only", side_effect=_fake_run):
        first = capture_phase3_raw_evidence(
            requests=approved_pilot_requests(),
            sandbox_root=sandbox_root,
            evidence_dir=evidence_dir,
        )
        second = capture_phase3_raw_evidence(
            requests=approved_pilot_requests(),
            sandbox_root=sandbox_root,
            evidence_dir=evidence_dir,
        )

    assert first["rerun_safe"] is True
    assert second["rerun_safe"] is True
    assert len(second["fetches"]) == 3
    persisted = json.loads((evidence_dir / "phase3_raw_micro_fetch_evidence.json").read_text())
    assert persisted["rerun_safe"] is True
    assert [item["pilot_request_id"] for item in persisted["fetches"]] == [
        "pilot-req-1",
        "pilot-req-2",
        "pilot-req-3",
    ]
    for item in persisted["fetches"]:
        proof = item["production_mutation_proof"]
        assert proof["db_hash_unchanged"] is True
        assert proof["row_counts_unchanged"] is True


@pytest.mark.network
@pytest.mark.slow
def test_livePilot_phase3RawOnly_threeRequestsLive(tmp_path: Path) -> None:
    """覆盖范围：三路授权请求的 sandbox live raw-only 微拉取（需外网）
    测试对象：capture_phase3_raw_evidence 与 execute-evidence HITL 文件
    目的/目标：baostock 与 akshare validation 真网 SUCCESS；macro DISABLED_SOURCE 政策性失败
    验证点：前两路 SUCCESS、row_count>0、content_hash；第 3 路 FAILED 且 error 含 DISABLED；
            mutation_proof 两 True；raw 路径在 sandbox 下；标记 network/slow
    失败含义：live micro-fetch 不能成功或污染生产路径，Batch 2.75 Request 1 证据无效
    """
    from backend.app.ops.live_pilot import (
        approved_pilot_requests,
        capture_phase3_raw_evidence,
    )

    sandbox = tmp_path / "live-sandbox"
    out = tmp_path / "phase3-out"
    out.mkdir()
    hitl_src = EVIDENCE_DIR / "phase3_hitl_user_confirmation.md"
    assert hitl_src.is_file()
    (out / "phase3_hitl_user_confirmation.md").write_text(
        hitl_src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    requests = approved_pilot_requests()
    result = capture_phase3_raw_evidence(
        requests=requests,
        sandbox_root=sandbox,
        evidence_dir=out,
    )
    assert len(result["fetches"]) == 3
    for index, item in enumerate(result["fetches"]):
        req = requests[index]
        proof = item["production_mutation_proof"]
        assert proof["db_hash_unchanged"] is True
        assert proof["row_counts_unchanged"] is True
        if req.data_domain == "macro_supplementary":
            assert item["fetch_result"]["status"] == "FAILED"
            assert "DISABLED" in item["fetch_result"]["error_message"]
            continue
        assert item["fetch_result"]["status"] == "SUCCESS"
        assert item["fetch_result"]["row_count"] > 0
        assert item["fetch_result"]["content_hash"]
        for path in item["fetch_result"]["raw_file_paths"]:
            assert str(sandbox.resolve()) in str(Path(path).resolve())


def test_livePilot_phase4Validation_noCleanWriteByDefault() -> None:
    """覆盖范围：Phase 4 任务证据是否默认禁止 clean write
    测试对象：capture_task_phase4_validation_evidence(EVIDENCE_DIR)
    目的/目标：第四阶段校验默认不能写清洁库，只应记录校验结论
    验证点：result allow_clean_write/clean_write_performed 为 False；report 含 ALLOW_CLEAN_WRITE_FALSE_DEFAULT 与三类 validator 路径；proof 含 allow_clean_write false
    失败含义：校验阶段默认允许写清洁层，试点可能误把观测写入生产库
    """
    from backend.app.ops.live_pilot import capture_task_phase4_validation_evidence

    result = capture_task_phase4_validation_evidence(EVIDENCE_DIR)
    try:
        assert result["allow_clean_write"] is False
        assert result["clean_write_performed"] is False

        report_path = EVIDENCE_DIR / "phase4_validation_report.json"
        proof_path = EVIDENCE_DIR / "phase4_no_production_mutation_proof.md"
        assert report_path.is_file()
        assert proof_path.is_file()

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        assert payload["allow_clean_write"] is False
        assert payload["can_write_clean"] is False
        assert "ALLOW_CLEAN_WRITE_FALSE_DEFAULT" in payload["clean_write_block_reasons"]
        declared_paths = payload["declared_validation_conflict_paths"]
        assert declared_paths["data_quality_validator"].endswith("DataQualityValidator")
        assert declared_paths["source_conflict_validator"].endswith("SourceConflictValidator")
        assert declared_paths["clean_write_gate"].endswith("DbValidationGate")
        for item in payload["validations"]:
            assert item.get("allow_clean_write") is False

        proof = proof_path.read_text(encoding="utf-8")
        assert "allow_clean_write" in proof
        assert "false" in proof.lower()
    finally:
        _restore_batch275_execute_evidence()


def test_livePilot_phase4_requiresRequest2Prerequisites(tmp_path: Path) -> None:
    """覆盖范围：Phase 4 是否在缺 Request 2 前置工件时 fail-closed
    测试对象：capture_phase4_validation 仅有 phase3 JSON、无 eastmoney verdict/reconciliation 时
    目的/目标：仅有 raw fetch 证据不足以进入 Phase 4 校验
    验证点：pytest.raises(LivePilotAuthorizationError, match='Request 2')；phase3 源文件存在并已复制到 tmp
    失败含义：缺 Request 2 裁决也能跑 Phase 4，stock_zh_a_hist 边界会被跳过
    """
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        capture_phase4_validation,
    )

    phase3_src = EVIDENCE_DIR / "phase3_raw_micro_fetch_evidence.json"
    assert phase3_src.is_file()
    (tmp_path / "phase3_raw_micro_fetch_evidence.json").write_text(
        phase3_src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(LivePilotAuthorizationError, match="Request 2"):
        capture_phase4_validation(evidence_dir=tmp_path)


def test_livePilot_phase4_severeBlocksCleanWriteEvidence(tmp_path: Path) -> None:
    """覆盖范围：严重校验发现是否阻止 clean write 并写入证据
    测试对象：capture_phase4_validation 在提供 Request 2 工件后
    目的/目标：出现严重校验问题时，必须阻止清洁层写入并留下证明
    验证点：result 三 flag：severe_findings_block_clean_write True、clean_write_performed False、severe_findings 非空；proof 含 severe_findings_block_clean_write
    失败含义：严重问题仍允许写清洁层，数据质量门禁失去阻断作用
    """
    from backend.app.ops.live_pilot import capture_phase4_validation

    (tmp_path / "eastmoney_stock_zh_a_hist_verdict.md").write_text(
        "Request 2 original endpoint 不可用\n",
        encoding="utf-8",
    )
    (tmp_path / "phase3_request2_evidence_reconciliation.md").write_text(
        "Request 2 stock_zh_a_hist push2his.eastmoney.com sidecar only\n",
        encoding="utf-8",
    )

    result = capture_phase4_validation(
        evidence_dir=tmp_path,
        phase3_payload={"fetches": []},
    )

    assert result["severe_findings_block_clean_write"] is True
    assert result["clean_write_performed"] is False
    assert result["severe_findings"]
    proof = _read(tmp_path / "phase4_no_production_mutation_proof.md")
    assert "severe_findings_block_clean_write" in proof


def test_livePilot_phase4Conflict_inspectOrNoConflict() -> None:
    """覆盖范围：Phase 4 冲突 inspect 与 Request 2 sidecar 边界
    测试对象：任务 execute-evidence 中 phase4_conflict_inspect 与 validation_report
    目的/目标：冲突报告须说明 Request 2 只是旁路信息，不能当成原接口已闭合
    验证点：conflict 与 reconciliation 文件存在；inspect 含 Request 2/sidecar/NO_CONFLICT 或 Informational；report 中 req-2 closes_original_request2 为 False
    失败含义：冲突叙事含糊，Request 2 失败可能被误当成原 endpoint 已闭合
    """
    from backend.app.ops.live_pilot import capture_task_phase4_validation_evidence

    capture_task_phase4_validation_evidence(EVIDENCE_DIR)
    try:
        conflict_path = EVIDENCE_DIR / "phase4_conflict_inspect.txt"
        reconciliation_path = EVIDENCE_DIR / "phase3_request2_evidence_reconciliation.md"
        assert conflict_path.is_file()
        assert reconciliation_path.is_file()

        text = _read(conflict_path)
        assert "Request 2" in text
        assert "sidecar" in text.lower() or "informational" in text.lower()
        assert "NO_CONFLICT_INSPECT_REQUIRED_FOR_CLOSEOUT" in text or "Informational sidecar" in text

        report = json.loads(_read(EVIDENCE_DIR / "phase4_validation_report.json"))
        req2 = next(v for v in report["validations"] if v["pilot_request_id"] == "pilot-req-2")
        assert req2["status"] == "SOURCE_ENDPOINT_FAILURE"
        classification = req2["request2_endpoint_classification"]
        assert classification["closes_original_request2"] is False
        assert classification["supports_pilot_pass_raw_only"] is False
    finally:
        _restore_batch275_execute_evidence()


def test_livePilot_request2Reconciliation_requiredBeforePhase4() -> None:
    """覆盖范围：Phase 4 前 Request 2 对账工件是否齐全
    测试对象：phase3_request2_evidence_reconciliation.md 与 eastmoney_stock_zh_a_hist_verdict.md
    目的/目标：对账文须连接 stock_zh_a_hist、eastmoney sidecar、daily 候选与 018C 边界
    验证点：两文件存在；reconciliation 含 hist/push2his/stock_zh_a_daily/sidecar/PILOT_PASS_RAW_ONLY/018C
    失败含义：缺对账或裁决，Phase 4 无法证明 Request 2 未越权闭合
    """
    reconciliation = EVIDENCE_DIR / "phase3_request2_evidence_reconciliation.md"
    verdict = EVIDENCE_DIR / "eastmoney_stock_zh_a_hist_verdict.md"
    assert reconciliation.is_file()
    assert verdict.is_file()
    text = _read(reconciliation)
    assert "stock_zh_a_hist" in text
    assert "push2his.eastmoney.com" in text
    assert "stock_zh_a_daily" in text
    assert "sidecar" in text.lower()
    assert "PILOT_PASS_RAW_ONLY" in text
    assert "018C_tdx_pytdx_low_cost_probe.md" in text
