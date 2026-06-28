# Original Plan Trace — R3H-04

> 活卡章节 → EXECUTION_INDEX §2 AC 映射

| 活卡锚点 | AC ID | INDEX Step | 验证 |
| --- | --- | --- | --- |
| §1 Goal — 三源闭环 | AC-SCOPE | 9.5, 9.8 | `test_r3h_source_final_decisions` + `-k r3h` A8 子集 |
| §5 — kalshi 实现 | AC-KALSHI | 9.2 | `test_prediction_market_adapters -k kalshi` |
| §5 — polymarket 实现 | AC-POLY | 9.3 | `test_prediction_market_adapters -k polymarket` |
| §5 — web_search 实现 | AC-WEB | 9.4 | `test_web_evidence_adapter` |
| §5.7 — probability_signal | AC-PROB-NORM | 9.1 | `-k evidence_contract or resolve` |
| §5.8 — Layer5/manual-review | AC-L5 | 9.7 | `-k layer` |
| §6 — 无 clean write | AC-NO-CLEAN | 9.6 | `test_no_clean_write_for_web_evidence` |
| §6 — 预测不 resolve 事实 | AC-NO-RESOLVE | 9.6 | 同上 `-k resolve` |
| §6 — contract coverage | AC-REGISTRY | 9.5 | capabilities + route + manifest |
| §11 — 验收命令 | AC-MERGE | 9.8 | 全库 pytest exit 0 + `9.8-green.txt` |
| §11 — DSS 集成 | AC-DSS | 9.8 | `test_predictionMarket_dataSourceService_fetch_portIntegration` |
