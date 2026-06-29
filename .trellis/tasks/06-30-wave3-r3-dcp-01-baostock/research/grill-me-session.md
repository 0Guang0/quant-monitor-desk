# Grill-me Session — R3-DCP-01

> **日期：** 2026-06-30 · Plan Agent

## 状态：**无未决问题**

Plan 阶段所有原可歧义点已在调研中闭合，无需用户 Grill-me。决策记录如下（供 Plan-Audit 核对）：

| # | 原问题 | 决策 | 依据 |
|---|--------|------|------|
| 1 | clean 表用哪张？ | `security_bar_1d`（`cn_equity_daily_bar`） | `clean_write_targets.py` R3H-06 SSOT |
| 2 | watermark 字段？ | `max(trade_date)`；PK 含 `adjustment_type` 时查询带默认 `none` | migration 013 + clean_write_targets |
| 3 | CN 交易日历？ | Wave 3 ponytail：**calendar day** `max+1` | 活卡未要求 G2/G17 完整日历；R3H-03 日历未完成 |
| 4 | CLI 形态？ | 扩展 `qmd data sync --data-domain cn_equity_daily_bar` + watermark 自动算窗；保留 `--dry-run` 默认 | `data_commands.sync_plan` 已有壳；R3H-10 CLI SSOT |
| 5 | `runners.py` 谁改？ | 轨 A 最小注入 date→FetchRequest；轨 B fred 只读消费 | `00-MAIN-SESSION-COORDINATOR.md` §4 |
| 6 | live vs replay？ | 默认 replay fixture；live 可选 env-gated smoke，非 AC 阻塞 | `baostock_port` replay-first |
| 7 | 参考项目树缺失？ | 引用 R3H-03/10 归档 adoption；Execute 在用户环境再 Read `参考项目/**` 若存在 | worktree 无 `参考项目/` |
| 8 | instrument 范围？ | 沿用 port `SYMBOL_WHITELIST`（≤5）；与 R3H-03 pilot 一致 | `baostock_port.py` |

## 无需追问用户

以上决策均可在活卡 / INDEX / 已有 SSOT 内推导；无产品取舍冲突。
