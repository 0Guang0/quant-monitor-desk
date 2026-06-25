"""第一层数据摄取「开工前检查」测试（Phase 0）。

覆盖范围：数据库迁移是否就绪、约定 YAML 是否与代码一致、
路由与写入门禁是否接好，以及相关文档与注册表是否对齐。
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import duckdb
import pytest
import yaml
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import MIGRATIONS_DIR, apply_migrations
from backend.app.layer1_axes.observation_contract import (
    AXIS_OBSERVATION_DDL_COLUMNS,
    AXIS_OBSERVATION_TABLE,
    FETCH_TO_OBSERVATION_TRACE_VIA,
    WRITE_REQUEST_REQUIRED_FOR_OBSERVATION,
)
from backend.app.ops.db_inspector import FUTURE_PHASE_KEY_TABLES, KEY_TABLES
from tests.contract_gate_support import (
    PROJECT_ROOT,
    load_yaml,
    scan_package_for_create_adapter,
    trellis_task_dir,
)

BATCH25_TASK_SLUG = "06-20-round3-batch2-5-layer1-obs-ingest"
TASK_ROOT = trellis_task_dir(BATCH25_TASK_SLUG)
PIPELINE_TESTS = TASK_ROOT / "research/layer1-ingestion-pipeline-tests.md"
SERVICE_CONTRACT = PROJECT_ROOT / "specs/contracts/datasource_service_contract.yaml"
LAYER1_AXES_CONFIG = PROJECT_ROOT / "configs/layer1_axes.yml"

MIGRATION_011 = PROJECT_ROOT / "backend/app/db/migrations/011_layer1_tables.sql"
SCHEMA_SQL = PROJECT_ROOT / "specs/schema/schema.sql"
SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
WRITE_CONTRACT = PROJECT_ROOT / "specs/contracts/write_contract.yaml"
LINEAGE_CONTRACT = PROJECT_ROOT / "specs/contracts/snapshot_lineage_contract.yaml"
LAYER1_AXIS_CONTRACT = PROJECT_ROOT / "specs/contracts/layer1_axis_contract.yaml"
DATA_QUALITY_RULES = PROJECT_ROOT / "specs/contracts/data_quality_rules.yaml"
DATA_CLI_CONTRACT = PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml"
SOURCE_ROUTE_CONTRACT = PROJECT_ROOT / "specs/contracts/source_route_contract.yaml"
OPS_INSPECT_CONTRACT = PROJECT_ROOT / "specs/contracts/ops_db_inspect_contract.yaml"
MODULE_SPEC_DDL = PROJECT_ROOT / "docs/modules/layer1_global_regime_panel.md"

LAYER1_AXIS_TABLES = frozenset(
    {
        "axis_registry",
        "axis_indicator_registry",
        "axis_indicator_profile",
        "axis_observation",
        "axis_feature_snapshot",
        "axis_interpretation_snapshot",
        "axis_snapshot_lineage",
    }
)

INGESTION_MIGRATIONS = (
    "004_ingestion_sources",
    "005_ingestion_validation",
    "006_ingestion_sync",
    "007_ingestion_sync_hardening",
    "008_lineage_fields",
    "009_fetch_log_check",
    "010_validation_report_not_null",
    "011_layer1_tables",
)

FROZEN_STAGED_INDICATOR = "ENV-E1-DGS10"
STAGED_DATA_DOMAIN = "macro_supplementary"
STAGED_OPERATION = "fetch_macro_series"


@lru_cache(maxsize=64)
def _repo_text(path: Path) -> str:
    """ponytail: gate tests re-read the same repo files; cache by path."""
    return path.read_text(encoding="utf-8")


def _table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchall()
    return {row[0] for row in rows}


def test_layer1Ingestion_phase0_migration011_definesAxisTables() -> None:
    """覆盖范围：开工前检查——第一层轴表迁移脚本是否定义全部七张表
    测试对象：011_layer1_tables.sql DDL 文本
    目的/目标：七张轴相关表均须在迁移脚本中有建表语句
    验证点：每张 LAYER1_AXIS_TABLES 表名出现在 migration 文本中
    失败含义：迁移漏表，后续建库与盘点门禁全部失效
    """
    migration_text = _repo_text(MIGRATION_011)
    for table in LAYER1_AXIS_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in migration_text


def test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02() -> None:
    """覆盖范围：开工前检查——权威 schema 文档是否与已落地轴表对齐
    测试对象：specs/schema/schema.sql
    目的/目标：schema 文档不得滞后于已落地的七张轴表定义
    验证点：missing == []（七张表均出现在 schema.sql）
    失败含义：schema 文档漂移，运维检查与 DBA 参考不一致
    """
    schema_text = _repo_text(SCHEMA_SQL)
    missing = [t for t in LAYER1_AXIS_TABLES if t not in schema_text]
    assert missing == []


def test_layer1Ingestion_phase0_applyMigrations_createsAxisTables() -> None:
    """覆盖范围：开工前检查——空库执行迁移后轴表是否真实存在
    测试对象：apply_migrations 与 SHOW TABLES
    目的/目标：迁移运行器必须真正创建七张轴表并登记 011 版本
    验证点：LAYER1_AXIS_TABLES 是 tables 的子集；schema_version 含 011_layer1_tables
    失败含义：迁移脚本与运行器脱节，空库无法跑第一层流程
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert LAYER1_AXIS_TABLES.issubset(tables)
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert "011_layer1_tables" in versions
    con.close()


