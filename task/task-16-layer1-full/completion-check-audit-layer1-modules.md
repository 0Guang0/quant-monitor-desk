# completion-check

- 角色：`audit`
- 日期：`2026-07-10`
- 对应 plan：`task-02-layer1-full-task_plan.md` · `PHASE1_COMPLETION_INVENTORY.md`
- 对象范围：**data_sources** · **sync（orchestrator/runners）** · **validation** · **write_manager** · **backfill** · **full-load** · **scheduler** — 对照 MIGRATION_MAP 索引设计图与 Phase 1 P1-GATE 声称
- 声称：上述模块已按权威设计「完整落地 / R4 成品」
- 权威：`MIGRATION_MAP.md` → `data_sources.md` · `source_route_plan.md` · `source_capability_registry.md` · `data_sync_orchestrator.md` · `data_validation_and_conflict.md` · `write_manager.md` · `03_runtime_flows.md` · `runtime_flow_contract.yaml` · `data_cli_contract.yaml` `phase1_gate`
- 正式入口：`qmd-data data backfill|full-load|scheduler run` · `DataSourceService.fetch` · `DataSyncOrchestrator` job runners
- 声称档位：**production-equivalent live**（`source-route-db` + `QMD_ALLOW_LIVE_FETCH` + `--no-dry-run`）

> 对抗性审计：独立读权威 + 追正式入口调用链 + 主动找反证。不抄执行者「约 70%」摘要。

---

## 对象 1 · data_sources（注册 / 路由 / DataSourceService）

| CC   | 本对象运行事实                                                                                          | 证据 / 反证                                                                                | Verdict  | 闭环控制                                           |
| ---- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | -------- | -------------------------------------------------- |
| CC-0 | 用户要的是多源 Primary/Validation/Fallback 可审计选路 + 按域启用；交付侧重 planner 存在与 registry YAML | `SourceRoutePlanner.plan` 存在；大量源 disabled **按设计**；fallback 热路径未接            | **FAIL** | 声称否认：路由机制≠全源生产就绪                    |
| CC-1 | 矩阵 fred overlay 可绿；scheduler binding 同参 DISABLED                                                 | F-07/F-14；`phase1_acceptance._build_datasource_service` vs `enabled_fred_source_registry` | **FAIL** | 须 binding≡matrix 最高接缝测，无 patch             |
| CC-2 | Registry/capability/plan 有；**use_fallback 从未在 fetch 调用**；FileRegistry 占位                      | `service.py` L155 `use_fallback` 未传；`product_live_ports` L76–78 placeholder             | **FAIL** | 接 fallback 决策链 + 持久化 primary_failure_reason |
| CC-3 | CLI sync 矩阵 vs scheduler binding vs `build_product_live_service` 三套启用/工厂                        | F-07/F-14/F-01                                                                             | **FAIL** | One-Version enable + 单一 service 工厂             |
| CC-4 | disabled-by-default 诚实；macro 域仍 sandbox 语义                                                       | F-15 registry `domain_enabled_by_default: false`                                           | **FAIL** | Slice 1-P 落地后复验                               |
| CC-5 | route_grade 事后推断；route_status 粗粒度 READY；validation 源未强制 degraded 写                        | `route_models.infer_route_grade` vs design READY_PRIMARY/DEGRADED                          | **FAIL** | 对表 design `source_route_plan.md` §4              |
| CC-6 | 双轨 enable、fallback 未接属可本轮修共享根因                                                            | F-16 台账缺；禁止 mass-enable                                                              | **FAIL** | Slice 1-E/1/1-P；非登记了事                        |
| CC-7 | 缺 key/未授权 → DISABLED/BLOCKED 诚实                                                                   | F-17 按设计；ADR-015/016                                                                   | **PASS** | 保持诚实；不得 mass-enable 冒充完成                |

**对象 1 小结：** 路由**机制已落地**，非空壳；**Fallback、入口一致、macro 域策略**未达权威。**OPEN** · Finding：F-07 · F-14 · F-15 · F-16 · F-17(按设计) · F-01 · F-13

---

## 对象 2 · sync（DataSyncOrchestrator + runners 主线）

