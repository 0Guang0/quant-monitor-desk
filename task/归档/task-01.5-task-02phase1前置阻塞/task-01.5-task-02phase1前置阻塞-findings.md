# task-01.5 · Findings（查码 + 用户决议 + 开放 ledger）

> **SSOT 输入：** `task/audit/TEMP-ADR-cleanup-vs-runtime-behavior-review.md`（已归档）· 累积审计 `C:\Users\Guang\Desktop\Findings.txt`  
> **查证：** GitNexus impact + grep/Read · **最近刷新 2026-07-10（AUD-DOUBT-01～16 关账）**  
> **用户决议：** 一区 A + 二区 A/B **全部**须在 `task-02` Phase 1 切片开工前关账（含 **B11、B12**）。  
> **分工：** 本文件 = TEMP disposition · 查码结论 · **开放 ledger（§9）** · 计划阶段决议；**执行期计划外** → `note.md`（AC-CLOSE-2）。

---

## 1. 成品权威栈（执行时不偏离）

| 层级     | 路径                                                                            |
| -------- | ------------------------------------------------------------------------------- |
| 根 ADR   | v1 `ADR-0001～0005`（`docs/architecture/design/08_decision_log_index.md` 索引） |
| 保留 ADR | `docs/decisions/` 磁盘现存 003、004、007、009、010、011、015、016               |
| 设计图   | `MIGRATION_MAP.md` → `**/design/**`                                             |
| 本票输入 | TEMP 全文 A1–A10、B11–B19；一区 B1–B10 = **保留行为 + 补文档指针**              |

---

## 2. GitNexus 爆炸半径（改 symbol 前必读）

| 目标 symbol                                    | 风险         | 直接上游（摘要）                                                                          | 本票关联项                                       |
| ---------------------------------------------- | ------------ | ----------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `plan_backfill_shards`                         | **HIGH**     | `backfill_plan`、`full_load_plan`、`BackfillShardRunner.run`、`run_baostock_bar_backfill` | **B19**                                          |
| `resolve_prod_source_tier`                     | **HIGH**     | `create_product_live_fetch_port` → matrix live / `live_fetch`                             | **B14** ✅                                       |
| `guard_production_datasource_service_required` | **CRITICAL** | orchestrator 全 job 类型                                                                  | 一区 B2（**只文档，不改逻辑**）                  |
| `_execute_write`                               | **LOW**      | `WriteManager.write`；间接 layer2 staging、sandbox_clean_write                            | **B11** S7-2 ✅                                  |
| `_validate_domain_roles`                       | **CRITICAL** | `SourceRegistry.load` → matrix live / sync / backfill 等 19 processes                     | **B11** S7-1 ✅（内部提取，**无**公开 API 变更） |

---

## 3. 逐项 disposition（TEMP → 本票切片）

