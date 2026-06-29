# 执行索引 — R3H-07 US Trading Calendar L2（Plan v4.1）

> Execute 读 `research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                            |
| ------------- | ------------------------------------------------------------- |
| slug          | `06-29-round3h-r3h07-us-trading-calendar`                     |
| protocol      | `4.1`                                                         |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                              |
| source_card   | `docs/implementation_tasks/.../R3H_07_US_TRADING_CALENDAR.md` |
| frozen_card   | `frozen/R3H_07_US_TRADING_CALENDAR.md`                        |
| blocked_by    | R3H-10 CLOSED @ `227e0734`                                    |

## 1. 步骤与证据（Execute）

| Step | 切片     | RED    | GREEN  | 证据路径                               |
| ---- | -------- | ------ | ------ | -------------------------------------- |
| 9.0  | S07-BOOT | 见切片 | 见切片 | `execute-evidence/9.0-{red,green}.txt` |
| 9.1  | S07-01   | 见切片 | 见切片 | `execute-evidence/9.1-{red,green}.txt` |
| 9.2  | S07-02   | 见切片 | 见切片 | `execute-evidence/9.2-{red,green}.txt` |
| 9.3  | S07-03   | 见切片 | 见切片 | `execute-evidence/9.3-{red,green}.txt` |
| 9.4  | S07-04   | 见切片 | 见切片 | `execute-evidence/9.4-{red,green}.txt` |

## 2. AC ↔ 测试 / 验收

| AC ID     | INDEX / 活卡来源                        | 测试 / 命令                                    | 通过条件                       | 切片      |
| --------- | --------------------------------------- | ---------------------------------------------- | ------------------------------ | --------- |
| AC-BOOT   | 基线自然日窗缺口                        | `calendar-baseline-matrix.md` + BOOT RED 测    | 矩阵齐全 · RED 证明缺口        | S07-BOOT  |
| AC-01     | US 日历 SSOT 行集（有界）               | S07-01 新建 `test_us_trading_calendar*` 模块测 | 假日/交易日 API 绿             | S07-01    |
| AC-02     | US 源 window_kind / fetch plan 交易日历 | `test_market_data_*` · service fetch 测        | `window_kind=trading_sessions` | S07-02    |
| AC-03     | Layer4 日历专项测绿                     | `tests/test_layer4_market_structure.py`        | US 假日拒绝 + 交易日通过       | S07-03    |
| AC-04     | 美股假日窗 RED→GREEN                    | 假日负向测 + 全量 pytest                       | 假日无 bar / build 拒绝        | S07-04    |
| AC-CN-REG | CN 日历不被破坏                         | `tests/test_cn_market_adapters.py` -k calendar | 回归绿                         | 全切片    |
| AC-SVC    | 经 DataSourceService 验证窗口           | `test_datasource_service` / vendor e2e         | bundle 字段可验证              | S07-02    |
| AC-BOUND  | 禁止万年历无 cap                        | code review + 日历模块有 `_RANGE_END`          | 有界                           | S07-01    |
| AC-NO-DDL | 无 R3H-06 migration                     | git diff migrations/ 空                        | 无新 migration                 | 全切片    |
| AC-CLOSE  | `CAL-US` = CLOSED                       | audit + registry                               | G4 R3→R4 证据                  | S07-CLOSE |

切片 AC 唯一 SSOT：`research/to-issues-slices.md`

## 3. 必须读原文（manifest）

| path                                                                                                                                         | manifest  | audience | for        |
| -------------------------------------------------------------------------------------------------------------------------------------------- | --------- | -------- | ---------- |
| `docs/decisions/ADR-026-r3h07-us-trading-calendar-ssot.md`                                                                                   | must-read | execute  | S07-01..04 |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_07_US_TRADING_CALENDAR.md`             | must-read | execute  | BOOT       |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md` | must-read | execute  | AC 对照    |

## 4. 已并入冻结任务卡

| 来源 | 并入 | 摘要                          |
| ---- | ---- | ----------------------------- |
| 活卡 | 指针 | R3H-07 G4/C3 CAL-US · Wave 1b |

## 5. Audit 追溯集

| 类别   | 文件                                   |
| ------ | -------------------------------------- |
| frozen | `frozen/R3H_07_US_TRADING_CALENDAR.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`       |
| slices | `research/to-issues-slices.md`         |
