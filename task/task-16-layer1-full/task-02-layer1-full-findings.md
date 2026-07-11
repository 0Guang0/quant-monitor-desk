# task-02-layer1-full · Findings 台账（活文档）

> **更新：** 2026-07-10（§7 自 task-01.5 承接 · F-01/F-03 复核重开）  
> **规则：** 每条 finding 一种 disposition：`已关闭` · `仍开放` · `按设计`。**P1-GATE 关账**仅允许 `已关闭` / `按设计`；**禁止** `阶段外置`（见 `task_plan.md` Authority Parity · G8）。  
> **分工：** 本文件 = **查证/计划阶段**的问题与 disposition；**执行期计划外决策** → `note.md`（AC-CLOSE-2），勿混。  
> **复验：** 代码 + pytest + 本机真网（baostock）；GitNexus 查码 `execute_spine_or_binding_live` · `SourceRoutePlanner.plan` · `QualityJobRunner`

---

## 1. 仍开放（P1-GATE 相关）

### F-01 · backfill / full-load / scheduler 真跑崩溃 `fetch_port is required`（**复核重开** · 2026-07-10）

| 项              | 内容                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **来源**        | task-01.5 **FIND-B-01**（§9.2 迁入 · 原标「已关闭」作废）                                                                 |
| **现象**        | 正式 CLI 部分路径仍可能 **`fetch_port is required`** 崩溃；测试靠 patch `_build_datasource_service` 或 replay port 才能绿 |
| **为何重开**    | 前执行者曾标 **已关闭**（commits `0aceff32` 等），task-01.5 对抗审计复核认为入口脱节**未真正消除**；缺口仍大量存在        |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**                                                                      |
| **关账条件**    | 全正式写入口不经 patch 亦可跑；`fetch_port` 接线根因消除 + 最高接缝测锁定                                                 |

### F-03 · sync PASS 但 `observability_evidence` 全空（**复核重开** · 2026-07-10）

| 项              | 内容                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------ |
| **来源**        | task-01.5 **FIND-B-02**（§9.2 迁入 · 原标「已关闭」作废）                                        |
| **现象**        | sync 能跑但 **`fetch_log_ids` / `rows_written`** 等 R4 证据链可为空；矩阵/binding 路径回填不完整 |
| **为何重开**    | 前执行者曾标 **已关闭**；复核认为 R4 验收信封**未全路径诚实**                                    |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**                                             |
| **关账条件**    | 全正式 sync/backfill 路径 `observability_evidence` 非空且可审计；最高接缝 live/replay 测锁定     |

### F-07 · scheduler binding 路径 fred 未走统一启用语义 → `DISABLED_SOURCE`

| 项                                 | 内容                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **现象**                           | `daily_close` live：`fred` incremental 子任务 `FAILED_FINAL`，errors 含 `route_status=DISABLED_SOURCE`；parent 诚实 `FAIL`                                                                                                                                                                                                                                                                                                                                                                             |
| **根因（路由已落地，接线未接严）** | `SourceRoutePlanner` + `DataSourceService.fetch` **已成品**；问题在 **入口双轨**：(1) registry：`fred` `enabled_by_default: false`（规格+代码一致，见 F-17）；(2) scheduler 有 binding 时走 `resolve_binding_datasource_service` → `_build_datasource_service` → `build_product_live_service()`，使用**默认** `SourceRegistry`，**未** overlay `enabled_fred_source_registry()` / `enabled_source_registry()`。对比：矩阵 spine `execute_fred_matrix_live` → `_run_fred_macro_live_sync` 会临时 enable |
| **证据**                           | `phase1_acceptance._build_datasource_service` L929–955 · `product_live_ports.build_product_live_service` 无 registry 注入 · `fred_incremental_watermark.enabled_fred_source_registry` · `matrix_live_handlers.execute_fred_matrix_live`                                                                                                                                                                                                                                                                |
| **与用户「已放开权限」**           | 通常指 `FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH`；**不等于** binding 路径已 enable。仅配 key 仍可能 DISABLED                                                                                                                                                                                                                                                                                                                                                                                             |
| **disposition**                    | **仍开放** · 切片 `P1-SCHED-FRED`（`task_plan.md` Slice 1）                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **关账条件**                       | binding 与 matrix spine **同一套**启用语义（正式写入口，非测试 monkeypatch）；`daily_close` fred child 在授权+启用条件下非误报 `DISABLED_SOURCE`；最高接缝测锁定                                                                                                                                                                                                                                                                                                                                       |