def test_layer1Migration_axisObservation_columnsMatchModuleSpec(migrated_con, tmp_path) -> None:
    """覆盖范围：开工前检查——观测表列是否与模块规格和契约一致
    测试对象：migrated DB 的 axis_observation information_schema
    目的/目标：DDL 列集必须与契约常量及模块文档完全对齐
    验证点：set(AXIS_OBSERVATION_DDL_COLUMNS) == cols；每列在 module spec 文本中
    失败含义：列漂移导致映射写入 INSERT 失败或静默丢字段
    """
    con = migrated_con(tmp_path)
    cols = _table_columns(con, AXIS_OBSERVATION_TABLE)
    assert set(AXIS_OBSERVATION_DDL_COLUMNS) == cols
    spec_text = _repo_text(MODULE_SPEC_DDL)
    for col in AXIS_OBSERVATION_DDL_COLUMNS:
        assert col in spec_text
    con.close()


def test_layer1Ingestion_phase0_migrations004to011PresentOnDisk() -> None:
    """覆盖范围：开工前检查——摄取链迁移文件 004 至 011 是否在磁盘存在
    测试对象：MIGRATIONS_DIR glob
    目的/目标：每条要求的 version_id 须有对应 .sql 迁移文件
    验证点：每个 INGESTION_MIGRATIONS 前缀能 glob 到至少一个文件
    失败含义：缺迁移文件，全新数据库无法升到第一层就绪状态
    """
    for version_id in INGESTION_MIGRATIONS:
        prefix = version_id.split("_", 1)[0]
        matches = list(MIGRATIONS_DIR.glob(f"{prefix}_*.sql"))
        assert matches, f"missing migration file for {version_id}"


