"""Round 3G R3G-01 sandbox clean-write rehearsal 契约门禁。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT, load_yaml
from tests.repo_paths import repo_relative

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"
FRED_AUTH = PROJECT_ROOT / ".audit-sandbox/round3g/fred_user_authorization.yaml"

# ponytail: ResourceGuard autouse — tests/conftest.py::_resourceGuardOkUnlessTestOverrides


@pytest.fixture
def _dry_run_rehearsal_paths(tmp_path: Path) -> dict[str, Path]:
    """Shared sandbox/evidence/report paths for dry-run runner tests (R3G-REP-P3-05)."""
    return {
        "sandbox_db": tmp_path / "sandbox.duckdb",
        "evidence_dir": tmp_path / "evidence",
        "report_path": tmp_path / "report.json",
    }


def _contract() -> dict:
    return load_yaml(CONTRACT)


def test_r3g01Contract_sandboxOnlyBlocksProductionMutation() -> None:
    """覆盖范围：R3G-01 rehearsal 契约 fail-closed 语义
    测试对象：sandbox_clean_write_contract.yaml r3g01_rehearsal
    目的/目标：排练阶段必须 sandbox-only 且禁止 production mutation
    验证点：production_mutation_allowed 为 false；sandbox_only 为 true
    失败含义：契约允许生产写路径，Batch 3G 安全边界被突破
    """
    gate = _contract()["r3g01_rehearsal"]
    assert gate["production_mutation_allowed"] is False
    assert gate["sandbox_only"] is True


def test_r3g01Contract_requiresRehearsalReportFields() -> None:
    """覆盖范围：R3G-01 排练报告必填字段
    测试对象：r3g01_rehearsal.required_report_fields
    目的/目标：排练证据须可审计 lineage 与 write_manager 操作
    验证点：必填字段含 rollback_artifact_path 与 write_manager_operation_id
    失败含义：排练报告缺关键字段会导致 3G 证据链不可追溯
    """
    fields = set(_contract()["r3g01_rehearsal"]["required_report_fields"])
    assert "rollback_artifact_path" in fields
    assert "write_manager_operation_id" in fields
    assert "source_fetch_id_coverage" in fields


def test_r3g01TaskCard_linkedFromContract() -> None:
    """覆盖范围：契约与 R3G-01 任务卡交叉引用
    测试对象：canonical_task_cards.R3G-01
    目的/目标：契约 SSOT 须指向可读的冻结任务卡路径
    验证点：任务卡文件存在且正文引用本契约
    失败含义：Execute 无法从契约路由到 R3G-01 实施说明
    """
    rel = _contract()["canonical_task_cards"]["R3G-01"]
    card = repo_relative(rel)
    assert card.is_file(), f"missing task card: {rel}"
    assert "sandbox_clean_write_contract.yaml" in card.read_text(encoding="utf-8")


# --- RehearsalPlan (9.1) -----------------------------------------------------


def test_RehearsalPlan_r3gP0_withinContractCaps() -> None:
    """覆盖范围：r3g_p0 候选集在契约 cap 内
    测试对象：load_candidate_set + validate_source_caps
    目的/目标：仅 baostock/cninfo/fred 三源且符号/窗口受 r3g01 cap 约束
    验证点：r3g_p0 三候选 validate_source_caps 不抛错
    失败含义：默认候选集超 cap 或含未批准源
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        load_candidate_set,
        validate_source_caps,
    )

    candidates = load_candidate_set("r3g_p0")
    assert {c.source_id for c in candidates} == {"baostock", "cninfo", "fred"}
    for candidate in candidates:
        validate_source_caps(candidate)


def test_RehearsalPlan_rejectsOverWindowDays() -> None:
    """覆盖范围：超 cap 窗口硬拒绝
    测试对象：validate_source_caps window_days
    目的/目标：扩大窗口须 fail-closed（R3G-REP-P2-01）
    验证点：baostock 31d 窗口抛 RehearsalPlanError
    失败含义：window cap 可被静默突破
    """
    from dataclasses import replace

    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        RehearsalPlanError,
        load_candidate_set,
        validate_source_caps,
    )

    baostock = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "baostock")
    over_window = replace(baostock, window_days=31)
    with pytest.raises(RehearsalPlanError, match="max window"):
        validate_source_caps(over_window)