### F-14 · 双轨启用语义（同源不同入口）

| 项              | 内容                                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **现象**        | 同一条 fred 宏观线：`qmd-data data sync`（矩阵）在 overlay enable 后可跑；`scheduler run --profile daily_close`（binding）仍 DISABLED |
| **业务影响**    | 用户感知「路由不一致」；误以为「路由没落地」或「registry 忘了开」                                                                     |
| **根因**        | 非 planner 缺失，而是 **CLI 接缝两条路径对 registry 处理不一致**（见 F-07）                                                           |
| **disposition** | **仍开放** · 与 F-07 同切片关账                                                                                                       |
| **关账条件**    | One-Version Rule：全正式入口共享同一 enable 策略                                                                                      |

### F-15 · `macro_series` 域 production-live（**决议 A · 2026-07-09**）

| 项              | 内容                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------- |
| **决议**        | **A · 纳入** P1 `daily_close` production-live，与 `sync_scheduler_profiles.yaml` 对齐（OQ-P1-Q6 已关闭 · AD-11） |
| **待做**        | Slice 1-P：更新 `domain_roles.macro_series` registry；fred 源仍 disabled-by-default + 按源启用                   |
| **关账条件**    | registry 落地 + 测 + 与 Slice 1 接缝一致；前置齐全时宏观 child 非域级误挡                                        |
| **disposition** | **仍开放**（决议已拍板 · **实现**待 Slice 1-P）                                                                  |

### F-16 · 无 Tier A / READY_WITH_EVIDENCE 运营启用清单 SSOT

| 项              | 内容                                                                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **现象**        | 各源 `notes` 分散（READY_WITH_EVIDENCE、DCP-05、ADR-009）；缺单一表：adapter ✓ · capability ✓ · replay ✓ · clean ✓ → **谁 flip `is_enabled` / `domain_enabled`** |
| **业务影响**    | 运营与开发无法判断「该开哪个源」；易误走 mass-enable YAML                                                                                                        |
| **权威**        | `data_sources.md` §5.9.1：完成证据后**才能**启用，非默认全开                                                                                                     |
| **disposition** | **仍开放** · 建议 `task_plan.md` 增运营清单切片或 `docs/ops/` 登记（P1 可与 Slice 1 并行文档）                                                                   |
| **关账条件**    | Tier A 11 源 + fred 金路径各行：启用前置 · owner · 关账测 · **禁止** bulk `enabled_by_default: true`                                                             |

### F-08 · `revision_audit` 未接成品（空壳）

| 项               | 内容                                                                                                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **现象**         | `daily_close` 含 `revision_audit`；live 报 `revision_audit requires instrument_id`                                                                                                                |
| **根因**         | `QualityJobRunner.run_revision_audit`（`sync/runners.py`）仅为 minimal：要 `instrument_id`、数 clean 表行数、转状态机；**无**修订对比、重拉、Phase1 验收信封。profile YAML 未提供 `instrument_id` |
| **PRD**          | §162：若纳入 Phase 1 最终 job 行为，不能停留 state-machine stub，须可观察产品工作或 ADR defer                                                                                                     |
| **Slice 0 决策** | **A · 成品纳入 P1**；**P1 必做修订 diff**（`task_plan.md` AD-7）                                                                                                                                  |
| **daily_close**  | `revision_audit` macro/fred + **`data_quality` cn_equity/baostock**（均 P1，不延后）                                                                                                              |
| **disposition**  | **仍开放** · 切片 2a-R1–R3                                                                                                                                                                        |

### F-09 · `data_quality` 同 F-08（空壳）

