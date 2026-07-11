# Implementation Plan: task-01.5 · task-02 Phase 1 前置阻塞

> **角色：** `task-02-layer1-full` 的 **硬前置**；未绿 **禁止** 开工 `task_plan.md` Slice 0-N 及以后。  
> **活文档：** `findings.md` · `progress.md` · `note.md`  
> **输入 SSOT：** `task/audit/TEMP-ADR-cleanup-vs-runtime-behavior-review.md`（已归档；原路径见本目录重定向 stub）  
> **更新：** 2026-07-10（S3–S5 · AUD-DOUBT · 测试卫生）

---

## Goal

在不动「一区 B1–B10」安全/数据正确性**行为**的前提下，关账 TEMP 中 **全部 A1–A10 与 B11–B19**，使 Agent/人类只认 **保留 ADR + MIGRATION_MAP design**，且 **backfill 上限、沙箱路径、Tier 命名、legacy CLI、ADR-015 正文** 与成品一致；`uv run pytest -q` 全绿后 `task-02` Phase 1 方可开工。

---

## 与 task-02 的关系

```text
task-01.5（本票）ALL GREEN
        ↓
task-02 Slice 0-N → 1-E ∥ 1-P ∥ 2a-0 → …
```

| 本票产出                       | task-02 受益                                           |
| ------------------------------ | ------------------------------------------------------ |
| S4 正名 / 去 Tier harness 歧义 | Slice 0-N `phase1_acceptance` 重命名不踩旧名           |
| S3 统一 `source-route-db`      | 四命令验收根与矩阵一致                                 |
| S1 指针不断链                  | findings/ADR 引用可信任                                |
| S5 backfill 与 design 一致     | `weekly_backfill` / backfill child 不混两套尺子        |
| S6 删 legacy CLI               | PRD「不得再依赖 sandbox-clean-write」落地              |
| S7 写入热路径降 C901           | `WriteManager` / `SourceRegistry` 可维护；ADR-004 关账 |

---

## Architecture Decisions（本票 AD）

### AD-01 · 权威顺序（spec-driven-development）

```text
MIGRATION_MAP design  >  保留 ADR  >  specs/contracts 运行副本
```

改 `**/design/**` 须用户审阅；改运行副本用 `uv run python scripts/promote_design_runtime.py`（仅 design→runtime）。

### AD-02 · 边界校验（api-and-interface-design）

- **文档/指针：** S1 只改字符串，不改分支逻辑。
- **backfill：** 日期窗在 **CLI 边界** 校验；`plan_backfill_shards` 信任已解析的 `date_start`/`date_end`（交易日序列）。
- **legacy CLI：** **删除入口**优于长期 `LEGACY_COMMAND_RETIRED`（用户 B12）。

### AD-03 · 废弃策略（deprecation-and-migration）

- `m-data-03`：**强制迁移**至 `source-route-db`（Strangler 完成，删常量）。
- `sandbox-clean-write`：**删代码**（非 advisory 退役文案）。
- Tier harness 叙事：**删文档**，保留源分档表但 **rename**（B14）。

### AD-04 · B11 复杂度重构（用户决议修订 · 2026-07-09）

- **原 TEMP「后续决策」作废** — 用户明确要求 **本票做行为保持的结构简化**，非仅 ADR-004 文档关账。
- **权威：** `write_manager.md` 未规定圈复杂度上限；ADR-004「不修」是 **Round2 工程纪律**，现由 **提取 helper、降 C901** 取代（**零**对外行为变更）。
- **范围：** 仅 `WriteManager._execute_write`（C901=13）与 `SourceRegistry._validate_domain_roles`（C901=11）；**不**引入 design §3 全量 `MergePlanner`/`TransactionRunner` 类（ponytail）。
- **关账证据：** `ruff check --select=C901` 两符号通过 + 既有 pytest 全绿 + ADR-004 修订为「已拆分（提取）」+ D3-P1-2 registry 关账。

### AD-05 · B17 二十二源 SSOT（用户决议）

- **唯一枚举：** `docs/modules/design/data_sources.md` §5.9.1（22 源）。
- **ADR-009：** 保留 11 源 incremental 金路径表，文首加「⊂ 22 源矩阵」并链到 §5.9.1；**禁止**在多处维护互斥列表。

### AD-06 · B19 backfill（source-driven-development）

- **权威数字 SSOT：** `docs/ops/design/performance_limits.md` §8（L250：`5 trading days` / `20 trading days`）。
- **运行契约：** `specs/contracts/bounded_backfill_cap.yaml` 已与 §8 对齐（5/20 交易日 · `default_max_backfill_shards: 1`）。
- **接口：** CLI 边界 fail-closed；orchestrator/scheduler/baostock 金路径 `truncate_to_cap=True`（宽窗裁至 20 交易日）。

---

## Current Phase

### Phase 1 · **ALL GREEN** @ 2026-07-10 — S1–S7 ✅ · Phase F ✅

---

## Project Definition of Done（每切片通用）

每条切片除自身 AC 外，还须满足：