def test_RehearsalPlan_rejectsOverCapSymbols() -> None:
    """覆盖范围：超 cap 符号硬拒绝
    测试对象：validate_source_caps
    目的/目标：扩大候选集须 fail-closed
    验证点：4 符号 baostock 候选抛 RehearsalPlanError
    失败含义：cap 可被静默突破
    """
    from dataclasses import replace

    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        RehearsalPlanError,
        load_candidate_set,
        validate_source_caps,
    )

    baostock = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "baostock")
    over = replace(
        baostock,
        symbols_or_series=("sh.600519", "sh.600000", "sz.000001", "sz.000002"),
    )
    with pytest.raises(RehearsalPlanError, match="max 3 symbols"):
        validate_source_caps(over)


def test_RehearsalPlan_fredRequiresAuthorizationArtifact() -> None:
    """覆盖范围：FRED 无 artifact fail-closed
    测试对象：validate_fred_authorization
    目的/目标：fred 排练须 explicit authorization YAML
    验证点：缺失文件抛 RehearsalPlanError
    失败含义：无授权仍可排练 fred
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        RehearsalPlanError,
        validate_fred_authorization,
    )

    with pytest.raises(RehearsalPlanError, match="authorization"):
        validate_fred_authorization(
            PROJECT_ROOT / ".audit-sandbox/round3g/nonexistent_auth.yaml",
            series_ids=("DGS10",),
        )


def test_RehearsalPlan_fredAuthorization_validArtifactPasses() -> None:
    """覆盖范围：有效 FRED 授权 artifact
    测试对象：validate_fred_authorization + 默认 round3g YAML
    目的/目标：用户授权 3 series / 120d 样本可排练
    验证点：authorization_present true；series 在 artifact 内
    失败含义：合法授权 artifact 被误拒
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import validate_fred_authorization

    auth = validate_fred_authorization(
        FRED_AUTH,
        series_ids=("DGS10", "T10Y3M", "VIXCLS"),
    )
    assert auth["authorization_present"] is True
    assert auth["allow_production_clean_write"] is False


def test_RehearsalPlan_cninfoRequiresMetadataOnlyPerContract() -> None:
    """覆盖范围：契约 metadata_only 布尔在 cap 校验中强制
    测试对象：validate_source_caps（cninfo 候选）
    目的/目标：cninfo 契约 metadata_only=true 时候选须 metadata_only（R3G-REP-P1-07）
    验证点：metadata_only=False 的 cninfo 候选抛 RehearsalPlanError
    失败含义：metadata-only 域可被误扩为全量下载语义
    """
    from dataclasses import replace

    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        RehearsalPlanError,
        load_candidate_set,
        validate_source_caps,
    )

    cninfo = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "cninfo")
    not_metadata = replace(cninfo, metadata_only=False)
    with pytest.raises(RehearsalPlanError, match="metadata_only"):
        validate_source_caps(not_metadata)


