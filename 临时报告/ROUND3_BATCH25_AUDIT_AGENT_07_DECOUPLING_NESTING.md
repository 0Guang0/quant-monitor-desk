# Agent 07 — 解耦性、嵌套与工程细节审计

## 1. 独立角色边界

本 agent 只审计代码/模块之间的解耦性、嵌套深度、依赖方向、工程细节规范和模块职责分配。不评价业务是否完成或 DB schema 是否正确。

## 2. 使用的有效 skill / 工具

| 名称                      | 用途                                     | 执行命令或依据                                          | 结果                                   |
| ------------------------- | ---------------------------------------- | ------------------------------------------------------- | -------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------- |
| codebase-design skill     | deep module / seam / adapter 判断        | 已加载；审计 Layer1/DataSourceService/WriteManager seam | 外部 seam 正确，内部职责偏集中         |
| code-simplification skill | 长函数、重复条件、混合职责审计           | 已加载；结合 ponytail A2 报告                           | 发现 monolith 与重复 fetch/route/guard |
| CodexPro search/read      | 搜索 Layer1 direct adapter、读取关键模块 | `search create_adapter                                  | DataSourceService                      | fetch`; 读取 `path_compat.py`, `raw_store.py` | 没有直接 adapter factory；存在新 storage helper 与 raw store 分离 |
| pytest module boundary    | 检查模块边界                             | `pytest tests/test_module_boundaries.py ... -q`         | exit 0                                 |
| pytest targeted           | 验证解耦边界对应行为                     | DataSourceService/Sync/Layer1 tests                     | exit 0                                 |

## 3. 验证命令

| 命令                                                                                                                                                                                                    | 结果   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| `pytest tests/test_module_boundaries.py tests/test_global_execution_rules.py tests/test_documentation_index.py tests/test_manifest_protocol.py -q`                                                      | exit 0 |
| `pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_data_cli_contract.py tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py -q` | exit 0 |
| `pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py tests/test_batch25_production_data_gate.py tests/test_datasource_service.py -q`                                 | exit 0 |

## 4. 解耦/嵌套发现

### P0

无。

### P1

| ID        | 问题                                             | 证据                                                 | 影响                                                                                            | 当前阶段可修复?        | 修复状态 | 解决方案                                                                                                 |
| --------- | ------------------------------------------------ | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------- | -------- | -------------------------------------------------------------------------------------------------------- |
| A07-P1-01 | `Layer1ObservationIngestionService` 内部职责过多 | A2 report：service core ~704 LOC；commit 方法 369 行 | 单一类同时做 route、fetch、validation、conflict、write、snapshot、lineage、evidence，内部耦合高 | 是，但用户禁止代码变更 | 未修复   | 外部保留 facade，内部拆成 route/fetch、validate/conflict、write/snapshot、lineage/evidence collaborators |
| A07-P1-02 | Phase3/Phase4 共享流程未完全通过公共 seam 表达   | A2 report：fetch path duplication 约 45 LOC          | 后续改 route/fetch/guard 容易出现分支漂移                                                       | 是                     | 未修复   | 定义内部 `_prepare_and_fetch_staging` seam，Phase3/4 复用                                                |

### P2

| ID        | 问题                                                                                     | 证据                                     | 影响                                              | 当前阶段可修复? | 修复状态 | 解决方案                                                                         |
| --------- | ---------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------- | --------------- | -------- | -------------------------------------------------------------------------------- |
| A07-P2-01 | evidence writer 与 runtime module 耦合                                                   | `ingestion.py` evidence/tooling ~557 LOC | 工程导航困难，测试也会依赖 runtime 文件内工具函数 | 是              | 未修复   | `ingestion_evidence.py` 或 `ops/layer1_ingestion_evidence.py` 承担 artifact 写入 |
| A07-P2-02 | untracked `backend/app/storage/path_compat.py` 新 helper 与 raw_store 未纳入清晰迁移说明 | `show_changes`; read path_compat         | 可能是合理 seam，也可能是未完整接线的支线 helper  | 是              | 未修复   | 在 PR 描述或报告中说明该 helper 的调用方、测试与必要性；未使用则删除             |

### P3

| ID        | 问题                          | 影响   | 解决方案            |
| --------- | ----------------------------- | ------ | ------------------- |
| A07-P3-01 | markdown/sandbox helpers 重复 | 低到中 | 提取共享内部 helper |

## 5. 正向证据

- Layer1 未直接调用 `create_adapter`；数据源路径通过 `DataSourceService`。
- Module boundary tests 通过。
- WriteManager 相关测试通过，说明 clean write seam 仍可验证。

## 6. 评分

**83 / 100 — FAIL**

扣分依据：核心 service 内聚过高 -7；Phase3/4 internal seam 缺失 -4；evidence/runtime 耦合 -3；untracked helper 说明不足 -2；helper 重复 -1。

## 7. 达到 95+ 的最小修复清单

1. 拆分 `Layer1ObservationIngestionService` 内部职责，同时保持外部 facade。
2. Phase3/4 复用同一 route/fetch/guard seam。
3. 将 evidence artifact 写入从 runtime service 中移出。
4. 对 `path_compat.py` 明确归属、调用方与测试，或移除。

## 8. 结论

本维度 **FAIL**。外部架构边界基本正确，但内部解耦和嵌套复杂度不能达到 95+。
