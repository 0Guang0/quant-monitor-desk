# Integration Audit — R3H-07（Plan 5d）

## CLAIM → DOUBT → RECONCILE

| CLAIM                    | DOUBT             | RECONCILE                                  |
| ------------------------ | ----------------- | ------------------------------------------ |
| CN 镜像即可闭合 US       | 美股假日规则不同  | ADR-026 独立模块；API 对称                 |
| 只改 window_kind 字段    | span 仍自然日     | S07-02 同时改 `fetch_window` + bar 过滤    |
| Layer4 必须 full US live | `L4-US-DEFERRED`  | S07-03 仅 calendar 绑定                    |
| Service 已闭合窗口       | R3H-10 只闭合入口 | 窗口语义在 evidence；S07-02 service 测扩展 |

## 六类检查（Plan 期）

| 类   | 状态           | 备注                                       |
| ---- | -------------- | ------------------------------------------ |
| 契约 | PASS           | ADR-026 · R3H-10 service 承接              |
| 测试 | PASS_WITH_GAPS | 切片测名在 to-issues；Execute 写 RED/GREEN |
| 安全 | PASS           | 无 secrets；有界日历                       |
| 架构 | PASS           | 单 SSOT；CN 隔离                           |
| 文档 | PASS           | ENTRY + matrix + trace                     |
| 运维 | PASS           | 无 migration                               |

## adversarial（对抗性审计）

| 检查项                               | 结果 | 修复                             |
| ------------------------------------ | ---- | -------------------------------- |
| plan-doubt-review D1–D8              | PASS | `plan-doubt-review.md` RECONCILE |
| ADR-026 与 S07-01 绑定               | PASS | ENTRY §4                         |
| CN 隔离不回退                        | PASS | 专用回归测 AC-CN-REG             |
| R3H-10 Wave 2 defer 未 silent bypass | PASS | ENTRY §2 承接表                  |

## doc-gap（Execute 期闭合）

| GAP                           | 绑定切片  |
| ----------------------------- | --------- |
| `us_trading_calendar.py` 实现 | S07-01    |
| 三源 `trading_sessions`       | S07-02    |
| Layer4 US 假日拒绝            | S07-03    |
| 假日负向 RED→GREEN            | S07-04    |
| `CAL-US` registry             | S07-CLOSE |

## closure

**PASS_WITH_GAPS** — Plan 对抗项已 reconcile；实现 GAP 由 Execute S07-BOOT..CLOSE 闭合。

**Phase 5d complete**