- [ ]不破坏 `ponytail`：在 **不破坏功能、不简化功能、不破坏流程/机制** 前提下，写 **最简**能工作的代码。

**禁止**：未请求需求的抽象、依赖、样板；测试堆无关 case。

**顺序**：YAGNI → 复用 → 标准库 → 平台能力 → 已有依赖 → 一行 → 最后才写最少代码。

\***\*永不偷懒的领域（各模式相同）：信任边界校验、防数据丢失的错误处理、安全、无障碍、用户明确要求的功能。\*\***

- [ ] 正式代码改动：**先 RED 后 GREEN**（`test-driven-development`）
- [ ] 新/改 `test_*`：**五字段 docstring**（覆盖范围、测试对象、目的、验证点、失败含义）
- [ ] `uv run pytest -q` exit 0
- [ ] 改 前 GitNexus ## 查码（GitNexus 优先）
  1. GitNexus：gitnexus系列skill/MCP或者其他gitnexus工具，若gitnexus滞后就刷新后使用
     查代码怎么工作→ gitnexus-exploring
     要改 symbol、怕踩调用方→ gitnexus-impact-analysis
     重命名 / 提取 / 拆分 / 搬模块？ ─→ gitnexus-refactoring
     GitNexus 索引过期 / 首次建图？ ──→ gitnexus-cli → 再跑对应 gitnexus-\* 工作流
     问 GitNexus 工具 / MCP 怎么用？ ─→ gitnexus-guide
     开发 GitNexus --pdg 污点/CFG？ ──→ gitnexus-taint-analysis / gitnexus-pdg-query
     出 bug / 行为异常？ → diagnosing-bugs / debugging-and-error-recovery+ gitnexus-debugging
  2. 仍不够 → `grep` / Read 深挖
     **完成条件**：接口与行为有据可查。
     **禁止**：未查就猜接口或行为。
- [ ] ## 逐功能闭环 **完成判定以实际代码为准**，不以文档为准。真实流程下须能运行、无偏离、无部分完成（必须是完全完成）、无漏洞/缺口；否则 **FAIL**。
  **完成条件（每功能/每批）**：
  - [ ] 真实流程可运行（非 mock 糊弄、非仅文档声称）
  - [ ] 与本批 AC 一致，无未声明缺口
  - [ ] 对应测试/验收已跑且通过
  - [ ] ## 禁止捷径（Execute / 修复 / 收尾）
    | 捷径                                                                  | 真做法                                                                                                     |
    | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
    | 绕过根因：包一层/吞异常/假数据/只修表象                               | 共享处一次 guard，根因一处修；有意简化须 `ponytail:` 在 **不破坏功能、不简化功能、不破坏流程/机制** 前提下 |
    | 假完成：改测试目的、缩验证、跳过 pytest、大量使用mock替代真实功能完成 | 保持目的/目标`uv run pytest -q` 全绿                                                                       |
    | 假分批：技术层碎片、本批不可验收                                      | Read **本批契约** + **逐功能闭环**，重定本批范围                                                           |
- [ ] 不通过改 `**/design/`\*\* 贴合 runtime 过 parity；漂移用 `promote_design_runtime.py`（AD-01）
- [ ] **AC-CLOSE-1 · 回读对齐**（见下节）
- [ ] **AC-CLOSE-2 · 计划外记账**（见下节）

---

## 每切片关账 AC（AC-CLOSE · **绑定全部切片 S1–S7 · Phase F**）

> **SSOT：** 下列两条为**每一切片** Acceptance criteria 的**强制尾部**（与切片专属 AC 并列，缺一不可）。

### 三文件分工（勿混）

| 文件                 | 记什么                                                              | 何时写                                             |
| -------------------- | ------------------------------------------------------------------- | -------------------------------------------------- |
| `**task_plan.md`\*\* | 切片范围 · 专属 AC · **计划内** AD（AD-01～06）· TEMP→切片映射      | 计划冻结 / 用户拍板（如 B11 重构）                 |
| `**findings.md`\*\*  | TEMP 项 disposition · 查码/GitNexus 结论 · **计划阶段**用户决议摘要 | 查证、计划修订；关账 → **已修复** / **按设计保留** |
| `**note.md`\*\*      | **执行过程中**计划与权威**均未写明**的发现 · 偏离 · **计划外决策**  | 仅切片实现中；勾 PASS 前写入或记 N/A               |

**规则：** TEMP/A/B 关账走 `findings.md` ledger；**不要**把应进 `docs/decisions/`** 或 `**/design/\*\*`的变更只写`note.md`（权威仍须用户审阅/ADR）。

### AC-CLOSE-1 · 回读对齐（权威 Parity 复检）

切片自称完成前：

1. **完整回读**本切片在 `task_plan.md` 中的：范围 · AC · Verification · 依赖 · 允许文件 · 绑定 TEMP 项（A*/B*）。
2. **完整回读**本切片 **权威清单**（各切片 AC 末尾列出）。
3. **对照** `TEMP-ADR-cleanup-vs-runtime-behavior-review.md` 对应行 — 用户解决方案是否落地。
4. 任一成立则 **不得勾 PASS**：计划写了没做/做一半；权威写了没做；做了但与计划/权威不一致。

