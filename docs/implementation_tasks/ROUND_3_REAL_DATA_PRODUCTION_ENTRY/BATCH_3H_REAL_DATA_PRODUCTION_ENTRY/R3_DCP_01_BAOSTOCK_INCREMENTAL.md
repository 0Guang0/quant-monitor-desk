# R3-DCP-01 — baostock 增量水位 + 产品 CLI

> **规划 ID：** R3-DCP-01  
> **Wave：** 3a · **并行轨 A**  
> **Trellis：** debt-lite · `wave3-r3-dcp-01-baostock`  
> **Module：** D1 Sync orchestration · E1 `qmd data` CLI  
> **评级：** D1/E1 R3→R4

---

## 1. Goal（人话）

让中国 A 股日频 bar（baostock）能走**产品路径**：先看库里最后一天，只拉新来的数据，写进隔离库，命令行能反复跑也不重复堆行。

---

## 2. 价值

- Round4 日常增量的**第一个试点源**（与 fred 并列）
- 验证「读库水位 → incremental → clean write」在真实 port 上可复制到 Wave 4 Tier A 扩展
- 不依赖 `--live-wire` 运维脚本

---

## 3. 约束

| 约束 | 要求 |
| ---- | ---- |
| 金路径 | `DataSourceService.fetch` + `DataSyncOrchestrator.run_incremental` |
| 数据根 | 默认 `QMD_DATA_ROOT` 隔离库；**禁止** silent 写 canonical `data/duckdb/` |
| Schema | R3H-06 clean 表 + upsert PK；**无新 migration** |
| Registry | 仅 touch `baostock` 相关行；合并由主会话排队 |
| 参考项目 | Plan 须 L1/L2/L3 标注（见 INDEX §5） |

---

## 4. 架构触点

```text
qmd data sync …
  → watermark 读 clean.max(trade_date)
  → SyncJobSpec(incremental)
  → DataSourceService.fetch(baostock)
  → IncrementalJobRunner → clean 表
```

**拥有文件组（轨 A）：**

```text
backend/app/sync/watermark*.py（若新建，轨 A 拥有；轨 B 只读）
backend/app/cli/**（本轨 baostock 子命令切片）
backend/app/datasources/fetch_ports/baostock_port.py
backend/app/datasources/adapters/baostock.py
backend/app/ops/**（baostock 增量 smoke，若有）
tests/test_*baostock* / tests/test_*incremental*（本轨新增）
```

**禁止：** 改 `fred_port`、宏观 clean 域逻辑（轨 B）。

---

## 5. Acceptance criteria

- [ ] watermark 单测：空表 / 有数据 / 边界日
- [ ] incremental 集成测：replay 或 env-gated live（隔离库）
- [ ] 重复跑任务行数不增（写库幂等）
- [ ] CLI help + dry-run 可审计
- [ ] Plan 调研 `research/reference-adoption-dcp01.md` 含 L1/L2/L3 表
- [ ] Audit A1–A8 各维报告 + Repair ledger 关账
- [ ] `uv run pytest -q` exit 0

---

## 6. Done

活卡 §5 全勾 + 主会话 merge 轨 A + `R3H_PASS_EXECUTION_PLAN` Wave 3 行可标 DCP-01 CLOSED。

---

## 7. 非目标

- 全 Tier A 源扩展（Wave 4 DCP-05）
- FullLoad / Backfill 产品化
- 改 prediction market / Kalshi / Polymarket
- web_search 真 API
