"""Provider catalog contract tests (R3FR-05).

覆盖范围：provider_catalog.yaml 与 source_registry/capabilities/contracts 对齐。
"""

from __future__ import annotations

import pytest

from backend.app.datasources.provider_catalog import (
    ProviderCatalogError,
    load_provider_catalog,
    provider_for_source,
)
from backend.app.datasources.source_registry import (
    SCHEMA_CHECK_LICENSE_TYPES,
    SCHEMA_CHECK_SOURCE_TYPES,
    SourceRegistry,
)

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

PROVIDER_CATALOG = PROJECT_ROOT / "specs/datasource_registry/provider_catalog.yaml"
SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
SOURCE_CAPABILITY_CONTRACT = PROJECT_ROOT / "specs/contracts/source_capability_contract.yaml"
DATASOURCE_SERVICE_CONTRACT = PROJECT_ROOT / "specs/contracts/datasource_service_contract.yaml"

REQUIRED_PROVIDER_FIELDS = frozenset(
    {
        "provider_id",
        "source_ids",
        "source_type",
        "license_type",
        "license_or_terms",
        "allowed_domains",
        "enabled_by_default",
        "status",
        "production_default_candidate",
        "production_default_enabled",
        "requires_user_authorization",
        "requires_local_client",
        "validation_only",
        "max_default_symbols_or_series",
        "max_default_window_days",
        "reference_architecture",
        "runtime_source_copy_allowed",
    }
)

VALID_CATALOG_STATUS = frozenset(
    {"active", "sandbox_candidate", "proposed_disabled_source", "READY_WITH_EVIDENCE"}
)

PROPOSED_EXTERNAL_SOURCE_IDS = frozenset(
    {
        "mootdx",
        "eastmoney",
        "sina_finance",
        "ths_ifind",
    }
)

LOCAL_TERMINAL_SOURCE_IDS = frozenset({"qmt_xtdata", "tdx_pytdx", "qmt_xqshare"})


def _registry_by_id() -> dict[str, dict]:
    registry = load_yaml(SOURCE_REGISTRY)
    return {s["source_id"]: s for s in registry.get("sources") or []}


def _catalog_providers() -> list[dict]:
    return list(load_provider_catalog().get("providers") or [])


def _catalog_source_to_provider() -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for entry in _catalog_providers():
        for sid in entry.get("source_ids") or []:
            mapping[sid] = entry
    return mapping


def test_everyRegistrySource_hasCatalogEntry() -> None:
    """覆盖范围：source_registry 每个 source_id 在 catalog 中有且仅有一条 provider 映射
    测试对象：source_registry.yaml 与 provider_catalog.yaml providers 列表
    目的/目标：25 源全覆盖，每源恰一 provider entry（1:1 主模式）
    验证点：registry 源集合等于 catalog 源集合；len(providers)==25
    失败含义：registry 与 catalog 脱节，Round3G 无法读取统一 posture
    """
    registry_ids = {s["source_id"] for s in load_yaml(SOURCE_REGISTRY).get("sources") or []}
    catalog_map = _catalog_source_to_provider()
    assert set(catalog_map.keys()) == registry_ids
    assert len(_catalog_providers()) == 25


def test_catalogRequiredFields_present() -> None:
    """覆盖范围：provider catalog 每条目必填字段完整性
    测试对象：provider_catalog.yaml 全量 providers
    目的/目标：机器可读 catalog 字段集与冻结卡 §4 一致
    验证点：每条 provider 键集合 ⊇ REQUIRED_PROVIDER_FIELDS
    失败含义：下游 R3G/Round4 读取缺字段 posture 不确定
    """
    missing: list[str] = []
    for entry in _catalog_providers():
        pid = entry.get("provider_id", "<unknown>")
        absent = REQUIRED_PROVIDER_FIELDS - set(entry.keys())
        if absent:
            missing.append(f"{pid}: {sorted(absent)}")
    assert missing == [], f"catalog entries missing required fields: {missing}"


def test_catalogEnums_matchSchemaCheck() -> None:
    """覆盖范围：catalog source_type/license_type 与 schema CHECK 枚举一致
    测试对象：provider_catalog.yaml 全量 providers
    目的/目标：catalog enum 与 schema.sql / migration 009 零违规
    验证点：每个 provider 的 source_type/license_type 在白名单内
    失败含义：catalog 可加载但 DB sync 或迁移约束会失败
    """
    bad_types: list[str] = []
    bad_licenses: list[str] = []
    for entry in _catalog_providers():
        pid = entry["provider_id"]
        if entry["source_type"] not in SCHEMA_CHECK_SOURCE_TYPES:
            bad_types.append(f"{pid}:{entry['source_type']}")
        if entry["license_type"] not in SCHEMA_CHECK_LICENSE_TYPES:
            bad_licenses.append(f"{pid}:{entry['license_type']}")
    assert bad_types == [], f"invalid catalog source_type: {bad_types}"
    assert bad_licenses == [], f"invalid catalog license_type: {bad_licenses}"