**合法例外：** 一区 B1–B10 **按设计保留代码**（仅 S1 验证指针）；诚实 `BLOCKED` 非本票范围。

### AC-CLOSE-2 · 计划外记账（`note.md`）

执行中凡 **task_plan + MIGRATION_MAP 权威 + TEMP 用户决议** 均未写明、但实现中**暴露或决定**的事项 → 勾 PASS 前写入 `note.md`（模板见该文件）。

**无计划外** → 在 `progress.md` 该切片行写 `AC-CLOSE-2: N/A`，不必占 `note.md` 正文。

### 切片 AC 引用方式

各切片 Acceptance criteria **末尾**须含：

```markdown
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **本切片权威清单**；与计划/权威/TEMP 零缺口
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**
```

---

## Phases & Slices

### Phase 0 · 计划与查证 — Status: **complete**

- [x] Read TEMP + MIGRATION_MAP 触点
- [x] GitNexus impact：`plan_backfill_shards` · `resolve_live_tier` · `raise_retired_legacy_command` · `_execute_write` · `_validate_domain_roles`
- [x] 写入 `findings.md` disposition 表

- **Status:** complete

---

### Slice S1 · 指针与注释清扫（A1–A10 + 一区 B 文档验证）

**范围：** 仅字符串；**零**行为变更。

| 项       | 文件（允许）                                                                                                           |
| -------- | ---------------------------------------------------------------------------------------------------------------------- |
| A1/A2/A8 | `backend/app/cli/data_commands.py`                                                                                     |
| A3/A18   | `backend/app/cli/phase1_acceptance.py`                                                                                 |
| A4       | `specs/contracts/source_route_db_acceptance_contract.yaml`                                                             |
| A5/A9    | `docs/decisions/README.md`                                                                                             |
| A6       | `docs/ops/data_sync_quick_reference.md` · `openwiki/workflows/data-sync-and-live-gates.md` · `openwiki/agent-guide.md` |
| A7       | `product_live_gate.py` · `runners.py` · `baostock_incremental_run.py` 等注释                                           |
| A10      | `docs/RESOLVED_ISSUES_REGISTRY.md` · 测试 docstring（ADR-008→015）                                                     |

**AC：**

- [x] `rg "ADR-015-tier-a|ADR-008-product|ADR-006-sync|ADR-009-tier-a"` → `backend/`、`specs/`、`docs/decisions/` **零命中**
- [x] 一区 B1–B10：`product_live_gate` / `guard_production_*` / `resolve_matrix_data_root` 等 **无逻辑 diff**（`git diff` 仅文档与字符串）
- [x] `uv run pytest -q` exit 0
- [x] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · `TEMP` A1–A10 · `MIGRATION_MAP.md`（本切片触及 design 只读核对）· 一区 B1–B10 保留行为清单
- [x] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification：** `rg` + `uv run pytest -q`

**依赖：** 无 · **可与 S2 并行**

**Scope：** S · ~8 文件

---

### Slice S2 · ADR / 运维文档对齐（B15 · B16 · B17 · ADR-011 正文）

**范围：** `docs/decisions/` 保留 ADR + 触点；**不改** `**/design/`\*\*（B19 数字在 S5 动 design 时一起）。

| 项            | 动作                                                                                                  |
| ------------- | ----------------------------------------------------------------------------------------------------- |
| B15           | `ADR-015-live-acceptance-sandbox-dual-track.md` 删 `tier_a_live_acceptance.py`、删 m-data-03 作主路径 |
| B16           | 删/归档 M-DATA-03、MCR、R4_SANDBOX 当执行 SSOT 段落；指向 MIGRATION_MAP R4                            |
| B17           | `data_sources.md` §5.9.1 为 22 源 SSOT；`ADR-009` 加子集说明 + 单链                                   |
| B19（文档半） | `ADR-011` 补正文：backfill = 交易日 5/20；CI nightly 链到 `docs/ops/nightly_ci.md`                    |

**AC：**

- [x] ADR-015 文内无 `tier_a_live_acceptance`、无「m-data-03 为主验收路径」
- [x] ADR-011 非空，且与 `performance_limits.md` §8 叙述一致
- [x] B17：22 源枚举仅在 `data_sources.md` §5.9.1 完整列出
- [x] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-05 · `TEMP` B15–B17 · `docs/decisions/ADR-015` · `docs/decisions/ADR-011` · `docs/ops/design/performance_limits.md` §8（文档半）· `docs/modules/design/data_sources.md` §5.9.1（若改动须用户审阅记录于 `progress.md`）
- [x] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification：** 人工读 ADR-015/011 + `rg tier_a_live_acceptance docs/decisions`

**依赖：** 无 · **与 S1 并行**

**Scope：** M · 文档 only

**注意：** 改 `docs/decisions/`** 保留 ADR = 用户已审阅范围；**若**触及 `data_sources.md`（design）须 **用户确认\*\*（MIGRATION_MAP 索引）。

---

### Slice S3 · 沙箱路径统一（B13）

