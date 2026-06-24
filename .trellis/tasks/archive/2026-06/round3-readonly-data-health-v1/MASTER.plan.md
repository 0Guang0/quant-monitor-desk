# MASTER 计划 — C-20 Read-only Data Health v1

> **Execute 入口** — staged-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`

---

## 0. 元信息

| 字段                      | 值                                                             |
| ------------------------- | -------------------------------------------------------------- |
| 任务 slug                 | `round3-readonly-data-health-v1`                               |
| 分支                      | `feature/round3-readonly-data-health-v1`                       |
| Worktree                  | `../quant-monitor-desk-wt-r3-data-health`                      |
| 前置                      | staged pilot v2 archived；`db_inspector` Phase A on master     |
| manifest_protocol_version | `3`                                                            |
| analysis_waiver           | `false`                                                        |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md` |

### Staged / Wave C limitations（强制）

1. `production_live_pilot_policy.md` — **不得**声称 production-live
2. `R3-B2.75-REQ2-EM` — **DEFERRED**；不得作 live unblock 依据
3. `staged_acceptance_policy.md` — staged evidence only
4. Wave C playbook §2.2 — TDD、ponytail（含 `tests/`）、五字段 docstring、全量 pytest
5. Wave C playbook §2.3 — 全部 agent **`composer-2.5`**（禁 `composer-2.5-fast`）
6. MAP §2.2 — allowed/forbidden 文件组锁定

### Failure modes / 回滚

| 场景                    | 处理                                                                  |
| ----------------------- | --------------------------------------------------------------------- |
| 触发 forbidden 路径修改 | 立即停止；revert                                                      |
| production DB 变异      | 中止；不勾 GREEN                                                      |
| source fetch 执行       | 中止；违反 AC-DH-BOUND                                                |
| scope 偏离 R3Y 任务卡   | 退回 Plan                                                             |
| 回滚                    | 删除 `data_health*.py` + `test_ops_data_health.py`；无 prod migration |

### 0.1 门控速查

| 项        | 值                                            |
| --------- | --------------------------------------------- |
| 怎么测    | §8 RED→GREEN；`tests/test_ops_data_health.py` |
| 怎么验收  | §10 Tier A + playbook §8.1                    |
| 什么叫过  | §2 全部 AC-DH-\*                              |
| prod-path | Tier B：`uv run pytest -q`（仅 §8.10）        |
| 6.pre     | `research/gitnexus-summary.md`                |

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；先读 `research/integration-ledger.md`。  
**禁止**在 §8.0 枚举路径清单 — 以 §0.3 + implement.jsonl 为准。

### 0.3a Execute 工程纪律 — Ponytail

1. Boot 起 MUST Read `.cursor/rules/ponytail.mdc`；每 §8.x 步开始前对照 ladder
2. 写业务代码前：YAGNI → 复用 `db_inspector` / `validators` / `staged_pilot` 常量 → 最小 diff
3. 禁止新框架、未请求 helper、新依赖；`ponytail:` 标注已知天花板
4. TDD：RED → karpathy-guidelines → testing-guidelines → ponytail → GREEN

### 0.3b Execute 工程纪律 — 测试与回归

1. 每 §8.x 先 RED（必须 FAIL）再 GREEN
2. 每步 GREEN 后 Read `incremental-implementation`；Tier B 全库仅 §8.10 一次
3. 测试五字段 docstring（playbook §2.2.1）；`tests/` 代码同样 ponytail（§2.2.2）
4. 禁止弱化测试目的

### 0.4 上下文打包（v3）

Execute 以 MASTER inline + ledger + `implement.jsonl` 为准；`context_pack.json` slot 2 由 router 填充。

### Source Context Index（Playbook §3.1 + §3.2 全文）

> Agent-2 质检：下表 **每一行** 须与 `implement.jsonl` 可索引；摘要一句供 Execute 路由。

#### §3.1 四路共用底座

