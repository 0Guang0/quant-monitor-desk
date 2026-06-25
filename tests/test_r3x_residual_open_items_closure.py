"""R3X 残余开放项闭环回归（PROMPT_15）。

覆盖范围：路由阻断、生产 fetch 注入、write_mode fail-closed、适配器注册、
编排器延期 API、Layer1 解读禁词与 .gitignore 密钥模式等 ADV 审计项。
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.adapters import _ADAPTER_TYPES
from backend.app.datasources.exceptions import AdapterConfigurationError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.service import DataSourceService, _default_operation
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteRequest
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine, InterpretationRejectedError
from backend.app.validators.source_conflict import CONFLICT_DOMAIN_ALIASES, SourceConflictValidator
from tests.contract_gate_support import PROJECT_ROOT, load_yaml
from tests.db_helpers import create_test_write_manager
from tests.service_path_support import production_route_planner

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"

# ponytail: SSOT for PROMPT_15 archived execute evidence (α-3 backfill)
PROMPT15_ARCHIVE_EVIDENCE = (
    PROJECT_ROOT
    / ".trellis/tasks/archive/2026-06/fix-round3-r3x-residual-open-items-closure/execute-evidence"
)
PROMPT15_EVIDENCE_INDEX = PROMPT15_ARCHIVE_EVIDENCE / "closed_claim_evidence_index.yaml"


def _migrated_write_manager(tmp_path: Path, *, db_name: str = "wm.duckdb"):
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    db = tmp_path / db_name
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    return create_test_write_manager(cm), cm


def test_advR3xRoute001_validationOnlyPrimaryBlocked() -> None:
    """覆盖范围：validation_only 源不得作为唯一 READY 主源（ADV-R3X-ROUTE-001）
    测试对象：SourceRoutePlanner 对 macro_supplementary 的路由
    目的/目标：akshare 仅校验角色时须阻断为 Primary
    验证点：route_status 在阻断集合内；selected_source_id=None；akshare skip_reason=validation_only_cannot_be_primary
    失败含义：仅校验源被误选为主源，生产数据血缘不可信
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="macro_supplementary",
        operation="fetch_macro_series",
        run_id="r3x-route-001",
        job_id="j3x-route-001",
    )
    assert plan.route_status in {"VALIDATION_ONLY_BLOCKED", "DISABLED_SOURCE", "NO_AVAILABLE_SOURCE"}
    assert plan.selected_source_id is None
    akshare = next(c for c in plan.candidates if c.source_id == "akshare")
    assert akshare.skip_reason == "validation_only_cannot_be_primary"