**范围：** 退役 `m-data-03`；测试/ fixture 仅用 `source-route-db`。

| 允许文件                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------- |
| `backend/app/ops/acceptance_isolation.py`（删 `M_DATA_03_SANDBOX_SEGMENT`）                                                     |
| `tests/conftest.py` · `tests/*_support.py` · `tests/acceptance_e2e_bootstrap.py`                                                |
| `tests/fred_macro_incremental_support.py` · `tests/macro_incremental_support.py` · `tests/alpha_vantage_incremental_support.py` |

**AC：**

- [x] `rg "m-data-03|M_DATA_03"` 仓库 **零命中**（除 `TEMP`/`task` 历史文档可选保留一句「已退役」）
- [x] `conftest` 隔离根使用 `SOURCE_ROUTE_DB_SANDBOX_SEGMENT`
- [x] `uv run pytest -q` exit 0
- [x] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-03 · `TEMP` B13 · `docs/decisions/ADR-015`（S2 已对齐）· `source_route_db_acceptance_matrix.py` `SOURCE_ROUTE_DB_SANDBOX_SEGMENT`
- [x] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification：** `rg` + pytest

**依赖：** S2 中 ADR-015 已改（避免文档与代码再打架）

**GitNexus：** 改 `assert_isolated_live_data_root` 前 `impact()`

**Scope：** M · ~15 文件

---

### Slice S4 · Tier 命名去 harness 歧义（B14 · B18）

**范围：** GitNexus `rename`；**不**改 A/B/C 集合成员。

| 变更（计划）                                                                                                  |
| ------------------------------------------------------------------------------------------------------------- |
| `live_tier_router.py` → `live_prod_source_tiers.py`                                                           |
| `resolve_live_tier` → `resolve_prod_source_tier`                                                              |
| `TIER_A_SOURCES` → `INCREMENTAL_GOLD_PATH_SOURCE_IDS`                                                         |
| `tier_a_fetch_operation` → `domain_fetch_operation`（`phase1_acceptance.py`）                                 |
| `acceptance_request_for_tier_a` → `acceptance_request_for_domain`（**同文件** — 与上配套，避免 harness 残留） |
| 测试文件 `test_tierA_*` 改名或 docstring 去 harness 暗示                                                      |

**AC：**

- [x] `rg "tier_a_live_acceptance|test_tierA"` 代码 **零命中**
- [x] `incremental_source_registry` 与 rename 后常量仍 11 源对齐
- [x] GitNexus `impact(resolve_prod_source_tier)` 已跑并记入 `progress.md`
- [x] `uv run pytest -q` exit 0
- [x] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-03 · `TEMP` B14/B18 · `docs/decisions/ADR-009`（11 源金路径）· rename 后模块与 `incremental_source_registry` 对齐
- [x] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification：** pytest + `rg`

**依赖：** S1（A7 注释）· **建议 S3 后**（减少 conftest 冲突）

**Scope：** L · 用 `rename` 一批提交

---

### Slice S5 · backfill 交易日上限（B19）— **HIGH 风险**

**范围：** 代码 + 契约；**可能**触 design 审阅。

| 允许文件                                                                                                             |
| -------------------------------------------------------------------------------------------------------------------- |
| `backend/app/sync/jobs.py` · `plan_backfill_shards` · `load_bounded_backfill_cap`                                    |
| `backend/app/cli/data_commands.py` · `backfill_plan` / `full_load_plan`                                              |
| `backend/app/sync/runners.py` · `backend/app/ops/baostock_incremental_run.py`（间接调用 — 须同批迁移）               |
| `specs/contracts/bounded_backfill_cap.yaml`（**无** promote 镜像 — 对齐 `performance_limits.md` 后直改）             |
| `docs/ops/design/performance_limits.md` §8（**若**改数字 — 须用户审阅 design）                                       |
| `tests/test_qmd_data_backfill_cli.py` · `tests/test_bounded_backfill_cli_e2e.py` · `tests/test_sync_jobs.py`（若有） |

**查码注记（source-driven-development）：**

- **权威：** `docs/ops/design/performance_limits.md` L250 — 默认 **5**、最大 **20** **trading days**。
- **现行 YAML：** `eco_max_backfill_days_per_task: 31`（自然日）— 与 design **分歧**。
- **YAML `closure_command`** 指向 `tests/test_bounded_backfill_cap.py` — **文件不存在**；S5 须改指向现有测或补最小 cap 测。

**实现要点（TDD）：**

1. **RED：** 测 `plan_backfill_shards` — 窗 30 **自然日**但仅 20 **交易日**应 PASS；超 20 交易日 FAIL/`truncate`。
2. **GREEN：** 引入 `window_kind=trading_sessions`；CN 域用 `cn_trading_calendar`，US 域用 `us_trading_calendar`（ADR-007）。
3. **YAML：** `default_max_trading_days: 5` · `absolute_max_trading_days: 20`；弃用或映射旧 `31/3/12` 字段（**破坏性** — 测试全改）。

**AC：**

