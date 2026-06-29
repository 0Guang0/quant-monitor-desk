# R3-DCP-01 参考采纳调研 — baostock incremental watermark

> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-01-baostock/`  
> **日期：** 2026-06-30  
> **方式：** 仓库源码 Read + R3H/R3G 归档 adoption 文档 + GitNexus query；`参考项目/**` 本 worktree **不存在**（`.gitignore` 本地-only），结论引用归档深读，Execute 前用户环境须再 Read 活卡列路径。

---

## L1 / L2 / L3 总表

| 等级 | 含义 | QMD 目标 | 证据路径 | 函数/模式对照 |
|------|------|----------|----------|---------------|
| **L1** | 直接复用 | `DataSyncOrchestrator.run_incremental` | `backend/app/sync/orchestrator.py:173-220` | `datasource_service` → `_service_fetch` → `IncrementalJobRunner.run` |
| **L1** | 直接复用 | `IncrementalJobRunner` 编排 | `backend/app/sync/runners.py:384-500` | fetch → STAGED → VALIDATING → write pipeline |
| **L1** | 直接复用 | `DataSourceService.fetch` 金路径 | `backend/app/datasources/service.py:40-256` | route → guard → adapter → fetch_log |
| **L1** | 直接复用 | clean 表路由 | `backend/app/ops/sandbox_clean_write/clean_write_targets.py:25-33` | `cn_equity_daily_bar` → `security_bar_1d`, `upsert_by_pk` |
| **L1** | 直接复用 | baostock fetch port | `backend/app/datasources/fetch_ports/baostock_port.py` | `create_baostock_fetch_port`, replay fixture |
| **L1** | 直接复用 | 幂等增量先例测 | `tests/test_batch_d_orchestration_flow.py:174-220` | `test_incrementalJob_repeatRun_noDuplicatePrimaryKey` |
| **L1** | 直接复用 | service 路径 E2E | `tests/test_vendor_fetch_e2e.py:90-175` | `test_vendorFixtureFetch_e2eThroughDataSourceServicePath` |
| **L1** | 直接复用 | 日期窗 cap 校验 | `backend/app/datasources/fetch_window.py:94-125` | `reject_fetch_window_span_over_cap` |
| **L1** | 直接复用 | CLI dry-run 壳 | `backend/app/cli/data_commands.py:59-104` | `sync_plan` guard + route_preview |
| **L2** | 拷改 | **新建** `sync/watermark.py` | 设计 `docs/modules/data_sync_orchestrator.md` §13.4.2 步骤 1–4 | `read_bar_trade_date_watermark(con, *, clean_table, instrument_id?, adjustment_type?)` → `compute_incremental_window` → `IncrementalWindow`；对照 R3H-10 EasyXT `auto_data_updater` **增量游标语义**（归档 `reference-adoption-r3h10.md` §3.2 反例：scheduler 绕过门面 → 本任务**禁止**） |
| **L2** | 拷改 | `IncrementalJobRunner` 注入窗 | `backend/app/sync/runners.py:419-425` | 从 `spec.date_start/date_end` 填 `FetchRequest.start_time/end_time`（ISO UTC） |
| **L2** | 拷改 | `baostock_port` 窗内过滤 | `baostock_port.py:65-97` | replay 路径现返回全 fixture；mock 路径未按 `req.start_time/end_time` 过滤 — Execute 须补窗内 bar 过滤 |
| **L2** | 拷改 | CLI 真跑子路径 | `data_commands.py` + `cli/main.py:128-136` | 新增 `sync_baostock_incremental` 或扩展 `sync`：`dry_run=False` 时 orchestrator + watermark；对照 `live_fetch` 门禁模式 |
| **L2** | 拷改 | 集成测 | 新 `tests/test_baostock_incremental_watermark.py` | 模式来自 `test_vendor_fetch_e2e` + `test_batch_d` 重复跑 |
| **L3** | 绿场 | CN 交易日历算窗 | 活卡 ponytail | R3H-03 日历仅 weekday proxy；Wave 3 用 **calendar day `max(trade_date)+1`**，完整 G2/G17 绑后续任务 |
| **L3** | 绿场 | baostock 真网 live | `BaostockProductLiveFetchPort` | replay-first；live 须 `gate_live_fetch_port` + env；非本切片阻塞项 |
| **L3** | 禁止 | EasyXT `UnifiedDataInterface` | 归档 R3H-10 §3.2 | silent bypass / hardcoded DB — **不得**进入 sync 路径 |
| **L3** | 禁止 | OpenBB Provider runtime | 归档 R3H-10 §3.1 | architecture_only |

---

## 分主题深读

### A. 仓库内 L1 — 编排与写库

**Orchestrator 金路径（已存在）：**

```173:220:backend/app/sync/orchestrator.py
    def run_incremental(
        self,
        spec: SyncJobSpec,
        *,
        adapter: BaseDataAdapter | None = None,
        datasource_service=None,
        clean_table: str,
        ...
    ) -> SyncJobResult:
        ...
        if datasource_service is not None:
            def _service_fetch(req, con, job_id, operation=None):
                return datasource_service.fetch(...)
            fetch_callable = _service_fetch
        return self._incremental.run(spec, ..., fetch_callable=fetch_callable, config=...)
```

**Clean 目标（R3H-06 SSOT）：**

```25:33:backend/app/ops/sandbox_clean_write/clean_write_targets.py
    if domain in BAR_DOMAINS:
        return CleanWriteTarget(
            target_table="security_bar_1d",
            staging_table="stg_foundation_smoke",
            write_mode="upsert_by_pk",
            primary_keys=("instrument_id", "trade_date", "adjustment_type"),
        )
```

### B. L2 — watermark 模块（新建）

**设计契约（来自 `data_sync_orchestrator.md` §13.4.2）：**

1. 读 clean 表最新 `trade_date`（可按 `instrument_id` 过滤）。
2. 空表 → `date_start` = 配置默认（如最近 N 日历日或 fixture 起点）。
3. 有数据 → `date_start = max(trade_date) + 1 day`。
4. `date_end` = UTC today（calendar）；后续 Wave 4 可换 CN trading calendar。

**与 pilot 区分：** `ops/live_pilot_fetch_ports.parse_pilot_date_window` 服务 rehearsal，**不**挂产品 sync。

### C. L2 — baostock port（已有，补窗过滤）

`baostock_port.py` 头注释已标 L2 migrate from `staged_pilot_fetch_ports`。Execute 须：

- replay JSON 按 watermark 窗过滤 bars；
- `adjustment_type` 与 `security_bar_1d` PK 对齐（默认如 `none` 或契约字段）。

### D. 归档参考 — R3H-10 / R3H-03

| 归档 | 可采纳 | 禁止 |
|------|--------|------|
| `06-29-round3h-r3h10/.../reference-adoption-r3h10.md` | DataSourceService 分层；fetch_ports 双轨收敛结论 | EasyXT scheduler bypass；OpenBB runtime |
| `06-28-round3h-r3h03/.../reference-adoption-audit.md` | baostock port L2 from staged_pilot | 未读 `参考项目/EasyXT` 前标 L3 |

### E. R3G 边界（非 watermark 实现）

R3G 归档实现 sandbox → limited production **promote**；本任务走 **incremental 产品 sync**，复用 R3G 确立的隔离库 / `QMD_DATA_ROOT` 纪律，**不**调用 `sandbox-clean-write promote` 路径。

### F. `参考项目/**` 状态与 Execute 门禁

本 worktree **无** `参考项目/` 目录（`.gitignore` 本地-only）。

| 阶段 | 要求 |
|------|------|
| Plan | 可引用 R3H-10/08 归档深读 + 上表 L1/L2/L3 |
| **Execute RED 前** | **必须** Read 主仓绝对路径：`C:\Users\Guang\Desktop\quant-monitor-desk\参考项目\` 下表文件 → 落盘 `research/execute-reference-read-evidence.md` |

**Execute 必读（主仓）：**

- `EasyXT/data_manager/auto_data_updater.py` — 增量游标概念 L2；**forbidden** scheduler/runtime import
- `EasyXT/data_manager/unified_data_interface.py` L172-237 — **forbidden** DuckDB→QMT 回退反例

**纪律：** 禁止 runtime import；仅 Read 对照。详见 `EXECUTE-REFERENCE-READ-GATE.md`。

---

## 采纳决策摘要

| 组件 | 等级 | 决策 |
|------|------|------|
| Orchestrator + Service + clean target | L1 | 直接接，不 fork |
| watermark 读库算窗 | L2 | 新建 `sync/watermark.py`，轨 A 拥有 |
| Runner FetchRequest 窗 | L2 | 最小补丁 `runners.py`（与轨 B 协调：仅 date 注入，接口稳定） |
| baostock port 过滤 | L2 | 本轨 `baostock_port.py` |
| CLI sync 真跑 | L2 | 本轨 `data_commands.py` |
| CN 交易日历 | L3 | Wave 3 ponytail calendar days |
| 真网 baostock | L3 | replay-first；live env-gated 可选 smoke |