def test_proposedExternalSources_notProductionEnabled() -> None:
    """覆盖范围：拟新增外部源不得 production 默认启用
    测试对象：PROPOSED_EXTERNAL_SOURCE_IDS 对应 catalog entries
    目的/目标：adapter/auth/license/route/replay 证据前保持 disabled posture
    验证点：enabled_by_default 与 production_default_enabled 均为 False
    失败含义：未审批外部源被标为生产可用，合规与路由风险
    """
    catalog_map = _catalog_source_to_provider()
    violations: list[str] = []
    for sid in PROPOSED_EXTERNAL_SOURCE_IDS:
        entry = catalog_map[sid]
        if entry.get("enabled_by_default"):
            violations.append(f"{sid}: enabled_by_default")
        if entry.get("production_default_enabled"):
            violations.append(f"{sid}: production_default_enabled")
    assert violations == [], f"proposed external sources over-enabled: {violations}"


def test_productionDefaultCandidate_distinctFromEnabled() -> None:
    """覆盖范围：production_default_candidate 与 production_default_enabled 语义分离
    测试对象：provider_catalog.yaml 全量 providers
    目的/目标：候选与当前生产启用是不同字段，避免 R3G 误读
    验证点：存在 candidate=true 且 enabled=false（baostock/cninfo）；无 enabled=true 条目
    失败含义：两字段混用，planned primary 被误当作已生产启用
    """
    has_distinct_candidate = False
    wrongly_enabled: list[str] = []
    for entry in _catalog_providers():
        candidate = bool(entry.get("production_default_candidate"))
        enabled = bool(entry.get("production_default_enabled"))
        if candidate and not enabled:
            has_distinct_candidate = True
        if enabled:
            wrongly_enabled.append(entry["provider_id"])
    assert has_distinct_candidate, "expected at least one production_default_candidate without enabled"
    assert wrongly_enabled == [], f"production_default_enabled must stay false in R3FR-05: {wrongly_enabled}"


def test_fredAndLocalTerminalPosture() -> None:
    """覆盖范围：fred 授权与 QMT/TDX/xqshare 本地终端默认禁用 posture
    测试对象：fred、qmt_xtdata、tdx_pytdx、qmt_xqshare catalog entries
    目的/目标：fred 须 requires_user_authorization 且默认关闭；终端源默认关闭
    验证点：fred auth=true, enabled=false；终端三源 enabled_by_default=false
    失败含义：宏观/终端源在未授权时被默认可调度
    """
    catalog_map = _catalog_source_to_provider()
    fred = catalog_map["fred"]
    assert fred.get("requires_user_authorization") is True
    assert fred.get("enabled_by_default") is False
    for sid in LOCAL_TERMINAL_SOURCE_IDS:
        assert catalog_map[sid].get("enabled_by_default") is False, sid


def test_openbbReference_noRuntimeCopy() -> None:
    """覆盖范围：openbb_provider_reference 元数据占位不得允许 runtime 复制
    测试对象：openbb_provider_reference catalog entry
    目的/目标：OpenBB 仅 architecture_only，catalog 显式禁止 runtime copy
    验证点：runtime_source_copy_allowed is False；reference_architecture 非空
    失败含义：AGPL runtime 复制 posture 被 catalog 误标为允许
    """
    entry = _catalog_source_to_provider()["openbb_provider_reference"]
    assert entry.get("runtime_source_copy_allowed") is False
    assert entry.get("reference_architecture") == "openbb_provider_architecture"
    assert entry.get("status") == "proposed_disabled_source"


def test_catalogStatus_matchesCapabilityRegistry() -> None:
    """覆盖范围：catalog status 与 source_capabilities 显式 status 对齐
    测试对象：source_capabilities.yaml status 字段与 catalog providers
    目的/目标：capability registry 有 status 时 catalog 不得漂移
    验证点：cap 有 status 的源 catalog.status 相等
    失败含义：capability 与 catalog 状态不一致，路由/诊断矛盾
    """
    caps = load_yaml(SOURCE_CAPABILITIES).get("sources") or {}
    catalog_map = _catalog_source_to_provider()
    mismatches: list[str] = []
    for sid, cap_entry in caps.items():
        cap_status = cap_entry.get("status")
        if cap_status is None:
            continue
        cat_status = catalog_map[sid].get("status")
        if cat_status != cap_status:
            mismatches.append(f"{sid}: catalog={cat_status!r} cap={cap_status!r}")
    assert mismatches == [], f"catalog status drift from capabilities: {mismatches}"