- [x] CLI backfill 默认窗 ≤ **5 交易日**；硬顶 **20 交易日**（与 `performance_limits.md` §8 一致）
- [x] `bounded_backfill_cap.yaml` 与 `performance_limits.md` §8 一致（**非** `test_design_runtime_parity` 路径 — 该 YAML 不在 `FILE_PAIRS`）
- [x] `bounded_backfill_cap.yaml` 的 `closure_command` 指向**存在**的 pytest 且 exit 0
- [x] `docs_anchor` 指向 ADR-011（已补正文）
- [x] `uv run pytest -q` exit 0
- [x] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-06 · `TEMP` B19 · `docs/ops/design/performance_limits.md` §8 · `docs/decisions/ADR-011` · `specs/contracts/bounded_backfill_cap.yaml` · 间接调用方 `runners.py` / `baostock_incremental_run.py`
- [x] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification：** 针对性 pytest + 全量 `uv run pytest -q`

**依赖：** S2（ADR-011 正文）· **须在 S4 后或并行不同 worktree**

**GitNexus：** `impact(plan_backfill_shards)` — **HIGH**，已记入 findings

**Scope：** L · 核心行为变更

---

### Slice S6 · 删除 legacy sandbox-clean-write（B12）

**范围：** 删退役桩；契约与测试改为「无此命令」。

| 允许文件                                                                                                                      |
| ----------------------------------------------------------------------------------------------------------------------------- |
| `backend/app/cli/phase1_acceptance.py`（删 `RETIRED_LEGACY_COMMANDS` / `raise_retired_legacy_command` 若无处调用）            |
| `backend/app/ops/sandbox_clean_write/limited_production_entry.py`（删 `run_limited_production_entry` 或整文件 — 须 `impact`） |
| `backend/app/cli/main.py`（若有子命令注册）                                                                                   |
| `specs/contracts/data_cli_contract.yaml`                                                                                      |
| `tests/test_data_cli_contract.py`                                                                                             |
| `scripts/check_acceptance_helper_consumers.py`                                                                                |
| `docs/ops/staging_data_e2e_runbook.md`（删 CLI 行）                                                                           |

**AC：**

- [x] `qmd-data` / `qmd data` **无** `sandbox-clean-write` 子命令
- [x] `rg "sandbox-clean-write|raise_retired_legacy_command"` **零命中**（task 文档除外）
- [x] `data_cli_contract.yaml` 不再要求 `LEGACY_COMMAND_RETIRED` 测退役命令
- [x] `uv run pytest -q` exit 0
- [x] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-02/AD-03 · `TEMP` B12 · `specs/contracts/data_cli_contract.yaml` · `docs/decisions/ADR-015`（替代路径叙事）
- [x] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification：** CLI `--help` + pytest

**依赖：** S1 完成后更易（契约一致）

**注意：** `limited_production_entry` 其他函数若仍被 rehearsal 使用 — **只删 CLI 入口**，勿误删 `rehearsal_runner` 路径（先 `impact`）。

**Scope：** M

---

### Slice S7 · 写入热路径复杂度重构（B11）

**用户决议：** 重构（非「暂不拆」）。**原则：** code-simplification 五则 — **行为完全保持**，测试不改断言语义，每步可 `pytest -q`。

#### S7 · 深度分析摘要（查码 + GitNexus · 2026-07-09）

| 维度                      | `_execute_write`                                                                                                              | `_validate_domain_roles`                                                                       |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **文件**                  | `backend/app/db/write_manager.py` L322–424                                                                                    | `backend/app/datasources/source_registry.py` L398–438                                          |
| **C901**                  | **13**（阈值 10）                                                                                                             | **11**                                                                                         |
| **GitNexus upstream**     | **LOW** — 直接 caller 仅 `write`；间接 `layer2 write_staging`、`sandbox_clean_write`（S6 可能删部分间接路径）                 | **CRITICAL** — 59 节点 / 19 processes；**但**仅 `load()` 在构造时调用，**无**稳定公开 API 变更 |
| **设计图**                | `write_manager.md` §3 理想组件含 MergePlanner/TransactionRunner — 现行单体；本票 **ponytail 提取** 对齐命名，**不**新建类模块 | `data_sources.md` 域角色约束 — 错误文案须 **逐字保持**（`InvalidRegistryError` match 测试）    |
| **债务类型**              | 架构债（编排+合并+三路上下文异常缠在一处）                                                                                    | 代码债（primary/validation 校验 **镜像重复**）                                                 |
| **Priority（tech-debt）** | Impact 4 · Risk 3 · Effort 2 → **(4+3)×4=28**                                                                                 | 同左                                                                                           |

**复杂度根因（Chesterton's Fence 后）：**

1. `**_execute_write`** — 单函数承担：staging 行数守卫、`own_transaction` BEGIN/COMMIT/ROLLBACK、`ValidationGate`、upsert 预检、merge SQL 循环、成功审计、**三条**异常路径（`ValidationRejected`/`ValidationGateError` vs `duckdb.Error` vs 重抛），且 `own_transaction=False` 时 duckdb 路径 **不\*\*走 `_commit_audit_after_rollback`（GPT P1 契约）。
2. `**_validate_domain_roles`** — primary 与 validation 各 4 条守卫；差异仅「primary 在 `domain_enabled_by_default` 时才查 disabled」— 缺共享 **role binding\*\* helper，圈复杂度叠满。

