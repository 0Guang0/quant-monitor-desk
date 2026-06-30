# Audit matrix — R3-DCP-03 post-write inspect

> **追溯：** 活卡 `R3_DCP_03_POST_WRITE_INSPECT.md` · `DEBT.plan.md` · `research/reference-adoption-dcp03.md`

| 维度            | 状态     | 范围 / 理由                                                                                                                                                           |
| --------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A1 正确性**   | 必做     | 2× incremental 后 **`DbInspector` 报告** `security_bar_1d.row_count` 稳定；`max(trade_date)` 断言；incremental 会话后 evidence bundle → health profile 不抛未处理异常 |
| **A2 可读性**   | 必做     | 测试五字段 docstring；参考采纳与仓内复用注释分明（**禁止**把仓内代码标 L1/L2/L3）；无重复 inspect 实现                                                                |
| **A3 架构**     | 必做     | E2/F0 只读边界；不改 sync 金路径；测试编排不嵌入 runner 默认 hook                                                                                                     |
| **A4 安全**     | 必做     | 隔离库；禁止 canonical 写；inspect 无自由 SQL；无 live fetch 副作用                                                                                                   |
| **A5 测试**     | 必做     | `test_incremental_post_write_inspect.py` RED→GREEN；`test_catalog` 登记                                                                                               |
| **A6 性能**     | **SKIP** | 单库单表抽检；无全库 scan SLA                                                                                                                                         |
| **A7 GitNexus** | 必做     | 若触 `db_inspector` 则 impact；默认仅新测文件                                                                                                                         |
| **A8 证据**     | 必做     | `execute-evidence/s01–s03-green.txt`；pytest 全绿                                                                                                                     |

---

## A6 SKIP 理由

写后抽检在隔离库、单 instrument replay 路径；`DbInspector` 已有 contract limit；无新产品化批量 inspect。

---

## Execute 后派发

A1–A8 各一报告 → A9 Repair ledger → 关账 → Wave 3 CLOSED。
