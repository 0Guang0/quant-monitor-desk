# Agent 05 — 可维护性与测试覆盖审计

## 1. 独立角色边界

本 agent 只审计可维护性与测试覆盖：模块是否容易演进、测试是否覆盖关键行为、覆盖率是否足以防回归、skip/低覆盖/报告漂移是否影响维护。不评价业务准入、DB 设计或性能。

## 2. 使用的有效 skill / 工具

| 名称                          | 用途                                             | 执行命令或依据                                                              | 结论                                          |
| ----------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------- | --------------------------------------------- |
| test-driven-development skill | 检查行为测试、边界测试、回归测试                 | 已加载；对照 Batch2.5 关键行为测试                                          | 行为测试较多，但低覆盖热点仍在                |
| code-review-and-quality skill | 审查测试是否只测调用还是测语义                   | 已加载；结合 018A 与测试套件                                                | Batch2.5 关键测试为语义测试，不只是 call-only |
| CodexPro read/search          | 读取历史 repair verification、coverage、测试清单 | `read adversarial-audit-repair-verification.md`; `pytest --collect-only -q` | 收集 589 项；历史报告指出 A4/A8 gaps 已关闭   |
| pytest-cov                    | 量化覆盖率与低覆盖模块                           | `pytest --cov=backend --cov-fail-under=85 -q`                               | 总覆盖率 91.31%，低覆盖模块需补测             |
| pytest                        | 针对性/全量测试                                  | 多组命令                                                                    | 全部 exit 0，1 skip 需定位                    |

## 3. 测试执行结果

| 类型              | 命令                                                                                                                                                                    | 结果                    |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| 测试收集          | `pytest --collect-only -q`                                                                                                                                              | exit 0；共 589 项       |
| 全量测试          | `pytest -q`                                                                                                                                                             | exit 0；观察到 1 skip   |
| 覆盖率            | `pytest --cov=backend --cov-fail-under=85 -q`                                                                                                                           | exit 0；总覆盖率 91.31% |
| Batch2.5 关键套件 | `pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py tests/test_batch25_production_data_gate.py tests/test_datasource_service.py -q` | exit 0                  |
| 维护/边界套件     | `pytest tests/test_module_boundaries.py tests/test_global_execution_rules.py tests/test_documentation_index.py tests/test_manifest_protocol.py -q`                      | exit 0                  |

## 4. 覆盖与可维护性证据

- 总覆盖率通过 85% 门槛：91.31%。
- 低覆盖热点：`backend/app/layer1_axes/observation_mapper.py` 55%，`backend/app/storage/raw_store.py` 54%，`backend/app/ops/db_inspector.py` 77%。
- Batch2.5 repair verification 指出 A4-01..06、G-A8-01/02 均有测试关闭。
- 当前 `ingestion.py` 92% 覆盖，但文件过长，覆盖率不能抵消维护复杂度。

## 5. P0/P1/P2/P3

### P0

无。

### P1

| ID        | 问题                       | 证据                                                                             | 影响                                             | 当前阶段可修复?             | 修复状态 | 解决方案                                                                      |
| --------- | -------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------- | -------- | ----------------------------------------------------------------------------- |
| A05-P1-01 | 关键边界模块单文件覆盖率低 | coverage：`observation_mapper.py` 55%，`raw_store.py` 54%，`db_inspector.py` 77% | raw payload/path/DB inspect 异常路径未充分防回归 | 是，但用户禁止代码/测试变更 | 未修复   | 补充异常输入、路径逃逸、缺字段、read-only DB error、malformed raw JSON 等测试 |
| A05-P1-02 | full pytest skip 未定位    | full pytest 输出含 1 skip；collect-only 589                                      | 不能确认 skip 是否可接受                         | 是                          | 未修复   | 运行 verbose skip report 并记录 skip reason；必要时补替代验证                 |

### P2

| ID        | 问题                                                  | 证据                                                                                  | 影响                                 | 当前阶段可修复? | 修复状态 | 解决方案                                                                                                          |
| --------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------ | --------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| A05-P2-01 | 维护文档与历史 audit report 存在 stale narrative 风险 | repair verification 曾列出 PH/A5/A1 stale OPEN 后已 reconcile，但历史报告仍需人工核验 | 后续 agent 可能读取旧 narrative 误判 | 是              | 未修复   | 在最终 closeout 中明确 authoritative evidence path：registry + final_registry_update + latest repair verification |
| A05-P2-02 | 测试覆盖率总分掩盖局部薄弱模块                        | coverage 总 91.31%，但局部 54–55%                                                     | 局部边界风险                         | 是              | 未修复   | 为 coverage gate 增加模块级阈值或至少对 storage/mapper/ops 添加 focused tests                                     |

### P3

| ID        | 问题                             | 影响                     | 解决方案                                            |
| --------- | -------------------------------- | ------------------------ | --------------------------------------------------- |
| A05-P3-01 | `.audit-sandbox*` 与测试缓存较多 | 低；可能影响人工审计噪音 | release 前按 final_package_rules 清理或标注保留原因 |

## 6. 当前未修复原因

用户要求只产出报告，不允许修改测试或代码。因此补测、清理、阈值调整均列为最小修复清单。

## 7. 评分

**90 / 100 — FAIL**

扣分依据：局部低覆盖 -4；skip 未定位 -2；维护性受长模块影响 -2；历史/测试产物噪音 -1；缺模块级覆盖门槛 -1。

## 8. 达到 95+ 的最小修复清单

1. 补测 `observation_mapper.py`、`raw_store.py`、`db_inspector.py`，将关键边界覆盖提升到合理水平。
2. 定位并记录 1 个 skipped test 的原因。
3. 对 Batch2.5 authoritative evidence 建立单一索引，避免旧 audit narrative 误导。
4. 在 CI 增加 coverage/skip 可见性。

## 9. 结论

本维度 **FAIL**。测试总量和总体覆盖率不错，但局部边界覆盖与维护噪音不满足 95+ 标准。
