# Original Plan Trace — R3H-06（9.0–9.10）

| 活卡 §9            | Step | AC                        |
| ------------------ | ---- | ------------------------- |
| 9.0 boot           | 9.0  | AC-BOOT                   |
| 9.1 bar_ddl        | 9.1  | AC-SCHEMA-G3G4-BAR        |
| 9.2 disclosure_ddl | 9.2  | AC-CNINFO-SHAPE           |
| 9.3 stg_bar_ohlcv  | 9.3  | AC-SCHEMA-G4-OHLCV        |
| 9.4 stg_disclosure | 9.4  | AC-STG-DISCLOSURE         |
| 9.5 domain_router  | 9.5  | AC-SCHEMA-G3-ROUTER       |
| 9.6 cninfo_shape   | 9.6  | AC-CNINFO-NO-BAR（含 G5） |
| 9.7 idempotency    | 9.7  | AC-G6-IDEMPOTENCY         |
| 9.8 pilot_compat   | 9.8  | AC-PILOT-COMPAT           |
| 9.9 docs_coverage  | 9.9  | AC-DOCS                   |
| 9.10 merge_gate    | 9.10 | AC-MERGE                  |

§5.0.1：**SCHEMA-G3G4**←9.1+9.3+9.5；**CNINFO-DISCLOSURE-SHAPE**←9.2+9.4+9.6；**G6**←9.7。
