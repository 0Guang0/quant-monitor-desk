# Round3 Batch2.5 — 9-Agent 对抗性审计总报告

## 0. 审计基准

用户纠正后的当前项目进度为：**Round3 Batch2.5 已完成**。本轮审计以归档任务 `.trellis/tasks/archive/2026-06/06-20-round3-batch2-5-layer1-obs-ingest/` 为权威完成证据，而不是旧 handoff 中的“Batch2.5 execute ready”叙述。

用户后续明确限制：**只产出报告，不得进行代码变更**。因此本轮未修复代码/测试/配置/设计文档；所有发现项均给出修复方案、当前阶段可修复性与未修复原因。

## 1. 统一执行边界

- 真实生产/live source 未执行。原因：`018B_production_live_pilot_gate.md` 与 `production_live_pilot_policy.md` 要求显式用户授权、sandbox-first、raw_only-first、禁止 production clean DB mutation。
- 对维度 1/2/8/9 的生产验证采用生产等价替代：policy gate、Batch2.5 production-data gate、DataSourceService route/E2E、DB/schema/write/validation tests、frontend production build、read-only evidence 核对。
- 未污染项目业务代码：未进行代码、测试、配置或设计文档修改；只运行读取/搜索/测试命令并写入报告文件。
- `ruff check .` 被 CodexPro safe bash allowlist 拒绝执行，已在相关报告记录，不计入有效工具。

## 2. 执行过的核心命令

| 命令                                                                                                                                                                                                        | 结果                                      |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `pytest -q`                                                                                                                                                                                                 | exit 0；收集 589 项；观察到 1 skip        |
| `pytest --cov=backend --cov-fail-under=85 -q`                                                                                                                                                               | exit 0；backend coverage 91.31%           |
| `pytest --collect-only -q`                                                                                                                                                                                  | exit 0；589 项                            |
| `pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py tests/test_batch25_production_data_gate.py tests/test_datasource_service.py -q`                                     | exit 0                                    |
| `pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py tests/test_layer1_observation_ingestion.py tests/test_layer1_ingestion_gates.py tests/test_batch25_production_data_gate.py -q` | exit 0                                    |
| `pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q`                                                                                                           | exit 0；11 tests passed                   |
| `pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_data_cli_contract.py tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py -q`     | exit 0                                    |
| `pytest tests/test_ops_db_inspector.py tests/test_duckdb_connection.py tests/test_schema_contract.py tests/test_schema_migration.py -q`                                                                     | exit 0；含 1 skip                         |
| `pytest tests/test_write_manager.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_db_validation_gate.py -q`                                                       | exit 0                                    |
| `pytest tests/test_module_boundaries.py tests/test_global_execution_rules.py tests/test_documentation_index.py tests/test_manifest_protocol.py -q`                                                          | exit 0                                    |
| `npm run typecheck`                                                                                                                                                                                         | exit 0                                    |
| `npm test` in `frontend`                                                                                                                                                                                    | 2 files / 3 tests passed                  |
| `npm run build` in `frontend`                                                                                                                                                                               | exit 0；Vite build 88ms；JS gzip 60.16 kB |

## 3. 9 个独立 agent 评分

