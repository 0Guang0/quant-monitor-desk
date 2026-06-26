# GitNexus summary — R3FR-05（Phase 1b）

## Query: provider catalog / datasource registry

- 无现有 `provider_catalog` 符号；greenfield YAML + loader
- `load_source_registry` 仅在测试与契约门中使用（`tests/test_source_capabilities.py`）
- `DataSourceService` 生产 fetch 不依赖 catalog（本批不接线）

## Impact 预判（Plan）

| 拟新增/修改符号              | 方向   | 风险                         |
| ---------------------------- | ------ | ---------------------------- |
| `load_provider_catalog`      | 新函数 | LOW — 无 upstream caller     |
| `provider_catalog.yaml`      | 新文件 | LOW — 测试驱动消费           |
| `source_registry.yaml` +2 行 | 数据   | LOW — proposed_disabled only |
| contract yaml 引用           | 文档   | LOW                          |

Execute 前须对 `load_provider_catalog` 跑 `impact()`；预计无 production caller。

## 禁止模式（已有护栏）

`reference_adoption_guardrails.yaml` 已列：

- `copied_openbb_runtime_source`
- `openbb_provider_architecture.required_rewrites`

扩展测试应引用 R3FR-05 catalog 路径而非新护栏类别。

## 建议 Execute 顺序

1. 测试 RED（结构 + coverage）
2. YAML 全量
3. loader GREEN
4. contracts
5. guardrails closure
6. full pytest