| 路径                                                          | 遵守什么                              | 摘要                                              | implement |
| ------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------- | --------- |
| `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                 | Wave C 派发、PASS、模型、测试铁律     | §2.2 TDD/ponytail/五字段；§8.1 C-20 PASS          | [x]       |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2–§2.6                | worktree、allowed/forbidden、验证命令 | C-20 allowed `data_health*`；merge 顺序 C-20 第一 | [x]       |
| `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §6 | 一分支一核心文件组                    | 禁止与 022/β-2 抢文件                             | [x]       |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                             | 开放/已关闭 ID；**只读**              | 本分支不改 registry                               | [x]       |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                          | 操作面 OPEN 项                        | 只读对照                                          | [x]       |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                            | 防重复打开                            | 只读对照                                          | [x]       |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`  | ID → 任务/分支映射                    | C-20 不在此关 registry                            | [x]       |
| `docs/ROUND3_HANDOFF.md`                                      | Round 3 入口与 staged-only 语境       | staged-only 起手                                  | [x]       |
| `docs/quality/staged_acceptance_policy.md`                    | 分阶段验收                            | backend 分层验收                                  | [x]       |
| `docs/quality/production_live_pilot_policy.md`                | 不得声称 production-live              | fail-closed pilot 语境                            | [x]       |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`               | Batch 3 下游 staged 门禁              | 语境只读；本任务不建 L2–L4                        | [x]       |
| `docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md`          | 测试五字段                            | §5.0 对齐                                         | [x]       |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`         | docs/specs 非实现路径                 | 边界：只改 allowed                                | [x]       |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`          | 语义测试                              | 非 call-only                                      | [x]       |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`         | eco / ResourceGuard                   | 默认 eco；禁 full scan                            | [x]       |
| `specs/contracts/runtime_versions.md`                         | 工具链与验证命令权威                  | `uv run pytest`                                   | [x]       |
| `specs/contracts/write_contract.yaml`                         | 写路径合约                            | 本任务零写路径                                    | [x]       |
| `specs/contracts/resource_limits.yaml`                        | 资源上限                              | scan cap                                          | [x]       |
| `specs/contracts/snapshot_lineage_contract.yaml`              | 快照血缘                              | lineage 检查语境                                  | [x]       |
| `docs/architecture/module_boundary_matrix.md`                 | 模块边界                              | ops vs layer4                                     | [x]       |
| `MIGRATION_MAP.md`                                            | 实现目录与文档映射                    | ops 落点                                          | [x]       |

#### §3.2 C-20 — 只读 Data Health

**任务卡 / Prompt**

| 路径                                                                                                     | 用途                            | 摘要                  | implement |
| -------------------------------------------------------------------------------------------------------- | ------------------------------- | --------------------- | --------- |
| `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_20_feature_round3_readonly_data_health_v1.md` | 分支启动、验证命令              | 九切片 + allowed 文件 | [x]       |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`            | AC、九切片、禁止项、报告 schema | 权威任务卡            | [x]       |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_execution_discipline_addendum.md`      | TDD / ponytail / 全量 pytest    | Execute 纪律          | [x]       |

**`docs/` 设计文档**

| 路径                                                    | 用途                               | 摘要                                 | implement |
| ------------------------------------------------------- | ---------------------------------- | ------------------------------------ | --------- |
| `docs/ops/data_health_cli.md`                           | CLI 行为与只读边界                 | Batch6 设计；v1 子集 + evidence 模式 | [x]       |
| `docs/ops/db_inspect_cli.md`                            | DB/数据根只读检查模式              | 与 db-inspect 分工                   | [x]       |
| `docs/ops/verification_commands.md`                     | Round 3 gate hygiene pytest 矩阵   | §10 回归引用                         | [x]       |
| `docs/modules/data_validation_and_conflict.md`          | 校验与冲突语义                     | validator 权威                       | [x]       |
| `docs/modules/duckdb_and_parquet.md`                    | 只读 DuckDB/Parquet 约定           | 只读连接                             | [x]       |
| `docs/modules/write_manager.md`                         | **禁止绕过** WriteManager 写 clean | 本任务不写 clean                     | [x]       |
| `docs/modules/data_sources.md`                          | source 角色与 disabled 默认        | DISABLED_SOURCE_USED 规则            | [x]       |
| `docs/modules/ops_and_performance.md`                   | ops 模块边界                       | ops 包范围                           | [x]       |
| `docs/quality/ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §3 | `R3-B2.75-REQ2-EM` 等硬约束        | REQ2-EM 保持 DEFERRED                | [x]       |

