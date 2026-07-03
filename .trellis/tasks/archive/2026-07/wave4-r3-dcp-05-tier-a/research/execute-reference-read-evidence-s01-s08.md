# Execute reference read evidence — S01 / S08 (Agent A)

> RED 前实读 · 2026-07-02 · worktree `feature/dcp05-s01-s08`

## 参考项目实读

| 路径                                         | 采纳                                                                                                                       | 禁止                                        |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| OpenBB `fetcher.py` L36–85                   | L3 对齐：`transform_query`→`extract`→`transform`；QMD 等价 watermark→`FetchRequest.start_time/end_time`→port→staging→clean | 禁止拷贝 `Fetcher` 类 / OpenBB runtime      |
| EasyXT `auto_data_updater.py` L114–178       | L2 概念：增量只拉日期窗 `start_date`/`end_date`；对齐 `compute_incremental_window`                                         | 禁止 schedule 线程 / `DataManager`          |
| EasyXT `auto_data_updater.py` L31–32, L87–97 | —                                                                                                                          | 禁止 `sys.path` / 延迟 `DataManager` import |
| EasyXT `unified_data_interface.py` L172–244  | —                                                                                                                          | 禁止 DuckDB 不全→在线 silent fallback       |

## 仓内模板

| 路径                                     | S01/S08 用法                                                 |
| ---------------------------------------- | ------------------------------------------------------------ |
| `ops/fred_incremental_run.py`            | ops 层承载增量 run；CLI 薄包装                               |
| `sync/watermark.py`                      | bar watermark + `compute_incremental_window`                 |
| `fetch_ports/baostock_port.py`           | `_filter_bars_by_window` + `create_*_fetch_port(use_mock=…)` |
| `tests/test_baostock_incremental_e2e.py` | mootdx e2e 镜像                                              |

## 切片决策

- **S01**：`QMD_ALLOW_LIVE_FETCH=1` → `use_mock=False` + `product_live=True`；默认仍 replay mock（fail-closed ADR-027）
- **S08**：mootdx port 补窗过滤（仿 baostock）；`ops/mootdx_incremental_run.py` + e2e → `security_bar_1d`

## GitNexus impact（计划改 symbol）

- `sync_baostock_incremental`（data_commands）— 薄化调用 ops
- 新增 `run_baostock_bar_incremental` / `run_mootdx_bar_incremental`
- `MootdxMockFetchPort.fetch_payload` — 加 `_filter_bars_by_window`
- 风险：LOW（无 orchestrator/registry 变更）