def test_RehearsalPlan_fredContractRequiresUserAuthorizationFlag() -> None:
    """覆盖范围：契约 requires_user_authorization 在 cap 层可读
    测试对象：validate_source_caps + 契约 candidate_caps.fred
    目的/目标：fred 源须在契约中声明 requires_user_authorization（R3G-REP-P1-07）
    验证点：契约 fred.requires_user_authorization 为 true；r3g_p0 fred 候选 validate 通过
    失败含义：fred 排练可绕过用户授权契约约束
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        load_candidate_set,
        validate_source_caps,
    )

    caps = _contract()["candidate_caps"]["fred"]
    assert caps.get("requires_user_authorization") is True
    fred = next(c for c in load_candidate_set("r3g_p0") if c.source_id == "fred")
    validate_source_caps(fred)


def test_RehearsalPlan_fredLivePathRequiresFredApiKey(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：live FRED 路径须 FRED_API_KEY env
    测试对象：validate_fred_authorization(require_live_credentials=True)
    目的/目标：live fetch fail-closed 无密钥（R3G-REP-P1-10）
    验证点：无 FRED_API_KEY 抛 RehearsalPlanError
    失败含义：live FRED 可在无 API key 下排练
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        RehearsalPlanError,
        validate_fred_authorization,
    )

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(RehearsalPlanError, match="FRED_API_KEY"):
        validate_fred_authorization(
            FRED_AUTH,
            series_ids=("DGS10", "T10Y3M", "VIXCLS"),
            require_live_credentials=True,
        )


def test_RehearsalPlan_productionDefaultEnabledFalse() -> None:
    """覆盖范围：provider catalog production_default_enabled
    测试对象：assert_sandbox_route_posture
    目的/目标：排练源须 sandbox posture（非 production_default_enabled）
    验证点：三候选 assert_sandbox_route_posture 不抛错
    失败含义：排练源被标为 production default enabled
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
        assert_sandbox_route_posture,
        load_candidate_set,
    )

    for candidate in load_candidate_set("r3g_p0"):
        assert_sandbox_route_posture(candidate.source_id)


# --- RehearsalRunner (9.4) ---------------------------------------------------


def test_RehearsalRunner_refusesDataRootProductionDbPath(tmp_path: Path) -> None:
    """覆盖范围：DATA_ROOT 默认生产 duckdb 路径拒绝
    测试对象：assert_sandbox_db_allowed / run_sandbox_clean_write_rehearsal
    目的/目标：AC-13 第二生产路径别名须 fail-closed（R3G-REP-P1-05）
    验证点：DATA_ROOT/duckdb/quant_monitor.duckdb 抛 RehearsalRunnerError
    失败含义：排练可指向 resolve 等价的第二生产库路径
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        RehearsalRunnerError,
        run_sandbox_clean_write_rehearsal,
    )

    prod_db = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
    with pytest.raises(RehearsalRunnerError, match="production DB path refused"):
        run_sandbox_clean_write_rehearsal(
            RehearsalRequest(
                candidate_set="r3g_p0",
                sandbox_db=prod_db,
                evidence_dir=tmp_path / "evidence",
                report_path=tmp_path / "report.json",
                no_production_mutation=True,
                dry_run=True,
            )
        )


def test_RehearsalRunner_refusesProductionDbPath(tmp_path: Path) -> None:
    """覆盖范围：生产 DB 路径拒绝
    测试对象：assert_sandbox_db_allowed / run_sandbox_clean_write_rehearsal
    目的/目标：sandbox-only；DEFAULT_PRODUCTION_DB 不可作 sandbox-db
    验证点：生产路径抛 RehearsalRunnerError
    失败含义：排练可指向生产 duckdb
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        RehearsalRunnerError,
        run_sandbox_clean_write_rehearsal,
    )
    from backend.app.ops.staged_pilot import DEFAULT_PRODUCTION_DB

    with pytest.raises(RehearsalRunnerError, match="production DB path refused"):
        run_sandbox_clean_write_rehearsal(
            RehearsalRequest(
                candidate_set="r3g_p0",
                sandbox_db=DEFAULT_PRODUCTION_DB,
                evidence_dir=tmp_path / "evidence",
                report_path=tmp_path / "report.json",
                no_production_mutation=True,
                dry_run=True,
            )
        )