**`specs/` 契约与注册表**

| 路径                                                 | 用途                           | 摘要                       | implement |
| ---------------------------------------------------- | ------------------------------ | -------------------------- | --------- |
| `specs/contracts/data_quality_rules.yaml`            | rule_id、severity 语义         | §5.1 rule 子集 SSOT        | [x]       |
| `specs/contracts/source_conflict_rules.yaml`         | 冲突与 reconcile 规则          | 只读报告冲突               | [x]       |
| `specs/contracts/ops_db_inspect_contract.yaml`       | 只读 inspect 合约              | 与 db_inspector 对齐       | [x]       |
| `specs/contracts/source_route_contract.yaml`         | route / validation_only        | VALIDATION_ONLY_AS_PRIMARY | [x]       |
| `specs/contracts/ops_health_check_contract.yaml`     | health 报告 envelope（若触及） | envelope 字段参考          | [x]       |
| `specs/datasource_registry/source_registry.yaml`     | source 启用与角色              | disabled 默认              | [x]       |
| `specs/datasource_registry/source_capabilities.yaml` | capability / validation_only   | misuse 检测                | [x]       |

**前序证据（Execute 须引用路径）**

| 路径                                                                                        | 用途                          | 摘要                                           | implement |
| ------------------------------------------------------------------------------------------- | ----------------------------- | ---------------------------------------------- | --------- |
| `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/execute-evidence/`   | PROMPT_19 v2 证据（**优先**） | §8.9 默认 evidence 根                          | [x]       |
| `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/`                    | PROMPT_14 证据（回退）        | v2 缺失时回退；含 `merge_gate_report.md`       | [x]       |
| `.trellis/tasks/fix-round3-post14-audit-staged-pilot/execute-evidence/merge_gate_report.md` | PROMPT_14 审计 merge gate     | post14 审计语境                                | [x]       |
| `AGENTS.md`                                                                                 | Trellis 全员路由              | Execute 纪律入口                               | [x]       |
| `CLAUDE.md`                                                                                 | GitNexus / worktree 协议      | impact 前置                                    | [x]       |
| `.trellis/workflow.md`                                                                      | Trellis 阶段机                | Plan/Execute 门控                              | [x]       |
| `.trellis/spec/guides/complex-task-planning-protocol.md`                                    | 复杂任务 Plan 协议            | freeze 门禁                                    | [x]       |
| `backend/app/storage/raw_store.py`                                                          | raw/staging 路径（只读）      | loader 路径语境；**禁改** `staged_evidence.py` | [x]       |
| `backend/app/datasources/source_registry.py`                                                | source 启用对照               | DISABLED_SOURCE_USED 语境                      | [x]       |
| `tests/fixtures/data_health/`                                                               | 合成坏/好 fixture             | §8.3–8.6 最小数据                              | [x]       |

**实现邻接（Execute 必读代码）**

| 路径                                        | 用途                      | 摘要                         | implement |
| ------------------------------------------- | ------------------------- | ---------------------------- | --------- |
| `backend/app/ops/db_inspector.py`           | 只读 inspect 模式         | `InspectReport` 形态         | [x]       |
| `backend/app/ops/staged_pilot.py`           | manifest 常量/evidence 名 | `RAW_MANIFEST_JSON` 等       | [x]       |
| `backend/app/ops/mutation_proof.py`         | 无变异证明语境            | `production_db_mutated` 对照 | [x]       |
| `backend/app/db/validation_gate.py`         | validation_report 语境    | gate 输入字段                | [x]       |
| `backend/app/validators/data_quality.py`    | 数据质量规则              | 复用 rule 语义               | [x]       |
| `backend/app/validators/source_conflict.py` | 冲突规则                  | 只读摘要                     | [x]       |
| `tests/test_ops_db_inspector.py`            | db inspect 回归           | Tier A 邻接                  | [x]       |
| `tests/test_staged_pilot.py`                | staged pilot 回归         | Tier A 邻接                  | [x]       |
| `tests/test_data_quality_validator.py`      | DQ 回归                   | Tier A 邻接                  | [x]       |
| `tests/test_source_conflict_validator.py`   | 冲突回归                  | Tier A 邻接                  | [x]       |
| `tests/test_db_validation_gate.py`          | validation gate 回归      | Tier A 邻接                  | [x]       |
| `tests/test_raw_store.py`                   | raw store 回归            | Tier A 邻接                  | [x]       |

