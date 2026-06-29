# Original Plan Trace — R3H-07

> 活卡 / INDEX AC → `EXECUTION_INDEX.md` §2 映射

| 活卡 / INDEX 来源                                | EXECUTION_INDEX §2 AC | 切片           |
| ------------------------------------------------ | --------------------- | -------------- |
| `CAL-US` = CLOSED                                | AC-CLOSE              | S07-CLOSE      |
| US 源 window_kind / orchestrator 交易日历        | AC-02                 | S07-02         |
| `test_layer4_market_structure.py` + 日历专项测绿 | AC-03                 | S07-03, S07-04 |
| CN 日历 R3H-03 不破坏                            | AC-CN-REG             | 全切片回归     |
| 经 DataSourceService 暴露/验证窗口语义           | AC-SVC                | S07-02         |
| 禁止万年历无 cap                                 | AC-BOUND              | S07-01         |
| 禁止 R3H-06 新 migration                         | AC-NO-DDL             | 全切片         |
| 美股假日窗 RED→GREEN                             | AC-04                 | S07-04         |
| Out: R3H-08 live                                 | —                     | Out of scope   |
| Out: 新 clean DDL                                | —                     | ADR-026        |

**活卡：** `R3H_07_US_TRADING_CALENDAR.md`  
**INDEX：** `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md` §2