def test_advR3xRoute003_domainDisabledByDefault() -> None:
    """覆盖范围：domain_enabled_by_default=false 域的路由（ADV-R3X-ROUTE-003）
    测试对象：cn_equity_minute_bar 路由预览
    目的/目标：默认禁用域须返回 DISABLED_SOURCE 并带 DOMAIN_DISABLED_BY_DEFAULT 标记
    验证点：route_status=DISABLED_SOURCE；quality_flags 含 DOMAIN_DISABLED_BY_DEFAULT
    失败含义：默认关闭的分钟线域仍可路由，违背 staged pilot 策略
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="cn_equity_minute_bar",
        operation="fetch_minute_bar",
        run_id="r3x-route-003",
        job_id="j3x-route-003",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert "DOMAIN_DISABLED_BY_DEFAULT" in plan.quality_flags


def test_advR3xRoute004_validationRoleAddsQualityFlag() -> None:
    """覆盖范围：显式注入 Validation 候选时的质量标记（ADV-R3X-ROUTE-004）
    测试对象：SourceRoutePlanner.plan(extra_candidates)
    目的/目标：若选中 validation 源，须打 VALIDATION_SOURCE_USED 质量旗标
    验证点：选中 akshare 时 quality_flags 含 VALIDATION_SOURCE_USED
    失败含义：校验源被使用但无标记，下游无法识别非主源数据
    """
    registry = SourceRegistry()
    registry.load(SOURCE_REGISTRY)
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry

    planner = SourceRoutePlanner(
        source_registry=registry,
        capability_registry=SourceCapabilityRegistry(),
    )
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="r3x-route-004",
        job_id="j3x-route-004",
        extra_candidates=[("akshare", "Validation")],
    )
    if plan.selected_source_id == "akshare":
        assert "VALIDATION_SOURCE_USED" in plan.quality_flags


def test_advR3xService001_productionFetchRequiresFileRegistry(monkeypatch) -> None:
    """覆盖范围：生产 DataSourceService.fetch 依赖注入（ADV-R3X-SERVICE-001）
    测试对象：DataSourceService.fetch 无 fetch_port/file_registry
    目的/目标：生产路径不得静默回落到测试适配器
    验证点：抛出 AdapterConfigurationError 且消息含 fetch_port
    失败含义：生产 fetch 无端口仍执行，可能写脏数据或跳过审计
    """
    # ponytail: adapter-only; apply_migrations = prod-shaped log table; guard thresholds → test_resource_guard.py
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service = DataSourceService()
    req = FetchRequest(
        run_id="r3x-svc",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
    )
    con = duckdb.connect(":memory:")
    apply_migrations(con)  # ponytail: prod-shaped con so guard WARN log does not CatalogException
    with pytest.raises(AdapterConfigurationError, match="fetch_port"):
        service.fetch(req, con=con, job_id=None)


def test_advR3xConflict001_domainAliasThresholdLookup() -> None:
    """覆盖范围：源冲突校验的域别名阈值（ADV-R3X-CONFLICT-001）
    测试对象：SourceConflictValidator._threshold_for
    目的/目标：cn_equity_daily_bar 应别名到 market_bar_1d 的 close 阈值
    验证点：threshold 非空；CONFLICT_DOMAIN_ALIASES 含该域
    失败含义：日 K 域冲突判定用错阈值，多源一致性误判
    """
    validator = SourceConflictValidator()
    threshold = validator._threshold_for("cn_equity_daily_bar", "close")
    assert threshold is not None
    assert "cn_equity_daily_bar" in CONFLICT_DOMAIN_ALIASES


def test_advA2_009_tdxPytdxRegisteredInFactory() -> None:
    """覆盖范围：适配器工厂 TDX 注册（ADV-A2-009）
    测试对象：_ADAPTER_TYPES
    目的/目标：tdx_pytdx 已注册；默认启用仍由 registry 控制不变
    验证点：'tdx_pytdx' in _ADAPTER_TYPES
    失败含义：TDX 适配器未接入工厂，018C 探针无法实例化
    """
    assert "tdx_pytdx" in _ADAPTER_TYPES


def test_advA2_004_cninfoSupportsFilingsDomains() -> None:
    """覆盖范围：CninfoAdapter 声明的数据域（ADV-A2-004）
    测试对象：CninfoAdapter.supported_domains
    目的/目标：cninfo 须支持 cn_filings 与 cn_pdf_reports
    验证点：两域均在 supported_domains
    失败含义：公告/财报域无法经 cninfo 路由， filings 链路断裂
    """
    from backend.app.datasources.adapters.cninfo import CninfoAdapter

    assert "cn_filings" in CninfoAdapter.supported_domains
    assert "cn_pdf_reports" in CninfoAdapter.supported_domains


def test_advA1_001_writeRequestRequiresDataDomain(tmp_path: Path) -> None:
    """覆盖范围：WriteRequest 必填 data_domain（ADV-A1-001）
    测试对象：WriteManager.write 空 data_domain
    目的/目标：无数据域的写入请求须在门禁层拒绝
    验证点：抛出 ValueError 且消息含 data_domain
    失败含义：空域写入可落库，血缘与审计无法追溯域
    """
    wm, _cm = _migrated_write_manager(tmp_path)
    req = WriteRequest(
        run_id="r",
        job_id="j",
        target_table="t",
        staging_table="s",
        write_mode="append_only",
        primary_keys=("id",),
        validation_report_id="stub-pass-x",
        source_used="baostock",
        data_domain="",
    )
    with pytest.raises(ValueError, match="data_domain"):
        wm.write(req)


def test_advA5_001_gitignoreSecretPatterns() -> None:
    """覆盖范围：.gitignore 密钥文件模式（ADV-A5-001）
    测试对象：仓库根 .gitignore
    目的/目标：须忽略 *.secret、*.key、credentials.* 等敏感后缀
    验证点：三模式均出现在 gitignore 正文
    失败含义：密钥文件可能被误提交，供应链安全风险
    """
    text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("*.secret", "*.key", "credentials.*"):
        assert pattern in text


def test_advA6_004_viteApiProxy() -> None:
    """覆盖范围：前端开发代理配置（ADV-A6-004）
    测试对象：frontend/vite.config.ts
    目的/目标：Vite dev server 须将 /api/* 代理到 backend
    验证点：配置文本含 '"/api"' 代理段
    失败含义：本地开发 API 请求未转发，前后端联调断裂
    """
    text = (PROJECT_ROOT / "frontend/vite.config.ts").read_text(encoding="utf-8")
    assert '"/api"' in text


def test_advR3xL1_002_interpretationRejectsForbiddenTerms() -> None:
    """覆盖范围：Layer1 解读模板禁用词（ADV-R3X-L1-002 / ADV-A4-002）
    测试对象：AxisInterpretationEngine.build_interpretation
    目的/目标：含「建议买入」等禁词的模板须拒绝写路径
    验证点：抛出 InterpretationRejectedError
    失败含义：投资建议类措辞可进入解读层，合规与审计风险
    """
    from tests.test_layer1_interpretation import _history

    engine = AxisInterpretationEngine()
    hist = _history("ENV-E1-EFFR", 5)
    feat = AxisFeatureEngine(min_obs_required=3, window_len=10).compute_features(
        as_of=hist[-1].as_of_timestamp,
        observations=[hist[-1]],
        history=hist,
    )[0]
    with pytest.raises(InterpretationRejectedError):
        engine.build_interpretation(
            as_of=hist[-1].as_of_timestamp,
            features=[feat],
            templates={feat.indicator_id: "建议买入"},
        )


def test_advR3xCap002_tdxPytdxFactoryParity() -> None:
    """覆盖范围：TDX 与 QMT 工厂注册对等（ADV-R3X-CAP-002）
    测试对象：_ADAPTER_TYPES
    目的/目标：tdx_pytdx 与 qmt_xtdata 均须在工厂注册
    验证点：两 source_id 均在 _ADAPTER_TYPES
    失败含义：某本地行情源未注册，路由选中后无法实例化
    """
    assert "qmt_xtdata" in _ADAPTER_TYPES
    assert "tdx_pytdx" in _ADAPTER_TYPES


def test_defaultOperation_coversAllDomainRoles() -> None:
    """覆盖范围：domain_roles 全键 _default_operation 映射
    测试对象：_default_operation
    目的/目标：注册表每个 domain_roles 键须有非空默认 operation
    验证点：all(_default_operation(k) for k in role_keys)
    失败含义：某域无默认 operation，服务层 fetch 无法自动选操作
    """
    registry = load_yaml(SOURCE_REGISTRY)
    role_keys = set((registry.get("domain_roles") or {}).keys())
    assert all(_default_operation(k) for k in role_keys)


def test_advR3xWrite002_unsupportedWriteModeRejected(tmp_path) -> None:
    """覆盖范围：未实现 write_mode 拒绝（ADV-R3X-WRITE-002）
    测试对象：WriteManager.write(write_mode=replace_partition)
    目的/目标：合约列出但未实现的写模式须 fail-closed
    验证点：抛出 ValueError 且消息含 not implemented
    失败含义：未实现模式静默成功或部分写入，数据完整性风险
    """
    wm, _cm = _migrated_write_manager(tmp_path, db_name="wm2.duckdb")
    req = WriteRequest(
        run_id="r",
        job_id="j",
        target_table="t",
        staging_table="s",
        write_mode="replace_partition",
        primary_keys=("id",),
        validation_report_id="stub-pass-x",
        source_used="baostock",
        data_domain="cn_equity_daily_bar",
    )
    with pytest.raises(ValueError, match="not implemented"):
        wm.write(req)


def test_advA2_002_healthCheckStub(tmp_path: Path) -> None:
    """覆盖范围：BaseDataAdapter.health_check 结构化 stub（ADV-A2-002）
    测试对象：create_test_adapter(...).health_check()
    目的/目标：健康检查须返回 STUB_OK 及 supported_domains 列表
    验证点：status=STUB_OK；含 cn_equity_daily_bar
    失败含义：运维探针无法获取结构化健康报告，接口契约破裂
    """
    from backend.app.datasources.adapters import create_test_adapter
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    adapter = create_test_adapter("baostock", registry, tmp_path)
    report = adapter.health_check()
    assert report["status"] == "STUB_OK"
    assert "cn_equity_daily_bar" in report["supported_domains"]


def test_advR3xCap001_compatibilityMapEmpty() -> None:
    """覆盖范围：遗留适配器域兼容映射清空（ADV-R3X-CAP-001）
    测试对象：ADAPTER_DOMAIN_COMPATIBILITY_MAP
    目的/目标：适配器域须完全来自 registry，不得靠硬编码兼容表
    验证点：ADAPTER_DOMAIN_COMPATIBILITY_MAP == {}
    失败含义：双轨域定义残留，路由与能力注册可能不一致
    """
    from backend.app.datasources.capability_registry import ADAPTER_DOMAIN_COMPATIBILITY_MAP

    assert ADAPTER_DOMAIN_COMPATIBILITY_MAP == {}


def test_advA3_016_orchestratorDeferredRunners(tmp_path) -> None:
    """覆盖范围：编排器 full_load 延期 API 显式 deferred 错误（ADV-A3-016 / VR-SYNC-002）
    测试对象：DataSyncOrchestrator.run_full_load
    目的/目标：未实现的全量批跑入口须抛 DeferredJobTypeError，调用方不得误以为已实现
    验证点：pytest.raises(DeferredJobTypeError) 且 code=DEFERRED_JOB_TYPE；match 含 run_full_load
    失败含义：调用方误以为 full_load 已可用，生产 job 静默无效果（dq/ra 见 test_b3f_quality_runners.py）
    """
    from datetime import date

    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.sync.contract import DEFERRED_JOB_TYPE_CODE, DeferredJobTypeError
    from backend.app.sync.jobs import SyncJobSpec
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    db = tmp_path / "orch.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id="r",
        job_id="j",
        job_type="full_load",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 2),
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    with pytest.raises(DeferredJobTypeError, match="run_full_load") as exc_info:
        orch.run_full_load(spec)
    assert exc_info.value.code == DEFERRED_JOB_TYPE_CODE


def test_advA1_012_minStagingRowsEnforced(tmp_path) -> None:
    """覆盖范围：空 staging 写入拒绝（ADV-A1-012 / ADV-A1-015）
    测试对象：WriteManager.write 对空 staging 表
    目的/目标：clean 写入前须有最小 staging 行数
    验证点：抛出 ValueError 且消息含 minimum
    失败含义：空批次可写 clean，产生无意义审计与空洞分区
    """
    wm, cm = _migrated_write_manager(tmp_path, db_name="empty-stg.duckdb")
    with cm.writer() as con:
        con.execute("CREATE TABLE t (id INTEGER)")
        con.execute("CREATE TABLE s (id INTEGER)")
    req = WriteRequest(
        run_id="r",
        job_id="j",
        target_table="t",
        staging_table="s",
        write_mode="append_only",
        primary_keys=("id",),
        validation_report_id="stub-pass-x",
        source_used="baostock",
        data_domain="cn_equity_daily_bar",
    )
    with pytest.raises(ValueError, match="minimum"):
        wm.write(req)


def test_r3yPrompt15_closedClaimEvidenceIndexMapsToGreenTxt() -> None:
    """覆盖范围：PROMPT_15 closed-claim 与 execute *-green.txt 可审计映射（R3Y-PROMPT15-EVID-001）
    测试对象：归档 execute-evidence/closed_claim_evidence_index.yaml 与 *-green.txt
    目的/目标：73 项 Master Checklist 闭合声称须各有 green 证据与 pytest 交叉引用，不得仅 merge_gate 自述
    验证点：索引存在；每组 green 文件存在且含 passed/EXIT:0；伞测 18 条均被索引；checklist 行数=73
    失败含义：PROMPT_15 全量闭合仍不可审计，AUD-01 F-01  hygiene 未关闭
    """
    assert PROMPT15_EVIDENCE_INDEX.is_file(), "closed_claim_evidence_index.yaml missing"
    index = load_yaml(PROMPT15_EVIDENCE_INDEX)
    assert index.get("checklist_total") == 73

    groups = index.get("groups") or []
    assert groups, "evidence index must list checklist groups"

    green_names: set[str] = set()
    indexed_claims: set[str] = set()
    umbrella_tests_in_index: set[str] = set()

    for group in groups:
        green_rel = group.get("green")
        assert green_rel, f"group {group.get('id')} missing green file"
        green_path = PROMPT15_ARCHIVE_EVIDENCE / green_rel
        assert green_path.is_file(), f"missing green evidence: {green_rel}"
        body = green_path.read_text(encoding="utf-8")
        assert "passed" in body.lower() or "exit:0" in body.lower(), (
            f"{green_rel} lacks pytest pass marker"
        )
        green_names.add(green_rel)

        for claim_id in group.get("claim_ids") or []:
            indexed_claims.add(str(claim_id))

        for test_name in group.get("umbrella_tests") or []:
            umbrella_tests_in_index.add(str(test_name))

    assert len(indexed_claims) == 73, f"expected 73 claim_ids, got {len(indexed_claims)}"

    # ponytail: 73 = 75 checklist rows − R3/R4 merged into DOC-001 / A6-003 aliases
    expected_claims = {
        "ADV-R3X-ROUTE-001", "ADV-R3X-ROUTE-002", "ADV-R3X-ROUTE-003", "ADV-R3X-ROUTE-004",
        "ADV-R3X-SYNC-001", "ADV-R3X-SYNC-002", "ADV-R3X-SYNC-003",
        "ADV-R3X-WRITE-001", "ADV-R3X-WRITE-002", "ADV-R3X-VALID-001",
        "ADV-R3X-CONFLICT-001", "ADV-R3X-L1-001", "ADV-R3X-L1-002",
        "ADV-R3X-PILOT-001", "ADV-R3X-PILOT-002", "ADV-R3X-SERVICE-001",
        "ADV-R3X-STAGE-001", "ADV-R3X-CAP-001", "ADV-R3X-CAP-002",
        "ADV-A1-001", "ADV-A1-002", "ADV-A1-003", "ADV-A1-004", "ADV-A1-005",
        "ADV-A1-006", "ADV-A1-007", "ADV-A1-008", "ADV-A1-009", "ADV-A1-010",
        "ADV-A1-011", "ADV-A1-012", "ADV-A1-013", "ADV-A1-014", "ADV-A1-015",
        "ADV-A2-001", "ADV-A2-002", "ADV-A2-003", "ADV-A2-004", "ADV-A2-005",
        "ADV-A2-006", "ADV-A2-007", "ADV-A2-008", "ADV-A2-009", "ADV-A2-010",
        "ADV-A2-011", "ADV-A2-012",
        "ADV-A3-001", "ADV-A3-002", "ADV-A3-003", "ADV-A3-004", "ADV-A3-005",
        "ADV-A3-006", "ADV-A3-007", "ADV-A3-008", "ADV-A3-009", "ADV-A3-010",
        "ADV-A3-011", "ADV-A3-012", "ADV-A3-013", "ADV-A3-014", "ADV-A3-015",
        "ADV-A3-016",
        "ADV-A5-001", "ADV-A5-002", "ADV-A6-001", "ADV-A6-003", "ADV-A6-004",
        "F-019-R01", "F-019-R02", "F-019-R03",
        "R1", "R2", "ADV-R3X-DOC-001",
    }
    assert indexed_claims == expected_claims, (
        f"claim_id set mismatch: missing={expected_claims - indexed_claims}, "
        f"extra={indexed_claims - expected_claims}"
    )
    assert "full-pytest-green.txt" in green_names

    expected_umbrella = {
        "test_advR3xRoute001_validationOnlyPrimaryBlocked",
        "test_advR3xRoute003_domainDisabledByDefault",
        "test_advR3xRoute004_validationRoleAddsQualityFlag",
        "test_advR3xService001_productionFetchRequiresFileRegistry",
        "test_advR3xConflict001_domainAliasThresholdLookup",
        "test_advA2_009_tdxPytdxRegisteredInFactory",
        "test_advA2_004_cninfoSupportsFilingsDomains",
        "test_advA1_001_writeRequestRequiresDataDomain",
        "test_advA5_001_gitignoreSecretPatterns",
        "test_advA6_004_viteApiProxy",
        "test_advR3xL1_002_interpretationRejectsForbiddenTerms",
        "test_advR3xCap002_tdxPytdxFactoryParity",
        "test_defaultOperation_coversAllDomainRoles",
        "test_advR3xWrite002_unsupportedWriteModeRejected",
        "test_advA2_002_healthCheckStub",
        "test_advR3xCap001_compatibilityMapEmpty",
        "test_advA3_016_orchestratorDeferredRunners",
        "test_advA1_012_minStagingRowsEnforced",
    }
    assert expected_umbrella <= umbrella_tests_in_index, (
        f"umbrella tests missing from index: {expected_umbrella - umbrella_tests_in_index}"
    )

    merge_gate = PROMPT15_ARCHIVE_EVIDENCE / "merge_gate_report.md"
    assert merge_gate.is_file(), "archived merge_gate_report.md missing"