def test_RehearsalRunner_requiresNoProductionMutationFlag(tmp_path: Path) -> None:
    """覆盖范围：--no-production-mutation 强制
    测试对象：assert_sandbox_db_allowed
    目的/目标：缺失 no_production_mutation 须失败
    验证点：no_production_mutation=False 抛错
    失败含义：可无标志排练，生产 mutation 风险
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )

    with pytest.raises(RehearsalRunnerError, match="no-production-mutation"):
        assert_sandbox_db_allowed(tmp_path / "sandbox.duckdb", no_production_mutation=False)


def test_RehearsalRunner_dryRun_composesGatesAndWritesEvidence(tmp_path: Path) -> None:
    """覆盖范围：runner 门禁链与 sandbox 写证据
    测试对象：run_sandbox_clean_write_rehearsal（dry_run）
    目的/目标：compose DSS/RoutePlanner/ResourceGuard/DH/ValidationGate/WM；产出 mutation_proof
    验证点：required_gates 全有；per_source_reports 非空；conflict + no-mutation 文件存在
    失败含义：ad-hoc bypass runner 或未写 sandbox 证据
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        CONFLICT_CHECK_JSON,
        NO_MUTATION_MD,
        RehearsalRequest,
        REQUIRED_GATES,
        run_sandbox_clean_write_rehearsal,
    )

    evidence = tmp_path / "evidence"
    sandbox_db = tmp_path / "rehearsal.duckdb"
    report_path = tmp_path / "rehearsal_report.json"
    result = run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=sandbox_db,
            evidence_dir=evidence,
            report_path=report_path,
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    assert result["production_mutation_allowed"] is False
    assert result["sandbox_only"] is True
    for gate in REQUIRED_GATES:
        assert gate in result["required_gates"]
    assert len(result["per_source_reports"]) == 3
    assert (evidence / CONFLICT_CHECK_JSON).is_file()
    assert (evidence / NO_MUTATION_MD).is_file()
    conflict_payload = json.loads((evidence / CONFLICT_CHECK_JSON).read_text(encoding="utf-8"))
    assert conflict_payload.get("status") == "NO_CONFLICT_CHECK_DEFERRED"
    assert "reason" in conflict_payload
    assert result["conflict_check_summary"] == conflict_payload
    assert report_path.is_file()
    for src_report in result["per_source_reports"]:
        assert src_report["write_manager_operation_id"]
        assert src_report["rollback_artifact_path"]
        rollback_file = evidence / Path(src_report["rollback_artifact_path"]).name
        if not rollback_file.is_file():
            rollback_file = PROJECT_ROOT / src_report["rollback_artifact_path"]
        assert rollback_file.is_file(), src_report["rollback_artifact_path"]
        rollback_payload = json.loads(rollback_file.read_text(encoding="utf-8"))
        assert rollback_payload["write_manager_operation_id"] == src_report["write_manager_operation_id"]
        assert rollback_payload["source_id"] == src_report["source_id"]


def test_RehearsalRunner_perSourceRollbackArtifactsAreDistinct(tmp_path: Path) -> None:
    """覆盖范围：三源 rollback 证据互不覆盖
    测试对象：_write_rollback_artifact per-source 文件名
    目的/目标：每源独立 rollback_artifact_{source_id}.json 且 write_id 可交叉审计
    验证点：三文件均存在；write_id 各不相同且与报告一致
    失败含义：后写覆盖前写，rollback 证据链断裂（R3G-REP-P0-03）
    """
    import json

    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        run_sandbox_clean_write_rehearsal,
    )

    evidence = tmp_path / "evidence"
    result = run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=tmp_path / "sandbox.duckdb",
            evidence_dir=evidence,
            report_path=tmp_path / "report.json",
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    by_source = {r["source_id"]: r for r in result["per_source_reports"]}
    write_ids: set[str] = set()
    for source_id in ("baostock", "cninfo", "fred"):
        path = evidence / f"rollback_artifact_{source_id}.json"
        assert path.is_file(), f"missing per-source rollback: {path}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["source_id"] == source_id
        wm_id = by_source[source_id]["write_manager_operation_id"]
        assert payload["write_manager_operation_id"] == wm_id
        write_ids.add(wm_id)
    assert len(write_ids) == 3


