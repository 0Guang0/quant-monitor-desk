# Plan Boot — R3H-01 Official Macro Disclosure Adapters

> **Phase P0 complete** · 2026-06-28

## 批次定位

| 项           | 值                                                                                  |
| ------------ | ----------------------------------------------------------------------------------- |
| Batch        | `ROUND_3_REAL_DATA_PRODUCTION_ENTRY` / Batch 3H                                     |
| Task ID      | `R3H-01`                                                                            |
| Trellis slug | `06-28-round3h-r3h01-official-macro`                                                |
| 协议         | v4 (`plan_protocol_version: "4"`)                                                   |
| 前置         | Batch 3G CLOSED @ `01465a7c`；mass rehearsal 索引 `R3G_MASS_REHEARSAL_OPEN_GAPS.md` |
| 禁止提前     | **R3H-05** Layer binding audit；主库 `quant_monitor.duckdb` 写入（无 gate/ADR）     |

## 已读 P0 输入（按用户指定顺序）

| #   | 文件                                                 | 摘要                                                 |
| --- | ---------------------------------------------------- | ---------------------------------------------------- |
| 1   | `agent-toolchain.md`                                 | GitNexus impact/query 优先；Plan→freeze→Execute      |
| 2   | `PROJECT_IMPLEMENTATION_ROADMAP.md` §4.6、§5.0       | 3G→3H 映射；G10→R3H-01 fred                          |
| 3   | `docs/implementation_tasks/README.md`                | Round 3H 为当前下一执行入口                          |
| 4   | `R3G_MASS_REHEARSAL_OPEN_GAPS.md`                    | G1–G17 全表；G10 FRED 证据分裂为 R3H-01 首优         |
| 5   | `BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md`      | 全目标 source 须 READY_WITH_EVIDENCE 或 ADR_DISABLED |
| 6   | `BATCH_3H_TASK_CARD_MANIFEST.md`                     | R3H-01~04 可并行；R3H-05 最后                        |
| 7   | `BATCH_3H_COORDINATOR_PLAYBOOK.md`                   | 合并顺序与共享文件协调                               |
| 8   | `BATCH_3H_HARDENING_RULES.md`                        | 禁止微切片 closure                                   |
| 9   | `research/r3g03_mass_rehearsal_report.md`            | pilot 五源 PASS；FRED 须 bridge                      |
| 10  | `specs/contracts/reference_adoption_guardrails.yaml` | L1/L2/L3 采纳阶梯                                    |
| 11  | `specs/contracts/sandbox_clean_write_contract.yaml`  | 3G caps；3H 产品化须 supersede pilot bridge          |
| 12  | `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`       | 活任务卡（6 source 闭环）                            |
| 13  | `.cursor/skills/trellis-plan/SKILL.md`               | v4 冻结三件套流程                                    |

## 3G→3H 首切片（G10）

**问题：** R3E `fred_live_fetch_evidence.json`（`series[].rows` + `observation_date`）≠ promote `fred_evidence.json`（`observations[].date`）；`live_evidence_bridge.materialize_fred_promote_evidence` + DH sidecar 为 **pilot 专用**。

**R3H-01 目标：** 统一证据契约，使 fetch port / live pilot / promote loader **同一 schema**，无需 bridge sidecar；保留 bridge 仅作 3G 运维兼容或删除并迁移测试。

**关键代码（当前）：**

- `backend/app/ops/sandbox_clean_write/live_evidence_bridge.py` — pilot 物化
- `backend/app/ops/sandbox_clean_write/rehearsal_loader.py` — `_fred_staging_rows` 读 `fred_evidence.json`
- `scripts/r3g03_isolated_pilot_dry_run.py` — `--live-wire` 入口
- **缺失：** `backend/app/datasources/fetch_ports/fred_port.py`（活卡 §4 目标路径尚不存在）

## 任务边界（一句话）

将官方宏观/披露六源（`fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`）从 staged/proposed-disabled 推进到 `READY_WITH_EVIDENCE` 或 `ADR_DISABLED_OUT_OF_SCOPE`；首步闭合 G10 FRED 证据分裂，再逐源 adapter/gate/route/replay。

## 明确不做

- 写 `data/duckdb/quant_monitor.duckdb`（无 Batch 3H gate/ADR）
- 运行时 import `参考项目/**` 或拷贝 OpenBB AGPL provider
- R3H-05 层绑定审计（本任务禁止）
- 全市场/全历史 macro series 默认拉取
- 把 3G pilot 预演数据 merge 进主库

## GitNexus（Plan 1a/1b）

- `query("FRED promote evidence loader")` — 命中 live_pilot_phase3、batch25/275 策略测试；**未索引** `live_evidence_bridge`（索引可能滞后）
- `impact(materialize_fred_promote_evidence)` — UNKNOWN（符号未入索引）；静态 grep 确认调用方：`r3g03_isolated_pilot_dry_run.py`、`test_round3g_limited_production_clean_write.py`

## context_pack

`uv run python scripts/context_router.py --task .trellis/tasks/06-28-round3h-r3h01-official-macro` — 已生成（modules 空，Execute boot 须刷新）。

## Phase 3（grill-me）

- 产出：`research/grill-me-session.md`（**Phase 3 complete**）
- 活卡加固：`R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md` §7–§15，§9 共 9 步（9.0–9.8 索引对齐）
- 追溯：`research/original-plan-trace.md`
