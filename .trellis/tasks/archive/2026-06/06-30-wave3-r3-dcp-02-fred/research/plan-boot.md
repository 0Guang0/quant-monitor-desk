# Plan Boot — R3-DCP-02 fred macro incremental

> **任务目录：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **分支：** `feature/wave3-r3-dcp-02-fred`  
> **协议：** debt-lite Phase 8D · Plan 增强 §1.1（调研先行）  
> **日期：** 2026-06-30

---

## 1. 上下文复述（自己的话）

### 做什么

让 FRED 宏观序列（P0 whitelist：`DGS10` 等）走**产品增量路径**：从隔离库 `axis_observation`（macro clean 域）读出每个 series 的最新观测日（`max(DATE(publish_timestamp))` per `indicator_id`），只向 FRED API 拉新增点，经 `DataSourceService` + `DataSyncOrchestrator.run_incremental` + `IncrementalJobRunner` 写入 clean 表；`qmd data sync --domain macro_series --source-id fred` 可重复跑且幂等。

### 价值

- 与轨 A（baostock）并列的 Wave 3 试点，验证**宏观序列 watermark** 语义（per `indicator_id` + `DATE(publish_timestamp)`，非 equity `trade_date`）
- 承接 R3H-08C 已闭合的 fred live port，从「能拉」升级到「能增量产品跑」
- 为 Wave 4 宏观六源扩展提供可复制 tracer bullet

### 约束

| 约束      | 要求                                                                                                                                                                  |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 金路径    | `DataSourceService.fetch` → `fred_port` → `run_incremental`（禁止 adapter bypass / rehearsal pilot 替身）                                                             |
| 授权      | `FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH`；缺 key → `USER_AUTH_REQUIRED` 负例                                                                                           |
| 数据根    | `QMD_DATA_ROOT` 隔离库；禁止 silent 写 canonical `data/duckdb/`                                                                                                       |
| Watermark | **按 series_id（= clean 表 `indicator_id`）** 绑定；读 `max(DATE(publish_timestamp))` per series（= evidence `observation_date`）；**不**盲目抄 baostock `trade_date` |
| Clean PK  | `axis_observation.observation_id` + `upsert_by_pk`（`clean_write_targets.py`）                                                                                        |
| 共享 sync | `backend/app/sync/watermark*.py` 若由轨 A 创建 → **本轨只读消费**；不得与轨 A 同时改同一文件                                                                          |
| Registry  | 仅 touch `fred` 相关行；合并由主会话排队                                                                                                                              |
| Schema    | R3H-06 已封板；**无新 migration**                                                                                                                                     |

### 相关设计（上游 SSOT）

```text
活卡 R3_DCP_02_FRED_INCREMENTAL.md
INDEX R3_DCP_TO_ISSUES_INDEX.md §2
docs/modules/data_sync_orchestrator.md §13.4.2 IncrementalUpdateJob
clean_write_targets.py → macro_series → axis_observation / stg_axis_observation_smoke
source_capabilities.yaml fred.macro_series（observation_date, series_id）
fred_port.py（R3H-01 L2；live gate ADR-027）
R3H-08 reference-adoption-r3h08.md（金路径先例）
R3G-03 limited_production_entry（macro promote 链；隔离写守卫）
```

### 成功标准（活卡 §5 AC）

- [ ] fred watermark 单测：空表 / 有观测 / 多 series
- [ ] replay + env-gated live smoke（隔离库）
- [ ] 幂等：重复跑不增行
- [ ] `research/reference-adoption-dcp02.md` L1/L2/L3
- [ ] Audit A1–A8 + Repair ledger 关账
- [ ] `uv run pytest -q` exit 0

### 完成条件

活卡 §5 全勾 + P6 Repair 关账；可独立于 DCP-01 宣告 CLOSED（DCP-03 仅需 01/02 其一 PASS）。

---

## 2. 必读清单（阶段 0）

