# To-Issues 垂直切片 — R3H-06（审计修复后）

| 序  | Slice         | 交付                                             | 依赖        |
| --- | ------------- | ------------------------------------------------ | ----------- |
| S0  | BOOT          | 测试空壳                                         | —           |
| S1  | BAR-DDL       | 013 bar + instrument_registry                    | S0          |
| S2  | DISC-DDL      | 013 cn_announcement_clean + stg_disclosure_smoke | S0          |
| S3  | STG-BAR-OHLCV | 014 stg OHLCV + StagingRow                       | S1          |
| S4  | STG-DISC      | populate_disclosure_from_bundle                  | S2          |
| S5  | ROUTER        | clean_write_targets + limited_production_entry   | S1,S2,S3,S4 |
| S6  | CNINFO-NO-BAR | 删 bar 合成 + 负向测                             | S4,S5       |
| S7  | G6-UPSERT     | promote 真实幂等                                 | S5          |
| S8  | PILOT-NO-VIEW | rg 零匹配 + r3g03 改 security_bar_1d             | S5,S1       |
| S9  | DOCS          | MIGRATION_COVERAGE + rollback 注记               | S1,S2       |
| S10 | MERGE         | 全库 pytest                                      | S1–S9       |

映射：9.0=S0 … 9.10=S10。**禁止 VIEW。**
