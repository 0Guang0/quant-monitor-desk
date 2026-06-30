# Audit matrix — R3-DCP-01 baostock incremental

> **追溯：** 活卡 `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` · `DEBT.plan.md` · `research/reference-adoption-dcp01.md`

| 维度            | 状态     | 范围 / 理由                                                                                                            |
| --------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| **A1 正确性**   | 必做     | watermark 空/有/边界；incremental 窗 `max+1`；upsert 幂等；`security_bar_1d` PK 不重复；隔离库路径                     |
| **A2 可读性**   | 必做     | `watermark.py` API 命名；CLI help；L2 attribution 注释（staged_pilot / orchestrator 先例）                             |
| **A3 架构**     | 必做     | 金路径 `DataSourceService` + `run_incremental`；无 `adapter=` 生产 bypass；轨 A/B 文件锁遵守；`watermark` 模块归属轨 A |
| **A4 安全**     | 必做     | `QMD_DATA_ROOT` 隔离；禁止 canonical 主库 silent 写；live env gate；`ResourceGuard` 在 CLI 真跑路径                    |
| **A5 测试**     | 必做     | 五字段 docstring；RED→GREEN 证据；`test_baostock_incremental_*` + CLI 契约测                                           |
| **A6 性能**     | **SKIP** | 单源 whitelist ≤5 symbols、replay/隔离库；无批量全市场增量；无 perf SLA                                                |
| **A7 GitNexus** | 必做     | 改 `run_incremental`/`IncrementalJobRunner`/`watermark` 前 impact；`detect_changes` 与切片 scope 对齐                  |
| **A8 证据**     | 必做     | `research/execute-evidence/s0*-*.txt`；pytest 日志；`loop_maintain`；Audit 不信文档自述                                |

---

## A6 SKIP 理由（登记）

本任务为单源试点增量，数据量受 `baostock_port` `MAX_SYMBOLS=5` / `MAX_ROWS=500` / `MAX_WINDOW_DAYS=120` 约束；无全表 scan 或高并发路径。性能风险不高于既有 `IncrementalJobRunner` 基线；Wave 4 Tier A 扩展时再开 A6。

---

## 各维重点验证点

### A1

- [ ] `compute_incremental_window(max=2026-06-28).date_start == 2026-06-29`
- [ ] 空表 lookback 符合契约
- [ ] 两次 incremental COMPLETED 后 `COUNT(*)` 不变

### A2

- [ ] `watermark.py` API 与 `architecture-dcp01.md` 建议签名一致
- [ ] L2 拷改处有 `staged_pilot` / R3H-03 先例 attribution 注释

### A3

- [ ] `rg "adapter=" backend/app/cli` 真跑路径经 `datasource_service=`
- [ ] 未改 `fred_port`
- [ ] `sync/watermark.py` 仅轨 A 提交

### A4

- [ ] 测试/证据无 `data/duckdb/quant_monitor.duckdb` 写
- [ ] dry-run 默认无 side effect

### A5

- [ ] 新 `test_*` 均有五字段 docstring
- [ ] `tests/test_catalog.yaml` 登记

### A6

- **SKIP**（见上表）；Execute 后仍扫描计划外无界 I/O / 全市场 scan

### A7

- [ ] 改 `run_incremental` / `IncrementalJobRunner` / `watermark` 前 `impact()` 有记录
- [ ] `detect_changes()` scope 与 `DEBT.plan.md` allowed 对齐

### A8

- [ ] `research/execute-evidence/s0*-green.txt` 与 pytest 日志可交叉验证
- [ ] 边界：空表 lookback、边界日 +1、重复跑幂等均有独立断言

---

## Repair 来源

- Execute 后各维 `research/audit-a{n}-report.md`
- 汇总 `audit.report.md` §4.3 → A9 ledger → P6 Repair
