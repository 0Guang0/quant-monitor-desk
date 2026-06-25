# MASTER 计划 — B3F-MIG migration residuals

> **Execute 入口** — 无 production clean write；registry 闭合归 B3F-REG。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`

---

## 0. 元信息

| 字段                      | 值                                                             |
| ------------------------- | -------------------------------------------------------------- |
| 任务 slug                 | `round3f-migration-residual-checks`                            |
| Playbook ID               | B3F-MIG                                                        |
| 分支                      | `feature/round3f-migration-residual-checks`                    |
| Worktree                  | `../quant-monitor-desk-wt-b3f-mig`                             |
| 合并顺序                  | **§7.2 序 1**（B3F-SH 依赖本分支 migration）                   |
| manifest_protocol_version | `3`                                                            |
| analysis_waiver           | `false`                                                        |
| 原计划                    | `research/original-plan-trace.md` · `research/source-index.md` |

### Batch 3F 边界（Playbook §2.5 / §2.6）

| Owns                                              | Must not                                      |
| ------------------------------------------------- | --------------------------------------------- |
| `012_migration_residuals.sql`；008/009 路由文档   | 重复实现 009 已关 CHECK（MIG-01 verify-only） |
| `registry_generation` / `removed_from_yaml_at` 列 | `source_health_snapshot` 表语义               |
| ADR-002 priority app-layer 记录                   | sync 业务重构；registry 三件套直接闭合        |
| `test_round3f_migration_residuals.py`             | production clean write                        |

### 0.1 门控速查

| 项        | 值                                                                |
| --------- | ----------------------------------------------------------------- |
| 怎么测    | §9 RED→GREEN；playbook §8.1 pytest 子集 + 全量 `uv run pytest -q` |
| 怎么验收  | §6 Tier A/C                                                       |
| 什么叫过  | AC-MIG-01..06                                                     |
| prod-path | Tier A only（内存 DuckDB migrate）                                |
| 6.pre     | `research/gitnexus-execute-summary.md`（Execute 例外可读）        |

### 0.3 Execute 强制必读

Phase 0 **逐条 Read `implement.jsonl`**；先读 `research/integration-ledger.md`。

### 0.3a Ponytail

MUST Read `.cursor/rules/ponytail.mdc`；复用 `apply_migrations`；无新依赖；012 单文件最小 diff。

### Source Context Index（Playbook §3.1 + §3.3）

#### §3.1 共用底座

| 路径                                            | 摘要                 | implement |
| ----------------------------------------------- | -------------------- | --------- |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md`              | §2.5 锁、§7.2 合并序 | [x]       |
| `BATCH_3F_TASK_CARD_MANIFEST.md`                | B3F-MIG 路由         | [x]       |
| `BATCH_3F_HARDENING_RULES.md`                   | 禁 production 措辞   | [x]       |
| `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` | B3F-AUD-VS-02        | [x]       |
| `ROUND_3_BATCH6_DATA_GOVERNANCE/README.md`      | Round 3F 入口        | [x]       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`             | R3F-MIG-01..06       | [x]       |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3               | 全局纪律             | [x]       |

#### §3.3 B3F-MIG

| 路径                                    | 摘要           | implement |
| --------------------------------------- | -------------- | --------- |
| `MIGRATION_008_PLAN.md`                 | 008 残余路由   | [x]       |
| `MIGRATION_COVERAGE.md`                 | 009/3F 桶      | [x]       |
| `009_status_check_constraints.sql`      | 009 只读对照   | [x]       |
| `012_migration_residuals.sql`           | 012 交付       | [x]       |
| `ADR-002-db-check-vs-app-validation.md` | CHECK 策略     | [x]       |
| `source_registry.py`                    | sync tombstone | [x]       |
| `test_round3f_migration_residuals.py`   | 六用例         | [x]       |
| `test_schema_contract.py`               | 基线           | [x]       |
| `test_migration_coverage.py`            | 基线           | [x]       |

---

## 1. 目标与目的

### 1.1 目标

闭合 `R3F-MIG-01..06`：migration 残余（verify、ADR、显式重建、lifecycle 列、路由文档、regression guard），作为 Batch 3F **第一合并位**。

### 1.2 目的

解除 B3F-SH 对共享 migration 的合并阻塞；对齐 008→009→3F 审计矩阵。

### 1.3 前置

- 基线 `7f628c9`；post Batch 3V master。
- Playbook §7.2：本分支序 1，无前置合并。

### 1.4 约束

- 无 production clean write；无 live pilot。
- **R3F-MIG-01 verify-only**：不得新建重复 009 CHECK migration。

### 1.5 停止条件

| #   | 事件                                         | 处理                       |
| --- | -------------------------------------------- | -------------------------- |
| 1   | 修改 forbidden（SH 表语义 / registry 闭合）  | 禁止；退回 Plan            |
| 2   | 生产库 migration 或 clean write              | HARD_STOP                  |
| 3   | scope 偏离 R3F-MIG-\*                        | 退回 Plan                  |
| 4   | RED 异常 / 削弱测试目的                      | 停当前 §9 步               |
| 5   | GitNexus impact HIGH/CRITICAL 未确认         | 停；主会话裁定             |
| 6   | 新建 013 重复 009 status CHECK               | HARD_STOP（B3F-AUD-VS-02） |
| 7   | B3F-SH 在 MIG 合并前要求同 PR 建 snapshot 表 | 拒绝；保持 §7.2 序         |

### 1.6 原计划归并

| 来源                   | 内容                    |
| ---------------------- | ----------------------- |
| Playbook §3.3 + §8.1   | 六切片 + PASS 命令      |
| Roadmap R3F-MIG-01..06 | AC 映射                 |
| B3F-AUD-VS-02          | MIG-01 verify-only 负向 |

---

## 2. 架构与设计

**2.1 架构** `migrate.py` 顺序应用 001–012 → DuckDB DDL + `SourceRegistry.sync_to_db`

**2.2 设计**

1. **MIG-01**：磁盘 verify 009；负向无 013。
2. **MIG-02**：ADR-002 记录 priority；012 MRQ 无 priority CHECK。
3. **MIG-03/04**：012 显式列重建 + lifecycle 列。
4. **MIG-05**：COVERAGE/008 PLAN 路由段。
5. **MIG-06**：roadmap 行 regression。

**2.3 规则** GLOBAL + BATCH_3F_HARDENING + Playbook §2.6

**2.4 契约** `MIGRATION_COVERAGE.md` · `MIGRATION_008_PLAN.md` · ADR-002

**2.5 决策** priority app-layer（ADR-002）；009 CHECK 不重复

---

## 3. 需求与场景矩阵

| 场景# | Given             | When              | Then                          | AC        | 测试   | Tier |
| ----- | ----------------- | ----------------- | ----------------------------- | --------- | ------ | ---- |
| S1    | 009 在磁盘        | 读 migration 目录 | CHECK 在 009；无 013          | AC-MIG-01 | MIG-01 | A    |
| S2    | 012 已 apply      | 查 MRQ DDL + ADR  | 无 priority CHECK             | AC-MIG-02 | MIG-02 | A    |
| S3    | 012 SQL           | 静态读 012        | 显式列 INSERT；无 SELECT \*   | AC-MIG-03 | MIG-03 | A    |
| S4    | registry YAML     | sync + tombstone  | generation≥1；removed_at 非空 | AC-MIG-04 | MIG-04 | B    |
| S5    | COVERAGE/008 PLAN | 读文档            | Round 3F 路由桶存在           | AC-MIG-05 | MIG-05 | A    |
| S6    | ROADMAP           | 读 R3F-MIG-06 行  | CLOSED B3V                    | AC-MIG-06 | MIG-06 | A    |

**3.1 需求说明**：闭合 migration 残余；009 不重复实现。

**3.2 范围** in: 012、文档、ADR、测试 · out/defer: `source_health_snapshot`（B3F-SH）；registry 三件套（B3F-REG）

---

## 4. 预期结果

| #         | 预期结果                | 验证链    |
| --------- | ----------------------- | --------- |
| AC-MIG-01 | 009 verify-only PASS    | S1 → §9.1 |
| AC-MIG-02 | priority app-layer 闭合 | S2 → §9.2 |
| AC-MIG-03 | 显式列重建              | S3 → §9.3 |
| AC-MIG-04 | lifecycle 列 + sync     | S4 → §9.4 |
| AC-MIG-05 | 路由文档                | S5 → §9.5 |
| AC-MIG-06 | regression guard        | S6 → §9.6 |

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring（purpose/target/verifies/failure_meaning）
2. MIG-01 verify-only：不得为过关删除 009 或添加重复 migration
3. RED 后 GREEN 前 Read karpathy + testing-guidelines

### 5.1 测试文件路径

| 测试文件路径                                | 目标文件                                             | 测试目的（冻结）          | §9      |
| ------------------------------------------- | ---------------------------------------------------- | ------------------------- | ------- |
| `tests/test_round3f_migration_residuals.py` | `012_migration_residuals.sql` + `source_registry.py` | R3F-MIG-01..06 六用例语义 | 9.1–9.6 |
| `tests/test_schema_contract.py`             | migration 契约                                       | playbook §8.1 基线回归    | Boot    |
| `tests/test_migration_coverage.py`          | `MIGRATION_COVERAGE.md`                              | coverage 基线回归         | Boot    |

### 5.2 成功怎么测 / 失败怎么测

| 能力             | 成功怎么测                | 失败怎么测               | 场景 |
| ---------------- | ------------------------- | ------------------------ | ---- |
| 009 verify       | 009 含 CHECK；无 013 文件 | 出现 013 或 009 缺 CHECK | S1   |
| priority ADR     | ADR + DDL 无 CHECK        | DB CHECK 或 ADR 缺段     | S2   |
| explicit rebuild | 012 显式 INSERT           | SELECT \* 在重建段       | S3   |
| lifecycle sync   | 列存在 + tombstone        | 列缺失或 sync 不写       | S4   |
| routing docs     | COVERAGE/PLAN 含 3F       | 缺 Round 3F 段           | S5   |
| partial-5 guard  | CLOSED B3V 行             | 行被重开为实现           | S6   |

### 5.3 用例设计

| 测试文件                              | test\_\* 名称                                                      | 断言语义                    | 场景 | RED 命令                                                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------ | --------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------ |
| `test_round3f_migration_residuals.py` | `test_r3fMig01_migration009_statusChecks_present_verifyOnly`       | 009 CHECK；无 013           | S1   | `uv run pytest tests/test_round3f_migration_residuals.py::test_r3fMig01_migration009_statusChecks_present_verifyOnly -v` |
| 同上                                  | `test_r3fMig02_manualReviewPriority_appLayerOnly_documented`       | 无 priority CHECK；ADR 记录 | S2   | `uv run pytest …::test_r3fMig02_manualReviewPriority_appLayerOnly_documented -v`                                         |
| 同上                                  | `test_r3fMig03_fetchLogAndManualReview_rebuildUsesExplicitColumns` | 显式列；无 SELECT \*        | S3   | `uv run pytest …::test_r3fMig03_fetchLogAndManualReview_rebuildUsesExplicitColumns -v`                                   |
| 同上                                  | `test_r3fMig04_sourceRegistry_lifecycleColumns_existAfterMigrate`  | 列 + sync/tombstone         | S4   | `uv run pytest …::test_r3fMig04_sourceRegistry_lifecycleColumns_existAfterMigrate -v`                                    |
| 同上                                  | `test_r3fMig05_migrationCoverage_routes008To009To3f`               | 路由文档段                  | S5   | `uv run pytest …::test_r3fMig05_migrationCoverage_routes008To009To3f -v`                                                 |
| 同上                                  | `test_r3fMig06_partial5_regressionGuard_noReopenAsActive`          | CLOSED B3V                  | S6   | `uv run pytest …::test_r3fMig06_partial5_regressionGuard_noReopenAsActive -v`                                            |

### 5.4 四层测试

| 层   | 环境 | 命令               | 通过   |
| ---- | ---- | ------------------ | ------ |
| 单元 | ci   | playbook §8.1 子集 | exit 0 |
| 集成 | ci   | `uv run pytest -q` | exit 0 |
| 管道 | —    | N/A                | —      |
| E2E  | —    | N/A                | —      |

---

## 6. 验证

| Tier | 环境     | 命令                                                                                                                        | 场景   | 通过   |
| ---- | -------- | --------------------------------------------------------------------------------------------------------------------------- | ------ | ------ |
| A    | local/ci | `uv run pytest tests/test_schema_contract.py tests/test_migration_coverage.py tests/test_round3f_migration_residuals.py -q` | S1–S6  | exit 0 |
| B    | local/ci | `uv run ruff check backend/app/db docs/schema tests`                                                                        | —      | exit 0 |
| C    | local/ci | `uv run pytest -q`                                                                                                          | 全回归 | exit 0 |

**6.1 交接门槛**：§9 证据齐 · §5.1 用例存在 · §1.5 未触发 · registry **不**在本任务勾选

---

## 7. Red Flags

| 风险                        | 预防                        |
| --------------------------- | --------------------------- |
| 重复 009 CHECK              | MIG-01 verify-only；§1.5 #6 |
| 抢建 source_health_snapshot | §3.2 defer B3F-SH           |
| SELECT \* 静默丢列          | MIG-03 静态断言             |
| SH 抢先合并                 | §7.2 序 4 前提              |
| 重开 crash-window 实现      | MIG-06 regression only      |

---

## 8. 实现顺序

| 序  | ID     | 交付物（完标准）           | 依赖   | AC        |
| --- | ------ | -------------------------- | ------ | --------- |
| 1   | MIG-01 | 009 verify 测试绿          | —      | AC-MIG-01 |
| 2   | MIG-02 | ADR + priority 烟测绿      | MIG-01 | AC-MIG-02 |
| 3   | MIG-03 | 012 显式重建测试绿         | MIG-01 | AC-MIG-03 |
| 4   | MIG-04 | lifecycle 列 + sync 测试绿 | MIG-03 | AC-MIG-04 |
| 5   | MIG-05 | 路由文档测试绿             | MIG-03 | AC-MIG-05 |
| 6   | MIG-06 | roadmap regression 测试绿  | —      | AC-MIG-06 |

---

## 9. 实现步骤

### 9.0 Boot

**必读**：§0.3 Execute 强制必读 → 逐条 `implement.jsonl`；先读 `research/integration-ledger.md`。

| RED / GREEN                                                                       | 证据                            | 绑定 Execute Skill                | [x] |
| --------------------------------------------------------------------------------- | ------------------------------- | --------------------------------- | --- |
| `uv run pytest tests/test_schema_contract.py tests/test_migration_coverage.py -q` | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [x] |

### 9.1 MIG-01 — 009 verify-only

| 字段        | 内容                                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| RED / GREEN | `uv run pytest tests/test_round3f_migration_residuals.py::test_r3fMig01_migration009_statusChecks_present_verifyOnly -v` |
| 证据        | `9.1-red.txt` / `9.1-green.txt`                                                                                          |
| Skill       | test-driven-development · karpathy-guidelines · testing-guidelines                                                       |
| 通过        | RED FAIL（缺测试或误加 013）；GREEN 0；**不得**新建重复 CHECK migration                                                  |
| [x]         | [x]                                                                                                                      |

### 9.2 MIG-02 — priority app-layer

| 字段        | 内容                                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| RED / GREEN | `uv run pytest tests/test_round3f_migration_residuals.py::test_r3fMig02_manualReviewPriority_appLayerOnly_documented -v` |
| 证据        | `9.2-red.txt` / `9.2-green.txt`                                                                                          |
| Skill       | test-driven-development · incremental-implementation                                                                     |
| [x]         | [x]                                                                                                                      |

### 9.3 MIG-03 — explicit rebuild

| 字段        | 内容                                                                                                                           |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------ |
| RED / GREEN | `uv run pytest tests/test_round3f_migration_residuals.py::test_r3fMig03_fetchLogAndManualReview_rebuildUsesExplicitColumns -v` |
| 证据        | `9.3-red.txt` / `9.3-green.txt`                                                                                                |
| impact      | `012_migration_residuals.sql`（LOW）                                                                                           |
| [x]         | [x]                                                                                                                            |

### 9.4 MIG-04 — lifecycle columns

| 字段        | 内容                                                                                                                          |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------- |
| RED / GREEN | `uv run pytest tests/test_round3f_migration_residuals.py::test_r3fMig04_sourceRegistry_lifecycleColumns_existAfterMigrate -v` |
| 证据        | `9.4-red.txt` / `9.4-green.txt`                                                                                               |
| impact      | `SourceRegistry.sync_to_db`（MEDIUM）                                                                                         |
| [x]         | [x]                                                                                                                           |

### 9.5 MIG-05 — routing docs

| 字段        | 内容                                                                                                             |
| ----------- | ---------------------------------------------------------------------------------------------------------------- |
| RED / GREEN | `uv run pytest tests/test_round3f_migration_residuals.py::test_r3fMig05_migrationCoverage_routes008To009To3f -v` |
| 证据        | `9.5-red.txt` / `9.5-green.txt`                                                                                  |
| [x]         | [x]                                                                                                              |

### 9.6 MIG-06 — regression guard

| 字段        | 内容                                                                                                                  |
| ----------- | --------------------------------------------------------------------------------------------------------------------- |
| RED / GREEN | `uv run pytest tests/test_round3f_migration_residuals.py::test_r3fMig06_partial5_regressionGuard_noReopenAsActive -v` |
| 证据        | `9.6-red.txt` / `9.6-green.txt`                                                                                       |
| [x]         | [x]                                                                                                                   |

---

## 10. Execute 交接 DoD

- [x] §9 证据齐 · playbook §8.1 子集全绿 · §11 Skill `[x]` · `validate-execute-handoff` 0 · 未 finish-work

---

## 11. Execute Skill 冻结

| Skill                      | 本任务   | 绑定       | 已读 | 已执行 |
| -------------------------- | -------- | ---------- | ---- | ------ |
| trellis-execute            | 必做     | Boot       | [x]  | [x]    |
| test-driven-development    | 必做     | §9 RED     | [x]  | [x]    |
| incremental-implementation | 必做     | §9 SLICE   | [x]  | [x]    |
| karpathy-guidelines        | 必做     | GREEN      | [x]  | [x]    |
| testing-guidelines         | 必做     | 写测       | [x]  | [x]    |
| gitnexus-impact            | 必做     | 改 symbol  | [x]  | [x]    |
| systematic-debugging       | 条件     | DEBUG      | [ ]  | [ ]    |
| trellis-implement          | inline   | Execute    | [x]  | [x]    |
| trellis-check              | **不用** | → Audit A1 | —    | —      |

路径见 `execute-skill-paths.yaml`。