---

## 1. 目标

交付最小 **read-only data health** 能力：加载 staged pilot evidence/manifest，按 contract rule 子集检查，输出 JSON + 人可读 summary；可作为 sandbox clean-write rehearsal 的 **gate 输入**（陈述充分性，不声称 production-live）。

### 1.2 前置

- `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2` 已归档
- `backend/app/ops/db_inspector.py` 已存在（只读模式参考）

### 1.3 约束

- **Allowed:** `backend/app/ops/data_health*.py`, `tests/test_ops_data_health.py`, 本任务 evidence
- **Forbidden:** `layer4_markets/**`, `staged_evidence.py`, registry 三件套, production DB write, live fetch, migration, free SQL, full market scan

### 1.5 停止条件

| #   | 事件                                                       | 处理                    |
| --- | ---------------------------------------------------------- | ----------------------- |
| 1   | Plan 未 freeze / 用户未批准                                | 禁止 `task.py start`    |
| 2   | 修改 forbidden 路径（layer4 / staged_evidence / registry） | 立即停止；revert        |
| 3   | RED 非预期全库红                                           | 停当前 §8 步            |
| 4   | 执行 source fetch 或 production DB 写                      | 中止；不勾 GREEN        |
| 5   | 自定义：声称 production-live 或 REQ2-EM unblock            | 停止；修正 MASTER/AUDIT |
| 6   | 自定义：仅实现 CLI 壳无 §8.3–8.6 规则测                    | 停止；回 Plan           |
| 7   | 自定义：改动测试目的换取 GREEN                             | 停止；恢复 purpose      |

### 1.6 原计划归并

| 来源                             | 内容                           |
| -------------------------------- | ------------------------------ |
| `R3Y_readonly_data_health_v1.md` | 九切片、rule 子集、报告 schema |
| `PROMPT_20`                      | 启动边界、验证命令             |
| Playbook §8.1                    | PASS 子 AC → §2                |
| MAP §2.2 C-20                    | allowed/forbidden              |

---

## 2. 预期结果（AC）— 抄自 Playbook §8.1

| ID          | 维度     | PASS 条件                                                                                    | 验证链   |
| ----------- | -------- | -------------------------------------------------------------------------------------------- | -------- |
| AC-DH-PLAN  | Plan     | `validate-plan-freeze` exit 0；`implement.jsonl` 覆盖 R3Y-DH-01..09；§3.1+§3.2 全文已索引    | freeze   |
| AC-DH-IMPL  | 实现     | `data_health*.py` 存在；只读；无 prod DB 写、source fetch、migration、free SQL               | §8.8     |
| AC-DH-BIZ   | 业务 AC  | 对 staged pilot v2 evidence 产出 JSON + 人可读 summary；坏 fixture meaningful FAIL           | §8.9     |
| AC-DH-RULES | 规则面   | 覆盖 §5.1 rule_id 子集（OHLC、duplicate key、lineage、staleness、validation-only misuse 等） | §8.3–8.6 |
| AC-DH-SLICE | 切片证据 | 每个 `/to-issues` 切片独立可跑测试 + execute-evidence RED/GREEN                              | §8.1–8.9 |
| AC-DH-TEST  | 测试     | `test_ops_data_health.py` 全绿；五字段 + §2.2.2 测试 ponytail；语义断言                      | §10      |
| AC-DH-MAP   | MAP 验证 | §10 Tier A 命令绿；邻接测试绿                                                                | §10      |
| AC-DH-AUDIT | Audit    | A1–A8 报告；`audit_matrix.json` 无 OPEN；对抗性零遗留                                        | Audit    |
| AC-DH-BOUND | 边界     | 未改 forbidden；未声称 production-live / clean-write 已授权                                  | §8.8–8.9 |
| AC-DH-GATE  | 门禁陈述 | 报告含 `sandbox_clean_write_gate_ready` + `gate_rationale`；merge gate 证据可审计            | §8.9     |