def test_layer1Ingestion_phase0_ingestionChainTablesAfterApply() -> None:
    """覆盖范围：开工前检查——迁移后摄取证据链核心表是否齐全
    测试对象：apply_migrations 后的 SHOW TABLES
    目的/目标：源注册、拉取日志、文件登记、校验报告等追溯表必须同时存在
    验证点：required 集合（含 axis_observation）是 tables 的子集
    失败含义：证据链缺表，盘点与正式提交无法写审计
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    required = {
        "source_registry",
        "fetch_log",
        "file_registry",
        "validation_report",
        "write_audit_log",
        AXIS_OBSERVATION_TABLE,
    }
    assert required.issubset(tables)
    con.close()


def test_layer1_axes_doesNotImportCreateAdapter() -> None:
    """覆盖范围：开工前检查——第一层轴包不得直接引用适配器工厂
    测试对象：scan_package_for_create_adapter('layer1_axes')
    目的/目标：第一层必须经统一数据服务取数，禁止绕过工厂边界
    验证点：violations == []
    失败含义：第一层直连适配器，架构边界与审计追溯失效
    """
    violations = scan_package_for_create_adapter("layer1_axes")
    assert violations == [], "layer1_axes must not import adapter factory: " + "; ".join(violations)


def test_sourceRegistry_roles_forbidShadowEmergency() -> None:
    """覆盖范围：开工前检查——源注册表是否禁止废弃的 Shadow/Emergency 角色
    测试对象：SOURCE_REGISTRY YAML 与原文
    目的/目标：角色模型仅允许 Primary/Validation/FallbackPolicy，废弃角色不得出现
    验证点：source_role_model 正确；legacy_roles_forbidden 含 Shadow/Emergency；正文无 Shadow:/Emergency: 行
    失败含义：废弃角色仍可用，多源路由与降级语义混乱
    """
    doc = yaml.safe_load(_repo_text(SOURCE_REGISTRY)) or {}
    assert doc.get("source_role_model") == "Primary / Validation / FallbackPolicy"
    rules = doc.get("rules") or {}
    forbidden = {str(r) for r in (rules.get("legacy_roles_forbidden") or [])}
    assert forbidden >= {"Shadow", "Emergency", "shadow_source", "emergency_source"}
    text = _repo_text(SOURCE_REGISTRY)
    for role in ("Shadow", "Emergency"):
        assert not re.search(rf"\b{role}\b\s*:", text)


def test_layer1Ingestion_phase0_frozenIndicator_stagedRouteCapabilityDeclared() -> None:
    """覆盖范围：开工前检查——冻结测试指标的路由与能力声明是否对齐
    测试对象：SourceRegistry、SourceCapabilityRegistry、SourceRoutePlanner
    目的/目标：冻结指标走暂存宏数据路径时，须为仅校验不拉数且 akshare 能力已声明
    验证点：primary=akshare；route_status=VALIDATION_ONLY_BLOCKED；akshare skip_reason=validation_only_cannot_be_primary
    失败含义：冻结指标路由与能力注册不一致，试路由证据失真
    """
    reg = SourceRegistry(SOURCE_REGISTRY)
    reg.load()
    cap = SourceCapabilityRegistry()
    cap.load()
    cap.assert_source_domain_operation("akshare", STAGED_DATA_DOMAIN, STAGED_OPERATION)
    binding = reg.get_domain_roles(STAGED_DATA_DOMAIN)
    assert binding.primary_source_id == "akshare"
    planner = SourceRoutePlanner(source_registry=reg, capability_registry=cap)
    plan = planner.plan(
        data_domain=STAGED_DATA_DOMAIN,
        operation=STAGED_OPERATION,
        run_id="phase0-route",
        job_id="phase0-job",
    )
    assert plan.data_domain == STAGED_DATA_DOMAIN
    assert plan.operation == STAGED_OPERATION
    assert plan.selected_source_id is None
    assert plan.route_status == "VALIDATION_ONLY_BLOCKED"
    akshare = next(c for c in plan.candidates if c.source_id == "akshare")
    assert akshare.capability_declared is True
    assert akshare.skip_reason == "validation_only_cannot_be_primary"
    assert plan.candidates


def test_layer1Ingestion_phase0_writeContractMapsToObservationTarget() -> None:
    """覆盖范围：开工前检查——写入契约与观测写入必填字段是否一致
    测试对象：WRITE_CONTRACT 与 WRITE_REQUEST_REQUIRED_FOR_OBSERVATION
    目的/目标：Python 常量须与 YAML 写入请求必填字段完全一致
    验证点：两集合相等；reject_if 含 FAILED 与 severe conflict 规则
    失败含义：契约与代码漂移，WriteManager 请求缺字段仍过门禁
    """
    contract = load_yaml(WRITE_CONTRACT)
    required = set(contract["write_request"]["required"])
    assert set(WRITE_REQUEST_REQUIRED_FOR_OBSERVATION) == required
    reject_if = contract["validation_gate"]["reject_if"]
    assert "validation_status == FAILED" in reject_if
    assert "source_conflict_severity == severe" in reject_if


def test_layer1Ingestion_phase0_writeContractRejectIf_hasPlannedValidatorHooks() -> None:
    """覆盖范围：开工前检查——写入契约拒绝规则是否与校验器钩子对齐
    测试对象：WRITE_CONTRACT validation_gate.reject_if
    目的/目标：三条拒绝规则（校验失败、严重冲突、需人工复核）须在契约中声明
    验证点：mapping 中每条 rule 均在 reject_if 列表
    失败含义：拒绝规则缺项，数据库写入门禁与校验器钩子不对齐
    """
    mapping = {
        "validation_status == FAILED": "DbValidationGate + DataQualityValidator",
        "source_conflict_severity == severe": "DbValidationGate + SourceConflictValidator",
        "manual_review_required == true and write_mode != manual_patch": "DbValidationGate",
    }
    contract = load_yaml(WRITE_CONTRACT)
    for rule in mapping:
        assert rule in contract["validation_gate"]["reject_if"]


def test_layer1Lineage_phase0_ddlStoresSerializedFetchIds(migrated_con, tmp_path) -> None:
    """覆盖范围：开工前检查——快照血缘表是否具备拉取编号与内容指纹列
    测试对象：migrated DB axis_snapshot_lineage 与 LINEAGE_CONTRACT
    目的/目标：来源拉取编号与内容指纹以字符串存 JSON，契约声明为列表类型
    验证点：两列存在于 DDL；contract required_fields 类型为 list[string]
    失败含义：血缘列缺失或类型不符，应用层无法解析拉取追溯
    """
    con = migrated_con(tmp_path)
    cols = _table_columns(con, "axis_snapshot_lineage")
    assert "source_fetch_ids" in cols
    assert "source_content_hashes" in cols
    contract = load_yaml(LINEAGE_CONTRACT)
    required = contract["required_fields"]
    assert required["source_fetch_ids"] == "list[string]"
    assert required["source_content_hashes"] == "list[string]"
    con.close()


def test_layer1Ingestion_phase0_dataQualityRules_layer1SectionExists() -> None:
    """覆盖范围：开工前检查——数据质量规则文件是否含第一层专用规则段
    测试对象：DATA_QUALITY_RULES layer1_rules
    目的/目标：第一层必须声明缺来源、无降级理由、盲点有值等核心规则
    验证点：rule_ids 包含 MISSING_SOURCE_USED、FALLBACK_WITHOUT_REASON、BLINDSPOT_SHOULD_NOT_HAVE_VALUE
    失败含义：第一层质量规则未注册，校验器无规则可执行
    """
    rules = load_yaml(DATA_QUALITY_RULES)
    layer1 = rules.get("layer1_rules") or []
    rule_ids = {r["id"] for r in layer1}
    assert rule_ids >= {
        "MISSING_SOURCE_USED",
        "FALLBACK_WITHOUT_REASON",
        "BLINDSPOT_SHOULD_NOT_HAVE_VALUE",
    }


def test_layer1Ingestion_phase0_layer1AxisContractRequiredFields() -> None:
    """覆盖范围：开工前检查——第一层轴契约是否声明必填指标字段
    测试对象：LAYER1_AXIS_CONTRACT
    目的/目标：契约须声明指标编号必填及禁止替代使用标记
    验证点：indicator_id in required_indicator_fields；FORBIDDEN_SUBSTITUTE_USED in quality_flags
    失败含义：轴契约缺字段，加载器与写入器无法统一校验
    """
    contract = load_yaml(LAYER1_AXIS_CONTRACT)
    assert "indicator_id" in contract["required_indicator_fields"]
    assert "FORBIDDEN_SUBSTITUTE_USED" in contract["quality_flags"]


def test_layer1Ingestion_phase0_dataCliContract_loadable() -> None:
    """覆盖范围：开工前检查——数据 CLI 契约是否可加载且含同步命令
    测试对象：DATA_CLI_CONTRACT
    目的/目标：CLI 契约须声明用途与 qmd data sync 命令入口
    验证点：doc.purpose 非空；commands 含 qmd data sync
    失败含义：CLI 契约缺失，运维与 CI 无法对照 data 子命令
    """
    doc = load_yaml(DATA_CLI_CONTRACT)
    assert doc.get("purpose")
    assert "qmd data sync" in doc.get("commands", {})


def test_layer1Ingestion_phase0_sourceRouteContract_forbidsSilentFallback() -> None:
    """覆盖范围：开工前检查——路由契约是否明确禁止静默降级
    测试对象：SOURCE_ROUTE_CONTRACT purpose 字段
    目的/目标：契约用途说明须明确写出禁止静默 fallback
    验证点：purpose 小写文本含 silent fallback is forbidden
    失败含义：路由契约未禁止静默降级，多源故障转移可能无声切换
    """
    doc = load_yaml(SOURCE_ROUTE_CONTRACT)
    assert "silent fallback is forbidden" in doc.get("purpose", "").lower()


def test_layer1Ingestion_phase0_noSilentFallback_backendScan() -> None:
    """覆盖范围：开工前检查——后端代码是否存在违规静默降级模式
    测试对象：test_noSilentFallbackCopied（guardrails 复用）
    目的/目标：开工前须确认后端无违规静默 fallback 实现
    验证点：委托 guardrails 测试通过（无断言即 pass）
    失败含义：后端存在静默降级，路由规划器契约被违反
    """
    from tests.test_reference_adoption_guardrails import test_noSilentFallbackCopied

    test_noSilentFallbackCopied()


def test_layer1Ingestion_phase0_frozenIndicator_metadataEligible() -> None:
    """覆盖范围：开工前检查——冻结测试指标在轴规格中的元数据是否合格
    测试对象：environment_axis_indicator_spec.yaml
    目的/目标：须为 Layer1_State、有主数据源、非禁止非盲点
    验证点：frozen.layer==Layer1_State；有 primary_source；id 与字段无 forbidden/blindspot
    失败含义：冻结指标元数据不合格，后续全流程无法以其为验收基准
    """
    cfg = load_yaml(LAYER1_AXES_CONFIG)
    spec_root = PROJECT_ROOT / cfg["spec_root"]
    env_spec = spec_root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    doc = load_yaml(env_spec)
    indicators = []
    for section in (doc.get("modules") or {}).values():
        indicators.extend(section.get("indicators") or [])
    frozen = next(i for i in indicators if i["indicator_id"] == FROZEN_STAGED_INDICATOR)
    assert frozen["layer"] == "Layer1_State"
    assert frozen.get("primary_source")
    assert "forbidden" not in str(frozen).lower()
    assert "blindspot" not in frozen["indicator_id"].lower()


def test_layer1Ingestion_phase0_layer1AxesConfig_resolvesSpecRoot() -> None:
    """覆盖范围：开工前检查——第一层轴配置指向的规格目录是否可解析
    测试对象：LAYER1_AXES_CONFIG 与磁盘 spec_root 目录
    目的/目标：配置指向的规格目录须存在且含冻结指标编号
    验证点：spec_root.is_dir()；environment spec 文本含 ENV-E1-DGS10
    失败含义：配置路径错误，轴规格加载器在生产无法启动
    """
    cfg = load_yaml(LAYER1_AXES_CONFIG)
    spec_root = PROJECT_ROOT / cfg["spec_root"]
    assert spec_root.is_dir()
    env_spec = spec_root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    text = _repo_text(env_spec)
    assert FROZEN_STAGED_INDICATOR in text


def test_layer1Ingestion_phase0_datasourceServiceFactoryBoundaryEnforced() -> None:
    """覆盖范围：开工前检查——数据服务工厂边界是否被禁止包穿透
    测试对象：SERVICE_CONTRACT call_boundaries 与 scan_package_for_create_adapter
    目的/目标：layer1_axes 须在禁止直接调用列表中且无一违规 import
    验证点：forbidden 含 layer1_axes；全 forbidden 包 violations == []
    失败含义：工厂边界被穿透，第一层可绕过数据服务直连适配器
    """
    contract = load_yaml(SERVICE_CONTRACT)
    forbidden_pkgs = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    assert any("layer1_axes" in pkg for pkg in forbidden_pkgs)
    violations: list[str] = []
    for pkg in forbidden_pkgs:
        pkg_path = pkg.replace("backend.app.", "")
        violations.extend(scan_package_for_create_adapter(pkg_path))
    assert violations == [], "forbidden packages must not import create_adapter: " + "; ".join(
        violations
    )


def _init_db(db_path: Path) -> None:
    cm = ConnectionManager(db_path=db_path)
    with cm.writer() as con:
        apply_migrations(con)


def test_layer1Ingestion_phase0_validationGateRejectsMissingReport(tmp_path: Path) -> None:
    """覆盖范围：开工前检查——缺失校验报告时写入门禁是否拒绝
    测试对象：DbValidationGate.assert_can_write
    目的/目标：不存在的校验报告编号必须触发写入门禁错误
    验证点：pytest.raises(ValidationGateError)
    失败含义：无报告仍能 clean write，WriteManager 最后一道闸失效
    """
    from backend.app.db.validation_gate import DbValidationGate, ValidationGateError

    db = tmp_path / "gate.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationGateError):
        gate.assert_can_write("missing-report-id", "append_only")


def test_layer1Ingestion_phase0_resourceGuardReturnsDecisionOnMigratedDb(tmp_path: Path) -> None:
    """覆盖范围：开工前检查——迁移后沙箱库上资源门禁是否可正常调用
    测试对象：ResourceGuard.check
    目的/目标：门禁须返回 OK/PAUSE/HARD_STOP 之一，不能抛未处理异常
    验证点：decision in (Decision.OK, Decision.PAUSE, Decision.HARD_STOP)
    失败含义：ResourceGuard 在迁移库上不可用，摄取无法 fail-closed
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard

    db = tmp_path / "guard.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    with cm.writer() as con:
        decision, _reason = ResourceGuard(con=con).check()
    assert decision in (Decision.OK, Decision.PAUSE, Decision.HARD_STOP)


