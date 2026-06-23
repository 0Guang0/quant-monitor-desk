"""第一层五轴指标规格加载与工程护栏测试。

覆盖范围：从 YAML 加载五轴指标定义、拦截不合规指标配置，
以及数据库迁移是否建好指标注册表与快照血缘表。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb
import pytest
import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.layer1_axes.axis_loader import (
    AxisSpecLoader,
    AxisSpecLoadError,
)
from backend.app.layer1_axes.guardrails import (
    AxisEngineeringGuardrailValidator,
    GuardrailViolationError,
)

MIGRATION_011 = "011_layer1_tables"

LAYER1_REGISTRY_TABLES = frozenset(
    {
        "axis_registry",
        "axis_indicator_registry",
        "axis_indicator_profile",
    }
)

AXIS_SNAPSHOT_LINEAGE_COLUMNS = frozenset(
    {
        "snapshot_id",
        "snapshot_type",
        "layer_id",
        "as_of_timestamp",
        "generated_at",
        "input_data_window_start",
        "input_data_window_end",
        "source_dataset_ids",
        "source_fetch_ids",
        "source_content_hashes",
        "rule_version",
        "code_version",
        "parameter_hash",
        "resource_profile",
        "upstream_snapshot_ids",
        "is_incremental",
        "rebuild_reason",
    }
)


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


def test_layer1Migration_createsRegistryTables(migrated_con, tmp_path) -> None:
    """覆盖范围：数据库迁移后，第一层指标注册相关表是否建好
    测试对象：apply_migrations 后的 SHOW TABLES 与 schema_version
    目的/目标：轴注册、指标注册、指标画像三张表必须随迁移落地
    验证点：三张 registry 表均存在；schema_version 含 011_layer1_tables
    失败含义：注册表缺失，第一层指标元数据无法入库
    """
    con = migrated_con(tmp_path)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert LAYER1_REGISTRY_TABLES.issubset(tables)
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert MIGRATION_011 in versions
    con.close()


def test_layer1Migration_createsSnapshotLineageTable(migrated_con, tmp_path) -> None:
    """覆盖范围：数据库迁移后，快照来源追溯表是否建好且列齐全
    测试对象：migration 011 的 axis_snapshot_lineage DDL
    目的/目标：血缘表须包含规则版本、来源指纹等契约要求的全部列
    验证点：表存在；契约列集合是实际列的子集
    失败含义：血缘表结构不全，快照追溯无法持久化
    """
    con = migrated_con(tmp_path)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "axis_snapshot_lineage" in tables
    cols = _table_columns(con, "axis_snapshot_lineage")
    assert AXIS_SNAPSHOT_LINEAGE_COLUMNS.issubset(cols)
    assert "rule_version" in cols
    con.close()


def _spec_root() -> Path:
    return PROJECT_ROOT / "specs/layer1_axes/restructured_axes_v1_1"


def _copy_specs(tmp_path: Path) -> Path:
    dest = tmp_path / "specs"
    shutil.copytree(_spec_root(), dest)
    return dest


def test_axisSpecLoader_loadsFiveAxes() -> None:
    """覆盖范围：从正式规格目录加载五轴指标定义是否成功
    测试对象：AxisSpecLoader.load
    目的/目标：必须解析环境、信用压力等五轴，且至少有一条可观测指标
    验证点：axis_ids 等于五轴集合；indicators 与 observable 均非空
    失败含义：轴规格加载失败，整个第一层面板无指标定义
    """
    result = AxisSpecLoader().load(spec_root=_spec_root())
    axis_ids = {a.axis_id for a in result.axes}
    assert axis_ids == {
        "ENVIRONMENT",
        "CREDIT_STRESS",
        "RISK_APPETITE",
        "LIQUIDITY",
        "SENTIMENT",
    }
    assert len(result.indicators) > 0
    observable = [i for i in result.indicators if i.is_observable]
    assert len(observable) > 0


def test_axisSpecLoader_missingIndicatorId_rejects(tmp_path: Path) -> None:
    """覆盖范围：指标 YAML 缺少指标编号时如何拒绝加载
    测试对象：AxisSpecLoader.load
    目的/目标：每条指标必须有唯一编号，缺编号必须拒绝整个加载
    验证点：pytest.raises(AxisSpecLoadError, match='indicator_id')
    失败含义：无编号指标仍加载，注册表与路由无法引用
    """
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    first = spec["modules"]["E0_money_quantity"]["indicators"][0]
    del first["indicator_id"]
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    with pytest.raises(AxisSpecLoadError, match="indicator_id"):
        AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])


def test_axisSpecLoader_missingQualityRules_rejects(tmp_path: Path) -> None:
    """覆盖范围：可观测指标的质量规则列表为空时如何拒绝
    测试对象：AxisSpecLoader.load
    目的/目标：可观测指标必须声明至少一条质量规则，空列表必须拒绝
    验证点：pytest.raises(AxisSpecLoadError, match='quality_rules')
    失败含义：无质量规则指标入库，数据质量校验器无规则可执行
    """
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    ind = spec["modules"]["E0_money_quantity"]["indicators"][0]
    ind["quality_rules"] = []
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    with pytest.raises(AxisSpecLoadError, match="quality_rules"):
        AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])


def test_axisSpecLoader_forbiddenIndicator_notObservable() -> None:
    """覆盖范围：标记为禁止使用的指标不得视为可观测
    测试对象：AxisSpecLoader.load 产出的 IndicatorDefinition
    目的/目标：禁止类指标的 is_observable 必须为 False，不能进入摄取白名单
    验证点：存在禁止指标；全部 is_observable 为 False
    失败含义：禁止指标进入摄取允许列表，产品红线被突破
    """
    result = AxisSpecLoader().load(spec_root=_spec_root())
    forbidden = [i for i in result.indicators if i.is_forbidden]
    assert forbidden, "expected at least one forbidden indicator from specs"
    assert all(not i.is_observable for i in forbidden)


def test_axisSpecLoader_blindspot_notObservable() -> None:
    """覆盖范围：标记为盲点的指标不得视为可观测
    测试对象：AxisSpecLoader.load 产出的 IndicatorDefinition
    目的/目标：盲点类指标的 is_observable 必须为 False，不能进入拉数路由
    验证点：存在盲点指标；全部 is_observable 为 False
    失败含义：盲点指标可被路由拉数，数据边界被突破
    """
    result = AxisSpecLoader().load(spec_root=_spec_root())
    blind = [i for i in result.indicators if i.is_blindspot]
    assert blind, "expected blindspot indicators"
    assert all(not i.is_observable for i in blind)


def test_axisEngineeringGuardrail_rejectsForbiddenSubstitute() -> None:
    """覆盖范围：使用规格明确禁止的替代指标时如何拒绝
    测试对象：AxisEngineeringGuardrailValidator.reject_forbidden_substitute
    目的/目标：工程护栏必须拒绝禁止替代指标，防止用错误代理数据
    验证点：pytest.raises(GuardrailViolationError, match='forbidden substitute')
    失败含义：禁止替代仍被接受，信用等轴会用到错误代理
    """
    result = AxisSpecLoader().load(spec_root=_spec_root())
    validator = AxisEngineeringGuardrailValidator(result.guardrails)
    credit = next(i for i in result.indicators if i.forbidden_substitutes)
    substitute = credit.forbidden_substitutes[0]
    with pytest.raises(GuardrailViolationError, match="forbidden substitute"):
        validator.reject_forbidden_substitute(credit, substitute_id=substitute)


def test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover() -> None:
    """覆盖范围：影子诊断类指标允许存在但不得抢占主信号
    测试对象：AxisEngineeringGuardrailValidator.assert_shadow_diagnostics_allowed
    目的/目标：影子诊断指标可存在，但必须标注仅诊断、不得接管主面板
    验证点：至少 3 个影子指标；role_notes 含 no_takeover 或 diagnostic_only
    失败含义：影子诊断越权成为主信号，数据源角色混乱
    """
    result = AxisSpecLoader().load(spec_root=_spec_root())
    shadows = [i for i in result.indicators if i.is_shadow and i.module == "shadow_diagnostics"]
    assert len(shadows) >= 3
    for ind in shadows:
        AxisEngineeringGuardrailValidator.assert_shadow_diagnostics_allowed(ind)
        assert "no_takeover" in ind.role_notes.lower() or ind.diagnostic_only


def test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles() -> None:
    """覆盖范围：影子指标不得把自身登记为主数据源
    测试对象：AxisSpecLoader 产出的影子指标定义
    目的/目标：影子仅作诊断标签，主数据源不能是 shadow 本身
    验证点：所有影子指标 primary_source 不是 shadow 且 dest_tag 为 SHADOW
    失败含义：影子进入主数据源角色，路由规划器会误选
    """
    result = AxisSpecLoader().load(spec_root=_spec_root())
    for ind in result.indicators:
        if ind.is_shadow:
            assert ind.primary_source.lower() != "shadow"
            assert ind.dest_tag == "SHADOW"


def test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly(tmp_path: Path) -> None:
    """覆盖范围：影子诊断组外的孤儿影子指标须显式标注仅诊断
    测试对象：AxisEngineeringGuardrailValidator.assert_shadow_outside_group_has_diagnostic_only
    目的/目标：非影子诊断模块的影子指标缺 diagnostic_only 标记应被拒绝
    验证点：孤儿影子触发 GuardrailViolationError(match='diagnostic_only')；diagnostic_only 仍为 False
    失败含义：组外影子无约束，可能悄悄进入主面板
    """
    root = _copy_specs(tmp_path)
    spec_path = root / "liquidity_axis" / "liquidity_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    spec["modules"]["L1_tightness"]["indicators"].append(
        {
            "indicator_id": "LIQ.SHADOW.ORPHAN_TEST",
            "display_name_cn": "orphan shadow",
            "plain_language_summary": "shadow outside group",
            "layer": "Shadow",
            "dest_tag": "SHADOW",
            "frequency": "daily",
            "primary_source": "none",
        }
    )
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    result = AxisSpecLoader().load(spec_root=root, enabled_axes=["liquidity"])
    orphan = next(i for i in result.indicators if i.indicator_id == "LIQ.SHADOW.ORPHAN_TEST")
    with pytest.raises(GuardrailViolationError, match="diagnostic_only"):
        AxisEngineeringGuardrailValidator.assert_shadow_outside_group_has_diagnostic_only(orphan)
    orphan_diag = next(
        (i for i in result.indicators if i.indicator_id == "LIQ.SHADOW.ORPHAN_TEST"),
    )
    assert orphan_diag.is_shadow
    # Fix by setting diagnostic_only — loader should mark it
    assert not orphan_diag.diagnostic_only


def test_axisSpecLoader_emptySpecRoot_rejects(tmp_path: Path) -> None:
    """覆盖范围：规格目录为空、没有任何指标文件时如何拒绝
    测试对象：AxisSpecLoader.load
    目的/目标：没有指标规格文件时必须拒绝加载，不能假装成功
    验证点：pytest.raises(AxisSpecLoadError, match='missing indicator spec')
    失败含义：空目录仍「成功」加载，运行时才发现无指标可用
    """
    empty_root = tmp_path / "empty_specs"
    empty_root.mkdir()
    with pytest.raises(AxisSpecLoadError, match="missing indicator spec"):
        AxisSpecLoader().load(spec_root=empty_root, enabled_axes=["environment"])


def test_axisSpecLoader_allForbiddenAxis_registersNoneObservable(tmp_path: Path) -> None:
    """覆盖范围：整轴全部指标都标为禁止时如何加载
    测试对象：AxisSpecLoader.load
    目的/目标：指标仍可注册到目录，但无一可观测、不可进入摄取
    验证点：indicators 非空；全部 is_forbidden；无 is_observable
    失败含义：全禁止轴仍产出可观测指标，摄取门禁失效
    """
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    for mod in spec.get("modules", {}).values():
        for ind in mod.get("indicators", []):
            ind["status"] = "forbidden"
            ind["layer"] = "Forbidden"
            ind["dest_tag"] = "FORBIDDEN"
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    result = AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])
    assert len(result.indicators) > 0
    assert all(i.is_forbidden for i in result.indicators)
    assert not any(i.is_observable for i in result.indicators)


def test_axisSpecLoader_missingQualityRulesKey_appliesContractDefaults(tmp_path: Path) -> None:
    """覆盖范围：指标 YAML 省略质量规则键时如何套用默认规则
    测试对象：AxisSpecLoader.load
    目的/目标：缺键时应自动套用契约规定的四条默认质量规则
    验证点：loaded.quality_rules 等于四条默认规则元组
    失败含义：缺键导致空规则或加载失败，与轴契约不一致
    """
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    ind = spec["modules"]["E0_money_quantity"]["indicators"][0]
    indicator_id = ind["indicator_id"]
    ind.pop("quality_rules", None)
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    result = AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])
    loaded = next(i for i in result.indicators if i.indicator_id == indicator_id)
    assert loaded.quality_rules == (
        "MISSING_VALUE",
        "STALE_DATA",
        "INSUFFICIENT_HISTORY",
        "SOURCE_SWITCHED",
    )


def test_axisSpecLoader_observableIndicators_matchContractFields() -> None:
    """覆盖范围：可观测指标的契约必填字段是否完整
    测试对象：AxisSpecLoader.load 产出的可观测指标与画像
    目的/目标：频率、单位、主数据源等定义字段与中文摘要均不能为空
    验证点：每条可观测指标的 profile 与 definition_fields 均满足非空
    失败含义：缺字段指标进入注册表，界面与校验器运行时崩溃
    """
    result = AxisSpecLoader().load(spec_root=_spec_root())
    observable = [i for i in result.indicators if i.is_observable]
    assert observable, "expected observable indicators"
    profiles_by_id = {p.indicator_id: p for p in result.profiles}
    definition_fields = {
        "frequency",
        "unit",
        "primary_source",
        "validation_source",
        "fallback_policy",
    }
    for ind in observable:
        profile = profiles_by_id[ind.indicator_id]
        assert profile.plain_language_summary
        assert profile.display_name_cn
        assert ind.layer_tag
        for field in definition_fields:
            assert getattr(ind, field, None) not in (None, ""), (
                f"{ind.indicator_id} missing contract field {field!r}"
            )


def test_axisSpecLoader_rejectsSpecRootOutsideAllowedRoots() -> None:
    """覆盖范围：规格目录不在项目白名单内时如何拒绝加载
    测试对象：AxisSpecLoader.load
    目的/目标：项目外任意目录不得作为规格来源，防止加载未审计配置
    验证点：pytest.raises(AxisSpecLoadError, match='spec_root')
    失败含义：路径白名单失效，可加载未审计的外部 YAML
    """
    evil_root = (PROJECT_ROOT.resolve().parent.parent / "evil_layer1_specs_outside").resolve()
    with pytest.raises(AxisSpecLoadError, match="spec_root"):
        AxisSpecLoader().load(
            spec_root=evil_root,
            enabled_axes=["environment"],
        )


def test_axisSpecLoader_engineeringRules_documentProjectionMetadata() -> None:
    """覆盖范围：环境轴工程规则文件是否文档化投影元数据
    测试对象：AxisSpecLoader.load 产出的 guardrails.engineering_rules_path
    目的/目标：工程规则 YAML 须写明投影方法与源频率映射，供特征引擎对齐
    验证点：engineering_rules 文件文本含 projection_method 与 source_frequency_map
    失败含义：投影元数据未文档化，特征引擎无法对齐频率映射
    """
    result = AxisSpecLoader().load(spec_root=_spec_root(), enabled_axes=["environment"])
    env_guard = next(g for g in result.guardrails if g.axis_id == "ENVIRONMENT")
    assert env_guard.engineering_rules_path
    eng_path = PROJECT_ROOT / env_guard.engineering_rules_path
    text = eng_path.read_text(encoding="utf-8")
    assert "projection_method" in text
    assert "source_frequency_map" in text