---

## 3. 范围

### 3.1 In scope

- `backend/app/ops/data_health.py` — model、loader、rules、report builder、service
- `backend/app/ops/data_health_cli.py` — read-only CLI（若薄包装更短则合并进上文件）
- `tests/test_ops_data_health.py`
- `tests/fixtures/data_health/` — 最小坏/好 fixture（Execute 创建）
- `.trellis/tasks/round3-readonly-data-health-v1/execute-evidence/`

### 3.2 Out of scope · defer

| 项                                 | 边界                      | 偿还            |
| ---------------------------------- | ------------------------- | --------------- |
| 完整 Batch6 `qmd data health` 平台 | out                       | Batch 6         |
| `source_health_snapshot` clean 表  | **禁止**                  | Batch 6         |
| DuckDB full domain scan            | out — evidence-path first | Batch 6         |
| registry 三件套更新                | out — 主会话批处理        | Wave C merge 后 |

### 3.3 禁止修改

- `backend/app/layer4_markets/**`
- `backend/app/storage/staged_evidence.py`
- `docs/AUDIT_DEFERRED_REGISTRY.md`、`docs/UNRESOLVED_ISSUES_REGISTRY.md`、`docs/RESOLVED_ISSUES_REGISTRY.md`
- production DB / live fetch / migration

---

## 4. 代码地图

| 路径                                 | 操作                       |
| ------------------------------------ | -------------------------- |
| `backend/app/ops/data_health.py`     | 创建 — core service        |
| `backend/app/ops/data_health_cli.py` | 创建（可选）— CLI entry    |
| `tests/test_ops_data_health.py`      | 创建 — §5.3 用例           |
| `tests/fixtures/data_health/`        | 创建 — 坏/好 manifest 子集 |

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring：覆盖范围、测试对象、目的/目标、验证点、失败含义（中文）
2. `tests/` 代码遵守 playbook §2.2.2 ponytail
3. 每测至少一条业务语义断言（`overall_status`、具体 `rule_id` FAIL 等）

### 5.1 测试文件路径

| 路径                            | 目标文件                         | 测试目的                | §8 步   |
| ------------------------------- | -------------------------------- | ----------------------- | ------- |
| `tests/test_ops_data_health.py` | `backend/app/ops/data_health.py` | read-only health 全切片 | 8.1–8.9 |

### 5.2 成功/失败语义

| 能力        | 成功怎么测            | 失败怎么测         | 场景 |
| ----------- | --------------------- | ------------------ | ---- |
| model       | dataclass roundtrip   | 非法 severity 拒绝 | S1   |
| loader      | 读 v2 manifest        | 缺文件 → FAIL      | S2   |
| daily bar   | 好 bar PASS           | 坏 OHLC → FAIL     | S3   |
| lineage     | 完整 lineage PASS     | 缺 hash → FAIL     | S4   |
| report      | JSON+text 字段齐全    | 缺 overall_status  | S5   |
| integration | v2 evidence PASS/WARN | 空目录 FAIL        | S6   |

### 5.3 用例设计

| 测试文件                        | `test_*` 名称                                     | 断言语义                     | §8  |
| ------------------------------- | ------------------------------------------------- | ---------------------------- | --- |
| `tests/test_ops_data_health.py` | `test_dataHealthModel_roundtrip_success`          | severity/rule_id 映射        | 8.1 |
| 同上                            | `test_dataHealthLoader_missingManifest_fails`     | loader 失败路径              | 8.2 |
| 同上                            | `test_dataHealthDailyBar_invalidOhlc_fails`       | INVALID_OHLC                 | 8.3 |
| 同上                            | `test_dataHealthMetadata_emptyTitle_fails`        | MISSING_REQUIRED_FIELD       | 8.4 |
| 同上                            | `test_dataHealthLineage_missingContentHash_fails` | MISSING_CONTENT_HASH         | 8.5 |
| 同上                            | `test_dataHealthStaleness_staleData_fails`        | STALE_DATA                   | 8.6 |
| 同上                            | `test_dataHealthReport_jsonAndText_success`       | JSON+markdown 字段           | 8.7 |
| 同上                            | `test_dataHealthCli_readOnly_exitZero`            | CLI 只读 exit 0              | 8.8 |
| 同上                            | `test_dataHealthIntegration_v2Evidence_bundle`    | v2 evidence 集成 + gate 字段 | 8.9 |