| CC   | 本对象运行事实                                                                                                | 证据 / 反证                                                                   | Verdict  | 闭环控制                                  |
| ---- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------- | ----------------------------------------- |
| CC-0 | 用户要六类 Job 成品 + 状态机 + 失败恢复；交付有 orchestrator 与 incremental/backfill/full_load/reconcile 主线 | `orchestrator.py` + runners 1200+ 行；**revision/data_quality 空壳**          | **FAIL** | QualityJobRunner 须走 validator/修订 diff |
| CC-1 | 金路径测多靠 staging adapter / ResourceGuard patch                                                            | `test_sync_orchestrator.py`；`test_b3f_quality_runners` 只断言 COMPLETED 字样 | **FAIL** | outcome 测替换 F-21                       |
| CC-2 | incremental/backfill/full_load **有**完整 pipeline；revision_audit/data_quality **只 COUNT 行**               | `runners.py` L1253–1282 `_ = self._validation` 未调用                         | **FAIL** | 2a-R\* / 2a-Q                             |
| CC-3 | binding 路径与 orchestrator quality 路径能力分裂                                                              | scheduler `_run_orchestrator_job` instrument_id=None                          | **FAIL** | 2a-0 禁 synthetic child PASS              |
| CC-4 | replay/staging 测绿 ≠ 全源 live                                                                               | FIND-A-02 按设计（CI 彩排）                                                   | **NA**   | CI replay 不得升格 live 关账              |
| CC-5 | backfill 分片/cap 对齐 §13.4.3；reconcile **仅 primary 重抓**                                                 | design §9.2 双源；`ReconcileJobRunner` L1117                                  | **FAIL** | ponytail 或 ADR 边界 + 测                 |
| CC-6 | 空分片停 whole job、quality stub 可本轮修                                                                     | F-18 · F-23                                                                   | **FAIL** | runners 续跑策略；非仅登记                |
| CC-7 | 无 key 可 BLOCKED；guard 机制有                                                                               | ResourceGuard 在 service/scheduler                                            | **PASS** | F-19 conftest autouse 须分层              |

**对象 2 小结：** 主线 sync **非空壳**；P1 必做 **revision/data_quality** 为 **shell-done**。**OPEN** · F-08 · F-09 · F-18 · F-21 · F-23 · F-13

---

## 对象 3 · validation（DataQualityValidator + SourceConflictValidator）

| CC   | 本对象运行事实                                                                             | 证据 / 反证                                           | Verdict  | 闭环控制                             |
| ---- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------- | -------- | ------------------------------------ |
| CC-0 | 用户要 staging→quality→conflict→gate→写；交付 validator 类存在且单测绿                     | sync 金路径**正式**走 validator；quality **job 不走** | **FAIL** | 2a-Q 须接 `DataQualityValidator`     |
| CC-1 | `test_data_quality_validator.py` / `test_source_conflict_validator.py` 较强；`test_b3f` 弱 | F-21                                                  | **FAIL** | scheduler quality outcome 测         |
| CC-2 | PK/价格/阈值/severe/manual_review **已实现**；缺 INVALID_TRADE_DATE 等部分规则             | grep 无 `INVALID_TRADE_DATE`；runner 只比 close       | **FAIL** | 权威规则缺口清单 + 测或 ponytail ADR |
| CC-3 | incremental/backfill 走 pipeline；scheduler data_quality **绕开** validator                | `QualityJobRunner` stub                               | **FAIL** | 同 2a-Q                              |
| CC-4 | validator 单测不涉及 live 档位                                                             | 单元测合法                                            | **PASS** | 须增最高接缝 quality child 测        |
| CC-5 | conflict skip 分支 `CONFLICT_CHECK_SKIPPED`；reconcile 非双源 normalize                    | `_validate_staging`；design §9                        | **FAIL** | 对表或 ADR 收窄范围                  |
| CC-6 | quality job 未接 validator 属本轮债                                                        | F-09                                                  | **FAIL** | 2a-Q                                 |
| CC-7 | severe 阻塞写；validation-only 不写 primary                                                | `DbValidationGate`                                    | **PASS** | 保持                                 |

**对象 3 小结：** **Validator 本体较完整**（sync 金路径可用）；**作为产品面的 data_quality/revision job 未验真**。**OPEN** · F-08 · F-09 · F-21 · F-13

---

## 对象 4 · write_manager（WriteManager + DbValidationGate）

