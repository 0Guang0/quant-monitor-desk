# Plan Boot — R3H-02 Market Data Adapters

> **Phase P0 complete** · 2026-06-28

## 批次定位

| 项           | 值                                                                              |
| ------------ | ------------------------------------------------------------------------------- |
| Batch        | `ROUND_3_REAL_DATA_PRODUCTION_ENTRY` / Batch 3H                                 |
| Task ID      | `R3H-02`                                                                        |
| Trellis slug | `06-28-06-28-round3h-r3h02-market-data`                                         |
| 协议         | v4 (`plan_protocol_version: "4"`)                                               |
| 前置         | **R3H-01 CLOSED** @ 2026-06-28；Batch 3G CLOSED                                 |
| 禁止提前     | **R3H-05** Layer binding audit；主库 `quant_monitor.duckdb` 写入（无 gate/ADR） |

## 已读 P0 输入

| #   | 文件                                            | 摘要                                                 |
| --- | ----------------------------------------------- | ---------------------------------------------------- |
| 1   | `agent-toolchain.md`                            | GitNexus impact/query 优先；Plan→freeze→Execute      |
| 2   | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0        | R3H-01 CLOSED；**当前入口** R3H-02~04 并行           |
| 3   | `docs/implementation_tasks/README.md`           | Round 3H 执行入口                                    |
| 4   | `R3G_MASS_REHEARSAL_OPEN_GAPS.md`               | G2/G13/G16 → yahoo fixture；交易日窗开放             |
| 5   | `BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md` | 全目标 source 须 READY_WITH_EVIDENCE 或 ADR_DISABLED |
| 6   | `BATCH_3H_TASK_CARD_MANIFEST.md`                | R3H-02 拥有五源 market/crypto                        |
| 7   | `BATCH_3H_COORDINATOR_PLAYBOOK.md`              | 并行 ownership + registry 合并                       |
| 8   | `BATCH_3H_HARDENING_RULES.md`                   | 禁止微切片 closure                                   |
| 9   | `R3H_02_MARKET_DATA_ADAPTERS.md`                | 活任务卡（5 source 闭环）                            |
| 10  | `R3H_01` 归档三件套                             | 模式参照：normalizer + fetch_port + §9.6 coordinator |
| 11  | `.cursor/skills/trellis-plan/SKILL.md`          | v4 冻结三件套流程                                    |

## 首切片问题（五源 baseline）

**问题：** 五源在 registry 有定义，但除 yahoo skeleton adapter + 3G fixture 外，**无** `fetch_ports/*`、**无** `market_data`/`crypto_market` normalizer、capabilities 仍为 `proposed_disabled_source`。

**R3H-02 目标：** mock/replay-first fetch port + evidence normalizer + route READY/DISABLED + registry 终态；yahoo **保持 validation-only**。

## 任务边界（一句话）

将跨资产/美股/加密五源（`alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`）从 scaffold/proposed-disabled 推进到 `READY_WITH_EVIDENCE` 或 `ADR_DISABLED_OUT_OF_SCOPE`；聚合/验证源不得 silent primary。

## 明确不做

- 写 `data/duckdb/quant_monitor.duckdb`
- 运行时 import `参考项目/**` 或拷贝 OpenBB AGPL provider
- R3H-05 层绑定审计
- yahoo 升格 primary（无 ADR）
- 全市场/全历史/分钟线/全期权链默认
- 完整 EasyXT TradingCalendar（G2 SSOT → 与 R3H-03 协调；本卡 ponytail 自然日窗）

## GitNexus（Plan 1a/1b）

- `query("market data fetch port yahoo route planner")` — 命中 `DataSourceService.fetch`, `route_planner`, `staged_pilot`, yahoo rehearsal_loader 路径
- **风险预判：** MEDIUM — 触及 route/capabilities/3G yahoo bundle

## context_pack

`uv run python scripts/context_router.py --task .trellis/tasks/06-28-06-28-round3h-r3h02-market-data` — Plan 阶段生成。

## Phase 3（grill-me）

- 产出：`research/grill-me-session.md`（**Phase 3 complete**）
- 活卡加固：`R3H_02_MARKET_DATA_ADAPTERS.md` §1.1–§15
- 追溯：`research/original-plan-trace.md`
