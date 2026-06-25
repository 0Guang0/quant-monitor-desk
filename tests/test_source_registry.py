"""数据源注册表加载与 DB 同步测试（Batch A）。

覆盖范围：YAML 校验、域角色、legacy 角色拒绝、sync_to_db 幂等与墓碑。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from backend.app.datasources.source_registry import (
    DomainDisabledError,
    DomainNotAllowedError,
    DomainRoleBinding,
    InvalidRegistryError,
    LegacyRoleError,
    SCHEMA_CHECK_LICENSE_TYPES,
    SCHEMA_CHECK_SOURCE_TYPES,
    SourceDisabledError,
    SourceNotFoundError,
    SourceRegistry,
)


def test_load_validYaml_parsesPrimaryDomainRoles(registry_yaml_fixture):
    """覆盖范围：测试用配置里主数据源角色能否正确解析
    测试对象：SourceRegistry.load + get_domain_roles(market_bar_1d)
    目的/目标：日线行情域应能读出谁是主源，且返回结构化角色对象
    验证点：roles.primary_source_id=baostock；isinstance(roles, DomainRoleBinding)
    失败含义：fixture 域角色解析错误，Batch A 契约基线失效
    """
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    roles = reg.get_domain_roles("market_bar_1d")
    assert roles.primary_source_id == "baostock"
    assert isinstance(roles, DomainRoleBinding)


def test_defaultYaml_loadsFromRepoSeed():
    """覆盖范围：仓库种子 source_registry.yaml 加载
    测试对象：SourceRegistry() 默认路径 load
    目的/目标：cn_equity_daily_bar 主源 baostock、校验源 akshare
    验证点：primary/validation source_id；DomainRoleBinding 类型
    失败含义：生产种子配置损坏，全库路由默认源错误
    """
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("cn_equity_daily_bar")
    assert roles.primary_source_id == "baostock"
    assert roles.validation_source_id == "akshare"
    assert isinstance(roles, DomainRoleBinding)


def test_sourceTypeAndLicenseType_matchSchemaCheckEnums():
    """覆盖范围：source_registry.yaml 的 source_type/license_type 与 DB CHECK 枚举一致
    测试对象：SourceRegistry 默认 YAML 全量 source 记录
    目的/目标：新增数据源不能使用 schema.sql / migration 009 不允许的枚举值
    验证点：每个 source.source_type 和 source.license_type 均在 CHECK 白名单内
    失败含义：registry 可加载但同步 DB 或迁移约束会失败，数据源扩展不可发布
    """
    allowed_source_types = SCHEMA_CHECK_SOURCE_TYPES
    allowed_license_types = SCHEMA_CHECK_LICENSE_TYPES
    reg = SourceRegistry()
    reg.load()
    bad_source_types = {
        source_id: rec.source_type
        for source_id, rec in reg._sources.items()
        if rec.source_type not in allowed_source_types
    }
    bad_license_types = {
        source_id: rec.license_type
        for source_id, rec in reg._sources.items()
        if rec.license_type not in allowed_license_types
    }
    assert bad_source_types == {}
    assert bad_license_types == {}


def test_load_yamlWithShadowRole_raisesLegacyRoleError(bad_shadow_yaml):
    """覆盖范围：已废弃的 Shadow 角色名不得再出现在配置里
    测试对象：SourceRegistry.load（bad_shadow_yaml）
    目的/目标：旧版「影子源」角色已淘汰，加载时应直接报错拒绝
    验证点：pytest.raises(LegacyRoleError)
    失败含义：Shadow 回退路径复活，与 Round2.6 角色模型冲突
    """
    reg = SourceRegistry(bad_shadow_yaml)
    with pytest.raises(LegacyRoleError):
        reg.load()


def test_load_yamlWithEmergencyRole_raisesLegacyRoleError(bad_emergency_yaml):
    """覆盖范围：禁止 Emergency 域角色名
    测试对象：SourceRegistry.load（bad_emergency_yaml）
    目的/目标：Emergency 角色已废弃，加载须失败
    验证点：pytest.raises(LegacyRoleError)
    失败含义：紧急源隐式启用，绕过 capability 与审批
    """
    reg = SourceRegistry(bad_emergency_yaml)
    with pytest.raises(LegacyRoleError):
        reg.load()


def test_load_yamlWithTopLevelShadowSource_raisesLegacyRoleError(
    bad_top_level_shadow_source_yaml,
):
    """覆盖范围：顶层 shadow_source 配置段不得存在
    测试对象：SourceRegistry.load（bad_top_level_shadow_source_yaml）
    目的/目标：旧架构的顶层影子源块一旦出现在 YAML 里就应被拒绝
    验证点：pytest.raises(LegacyRoleError, match=shadow_source)
    失败含义：顶层 shadow 配置可加载，旧架构渗透
    """
    reg = SourceRegistry(bad_top_level_shadow_source_yaml)
    with pytest.raises(LegacyRoleError, match="shadow_source"):
        reg.load()


def test_load_yamlWithTopLevelEmergencySource_raisesLegacyRoleError(
    bad_top_level_emergency_source_yaml,
):
    """覆盖范围：顶层 emergency_source 键禁止
    测试对象：SourceRegistry.load（bad_top_level_emergency_source_yaml）
    目的/目标：emergency_source 顶层键已废弃
    验证点：pytest.raises(LegacyRoleError, match=emergency_source)
    失败含义：紧急源块仍可解析，策略闸门失效
    """
    reg = SourceRegistry(bad_top_level_emergency_source_yaml)
    with pytest.raises(LegacyRoleError, match="emergency_source"):
        reg.load()


def test_load_primaryDomainNotInAllowedDomains_raises(
    bad_primary_domain_mismatch_yaml,
):
    """覆盖范围：primary 域须在源 allowed_domains 内
    测试对象：SourceRegistry.load（bad_primary_domain_mismatch_yaml）
    目的/目标：主域与源允许域不一致时 InvalidRegistryError
    验证点：pytest.raises(InvalidRegistryError, match=does not allow domain)
    失败含义：不可行主域可声明，路由后 vendor 必失败
    """
    reg = SourceRegistry(bad_primary_domain_mismatch_yaml)
    with pytest.raises(InvalidRegistryError, match="does not allow domain"):
        reg.load()


def test_load_boolStringRejected_raisesInvalidRegistryError(bad_bool_string_yaml):
    """覆盖范围：YAML 布尔须用 true/false 非字符串
    测试对象：SourceRegistry.load（bad_bool_string_yaml）
    目的/目标：字符串 'true'/'false' 拒收，防 YAML 类型歧义
    验证点：pytest.raises(InvalidRegistryError, match=YAML boolean)
    失败含义：布尔字段误解析，enabled 开关不可信
    """
    reg = SourceRegistry(bad_bool_string_yaml)
    with pytest.raises(InvalidRegistryError, match="YAML boolean"):
        reg.load()


def test_load_validationSourceDisabled_raisesInvalidRegistryError(
    bad_validation_disabled_yaml,
):
    """覆盖范围：校验源不得指向禁用源
    测试对象：SourceRegistry.load（bad_validation_disabled_yaml）
    目的/目标：validation_source 为 disabled 源时 InvalidRegistryError
    验证点：pytest.raises(InvalidRegistryError, match=validation.*disabled)
    失败含义：禁用源充当校验通道，双源对账失真
    """
    reg = SourceRegistry(bad_validation_disabled_yaml)
    with pytest.raises(InvalidRegistryError, match="validation.*disabled"):
        reg.load()


def test_load_validationSourceDomainMismatch_raisesInvalidRegistryError(
    bad_validation_domain_mismatch_yaml,
):
    """覆盖范围：校验源须覆盖同域
    测试对象：SourceRegistry.load（bad_validation_domain_mismatch_yaml）
    目的/目标：validation 源 allowed_domains 不含主域时拒收
    验证点：pytest.raises(InvalidRegistryError, match=validation.*does not allow domain)
    失败含义：校验源无法拉同域数据，对账形同虚设
    """
    reg = SourceRegistry(bad_validation_domain_mismatch_yaml)
    with pytest.raises(InvalidRegistryError, match="validation.*does not allow domain"):
        reg.load()


def test_load_validationStringNull_raisesInvalidRegistryError(
    bad_validation_string_null_yaml,
):
    """覆盖范围：校验源字段不能用字符串 null 冒充空值
    测试对象：SourceRegistry.load（bad_validation_string_null_yaml）
    目的/目标：没有校验源应写 YAML 的 null，不能把字面量 "null" 当成源 ID
    验证点：pytest.raises(InvalidRegistryError, match=string 'null')
    失败含义：字符串 null 被当源 ID，运行时 SourceNotFound
    """
    reg = SourceRegistry(bad_validation_string_null_yaml)
    with pytest.raises(InvalidRegistryError, match="string 'null'"):
        reg.load()


def test_load_validationYamlNull_allowsNoValidationSource():
    """覆盖范围：YAML null 表示无校验源
    测试对象：SourceRegistry.load（batch_b fixture）
    目的/目标：validation_source_id 可为 None
    验证点：cn_equity_minute_bar roles.validation_source_id is None
    失败含义：合法无校验域配置被拒，分钟线域无法加载
    """
    path = Path(__file__).parent / "fixtures" / "source_registry_batch_b.yaml"
    reg = SourceRegistry(path)
    reg.load()
    roles = reg.get_domain_roles("cn_equity_minute_bar")
    assert roles.validation_source_id is None


def test_load_primaryUnknownLicense_raises(bad_unknown_license_primary_yaml):
    """覆盖范围：primary 源 license 须在白名单
    测试对象：SourceRegistry.load（bad_unknown_license_primary_yaml）
    目的/目标：未知 license 的主源 InvalidRegistryError
    验证点：pytest.raises(InvalidRegistryError)
    失败含义：未审批许可源可作 primary，合规风险
    """
    reg = SourceRegistry(bad_unknown_license_primary_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_yaml_unknownPrimaryReference_raises(bad_unknown_primary_yaml):
    """覆盖范围：primary 须引用已声明源
    测试对象：SourceRegistry.load（bad_unknown_primary_yaml）
    目的/目标：domain_roles.primary 指向不存在 source_id 时拒收
    验证点：pytest.raises(InvalidRegistryError)
    失败含义：孤儿 primary 引用可加载，fetch 运行时崩溃
    """
    reg = SourceRegistry(bad_unknown_primary_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_invalidFallbackPolicy_raises(bad_invalid_fallback_yaml):
    """覆盖范围：fallback_policy 枚举合法性
    测试对象：SourceRegistry.load（bad_invalid_fallback_yaml）
    目的/目标：未知 fallback 策略 InvalidRegistryError
    验证点：pytest.raises(InvalidRegistryError)
    失败含义：非法 fallback 可配置，故障时行为未定义
    """
    reg = SourceRegistry(bad_invalid_fallback_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_malformedYaml_raises(malformed_yaml):
    """覆盖范围：畸形 YAML 拒收
    测试对象：SourceRegistry.load（malformed_yaml）
    目的/目标：语法错误 YAML 统一 InvalidRegistryError
    验证点：pytest.raises(InvalidRegistryError)
    失败含义：坏配置静默部分解析，半残注册表入库
    """
    reg = SourceRegistry(malformed_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_pathOutsideProjectRoot_raises(tmp_path, monkeypatch):
    """覆盖范围：注册表路径须在项目根内
    测试对象：SourceRegistry.load（PROJECT_ROOT 外路径）
    目的/目标：防通过符号链接或绝对路径加载仓外配置
    验证点：pytest.raises(InvalidRegistryError, match=project root)
    失败含义：仓外 YAML 可驱动生产路由，供应链风险
    """
    import backend.app.datasources.source_registry as registry_mod

    fake_project_root = tmp_path / "project"
    fake_project_root.mkdir()
    outside = tmp_path / "outside" / "outside.yaml"
    outside.parent.mkdir()
    outside.write_text("sources: {}\ndomain_roles: {}\n", encoding="utf-8")
    monkeypatch.setattr(registry_mod, "PROJECT_ROOT", fake_project_root)
    reg = SourceRegistry(outside)
    with pytest.raises(InvalidRegistryError, match="project root"):
        reg.load()


def test_getDomainRoles_unknownDomain_raisesKeyError(loaded_registry):
    """覆盖范围：未知 data_domain 查询
    测试对象：SourceRegistry.get_domain_roles
    目的/目标：未声明域 KeyError fail-closed
    验证点：pytest.raises(KeyError)
    失败含义：未知域返回默认值，静默走错源
    """
    with pytest.raises(KeyError):
        loaded_registry.get_domain_roles("no_such_domain")


def test_getSource_unknownId_raisesSourceNotFoundError(loaded_registry):
    """覆盖范围：未知 source_id 查询
    测试对象：SourceRegistry.get
    目的/目标：不存在源 SourceNotFoundError
    验证点：pytest.raises(SourceNotFoundError)
    失败含义：拼写错误源 ID 得 None，adapter 空指针
    """
    with pytest.raises(SourceNotFoundError):
        loaded_registry.get("no_such_source")


@pytest.mark.parametrize(
    "policy",
    [
        "retry_same_source",
        "use_validation_source_with_flag",
        "use_last_good_cache",
        "mark_missing",
        "manual_review_required",
        "skip_until_next_publish",
    ],
)
def test_load_validFallbackPolicy_succeeds(policy, registry_yaml_fixture):
    """覆盖范围：六种合法 fallback_policy 枚举
    测试对象：SourceRegistry.load（parametrize policy）
    目的/目标：每种策略可成功加载并写入 domain_roles
    验证点：roles.fallback_policy == policy 参数
    失败含义：合法策略被拒，运维无法配置降级路径
    """
    text = registry_yaml_fixture.read_text(encoding="utf-8")
    text = text.replace("retry_same_source", policy)
    fixtures_dir = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=fixtures_dir) as d:
        p = Path(d) / "policy.yaml"
        p.write_text(text, encoding="utf-8")
        reg = SourceRegistry(p)
        reg.load()
        roles = reg.get_domain_roles("market_bar_1d")
        assert roles.fallback_policy == policy


def test_assertDomainAllowed_unknownDomain_raises(loaded_registry):
    """覆盖范围：源对未知域 assert_domain_allowed
    测试对象：SourceRegistry.assert_domain_allowed
    目的/目标：源 allowed_domains 不含域时 DomainNotAllowedError
    验证点：pytest.raises(DomainNotAllowedError)
    失败含义：adapter 可在无域权限时 fetch
    """
    with pytest.raises(DomainNotAllowedError):
        loaded_registry.assert_domain_allowed("baostock", "unknown_domain")


def test_assertEnabled_disabledSource_raisesSourceDisabledError(disabled_registry):
    """覆盖范围：已禁用源不能被当作可用源调度
    测试对象：SourceRegistry.assert_enabled（disabled_registry）
    目的/目标：配置里 is_enabled=false 的源，运行时查询应直接报错
    验证点：pytest.raises(SourceDisabledError)
    失败含义：禁用源仍可调度，registry 开关无效
    """
    with pytest.raises(SourceDisabledError):
        disabled_registry.assert_enabled("baostock")


def test_syncToDb_removedYamlSource_isTombstoned(tmp_path, migrated_con, registry_yaml_fixture):
    """覆盖范围：YAML 移除源 DB 墓碑与 lifecycle 列
    测试对象：SourceRegistry.sync_to_db 二次同步
    目的/目标：YAML 中消失的源 is_enabled=false 且 removed_from_yaml_at 非空
    验证点：orphan_source 墓碑；首次 sync 写入 registry_generation>=1
    失败含义：已删源仍在 DB 启用，或 lifecycle 审计列未写入
    """
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    gen_after_first = con.execute(
        "SELECT registry_generation FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    assert gen_after_first is not None and int(gen_after_first) >= 1
    con.execute(
        """
        INSERT INTO source_registry (
            source_id, source_name, source_type, allowed_domain, is_enabled
        ) VALUES ('orphan_source', 'Orphan', 'vendor_api', '[]', true)
        """
    )
    reg.sync_to_db(con)
    row = con.execute(
        """
        SELECT is_enabled, removed_from_yaml_at
        FROM source_registry WHERE source_id='orphan_source'
        """
    ).fetchone()
    assert row is not None
    assert row[0] is False
    assert row[1] is not None


def test_syncToDb_insertsSourceRows(tmp_path, migrated_con, registry_yaml_fixture):
    """覆盖范围：首次把 YAML 同步进数据库时的行数
    测试对象：SourceRegistry.sync_to_db
    目的/目标：同步返回值应与实际写入 source_registry 表的行数一致
    验证点：n>=1；COUNT(*)==n
    失败含义：sync 不写表或计数不一致，DB 镜像为空
    """
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    n = reg.sync_to_db(con)
    assert n >= 1
    count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count == n


def test_syncToDb_roundTrip_preservesAllColumns(tmp_path, migrated_con, registry_yaml_fixture):
    """覆盖范围：YAML 同步到 DB 后各列值应完整往返不丢失
    测试对象：sync_to_db 后 baostock 行
    目的/目标：rate_limit_policy、auth_required、allowed_domain JSON 保留
    验证点：row[0] 非空；allowed_domain 可 json.loads
    失败含义：列截断或序列化错误，运行时域列表丢失
    """
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    row = con.execute("""
        SELECT rate_limit_policy, auth_required, allowed_domain
        FROM source_registry WHERE source_id='baostock'
    """).fetchone()
    assert row[0]
    assert json.loads(row[2])


def test_syncToDb_calledTwice_isIdempotent(tmp_path, migrated_con, registry_yaml_fixture):
    """覆盖范围：重复 sync 幂等
    测试对象：sync_to_db 连续两次
    目的/目标：行数不变、计数稳定
    验证点：n1==n2；count==n1
    失败含义：重复 sync 重复插行或删行，DB 膨胀
    """
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    n1 = reg.sync_to_db(con)
    n2 = reg.sync_to_db(con)
    assert n1 == n2
    count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count == n1


def test_syncToDb_secondCall_updatesUpdatedAt(tmp_path, migrated_con, registry_yaml_fixture):
    """覆盖范围：二次 sync 刷新 updated_at
    测试对象：sync_to_db 两次 baostock 行
    目的/目标：第二次 updated_at >= 第一次
    验证点：t2 >= t1
    失败含义：同步时间戳不更新，运维无法判断配置刷新
    """
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    t1 = con.execute(
        "SELECT updated_at FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    reg.sync_to_db(con)
    t2 = con.execute(
        "SELECT updated_at FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    assert t2 >= t1


def test_syncToDb_withinExplicitTransaction_rollsBackOnRollback(
    tmp_path,
    migrated_con,
    registry_yaml_fixture,
):
    """覆盖范围：调用方事务内 sync 可回滚（P1-4）
    测试对象：BEGIN → sync_to_db → ROLLBACK
    目的/目标：回滚后 source_registry 行数为 0
    验证点：sync 中 n>=1；ROLLBACK 后 count==0
    失败含义：外层事务回滚无法撤销 sync，数据一致性破坏
    """
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    con.execute("BEGIN")
    n = reg.sync_to_db(con)
    assert n >= 1
    con.execute("ROLLBACK")
    count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count == 0


def test_disabledPrimaryDomain_returnsDisabledSource():
    """覆盖范围：默认禁用的分钟线域调度检查
    测试对象：get_domain_roles + assert_domain_schedulable（cn_equity_minute_bar）
    目的/目标：分钟线默认不开，尝试调度时应明确报「域已禁用」
    验证点：domain_enabled_by_default=False；
        pytest.raises(DomainDisabledError, match=DISABLED_SOURCE)
    失败含义：默认禁用分钟线仍可调度，QMT 误触发
    """
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("cn_equity_minute_bar")
    assert roles.domain_enabled_by_default is False
    with pytest.raises(DomainDisabledError, match="DISABLED_SOURCE"):
        reg.assert_domain_schedulable("cn_equity_minute_bar")


def test_fallbackDisabledByDefault_isSkippedUntilConfigured():
    """覆盖范围：fallback 源默认跳过策略
    测试对象：cn_equity_daily_bar domain_roles
    目的/目标：fallback_policy=skip_until_next_publish；qmt_xtdata 在 disabled_fallback 集
    验证点：policy 与 fallback_source_ids；disabled_fallback 含 qmt_xtdata
    失败含义：未配置 fallback 即启用备用源，成本与合规失控
    """
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("cn_equity_daily_bar")
    assert roles.fallback_policy == "skip_until_next_publish"
    assert roles.fallback_source_ids == ("qmt_xtdata",)
    assert reg.disabled_fallback_source_ids("cn_equity_daily_bar") == frozenset({"qmt_xtdata"})


@pytest.mark.parametrize("banned_role", ["Shadow", "Emergency"])
def test_legacySourceRoles_forbiddenAsSourceRoles(banned_role, registry_yaml_fixture):
    """覆盖范围：primary 位禁止写 Shadow/Emergency 字面量
    测试对象：SourceRegistry.load（parametrize banned_role）
    目的/目标：遗留角色名不能冒充真正的数据源 ID 写在主源位置
    验证点：primary 为 Shadow/Emergency 时 pytest.raises(LegacyRoleError)
    失败含义：遗留角色名可作 primary，架构回退
    """
    text = registry_yaml_fixture.read_text(encoding="utf-8")
    text = text.replace("primary: baostock", f"primary: {banned_role}", 1)
    fixtures_dir = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=fixtures_dir) as d:
        p = Path(d) / "banned_role.yaml"
        p.write_text(text, encoding="utf-8")
        reg = SourceRegistry(p)
        with pytest.raises(LegacyRoleError):
            reg.load()


def test_legacySourceRoles_forbiddenTopLevelKeys(registry_yaml_fixture):
    """覆盖范围：注入顶层 shadow_source 段
    测试对象：registry_yaml_fixture + 前置 shadow_source 块
    目的/目标：任意顶层 shadow_source 键 LegacyRoleError
    验证点：pytest.raises(LegacyRoleError, match=shadow_source)
    失败含义：顶层 shadow 块可加载，双轨配置复活
    """
    text = registry_yaml_fixture.read_text(encoding="utf-8")
    text = "shadow_source: {}\n" + text
    fixtures_dir = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=fixtures_dir) as d:
        p = Path(d) / "shadow_top.yaml"
        p.write_text(text, encoding="utf-8")
        reg = SourceRegistry(p)
        with pytest.raises(LegacyRoleError, match="shadow_source"):
            reg.load()
