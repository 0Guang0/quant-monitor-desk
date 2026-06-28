# To-Issues Vertical Slices — R3H-02（Plan 3.5）

> Skill: `to-issues` · 工单列表 → EXECUTION_INDEX §1 / 活卡 §9

| ID  | 切片                          | 交付物                                                     | 依赖  | 索引 Step |
| --- | ----------------------------- | ---------------------------------------------------------- | ----- | --------- |
| S0  | boot_test_skeleton            | `test_market_data_adapters.py` + `test_crypto_*` 骨架      | —     | 9.0       |
| S1  | market_data_evidence_contract | `market_data.py` + evidence round-trip                     | S0    | 9.1       |
| S2  | alpha_vantage_port            | `alpha_vantage_port.py` + replay + route                   | S1    | 9.2       |
| S3  | stooq_port                    | `stooq_port.py` + validation route                         | S1    | 9.3       |
| S4  | yahoo_finance_port            | `yahoo_finance_port.py` + 3G fixture 迁移                  | S1    | 9.4       |
| S5  | deribit_coingecko_ports       | `deribit_port.py`, `coingecko_port.py`, `crypto_market.py` | S1    | 9.5       |
| S6  | registry_coordinator          | 五源 registry/route manifest PR                            | S2–S5 | 9.6       |
| S7  | layer_smoke                   | L2/L4/L5 最小契约测                                        | S1,S2 | 9.7       |
| S8  | merge_gate                    | 全量 pytest + loop_maintain                                | S1–S7 | 9.8       |

**并行规则：** S3/S4/S5 可在 S1 完成后并行；S6 必须 coordinator；S7 依赖 S1+至少一个 equity port；S8 最后。

**Phase 3.5 complete**
