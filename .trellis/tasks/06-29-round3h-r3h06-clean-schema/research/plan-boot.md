# Plan Boot — R3H-06 Clean Schema (Wave 1)

> **Phase P0 complete** · 2026-06-29

## 批次定位

| 项           | 值                                                             |
| ------------ | -------------------------------------------------------------- |
| Batch        | `ROUND_3_REAL_DATA_PRODUCTION_ENTRY` / Batch 3H PASS 收口      |
| Task ID      | `R3H-06`                                                       |
| Wave         | **Wave 1**（串行；阻塞 Wave 3）                                |
| Trellis slug | `06-29-round3h-r3h06-clean-schema`                             |
| 协议         | v4                                                             |
| 前置         | Wave 0 Batch 3V **CLOSED** @ 2026-06-28；R3H-01～04 **CLOSED** |
| 禁止提前     | R3H-05 审计；R3H-08 live；主库写入                             |

## 已读 P0 输入

| #   | 文件                                                       | 摘要                                                  |
| --- | ---------------------------------------------------------- | ----------------------------------------------------- |
| 1   | `agent-toolchain.md`                                       | GitNexus query/impact；Plan 5e 三件套                 |
| 2   | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.1–§5.0.5          | PASS 波次；R3H-06 闭合 G3/G4/G5/G6                    |
| 3   | `docs/implementation_tasks/README.md`                      | 条目 11：PASS 收口顺序                                |
| 4   | `R3H_PASS_EXECUTION_PLAN.md`                               | Wave 1 范围；DDL 独占                                 |
| 5   | `R3G_MASS_REHEARSAL_OPEN_GAPS.md` §2                       | G3–G6 仍 ❌/⚠️                                        |
| 6   | `BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md`            | 3H 门禁（注：PASS 计划覆盖「R3H-05 当前入口」旧叙事） |
| 7   | `BATCH_3H_HARDENING_RULES.md`                              | 禁止微切片                                            |
| 8   | `GLOBAL_EXECUTION_RULES.md` ×3 + `GLOBAL_TASK_TEMPLATE.md` | 边界/TDD                                              |
| 9   | `TASK_INPUT_CONTEXT_INDEX.md`                              | Plan 桥接                                             |
| 10  | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                       | 批次索引（checkpoint 旧；PASS 计划为准）              |
| 11  | `MIGRATION_MAP.md`                                         | schema 实现目录                                       |
| 12  | `docs/schema/MIGRATION_COVERAGE.md`                        | `security_bar_1d` DEFERRED → 本卡 owner               |
| 13  | `specs/schema/schema.sql`                                  | `security_bar_1d` + `axis_observation` 设计           |
| 14  | `R3H_06_CLEAN_SCHEMA.md`                                   | 活任务卡                                              |
| 15  | `.cursor/skills/trellis-plan/SKILL.md`                     | v4 流程                                               |

## 任务边界（一句话）

交付三域 clean DDL（bar/disclosure/macro→axis_observation）、OHLCV、cninfo 原生形、PK/upsert 幂等；替换 pilot `market_bar_clean` 单表偏离。

## 明确不做

- R3H-08 env-gated live 产品化
- R3H-07 US 日历 / R3H-10 staged SSOT
- R3H-05-GATE PASS 裁决
- Layer3/4 migration（Round 3F）
- 主库 `quant_monitor.duckdb` 写入

## GitNexus（Plan 1a/1b）

- `query("clean schema market_bar")` — 命中 validation_gate、sync `_write_clean`、pilot ports
- `query("cninfo disclosure promote")` — 命中 staged_pilot_fetch_ports、cninfo_port
- **索引滞后：** `market_bar_clean` 多为测试/SQL 字符串，非符号

## context_pack

`uv run python scripts/context_router.py --task .trellis/tasks/06-29-round3h-r3h06-clean-schema`

## Phase 3（grill-me）

- 产出：`research/grill-me-session.md`（**Phase 3 complete**）
- 用户裁决 @ 2026-06-28（PASS 路径）已覆盖主库/live 范围；本卡仅补 schema 形态锁定