| 项               | 内容                                                        |
| ---------------- | ----------------------------------------------------------- |
| **现象**         | 与 revision_audit 同族 minimal runner（`run_data_quality`） |
| **Slice 0 决策** | **A**；**cn_equity/baostock** 金路径；**daily_close 必含**  |
| **disposition**  | **仍开放** · 切片 2a-Q                                      |

### F-13 · 全链路「机制有、按入口/源/任务类型仍有缝」

| 项              | 内容                                                                                                                                            |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **说明**        | 8 步金路径在隔离验收库**已实现**；`SourceRoutePlanner` **已落地**（见 §6）。缝隙见 F-01/F-03/F-07/F-14/F-15、F-08/F-09、`daily_close` 整单 PASS |
| **disposition** | **仍开放**（随 P0 切片关闭）                                                                                                                    |

### F-18 · 空分片拖死整 backfill job（task-01.5 AUD-S5-06 / AUD-DOUBT-15）

| 项              | 内容                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------- |
| **来源**        | task-01.5 **AUD-S5-06** · **AUD-DOUBT-15**                                                  |
| **现象**        | 某片无 bar 时 fetch 无 staging → `FAILED_RETRYABLE` 并**停止后续片**；S5 切片更细后更易触发 |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**                                        |
| **关账条件**    | runners 空分片续跑/跳过策略 + 集成行为测；e2e 不得仅靠 replay 日期对齐规避                  |

### F-19 · conftest ResourceGuard autouse 假绿（task-01.5 FIND-A-01 / AUD-DOUBT-09）

| 项              | 内容                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------ |
| **来源**        | task-01.5 **FIND-A-01** · **AUD-DOUBT-09**                                                 |
| **现象**        | `tests/conftest.py` **autouse** 全局 ResourceGuard=OK；主机压力时集成路径 guard 失效不可见 |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**                                       |
| **关账条件**    | 分层 fixture：仅 guard 专测保留真实 guard；集成路径 opt-in 压测或真实 guard                |

### F-20 · scheduler/baostock 宽窗片数无集成行为测（task-01.5 AUD-TEST-04）

| 项              | 内容                                                                                                |
| --------------- | --------------------------------------------------------------------------------------------------- |
| **来源**        | task-01.5 **AUD-TEST-04**                                                                           |
| **现象**        | cap 已在 `plan_backfill_shards` 单测 + runners 代码，但 scheduler/baostock **宽窗片数**缺集成行为测 |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**                                                |
| **关账条件**    | scheduler + baostock 宽窗路径片数/预算集成测绿                                                      |

### F-21 · 弱测试无业务 outcome（task-01.5 FIND-A-03）

| 项              | 内容                                                      |
| --------------- | --------------------------------------------------------- |
| **来源**        | task-01.5 **FIND-A-03**                                   |
| **现象**        | vacuous / call-count / 宽枚举 membership 测试仍散见各模块 |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**      |
| **关账条件**    | 按 `testing-guidelines` 替换为 outcome 测或删无效测       |

### F-22 · `sync_scheduler_profiles.yaml` 无 schema 校验（task-01.5 FIND-E-01）

| 项              | 内容                                                                 |
| --------------- | -------------------------------------------------------------------- |
| **来源**        | task-01.5 **FIND-E-01**                                              |
| **现象**        | scheduler profile YAML **无 schema 校验**；拼写/字段漂移难以及早发现 |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**                 |
| **关账条件**    | profile schema + CI/契约测锁定                                       |

### F-23 · Orchestrator 单体 · adapter 绑具体 storage（task-01.5 FIND-E-02）

| 项              | 内容                                                     |
| --------------- | -------------------------------------------------------- |
| **来源**        | task-01.5 **FIND-E-02**                                  |
| **现象**        | Orchestrator 单体过大；adapter 绑具体 storage（R2-RISK） |
| **disposition** | **仍开放** · Phase 1 **必关** · **禁止再次阶段外置**     |
| **关账条件**    | 按 task_plan 切片拆分或 ADR 记录边界 + 测锁定接缝        |

---

## 2. 已关闭（勿重开）