| CC   | 本对象运行事实                                                                     | 证据 / 反证                                | Verdict  | 闭环控制                                     |
| ---- | ---------------------------------------------------------------------------------- | ------------------------------------------ | -------- | -------------------------------------------- |
| CC-0 | 用户要唯一写入口 + 八子组件 + 降级语义；交付 WriteManager 单体 + gate              | `write_manager.md` MergePlanner 等无独立类 | **FAIL** | ponytail 须 ADR/注释边界；非假装八组件       |
| CC-1 | `test_write_manager.py` 多 StubValidationGate；`test_db_validation_gate.py` 较正式 | 金路径用 `DbValidationGate`                | **FAIL** | 最高接缝写路径 outcome 测补强                |
| CC-2 | append/upsert + audit + lock **有**；replace_partition/manual_patch **未实现**     | `write_manager.py` L474–479                | **FAIL** | 权威 §7.3/§10 或 ADR defer（须严格阶段后置） |
| CC-3 | 所有 sync 写经 `SyncWritePipeline`→WriteManager；无发现旁路直写 clean              | grep 金路径                                | **PASS** | 保持 module boundary                         |
| CC-4 | degraded 写测有；route quality_flags→WriteRequest **未贯通**                       | `_resolve_write_provenance` 启发式         | **FAIL** | 从 RoutePlan 传递降级语义                    |
| CC-5 | gate 无 PASSED_PRIMARY vs PASSED_DEGRADED 细分                                     | design §6                                  | **FAIL** | 对表或收窄权威声称                           |
| CC-6 | 内联 merge 属结构债；若不影响 P1 可 ADR                                            | F-23 部分                                  | **FAIL** | ADR 边界 + 测锁定接缝                        |
| CC-7 | validation FAILED 拒绝写                                                           | `DbValidationGate`                         | **PASS** | 保持                                         |

**对象 4 小结：** **生产写边界有效**（非空壳）；**设计图八组件 / 全 write_mode / 降级链**未完整对表。**OPEN** · F-03 · F-13 · F-23（部分）

---

## 对象 5 · backfill（CLI + BackfillShardRunner）

| CC   | 本对象运行事实                                                                         | 证据 / 反证                                   | Verdict  | 闭环控制                         |
| ---- | -------------------------------------------------------------------------------------- | --------------------------------------------- | -------- | -------------------------------- |
| CC-0 | 用户要 Tier A 域 bounded live backfill + 续跑 + 审计；交付 baostock 金路径 + 11 源计划 | PRD §28；仅 baostock 强 outcome 测            | **FAIL** | 多域 honest BLOCKED 或 PASS 证据 |
| CC-1 | live PASS 测 patch `_build_datasource_service` replay port                             | `test_bounded_backfill_cli_e2e` · F-01        | **FAIL** | 正式入口无 patch 测              |
| CC-2 | 分片/cap/trigger/validation/write **有**；空分片 **停整 job**                          | `runners.py` L796–817 return                  | **FAIL** | F-18 续跑/跳过                   |
| CC-3 | CLI phase1 路径 vs 旧 baostock 专用路径已收敛到 phase1                                 | `backfill_plan` L541+ 仅 source-route-db live | **PASS** | 保持                             |
| CC-4 | replay 测标 live；本机真网 F-10 仅 baostock                                            | F-11 按设计                                   | **FAIL** | 档位不得混用关账                 |
| CC-5 | §13.4.3 步骤 1–5 大体对齐；步骤 6 标记部分有 evidence                                  | `build_backfill_evidence`                     | **FAIL** | 全路径 affected 标记             |
| CC-6 | F-01/F-18 可本轮修                                                                     | task-02 §7                                    | **FAIL** | P0 轨                            |
| CC-7 | 缺授权 BLOCKED 诚实                                                                    | `test_qmd_data_backfill_acceptance`           | **PASS** | 保持                             |

**对象 5 小结：** **非空壳**；**未按权威完整**（多域、无 patch、空分片）。**OPEN** · F-01 · F-03 · F-18 · F-10(样本) · F-20

---

## 对象 6 · full-load（CLI + FullLoadJobRunner）

