# 架构决策记录（`docs/decisions/`）

> 与 `docs/architecture/design/08_decision_log_index.md` 中 **ADR-0001～0005**（v1.6 设计包）编号独立；本目录从 **ADR-001** 起按主题顺序编号。

## 现行保留 ADR

| ADR                                                       | 文件                                                    | 主题 |
| --------------------------------------------------------- | ------------------------------------------------------- | ---- |
| [ADR-003](ADR-003-implementation-path-mapping.md)         | 任务文档与代码路径映射                                  |
| [ADR-004](ADR-004-write-path-complexity-ceiling.md)       | 写入热路径 C901 复杂度                                  |
| [ADR-007](ADR-007-us-trading-calendar-ssot.md)            | 美股交易日历 SSOT（`trading_sessions`）                 |
| [ADR-009](ADR-009-clean-write-targets-migration-015.md)   | clean 域路由（migration 015 · DCP-05 增量金路径 11 源） |
| [ADR-010](ADR-010-layer1-five-axis-clean-read.md)         | Layer1 五轴 clean read                                  |
| [ADR-011](ADR-011-bounded-backfill-cap-and-ci-nightly.md) | 有界 backfill 上限与 CI nightly                         |
| [ADR-015](ADR-015-live-acceptance-sandbox-dual-track.md)  | 隔离沙箱 live 验收与双轨测试                            |
| [ADR-016](ADR-016-source-route-matrix-honest-closure.md)  | 22 源矩阵诚实关账（无资格 / 外部失败）                  |

**22 源完整枚举 SSOT：** `docs/modules/design/data_sources.md` §5.9.1（ADR-009 表为其中 11 源增量金路径子集）。

**v1 根决策（ADR-0001～0005）：** 见 `docs/architecture/design/08_decision_log_index.md`。

## 已删除 / 已合并（勿再引用）

| 原编号  | 状态       | 替代                                                                                      |
| ------- | ---------- | ----------------------------------------------------------------------------------------- |
| ADR-006 | **已删除** | `docs/modules/design/data_sync_orchestrator.md`（显式 DataSourceService 金路径）          |
| ADR-008 | **已删除** | [ADR-015](ADR-015-live-acceptance-sandbox-dual-track.md) §环境门 · `product_live_gate.py` |
| ADR-012 | **已合并** | `docs/modules/design/layer5_security_evidence.md` · lineage 契约                          |
| ADR-013 | **已合并** | `docs/modules/design/layer2_cross_asset_sensor.md`                                        |
| ADR-014 | **已合并** | `docs/modules/design/layer4_market_structure.md`                                          |
| ADR-005 | **已合并** | `docs/modules/design/data_sources.md` §健康与快照边界                                     |

旧 tier-a 命名 ADR 文件已退役，请使用上表现行路径。
