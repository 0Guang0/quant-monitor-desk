# M-DATA-03 设计权威倒查清单（项目地图 → 契约）

> **Query：** M-DATA-03 涉及模块的设计文档、规则、契约、架构  
> **Scope：** C3, D1, E1, E2, F0, B2 + 横切 ADR  
> **Date：** 2026-07-02

---

## 1. 活规划与评级

| 文件                                     | 用途                                 |
| ---------------------------------------- | ------------------------------------ |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1 | 业务 AC、十一源名单、切片建议        |
| `MODULE_COMPLETION_RATING.md` §0, §3.C–E | Pass E 诚实评级；DCP-05 不抬升整模块 |
| `MIGRATION_MAP.md` §4.12                 | 活票路径索引                         |
| `docs/implementation_tasks/README.md`    | 活工单目录                           |

## 2. 模块设计文档（第一层权威）

| Module | 设计文档                                                   | 业务要点                               |
| ------ | ---------------------------------------------------------- | -------------------------------------- |
| C3     | `docs/modules/datasource_service.md`                       | 生产 fetch 唯一门面；禁止 adapter 旁路 |
| C3     | `docs/architecture/10_external_references.md`              | 官方 API 边界（FRED/BIS 等）           |
| D1     | `docs/modules/data_sync_orchestrator.md` §12–13            | 增量/回补任务分离；§13.4.2 watermark   |
| E1     | `docs/ops/data_sync_quick_reference.md`                    | CLI sync 命令矩阵                      |
| E1     | `docs/ops/data_sync_command_matrix.md`                     | 五类 job 路由                          |
| E2     | `docs/ops/db_inspect_cli.md`                               | post-write inspect                     |
| F0     | `docs/modules/data_health_engine.md`（若存在）/ ops health | 巡检引擎                               |
| B2     | `docs/modules/data_quality_validator.md`                   | post-write 质量规则                    |

## 3. 机器契约（specs/contracts）

| 契约                 | 路径                                                 |
| -------------------- | ---------------------------------------------------- |
| DataSourceService    | `specs/contracts/datasource_service_contract.yaml`   |
| Sync job             | `specs/contracts/sync_job_contract.yaml`             |
| Data CLI             | `specs/contracts/data_cli_contract.yaml`             |
| Live tier A evidence | `specs/contracts/live_tier_a_evidence_v1.yaml`       |
| Ops inspect          | `specs/contracts/ops_db_inspect_contract.yaml`       |
| Source route         | `specs/contracts/source_route_contract.yaml`         |
| Source capability    | `specs/contracts/source_capability_contract.yaml`    |
| Reference guardrails | `specs/contracts/reference_adoption_guardrails.yaml` |
| Performance          | `docs/ops/performance_limits.md`                     |

## 4. Registry 与源矩阵

| 文件                                                 | 用途                          |
| ---------------------------------------------------- | ----------------------------- |
| `specs/datasource_registry/source_registry.yaml`     | 11 源角色 / validation_only   |
| `specs/datasource_registry/source_capabilities.yaml` | capability 声明               |
| `specs/datasource_registry/provider_catalog.yaml`    | provider 元数据               |
| `specs/context/authority_graph.yaml`                 | 模块图节点 · merge 冲突边界   |
| `R3H_PASS_EXECUTION_PLAN.archived-20260702.md` §2.1  | Tier A 逐源 live 要求（只读） |

## 5. 架构决策（ADR · 执行绑定）

| ADR     | 绑定本票                                   |
| ------- | ------------------------------------------ |
| ADR-025 | Sync 必须 `datasource_service=`            |
| ADR-027 | `QMD_ALLOW_LIVE_FETCH` 真网闸              |
| ADR-028 | clean 域 / migration 015（只读，不新 DDL） |
| ADR-034 | 本票新建：隔离库 live 验收契约             |

## 6. 仓内实现入口（Execute 触点 · 非参考 L 梯）

| 区域                 | 路径                                                         |
| -------------------- | ------------------------------------------------------------ |
| Live gate            | `backend/app/datasources/product_live_gate.py`               |
| Live service 工厂    | `backend/app/datasources/product_live_ports.py`              |
| Orchestrator         | `backend/app/sync/orchestrator.py`                           |
| Watermark            | `backend/app/sync/watermark.py`                              |
| Incremental registry | `backend/app/sync/incremental_source_registry.py`            |
| Per-source ops       | `backend/app/ops/*_incremental_*.py`                         |
| Fetch ports          | `backend/app/datasources/fetch_ports/*_port.py`              |
| CLI                  | `backend/app/cli/data_commands.py`                           |
| Clean 路由           | `backend/app/ops/sandbox_clean_write/clean_write_targets.py` |
| 11 源 e2e            | `tests/test_*_incremental_e2e.py`                            |
| Live 政策测          | `tests/test_r3h08_live_productization.py`                    |

## 7. 历史证据（只读 · 不当作 PASS）

| 归档                                                     | 用途                          |
| -------------------------------------------------------- | ----------------------------- |
| `.trellis/tasks/archive/2026-07/wave4-r3-dcp-05-tier-a/` | replay 逻辑 SSOT · 切片模板   |
| R3-DCP-01/02/03 Trellis 归档                             | baostock/fred 增量先例        |
| R3H-08 归档                                              | 24 源 env-gated live 工厂模式 |

## 8. 仓内直接复用 vs 借鉴三等级（防混淆）

| 类型             | 路径示例                                                                | Execute 标注                      |
| ---------------- | ----------------------------------------------------------------------- | --------------------------------- |
| **仓内直接复用** | `sync/orchestrator.py` · `ops/*_incremental_*` · `product_live_gate.py` | 「直接复用」；**禁止**写 L1/L2/L3 |
| **借鉴 L2**      | 仅 `参考项目/.../bis.py` 窗参数思路                                     | 「L2 改造」+ 改造清单             |
| **借鉴 L3**      | OpenBB fetcher 三阶段概念                                               | 「L3 对齐」；零粘贴               |
| **forbidden**    | EasyXT `unified_data_interface`                                         | 负向测                            |

本票参考侧 **无 L1**（无整段可原样粘贴的外部实现）。

## Caveats

- `docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` = 覆盖地图，**不是工单**
- Wave 4 DCP 任务卡已归档；本票是 **模块 v2 第一张 complex 活票**