**五轴评审（code-review-and-quality）：**

| 轴           | 结论                                                                                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Correctness  | 测试已锁：append/upsert、gate 拒绝、rollback 审计、`own_transaction=False` sidecar（`test_write_manager*.py`）；registry 坏 YAML fixture（`test_source_registry.py`） |
| Readability  | 提取后读者按「编排 → 合并 → 失败策略」三层读，概念数 **减少**（非搬迁）                                                                                               |
| Architecture | 向 `write_manager.md` §3 语义靠拢的 **私有** helper；**不**改 `WriteRequest`/`write()` 公共接口                                                                       |
| Security     | 无新信任边界；错误仍 `redact_error_message`                                                                                                                           |
| Performance  | 无热路径额外分配；仍单次事务                                                                                                                                          |

**废弃/迁移（deprecation-and-migration）：** 无 API 废弃；ADR-004「不修」决策 **废止** →「已用提取式简化关账」。

---

#### S7 子切片与推荐 commit 顺序（request-refactor-plan）

**允许文件：**

| 子切片 | 文件                                                                                                                                                              |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S7-1   | `backend/app/datasources/source_registry.py`                                                                                                                      |
| S7-2   | `backend/app/db/write_manager.py`                                                                                                                                 |
| S7-3   | `docs/decisions/ADR-004-write-path-complexity-ceiling.md` · `docs/AUDIT_DEFERRED_REGISTRY.md` · `docs/quality/待修复清单.md` · `docs/RESOLVED_ISSUES_REGISTRY.md` |

**S7-1 · SourceRegistry（先做 — 爆炸半径可控）**

| #   | Commit（每步后 `uv run pytest tests/test_source_registry.py -q`）                                                                                    |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 新增模块级 `_validate_bound_source(sources, data_domain, role_label, source_id, *, require_enabled)` — **复制**现有四条守卫与 **相同** f-string 文案 |
| 2   | `_validate_domain_roles`：primary 块改调 helper（`require_enabled=binding.domain_enabled_by_default`）                                               |
| 3   | validation 块改调 helper（`require_enabled=True`）；删重复分支                                                                                       |
| 4   | `uv run ruff check backend/app/datasources/source_registry.py --select=C901` → **0 错误**                                                            |

**S7-1 关账 AC：**

- [ ] **AC-CLOSE-1**：回读 S7-1 + `docs/modules/design/data_sources.md` 域角色 · `test_source_registry.py` match 语义
- [ ] **AC-CLOSE-2**：`note.md` 或 N/A（记入 `progress.md`）

**S7-2 · WriteManager（GitNexus `impact(_execute_write)` 已 LOW；改前再跑）**

| #   | Commit（每步后 `uv run pytest tests/test_write_manager.py tests/test_write_manager_degraded_audit.py -q`）                                                                                                                        |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 提取 `_resolve_audit_sidecar_root(own_transaction, audit_sidecar_root)` — sidecar 默认 `DATA_ROOT` 逻辑                                                                                                                           |
| 2   | 提取 `_apply_staging_to_clean(con, req, target, staging, primary_keys, columns) -> tuple[int,int]` — gate 后至 merge 完成，返回 `(rows_inserted, rows_updated)`                                                                   |
| 3   | 提取 `_fail_write_after_error(con, write_id, req, started_at, rows_in_staging, exc, *, own_transaction, audit_sidecar_root) -> WriteResult` — **集中**三条 except 的分流（保持 duckdb+`own_transaction=False` 不 spawn 审计连接） |
| 4   | `_execute_write` 瘦身为编排：校验 staging 行数 → BEGIN → try 成功路径 → except 委托 `_fail_write_after_error`                                                                                                                     |
| 5   | `uv run ruff check backend/app/db/write_manager.py --select=C901` → **0 错误**                                                                                                                                                    |

**S7-2 关账 AC：**

- [ ] **AC-CLOSE-1**：回读 S7-2 + `docs/modules/design/write_manager.md` §写入契约 · `test_write_manager*.py` · `own_transaction=False` 契约
- [ ] **AC-CLOSE-2**：`note.md` 或 N/A（记入 `progress.md`）

**S7-3 · ADR 与 registry 关账**

| #   | Commit                                                                                                                                                                                                                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | 修订 ADR-004：状态改为「已修订」；记录 S7 提取式简化；删除「第四种写入域才拆」作为 **唯一** 触发条件（改为「新增 write_mode 或第四类 merge 策略时再评 MergePlanner 模块」）                                                                |
| 2   | `AUDIT_DEFERRED_REGISTRY` / `待修复清单` D3-P1-2 → 已关账；`RESOLVED_ISSUES_REGISTRY` 证据：`ruff --select=C901` + `tests/test_write_manager.py` + `tests/test_source_registry.py`（**勿**引用已删的 `test_batch6_wave4_prep_closure.py`） |
| 3   | 全量 `uv run pytest -q`                                                                                                                                                                                                                    |

