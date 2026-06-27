# To-Issues Vertical Slices — R3H-01（Plan 3.5）

> Skill: `to-issues` · 工单列表 → EXECUTION_INDEX §1 / 活卡 §9

| ID  | 切片                   | 交付物                                           | 依赖   | 索引 Step |
| --- | ---------------------- | ------------------------------------------------ | ------ | --------- |
| S0  | boot_test_skeleton     | `tests/test_official_macro_adapters.py` 模块骨架 | —      | 9.0       |
| S1  | fred_evidence_contract | `official_macro.py` + bridge/loader 统一         | S0     | 9.1       |
| S2  | fred_fetch_port        | `fred_port.py` + replay + route tests            | S1     | 9.2       |
| S3  | us_treasury_port       | `us_treasury_port.py` + replay                   | S0     | 9.3       |
| S4  | sec_edgar_port         | `sec_edgar_port.py` + `sec_edgar.py` normalizer  | S0     | 9.4       |
| S5  | cftc_bis_wb_ports      | 三 port 文件或 ADR 各一份                        | S0     | 9.5       |
| S6  | registry_coordinator   | 六源 registry/route manifest PR                  | S2–S5  | 9.6       |
| S7  | layer_smoke            | Layer1/L5 最小契约测                             | S1, S2 | 9.7       |
| S8  | merge_gate             | 全量 pytest + loop_maintain                      | S1–S7  | 9.8       |

**并行规则：** S3/S4/S5 可在 S1 完成后并行；S6 必须最后合并 registry（coordinator）；S7 依赖 S1+S2。

**Phase 3.5 complete**
