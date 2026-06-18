# Original Plan Trace — 06-17-round2-batch-c-validation-conflict

## Round / Batch

`ROUND_2_DATA_INGESTION_VALIDATION` · Batch **C**（015 + 016）

## 任务卡清单

| NNN | 路径 |
|-----|------|
| 015 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/015_implement_data_quality_validator.md` |
| 016 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/016_implement_source_conflict_validator.md` |

## AC 映射（任务卡 → MASTER §2）

| 任务卡要点 | MASTER AC |
|-----------|-----------|
| 015：空值/重复/日期/schema drift/stale/history | AC-3 data quality 语义 |
| 015：validation_report、失败不进 clean | AC-2、AC-4、AC-8 |
| 016：多源冲突、source_conflict、manual review | AC-5、AC-6 |
| 016：严重冲突、口径差异 | AC-6、AC-7 |
| DECISIONS：005 migration、real ValidationGate | AC-1、AC-4 |
| BATCH_B：SUCCESS evidence、PortStatus、脱敏 | AC-9、AC-10 |

## 输入文件已读

- `docs/modules/data_validation_and_conflict.md`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `docs/architecture/03_runtime_flows.md`
- `docs/architecture/04_data_architecture.md`

## 路径纠偏

原计划 015/016 写 `backend/validation/*` → 实际 **`backend/app/validators/*`**（与 Round 1 `backend/app/*` 一致）。
