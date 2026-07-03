# GitNexus 摘要 — R3-DCP-05

> **日期：** 2026-07-02 · Plan Phase 1b  
> **索引：** quant-monitor-desk @ planning

## 改动冲击面（Plan 预判）

| 符号 / 区域                                      | 风险   | 说明                                      |
| ------------------------------------------------ | ------ | ----------------------------------------- |
| `sync_baostock_incremental`                      | MEDIUM | 上游 CLI；`use_mock` 变更影响 baostock 测 |
| `clean_write_targets.resolve_clean_write_target` | HIGH   | 全 sync 写路径依赖                        |
| `fred_incremental_run`                           | LOW    | 模板；DCP-05 复制模式                     |
| `DataSyncOrchestrator.run_incremental`           | HIGH   | 共享；切片禁止大改                        |
| migration 015                                    | MEDIUM | 新表；须 migration 测                     |

## 建议 Execute 前

- `impact(sync_baostock_incremental)` · `impact(resolve_clean_write_target)` · `impact(run_incremental)`
- 提交前 `detect_changes({scope: "compare", base_ref: "master"})`

## 执行流

`qmd data sync` → `data_commands` → watermark → `DataSourceService` → `IncrementalJobRunner` → clean upsert