| CC   | 本对象运行事实                                                            | 证据 / 反证                                                     | Verdict  | 闭环控制                |
| ---- | ------------------------------------------------------------------------- | --------------------------------------------------------------- | -------- | ----------------------- |
| CC-0 | PRD：超 `cn_equity+baostock` 试点；交付继承 backfill runner + baostock 测 | `test_qmdData_fullLoadAcceptance_livePassReplay...` 仅 baostock | **FAIL** | 第二域 cold-start 证据  |
| CC-1 | 同 backfill patch 依赖                                                    | replay patch                                                    | **FAIL** | 同 F-01                 |
| CC-2 | FULL_LOAD 事件/checkpoint/affected 标记 **有**（baostock）                | `full_load_evidence` 测                                         | **FAIL** | 去替身后仍成立          |
| CC-3 | 与 backfill 共用 `execute_spine_or_binding_live`                          | 同路                                                            | **PASS** | 保持                    |
| CC-4 | replay fetch_id 若标 live 则混档                                          | 须核对 report implementation_mode                               | **FAIL** | ADR-016 诚实            |
| CC-5 | §13.4.1 十步链在 baostock 样本成立；多域未证                              | design §13.4.1                                                  | **FAIL** | 扩域或诚实 BLOCKED 矩阵 |
| CC-6 | 同 backfill 共享根因                                                      | F-01                                                            | **FAIL** | P0 轨                   |
| CC-7 | 缺授权 BLOCKED                                                            | 同 backfill                                                     | **PASS** | 保持                    |

**对象 6 小结：** **试点级成品**，非 design/PRD 完整 full-load 面。**OPEN** · F-01 · F-03 · F-13

---

## 对象 7 · scheduler（`scheduler run` + profiles）

| CC   | 本对象运行事实                                                                           | 证据 / 反证                                     | Verdict  | 闭环控制              |
| ---- | ---------------------------------------------------------------------------------------- | ----------------------------------------------- | -------- | --------------------- |
| CC-0 | 用户要 daily_close 四 job 整单 P1-GATE；交付 weekly 可 PASS、daily FAIL                  | F-06 部分；F-08/09                              | **FAIL** | Slice 3 整单复验      |
| CC-1 | weekly live 绿靠 replay patch；daily quality 可能 synthetic PASS                         | `data_commands.scheduler_run` L1203–1254        | **FAIL** | 2a-0 RED 禁 synthetic |
| CC-2 | binding incremental/backfill/full_load **有** report；orchestrator quality **无** report | `scheduler.py` L445–454                         | **FAIL** | 2a-0                  |
| CC-3 | fred matrix vs binding DISABLED                                                          | F-07/F-14                                       | **FAIL** | Slice 1               |
| CC-4 | weekly replay 测 ≠ daily live 代表                                                       | 档位分裂                                        | **FAIL** | 分 profile 声称       |
| CC-5 | profile YAML 缺 data_quality；revision 缺 instrument_id                                  | `sync_scheduler_profiles.yaml` vs AD-6          | **FAIL** | 2a-Q/R1               |
| CC-6 | synthetic PASS、双轨 enable 可本轮修                                                     | F-06 · F-22 无 schema                           | **FAIL** | 2a-0 · profile schema |
| CC-7 | 缺 live 授权 BLOCKED；ResourceGuard skip non-core 诚实                                   | `test_syncSchedulerAcceptance_resourceGuard...` | **PASS** | 保持                  |

**对象 7 小结：** **调度骨架真实现**；**P1 代表 profile 未成品**，存在 **false-green 风险**。**OPEN** · F-06 · F-07 · F-08 · F-09 · F-14 · F-22

---

## Summary

- **首个决定性缺口：** **CC-2 验真** — `QualityJobRunner.run_revision_audit` / `run_data_quality` 仅 COUNT 行即 COMPLETED（`runners.py` L1253–1282），与 `data_sync_orchestrator.md` §13.4.4/§13.4.6 及 PRD §162 **shell-done**
- **第二决定性缺口：** **CC-3 同路** — fred **matrix overlay** vs **scheduler binding 默认 registry**（F-07/F-14）
- **第三决定性缺口：** **CC-1 证伪** — backfill/full-load/scheduler live outcome 测普遍 **patch `_build_datasource_service`**（F-01 · TEST-EVIDENCE-GOVERNANCE §4）
- **最终状态：** **OPEN**（Audit 声称「已完整落地」**拒绝**）
- **声称结论：** **denied** — 任一对象均存在 CC-1/CC-2/CC-3/CC-5 **FAIL**；不得 CLOSED
- **闭环控制：** 以 `PHASE1_COMPLETION_INVENTORY.md` + `task-02-layer1-full-findings.md` 23 项 ledger 为准；`uv run pytest -q` 全绿 **不等于** 本审计 PASS；复验须 **正式入口 outcome** + findings 零「仍开放」

### 模块级总表（审计员速查）