| ID     | 分区   | 用户解决方案（摘要）                                                                                                    | 本票切片             | disposition                                                                            |
| ------ | ------ | ----------------------------------------------------------------------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------- |
| A1–A7  | 一区 A | 改 `docs_anchor` / `adr_refs` / README / 注释                                                                           | S1                   | 已修复                                                                                 |
| A8–A10 | 二区 A | 同 S1，优先误导型指针                                                                                                   | S1                   | 已修复                                                                                 |
| B1–B10 | 一区 B | **保留代码**；S1 补文档指向 ADR-015/design                                                                              | S1 验证              | 按设计保留                                                                             |
| B11    | 二区   | **重构**（用户修订）：提取 helper 降 C901，行为由现有 pytest 锁定；修订 ADR-004 废止「不修」                            | S7（S7-1→S7-2→S7-3） | 已修复                                                                                 |
| B12    | 二区   | **删除** `sandbox-clean-write` / `limited_production_entry` 退役桩及相关测试契约中的「退役报错」语义                    | S6                   | 已修复                                                                                 |
| B13    | 二区   | 测试/fixture 迁 `source-route-db`；删 `M_DATA_03_SANDBOX_SEGMENT`                                                       | S3                   | 已修复                                                                                 |
| B14    | 二区   | `live_tier_router` → `live_prod_source_tiers`（GitNexus `rename`）；`tier_a_fetch_operation` 等改名                     | S4                   | 已修复（harness + **`incremental_gold_path_*` registry** · AUD-DOUBT-12 @ 2026-07-10） |
| B15    | 二区   | 修订 ADR-015：删 tier 脚本、M-DATA-03 主叙事                                                                            | S2                   | 已修复                                                                                 |
| B16    | 二区   | ADR-015 删 MCR/R4_SANDBOX 当 SSOT 的段落                                                                                | S2                   | 已修复                                                                                 |
| B17    | 二区   | **22 源 SSOT 收敛**：以 `data_sources.md` §5.9.1 为唯一枚举；ADR-009 只保留 11 源 **incremental 金路径**表并链到 §5.9.1 | S2                   | 已修复                                                                                 |
| B18    | 二区   | 并入 S1（A3）+ S4（报错文案去 Tier）                                                                                    | S1+S4                | 已修复                                                                                 |
| B19    | 二区   | **甲**：`plan_backfill_shards` 按 **交易日** 对齐 `performance_limits.md` §8；ADR-011；YAML 对齐                        | S5                   | 已修复（CLI fail-closed + 生产路径 `truncate_to_cap`；空分片行为见 **AUD-S5-06**）     |

### S7+ 可观测性与安全（计划外 · 2026-07-09）

| ID     | 摘要                                         | disposition                | 证据                                                                                                |
| ------ | -------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------- |
| OBS-P2 | CLI `run_id` / `requested_by` 贯通写入审计   | 已修复                     | `run_context.py` · `SyncJobSpec.requested_by` · `test_runIncremental_requestedBy_reachesWriteAudit` |
| OBS-P3 | `write_completed`/`write_failed` stderr JSON | 已修复                     | `write_telemetry.py` · `test_write_telemetry` · `test_write_success_emitsStructuredStderrEvent`     |
| SEC-S7 | 写入热路径静态安全体检                       | 按设计保留（0 可报告漏洞） | `security-scan-s7/VULN-FINDINGS.json`                                                               |
| REG-01 | `require_enabled` 主源 disabled 守卫         | 已修复                     | `bad_primary_disabled.yaml` · `test_load_primarySourceDisabled_raisesInvalidRegistryError`          |

---

## 4. 查码要点（有据可查）

> **§4.1** = S5 后现行快照 · **§4.2** = 已关账项历史快照（勿作现行）

### 4.1 B19 · backfill（S5 后现行 · 2026-07-09 刷新）

- **权威：** `docs/ops/design/performance_limits.md` §8 → backfill 日期窗口默认 **5**、硬顶 **20** **交易日**；`runtime_flow_contract.yaml` `flows.backfill.max_trading_days_default: 5`。
- **现行实现：**
  - `bounded_backfill_cap.yaml`：`max_trading_days_per_shard: 5` · `absolute_max_trading_days: 20` · **`default_max_backfill_shards: 1`**（整窗默认 **5 交易日**）。
  - `fetch_window.backfill_trading_days`：`cn_equity_daily_bar` / `market_bar_1d` → CN 历；`us_equity_daily_bar` → US 历；macro 等 → **日历日**（ADR-011 §1.1 + `ponytail:` 注释）。
  - `plan_backfill_shards(..., data_domain=...)`：按交易日切片；CLI 无 `--truncate-to-cap` 时超 20 交易日 **fail-closed**；orchestrator / scheduler / baostock 金路径调用时 **`truncate_to_cap=True`**，宽窗裁至 20 交易日再分片（AUD-DOUBT-01～03 · 13）。
- **仍开放（S5 后）：** 空分片 fetch 失败拖死整 job（**AUD-S5-06**，task-02 Phase 1 产品票）。

### 4.2 已关账查码快照（历史 · 勿作现行）

#### B13 · 双沙箱（S3 已关账）

