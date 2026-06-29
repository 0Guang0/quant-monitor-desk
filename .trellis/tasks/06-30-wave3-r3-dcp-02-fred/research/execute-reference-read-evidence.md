# Execute 参考项目实读证据

- MAIN_REPO_REFERENCE_ROOT: C:\Users\Guang\Desktop\quant-monitor-desk\参考项目
- 实读日期: 2026-06-30

| # | 文件 | 等级 | 关键符号/行 | 本轨采纳/拒绝 |
|---|------|------|-------------|---------------|
| R1 | OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py | architecture_only | `Fetcher.fetch_data` L74-85：`transform_query` → `extract_data` → `transform_data` 三阶段；`require_credentials` L40 | **采纳**分层对照：`FetchRequest.start_time`→port 窗、`FRED_API_KEY`→live credentials、`official_macro_evidence_v1`→transform；**拒绝**拷贝 Provider 类 |
| R2 | EasyXT/data_manager/unified_data_interface.py L172-237 | forbidden | L172-237：DuckDB 不全则 QMT 在线回退（`local_only=False`） | **拒绝** silent 扩窗/换源；冷启动用 capped 窗或显式 `--since` |
| R3 | EasyXT/data_manager/auto_data_updater.py | forbidden scheduler | L1-18：定时 scheduler bypass 门面 | **拒绝** import；本轨走 `DataSourceService` + `run_incremental` 金路径 |

**仓内源码（worktree 已读）：**

| 文件 | 采纳 |
|------|------|
| `fred_port.py` L101-121 `_window_start` 固定回溯 | L2：接 `FetchRequest.start_time` |
| `clean_write_targets.py` L41-47 macro → `axis_observation` | L1：PK `observation_id` |
| `rehearsal_loader.py` L315-371 `_macro_observation_rows_from_bundle` | L1：观测行映射参照 |
| `orchestrator.py` L173-220 `run_incremental` | L1：只读调用，传 macro `primary_keys` |

**自检：** 上表每行均已 Read 全文或指定行范围；未读不得进入 S02-01 RED。