| 模块          | 空壳？                | 机制存在？                     | 权威完整？ | 决定性 CC                  |
| ------------- | --------------------- | ------------------------------ | ---------- | -------------------------- |
| data_sources  | 否                    | 是（planner/registry/service） | 否         | CC-2 fallback · CC-3 双轨  |
| sync          | 部分（quality jobs）  | 是（主线 runners）             | 否         | CC-2 revision/quality stub |
| validation    | 否（validator 本体）  | 是（金路径）                   | 部分       | CC-3 job 未接              |
| write_manager | 否                    | 是（唯一写口）                 | 部分       | CC-5 八组件/降级链         |
| backfill      | 否                    | 是                             | 否         | CC-2 空分片 · CC-1 patch   |
| full-load     | 否                    | 是（试点）                     | 否         | CC-0 单源试点              |
| scheduler     | 部分（daily quality） | 是（weekly+聚合）              | 否         | CC-1 synthetic PASS        |

### 权威文件索引（MIGRATION_MAP）

| 域           | 设计权威                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------------ |
| data_sources | `docs/modules/design/data_sources.md` · `source_route_plan.md` · `source_capability_registry.md` |
| sync         | `docs/modules/design/data_sync_orchestrator.md` · `03_runtime_flows.md`                          |
| validation   | `docs/modules/design/data_validation_and_conflict.md` · `source_conflict_rules.yaml`             |
| write        | `docs/modules/design/write_manager.md` · `lock_and_concurrency_policy.md`                        |
| Phase 1 接缝 | `PHASE1_PRD.md` · `data_cli_contract.yaml` · `sync_scheduler_profiles.yaml`                      |

---

## 8. 端到端金路径追踪（`03_runtime_flows.md` · Phase 1 PRD）

> **声称：** Scheduler/CLI → ResourceGuard → Sync → Validator → WriteManager → downstream read  
> **正式样本：** `qmd-data data backfill|full-load|scheduler` + `cn_equity_daily_bar/baostock` + `source-route-db` live

```text
CLI (data_commands / scheduler_run)
  → phase1_acceptance.execute_spine_or_binding_live
      → SourceRoutePlanner.plan (preview)     [✅ 有 ROUTE_PLAN 事件]
      → _build_datasource_service             [⚠️ baostock 专用 vs product_live 分裂]
      → DataSourceService.fetch               [⚠️ use_fallback 永不启用]
      → adapter/fetch_port → raw/fetch_log    [⚠️ F-01 部分源 fetch_port 链]
      → staging                               [✅ 金路径]
      → SyncValidationPipeline                [✅ DataQuality + 可选 Conflict]
      → WriteManager + DbValidationGate       [✅ 唯一写口]
      → clean table + write_audit             [✅ baostock 样本]
      → AcceptanceReport + observability      [❌ F-03 可为空]
```

**scheduler `daily_close` 分叉（与上不同）：**

```text
incremental (fred) → binding → _build_datasource_service (无 overlay)  [❌ F-07 DISABLED]
revision_audit     → _run_orchestrator_job → QualityJobRunner stub    [❌ F-08 空壳]
                     → scheduler_run 无 acceptance_report
                     → 可能 synthetic PASS (L1203–1254)                  [❌ CC-1 假绿]
data_quality       → [profile YAML 未写入]                            [❌ F-09]
```

**结论：** 八步链在 **单源单入口** 下**机制闭合**；**产品面**（daily_close 四 job、多入口、fallback、quality）**未闭合**。

---

## 9. 权威逐条对照（对抗性 · 节选）

### 9.1 `data_sources.md` §5.10 验收测试 vs 实现

| 设计测试（§5.10）                                  | 实现 / 测试                                        | 审计                    |
| -------------------------------------------------- | -------------------------------------------------- | ----------------------- |
| source disabled → 不抓取                           | `test_disabledPrimaryDomain_returnsDisabledSource` | **PASS**                |
| fallback_policy=mark_missing → 不接管              | planner 有逻辑；**fetch 未接 use_fallback**        | **FAIL**（热路径未验）  |
| use_validation_source_with_flag → degraded + flags | planner 可加 flag；**写路径未读 flags**            | **FAIL**                |
| Validation 冲突 → SourceConflictValidator          | 金路径有；quality job 无                           | **部分**                |
| test_fallbackDisabledByDefault                     | `test_source_registry.py` L515                     | **PASS**（registry 层） |