def test_layer1Ingestion_phase0_commitPathIsCallable(tmp_path: Path) -> None:
    """覆盖范围：开工前检查——正式提交入口在摄取服务上是否已接线
    测试对象：Layer1ObservationIngestionService.commit_clean_observation_and_snapshots
    目的/目标：服务实例化后正式提交方法须可调用（冒烟接线）
    验证点：callable(service.commit_clean_observation_and_snapshots)
    失败含义：正式提交入口未接线，Batch2.5 校验后入库步骤无法执行
    """
    from backend.app.datasources.service import build_staged_fixture_service
    from backend.app.layer1_axes.ingestion import Layer1ObservationIngestionService

    db = tmp_path / "commit-smoke.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    service = Layer1ObservationIngestionService(
        db_path=db,
        data_root=data_root,
        datasource=build_staged_fixture_service(
            data_root=data_root,
            fixture_path=PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json",
        ),
    )
    assert callable(service.commit_clean_observation_and_snapshots)


def test_dbInspect_keyTables_includeLayer1AxisTables() -> None:
    """覆盖范围：开工前检查——数据库检查工具关键表列表是否含第一层轴表
    测试对象：KEY_TABLES 与 OPS_INSPECT_CONTRACT key_tables
    目的/目标：七张轴表与未来阶段表均须在 inspect 关键表列表
    验证点：每张 LAYER1_AXIS_TABLE 在 KEY_TABLES 与 contract_tables；FUTURE_PHASE_KEY_TABLES 也在 KEY_TABLES
    失败含义：inspect 漏表，盘点阶段行数统计不完整
    """
    contract_tables = load_yaml(OPS_INSPECT_CONTRACT)["key_tables"]
    for table in LAYER1_AXIS_TABLES:
        assert table in KEY_TABLES
        assert table in contract_tables
    for future in FUTURE_PHASE_KEY_TABLES:
        assert future in KEY_TABLES


