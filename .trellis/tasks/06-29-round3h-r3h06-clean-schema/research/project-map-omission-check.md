# Project Map Omission Check — R3H-06 Plan

> `check_docs_specs_indexed.py` + `loop_maintain.py --fix` @ 2026-06-29

## 机械检查

| 检查                                         | 结果                              |
| -------------------------------------------- | --------------------------------- |
| `R3H_06_CLEAN_SCHEMA.md` 在 docs_specs_index | ✅（loop_maintain --fix 后）      |
| `test_r3h06_clean_schema.py` 在 test_catalog | ⏳ Execute 9.0 创建后再次 `--fix` |
| authority_graph backend 包映射               | ✅ 无新包                         |
| context_pack.json                            | ✅ 已生成                         |

## 地图叙事缺口（Plan 期登记）

| 缺口                                             | 处置                                  | Owner       |
| ------------------------------------------------ | ------------------------------------- | ----------- |
| `BATCH_3H_TASK_CARD_MANIFEST.md` 未列 R3H-06～10 | 主会话 PASS merge 时补表              | coordinator |
| `BATCH_3H README` 仍写「R3H-05 当前入口」        | 与 `R3H_PASS_EXECUTION_PLAN` 对齐更新 | coordinator |
| `MIGRATION_COVERAGE` security_bar_1d DEFERRED    | Execute 9.8 改 DONE                   | R3H-06      |
| `cn_announcement_clean` 不在 schema.sql          | Execute 9.2 增表                      | R3H-06      |

## 结论

Plan 输入无阻塞遗漏；Execute 后须再跑 `loop_maintain.py`。

**Phase P0o complete**
