# CAL-US 自然日窗基线矩阵（S07-BOOT）

> **角色：** 类似 R3H-10 `bypass-baseline-matrix.md`；登记 US 源窗口语义缺口。

| #   | 入口                                   | 当前 window_kind / 窗语义                                 | 旁路/缺口                  | 目标切片   |
| --- | -------------------------------------- | --------------------------------------------------------- | -------------------------- | ---------- |
| 1   | `yahoo_finance_port.fetch_payload`     | 自然日 `timedelta` mock bars；bundle 默认 `calendar_days` | 假日 bar 可生成            | S07-02     |
| 2   | `stooq_port.fetch_payload`             | 同上                                                      | 同上                       | S07-02     |
| 3   | `alpha_vantage_port.fetch_payload`     | 同上；option chain 显式 `calendar_days`                   | US equity bar 域           | S07-02     |
| 4   | `fetch_window.recent_window_start`     | `calendar_days` only                                      | 无 trading session 变体    | S07-02     |
| 5   | `build_daily_bar_evidence_bundle`      | default `window_kind=calendar_days`                       | US 未覆盖                  | S07-02     |
| 6   | `test_market_data_adapters` R3H02-R-22 | 断言 `calendar_days`                                      | 与 CAL-US 冲突             | S07-02     |
| 7   | `MarketStructureBuilder` US_EQ         | staged fixture only；无 `us_trading_calendar`             | 假日拒绝未绑定 SSOT        | S07-03     |
| 8   | `layer4_market_source_plan.yaml` L4-US | `deferred`                                                | calendar 语义本卡闭合      | S07-03     |
| 9   | `DataSourceService.fetch`              | R3H-10 金路径 ✅                                          | 窗口语义在 evidence 层闭合 | S07-02     |
| 10  | `cn_trading_calendar`                  | `calendar_authority` ✅                                   | **不得回退**               | 全切片回归 |

## OPEN → CLOSED 追踪

| 项                      | BOOT            | CLOSE 目标         |
| ----------------------- | --------------- | ------------------ |
| US 三源 `calendar_days` | OPEN            | `trading_sessions` |
| US 假日负向             | OPEN            | S07-04 GREEN       |
| CN 回归                 | CLOSED @ R3H-03 | 保持 CLOSED        |
