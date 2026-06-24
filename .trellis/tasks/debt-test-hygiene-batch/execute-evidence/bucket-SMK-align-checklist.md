# 桶 SMK — Phase A align-checklist

**模块：** `tests/smoke/test_foundation_smoke.py`  
**分支：** `debt/test-hygiene/bucket-smk-smoke`  
**Agent：** agent-SMK

## `test_foundation_endToEnd_writesCleanAndAudits`

| #   | 五问                                                  | 结论  | 说明                                                                                                              |
| --- | ----------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------- |
| 1   | 注释中的**被测对象**是否就是代码 import/call 的对象？ | **Y** | 调用 `apply_migrations`、`ResourceGuard`、`RawStore`、`FileRegistry`、`create_test_write_manager`（WriteManager） |
| 2   | 注释中的**验证点**是否被 assert/raises/match 覆盖？   | **Y** | 001/002 迁移名与 `FOUNDATION_TABLES`；WARN→log count=1；SUCCESS 行数+audit；FAILED 不增行+failed audit=1          |
| 3   | **失败含义**是否与 assertion 粒度一致？               | **Y** | 各环节独立断言，任一断裂即失败                                                                                    |
| 4   | 是否有注释**未声称**的额外行为？                      | **Y** | 无；OK guard 路径与注释「资源 WARN/OK」一致                                                                       |
| 5   | 是否已复用 conftest/db_helpers/同桶模式？             | **Y** | 使用 `create_test_write_manager`；Phase A 复用单一 `wm` 实例替代三次重复构造                                      |

## ponytail 改动摘要

- 引入 `wm = create_test_write_manager(cm)`，供 `FileRegistry` 与两次 `write` 复用（删重复 setup，测试价值不变）
- 未改任何注释文本
- 未删/弱化断言

## 汇总

- 用例数：1
- 全 Y：是
- comment-conflicts：none
