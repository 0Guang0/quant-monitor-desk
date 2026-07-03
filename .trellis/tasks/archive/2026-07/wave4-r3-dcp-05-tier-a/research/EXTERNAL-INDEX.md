# EXTERNAL-INDEX — R3-DCP-05

> 包外必读与源码字典 · Plan v4.1

---

## §A 切片开工前必读（外部）

| 路径                                                                                                                               | 用途                       |
| ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_05_TIER_A_INCREMENTAL.md` | 活卡 §1–§5                 |
| `docs/implementation_tasks/.../R3_DCP_TO_ISSUES_INDEX.md` §7                                                                       | Wave 4 DCP-05 索引         |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5、§3.5.2                                                                                   | Wave 4 目标与并行          |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`                                                                    | 11/11 clean 矩阵           |
| `docs/modules/data_sync_orchestrator.md` §13.4.2                                                                                   | Incremental 流程           |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                               | 借鉴梯                     |
| `docs/quality/待修复清单.md` §4、§8                                                                                                | 台账承接                   |
| `docs/architecture/06_deployment_and_local_ops.md`                                                                                 | live sync 运维（S13 更新） |

### Wave 3 归档（仓内模板 · 非参考 L 梯）

| 路径                                                             | 用途          |
| ---------------------------------------------------------------- | ------------- |
| `.trellis/tasks/archive/2026-06/06-30-wave3-r3-dcp-01-baostock/` | baostock 模板 |
| `.trellis/tasks/archive/2026-06/06-30-wave3-r3-dcp-02-fred/`     | fred 模板     |

---

## §B 执行情境路由（外部）

| 情境            | 路径                                                      |
| --------------- | --------------------------------------------------------- |
| Migration 覆盖  | `docs/schema/MIGRATION_COVERAGE.md`                       |
| Clean 契约      | `backend/app/db/migrations/013_clean_domain_tables.sql`   |
| Registry 三件套 | `specs/datasource_registry/source_registry.yaml`          |
| Tier A 列表     | `backend/app/datasources/live_tier_router.py`             |
| 东财口径        | `docs/quality/待修复清单.md` `ACC-EASTMONEY-TAXONOMY-001` |

---

## §C 源码 / 测试字典

| 符号 / 路径                                    | 说明                                 |
| ---------------------------------------------- | ------------------------------------ |
| `sync_baostock_incremental`                    | `data_commands.py` — mock 硬编码待修 |
| `sync_fred_incremental`                        | `data_commands.py` — live gate 先例  |
| `read_bar_trade_date_watermark`                | `sync/watermark.py`                  |
| `read_observation_date_watermark`              | `ops/fred_incremental_watermark.py`  |
| `resolve_clean_write_target`                   | `clean_write_targets.py`             |
| `build_product_live_service`                   | `product_live_ports.py`              |
| `tests/test_baostock_incremental_watermark.py` | DCP-01 先例                          |
| `tests/test_baostock_incremental_e2e.py`       | DCP-01 e2e                           |
| `tests/test_fred_macro_incremental_e2e.py`     | DCP-02 先例                          |

---

## §D 参考项目源码（只读 · Execute RED 前实读）

| 文件                                                                            | 等级                        |
| ------------------------------------------------------------------------------- | --------------------------- |
| `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` | architecture_only           |
| `参考项目/digital-oracle/digital_oracle/providers/bis.py`                       | L2                          |
| `参考项目/EasyXT/data_manager/auto_data_updater.py`                             | L2 概念 / forbidden runtime |
| `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244               | forbidden                   |

落盘：`research/execute-reference-read-evidence.md`（Execute 阶段）
