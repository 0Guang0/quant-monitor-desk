# GitNexus Audit Summary — R3-DCP-08 Layer4

> **日期：** 2026-07-02 · **任务：** `07-02-wave4-r3-dcp-08-layer4` · **Repair A9**

## 新符号触点

| 符号                          | 路径                                       | 角色                                              |
| ----------------------------- | ------------------------------------------ | ------------------------------------------------- |
| `USEquityCleanMarketAdapter`  | `backend/app/layer4_markets/clean_read.py` | US_EQ clean read adapter                          |
| `aggregate_breadth_from_bars` | `clean_read.py`                            | Tier A bar → breadth                              |
| `_fetch_clean_bar_rows`       | `clean_read.py`                            | 单次 SQL 复用（Repair A2）                        |
| `_finalize_market_build`      | `market_structure.py`                      | staged/clean 共享 lineage finalize                |
| `sync_mootdx_incremental`     | `data_commands.py`                         | mootdx 显式路由（registry SSOT，无 runtime hack） |

## 调用链（业务视角）

```text
security_bar_1d (Tier A clean)
  → USEquityCleanMarketAdapter.load_breadth / load_calendar
  → MarketStructureBuilder._build_tier_a_clean
  → _finalize_market_build → lineage_envelope

qmd data sync --source-id mootdx
  → sync_mootdx_incremental
  → enabled_source_registry + DataSourceService.preview_route
  → selected_source_id=mootdx（registry validation_only=false）
```

## 索引状态

Repair 后新符号已落盘；合入主分支后须 `node .gitnexus/run.cjs analyze` 刷新索引以便 `context`/`impact` 命中 Layer4 clean 触点。

## Repair 验证

- `uv run pytest tests/test_layer4_clean_read.py tests/test_layer4_us_equity_clean_e2e.py -q` exit 0
- `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` exit 0
