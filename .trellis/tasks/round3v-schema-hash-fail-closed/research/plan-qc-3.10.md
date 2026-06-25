# Plan 质检 §3.10 — B3V-DATA

| 路径 | 已入 MASTER/implement | 摘要一句 | 遗漏风险 |
|------|----------------------|----------|----------|
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | MASTER §0 Source Context | 共用底座与文件锁 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.3 | MASTER §0 + implement | B3V-DATA 必读表 | 无 |
| `B02_02_schema_hash_fail_closed.md` | original-plan-trace + MASTER §1.6 | 五切片 AC | 无 |
| `data_adapter_contract.md` | implement + §8 DATA-01 | 结构化 schema_hash | 无 |
| `skeleton_base.py` | implement + §9.2 | CSV/Parquet infer | 无 |
| `validation_gate.py` | implement + §9.3 | fail-closed | 无 |
| `write_contract.yaml` | implement + §2.4 | schema_hash_changed | 无 |
| `data_quality_rules.yaml` | implement | SCHEMA_DRIFT | 无 |
| `resource_limits.yaml` | implement | 有界读取 | 无 |
| `test_db_validation_gate.py` | implement + §5.3 | 缺 hash 负向 | 无 |
| `test_adapter_skeletons.py` | implement + §5.3 | CSV/Parquet/corrupt | 无 |
| `test_data_adapter_contract.py` | implement | 契约回归 | 无 |
| `test_data_quality_validator.py` | implement | 邻接回归 | 无 |
| `docs/modules/data_validation_and_conflict.md` | implement | 模块语义 | 无 |
| `BATCH_3V_HARDENING_RULES.md` | MASTER §1.4 | 禁 production write | 无 |
| Registry 三件套 | 只读标注 | B02-DATA-05 主会话 | 无（刻意 deferred） |
| `adapters/registry.py` | implement 邻接 | 只读对照 | 无 |

**复检**: 遗漏风险列均为「无」或「刻意 deferred」。
