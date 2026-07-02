# Plan Context — R3-DCP-09

## Context Hierarchy

> **注：** 下表 L1–L5 为 **上下文层级**（活卡→切片→源码），与 `reference-adoption-dcp09.md` 的 **参考采纳 L1/L2/L3**（仅 `参考项目/**`）不同维度。

| Level | 内容                                              |
| ----- | ------------------------------------------------- |
| L1    | 活卡 §1–§3 · ADR-030 · orchestrator §backfill     |
| L2    | `to-issues-slices.md` · `bounded_backfill_cap.yaml` |
| L3    | `jobs.py` · `runners.py` · `data_commands.py`     |
| L4    | 当前切片 § + execute-reference-read-evidence      |
| L5    | pytest / nightly 本地复现命令                     |

## PROJECT CONTEXT（Execute 可复制）

- **金路径：** `qmd data backfill` → `run_backfill` → `BackfillShardRunner` → DataSourceService
- **Cap：** 31 天/片 × 默认 max 3 shards；超范围 fail-closed
- **CI 分层：** PR = replay；nightly = `--run-network` + live acceptance
- **隔离：** `QMD_DATA_ROOT` 子目录；主库 fingerprint 不变

## Level 3 源码表

| 切片 | 必读源码                                              |
| ---- | ----------------------------------------------------- |
| S00  | `jobs.py:plan_backfill_shards` · cap yaml              |
| S01  | `data_commands.py:sync_*` 先例 · `orchestrator.run_backfill` |
| S02  | `test_sync_orchestrator.py` backfill 测               |
| S03  | `wave3_isolated_production_acceptance.py` steps 表    |
| S04  | `ci.yml` · `conftest.py --run-network`                |
| S05  | `wave3_live_production_acceptance.py` findings 逻辑   |

## 开工必读 vs 情境路由

- **开工必读：** ENTRY §1–§4 · `to-issues-slices.md` 当前行 · `reference-adoption-dcp09.md` · ADR-030
- **S04 情境：** Read `docs/ops/nightly_ci.md` + workflow yaml
- **S05 情境：** Read `docs/quality/production_live_pilot_policy.md`
