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
| B | 013 | `06-17-round2-batch-b-adapters` | MASTER §8（`plans/013_batch_b.plan.md` 索引） |
| C | 015+016 | `06-17-round2-batch-c-validation-conflict` | MASTER §8（`plans/015_016_batch_c.plan.md` 索引） |
| D | 014 | （Plan 待建） | `plans/014_*.plan.md` |

## 执行前必读

- `../GLOBAL_EXECUTION_RULES.md`
- `../GLOBAL_TESTING_POLICY.md`
- `../GLOBAL_RESOURCE_LIMITS.md`
- `../GLOBAL_TASK_TEMPLATE.md`
- `./DECISIONS.md` — 本轮已确认决策（**先读**）
- `./BATCH_B_REPAIR_STATUS.md` — Batch B GPT repair 与延后台账
- `./BATCH_C_LEDGER.md` — C-C0 前置约定与 Batch C 台账

**Trellis Plan：** 每批次 `MASTER.plan.md` §1.3 须映射本目录 `NNN_*.md` 任务卡；`plans/*.plan.md` 仅为索引（Execute 只读 MASTER）。

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

- [x] `pytest -q` 全绿（**182** passed @ `ab8d1eb` · cov 93%）
- [x] migration **004** 已应用（003 resource_guard 保留）
- [x] YAML 加载 + legacy 角色拒绝（含顶层 banned key）
- [x] fetch 失败仍写 fetch_log
- [x] GPT P0 `SourceMismatchError`（`ab8d1eb`）

**Batch A 已完成** — 延后项见 `DECISIONS.md` §9。

## Batch B Checkpoint（013 + GPT repair）

- [x] 5 vendor skeleton + FetchPort + RawStore + FileRegistry
- [x] GPT P0/P1 repair（`NOT_PUBLISHED_YET`、禁默认 Stub、生产 FileRegistry 必填等）
- [x] 契约同步 `specs/contracts/data_adapter_contract.md`
- [x] PR #2 已合并；GPT repair 文档/测试同步（本 commit）

**Batch B 已完成** — 可进入 Batch C Plan（015+016）。Repair 台账：`BATCH_B_REPAIR_STATUS.md` · 延后项 `DECISIONS.md` §9–§10。

## Plan / Execute 状态

| 批次 | Plan | Execute | Audit | GPT repair |
|------|------|---------|-------|------------|
| A | ✅ 已冻结 | ✅ `ee48187` | ✅ PASS | ✅ `ab8d1eb` |
| B | ✅ v1.1 已冻结 | ✅ PR #2 合并 | ✅ PASS | ✅ 本 commit |
| C | ✅ 已冻结 | ✅ Execute complete / awaiting Audit | 待 Audit | — |
| D | 未开始 | 未开始 | — | — |

Trellis 任务目录：
- Batch A（已归档）：`.trellis/tasks/archive/2026-06/06-17-round2-batch-a-sources/`
- Batch B（已归档）：`.trellis/tasks/archive/2026-06/06-17-round2-batch-b-adapters/`
- Batch C（执行中，待 Audit）：`.trellis/tasks/06-17-round2-batch-c-validation-conflict/`
