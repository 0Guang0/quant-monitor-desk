# R3H-02 Market Data Adapters — PRD（薄索引）

> `thin-index: true` · Execute 读 `frozen/R3H_02_MARKET_DATA_ADAPTERS.md` + `EXECUTION_INDEX.md`

## 目标

闭合五源：`alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko` → `READY_WITH_EVIDENCE` 或 `ADR_DISABLED_OUT_OF_SCOPE`。

## 价值

Round4 前跨资产/美股/加密行情 adapter 与 route 可验收；yahoo 保持 validation-only；聚合源不得 silent primary。

## 权威文档

| 文档     | 路径                                                           |
| -------- | -------------------------------------------------------------- |
| 活任务卡 | `docs/implementation_tasks/.../R3H_02_MARKET_DATA_ADAPTERS.md` |
| 冻结卡   | `frozen/R3H_02_MARKET_DATA_ADAPTERS.md`                        |
| 执行索引 | `EXECUTION_INDEX.md`                                           |
| 审计矩阵 | `AUDIT.plan.md`                                                |

## AC 摘要

见 `EXECUTION_INDEX.md` §2 与 §0.1 血缘表。

## 禁止

主库写入；R3H-05；yahoo 升格 primary；全市场/全期权链默认。
