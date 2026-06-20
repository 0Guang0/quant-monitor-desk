# Agent 02 — 实际实现与原始设计文档偏差审计

## 1. 独立角色边界

本 agent 只核对当前实现与原始设计/任务文档/契约是否一致，并区分两类偏差：**实现偏差**（代码未按设计实现）与 **设计缺口**（实现中暴露出设计文档或契约本身不足/滞后）。不负责代码简化、性能或 DB 深挖，除非它们构成设计偏差证据。

## 2. 使用的有效 skill / 工具

| 名称                           | 用途                                           | 执行命令或依据                                                                                                        | 结论                                                            |
| ------------------------------ | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| documentation-and-adrs skill   | 判断文档/ADR/registry 是否准确记录决策         | 已加载；对照 018A、018B、Batch map、registry、handoff                                                                 | 文档总体可追溯，但 schema contract 与 live pilot 状态有明确差异 |
| api-and-interface-design skill | 检查接口/契约是否稳定且不误导调用方            | 已加载；核查 SourceRoutePlan、DataSourceService、WriteManager、schema contract                                        | 运行接口大体稳定，spec/schema 层存在 drift                      |
| CodexPro read/search           | 读取设计文档、迁移、注册表、证据；搜索 axis 表 | `read 018A/018B/final_registry_update`; `search specs/schema/schema.sql axis_observation`; `search migrations axis_*` | 发现 schema.sql 未含 axis 表，而 migration 011 已含             |
| pytest 契约/设计测试           | 验证设计约束是否被测试守住                     | 多组 pytest，见下节                                                                                                   | 全部 exit 0，但测试确认的是“staged，不是 production-live”       |

## 3. 测试与验证结果

| 类型              | 命令                                                                                                                                                                                                    | 结果                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| 设计/生产数据闸门 | `pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q`                                                                                                       | exit 0；11 项通过                      |
| schema/DB 契约    | `pytest tests/test_ops_db_inspector.py tests/test_duckdb_connection.py tests/test_schema_contract.py tests/test_schema_migration.py -q`                                                                 | exit 0；含 1 skip                      |
| Route/service/E2E | `pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_data_cli_contract.py tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py -q` | exit 0                                 |
| 全量              | `pytest -q`                                                                                                                                                                                             | exit 0；收集 589 项，运行观察到 1 skip |

生产等价边界：未执行真实 live source，因为 018B 与 policy 明确要求显式授权、sandbox-first、禁止 production DB mutation。本 agent 采用 read-only/isolated policy gate 与 service-path E2E 作为生产等价替代；残余风险是不能暴露真实 FRED/QMT/xqshare/Yahoo 源 shape drift。

## 4. 偏差分类

### 实现与设计一致处

- `018A` 要求 Batch2.5 五阶段 gate、route evidence、micro-fetch、clean write、snapshot、lineage；归档任务存在 `phase0_*` 至 `phase4_*` 与 `final_registry_update.md`。
- `018A` 要求 Phase3 不写 clean `axis_observation`，Phase4 clean write 必须经 WriteManager；Batch2.5 repair evidence 将 B2.5-O-04 resolved。
- `018A` 要求非生产 live 时不得声称 production live；`test_batch25_production_data_gate.py` 与 `final_registry_update.md` 明确限定 staged。

### 设计缺口 / 设计滞后