**S7-3 关账 AC：**

- [ ] **AC-CLOSE-1**：回读 S7-3 + `docs/decisions/ADR-004` · D3-P1-2 registry 行与证据路径一致
- [ ] **AC-CLOSE-2**：`note.md` 或 N/A（记入 `progress.md`）

**测试决策（Testing Decisions）：**

- **不**为 helper 单测（测实现细节）；**只**跑现有行为测试 — 与 ADR-004 原「测试锁行为」一致。
- 失败含义不变：任一步改错 match 串 → `test_source_registry` 或 `test_write_ownTransactionFalse`\_\* 红。
- 关账加跑：`uv run ruff check backend/app/db/write_manager.py backend/app/datasources/source_registry.py --select=C901`。

**Out of Scope（B11）：**

- 新建 `merge_planner.py` / `transaction_runner.py` 模块或类
- 修改 `WriteRequest` 字段、`write()` 签名、`SourceRegistry` 公开方法
- 改 merge SQL 语义或 `write_mode` 路由
- 为降 C901 而 **删** 错误分支或合并异常类型
- S6 之前的 `sandbox_clean_write` 间接 caller — S7 **不依赖** S6，但若 S6 先删 rehearsal 路径，S7-2 仍须绿全量 pytest

**AC：**

- [x] `ruff --select=C901` 对 `_execute_write`、`_validate_domain_roles` **0 命中**
- [x] `git diff` 无 `WriteRequest` / 公开方法签名变更
- [x] 错误消息字符串与重构前 **一致**（registry match 测试不改编）
- [x] ADR-004 反映「已重构」非「不修」
- [x] findings B11 → **已修复**
- [x] `uv run pytest -q` exit 0
- [x] **AC-CLOSE-1 · 回读对齐**：回读本切片 S7 全文 + S7-1/2/3 子 AC + **权威清单**：`task_plan.md` AD-04 · `TEMP` B11 · `docs/modules/design/write_manager.md` · `docs/decisions/ADR-004` · `findings.md` B11
- [x] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加 S7 条目（含子切片汇总），或 **N/A — 本切片无计划外**

**S7+ 可观测性收尾（2026-07-09 · 计划外 · 已绿）：**

| 项   | 产出                                                     |
| ---- | -------------------------------------------------------- |
| P2   | `run_context.py` · `SyncJobSpec.requested_by` → 写入审计 |
| P3   | `write_telemetry.py` · stderr JSON 事件                  |
| 安全 | `security-scan-s7/` 静态体检 0 findings                  |
| 补测 | `require_enabled` registry 行为测                        |

**Scope：** S · 不阻塞 S3–S6；**不**替代 Phase F。

**Verification：** 上表 commit 链 + C901 + 全量 pytest

**依赖：** S1∥S2 完成后即可开工（与 S3–S6 **无**文件重叠）；**建议**在 S5 之前完成，避免与 `data_commands` 大改并行。

**GitNexus：** S7-1 前 `impact(_validate_domain_roles)`（已知 CRITICAL — 仅内部提取）；S7-2 前 `impact(_execute_write)`（LOW）

**Scope：** M（~120–180 行净移动，3 子切片）

---

### Phase F · 关账（无遗留）

**AC（本票 DoD）：**

- [x] TEMP 表 A1–A10、B11–B19 在 `findings.md` 均为 **已修复**（一区 B1–B10 为 **按设计保留** + S1 验证）
- [x] `uv run pytest -q` exit 0
- [x] `task-02-layer1-full/progress.md` 增加一行：「task-01.5 已绿，可开工 Slice 0-N」
- [x] 可选：删或移 `TEMP-ADR-cleanup-vs-runtime-behavior-review.md` 至 `task/audit/`（用户确认后）→ **已归档** @ `task/audit/TEMP-ADR-cleanup-vs-runtime-behavior-review.md`（原路径重定向）
- [x] **AC-CLOSE-1 · 回读对齐**：**全票**回读 — `task_plan.md` 全文 · `TEMP` A1–A10/B11–B19 · `findings.md` disposition 全 **已修复**（一区 B 为 **按设计保留**）· `MIGRATION_MAP.md` 本票触及权威
- [x] **AC-CLOSE-2 · 计划外记账**：全票 `note.md` 闭合，或各切片 **N/A** 已在 `progress.md` 索引

---

## 推荐执行顺序（单 worktree 串行）

```text
S1 ∥ S2  →  S7（S7-1→S7-2→S7-3）  →  S3  →  S4  →  S5  →  S6  →  Phase F
```

| 并行？ | 切片             | 原因                                                                                               |
| ------ | ---------------- | -------------------------------------------------------------------------------------------------- |
| 可并行 | S1 ∥ S2          | 无文件重叠                                                                                         |
| 可并行 | S7 ∥ 无          | S7 独占 `write_manager`/`source_registry`；与 S1/S2 **可**不同 agent，但勿与 S5 抢 `data_commands` |
| 勿并行 | S4 ∥ S5          | 均可能改 `data_commands.py`                                                                        |
| 勿并行 | S4 ∥ task-02 0-N | 同改 `phase1_acceptance.py`                                                                        |