### 5.3b rule_id 覆盖矩阵（AC-DH-RULES）

> 同一 §8.x 步可含多个 `test_*`（共享 RED/GREEN 证据）；fixture 放 `tests/fixtures/data_health/`（ponytail：每 rule 一条最小坏行）。

| rule_id                      | §8 步 | `test_*`（或 `-k` 前缀）                            |
| ---------------------------- | ----- | --------------------------------------------------- |
| `MISSING_REQUIRED_FIELD`     | 8.4   | `test_dataHealthMetadata_emptyTitle_fails`          |
| `DUPLICATE_PRIMARY_KEY`      | 8.3   | `test_dataHealthDailyBar_duplicateKey_fails`        |
| `INVALID_OHLC`               | 8.3   | `test_dataHealthDailyBar_invalidOhlc_fails`         |
| `NEGATIVE_VOLUME`            | 8.3   | `test_dataHealthDailyBar_negativeVolume_fails`      |
| `EMPTY_RESPONSE`             | 8.6   | `test_dataHealthStaleness_emptyResponse_fails`      |
| `INSUFFICIENT_HISTORY`       | 8.3   | `test_dataHealthDailyBar_insufficientHistory_fails` |
| `MISSING_SOURCE_USED`        | 8.5   | `test_dataHealthLineage_missingSourceUsed_fails`    |
| `MISSING_SOURCE_FETCH_ID`    | 8.5   | `test_dataHealthLineage_missingFetchId_fails`       |
| `MISSING_CONTENT_HASH`       | 8.5   | `test_dataHealthLineage_missingContentHash_fails`   |
| `MISSING_AS_OF_TIMESTAMP`    | 8.5   | `test_dataHealthLineage_missingAsOf_fails`          |
| `VALIDATION_ONLY_AS_PRIMARY` | 8.5   | `test_dataHealthLineage_validationOnlyMisuse_fails` |
| `DISABLED_SOURCE_USED`       | 8.5   | `test_dataHealthLineage_disabledSource_fails`       |
| `STALE_DATA`                 | 8.6   | `test_dataHealthStaleness_staleData_fails`          |

### 5.4 四层测试

| 层      | 命令                                             | 通过             |
| ------- | ------------------------------------------------ | ---------------- |
| L1 单元 | `uv run pytest tests/test_ops_data_health.py -q` | exit 0           |
| L2 邻接 | MAP §2.2 C-20 邻接 pytest 命令                   | exit 0           |
| L3 管道 | —                                                | N/A              |
| L4 E2E  | `uv run pytest -q`                               | exit 0；仅 §8.10 |

---

## 6. 接口/契约

- **规则 SSOT:** `specs/contracts/data_quality_rules.yaml` — §5.1 rule_id 子集
- **报告 schema:** `R3Y_readonly_data_health_v1.md` §10 + `docs/ops/data_health_cli.md` §6
- **只读:** `production_db_mutated: false`, `source_fetch_performed: false` 硬编码且可测
- **门禁:** `sandbox_clean_write_gate_ready: bool` + `gate_rationale: string`（grill-me Q4；playbook §8.1 门禁陈述）
- **Evidence 根（默认）:** `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/execute-evidence/`

### 6.1 冻结 rule_id 子集（最小）

`MISSING_REQUIRED_FIELD`, `DUPLICATE_PRIMARY_KEY`, `INVALID_OHLC`, `NEGATIVE_VOLUME`, `EMPTY_RESPONSE`, `INSUFFICIENT_HISTORY`, `MISSING_SOURCE_USED`, `MISSING_SOURCE_FETCH_ID`, `MISSING_CONTENT_HASH`, `MISSING_AS_OF_TIMESTAMP`, `VALIDATION_ONLY_AS_PRIMARY`, `DISABLED_SOURCE_USED`, `STALE_DATA`

