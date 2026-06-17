# ROUND 2 DATA INGESTION VALIDATION

本目录包含 6 个正式 implementation task 文件（011–016）。**Execute 按四批次进行**（每批独立 Trellis 复杂任务 Plan → Execute → Audit → Finish）。

## Round 2 目标

建立数据源接入与校验底座：

1. **能注册、能契约化抓取**：source_registry + Adapter contract + fetch_log
2. **能挂接多源 skeleton**（Batch B）
3. **能质量检查与冲突治理**（Batch C），替换 stub ValidationGate
4. **能编排同步任务**（Batch D）

## 四批次 Execute 顺序

| 批次 | 任务 | Trellis slug（Plan） | 深度计划 |
|------|------|----------------------|----------|
| **A** | 011+012 | `06-17-round2-batch-a-sources` | MASTER §8（`plans/` 仅索引） |
| B | 013 | （Plan 待建） | `plans/013_*.plan.md` |
| C | 015+016 | （Plan 待建） | `plans/015_016_*.plan.md` |
| D | 014 | （Plan 待建） | `plans/014_*.plan.md` |

## 执行前必读

- `../GLOBAL_EXECUTION_RULES.md`
- `../GLOBAL_TESTING_POLICY.md`
- `../GLOBAL_RESOURCE_LIMITS.md`
- `../GLOBAL_TASK_TEMPLATE.md`
- `./DECISIONS.md` — 本轮已确认决策（**先读**）

## 任务清单

| 编号 | 任务 | Batch |
|------|------|-------|
| 011 | source_registry | A |
| 012 | data adapter contract | A |
| 013 | core adapter skeletons | B |
| 014 | data sync orchestrator | D |
| 015 | data quality validator | C |
| 016 | source conflict validator | C |

## Batch A Checkpoint（011+012 完成后）

- [x] `pytest -q` 全绿（**173** passed @ `9adef12`）
- [x] migration **004** 已应用（003 resource_guard 保留）
- [x] YAML 加载 + legacy 角色拒绝（含顶层 banned key）
- [x] fetch 失败仍写 fetch_log
- [x] GPT P0 `SourceMismatchError`（`ab8d1eb`）

**Batch A 已完成** — 可进入 Batch B Plan。延后项见 `DECISIONS.md` §9。

## Plan / Execute 状态

| 批次 | Plan | Execute | Audit | GPT 硬ening |
|------|------|---------|-------|-------------|
| A | ✅ 已冻结 | ✅ `ee48187` | ✅ PASS | ✅ `ab8d1eb` |
| B–D | 未开始 | 未开始 | — | — |

Trellis 任务目录：`.trellis/tasks/archive/2026-06/06-17-round2-batch-a-sources/`