| Agent    | 维度               | 分数 | 结论 | 主要原因                                                                |
| -------- | ------------------ | ---: | ---- | ----------------------------------------------------------------------- |
| Agent 01 | 当前完成情况与准入 |   88 | FAIL | Batch2.5 仅 staged；Batch2.75 live pilot 未执行；schema/DB deferred     |
| Agent 02 | 实现与设计偏差     |   86 | FAIL | schema.sql vs migration 011 drift；live pilot 只是 policy/planning gate |
| Agent 03 | Ponytail 简化/冗余 |   82 | FAIL | `ingestion.py` 1,516 LOC，长方法 369 行，evidence/runtime 混置          |
| Agent 04 | 代码质量           |   91 | FAIL | ruff 未验证、长模块、低覆盖热点、skip 未定位                            |
| Agent 05 | 可维护性与测试覆盖 |   90 | FAIL | 局部低覆盖、skip 未定位、历史审计 narrative/产物噪音                    |
| Agent 06 | 规范性/工程/架构   |   90 | FAIL | Batch2.75 未闭环、schema authority 分裂、workspace hygiene              |
| Agent 07 | 解耦性/嵌套        |   83 | FAIL | Layer1 ingestion 内部耦合高，Phase3/4 seam 重复，evidence/runtime 耦合  |
| Agent 08 | 性能占用与速度     |   87 | FAIL | 未执行 live/scale benchmark，full pytest 约 155s，缺性能预算 gate       |
| Agent 09 | 数据库             |   84 | FAIL | schema.sql drift、缺 DB CHECK、migration 008/liveness deferred          |

**整体结论：FAIL。** 用户定义要求所有维度均达到 95+ 才算 PASS；当前 9 个维度均低于 95。

## 4. 当前是否可以进入下一阶段

- 可以进入：**Batch2.75 controlled production/live pilot**。
- 可以有条件进入：**Batch3 规划/实施**，但必须显式限定为 **fixture/staged semantics only**，不得声称 production-live ready。
- 不可以进入：任何把 Batch2.5 结果宣传为真实生产数据已验证、live source 已闭环、或 production clean DB ready 的阶段。

## 5. 最高优先级最小修复清单

1. **执行或正式 re-defer Batch2.75 live pilot**：必须有授权、read-only baseline、route dry-run、raw-only live micro-fetch、sandbox validation、no production DB mutation proof。
2. **修复 schema authority drift**：同步 `specs/schema/schema.sql` 与 migration 011，或正式声明 migrations 为 DB contract authority 并加测试/ADR。
3. **补 DB CHECK / app-validator 决策闭环**：`axis_observation` timestamp ordering 与 migration 008 broad CHECK 需要迁移或明确 ADR+测试。
4. **拆分 Layer1 ingestion 复杂度**：`commit_clean_observation_and_snapshots`、Phase3/4 fetch path、evidence writers 应分层/复用。
5. **补低覆盖热点测试**：`observation_mapper.py`、`raw_store.py`、`db_inspector.py`。
6. **补完整质量门禁**：在 full shell/CI 执行 `ruff check .`、`ruff format --check .`；定位 full pytest skip。
7. **建立性能证据**：执行 production-equivalent smoke 或授权 live pilot 指标，记录 test tier、bundle budget、ResourceGuard budget。
8. **清理/确认工作区**：解释 modified/untracked 文件、异常 `=` 路径、审计/测试产物保留原因。

## 6. 独立报告文件清单

- `ROUND3_BATCH25_AUDIT_AGENT_01_COMPLETION_QUALITY.md`
- `ROUND3_BATCH25_AUDIT_AGENT_02_DESIGN_DEVIATION.md`
- `ROUND3_BATCH25_AUDIT_AGENT_03_PONYTAIL.md`
- `ROUND3_BATCH25_AUDIT_AGENT_04_CODE_QUALITY.md`
- `ROUND3_BATCH25_AUDIT_AGENT_05_MAINTAINABILITY_TEST_COVERAGE.md`
- `ROUND3_BATCH25_AUDIT_AGENT_06_ENGINEERING_ARCHITECTURE.md`
- `ROUND3_BATCH25_AUDIT_AGENT_07_DECOUPLING_NESTING.md`
- `ROUND3_BATCH25_AUDIT_AGENT_08_PERFORMANCE.md`
- `ROUND3_BATCH25_AUDIT_AGENT_09_DATABASE.md`

## 7. 最终判定

**整体 FAIL。** 当前项目的 Round3 Batch2.5 已完成且 staged 证据链基本可追溯；但由于 live pilot、schema/DB contract、pony-tail 复杂度、局部测试覆盖、性能证据与工作区卫生等问题，不能按用户定义判定为 95+ PASS。
