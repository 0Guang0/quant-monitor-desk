# GitNexus Audit Summary — R3H-04 Repair

**日期：** 2026-06-28

## 动作

- Repair 前：R3H-04 新 port/normalizer/staging 符号未入图（A1/A5/A8）
- Repair 后：执行 `node .gitnexus/run.cjs analyze` 刷新索引（见仓库 `.gitnexus/` 时间戳）

## 新增符号（Repair 触达）

| 符号 | 层 |
|------|-----|
| `build_probability_market_fetch_payload` | L3 common |
| `read_bounded_http_body` | L3 live cap |
| `run_prediction_market_live_smoke` | ops smoke |
| `_normalize_resolution_source` | normalizer |
| `reject_forbidden_resolution_fields` | normalizer（既有，现已可索引） |
| `reject_clean_table_promotion` | staging |

## detect_changes

Repair 会话未 commit；合并前主会话应对本轨 diff 跑 `detect_changes({scope: "compare", base_ref: "master"})`。