- 曾：`conftest.py` `m_data_03_sandbox_root` 用 `M_DATA_03_SANDBOX_SEGMENT`。
- 现：已迁 `source-route-db`；`rg m_data_03` 代码零命中（2026-07-09 复核）。

#### B14 · Tier 命名（S4 已关账）

- 曾：`live_tier_router.py` · `TIER_A_SOURCES` · `tier_a_fetch_operation`。
- 现：`live_prod_source_tiers.py` · `INCREMENTAL_GOLD_PATH_SOURCE_IDS` 等；契约 `retired_seam_patterns` 已登记旧名。

#### B11 · 复杂度（S7 已关账）

- 曾：C901 超阈 `_execute_write` / `_validate_domain_roles`。
- 现：提取式重构 + ADR-004 修订；`ruff --select=C901` 相关路径已关账（见 `note.md` §S7+）。

### B12 · legacy CLI（S6 已关账）

- **删除：** `phase1_acceptance.RETIRED_LEGACY_COMMANDS` + `raise_retired_legacy_command`；`limited_production_entry.run_limited_production_entry` 退役桩。
- **契约：** `data_cli_contract.yaml` 移除 sandbox-clean-write 于 `non_gate_evidence` / `retired_commands`；测试改断言 CLI 无此子命令。
- **保留：** `limited_production_entry.py` 内部 proof/promote helper（rehearsal 路径）；`sandbox_clean_write/` 模块未删。

---

## 5. 接口设计约束（api-and-interface-design）

| 接缝                     | 约束                                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| `qmd-data data backfill` | 边界校验日期窗；错误 JSON 保持 `error_code` + `docs_anchor` 指向 **design**                            |
| CLI 退役                 | **删除子命令**优于永久 `LEGACY_COMMAND_RETIRED`（用户 B12）；避免 Hyrum 定律把报错文案当契约           |
| 源分档 rename            | 对外 JSON 字段名不变；仅内部模块/函数名                                                                |
| `bounded_backfill_cap`   | 机器可读 SSOT 须与 `performance_limits.md` 一致；改 design 后 `promote_design_runtime.py` 同步运行副本 |

---

## 6. 废弃与迁移（deprecation-and-migration）

| 退役物                        | 替代                                         | 本票动作            |
| ----------------------------- | -------------------------------------------- | ------------------- |
| `m-data-03` 沙箱段            | `source-route-db`                            | S3 迁移测试 fixture |
| `sandbox-clean-write` CLI     | `qmd-data data sync\|backfill\|...` + 隔离库 | S6 删代码+契约      |
| `tier_a_live_acceptance` 叙事 | `qmd-ops accept-source-route-db`             | S2 ADR-015 正文     |
| 31×shard 自然日 cap           | 5/20 交易日 cap                              | S5 代码+YAML        |

---

## 7. 开放问题（OQ 决议记录）

| ID       | 问题                                                                         | 决议                                                        | 状态                                       |
| -------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------ |
| OQ-015-1 | backfill 交易日历：按 `data_domain` 自动选 CN/US，还是 CLI 显式 `--market`？ | **按 domain 自动**                                          | **已闭合**（S5 · `backfill_trading_days`） |
| OQ-015-2 | `max_shards` CLI 旗标是否保留？                                              | **保留**；单片 5 交易日，shard 预算 `min(20, max_shards×5)` | **已闭合**（S5）                           |
| OQ-015-3 | B11 是否在本票做 C901 拆分？                                                 | **是** — S7 提取式重构                                      | **已闭合**（S7）                           |

---

## 9. 开放 ledger（Findings.txt 累积 + 对抗审计 · 2026-07-09）

> **记账规则：** 每条一行 disposition ∈ {**待修复**, **按设计保留**, **阶段外置**}。  
> **阶段列：** 标明应在何时关账（**S5 关账前** = CP-3 前；**S6** / **Phase F** = 本票内；**task-02 Phase 1** = 本票解锁后；**阶段外** = 须登记 `docs/quality/待修复清单.md` + `PROJECT_IMPLEMENTATION_ROADMAP.md`）。

### 9.1 本票 TEMP / S5 直接相关

