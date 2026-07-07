# 架构决策记录（`docs/decisions/`）

> 与 `docs/adr/ADR-0001～0005`（v1.6 设计包）编号独立；本目录从 **ADR-001** 起按主题顺序编号。

| ADR                                                                   | 文件                                    | 主题 |
| --------------------------------------------------------------------- | --------------------------------------- | ---- |
| [ADR-001](ADR-001-ingestion-validation-write-transaction-boundary.md) | 接入校验与写入事务边界                  |
| [ADR-002](ADR-002-db-check-vs-app-validation.md)                      | 数据库 CHECK 与应用层校验分工           |
| [ADR-003](ADR-003-implementation-path-mapping.md)                     | 任务文档与代码路径映射                  |
| [ADR-004](ADR-004-write-path-complexity-ceiling.md)                   | 写入热路径 C901 复杂度不修              |
| [ADR-005](ADR-005-source-health-snapshot-boundary.md)                 | `source_health_snapshot` 模块边界       |
| [ADR-006](ADR-006-sync-datasource-service-fail-closed.md)             | 生产 Sync 须显式 `datasource_service=`  |
| [ADR-007](ADR-007-us-trading-calendar-ssot.md)                        | 美股交易日历 SSOT（`trading_sessions`） |
| [ADR-008](ADR-008-product-live-env-gate.md)                           | 产品 Live 环境门与 Tier 路由            |
| [ADR-009](ADR-009-tier-a-clean-domain-extension.md)                   | Tier A clean 域扩展（migration 015）    |
| [ADR-010](ADR-010-layer1-five-axis-clean-read.md)                     | Layer1 五轴 clean read                  |
| [ADR-011](ADR-011-bounded-backfill-cap-and-ci-nightly.md)             | 有界 backfill 上限与 CI nightly         |
| [ADR-012](ADR-012-layer5-evidence-provenance-binding.md)              | Layer5 证据血缘绑定                     |
| [ADR-013](ADR-013-layer2-vix-clean-read.md)                           | Layer2 VIX clean read                   |
| [ADR-014](ADR-014-layer4-us-equity-clean-read.md)                     | Layer4 美股 clean read                  |
| [ADR-015](ADR-015-tier-a-live-acceptance-sandbox.md)                  | Tier A 隔离沙箱 live 验收               |
| [ADR-016](ADR-016-source-route-matrix-honest-closure.md)              | 22 源矩阵诚实关账（无资格 / 外部失败）  |
