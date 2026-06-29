# Plan Boot — R3-DCP-01 baostock incremental watermark

> **轨道：** Wave 3a · 并行轨 A · debt-lite Phase 8D  
> **日期：** 2026-06-30 · Plan Agent `composer-2.5`

---

## 六项上下文复述（用自己的话）

### 1. 做什么

让中国 A 股日频 bar（baostock）走**产品路径**：从隔离库 clean 表读出已有数据的最后一天（watermark），只拉「那天之后」的新 bar，经金路径写回 `security_bar_1d`；`qmd data sync` 可 dry-run 审计、可真跑，重复执行行数不膨胀。

### 2. 价值

- Round 4 日常增量的**第一个试点源**（与 fred 并列），验证「读库水位 → incremental → clean upsert」可复制到 Tier A 扩展。
- 不依赖 `--live-wire` / staged pilot 运维脚本；巩固 R3H-10 `DataSourceService` 金路径在真实 CN bar 域上的端到端闭环。

### 3. 约束

| 约束 | 要求 |
|------|------|
| 金路径 | `DataSourceService.fetch` + `DataSyncOrchestrator.run_incremental`；生产禁止 `adapter=` bypass |
| 数据根 | 默认 `QMD_DATA_ROOT` 隔离库；**禁止** silent 写 canonical `data/duckdb/` |
| Schema | R3H-06 `security_bar_1d` + `upsert_by_pk`；**无新 migration** |
| Registry | 仅 touch `baostock` 相关行；合并由主会话排队 |
| 并行 | 轨 A 拥有 `watermark*.py` + baostock 切片；**禁止**改 `fred_port` / 轨 B 文件 |
| 参考项目 | Plan 须 L1/L2/L3（见 `reference-adoption-dcp01.md`） |

### 4. 相关设计

```text
qmd data sync --data-domain cn_equity_daily_bar …
  → watermark: SELECT max(trade_date) FROM security_bar_1d [+ instrument filter]
  → date_start = max + 1 day；date_end = today（UTC calendar；ponytail 暂不用 CN 交易日历）
  → SyncJobSpec(incremental, date_start, date_end)
  → DataSourceService.fetch(baostock)  [FetchRequest.start_time/end_time]
  → IncrementalJobRunner → validate → upsert security_bar_1d
```

**已有资产（调研结论）：**

- `IncrementalJobRunner` + `run_incremental` 已绿（Batch D / R3H-10）；幂等先例见 `test_incrementalJob_repeatRun_noDuplicatePrimaryKey`。
- `resolve_clean_write_target("cn_equity_daily_bar")` → `security_bar_1d` / `upsert_by_pk`（R3H-06 SSOT）。
- `baostock_port.py` 已 L2 迁自 staged pilot；replay-first；已校验 `start_time`/`end_time` 窗宽。
- **缺口：** 无 `sync/watermark*.py`；`IncrementalJobRunner` 建 `FetchRequest` 时**未**从 `spec.date_start/date_end` 注入 `start_time/end_time`；`data_commands.sync_plan` 仅 dry-run。

### 5. 成功标准（AC）

活卡 §5 + INDEX §1：

- [ ] watermark 单测：空表 / 有数据 / 边界日
- [ ] baostock 增量经 `datasource_service` + orchestrator 端到端（replay 或 env-gated live）
- [ ] 重复跑任务行数不增（upsert 幂等）
- [ ] CLI help + dry-run 可审计；真跑路径有契约或 smoke
- [ ] `research/reference-adoption-dcp01.md` L1/L2/L3 齐
- [ ] Audit A1–A8 + Repair ledger 关账
- [ ] `uv run pytest -q` exit 0

### 6. 完成条件

- 活卡 §5 全勾 + P6 Repair 无待修复 + 主会话 merge 轨 A。
- `R3H_PASS_EXECUTION_PLAN.md` Wave 3 行可标 **DCP-01 CLOSED**。
- Plan 闸门：本目录 `DEBT.plan.md` + `AUDIT.plan.md` + 调研产物齐 → 主会话放行 Execute（`task.py start` 由 Execute agent 执行，Plan **不** start）。

---

## 必读清单（阶段 0）

| # | 文件 | 状态 |
|---|------|------|
| 1 | `agent-toolchain.md` | ✅ |
| 2 | `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D | ✅ |
| 3 | `R3_DCP_TO_ISSUES_INDEX.md` §1 + 活卡 `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` | ✅ |
| 4 | `_tmp-wave3-dcp-parallel/BRANCH-DCP-01.md` | ✅ |
| 5 | `docs/modules/data_sync_orchestrator.md` §13.4.2 | ✅ |
| 6 | `docs/generated/project_map.generated.md` → sync / datasources 簇 | ✅ |
| 7 | `backend/app/sync/orchestrator.py` · `runners.py` | ✅ |
| 8 | `backend/app/datasources/fetch_ports/baostock_port.py` | ✅ |
| 9 | `backend/app/ops/sandbox_clean_write/clean_write_targets.py` | ✅ |
| 10 | R3H-10 归档 `reference-adoption-r3h10.md` + `EXECUTION_INDEX.md` | ✅ |
| 11 | R3H-03 归档 `reference-adoption-audit.md`（baostock L2 先例） | ✅ |
| 12 | R3G 归档 `plan-boot.md`（limited production 边界，非 watermark 实现） | ✅ |
| 13 | `BATCH_3H_COORDINATOR_PLAYBOOK.md` §5 | ✅ |
| 14 | GitNexus `query` watermark/incremental/sync | ✅ |

---

## GitNexus 调研摘要

`query("watermark incremental sync baostock trade_date")` 命中：

- `IncrementalJobRunner` / `run_incremental` 与 `test_batch_d_orchestration_flow`、`test_vendor_fetch_e2e` 测试簇。
- `parse_pilot_date_window`（ops pilot）— **非**产品 watermark；仅作日期窗解析对照，不接入金路径。
- **无**现有 `sync/watermark` 符号 — 确认绿场模块由轨 A 新建。

`context(run_incremental)`：6 个测试 caller；无生产 CLI caller — 符合「CLI 切片待建」判断。