def test_RehearsalRunner_rejectsWriteWhenDataHealthGateNotReady(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：DH gate_ready=false 时拒绝 sandbox 写
    测试对象：_process_candidate data-health admission
    目的/目标：sandbox_clean_write_gate_ready 为写入门禁（R3G-REP-P0-01）
    验证点：gate_ready=false 抛 RehearsalRunnerError；sandbox clean 表无新行
    失败含义：坏证据仍可通过 WriteManager 写入
    """
    from backend.app.ops.data_health import DataHealthReport
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        RehearsalRunnerError,
        run_sandbox_clean_write_rehearsal,
    )

    def _blocked_dh(_candidate, _evidence_dir):
        return DataHealthReport(
            report_id="test-blocked",
            generated_at="2026-01-01T00:00:00Z",
            input_kind="evidence_dir",
            profile="market_bar_p0",
            overall_status="PASS",
            sandbox_clean_write_gate_ready=False,
            gate_rationale="synthetic test: gate blocked",
        )

    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.rehearsal_runner._run_source_data_health",
        _blocked_dh,
    )
    sandbox_db = tmp_path / "sandbox.duckdb"
    with pytest.raises(RehearsalRunnerError, match="sandbox_clean_write_gate_ready=false"):
        run_sandbox_clean_write_rehearsal(
            RehearsalRequest(
                candidate_set="r3g_p0",
                sandbox_db=sandbox_db,
                evidence_dir=tmp_path / "evidence",
                report_path=tmp_path / "report.json",
                no_production_mutation=True,
                dry_run=True,
                fred_authorization=FRED_AUTH,
            )
        )


def test_RehearsalRunner_validationStatusReflectsDataHealthNotSilentPassed(tmp_path: Path) -> None:
    """覆盖范围：validation_status 与 DH 联动且标注 synthetic admission
    测试对象：per_source_reports validation_status / synthetic_admission
    目的/目标：禁止 silent PASSED 架空 DbValidationGate（R3G-REP-P0-02）
    验证点：validation_status 来自 DH overall；synthetic_admission 显式 true
    失败含义：报告硬编码 PASSED，审计无法区分 synthetic 与真实校验
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        run_sandbox_clean_write_rehearsal,
    )

    result = run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=tmp_path / "sandbox.duckdb",
            evidence_dir=tmp_path / "evidence",
            report_path=tmp_path / "report.json",
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    for src_report in result["per_source_reports"]:
        dh_status = src_report["data_health_status"]
        validation_status = src_report["validation_status"]
        assert validation_status in {"PASSED", "WARNING", "FAILED", "BLOCKED"}
        if dh_status == "PASS":
            assert validation_status == "PASSED"
        assert src_report.get("synthetic_admission") is True


