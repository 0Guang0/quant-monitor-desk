# Execute 参考项目实读证据

- MAIN_REPO_REFERENCE_ROOT: `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目`
- 实读日期: 2026-06-30

| #   | 文件                                                     | 等级                            | 关键符号/行                                                                                                                                                | 本轨采纳/拒绝                                                                                                            |
| --- | -------------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| R1  | `EasyXT/data_manager/auto_data_updater.py`               | L2 概念 / **forbidden runtime** | `AutoDataUpdater` L52-355：`schedule`+thread 定时、`should_update_today` 交易日判断、`update_single_stock` 按日拉取、`duckdb.connect` 直读写 `stock_daily` | **拒绝 runtime**：禁止 import/scheduler bypass；**采纳概念**：「读库→只补当日/增量窗」对照 watermark `max(trade_date)+1` |
| R2  | `EasyXT/data_manager/unified_data_interface.py` L172-237 | **forbidden**                   | `get_stock_data`：DuckDB 优先→失败 silent 降级 `_read_from_duckdb`/QMT；`local_only` 可挡在线但仍混源                                                      | **拒绝**：禁止 silent 换源/扩窗进入 QMD sync；金路径仅 `DataSourceService` + orchestrator                                |
| R3  | `EasyXT/data_manager/data_integrity_checker.py`          | L2 对照（可选）                 | 未全文深读；Plan 已标可选                                                                                                                                  | **阶段外**：Wave 3 用 sync validation pipeline 已有 quality/conflict                                                     |

**仓内源码（worktree 实读）：**

| 文件                                                                | 要点                                                                             |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `backend/app/sync/orchestrator.py` L173-220                         | `run_incremental` 金路径 `_service_fetch` → `IncrementalJobRunner`；**只读不改** |
| `backend/app/sync/runners.py` L419-425                              | `FetchRequest` 未填 `start_time/end_time` → S02 补丁点                           |
| `backend/app/datasources/fetch_ports/baostock_port.py` L65-68       | replay 全量返回 fixture → S03 窗过滤                                             |
| `backend/app/ops/sandbox_clean_write/clean_write_targets.py` L25-33 | `cn_equity_daily_bar` → `security_bar_1d` upsert PK                              |

**自检：** 上表 R1/R2 已 Read 全文或指定行范围；仓内四文件已 Read；未读不得进入 S01 RED — **已闭合**。