> **注意：** **F-01** · **F-03** 曾标「已关闭」，2026-07-10 task-01.5 复核后**重开**至 §1；本节条目勿与 §1 重开项混淆。

### F-02 · 测试仅 monkeypatch `_build_datasource_service` 才能绿（过期）

| 项              | 内容                                                                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **原报告**      | Findings.txt #4                                                                                                                                              |
| **现状**        | 正式路径不再依赖 patch `_build_datasource_service`；`test_backfillOfficialPath_usesWiredDatasourceServiceWithoutPhase1Patch` 仅 patch **网络层** replay port |
| **disposition** | **已关闭**（接线根因）；CI replay 见 F-11 **按设计** · F-01 重开见 §1                                                                                        |

---

## 3. 复验通过（非缺陷 · 记录口径）

### F-04 · 四条命令验收形状统一

| 项              | 内容                                                                                                                                                  |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **结论**        | `sync` / `backfill` / `full-load` / `scheduler` 均暴露 `data_cli_contract.yaml` `official_commands_must_expose` 字段；本机实测 `missing_envelope: []` |
| **说明**        | scheduler **父单**行数证据在 **子单** `child_envelopes`；设计如此，非格式分裂                                                                         |
| **disposition** | **已关闭**（满足 G1）· 2026-07-09                                                                                                                     |

### F-05 · live 与 replay 诚实区分

| 项               | 内容                                                                                                                 |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- |
| **真 live 路径** | `implementation_mode: live`；缺 `QMD_ALLOW_LIVE_FETCH` → `BLOCKED`；`baostock-live-*` fetch_id ≠ `baostock-replay-*` |
| **防假绿**       | `test_matrix_live_evidence_honesty.py` · ADR-016                                                                     |
| **CI replay**    | 见 F-11；**不**冒充产品 live 关账                                                                                    |
| **disposition**  | **已关闭**（产品路径诚实）；测试轨道见 F-11                                                                          |

### F-06 · scheduler live 语义：结构诚实、整 profile 未成品

| 项              | 内容                                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **已做到**      | parent + child 信封；`weekly_backfill` live backfill child **PASS**（本机 replay 注入时）；required child 失败 → parent **FAIL**（非假绿） |
| **未做到**      | `daily_close` 整单 PASS（fred F-07 + revision_audit F-08）                                                                                 |
| **disposition** | **部分仍开放** · 聚合机制 **已关闭** · profile 成品 **仍开放**                                                                             |

### F-10 · 本机真连 baostock（无 replay patch）

| 项              | 内容                                                                                                                  |
| --------------- | --------------------------------------------------------------------------------------------------------------------- |
| **环境**        | `QMD_ALLOW_LIVE_FETCH=1` · 隔离 `source-route-db-*` 根 · 终端见 baostock login/logout                                 |
| **结果**        | sync **PASS**（21 行写入，小票完整）；backfill/full-load **PASS**；`weekly_backfill` scheduler child backfill 可 PASS |
| **disposition** | **已关闭**（本机金路径）· 2026-07-09                                                                                  |

### F-11 · 测试故意用 replay 而非每次真上网

| 项              | 内容                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------- |
| **原因**        | ADR-015 双轨：默认 pytest **快、稳、无 key**；真网 `@pytest.mark.network` + `--run-network` |
| **业务比喻**    | 样货演练查流水线 vs 真货车卸货验收；两条都要，职责不同                                      |
| **disposition** | **按设计** · 非缺陷                                                                         |

### F-12 · 是否只有 baostock 接通完整流水线？

| 项               | 内容                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **结论**         | **否。** M-DATA-03 已关：22 源矩阵 · Tier A 11 · 适配器/矩阵 handler 在隔离库有证据                                            |
| **产品体感差异** | baostock：`enabled_by_default: true`，四命令本机真网最顺；fred 等：默认关闸 + 须 key + 正确入口；scheduler fred 另见 F-07/F-14 |
| **disposition**  | **按设计**（多源能力已有；默认可用性因源而异）                                                                                 |

### F-17 · registry 大量 `enabled_by_default: false`（路由已落地 · 非「未实现所以全关」）