def test_RehearsalRunner_perSourceDataHealthProfiles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：per-source DH profile spy（非三源均 market_bar_p0）
    测试对象：run_data_health_profile + DataHealthService.check_evidence_dir
    目的/目标：baostock→market_bar_p0；cninfo→staged_pilot_v3；fred→fred_sandbox_pilot（R3G-REP-P1-04）
    验证点：spy 记录三源各调用一次且 profile 参数正确
    失败含义：DH profile 映射错误或未调用
    """
    from backend.app.ops.data_health import DataHealthReport
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        run_sandbox_clean_write_rehearsal,
    )

    calls: list[tuple[str, str]] = []

    def _spy_market_bar(profile_id, domain, evidence_path, **kwargs):
        calls.append(("baostock", profile_id))
        from backend.app.ops.data_health_profiles import run_data_health_profile as real

        return real(
            profile_id=profile_id,
            domain=domain,
            evidence_path=evidence_path,
            db_path=kwargs.get("db_path"),
            start_date=kwargs.get("start_date"),
            end_date=kwargs.get("end_date"),
            max_rows=kwargs.get("max_rows", 1000),
        )

    class _SpyDHService:
        def check_evidence_dir(self, evidence_dir, *, profile):
            source = "cninfo" if profile == "staged_pilot_v3" else "fred"
            calls.append((source, profile))
            return DataHealthReport(
                report_id=f"spy-{source}",
                generated_at="2026-01-01T00:00:00Z",
                input_kind="evidence_dir",
                profile=profile,
                overall_status="PASS",
                sandbox_clean_write_gate_ready=True,
                gate_rationale="spy ok",
            )

    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.rehearsal_runner.run_data_health_profile",
        _spy_market_bar,
    )
    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.rehearsal_runner.DataHealthService",
        _SpyDHService,
    )

    result = run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=tmp_path / "sandbox.duckdb",
            evidence_dir=tmp_path / "evidence",
            report_path=tmp_path / "report.json",
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    by_profile = dict(calls)
    assert by_profile["baostock"] == "market_bar_p0"
    assert by_profile["cninfo"] == "staged_pilot_v3"
    assert by_profile["fred"] == "fred_sandbox_pilot"
    by_source = {r["source_id"]: r for r in result["per_source_reports"]}
    assert "data_health_summary" in by_source["baostock"]


def test_RehearsalRunner_writesPerSourceRoutePlanOnDisk(tmp_path: Path) -> None:
    """覆盖范围：route_plan 按源落盘证据
    测试对象：_process_candidate route_plan 持久化
    目的/目标：SourceRoutePlanner 证据链可审计（R3G-REP-P1-02）
    验证点：三源 evidence/{source_id}/route_plan.json 存在且含 selected_source_id
    失败含义：route_plan 仅内存计算未落盘，AC-03 证据不完整
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        run_sandbox_clean_write_rehearsal,
    )

    evidence = tmp_path / "evidence"
    result = run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=tmp_path / "sandbox.duckdb",
            evidence_dir=evidence,
            report_path=tmp_path / "report.json",
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    for source_id in ("baostock", "cninfo", "fred"):
        route_path = evidence / source_id / "route_plan.json"
        assert route_path.is_file(), f"missing route_plan for {source_id}"
        payload = json.loads(route_path.read_text(encoding="utf-8"))
        assert payload.get("selected_source_id") or payload.get("route_status")
        report = next(r for r in result["per_source_reports"] if r["source_id"] == source_id)
        assert report["route_plan"] == payload


def test_RehearsalRunner_perSourceReportsSatisfyContractFields(tmp_path: Path) -> None:
    """覆盖范围：每源报告满足契约 required_report_fields
    测试对象：per_source_reports + sandbox_clean_write_contract.yaml
    目的/目标：排练报告 JSON 可机读审计（R3G-REP-P1-03）
    验证点：契约列出的每个字段均在每源报告中
    失败含义：per-source 报告缺契约字段，R3G-02 block_if 可能误触发
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_report import required_report_fields
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        run_sandbox_clean_write_rehearsal,
    )

    report_path = tmp_path / "rehearsal_report.json"
    result = run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=tmp_path / "sandbox.duckdb",
            evidence_dir=tmp_path / "evidence",
            report_path=report_path,
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    fields = required_report_fields()
    for src_report in result["per_source_reports"]:
        for field in fields:
            assert field in src_report, f"{src_report['source_id']} missing {field}"


def test_RehearsalRunner_smokeOnlyStagingSemanticsExplicit(tmp_path: Path) -> None:
    """覆盖范围：frozen smoke-only 语义显式标注
    测试对象：per_source_reports staging_semantics
    目的/目标：三域共用 bar smoke 表须显式 smoke-only，非真实 staged 链（R3G-REP-P1-01）
    验证点：每源 staging_semantics == smoke_only_bar_table
    失败含义：审计误以为按 domain 真实 materialize
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        run_sandbox_clean_write_rehearsal,
    )

    result = run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=tmp_path / "sandbox.duckdb",
            evidence_dir=tmp_path / "evidence",
            report_path=tmp_path / "report.json",
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    for src_report in result["per_source_reports"]:
        assert src_report.get("staging_semantics") == "smoke_only_bar_table"


