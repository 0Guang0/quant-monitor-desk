# S08 Execute — 参考项目实读证据

> **Date:** 2026-07-02 · **Slice:** S08-BOOT..E2E

## 实读范围

| 路径                                 | 结果                                                                   |
| ------------------------------------ | ---------------------------------------------------------------------- |
| `参考项目/OpenBB/.../fetcher.py`     | worktree 内 **无** `参考项目/` 目录；主仓亦未索引到可直拷 breadth 模块 |
| `参考项目/digital-oracle/.../bis.py` | 同上 — 不可用                                                          |

## 采纳决策（对齐 `reference-adoption-dcp08.md`）

- Layer4 breadth / calendar：**L3 greenfield** — 仓内 `clean_read.py` 从 `security_bar_1d` 聚合
- OpenBB Fetcher 三阶段：architecture_only，**不** runtime import
- US 日历：仓内 `us_trading_calendar.py`（R3H-07 SSOT）
- Tier A bootstrap：仓内 `tests/layer1_clean_e2e_support.py` 模式复制

## copy/rewrite

| 参考                     | 决策                                                    |
| ------------------------ | ------------------------------------------------------- |
| 外部 breadth 模块        | **rewrite** — ponytail advancers/decliners/total_amount |
| layer1_clean_e2e_support | **仓内承接** — `layer4_clean_e2e_support.py`            |
