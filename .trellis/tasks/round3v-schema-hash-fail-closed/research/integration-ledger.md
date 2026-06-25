# Integration ledger — B3V-DATA

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
|--------|----------|----------|---------------|-----------------|-------------|
| `B02_02_schema_hash_fail_closed.md` | business | pointer | §1.1 目标 | 五切片 + §6 测试 | AC-DATA-* |
| `BATCH_3V_HARDENING_RULES.md` | decision | pointer | 1.4 约束 | 禁 production clean write | 停止条件 |
| `data_adapter_contract.md` | contract | pointer | 2.4 契约 | 结构化 schema_hash 段 | AC-DATA-01 |
| `write_contract.yaml` | contract | pointer | 2.4 契约 | schema_hash_changed reject | AC-DATA-03 |
| `data_quality_rules.yaml` | contract | pointer | SCHEMA_DRIFT | SCHEMA_DRIFT failed | AC-DATA-04 |
| `docs/modules/data_validation_and_conflict.md` | architecture | pointer | ## 2. | gate 数据流语义 | AC-DATA-03 |
| `GLOBAL_EXECUTION_RULES.md` | rule | pointer | 1.4 约束 | scope 纪律 | §3 |
| `skeleton_base.py` | wiring | pointer | ## 8. | _infer_schema_hash | AC-DATA-02,04 |
| `validation_gate.py` | wiring | pointer | ## 8. | _schema_hash_blocks_write | AC-DATA-03,05 |
| `fetch_port.py` | wiring | pointer | ## 8. | FetchPayload.schema_hash | AC-DATA-02 |
| `test_db_validation_gate.py` | wiring | pointer | 5.1 测试文件路径 | missing hash 用例 | AC-DATA-03 |
| `test_adapter_skeletons.py` | wiring | pointer | 5.1 测试文件路径 | CSV/Parquet/corrupt | AC-DATA-02,04 |
| `resource_limits.yaml` | rule | pointer | 1.4 约束 | 有界读取上限 | AC-DATA-02 |