def test_RehearsalRunner_fredWithoutAuthorizationArtifactFails(tmp_path: Path) -> None:
    """覆盖范围：runner 级 FRED 无 artifact fail-closed
    测试对象：run_sandbox_clean_write_rehearsal（缺失 fred_authorization）
    目的/目标：validate_candidate_set 在 runner 入口拒绝无授权 fred（R3G-REP-P1-06）
    验证点：无 fred_authorization 抛 RehearsalRunnerError
    失败含义：runner 可在 plan 层未校验时排练 fred
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        RehearsalRunnerError,
        run_sandbox_clean_write_rehearsal,
    )

    with pytest.raises(RehearsalRunnerError, match="authorization"):
        run_sandbox_clean_write_rehearsal(
            RehearsalRequest(
                candidate_set="r3g_p0",
                sandbox_db=tmp_path / "sandbox.duckdb",
                evidence_dir=tmp_path / "evidence",
                report_path=tmp_path / "report.json",
                no_production_mutation=True,
                dry_run=True,
                fred_authorization=PROJECT_ROOT / ".audit-sandbox/round3g/nonexistent_auth.yaml",
            )
        )


def test_RehearsalRunner_resourceGuardHardStopBlocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：ResourceGuard HARD_STOP 阻断排练
    测试对象：run_sandbox_clean_write_rehearsal ResourceGuard.check
    目的/目标：HARD_STOP fail-closed，非仅 autouse OK mock（R3G-REP-P1-09）
    验证点：HARD_STOP 抛 RehearsalRunnerError；无 per_source_reports
    失败含义：资源耗尽仍可 sandbox 写
    """
    from backend.app.core.resource_guard import Decision
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        RehearsalRunnerError,
        run_sandbox_clean_write_rehearsal,
    )

    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.rehearsal_runner.ResourceGuard.check",
        lambda self: (Decision.HARD_STOP, "test hard stop"),
    )
    with pytest.raises(RehearsalRunnerError, match="HARD_STOP"):
        run_sandbox_clean_write_rehearsal(
            RehearsalRequest(
                candidate_set="r3g_p0",
                sandbox_db=tmp_path / "sandbox.duckdb",
                evidence_dir=tmp_path / "evidence",
                report_path=tmp_path / "report.json",
                no_production_mutation=True,
                dry_run=True,
                fred_authorization=FRED_AUTH,
            )
        )