**反证：** `rg use_fallback=True backend/` → **零命中**；仅 `tests/` 与 `preview_route` 使用 fallback。

### 9.2 `data_sync_orchestrator.md` 六类 Job

| Job                  | 设计 § | 实现锚点                              | 成品？             |
| -------------------- | ------ | ------------------------------------- | ------------------ |
| IncrementalUpdateJob | 13.4.2 | `IncrementalJobRunner`                | ✅ 金路径          |
| BackfillJob          | 13.4.3 | `BackfillShardRunner`                 | ⚠️ 空分片 F-18     |
| FullLoadJob          | 13.4.1 | `FullLoadJobRunner`                   | ⚠️ 试点域          |
| RevisionAuditJob     | 13.4.4 | `QualityJobRunner.run_revision_audit` | ❌ 空壳            |
| ReconcileJob         | 13.4.5 | `ReconcileJobRunner`                  | ⚠️ 仅 primary 重抓 |
| DataQualityJob       | 13.4.6 | `QualityJobRunner.run_data_quality`   | ❌ 未调 validator  |

### 9.3 `data_validation_and_conflict.md` 规则覆盖

| 规则类                                   | 实现                                   | 缺口      |
| ---------------------------------------- | -------------------------------------- | --------- |
| PK / 必填 / 枚举 / OHLC                  | `data_quality.py`                      | ✅        |
| schema drift / stale                     | `data_quality.py`                      | ✅        |
| INVALID_TRADE_DATE / MISSING_TRADING_DAY | —                                      | ❌ 未实现 |
| conflict 多字段 comparable               | YAML 有；runner 常只比 `close`         | ⚠️        |
| severe → manual_review                   | validator 有；validate_rows 默认 false | ⚠️        |

### 9.4 `write_manager.md` 子组件

| 设计组件                                       | 代码                               | 审计                              |
| ---------------------------------------------- | ---------------------------------- | --------------------------------- |
| ValidationGate                                 | `DbValidationGate`                 | ✅ 生产用                         |
| MergePlanner / TransactionRunner / AuditLogger | 内联于 `WriteManager`              | ⚠️ ponytail；非设计八类独立       |
| replace_partition / manual_patch               | 抛 NotImplemented                  | ❌ P1 若声称全 write_mode 则 FAIL |
| 降级写 provenance                              | `_resolve_write_provenance` 启发式 | ⚠️ 未接 RoutePlan flags           |

### 9.5 Phase 1 契约（`data_cli_contract.yaml`）

| 要求                                   | backfill    | full-load | scheduler          |
| -------------------------------------- | ----------- | --------- | ------------------ |
| `official_commands_must_expose` 七字段 | ✅          | ✅        | ✅                 |
| `gate_eligible` live + source-route-db | ⚠️ F-01     | ⚠️ F-01   | ⚠️ daily 整单 FAIL |
| `observability_evidence` 非空（G3）    | ❌ F-03     | ❌ F-03   | ❌ quality 路径    |
| 非 gate：replay/mock/dry-run           | F-11 按设计 | 同左      | 同左               |

---

## 10. 对抗性挑战清单（已执行）

| #   | 挑战                                                        | 结果                               | 命中 CC |
| --- | ----------------------------------------------------------- | ---------------------------------- | ------- |
| C1  | 去掉 `_build_datasource_service` patch 后 live 测是否仍绿？ | 多数 **否** / 未测                 | CC-1    |
| C2  | `use_fallback` 生产热路径是否存在？                         | **backend 零 `use_fallback=True`** | CC-2    |
| C3  | 同 fred 源：matrix sync vs scheduler daily_close 同参？     | **分裂 DISABLED**                  | CC-3    |
| C4  | quality child 无 report 时 parent 是否仍可能 PASS？         | **synthetic 分支存在**             | CC-1    |
| C5  | revision_audit 去掉 COUNT 后是否仍有 diff/写库？            | **无**                             | CC-2    |
| C6  | 空分片 backfill 是否续跑？                                  | **return 停整 job** L796–817       | CC-2    |
| C7  | pytest 全绿是否等于本审计 PASS？                            | **否**                             | Summary |
| C8  | 「机制有」是否等于「权威完整」？                            | **否**（F-13）                     | CC-0    |

---

## 11. 测试证据治理（TEST-EVIDENCE-GOVERNANCE 摘要）

