# R3-DCP-02 — fred macro incremental

> **协议：** debt-lite Phase 8D · **Plan SSOT：** `DEBT.plan.md` + `research/reference-adoption-dcp02.md`  
> **活卡：** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_02_FRED_INCREMENTAL.md`

---

## 目标（人话）

FRED 宏观序列走产品增量：读库最新观测日 → 只拉新点 → 写 macro clean（`axis_observation`）→ CLI 可重复跑。

---

## 价值

- Wave 3 轨 B 试点；验证宏观 watermark（非 `trade_date`）
- 承接 R3H-08C fred live port → 产品增量

---

## Acceptance criteria（活卡 §5）

| #   | AC                                               | 验证                                       |
| --- | ------------------------------------------------ | ------------------------------------------ |
| 1   | fred watermark 单测（空表 / 有观测 / 多 series） | `test_fred_macro_incremental_watermark.py` |
| 2   | replay + env-gated live smoke（隔离库）          | `test_fred_macro_incremental_e2e.py`       |
| 3   | 幂等：重复跑不增行                               | `-k idempotent`                            |
| 4   | `research/reference-adoption-dcp02.md` L1/L2/L3  | Plan 产物                                  |
| 5   | Audit A1–A8 + Repair ledger 关账                 | `AUDIT.plan.md`                            |
| 6   | `uv run pytest -q` exit 0                        | merge gate                                 |

---

## 约束摘要

- 金路径：`DataSourceService.fetch` + `DataSyncOrchestrator.run_incremental`
- 授权：`FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH`；负例 `USER_AUTH_REQUIRED`
- 数据根：隔离 `QMD_DATA_ROOT`；禁止 canonical 主库 silent write
- Watermark：per `series_id` / `indicator_id` + `observation_date` 语义
- 禁止：改 `baostock_port`、CN equity clean、轨 A 拥有文件

---

## Execute 切片（5）

| Slice  | 内容                                                       |
| ------ | ---------------------------------------------------------- |
| S02-01 | fred watermark reader + 单测                               |
| S02-02 | `fred_port` 增量窗（`start_time`）                         |
| S02-03 | replay e2e orchestrator → `axis_observation`               |
| S02-04 | env-gated live smoke + 幂等                                |
| S02-05 | `qmd data sync --domain macro_series --source-id fred` CLI |

详见 `DEBT.plan.md`。

---

## 非目标

- 宏观六源全量增量（Wave 4）
- 新 FRED series UI · SEC/CFTC
- 新 migration

---

## 关联 research

- `research/plan-boot.md` — 上下文复述
- `research/reference-adoption-dcp02.md` — L1/L2/L3
- `research/architecture-dcp02.md` — 架构图与契约
- `research/grill-me-session.md` — 澄清记录（无未决）