| 项              | 内容                                                                                                                                                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **结论**        | **显式路由机制已成品**：`SourceRoutePlanner.plan` · `DataSourceService.fetch` 先 plan 后 fetch · `job_event_log` ROUTE_PLAN 持久化 · `test_source_route_planner.py`（含 `test_r3h01_officialMacroRoute_disabledByDefault`） |
| **业务含义**    | 大量禁用是 **`data_sources.md` §5.9.1** · **`source_route_plan.md` §5** 规定的**默认不上生产**，不是 planner 缺席                                                                                                           |
| **禁止**        | 批量把 `source_registry.yaml` 改为 `enabled_by_default: true` → 违反权威 + 打穿契约测                                                                                                                                       |
| **disposition** | **按设计** · 启用须 **按源**（F-16 清单），客观不可用继续 `DISABLED_SOURCE` / `USER_AUTH_REQUIRED`（ADR-015/016）                                                                                                           |

---

## 4. 归档：已过期源报告

`task/audit/task-02-layer1-full/Findings.txt`（手写审计 #1–#5）**整体过期**，已由本节 F-01–F-03 关闭、F-04–F-17 取代。**勿**再作为 P1-GATE 依据。

---

## 6. 路由与启用 · 产品决议（2026-07-09 · GitNexus + 权威对照）

> **权威：** `MIGRATION_MAP.md` → `source_route_plan.md` · `source_route_contract.yaml` · `data_sources.md` §5.9.1/§573 · `source_registry.yaml`

### 6.1 路由规则（业务一句话）

每次抓数前产出可审计 **SourceRoutePlan**：按 domain 主/校验/降级候选 + registry 启用 + capability + 平台/授权检查选源；**禁止 silent fallback**；未 READY 则诚实 `DISABLED_SOURCE` 等。

### 6.2 仍是半成品 / 有漏洞（路由相关 · 靠改 YAML 全开解决不了）

| 缺口                                    | Finding     | 业务影响                                                                   |
| --------------------------------------- | ----------- | -------------------------------------------------------------------------- |
| scheduler binding 未走 fred 启用 helper | **F-07**    | `daily_close` fred 仍 DISABLED；`build_product_live_service` 默认 registry |
| 双轨启用语义                            | **F-14**    | 矩阵 CLI 能跑、scheduler 不能                                              |
| macro_series 域 not production-live     | **F-15**    | **决议 A** · 待 Slice 1-P 改 registry 与 profile 对齐                      |
| P1 quality / revision 未成品            | **F-08/09** | 与路由无关；`daily_close` 整单仍红                                         |
| 无运营启用清单 SSOT                     | **F-16**    | READY_WITH_EVIDENCE 源不知何时 flip enabled                                |

### 6.3 不要做的

- **不要** mass-enable：`source_registry.yaml` 批量 `enabled_by_default: true` → 违反 `data_sources.md` · `source_route_plan.md`，打穿 `test_r3h01_*` 等（**F-17**）。
- **不要**把 validation-only 源（akshare、yahoo 等）当生产 Primary。

### 6.4 应该做的（对齐权威最终形态）

| 顺序 | 动作                                                                                                                                                              | 切片 / Finding                |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| 1    | **修接线一致性**：binding 与 matrix spine 同一套 `enabled_source_registry` 语义（正式写入口，非测试 patch）                                                       | Slice 1 · **F-07** · **F-14** |
| 2    | **按源启用**：Tier A + READY_WITH_EVIDENCE → adapter/capability/replay/clean ✓ 后再 flip；FRED 另需 `FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH` + **F-15** 域策略签字 | **F-16**                      |
| 3    | **继续诚实暴露不可用**                                                                                                                                            | ADR-015/016 · **按设计**      |
| 4    | **P1 其余**：0-N 正名 → quality/revision 成品 → `daily_close` 四 job                                                                                              | **F-08/09** · `task_plan.md`  |

### 6.5 OQ「已关闭」≠ 代码已完成

`task_plan.md` Open Questions（Q2/Q3/Q5 等）**已关闭** = **决策拍板**；实现状态见 §1 仍开放项。