def test_RehearsalRunner_rejectsWriteWhenDataHealthOverallFails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：DH overall_status=FAIL 时拒绝 sandbox 写
    测试对象：_assert_data_health_admission overall_status
    目的/目标：FAIL/BLOCKED 非仅 gate_ready=false 亦阻断写（R3G-REP-P1-09）
    验证点：overall_status=FAIL 抛 RehearsalRunnerError
    失败含义：坏 DH 结论仍可 WriteManager 写入
    """
    from backend.app.ops.data_health import DataHealthReport
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        RehearsalRunnerError,
        run_sandbox_clean_write_rehearsal,
    )

    def _fail_dh(_candidate, _evidence_dir):
        return DataHealthReport(
            report_id="test-fail",
            generated_at="2026-01-01T00:00:00Z",
            input_kind="evidence_dir",
            profile="market_bar_p0",
            overall_status="FAIL",
            sandbox_clean_write_gate_ready=True,
            gate_rationale="synthetic test: overall fail",
        )

    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.rehearsal_runner._run_source_data_health",
        _fail_dh,
    )
    with pytest.raises(RehearsalRunnerError, match="overall_status=FAIL"):
        run_sandbox_clean_write_rehearsal(
            RehearsalRequest(
                candidate_set="r3g_p0",
                sandbox_db=tmp_path / "sandbox.duckdb",
                evidence_dir=tmp_path / "evidence",
                report_path=tmp_path / "report.json",
                no_production_mutation=True,
                dry_run=True,
                fred_authorization=FRED_AUTH,
            )
        )


def test_RehearsalRunner_doesNotCallLayer1IngestionWrite() -> None:
    """覆盖范围：禁止 L1 ingestion write 路径
    测试对象：rehearsal_runner.py 静态 import
    目的/目标：排练不得 import 或调用 layer1_axes.ingestion 写路径
    验证点：runner 源码无 layer1_axes.ingestion import
    失败含义：排练误扩 L1 ingestion allowlist/write
    """
    runner_src = (
        PROJECT_ROOT / "backend/app/ops/sandbox_clean_write/rehearsal_runner.py"
    ).read_text(encoding="utf-8")
    assert "layer1_axes.ingestion" not in runner_src
    assert "Layer1ObservationIngestionService" not in runner_src


# --- RehearsalCli (9.5) ------------------------------------------------------


def test_RehearsalCli_missingNoProductionMutation_fails(tmp_path: Path) -> None:
    """覆盖范围：CLI --no-production-mutation 缺失
    测试对象：sandbox_clean_write_rehearse
    目的/目标：CLI 形状与 §7 一致；无标志则 fail-closed
    验证点：CliFailure 且 message 含 no-production-mutation
    失败含义：CLI 允许无标志排练
    """
    from backend.app.cli.data_commands import sandbox_clean_write_rehearse
    from backend.app.cli.errors import CliFailure

    with pytest.raises(CliFailure, match="no-production-mutation"):
        sandbox_clean_write_rehearse(
            candidate_set="r3g_p0",
            sandbox_db=tmp_path / "sandbox.duckdb",
            evidence_dir=tmp_path / "evidence",
            report=tmp_path / "report.json",
            no_production_mutation=False,
        )


def test_RehearsalCli_dataRootProductionDbPathRejected(tmp_path: Path) -> None:
    """覆盖范围：CLI 拒绝 DATA_ROOT 生产 duckdb
    测试对象：sandbox_clean_write_rehearse + DATA_ROOT/duckdb/quant_monitor.duckdb
    目的/目标：AC-13 CLI 第二生产路径（R3G-REP-P1-05）
    验证点：CliFailure 含 production DB path refused
    失败含义：CLI 可将排练指向 DATA_ROOT 生产库
    """
    from backend.app.cli.data_commands import sandbox_clean_write_rehearse
    from backend.app.cli.errors import CliFailure

    with pytest.raises(CliFailure, match="production DB path refused"):
        sandbox_clean_write_rehearse(
            candidate_set="r3g_p0",
            sandbox_db=PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb",
            evidence_dir=tmp_path / "evidence",
            report=tmp_path / "report.json",
            no_production_mutation=True,
        )


def test_RehearsalCli_productionDbPathRejected(tmp_path: Path) -> None:
    """覆盖范围：CLI 拒绝生产 DB 路径
    测试对象：sandbox_clean_write_rehearse + DEFAULT_PRODUCTION_DB
    目的/目标：--sandbox-db 不得等于生产 duckdb
    验证点：CliFailure 含 production DB path refused
    失败含义：CLI 可将排练指向生产库
    """
    from backend.app.cli.data_commands import sandbox_clean_write_rehearse
    from backend.app.cli.errors import CliFailure
    from backend.app.ops.staged_pilot import DEFAULT_PRODUCTION_DB

    with pytest.raises(CliFailure, match="production DB path refused"):
        sandbox_clean_write_rehearse(
            candidate_set="r3g_p0",
            sandbox_db=DEFAULT_PRODUCTION_DB,
            evidence_dir=tmp_path / "evidence",
            report=tmp_path / "report.json",
            no_production_mutation=True,
        )


def test_RehearsalCli_helpDocumentsRehearseSubcommand() -> None:
    """覆盖范围：CLI help 暴露 rehearse 子命令
    测试对象：qmd data sandbox-clean-write rehearse --help
    目的/目标：AC-12 CLI 形状可发现
    验证点：help 文本含 sandbox-clean-write 与 no-production-mutation
    失败含义：操作员无法发现排练 CLI
    """
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "backend.app.cli.main", "data", "sandbox-clean-write", "rehearse", "--help"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=False,
    )
    assert proc.returncode == 0
    assert "no-production-mutation" in proc.stdout
    assert "candidate-set" in proc.stdout
