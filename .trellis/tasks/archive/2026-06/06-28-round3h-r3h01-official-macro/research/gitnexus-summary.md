# GitNexus Summary — R3H-01 (Plan 1b)

> query + 静态补全 · 2026-06-28

## Query 结果

| Query                                                 | 命中                                        | 备注                |
| ----------------------------------------------------- | ------------------------------------------- | ------------------- |
| `FRED promote evidence loader`                        | live_pilot_phase3, batch25/275 policy tests | 偏 R3E/R3X 链       |
| `live_evidence_bridge fred_evidence rehearsal_loader` | 同上                                        | bridge 符号未入索引 |

## Impact（改前必跑）

| Target                                | 结果                   | 静态补全 callers                                                                                  |
| ------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------- |
| `materialize_fred_promote_evidence`   | UNKNOWN                | `scripts/r3g03_isolated_pilot_dry_run.py`, `tests/test_round3g_limited_production_clean_write.py` |
| `live_evidence_bridge` (module)       | not found              | 新文件，低风险新增                                                                                |
| `rehearsal_loader._fred_staging_rows` | 待 Execute 前 `impact` | promote 主路径                                                                                    |

**风险预判：** 统一 FRED 证据 schema 时，**MEDIUM** — 触及 rehearsal_loader、bridge、live_pilot、round3g 测试；不触及 Layer1–5 主路径（R3H-05 范围）。

## 建议 Execute 前刷新索引

```bash
node .gitnexus/run.cjs analyze
```

## Plan 阶段锚定符号（Execute 改前 impact）

1. `materialize_fred_promote_evidence` / 替代统一 writer
2. `_fred_staging_rows`
3. `capture_phase3_raw_evidence`（若 live 产出形态变更）
4. 新建 `fred_port` 公开 API