---

## 7. 自 task-01.5 承接（2026-07-10 · Phase 1 必关）

> **规则：** 下列项自 task-01.5 §9.2 **阶段外置**迁入；**disposition 一律仍开放**；**禁止再次阶段外置**（G8 · Authority Parity）。

| task-01.5 ID                     | task-02 ID                  | 业务含义（一句话）                               |
| -------------------------------- | --------------------------- | ------------------------------------------------ |
| **FIND-B-01**                    | **F-01**（重开）            | CLI 正式路径仍可能 `fetch_port is required` 崩溃 |
| **FIND-B-02**                    | **F-03**（重开）            | sync 证据链 `fetch_log_ids` 等可为空             |
| **AUD-S5-06** · **AUD-DOUBT-15** | **F-18**                    | 空分片拖死整 backfill job                        |
| **FIND-A-01** · **AUD-DOUBT-09** | **F-19**                    | conftest ResourceGuard autouse 假绿              |
| **AUD-TEST-04**                  | **F-20**                    | scheduler/baostock 宽窗片数缺集成测              |
| **FIND-A-03**                    | **F-21**                    | 弱测试无业务 outcome                             |
| **FIND-2-01**                    | **F-08**（对齐）            | `revision_audit` minimal stub                    |
| **FIND-2-02**                    | **F-09**（对齐）            | `data_quality` 同族 stub                         |
| **FIND-2-03**                    | **F-06**（对齐）            | scheduler quality child 合成 PASS 需复核         |
| **FIND-3-01**                    | **F-07** · **F-14**（对齐） | fred matrix overlay vs binding 双轨              |
| **FIND-E-01**                    | **F-22**                    | scheduler profile YAML 无 schema                 |
| **FIND-E-02**                    | **F-23**                    | Orchestrator 单体 / adapter storage 绑死         |

**未迁入（按设计保留于 task-01.5）：** **FIND-A-02**（replay CI 彩排）· **FIND-C-01**（sandbox DONE ≠ live primary）。

**task-01.5 本票已关：** **AUD-DOUBT-12**（`incremental_gold_path_*` rename · 2026-07-10）。

---

## 5. Ledger 速查

| ID   | 标题                         | disposition                       |
| ---- | ---------------------------- | --------------------------------- |
| F-01 | fetch_port 崩溃              | **仍开放**（复核重开 · §7）       |
| F-02 | monkeypatch 接线             | 已关闭                            |
| F-03 | sync 证据空                  | **仍开放**（复核重开 · §7）       |
| F-04 | 四命令信封统一               | 已关闭                            |
| F-05 | live/replay 诚实             | 已关闭                            |
| F-06 | scheduler 诚实聚合           | 部分仍开放                        |
| F-07 | scheduler fred 双轨 DISABLED | **仍开放**                        |
| F-08 | revision_audit 空壳          | **仍开放**                        |
| F-09 | data_quality 空壳            | **仍开放**                        |
| F-10 | 本机 baostock 真网           | 已关闭                            |
| F-11 | replay 测试轨道              | 按设计                            |
| F-12 | 仅 baostock？                | 按设计                            |
| F-13 | 全链路缝隙                   | **仍开放**                        |
| F-14 | 双轨启用语义                 | **仍开放**                        |
| F-15 | macro_series 域 A 落地       | **仍开放**（决议已定 · 实现 1-P） |
| F-16 | 运营启用清单 SSOT            | **仍开放**                        |
| F-17 | 大量 disabled 按设计         | 按设计                            |
| F-18 | 空分片拖死 backfill          | **仍开放**（§7）                  |
| F-19 | ResourceGuard autouse 假绿   | **仍开放**（§7）                  |
| F-20 | scheduler 宽窗集成测缺口     | **仍开放**（§7）                  |
| F-21 | 弱测试无 outcome             | **仍开放**（§7）                  |
| F-22 | scheduler YAML 无 schema     | **仍开放**（§7）                  |
| F-23 | Orchestrator 单体债          | **仍开放**（§7）                  |