| ID            | 来源                    | 问题（业务白话）                                                                                              | 阶段                | disposition      | 证据/备注                                                                                                                  |
| ------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **B12**       | TEMP B12                | legacy promote CLI 退役桩已删；argparse 拒绝旧命令                                                            | **S6**              | 已修复           | 删 `raise_retired_legacy_command` · `run_limited_production_entry` · `test_dataCliContract_sandboxCleanWriteNotRegistered` |
| **AUD-S5-01** | 对抗审计 · task_plan AC | **默认窗语义**：`default_max_backfill_shards: 1` → CLI 默认 **5 交易日**整窗                                  | **S5 关账前**       | 已修复           | `bounded_backfill_cap.yaml` · `test_planBackfillShards_defaultShardBudget_*`                                               |
| **AUD-S5-02** | 对抗审计                | `task_plan.md` S5 AC 已勾选；CP-3 关账链闭合                                                                  | **S5 关账前**       | 已修复           | `task_plan.md` §Slice S5                                                                                                   |
| **AUD-S5-03** | task_plan RED           | **30 自然日跨度、仅 20 交易日** PASS + 超 20 FAIL 行为测                                                      | **S5 关账前**       | 已修复           | `test_planBackfillShards_thirtyCalendarDays_*` · CLI 子进程测                                                              |
| **AUD-S5-04** | 对抗审计 · Findings A   | CLI/分片**运行时**行为测补足（非仅 YAML 数字对齐）                                                            | **S5 关账前**       | 已修复           | `test_qmd_data_backfill_defaultBudget_*` · `test_qmd_data_backfill_thirtyCalendarDays_*`                                   |
| **AUD-S5-05** | S5 ponytail             | macro 域日历日计数边界文档化                                                                                  | **S5 关账前**       | 已修复           | ADR-011 §1.1 · `fetch_window.py` docstring · `test_backfillTradingDays_macroDomain_*`                                      |
| **AUD-S5-06** | S5 对抗审计 · 执行暴露  | **空分片拖死整 job**：某片无 bar 时 fetch 无 staging → `FAILED_RETRYABLE` 并停止后续片；S5 切片更细后更易触发 | **task-02 Phase 1** | 已迁移至 task-02 | `task-02-layer1-full-findings.md` **F-18**                                                                                 |

### 9.1b AUD-DOUBT 对抗审计关账（2026-07-10）

| ID               | Findings 类 | 问题（摘要）                   | disposition          | 证据                                                                                         |
| ---------------- | ----------- | ------------------------------ | -------------------- | -------------------------------------------------------------------------------------------- |
| **AUD-DOUBT-01** | 2/3         | runners 无界分片               | **已修复**           | `runners.py` `truncate_to_cap=True` · `test_backfillJob_largeRange_splitsIntoTasks`          |
| **AUD-DOUBT-02** | 2           | baostock 无界分片              | **已修复**           | `baostock_incremental_run.py` · 同上                                                         |
| **AUD-DOUBT-03** | 1           | orchestrator 测假绿            | **已修复**           | `test_backfillJob_largeRange_splitsIntoTasks` 断言 4 片/20 日                                |
| **AUD-DOUBT-04** | 5/7         | m-data-03 契约残留             | **已修复**           | 契约清禁词 · `phase-scripts/check_task015_s3_s4_rg_compliance.py` · inventory base64         |
| **AUD-DOUBT-05** | 5           | task_plan ✅ vs AC [ ]         | **已修复**           | S3/S4 AC 已 `[x]` 与 CP-2 对齐                                                               |
| **AUD-DOUBT-06** | 5           | findings §9/§10 矛盾           | **已修复**           | §10 改写；本表为 SSOT                                                                        |
| **AUD-DOUBT-07** | 5           | YAML 缺 docs_anchor            | **已修复**           | `bounded_backfill_cap.yaml` `docs_anchor` → ADR-011                                          |
| **AUD-DOUBT-08** | 1           | closure 覆盖面窄               | **已修复**           | `closure_command` 含 orchestrator + CLI 子集测                                               |
| **AUD-DOUBT-09** | 1           | conftest ResourceGuard autouse | **已迁移至 task-02** | `FIND-A-01` → task-02 **F-19**                                                               |
| **AUD-DOUBT-10** | 1/4         | replay e2e ≠ live              | **按设计保留**       | CI 彩排合理；S5 关账文案不宣称 live-ready                                                    |
| **AUD-DOUBT-11** | 3/7         | OpenWiki 旧模块名              | **已修复**           | `openwiki/agent-guide.md` · `data-sync-and-live-gates.md`                                    |
| **AUD-DOUBT-12** | 3           | registry `tier_a_*` 残留       | **已修复**           | `incremental_gold_path_*` rename · `incremental_source_registry.py` · pytest 绿 @ 2026-07-10 |
| **AUD-DOUBT-13** | 2/3         | scheduler 旁路 cap             | **已修复**           | `scheduler.py` `plan_backfill_shards` 预检 + `truncate_to_cap`                               |
| **AUD-DOUBT-14** | 5           | macro 日历日 vs 交易日         | **已修复**           | `performance_limits.md` §8 脚注 · ADR-011 §1.1                                               |
| **AUD-DOUBT-15** | 2           | 空分片拖死 job / B19 过宽      | **已迁移至 task-02** | 同 **AUD-S5-06** → **F-18**；B19 cap 路径已修复                                              |
| **AUD-DOUBT-16** | 5           | S1–S5 complete ≠ Phase F       | **已修复**           | 对外文案区分切片交付 vs 整票；**Phase F 关账 2026-07-10**                                    |