| 测试资产                            | 保护的生产保证              | 正式入口？          | 判别力                | 判定                       |
| ----------------------------------- | --------------------------- | ------------------- | --------------------- | -------------------------- |
| `test_data_quality_validator.py`    | 规则→gate 拒绝              | 间接                | 高                    | **保留**                   |
| `test_source_conflict_validator.py` | 阈值/severe/人工队列        | 间接                | 高                    | **保留**                   |
| `test_source_route_planner.py`      | planner 行为                | 否                  | 中（多 patch enable） | **保留+补接缝**            |
| `test_sync_orchestrator.py`         | 状态机/分片                 | 否（staging patch） | 中                    | **保留+补 CLI 接缝**       |
| `test_b3f_quality_runners.py`       | 「非 defer」字样            | 否                  | **低（vacuous）**     | **F-21 须改写**            |
| `test_bounded_backfill_cli_e2e.py`  | 续跑/checkpoint             | CLI+patch           | 中                    | **去 patch 后复验**        |
| `test_qmd_data_*_acceptance.py`     | P1 信封                     | CLI+常 patch        | 中                    | **增无 patch 子集**        |
| `test_sync_scheduler_acceptance.py` | weekly spine / synthetic 禁 | CLI+replay patch    | 中高                  | **补 daily_close outcome** |
| `conftest` ResourceGuard autouse    | —                           | 全局污染            | **负**                | **F-19**                   |

---

## 12. 根因聚类与修复顺序（共享一处修）

```text
集群 A · 正式入口接线（最高优先级）
  根因：_build_datasource_service / enable overlay / fetch_port / file_registry 分裂
  症状：F-01 · F-07 · F-14 · F-03（证据回填依赖完整 fetch/job）
  修复面：phase1_acceptance · product_live_ports · scheduler binding · 共享 enable helper
  验证：四条 CLI + scheduler daily_close fred 无 patch 最高接缝测

集群 B · scheduler quality 假绿 + 空壳
  根因：orchestrator child 不产 report；QualityJobRunner stub；scheduler_run synthetic PASS
  症状：F-06 · F-08 · F-09 · 2a-0
  修复面：2a-0 → 2a-R* → 2a-Q（串并行见 task_plan）
  验证：禁 route_plan_id=None 的 child PASS；revision 六步；data_quality validator

集群 C · backfill 韧性 + 测试卫生
  根因：空分片 fail-stop；弱测；conftest autouse
  症状：F-18 · F-20 · F-21 · F-19
  修复面：BackfillShardRunner · 集成测 · conftest 分层
```

**建议顺序：** **A → B → C**（与 `PHASE1_COMPLETION_INVENTORY.md` P0 轨一致）。

---

## 13. 再验收门槛（Audit → CLOSED 条件）

声称从 **OPEN** 升为 **CLOSED** 须**全部**满足：

1. 本文件 **7 个对象 × CC-0–CC-7** 无 **FAIL**（`NA`/`PASS` 须有依据）
2. `task-02-layer1-full-findings.md` **23 项** ledger 仅 {已关闭, 按设计}
3. `daily_close` live 复验：四 job 齐全；parent `gate_eligible`；core child 诚实非假绿
4. **至少一条** per 命令（backfill / full-load / scheduler）**无 `_build_datasource_service` patch** 的 outcome 测
5. `data_sources.md` §5.10 中与 P1 相关的 fallback/degraded **热路径**有测或 ADR 收窄权威
6. `uv run pytest -q` exit 0（必要非充分）

**当前判定：再验收门槛 0/6 → 保持 OPEN。**

---

## 14. completion-check.project 模式触达（本轮审计）

| 模式（见 `completion-check.project.md`） | 本轮是否再次命中                  |
| ---------------------------------------- | --------------------------------- |
| 质检 runner 空壳                         | ✅ F-08/F-09                      |
| matrix/binding 启用双轨                  | ✅ F-07/F-14                      |
| 调度层合成 PASS 信封                     | ✅ scheduler_run L1203–1254       |
| 测注入正门分裂                           | ✅ live 测 patch                  |
| 决议已关台账仍待实现                     | ✅ F-15 决议 A / F-01·F-03 重开   |
| 可观测必填空值过关                       | ✅ F-03                           |
| fallback 热路径未接                      | **建议新起一行模式**（§9.1 反证） |

---

_审计方法：completion-check CORE v3 TRACE + TEST-EVIDENCE-GOVERNANCE v2；代码抽检 2026-07-10。§8–§14 续补 2026-07-10 晚。_