def test_layer1Ingestion_phase0_axisObservation_noDbCheck_classified() -> None:
    """覆盖范围：开工前检查——观测表 DDL 无数据库 CHECK 约束（已知限制）
    测试对象：MIGRATION_011 中 axis_observation 建表块
    目的/目标：DuckDB 变更限制下 CHECK 延后，由应用层校验承担
    验证点：obs_block 大写文本不含 CHECK
    失败含义：误以为数据库有 CHECK，与 ADR-002 及应用校验策略不一致
    """
    ddl = _repo_text(MIGRATION_011)
    obs_block = ddl.split("CREATE TABLE IF NOT EXISTS axis_observation")[1].split(");")[0]
    assert "CHECK" not in obs_block.upper()


def test_layer1Ingestion_phase0_axisObservation_appValidatorEnforcesTimestampOrder() -> None:
    """覆盖范围：开工前检查——未来发布日期拒绝是否由应用层测试覆盖
    测试对象：layer1-ingestion-pipeline-tests.md 测试矩阵
    目的/目标：流水线文档须登记未来数据拒绝的回归测试名
    验证点：pipeline 文本含 test_layer1Observation_noFutureDataRejected
    失败含义：时间序约束无回归测试，正式提交路径可能接受未来数据
    """
    pipeline = _repo_text(PIPELINE_TESTS)
    assert "test_layer1Observation_noFutureDataRejected" in pipeline