def test_catalogEnabledByDefault_notLooserThanRegistry() -> None:
    """覆盖范围：catalog enabled_by_default 不得比 registry 更松
    测试对象：source_registry 与 catalog 同名字段
    目的/目标：catalog 只能等同或更严，不能把 registry 禁用的源标为默认启用
    验证点：catalog enabled 为 True 时 registry 也为 True
    失败含义：catalog 放宽默认启用，绕过 registry D-11 等策略
    """
    registry = _registry_by_id()
    catalog_map = _catalog_source_to_provider()
    violations: list[str] = []
    for sid, reg in registry.items():
        reg_enabled = bool(reg.get("enabled_by_default", False))
        cat_enabled = bool(catalog_map[sid].get("enabled_by_default", False))
        if cat_enabled and not reg_enabled:
            violations.append(sid)
    assert violations == [], f"catalog enabled_by_default looser than registry: {violations}"


def test_catalogPosture_alignsWithSourceRegistry() -> None:
    """覆盖范围：catalog 与 registry 的 validation_only 与授权 posture 对齐
    测试对象：provider_catalog 与 source_registry 交叉字段
    目的/目标：design §1.5 映射 — validation_only 一致；需授权源 catalog 标记 authorization
    验证点：validation_only 相等；requires_user_setup/auth_required 时 catalog requires_user_authorization
    失败含义：catalog 与 registry 业务 posture 分叉，Round3G admission 无 SSOT
    """
    registry = _registry_by_id()
    catalog_map = _catalog_source_to_provider()
    mismatches: list[str] = []
    for sid, reg in registry.items():
        cat = catalog_map[sid]
        if bool(reg.get("validation_only", False)) != bool(cat.get("validation_only", False)):
            mismatches.append(f"{sid}: validation_only")
        needs_auth = bool(reg.get("requires_user_setup") or reg.get("auth_required"))
        if needs_auth and not cat.get("requires_user_authorization"):
            mismatches.append(f"{sid}: requires_user_authorization")
    assert mismatches == [], f"catalog/registry posture mismatch: {mismatches}"


def test_provider_catalog_contractRefs() -> None:
    """覆盖范围：契约 YAML 引用 provider catalog SSOT 路径
    测试对象：source_capability_contract.yaml、datasource_service_contract.yaml
    目的/目标：AC-7 — 契约机读指向 specs/datasource_registry/provider_catalog.yaml
    验证点：两契约 provider_catalog_path 字段值正确且文件存在
    失败含义：执行者无法从契约发现 catalog SSOT，loop/审计缺口
    """
    expected = "specs/datasource_registry/provider_catalog.yaml"
    cap_contract = load_yaml(SOURCE_CAPABILITY_CONTRACT)
    svc_contract = load_yaml(DATASOURCE_SERVICE_CONTRACT)
    assert cap_contract.get("provider_catalog_path") == expected
    assert svc_contract.get("provider_catalog_path") == expected
    assert (PROJECT_ROOT / expected).is_file()


def test_loadProviderCatalog_returnsProviders() -> None:
    """覆盖范围：只读 loader 能加载 catalog 文档
    测试对象：backend.app.datasources.provider_catalog.load_provider_catalog
    目的/目标：§9.3 loader 最小 API 可调用且返回 providers 列表
    验证点：version 与 providers 非空
    失败含义：runtime 无法读取 catalog，R3G 须重复解析 YAML
    """
    doc = load_provider_catalog()
    assert doc.get("version") == "provider_catalog_v1"
    assert len(doc.get("providers") or []) == 25


def test_providerForSource_knownAndUnknown() -> None:
    """覆盖范围：provider_for_source 查找已知/未知 source_id
    测试对象：backend.app.datasources.provider_catalog.provider_for_source
    目的/目标：按 source_id 反查 provider entry；未知返回 None
    验证点：baostock 命中；__no_such_source__ 为 None
    失败含义：loader 辅助函数不可用，下游须自行扫描 providers 列表
    """
    catalog = load_provider_catalog()
    hit = provider_for_source("baostock", catalog)
    assert hit is not None
    assert hit.get("provider_id") == "baostock"
    assert provider_for_source("__no_such_source__", catalog) is None


def test_catalogStatus_valuesAreValid() -> None:
    """覆盖范围：catalog status 枚举合法性
    测试对象：provider_catalog.yaml status 字段
    目的/目标：status 仅允许 active/sandbox_candidate/proposed_disabled_source
    验证点：所有 status ∈ VALID_CATALOG_STATUS
    失败含义：非法 status 无法与 capability/registry 状态机对齐
    """
    bad: list[str] = []
    for entry in _catalog_providers():
        status = entry.get("status")
        if status not in VALID_CATALOG_STATUS:
            bad.append(f"{entry.get('provider_id')}: {status!r}")
    assert bad == [], f"invalid catalog status values: {bad}"


