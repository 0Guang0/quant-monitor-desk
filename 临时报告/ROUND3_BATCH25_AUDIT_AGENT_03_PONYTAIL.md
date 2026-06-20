# Agent 03 — Ponytail 极简/反过度工程审计

## 1. 独立角色边界

本 agent 只按照 ponytail 理念审计当前已实现代码是否过度工程、是否可简化、是否存在重复封装、冗余证据工具代码混入运行时路径。不得以功能正确性、DB 设计或性能结论替代 ponytail 判断。

## 2. 使用的有效 skill / 工具

| 名称                      | 用途                                                 | 执行命令或依据                                 | 输出摘要                                              |
| ------------------------- | ---------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------- |
| code-simplification skill | Chesterton's Fence、重复/冗余/长函数审计             | 已加载；用于判断可删/可抽离而不改变行为的部分  | 发现 `ingestion.py` 运行时与 evidence tooling 混置    |
| ponytail-review 归档审计  | 项目既有 A2 ponytail 审计                            | 读取 `research/audit-a2-ponytail.md`           | 已识别 4 个 >=20 行 shrink 候选，估计可减 215–275 LOC |
| CodexPro search/read      | 搜索 Layer1 数据源调用、读取 `ingestion.py` 搜索结果 | `search backend/app/layer1_axes create_adapter | DataSourceService                                     | fetch` | 未发现 Layer1 直接 adapter factory；发现 `DataSourceService` 路径与大量 evidence capture |
| pytest 回归               | 验证当前行为仍绿，避免把可简化项误判为功能坏         | Batch2.5、Layer1、full pytest                  | 当前行为通过，问题是可维护/极简性而非立刻功能失败     |

`ruff check` 不可用（safe bash allowlist 拒绝），未计入。

## 3. 执行命令与验证

| 类型          | 命令                                                                                                                                                                    | 结果                                                           |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ----------------- | ------ | --------------------------------------------------------------------- |
| ponytail 依据 | 读取 `.trellis/tasks/archive/.../research/audit-a2-ponytail.md`                                                                                                         | 文件指出 `ingestion.py` 1,516 LOC，evidence/tooling 约 557 LOC |
| 静态边界搜索  | `search backend/app/layer1_axes create_adapter                                                                                                                          | adapter_factory                                                | DataSourceService | fetch` | Layer1 使用 `DataSourceService`，未出现 `create_adapter` 直接调用证据 |
| 针对性测试    | `pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py tests/test_batch25_production_data_gate.py tests/test_datasource_service.py -q` | exit 0                                                         |
| 全量回归      | `pytest -q`                                                                                                                                                             | exit 0，收集 589 项，观察到 1 skip                             |

## 4. Ponytail 发现摘要

| ID        | 严重级 | 位置                                     | 证据                                                                     | 判断                                                                                |
| --------- | ------ | ---------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| A03-P1-01 | P1     | `backend/app/layer1_axes/ingestion.py`   | A2 report：总 1,516 LOC；`commit_clean_observation_and_snapshots` 369 行 | 违反 ponytail：单方法承载 route/fetch/validate/write/snapshot/lineage，认知负载过高 |
| A03-P1-02 | P1     | `ingestion.py` Phase3/Phase4 fetch path  | A2 report：fetch path duplication 461–525 vs 646–684，约 45 LOC 可减     | 重复编排逻辑可组合为一个 staging fetch primitive                                    |
| A03-P2-01 | P2     | `ingestion.py` evidence/markdown writers | A2 report：evidence/tooling 557 LOC，占文件约 37%                        | 运行时服务模块被审计产物生成职责稀释                                                |
| A03-P2-02 | P2     | markdown table formatters                | A2 report：多个 formatter 共享表头/row loop，约 60–75 LOC 可减           | 简单 helper 可替代重复模板                                                          |
| A03-P3-01 | P3     | sandbox bootstrap                        | A2 report：phase2/3/4 重复 sandbox bootstrap，约 40–55 LOC               | 不阻塞功能，但增加维护成本                                                          |

## 5. P0/P1/P2/P3 清单

### P0

无。未发现直接导致错误写入、数据破坏或测试失败的 ponytail 问题。

### P1

| ID        | 问题                                                     | 影响                                                                | 当前阶段可修复?        | 修复状态 | 解决方案                                                                                                                  |
| --------- | -------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| A03-P1-01 | `commit_clean_observation_and_snapshots` 369 行 monolith | 高：后续修改 validation/write/snapshot 任何一段都需理解整段事务编排 | 是，但用户禁止代码变更 | 未修复   | 拆成：micro_fetch primitive、validation gate、conflict gate、write/snapshot/lineage commit 四个私有步骤；保持外部接口不变 |
| A03-P1-02 | Phase3/Phase4 fetch/route/guard 逻辑重复                 | 高：修一处易漏另一处，可能再次引入 double fetch_log 或 guard bypass | 是，但用户禁止代码变更 | 未修复   | 让 Phase4 复用 `_fetch_staging_on_connection` 或传入 `MicroFetchResult`；加回归测试防止 double fetch_log                  |

### P2

| ID        | 问题                                              | 影响                                     | 当前阶段可修复? | 修复状态 | 解决方案                                                                                            |
| --------- | ------------------------------------------------- | ---------------------------------------- | --------------- | -------- | --------------------------------------------------------------------------------------------------- |
| A03-P2-01 | evidence capture/markdown 代码混在 runtime module | 中：运行时模块过长，降低 AI/人类导航效率 | 是              | 未修复   | 新建 `ingestion_evidence.py` 只放 capture/format/write evidence；`ingestion.py` 保持 runtime facade |
| A03-P2-02 | markdown formatter 重复                           | 中：修改证据格式需要多处同步             | 是              | 未修复   | 提取 `_format_count_table_md`、`_format_phase_payload_md`                                           |

### P3

| ID        | 问题                   | 影响 | 解决方案                                          |
| --------- | ---------------------- | ---- | ------------------------------------------------- |
| A03-P3-01 | sandbox bootstrap 重复 | 低   | 提取 `_bootstrap_sandbox_db(evidence_dir, phase)` |

## 6. 当前未修复原因

用户明确要求“只产出报告，不得进行代码变更”。因此本 agent 不执行重构，只给出最小可验证重构清单。

## 7. 评分

**82 / 100 — FAIL**

扣分依据：长文件/长方法 -6；重复 route/fetch/guard -5；evidence tooling 混入 runtime -4；formatter/bootstrap 重复 -2；无法运行 ruff/complexity tool -1。

## 8. 达到 95+ 的最小修复清单

1. 将 `commit_clean_observation_and_snapshots` 拆成可读的内部步骤，外部接口保持兼容。
2. 统一 Phase3/Phase4 fetch path，防止重复 fetch_log/route/guard 漂移。
3. 将 evidence capture/markdown writer 移到独立模块。
4. 提取 shared markdown/sandbox helpers。
5. 重跑 Batch2.5、Layer1、full pytest 与 coverage。

## 9. 结论

本维度 **FAIL**。功能测试通过，但 ponytail 标准下存在明确可简化、可删除/迁移的非必要复杂度；不能评为 95+。
