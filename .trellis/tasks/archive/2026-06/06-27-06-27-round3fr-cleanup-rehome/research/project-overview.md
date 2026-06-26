# Project Overview — R3FR-07

> Phase 1a · GitNexus query + codebase read

## 任务在总路线图中的位置

```text
历史底座 (Round0–3V, 3F) ✅
  → Batch 3F-R (R3FR-01~06 ✅)
  → R3FR-07 cleanup ← 当前 Plan
  → Batch 3G (R3G-01→02→03 串行)
  → Batch 3H (4 分支并行 + R3H-05 最后)
```

## 业务价值

3F-R 的前六张卡已把参考采纳落成真实 runtime（data health profile、CLI、TDX port、provider catalog）。若不在 R3FR-07 关门：

- 规划文档仍指向 placeholder，Execute agent 会重复做已完成工作；
- 3G 门禁语义上仍「被 3F-R 阻塞」；
- 薄 wrapper 可能被误当作扩展点，导致微切片回归。

R3FR-07 的价值是 **治理收尾**：redirect + 索引一致性 + 测试锁门，不是新能力。

## 核心清理对象（四模块 + 四文档层）

| 层           | 对象                          | 做到什么程度                                                           |
| ------------ | ----------------------------- | ---------------------------------------------------------------------- |
| Runtime shim | `check_daily_bars`            | 保留证据路径兼容；文档指向 `run_data_health_profile` / `market_bar_p0` |
| CLI          | `health_check`                | 已实现；仅补注释 + 文档 guardrail                                      |
| TDX          | `TdxPytdxProbeFetchPort`      | 保持委托；禁止再长 pytdx 逻辑                                          |
| 编排         | `tdx_manual_probe`            | 注释标明 orchestration-only                                            |
| 规划         | ROADMAP / HANDOFF / 3G README | 3F-R CLOSED；3G 下一入口                                               |
| 评级         | `MODULE_COMPLETION_RATING`    | provider catalog 反映 R3FR-05 合并                                     |

## 架构边界（不变）

```text
DataSourceService / SourceRoutePlanner  ← 唯一生产路由
WriteManager / DbValidationGate         ← 写边界
run_data_health_profile (read-only)     ← CLI + profile canonical
TdxPytdxFetchPort (disabled/raw-only)   ← TDX canonical
provider_catalog.yaml                   ← source 元数据 SSOT
```

## 风险

| 风险                                  | 缓解                                                              |
| ------------------------------------- | ----------------------------------------------------------------- |
| DRY `check_daily_bars` 改变行为       | TDD：先跑 `test_ops_data_health` RED/GREEN；仅委托已测 OHLCV 函数 |
| 文档-only 被当成「假完成」            | 新增 `test_r3fr07_*` 对关键路径做静态断言                         |
| 与 master 上未 push 的 19 commit 分叉 | 基于当前 `master` 开 `chore/round3fr-cleanup-rehome`              |