### 9.1c 测试卫生（testing-guidelines · 2026-07-10）

| ID              | Findings 类      | 问题（业务白话）                                                               | disposition          | 证据                                                            |
| --------------- | ---------------- | ------------------------------------------------------------------------------ | -------------------- | --------------------------------------------------------------- |
| **AUD-TEST-01** | 1 artifact-guard | `test_s3_s4_task_compliance` 两条 rg 测在 pytest 内自豁免/编码绕过，非业务断言 | **已修复**           | 删 pytest；`phase-scripts/check_task015_s3_s4_rg_compliance.py` |
| **AUD-TEST-02** | 1 假绿           | `test_backfillJob_largeRange` 用 `≥4` 片，8 片仍绿                             | **已修复**           | 断言 `==4` + 末片 COMPLETED / 前片 PLANNED                      |
| **AUD-TEST-03** | 边界             | 负例路径 `not-source-route-db` 含子串 `source-route-db` 误判合法               | **已修复**           | `test_resolveMatrixDataRoot_*` 用 `wrong-sandbox-segment`       |
| **AUD-TEST-04** | 缺口             | scheduler/baostock 宽窗片数无集成行为测                                        | **已迁移至 task-02** | task-02 **F-20**                                                |

### 9.2 Findings.txt 七类 · 跨票累积（2026-07-10 迁入 task-02 §7）

