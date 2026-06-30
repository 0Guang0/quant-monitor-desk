# Plan 质检 §3.10 — B3V-DATA

| 路径                                           | 已入 MASTER/implement             | 摘要一句                                      | 遗漏风险                                  |
| ---------------------------------------------- | --------------------------------- | --------------------------------------------- | ----------------------------------------- |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1        | MASTER §0 Source Context          | 共用底座与文件锁                              | 无                                        |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.3        | MASTER §0 + implement L8          | B3V-DATA 必读表                               | 无                                        |
| `B02_02_schema_hash_fail_closed.md`            | original-plan-trace + MASTER §1.6 | 五切片 AC                                     | 无                                        |
| `data_adapter_contract.md`                     | implement L19 + §8 DATA-01        | 结构化 schema_hash                            | 无                                        |
| `skeleton_base.py`                             | implement L24 + §9.2              | CSV/Parquet infer                             | 无                                        |
| `validation_gate.py`                           | implement L27 + §9.3              | fail-closed                                   | 无                                        |
| `adapters/__init__.py` + `source_registry.py`  | implement L25–26 + MASTER §0 §3.3 | adapter 注册邻接（playbook registry.py 纠偏） | 无                                        |
| `write_contract.yaml`                          | implement L20 + §2.4              | schema_hash_changed                           | 无                                        |
| `data_quality_rules.yaml`                      | implement L21                     | SCHEMA_DRIFT                                  | 无                                        |
| `resource_limits.yaml`                         | implement L22                     | 有界读取                                      | 无                                        |
| `test_db_validation_gate.py`                   | implement L29 + §5.3              | 缺 hash 负向                                  | 无                                        |
| `test_adapter_skeletons.py`                    | implement L30 + §5.3              | CSV/Parquet/corrupt                           | 无                                        |
| `test_data_adapter_contract.py`                | implement L31                     | 契约回归                                      | 无                                        |
| `test_data_quality_validator.py`               | implement L32                     | 邻接回归                                      | 无                                        |
| `docs/modules/data_validation_and_conflict.md` | implement L23                     | 模块语义                                      | 无                                        |
| `BATCH_3V_HARDENING_RULES.md`                  | implement L10 + MASTER §1.4       | 禁 production write                           | 无                                        |
| Playbook §8.2 未改什么                         | MASTER §1.4 逐字                  | 负向边界                                      | 无                                        |
| Registry 三件套                                | implement L15 + MASTER §0         | B02-DATA-05 主会话                            | 无（刻意 deferred）                       |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §4          | vertical-slices + trace           | DATA-01..04 竖条                              | 无（worktree 以 vertical-slices 为 SSOT） |

**复检**: 遗漏风险列均为「无」或「刻意 deferred」。