---

## 7. Red Flags

| 风险                        | 预防                     |
| --------------------------- | ------------------------ |
| CLI 空壳                    | 九切片 §8.3–8.6 强制     |
| 写 DB / fetch               | forbidden + 报告字段断言 |
| 改 staged_evidence / layer4 | §3.3                     |
| 弱断言                      | GLOBAL_TESTING_POLICY    |
| production-live 声称        | §0 + gate_rationale      |
| 测试 fixture 膨胀           | §2.2.2 ponytail          |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Boot gate

| 字段               | 内容                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| 做什么             | 按 **§0.3** Read `implement.jsonl` 每一条 + `research/integration-ledger.md`；§0.3a ponytail；基线 RED pytest |
| RED 命令           | `uv run pytest tests/test_ops_data_health.py -q`                                                              |
| GREEN 命令         | `uv sync --locked` + `execute-evidence/8.0-boot-reads.txt`                                                    |
| RED 证据           | `execute-evidence/8.0-red.txt`                                                                                |
| GREEN 证据         | `execute-evidence/8.0-green.txt`                                                                              |
| 绑定 Execute Skill | trellis-execute · gitnexus-impact                                                                             |
| 已执行             | [x]                                                                                                           |

### 8.1 R3Y-DH-01 — DataHealth rule model

| 字段       | 内容                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------- |
| 切片       | R3Y-DH-01                                                                                |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py::test_dataHealthModel_roundtrip_success -q` |
| GREEN 命令 | 同上 exit 0                                                                              |
| RED 证据   | `execute-evidence/8.1-red.txt`                                                           |
| GREEN 证据 | `execute-evidence/8.1-green.txt`                                                         |
| 已执行     | [x]                                                                                      |

### 8.2 R3Y-DH-02 — Manifest loader

| 字段       | 内容                                                                                          |
| ---------- | --------------------------------------------------------------------------------------------- |
| 切片       | R3Y-DH-02                                                                                     |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py::test_dataHealthLoader_missingManifest_fails -q` |
| GREEN 命令 | 同上 exit 0                                                                                   |
| RED 证据   | `execute-evidence/8.2-red.txt`                                                                |
| GREEN 证据 | `execute-evidence/8.2-green.txt`                                                              |
| 已执行     | [x]                                                                                           |

### 8.3 R3Y-DH-03 — Daily bar health

| 字段       | 内容                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| 切片       | R3Y-DH-03                                                                |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py -k "dataHealthDailyBar" -q` |
| GREEN 命令 | 同上 exit 0                                                              |
| RED 证据   | `execute-evidence/8.3-red.txt`                                           |
| GREEN 证据 | `execute-evidence/8.3-green.txt`                                         |
| 已执行     | [x]                                                                      |

### 8.4 R3Y-DH-04 — Metadata health

| 字段       | 内容                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------ |
| 切片       | R3Y-DH-04                                                                                  |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py::test_dataHealthMetadata_emptyTitle_fails -q` |
| GREEN 命令 | 同上 exit 0                                                                                |
| RED 证据   | `execute-evidence/8.4-red.txt`                                                             |
| GREEN 证据 | `execute-evidence/8.4-green.txt`                                                           |
| 已执行     | [x]                                                                                        |

### 8.5 R3Y-DH-05 — Source lineage health

| 字段       | 内容                                                                    |
| ---------- | ----------------------------------------------------------------------- |
| 切片       | R3Y-DH-05                                                               |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py -k "dataHealthLineage" -q` |
| GREEN 命令 | 同上 exit 0                                                             |
| RED 证据   | `execute-evidence/8.5-red.txt`                                          |
| GREEN 证据 | `execute-evidence/8.5-green.txt`                                        |
| 已执行     | [x]                                                                     |

### 8.6 R3Y-DH-06 — Staleness/window health

| 字段       | 内容                                                                      |
| ---------- | ------------------------------------------------------------------------- |
| 切片       | R3Y-DH-06                                                                 |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py -k "dataHealthStaleness" -q` |
| GREEN 命令 | 同上 exit 0                                                               |
| RED 证据   | `execute-evidence/8.6-red.txt`                                            |
| GREEN 证据 | `execute-evidence/8.6-green.txt`                                          |
| 已执行     | [x]                                                                       |

