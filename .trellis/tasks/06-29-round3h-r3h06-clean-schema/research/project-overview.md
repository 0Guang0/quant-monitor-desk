# Project Overview — R3H-06（Plan 1a）

> GitNexus `query` + 静态对照 · 2026-06-29

## 当前 clean 写路径（偏离点）

| 组件             | 路径                                             | 现状                                              |
| ---------------- | ------------------------------------------------ | ------------------------------------------------- |
| Pilot promote    | `limited_production_entry.py`                    | `target_table` 常量为 `market_bar_clean`          |
| Rehearsal loader | `rehearsal_loader.py`                            | `StagingRow` 仅 `close`；cninfo **合成 bar 日期** |
| Sync pipeline    | `sync/runners.py` `_write_clean`                 | 通用 clean 写；依赖表已存在                       |
| WriteManager     | `write_manager.py`                               | `append_only` / `upsert_by_pk` 已实现（3V）       |
| 设计契约         | `specs/schema/schema.sql`                        | `security_bar_1d` **未迁移**；无 disclosure 表    |
| 宏观             | migration `011`                                  | `axis_observation` **已存在**                     |
| 测试锚点         | `test_round3g_limited_production_clean_write.py` | 断言 `market_bar_clean`                           |

## G3–G6 映射

| Gap              | 根因                            | R3H-06 交付                 |
| ---------------- | ------------------------------- | --------------------------- |
| G3 同表无域语义  | pilot 单表                      | 三域分表 + domain router    |
| G4 仅 close      | `StagingRow` 形状               | OHLCV staging + DDL         |
| G5 cninfo 压 bar | `_cninfo_staging_rows` ponytail | `cn_announcement_clean`     |
| G6 叠行          | append 无 PK                    | `upsert_by_pk` on PK tables |

## 模块触碰面（Execute 预期）

```text
backend/app/db/migrations/013_*.sql
backend/app/ops/sandbox_clean_write/{rehearsal_loader,limited_production_entry}.py
tests/test_r3h06_clean_schema.py
tests/test_round3g_limited_production_clean_write.py（目标表回归）
```

## 风险

- r3g03 脚本/测硬编码 `market_bar_clean` — **无 VIEW**；9.8 全量改 `security_bar_1d` + rg 零匹配
- `security_bar_1d` vs `security_bar_daily` 文档漂移 — 本卡以 schema.sql 为准
- fred→axis_observation 列映射与 Layer1 ingestion 契约需对齐（非新表）