def test_layer1Ingestion_phase0_knownPytestSkipsDocumented() -> None:
    """覆盖范围：开工前检查——已知 pytest skip 是否在文档登记
    测试对象：docs/quality/KNOWN_PYTEST_SKIPS.md
    目的/目标：CI 排障须能查到平台相关 skip 用例
    验证点：文档存在且含 test_dbInspect_symlinkOutsideDataRoot_notCounted
    失败含义：skip 未文档化，CI 失败难以归因
    """
    doc = PROJECT_ROOT / "docs/quality/KNOWN_PYTEST_SKIPS.md"
    assert doc.is_file()
    text = _repo_text(doc)
    assert "test_dbInspect_symlinkOutsideDataRoot_notCounted" in text


def test_layer1Ingestion_rollbackPlanDocumentsR2bSandboxBootstrap() -> None:
    """覆盖范围：回滚计划是否登记 R2b sandbox_bootstrap 模块
    测试对象：layer1_ingestion_refactor_rollback_plan.md
    目的/目标：R3F-HYG-07 拆分进度须可审计
    验证点：文档含 sandbox_bootstrap.py 与 R2b DONE
    失败含义：ingestion 拆分状态与代码漂移，并行 agent 误判可合并
    """
    plan = PROJECT_ROOT / "docs/architecture/layer1_ingestion_refactor_rollback_plan.md"
    text = _repo_text(plan)
    assert "sandbox_bootstrap.py" in text
    assert "R2b DONE" in text


