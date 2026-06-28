# Integration Ledger — R3H-04（Plan 5c）

## 内联 vs manifest 分工

| 来源类型 | 落点 | 理由 |
| --- | --- | --- |
| GLOBAL 四文件 | INDEX §3 must-read | 不可无损精简 |
| layer5 / user_input_privacy 契约 | INDEX §3 | 字段级 SSOT |
| registry 三源行 | INDEX §3 + §9.5 manifest | coordinator 对照 |
| grill 决策 / caps 表 | frozen §7–§8 | 可无损内联 |
| port 实现模式 | frozen §5 + `coingecko_port` §3 | 模式已总结；原文供 Execute 对照 |
| OpenBB 参考 | frozen §14 | 禁止清单须原文边界 |

## implement.jsonl 槽位预期

1. `frozen/R3H_04_*.md`
2. `EXECUTION_INDEX.md`
3. `context_pack.json`
4. §3 must-read 行（generate-manifests 自动）

**禁止：** `research/*` 路径进入 implement.jsonl

## E1–E15 登记（新模块）

| 新路径 | test_catalog | authority_graph |
| --- | --- | --- |
| `backend/app/datasources/normalizers/probability_signal.py` | Execute §9.8 loop_maintain | datasources |
| `backend/app/evidence/manual_review_staging.py` | 同上 | evidence |
| `tests/test_prediction_market_adapters.py` | 同上 | tests |
| `tests/test_web_evidence_adapter.py` | 同上 | tests |
| `tests/test_no_clean_write_for_web_evidence.py` | 同上 | tests |
