"""Provider catalog runtime loader tests (R3FR-05).

静态 YAML/registry/capabilities 对齐：
`uv run python scripts/check_provider_catalog.py --strict`
（亦由 production_gate 调用）。
"""

from __future__ import annotations

import pytest

from backend.app.datasources.provider_catalog import (
    ProviderCatalogError,
    load_provider_catalog,
    provider_for_source,
)
from backend.app.datasources.source_registry import SourceRegistry

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"


def test_loadProviderCatalog_returnsProviders() -> None:
    """覆盖范围：只读 loader 能加载 catalog 文档
    测试对象：backend.app.datasources.provider_catalog.load_provider_catalog
    目的/目标：§9.3 loader 最小 API 可调用且返回 providers 列表
    验证点：version 与 providers 非空；len(providers)==len(registry sources)
    失败含义：runtime 无法读取 catalog，R3G 须重复解析 YAML
    """
    doc = load_provider_catalog()
    registry_count = len(load_yaml(SOURCE_REGISTRY).get("sources") or [])
    assert doc.get("version") == "provider_catalog_v1"
    assert len(doc.get("providers") or []) == registry_count


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
