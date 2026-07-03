# Plan context — R3-DCP-05

## Context hierarchy (L1–L5)

| Level   | 本任务映射                                                 |
| ------- | ---------------------------------------------------------- |
| L1 项目 | Wave 4 PASS 路径；`PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5 |
| L2 批次 | BATCH_3H · `R3_DCP_TO_ISSUES_INDEX.md`                     |
| L3 模块 | D1 sync · E1 CLI · A2 schema · C3 ports                    |
| L4 任务 | 本 Trellis 目录 + 活卡                                     |
| L5 切片 | `to-issues-slices.md` S00–S13                              |

## PROJECT CONTEXT（Execute 可复制）

```text
Goal: 11 Tier A sources incremental sync → clean upsert (ADR-028).
Templates: DCP-01 bar, DCP-02 fred macro, migration 015 for sec_edgar + deribit.
P0 fix: baostock sync use_mock=True → product live gate.
Gates: QMD_ALLOW_LIVE_FETCH, sandbox DB, DataSourceService only.
Non-goals: FRED live primary, G12 five axes, Tier B/C.
```

## Level 3 源码表

| 主题           | 必读路径                                                           |
| -------------- | ------------------------------------------------------------------ |
| Bar watermark  | `sync/watermark.py`, `data_commands.sync_baostock_incremental`     |
| Macro template | `ops/fred_incremental_watermark.py`, `ops/fred_incremental_run.py` |
| Clean routing  | `ops/sandbox_clean_write/clean_write_targets.py`                   |
| Live gate      | `datasources/product_live_gate.py`, `product_live_ports.py`        |
| Schema         | `migrations/013_*`, **015 draft in plan-spec**                     |
| ADR            | `docs/decisions/ADR-028-*.md`                                      |

## 开工必读 vs 情境路由

**§5.2 开工必读（整包）：** ENTRY §1–§4 · `to-issues-slices.md` · `reference-adoption-dcp05.md` · ADR-028 · 活卡

**§5.3 情境：**

| 情境           | 再读                                                   |
| -------------- | ------------------------------------------------------ |
| 改 baostock    | S01 + DCP-01 归档                                      |
| 新宏观源       | S03–S06 + fred_incremental_run + digital-oracle bis L2 |
| 新 clean 表    | S00 + ADR-028 + migration tests                        |
| registry merge | S13 + B3F-REG policy                                   |
