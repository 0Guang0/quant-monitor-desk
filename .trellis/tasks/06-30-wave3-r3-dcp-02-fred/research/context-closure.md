# Execute 六项理解闭合 — R3-DCP-02

| # | 项 | 闭合 |
|---|-----|------|
| 1 | **做什么** | fred 宏观序列增量：读 `axis_observation` 水位 → 窄窗 fetch → upsert clean；CLI `qmd data sync --domain macro_series --source-id fred` |
| 2 | **价值** | 生产入口可重复跑 FRED P0 series，幂等写 macro clean，不走 rehearsal 旁路 |
| 3 | **完成条件** | DEBT S02-01..05 测绿 + 定向 pytest + 隔离 `QMD_DATA_ROOT` |
| 4 | **边界** | 仅 fred/macro；禁止改 orchestrator/runners/watermark*/baostock；无新 migration |
| 5 | **架构触点** | `fred_incremental_watermark` · `fred_port.start_time` · `fred_incremental_run` · `data_commands.sync` |
| 6 | **终态** | 每 series `indicator_id` + `DATE(publish_timestamp)` 水位；`observation_id` UUID5 upsert 幂等 |
