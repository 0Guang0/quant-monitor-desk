# Grill-Me Session — R3FR-05 Provider Catalog

## Doubt 1: 是否在本任务实现 DataSourceService 路由接线？

**Reconcile:** 否。本任务仅 YAML catalog + 只读 loader + 测试。`DataSourceService` 继续读 `source_registry` / `source_capabilities`；catalog 供 Round4/3H 诊断与 posture 机读，Execute 不得改 fetch 热路径。

## Doubt 2: `qmt_xqshare` 不在 source_registry — 是否跳过？

**Reconcile:** 否。任务卡 §4 明确要求。在 `source_capabilities.yaml` 已有 proposed_disabled 条目；本批补 `source_registry.yaml` 最小行 + catalog 元数据，仍 `enabled_by_default: false`。

## Doubt 3: `specs/contracts/provider_catalog.yaml` vs `specs/datasource_registry/provider_catalog.yaml`？

**Reconcile:** SSOT 为 `specs/datasource_registry/provider_catalog.yaml`（任务卡 §3 Target files）。contracts 文件只加交叉引用，不重复 YAML。

## Doubt 4: 是否复制 OpenBB provider 类？

**Reconcile:** 禁止。仅读 `参考项目/OpenBB/openbb_platform/providers/` 目录结构与 fred README 的 metadata 分离模式；`openbb_provider_reference` 行 `runtime_source_copy_allowed: false`。

## Doubt 5: `production_default_enabled` 与 registry `enabled_by_default` 冲突？

**Reconcile:** catalog 两字段表达「候选 vs 当前生产默认」；3F-R 批次内所有外部 proposed 源两者均为 false。registry 已 enabled 的 baostock/cninfo 在 catalog 可反映真实 registry 值，但 `production_default_enabled` 仍为 false（3F-R 非生产门）。

## Doubt 6: 能否拆成多个 PR 逐个加 provider？

**Reconcile:** 任务卡 §1 禁止。单 Trellis 任务单批完成全条目。