| ID            | Findings 类     | 问题（业务白话）                                                                       | 阶段                | disposition          | 证据/备注                                                              |
| ------------- | --------------- | -------------------------------------------------------------------------------------- | ------------------- | -------------------- | ---------------------------------------------------------------------- |
| **FIND-A-01** | 第1类 假绿      | `conftest` **autouse** 全局 ResourceGuard=OK；主机压力时集成路径 guard 失效不可见      | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-19**                                                       |
| **FIND-A-02** | 第1类 假绿      | backfill/full-load「live 验收」大量 **replay + patch fetch_port**；≠ 真网 primary 关账 | **task-02 Phase 1** | 按设计保留           | ADR-016；CI 彩排合理，不得冒充 live 关账                               |
| **FIND-A-03** | 第1类 假绿      | vacuous / call-count / 宽枚举 membership 测试仍散见各模块                              | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-21**                                                       |
| **FIND-B-01** | 第2类 入口脱节  | 正式 CLI 部分路径仍可能 **`fetch_port is required`** 崩溃；测试靠 patch                | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-01**（复核重开）                                           |
| **FIND-B-02** | 第2类 入口脱节  | sync 能跑但 **fetch_log_ids / rows_written** 等 R4 证据链可为空                        | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-03**（复核重开）                                           |
| **FIND-C-01** | 第4类 mock/live | FRED 等 **sandbox DONE ≠ live primary 关账**                                           | **按设计**          | 按设计保留           | B2.5-O-05 · ADR-016                                                    |
| **FIND-2-01** | 第2类 半成品    | `revision_audit` 仍为 minimal stub（数行非真修订审计）                                 | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-08**                                                       |
| **FIND-2-02** | 第2类 半成品    | `data_quality` job 同族 stub                                                           | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-09**                                                       |
| **FIND-2-03** | 第2类 半成品    | scheduler quality child 曾手工拼 PASS（需复核现行）                                    | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-06**                                                       |
| **FIND-3-01** | 第3类 接缝      | fred **matrix overlay** vs **binding 默认 registry** 双轨（F-07/F-14）                 | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-07** · **F-14**                                            |
| **FIND-E-01** | 第6类 卫生      | `sync_scheduler_profiles.yaml` **无 schema 校验**                                      | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-22**                                                       |
| **FIND-E-02** | 第6类 卫生      | Orchestrator 单体 · adapter 绑具体 storage（R2-RISK）                                  | **task-02 Phase 1** | **已迁移至 task-02** | task-02 **F-23**                                                       |
| **FIND-5-01** | 第5类 SSOT      | 多份 findings / audit / progress 措辞漂移                                              | **Phase F**         | 已修复               | Phase F 统一 §3/§9/§10 · `progress.md` 解锁行 · 删 GitNexus 已删符号行 |

### 9.3 本票关账门（Phase F）

| ID           | 问题                                                           | 阶段        | disposition |
| ------------ | -------------------------------------------------------------- | ----------- | ----------- | --------------------------------------------------------------- |
| **AUD-F-01** | §3 TEMP A1–A10、B11–B19 全 **已修复**（B1–B10 **按设计保留**） | **Phase F** | 已修复      | 2026-07-10 全表复核 §3 · 无「待修复」                           |
| **AUD-F-02** | `uv run pytest -q` 全绿 + 双 progress 解锁行                   | **Phase F** | 已修复      | pytest exit 0 · `task-01.5/progress.md` + `task-02/progress.md` |

---

## 10. S5 关账 vs 整票完工（速查）

| 时机                    | ID 列表                                                                                     | 业务含义（一句话）                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **S5 切片交付（CP-3）** | AUD-S5-01～05 · AUD-DOUBT-01～08/11/13/14/16                                                | CLI + orchestrator/scheduler/baostock **5/20 硬顶**、契约/rg/AC 对齐；**不等于** live-ready |
| **S6**（本票下一切片）  | **B12**                                                                                     | ✅ 删掉 legacy promote CLI 桩，改契约                                                       |
| **Phase F**（本票收尾） | AUD-F-01 · AUD-F-02 · FIND-5-01                                                             | ✅ 全表 disposition 关账、双 progress 解锁、文档索引一致                                    |
| **task-02 Phase 1**     | AUD-S5-06 · AUD-DOUBT-09/15 · FIND-A-01/03 · FIND-B-01/02 · FIND-2-_ · FIND-3-01 · FIND-E-_ | **已迁入** `task-02-layer1-full-findings.md` **§7**（仍开放 · 禁止再阶段外置）              |
| **本票已关**            | **AUD-DOUBT-12**                                                                            | `incremental_gold_path_*` rename @ 2026-07-10                                               |

**说明：** **S5 切片**已关账。**S6 已关账**（B12）。**Phase F 已关账**（2026-07-10）→ **task-01.5 已绿**，可解锁 task-02 Slice 0-N。§9.2 跨票项已迁入 task-02，**不挡**本票关账。

---

## 8. Errors Encountered

| Error    | Attempt | Resolution |
| -------- | ------- | ---------- |
| （尚无） | —       | —          |