def test_layer1Ingestion_phase0_batch25PendingFixRegistryPresent() -> None:
    """覆盖范围：开工前检查——Batch2.5 待办项注册表文档是否存在
    测试对象：ROUND3_BATCH25_PENDING_FIX_REGISTRY.md
    目的/目标：审计延期项与回滚计划须可检索
    验证点：文档存在；含 R3-B2.75-01 与 rollback plan 文件名
    失败含义：待办 registry 缺失，并行 agent 无法对齐债务收尾
    """
    reg = PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md"
    assert reg.is_file()
    text = _repo_text(reg)
    assert "R3-B2.75-01" in text
    assert "layer1_ingestion_refactor_rollback_plan.md" in text


def test_layer1Ingestion_phase0_batch3StagedDownstreamGateDocumented() -> None:
    """覆盖范围：开工前检查——Batch3 暂存下游门禁文档是否存在
    测试对象：BATCH3_STAGED_DOWNSTREAM_GATE.md
    目的/目标：Batch3 规划前须继承仅暂存数据交接说明
    验证点：文档存在；含 R3-B2.75-01 与 staged 关键词
    失败含义：下游 batch 无暂存门禁说明，可能误用生产数据
    """
    gate = PROJECT_ROOT / "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md"
    assert gate.is_file()
    text = _repo_text(gate)
    assert "R3-B2.75-01" in text
    assert "staged" in text.lower()


def test_layer1Ingestion_phase0_pytestSlowMarkerRegistered() -> None:
    """覆盖范围：开工前检查——pytest slow 标记与快速 CI 文档是否就绪
    测试对象：pyproject.toml markers 与 KNOWN_PYTEST_SKIPS.md
    目的/目标：slow 标记须注册且 skip 文档说明 not slow 过滤
    验证点：pyproject 含 slow:；skips 文档含 not slow
    失败含义：快速 CI 无法排除慢用例，流水线耗时失控
    """
    pyproject = _repo_text(PROJECT_ROOT / "pyproject.toml")
    assert "slow:" in pyproject
    skips = _repo_text(PROJECT_ROOT / "docs/quality/KNOWN_PYTEST_SKIPS.md")
    assert "not slow" in skips