| ID        | 类型              | 详情                                                                                | 证据                                                                                                                                   | 影响                                                                |
| --------- | ----------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| A02-P1-01 | 设计缺口          | `specs/schema/schema.sql` 未包含 7 个 `axis_*` 表，但 migration 011 已实现          | `search specs/schema/schema.sql axis_observation` 无命中；`backend/app/db/migrations/011_layer1_tables.sql` 有 `axis_observation` 等表 | 原始 schema 契约不再是完整 DB 真相，影响新 agent/审计者依据设计实现 |
| A02-P1-02 | 设计缺口          | live pilot 设计已补入 018B，但当前项目状态仍是 policy/planning gate，非实施完成     | `AUDIT_DEFERRED_REGISTRY.md` `R3-B2.75-01` DEFERRED                                                                                    | 不能把 Batch2.5 staged evidence 当作 production-ready 设计闭环      |
| A02-P2-01 | 设计/实现边界差异 | `ENV-E1-DGS10` 设计 primary live FRED，Batch2.5 实际走 staged `macro_supplementary` | `B2.5-O-05`; `final_registry_update.md` limitation                                                                                     | 属于实现过程中暴露出的设计/授权缺口，不是代码错误                   |
| A02-P2-02 | 设计缺口          | `axis_observation` 缺少 DB CHECK timestamp ordering；目前由 app validator 承担      | `B2.5-O-03`; migration 011 table definition无 CHECK                                                                                    | DB 层不能独立防错，需后续迁移/ADR 明确边界                          |
| A02-P3-01 | 文档一致性        | registry 中 O-02/O-03 resolution phase wording 存在微小 drift                       | `adversarial-audit-repair-verification.md` P3-REG-01                                                                                   | 不阻塞，但会增加后续计划歧义                                        |

## 5. P0/P1/P2/P3

### P0

无。

### P1

| ID        | 问题                               | 影响                             | 当前阶段可修复?             | 修复状态 | 解决方案                                                                                        |
| --------- | ---------------------------------- | -------------------------------- | --------------------------- | -------- | ----------------------------------------------------------------------------------------------- |
| A02-P1-01 | schema contract 未反映实际 axis 表 | 高：设计文档与实际 DB 迁移不一致 | 是，但用户禁止代码/文档变更 | 未修复   | 同步 `specs/schema/schema.sql` 或声明 migrations 为 DB contract authority 并更新 contract tests |
| A02-P1-02 | 未实施 Batch2.75 live pilot        | 高：无法证明真实生产源形态       | 否，需要授权与独立实施      | 未修复   | 执行 018B 六阶段 gate 或显式 re-defer，并禁止 Batch3 使用生产假设                               |

### P2

| ID        | 问题                                     | 影响                                 | 当前阶段可修复?    | 修复状态 | 解决方案                                                              |
| --------- | ---------------------------------------- | ------------------------------------ | ------------------ | -------- | --------------------------------------------------------------------- |
| A02-P2-01 | primary FRED vs staged route 差异        | 中：数据源设计与实际可验证路径不一致 | 否，需 live 授权   | 未修复   | Batch2.75 选择授权源并产生 route/fetch evidence                       |
| A02-P2-02 | DB CHECK 与 app validator 边界未完全固化 | 中：DB 不能独立兜底                  | 是，但本轮禁止变更 | 未修复   | migration 012 或 ADR 明确 app-layer only，并加 DB/app contract matrix |

### P3

| ID        | 问题                   | 影响 | 修复方案                             |
| --------- | ---------------------- | ---- | ------------------------------------ |
| A02-P3-01 | registry wording drift | 低   | 统一 O-02/O-03 resolution phase 文案 |

## 6. 评分

**86 / 100 — FAIL**

扣分依据：schema.sql drift -5；live pilot 仅 planning/policy -5；FRED primary vs staged -2；DB CHECK/app validator 边界 -1；registry wording drift -1。

## 7. 达到 95+ 的最小修复清单

1. 修复或正式声明 `specs/schema/schema.sql` 与 migration 011 的权威边界。
2. Batch2.75 live pilot 执行或 re-defer，且 Batch3 明确不使用 production-live 假设。
3. 对 `axis_observation` DB CHECK vs app validator 决策补 ADR/迁移测试。
4. 统一 registry wording。

## 8. 结论

本维度 **FAIL**。偏差主要是设计缺口/设计滞后，而不是 Batch2.5 核心实现错误。