| #   | 文档 / 路径                                                              | 状态 |
| --- | ------------------------------------------------------------------------ | ---- |
| 1   | `agent-toolchain.md`                                                     | [x]  |
| 2   | `complex-task-planning-protocol.md` Phase 8D                             | [x]  |
| 3   | `R3_DCP_TO_ISSUES_INDEX.md` + 活卡 + `BRANCH-DCP-02.md`                  | [x]  |
| 4   | `docs/generated/project_map.generated.md` → `data_sync_orchestrator.md`  | [x]  |
| 5   | `fred_port.py` · `orchestrator.py` · `runners.py` IncrementalJobRunner   | [x]  |
| 6   | `clean_write_targets.py` · `sandbox_clean_write_contract.yaml` fred caps | [x]  |
| 7   | R3H-08 归档 `reference-adoption-r3h08.md`                                | [x]  |
| 8   | R3G-03 `EXECUTION_INDEX.md`（隔离 promote 先例）                         | [x]  |
| 9   | `BATCH_3H_COORDINATOR_PLAYBOOK.md` §5 Wave 3 debt-lite                   | [x]  |
| 10  | GitNexus `query` fred/macro/incremental（7.pre 级）                      | [x]  |

---

## 3. 与轨 A（DCP-01）边界

| 项             | 轨 A 拥有                        | 轨 B（本轨）                                                                       |
| -------------- | -------------------------------- | ---------------------------------------------------------------------------------- |
| watermark 模块 | `sync/watermark*.py`（若新建）   | 只读消费或 `ops/fred_*` 局部 reader                                                |
| port           | `baostock_port`                  | `fred_port`                                                                        |
| clean 域       | `security_bar_1d` / CN bar       | `axis_observation` / macro                                                         |
| watermark 语义 | `max(trade_date)` per instrument | `max(DATE(publish_timestamp))` per `indicator_id`（= evidence `observation_date`） |

---

## 4. GitNexus 调研摘要

`query("fred macro incremental watermark observation_date axis_observation")` 命中：

- `Layer1ObservationIngestionService` / `commit_clean_observation_and_snapshots` — clean 写链
- `rehearsal_loader.populate_macro_from_bundle` — fred evidence → staging 映射
- `fred_port.fetch_payload` — 产品 fetch 入口
- **未命中** 专用 incremental watermark 模块（绿场切片，符合预期）

---

## 5. 计划产物索引

| 文件                                   | 用途              |
| -------------------------------------- | ----------------- |
| `research/reference-adoption-dcp02.md` | L1/L2/L3 调研     |
| `research/architecture-dcp02.md`       | 落地架构（可选）  |
| `DEBT.plan.md`                         | Phase 8D 垂直切片 |
| `AUDIT.plan.md`                        | A1–A8 范围        |
| `research/grill-me-session.md`         | 澄清记录          |
| `prd.md`                               | 活卡 AC 摘要      |

**未产出（debt-lite）：** `EXECUTION_INDEX.md` / `frozen/*.md` / `plan.freeze.md` — 主会话未升格 complex。

---

## 6. debt-lite Plan 自检（对抗审计前）

| 检查项                                                           | 状态 |
| ---------------------------------------------------------------- | ---- |
| `research/reference-adoption-dcp02.md` L1/L2/L3 非空且有证据路径 | [x]  |
| `research/plan-boot.md` 六项上下文复述齐全                       | [x]  |
| `DEBT.plan.md` allowed/forbidden/AC/验证/证据列完整              | [x]  |
| `AUDIT.plan.md` A1–A8 明确（A6 SKIP 有理由）                     | [x]  |
| 调研先于 Plan（引用链非空泛）                                    | [x]  |
| 共享 sync 归属与 `00-MAIN-SESSION-COORDINATOR.md` §4 一致        | [x]  |
| fred watermark per-series 语义 vs 轨 A `trade_date` 已区分       | [x]  |
| 禁止 baostock 触及已写入 forbidden                               | [x]  |
| `research/grill-me-session.md` 无未决                            | [x]  |