**多 agent：** S1+S2 可一人；S3 一人；S4 一人；**S5 独占** `jobs.py`/`data_commands.py`/`runners.py`。

---

## Checkpoints（planning-and-task-breakdown）

| 检查点   | 时机           | 必过项                                                                                                                          |
| -------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **CP-0** | S1 ∥ S2 完成后 | `uv run pytest -q`；S2 若动 `data_sources.md` design → **用户已审阅**并记入 `progress.md`；**AC-CLOSE-1/2** — **✅ 2026-07-09** |
| **CP-1** | S7 完成后      | C901 零命中 + `test_write_manager*` + `test_source_registry` 绿；**AC-CLOSE-1/2** — **✅ 2026-07-09**（含 S7+ P2/P3）           |
| **CP-2** | S3 + S4 完成后 | `phase-scripts/check_task015_s3_s4_rg_compliance.py --strict` · 全量 pytest；**AC-CLOSE-1/2** — **✅ 2026-07-10**               |
| **CP-3** | S5 完成后      | backfill 5/20 交易日 · orchestrator 硬顶 · closure 可跑；**AC-CLOSE-1/2** — **✅ 2026-07-10**                                   |
| **CP-4** | Phase F        | findings 全 **已修复**；`task-02` progress 解锁行；**全票 AC-CLOSE-2** 闭合 — **✅ 2026-07-10**                                 |

---

## Risks

| 风险                               | 影响                                      | 缓解                                                                                              |
| ---------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------- |
| S5 改变 backfill 默认窗            | baostock live backfill 测试需改日期       | 先 RED 测再改；复用 `progress.md` 本机证据                                                        |
| S6 误删 rehearsal 路径             | 彩排失败                                  | `impact(limited_production_entry)`；只删 CLI promote 入口                                         |
| S4 rename 漏引用                   | import 失败                               | GitNexus `rename` + pytest                                                                        |
| design 审阅阻塞 S5                 | 无法 promote YAML                         | 先仅改代码读 `performance_limits` 常量；YAML promote 跟用户批 design                              |
| **S7** 异常路径合并时改语义        | `own_transaction=False` 审计/sidecar 回归 | 逐步 commit；必跑 `test_write_ownTransactionFalse_*`；duckdb 分支 **禁止** 合并进 validation 分支 |
| **S7** registry helper 改 match 串 | `test_source_registry` 成片红             | 提取时 **复制粘贴** 原 f-string，不「润色」文案                                                   |

---

## Open Questions

见 `findings.md` §7。默认按表内「默认」列执行；推翻须用户一句确认。

---

## Errors Encountered

| Error    | Attempt | Resolution |
| -------- | ------- | ---------- |
| （尚无） | —       | —          |

---

## 技能映射（本计划已加载）

| Skill                         | 用于                                                           |
| ----------------------------- | -------------------------------------------------------------- |
| planning-with-files           | 本三文件骨架                                                   |
| planning-and-task-breakdown   | 切片 AC / 顺序 / 关账                                          |
| spec-driven-development       | AD-01 权威顺序、先 spec 后实现                                 |
| api-and-interface-design      | AD-02 边界、错误语义、Hyrum                                    |
| source-driven-development     | AD-06 backfill 对齐 design                                     |
| deprecation-and-migration     | AD-03 退役策略                                                 |
| architecture                  | AD 记录格式                                                    |
| request-refactor-plan         | **S7** commit 链 · S4/S5/S6 小步顺序                           |
| code-simplification           | **S7** 行为保持提取                                            |
| code-review-and-quality       | **S7** 五轴评审（见 S7 分析表）                                |
| tech-debt                     | **S7** D3-P1-2 优先级打分                                      |
| improve-codebase-architecture | S7 向 write_manager §3 语义靠拢（私有 helper）；S4 rename 接缝 |
| deprecation-and-migration     | S7 废止 ADR-004「不修」、无 API 废弃                           |

---

## Project DoD（本票）

- [x] 全部切片 AC 绿（含 **AC-CLOSE-1/2**）
- [x] `findings.md` ledger 无「待修复」（§9.2 **已迁移至 task-02** / 按设计保留 除外）
- [x] `uv run pytest -q` exit 0
- [x] **不**修改 `**/design/`\*\* 除非 S2/S5 经用户审阅（记录于 `progress.md`）
- [x] `note.md` 与 `progress.md` N/A 索引闭合（Phase F）

---

## 文档索引

| 文件                                             | 用途                                            |
| ------------------------------------------------ | ----------------------------------------------- |
| `task_plan.md`                                   | 执行计划 · §每切片关账 AC                       |
| `findings.md`                                    | TEMP disposition · 查码/GitNexus · 计划阶段决议 |
| `progress.md`                                    | 切片进度 · AC-CLOSE-2 N/A 索引                  |
| `note.md`                                        | **计划外**执行期决策（AC-CLOSE-2）              |
| `TEMP-ADR-cleanup-vs-runtime-behavior-review.md` | 输入 SSOT（**已归档** → `task/audit/`）         |