### 8.7 R3Y-DH-07 — Report builder

| 字段       | 内容                                                                                        |
| ---------- | ------------------------------------------------------------------------------------------- |
| 切片       | R3Y-DH-07                                                                                   |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py::test_dataHealthReport_jsonAndText_success -q` |
| GREEN 命令 | 同上 exit 0                                                                                 |
| RED 证据   | `execute-evidence/8.7-red.txt`                                                              |
| GREEN 证据 | `execute-evidence/8.7-green.txt`                                                            |
| 已执行     | [x]                                                                                         |

### 8.8 R3Y-DH-08 — CLI/service entrypoint

| 字段       | 内容                                                                                   |
| ---------- | -------------------------------------------------------------------------------------- |
| 切片       | R3Y-DH-08                                                                              |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py::test_dataHealthCli_readOnly_exitZero -q` |
| GREEN 命令 | 同上 exit 0                                                                            |
| RED 证据   | `execute-evidence/8.8-red.txt`                                                         |
| GREEN 证据 | `execute-evidence/8.8-green.txt`                                                       |
| 已执行     | [x]                                                                                    |

### 8.9 R3Y-DH-09 — Integration with staged pilot evidence

| 字段       | 内容                                                                                           |
| ---------- | ---------------------------------------------------------------------------------------------- |
| 切片       | R3Y-DH-09                                                                                      |
| RED 命令   | `uv run pytest tests/test_ops_data_health.py::test_dataHealthIntegration_v2Evidence_bundle -q` |
| GREEN 命令 | 同上 exit 0                                                                                    |
| RED 证据   | `execute-evidence/8.9-red.txt`                                                                 |
| GREEN 证据 | `execute-evidence/8.9-green.txt`                                                               |
| 已执行     | [x]                                                                                            |

### 8.10 Final gates

| 字段       | 内容                                        |
| ---------- | ------------------------------------------- |
| 做什么     | Tier A + **Tier B 全库 pytest（唯一一次）** |
| GREEN 命令 | 见 §10                                      |
| GREEN 证据 | `execute-evidence/8.10-green.txt`           |
| 已执行     | [x]                                         |

---

## 9. 四层测试（汇总）

见 §5.4。

---

## 10. Tier 验收（MAP §2.2 C-20）

| Tier | 命令                                                                                                                                                                                                               | 通过                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| A    | `uv sync --locked`                                                                                                                                                                                                 | exit 0               |
| A    | `uv run pytest tests/test_ops_data_health.py -q`                                                                                                                                                                   | exit 0               |
| A    | `uv run pytest tests/test_ops_db_inspector.py tests/test_staged_pilot.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_db_validation_gate.py tests/test_raw_store.py -q` | exit 0               |
| A    | `uv run ruff check backend/app/ops/data_health.py tests/test_ops_data_health.py`                                                                                                                                   | exit 0               |
| B    | `uv run pytest -q`                                                                                                                                                                                                 | exit 0；**仅 §8.10** |

**交接：** §8 证据齐 → `validate-execute-handoff` → Audit（非 finish-work）。

---

## 11. Execute Skill 冻结

| Skill                      | 本任务   | 已执行 |
| -------------------------- | -------- | ------ |
| trellis-execute            | 必做     | [x]    |
| test-driven-development    | 必做     | [x]    |
| incremental-implementation | 必做     | [x]    |
| karpathy-guidelines        | 必做     | [x]    |
| testing-guidelines         | 必做     | [x]    |
| ponytail                   | 必做     | [x]    |
| gitnexus-impact            | 必做     | [x]    |
| trellis-check              | **不用** | —      |

---

## 12. Audit 交接

- [x] §8 全部步骤已执行
- [x] `validate-execute-handoff` 通过
- [x] 无 production-live 声称
- [x] sandbox gate 充分性已陈述