def test_defaultYaml_registryStillLoads() -> None:
    """覆盖范围：registry 补两行后默认 SourceRegistry 仍可加载
    测试对象：SourceRegistry() 默认路径
    目的/目标：9.2 registry 补丁不破坏既有 loader
    验证点：load() 不抛异常；新源 openbb_provider_reference 可 get
    失败含义：catalog 任务破坏 source registry 基线
    """
    reg = SourceRegistry()
    reg.load()
    assert reg.get("openbb_provider_reference").source_id == "openbb_provider_reference"
    assert reg.get("qmt_xqshare").source_id == "qmt_xqshare"


def test_loadProviderCatalog_outsideRoot_raises(tmp_path, monkeypatch) -> None:
    """覆盖范围：catalog 路径须在项目根内
    测试对象：load_provider_catalog（PROJECT_ROOT 外路径）
    目的/目标：防通过符号链接或绝对路径加载仓外 catalog YAML
    验证点：pytest.raises(ProviderCatalogError, match=project root)
    失败含义：仓外 catalog 可驱动 posture 元数据，供应链风险
    """
    import backend.app.datasources.provider_catalog as catalog_mod
    import backend.app.datasources.source_registry as registry_mod

    fake_project_root = tmp_path / "project"
    fake_project_root.mkdir()
    outside = tmp_path / "outside" / "outside.yaml"
    outside.parent.mkdir()
    outside.write_text("version: x\nproviders: []\n", encoding="utf-8")
    monkeypatch.setattr(catalog_mod, "PROJECT_ROOT", fake_project_root)
    monkeypatch.setattr(registry_mod, "PROJECT_ROOT", fake_project_root)
    with pytest.raises(ProviderCatalogError, match="project root"):
        load_provider_catalog(outside)


def test_loadProviderCatalog_invalidShape_raises(tmp_path, monkeypatch) -> None:
    """覆盖范围：catalog 文档根结构与 providers 列表校验
    测试对象：load_provider_catalog 对畸形 YAML 的 fail-fast
    目的/目标：非 dict 根或非 list providers 立即抛 ProviderCatalogError
    验证点：两条畸形 fixture 均 raises ProviderCatalogError
    失败含义：畸形 catalog 被静默接受，下游读取 posture 不确定
    """
    import backend.app.datasources.provider_catalog as catalog_mod
    import backend.app.datasources.source_registry as registry_mod

    fake_root = tmp_path / "project"
    fake_root.mkdir()
    bad_root = fake_root / "bad_root.yaml"
    bad_root.write_text("not-a-mapping\n", encoding="utf-8")
    bad_providers = fake_root / "bad_providers.yaml"
    bad_providers.write_text("version: x\nproviders: not-a-list\n", encoding="utf-8")
    monkeypatch.setattr(catalog_mod, "PROJECT_ROOT", fake_root)
    monkeypatch.setattr(registry_mod, "PROJECT_ROOT", fake_root)
    with pytest.raises(ProviderCatalogError, match="mapping"):
        load_provider_catalog(bad_root)
    with pytest.raises(ProviderCatalogError, match="list"):
        load_provider_catalog(bad_providers)


def test_runtimeSourceCopy_notAllowed_allProviders() -> None:
    """覆盖范围：全量 provider 禁止 runtime 源码复制
    测试对象：provider_catalog.yaml 全部 providers 的 runtime_source_copy_allowed
    目的/目标：25 源均显式 runtime_source_copy_allowed=false，含 openbb 参考项
    验证点：任一 provider 该字段非 False 则失败
    失败含义：catalog 误标允许复制参考项目 runtime，AGPL/合规风险
    """
    violations: list[str] = []
    for entry in _catalog_providers():
        if entry.get("runtime_source_copy_allowed") is not False:
            violations.append(entry.get("provider_id", "<unknown>"))
    assert violations == [], f"runtime_source_copy_allowed must be false: {violations}"


def test_catalogTypes_matchSourceRegistry() -> None:
    """覆盖范围：catalog 与 registry 的 source_type/license_type 逐源对齐
    测试对象：provider_catalog.yaml 与 source_registry.yaml 交叉字段
    目的/目标：catalog enum 字段与 registry SSOT 零漂移
    验证点：25 源 source_type 与 license_type 均相等
    失败含义：catalog 与 registry 类型标注分叉，schema sync 会失败
    """
    registry = _registry_by_id()
    catalog_map = _catalog_source_to_provider()
    mismatches: list[str] = []
    for sid, reg in registry.items():
        cat = catalog_map[sid]
        if cat.get("source_type") != reg.get("source_type"):
            mismatches.append(f"{sid}: source_type")
        if cat.get("license_type") != reg.get("license_type"):
            mismatches.append(f"{sid}: license_type")
    assert mismatches == [], f"catalog/registry type drift: {mismatches}"