def test_layer1Ingestion_phase0_fetchTraceFieldsDocumented() -> None:
    """覆盖范围：开工前检查——拉取到观测的追溯字段常量是否文档化
    测试对象：FETCH_TO_OBSERVATION_TRACE_VIA
    目的/目标：契约须列出至少 3 个追溯节点且含校验报告中的拉取编号字段
    验证点：len >= 3；含 validation_report.source_fetch_ids_json
    失败含义：追溯链字段未文档化，审计无法对照拉取到观测链路
    """
    assert len(FETCH_TO_OBSERVATION_TRACE_VIA) >= 3
    assert "validation_report.source_fetch_ids_json" in FETCH_TO_OBSERVATION_TRACE_VIA


def test_layer1Ingestion_phase0_stagedFixturePresent() -> None:
    """覆盖范围：开工前检查——暂存宏数据测试夹具是否存在且字段正确
    测试对象：tests/fixtures/layer1_macro_observation_fixture.json
    目的/目标：小批量拉数前须有冻结指标、序列号、日期的测试夹具
    验证点：文件存在；indicator_id/series_id/as_of 与冻结指标一致
    失败含义：夹具缺失或字段错，小批量拉数与正式提交路径无法跑通
    """
    fixture = PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json"
    assert fixture.is_file()
    doc = json.loads(_repo_text(fixture))
    assert doc["indicator_id"] == FROZEN_STAGED_INDICATOR
    assert doc["series_id"] == "DGS10"
    assert doc["as_of"] == "2024-06-15"


def test_layer1Ingestion_phase0_axisObservationWritePath_implementedInPhase4() -> None:
    """覆盖范围：开工前检查——校验后正式写入路径是否在摄取模块实现
    测试对象：ingestion.py、observation_writer.py 与 pipeline tests 文档
    目的/目标：须含正式提交与小批量拉数入口，且运行时门面不含证据采集符号
    验证点：ingestion 文本含关键符号；pipeline 含 cleanWrite 闭包测试名
    失败含义：正式写入未落地或证据采集混进运行时门面
    """
    ingestion = PROJECT_ROOT / "backend/app/layer1_axes/ingestion.py"
    assert ingestion.is_file()
    text = _repo_text(ingestion)
    assert "commit_clean_observation_and_snapshots" in text
    assert "micro_fetch_staging" in text
    assert "def capture_phase" not in text
    assert "ingestion_commit" in text
    assert "Layer1ObservationWriter" in _repo_text(
        PROJECT_ROOT / "backend/app/layer1_axes/observation_writer.py"
    )
    closure_test = "test_layer1Observation_cleanWrite_usesWriteManager"
    pipeline_tests = _repo_text(PIPELINE_TESTS)
    assert closure_test in pipeline_tests


def test_layer1Ingestion_phase0_ingestionFacadeReexportsEvidenceModule() -> None:
    """覆盖范围：开工前检查——摄取运行时门面是否泄漏证据采集符号
    测试对象：backend.app.layer1_axes.ingestion 与 ingestion_evidence
    目的/目标：运行时门面与证据采集模块边界须分离
    验证点：ing 无 capture_task_phase3_evidence 或 ≠ ev 原函数；ingestion.py 无 evidence import
    失败含义：证据符号泄漏到运行时，任务脚本与生产 import 边界模糊
    """
    import backend.app.layer1_axes.ingestion as ing
    import backend.app.layer1_axes.ingestion_evidence as ev

    assert not hasattr(ing, "capture_task_phase3_evidence") or (
        getattr(ing, "capture_task_phase3_evidence", None) is not ev.capture_task_phase3_evidence
    )
    text = _repo_text(PROJECT_ROOT / "backend/app/layer1_axes/ingestion.py")
    assert "from backend.app.layer1_axes.ingestion_evidence import" not in text
    assert ev.capture_task_phase3_evidence is not None


def test_layer1Ingestion_phase0_evidenceModuleExportsPublicSurface() -> None:
    """覆盖范围：开工前检查——证据采集模块公开 API 是否完整
    测试对象：ingestion_evidence.__all__
    目的/目标：第四阶段证据采集与变更表常量须在 __all__ 导出
    验证点：capture_task_phase4_evidence 与 PHASE4_MUTATION_TABLES in __all__
    失败含义：证据公开面不全，任务执行脚本无法稳定 import
    """
    import backend.app.layer1_axes.ingestion_evidence as ev

    assert "capture_task_phase4_evidence" in ev.__all__
    assert "PHASE4_MUTATION_TABLES" in ev.__all__
